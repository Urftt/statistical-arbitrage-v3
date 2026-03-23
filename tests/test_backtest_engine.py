"""Deterministic tests for the look-ahead-safe backtest engine."""

import pytest

from statistical_arbitrage.backtesting.engine import run_backtest
from statistical_arbitrage.backtesting.models import StrategyParameters


def _params(**overrides) -> StrategyParameters:
    base = {
        "lookback_window": 3,
        "entry_threshold": 1.0,
        "exit_threshold": 0.25,
        "stop_loss": 2.0,
        "initial_capital": 1000.0,
        "position_size": 0.5,
        "transaction_fee": 0.005,
        "min_trade_count_warning": 3,
    }
    base.update(overrides)
    return StrategyParameters(**base)


def _single_long_fixture() -> tuple[
    list[int], list[float], list[float], StrategyParameters
]:
    timestamps = [0, 1, 2, 3, 4, 5]
    asset2 = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
    asset1 = [200.0, 202.0, 204.0, 194.0, 208.0, 222.0]
    return timestamps, asset1, asset2, _params()


def _long_short_fixture() -> tuple[
    list[int], list[float], list[float], StrategyParameters
]:
    timestamps = list(range(12))
    asset2 = [float(100 + i) for i in range(12)]
    deviations = [0.0, 0.0, 0.0, -12.0, 0.0, 12.0, 0.0, -12.0, 0.0, 12.0, 0.0, -12.0]
    asset1 = [
        2 * price + deviation
        for price, deviation in zip(asset2, deviations, strict=True)
    ]
    return timestamps, asset1, asset2, _params()


class TestBacktestEngine:
    def test_executes_signals_on_the_next_bar_without_lookahead(self):
        timestamps, asset1, asset2, params = _long_short_fixture()

        result = run_backtest(timestamps, asset1, asset2, params)

        assert result.status == "ok"
        assert len(result.signals) == 4
        assert len(result.trades) == 2

        first_signal = result.signals[0]
        first_trade = result.trades[0]
        second_trade = result.trades[1]

        assert first_signal.signal_type == "long_entry"
        assert first_signal.signal_index == 2
        assert first_signal.execution_index == 3
        assert first_trade.entry_execution_index == first_signal.execution_index
        assert first_trade.entry_price_asset1 == pytest.approx(asset1[3])
        assert first_trade.entry_price_asset1 != asset1[first_signal.signal_index]
        assert first_trade.entry_timestamp == str(timestamps[3])

        assert second_trade.direction == "short_spread"
        assert second_trade.entry_execution_index == 6
        assert second_trade.exit_execution_index == 7
        assert second_trade.exit_reason == "short_exit"

    def test_accounts_for_fees_and_marks_equity_deterministically(self):
        timestamps, asset1, asset2, params = _single_long_fixture()

        result = run_backtest(timestamps, asset1, asset2, params)

        assert result.status == "ok"
        assert len(result.trades) == 1

        trade = result.trades[0]
        equity_curve = result.equity_curve

        expected_quantity_asset1 = 1.25
        expected_quantity_asset2 = -2.5
        expected_entry_fee = 500.0 * params.transaction_fee
        expected_exit_fee = 540.0 * params.transaction_fee
        expected_total_fees = expected_entry_fee + expected_exit_fee
        expected_gross_pnl = expected_quantity_asset1 * (
            222.0 - 194.0
        ) + expected_quantity_asset2 * (105.0 - 103.0)
        expected_net_pnl = expected_gross_pnl - expected_total_fees

        assert trade.hedge_ratio == pytest.approx(2.0)
        assert trade.quantity_asset1 == pytest.approx(expected_quantity_asset1)
        assert trade.quantity_asset2 == pytest.approx(expected_quantity_asset2)
        assert trade.gross_pnl == pytest.approx(expected_gross_pnl)
        assert trade.total_fees == pytest.approx(expected_total_fees)
        assert trade.net_pnl == pytest.approx(expected_net_pnl)
        assert trade.return_pct == pytest.approx(expected_net_pnl / 500.0)

        assert equity_curve[3].equity == pytest.approx(997.5)
        assert equity_curve[4].equity == pytest.approx(1012.5)
        assert equity_curve[5].equity == pytest.approx(1024.8)
        assert result.metrics.total_trades == 1
        assert result.metrics.total_net_pnl == pytest.approx(24.8)
        assert result.metrics.final_equity == pytest.approx(1024.8)

    def test_blocks_short_histories_with_structured_preflight_output(self):
        params = _params()

        result = run_backtest(
            timestamps=[0, 1, 2, 3],
            asset1_prices=[100.0, 101.0, 102.0, 103.0],
            asset2_prices=[50.0, 51.0, 52.0, 53.0],
            params=params,
        )

        assert result.status == "blocked"
        assert result.preflight.status == "blocked"
        assert result.trades == []
        assert result.equity_curve == []
        blocker_codes = {warning.code for warning in result.preflight.blockers}
        assert "insufficient_observations" in blocker_codes
        assert result.metrics.final_equity == pytest.approx(params.initial_capital)

    def test_surfaces_fragile_run_warnings_and_honest_footer_metadata(self):
        timestamps, asset1, asset2, params = _single_long_fixture()

        result = run_backtest(timestamps, asset1, asset2, params)
        warning_codes = {warning.code for warning in result.warnings}
        preflight_warning_codes = {
            warning.code for warning in result.preflight.warnings
        }

        assert "limited_post_warmup_sample" in preflight_warning_codes
        assert "too_few_trades" in warning_codes
        assert "dropped_terminal_signals" in warning_codes
        assert "next bar" in result.footer.execution_model.lower()
        assert any(
            "close-only" in limitation.lower()
            for limitation in result.footer.limitations
        )
        assert result.model_dump()["warnings"]
