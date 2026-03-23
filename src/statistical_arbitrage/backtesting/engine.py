"""End-to-end fee-aware backtest runner."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import polars as pl

from config.settings import settings
from statistical_arbitrage.backtesting.models import (
    BacktestResult,
    DataQualityReport,
    EquityPoint,
    HonestReportingFooter,
    MetricSummary,
    StrategyParameters,
    TradeLedgerRow,
)
from statistical_arbitrage.backtesting.overfitting import detect_overfitting_warnings
from statistical_arbitrage.backtesting.preflight import (
    build_post_run_warnings,
    run_preflight,
)
from statistical_arbitrage.strategy.zscore_mean_reversion import (
    build_rolling_strategy_data,
    generate_signal_events,
    normalize_timestamps,
)


def default_strategy_parameters() -> StrategyParameters:
    """Build engine parameters from project settings."""
    strategy = settings.strategy
    return StrategyParameters(
        lookback_window=strategy.lookback_window,
        entry_threshold=strategy.entry_threshold,
        exit_threshold=strategy.exit_threshold,
        stop_loss=strategy.stop_loss,
        initial_capital=strategy.initial_capital,
        position_size=strategy.position_size,
        transaction_fee=strategy.transaction_fee,
    )


def _empty_metrics(initial_capital: float) -> MetricSummary:
    """Return a zero-trade metric payload."""
    return MetricSummary(
        total_trades=0,
        winning_trades=0,
        losing_trades=0,
        win_rate=0.0,
        total_net_pnl=0.0,
        total_return_pct=0.0,
        average_trade_return_pct=0.0,
        average_holding_period_bars=0.0,
        max_drawdown_pct=0.0,
        profit_factor=None,
        sharpe_ratio=None,
        sortino_ratio=None,
        final_equity=initial_capital,
    )


def _build_footer() -> HonestReportingFooter:
    """Return the honest-reporting metadata expected by downstream surfaces."""
    return HonestReportingFooter(
        execution_model="Signals are observed at bar close and executed on the next bar's close.",
        fee_model="Transaction fees are charged on both legs at entry and exit using traded notional.",
        data_basis="Spread and z-score use trailing-window OLS hedge ratios computed only from data available through each signal bar.",
        assumptions=[
            "Position size is allocated as a fraction of current equity based on gross pair notional.",
            "The hedge ratio captured at entry is held constant until the trade exits.",
            "Terminal signals without a next execution bar are discarded instead of force-filled.",
        ],
        limitations=[
            "This engine uses close-only candles; it does not model intrabar fills, slippage, borrow costs, or funding.",
            "Risk metrics are computed from bar-to-bar equity changes and are not annualized to a calendar timeframe.",
            "A rolling hedge ratio reduces look-ahead bias but may differ from a production execution model with explicit formation periods.",
        ],
    )


def _position_unrealized_pnl(
    position: dict[str, Any], price1: float, price2: float
) -> float:
    """Mark an open pair trade to market."""
    return float(
        position["quantity_asset1"] * (price1 - position["entry_price_asset1"])
        + position["quantity_asset2"] * (price2 - position["entry_price_asset2"])
    )


def _build_metrics(
    trades: list[TradeLedgerRow],
    equity_curve: list[EquityPoint],
    initial_capital: float,
) -> MetricSummary:
    """Compute deterministic summary metrics from the trade log and equity curve."""
    trade_net_pnls = np.array([trade.net_pnl for trade in trades], dtype=float)
    trade_returns = np.array([trade.return_pct for trade in trades], dtype=float)
    holding_periods = np.array([trade.bars_held for trade in trades], dtype=float)
    equity_values = np.array([point.equity for point in equity_curve], dtype=float)

    if len(equity_values) >= 2:
        returns = np.diff(equity_values) / equity_values[:-1]
    else:
        returns = np.array([], dtype=float)

    if len(equity_values) == 0:
        final_equity = initial_capital
        max_drawdown_pct = 0.0
    else:
        final_equity = float(equity_values[-1])
        running_peak = np.maximum.accumulate(equity_values)
        drawdowns = np.where(
            running_peak > 0, (running_peak - equity_values) / running_peak, 0.0
        )
        max_drawdown_pct = float(np.max(drawdowns)) if len(drawdowns) else 0.0

    if len(trade_net_pnls) == 0:
        return _empty_metrics(initial_capital=final_equity)

    losses = trade_net_pnls[trade_net_pnls < 0]
    gains = trade_net_pnls[trade_net_pnls > 0]
    profit_factor = None
    if len(losses) > 0:
        profit_factor = (
            float(np.sum(gains) / abs(np.sum(losses))) if len(gains) > 0 else 0.0
        )

    sharpe_ratio = None
    sortino_ratio = None
    if len(returns) >= 2:
        return_std = float(np.std(returns, ddof=1))
        if return_std > 1e-12:
            sharpe_ratio = float(
                (np.mean(returns) / return_std) * np.sqrt(len(returns))
            )
        downside = returns[returns < 0]
        if len(downside) >= 2:
            downside_std = float(np.std(downside, ddof=1))
            if downside_std > 1e-12:
                sortino_ratio = float(
                    (np.mean(returns) / downside_std) * np.sqrt(len(returns))
                )

    winning_trades = int(np.count_nonzero(trade_net_pnls > 0))
    losing_trades = int(np.count_nonzero(trade_net_pnls < 0))
    total_trades = len(trades)

    return MetricSummary(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=float(winning_trades / total_trades) if total_trades else 0.0,
        total_net_pnl=float(np.sum(trade_net_pnls)),
        total_return_pct=float((final_equity / initial_capital) - 1),
        average_trade_return_pct=float(np.mean(trade_returns))
        if len(trade_returns)
        else 0.0,
        average_holding_period_bars=float(np.mean(holding_periods))
        if len(holding_periods)
        else 0.0,
        max_drawdown_pct=max_drawdown_pct,
        profit_factor=profit_factor,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        final_equity=final_equity,
    )


def _blocked_result(
    params: StrategyParameters, preflight: DataQualityReport
) -> BacktestResult:
    """Build a structured blocked response instead of raising."""
    return BacktestResult(
        status="blocked",
        params=params,
        preflight=preflight,
        warnings=list(preflight.warnings),
        footer=_build_footer(),
        spread_mean=None,
        spread_std=None,
        signals=[],
        trades=[],
        equity_curve=[],
        metrics=_empty_metrics(params.initial_capital),
    )


def run_backtest(
    timestamps: Sequence[Any] | np.ndarray | pl.Series,
    asset1_prices: Sequence[Any] | np.ndarray | pl.Series,
    asset2_prices: Sequence[Any] | np.ndarray | pl.Series,
    params: StrategyParameters | None = None,
) -> BacktestResult:
    """Run the look-ahead-safe backtest and return a serializable result."""
    resolved_params = params or default_strategy_parameters()
    preflight = run_preflight(timestamps, asset1_prices, asset2_prices, resolved_params)
    if preflight.status == "blocked":
        return _blocked_result(resolved_params, preflight)

    normalized_timestamps = normalize_timestamps(timestamps)
    prices1 = np.asarray(asset1_prices, dtype=float)
    prices2 = np.asarray(asset2_prices, dtype=float)
    strategy_data = build_rolling_strategy_data(
        prices1, prices2, resolved_params.lookback_window
    )
    signals, dropped_terminal_signals = generate_signal_events(
        zscore=strategy_data["zscore"],
        timestamps=normalized_timestamps,
        params=resolved_params,
        hedge_ratios=strategy_data["hedge_ratio"],
    )
    events_by_execution_index = {event.execution_index: event for event in signals}

    current_cash = float(resolved_params.initial_capital)
    position: dict[str, Any] | None = None
    trades: list[TradeLedgerRow] = []
    equity_curve: list[EquityPoint] = []

    for index, (timestamp, price1, price2) in enumerate(
        zip(normalized_timestamps, prices1, prices2, strict=True)
    ):
        event = events_by_execution_index.get(index)

        if event is not None:
            if event.signal_type in {"long_entry", "short_entry"}:
                if position is None:
                    notional_denominator = (
                        price1 + abs(event.hedge_ratio_at_signal) * price2
                    )
                    scale = 0.0
                    allocated_capital = current_cash * resolved_params.position_size
                    if notional_denominator > 0:
                        scale = allocated_capital / notional_denominator

                    if event.direction == "long_spread":
                        quantity_asset1 = scale
                        quantity_asset2 = -scale * event.hedge_ratio_at_signal
                    else:
                        quantity_asset1 = -scale
                        quantity_asset2 = scale * event.hedge_ratio_at_signal

                    entry_notional = (
                        abs(quantity_asset1) * price1 + abs(quantity_asset2) * price2
                    )
                    entry_fee = entry_notional * resolved_params.transaction_fee
                    current_cash -= entry_fee
                    position = {
                        "direction": event.direction,
                        "entry_event": event,
                        "entry_timestamp": timestamp,
                        "entry_price_asset1": float(price1),
                        "entry_price_asset2": float(price2),
                        "entry_cash": float(current_cash),
                        "entry_fee": float(entry_fee),
                        "allocated_capital": float(allocated_capital),
                        "quantity_asset1": float(quantity_asset1),
                        "quantity_asset2": float(quantity_asset2),
                        "hedge_ratio": float(event.hedge_ratio_at_signal),
                    }
            else:
                if position is not None:
                    exit_notional = (
                        abs(position["quantity_asset1"]) * price1
                        + abs(position["quantity_asset2"]) * price2
                    )
                    exit_fee = exit_notional * resolved_params.transaction_fee
                    gross_pnl = _position_unrealized_pnl(
                        position, float(price1), float(price2)
                    )
                    net_pnl = gross_pnl - exit_fee
                    current_cash += gross_pnl - exit_fee

                    trades.append(
                        TradeLedgerRow(
                            trade_id=len(trades) + 1,
                            direction=position["direction"],
                            entry_signal_index=position["entry_event"].signal_index,
                            entry_execution_index=position[
                                "entry_event"
                            ].execution_index,
                            exit_signal_index=event.signal_index,
                            exit_execution_index=event.execution_index,
                            entry_timestamp=position["entry_timestamp"],
                            exit_timestamp=timestamp,
                            entry_reason=position["entry_event"].signal_type,
                            exit_reason=event.signal_type,
                            bars_held=event.execution_index
                            - position["entry_event"].execution_index,
                            entry_zscore=position["entry_event"].zscore_at_signal,
                            exit_zscore=event.zscore_at_signal,
                            hedge_ratio=position["hedge_ratio"],
                            quantity_asset1=position["quantity_asset1"],
                            quantity_asset2=position["quantity_asset2"],
                            entry_price_asset1=position["entry_price_asset1"],
                            entry_price_asset2=position["entry_price_asset2"],
                            exit_price_asset1=float(price1),
                            exit_price_asset2=float(price2),
                            allocated_capital=position["allocated_capital"],
                            gross_pnl=float(gross_pnl),
                            total_fees=float(position["entry_fee"] + exit_fee),
                            net_pnl=float(net_pnl - position["entry_fee"]),
                            return_pct=float(
                                (net_pnl - position["entry_fee"])
                                / position["allocated_capital"]
                            )
                            if position["allocated_capital"] > 0
                            else 0.0,
                            equity_after_trade=float(current_cash),
                        )
                    )
                    position = None

        if position is None:
            equity = current_cash
            unrealized_pnl = 0.0
            position_label = "flat"
        else:
            unrealized_pnl = _position_unrealized_pnl(
                position, float(price1), float(price2)
            )
            equity = position["entry_cash"] + unrealized_pnl
            position_label = position["direction"]

        equity_curve.append(
            EquityPoint(
                index=index,
                timestamp=timestamp,
                equity=float(equity),
                cash=float(current_cash),
                unrealized_pnl=float(unrealized_pnl),
                position=position_label,
            )
        )

    runtime_warnings = build_post_run_warnings(
        trade_count=len(trades),
        params=resolved_params,
        dropped_terminal_signals=dropped_terminal_signals,
        open_position_at_end=position is not None,
    )
    warnings = [*preflight.warnings, *runtime_warnings]

    valid_spreads = strategy_data["spread"][~np.isnan(strategy_data["spread"])]
    metrics = _build_metrics(
        trades=trades,
        equity_curve=equity_curve,
        initial_capital=resolved_params.initial_capital,
    )

    # Screen for suspiciously good metrics (overfitting heuristics)
    overfit_warnings = detect_overfitting_warnings(
        metrics=metrics, trade_count=len(trades)
    )
    warnings.extend(overfit_warnings)

    return BacktestResult(
        status="ok",
        params=resolved_params,
        preflight=preflight,
        warnings=warnings,
        footer=_build_footer(),
        spread_mean=float(np.mean(valid_spreads)) if len(valid_spreads) else None,
        spread_std=float(np.std(valid_spreads, ddof=1))
        if len(valid_spreads) > 1
        else None,
        signals=signals,
        trades=trades,
        equity_curve=equity_curve,
        metrics=metrics,
    )
