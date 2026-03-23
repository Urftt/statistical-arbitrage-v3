"""Typed domain models for the backtest engine."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BacktestModel(BaseModel):
    """Shared strict base model for backtesting payloads."""

    model_config = ConfigDict(extra="forbid")


class StrategyParameters(BacktestModel):
    """Serializable strategy and accounting parameters."""

    lookback_window: int = Field(gt=1)
    entry_threshold: float = Field(gt=0)
    exit_threshold: float = Field(ge=0)
    stop_loss: float = Field(gt=0)
    initial_capital: float = Field(gt=0)
    position_size: float = Field(gt=0, le=1)
    transaction_fee: float = Field(ge=0)
    min_trade_count_warning: int = Field(default=3, ge=0)


class EngineWarning(BacktestModel):
    """Structured warning or blocker surfaced to the caller."""

    code: str
    severity: Literal["warning", "blocking"]
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class DataQualityReport(BacktestModel):
    """Preflight validation output exposed with every run."""

    status: Literal["passed", "blocked"]
    observations_total: int = Field(ge=0)
    observations_usable: int = Field(ge=0)
    warmup_bars: int = Field(ge=0)
    blockers: list[EngineWarning] = Field(default_factory=list)
    warnings: list[EngineWarning] = Field(default_factory=list)


class HonestReportingFooter(BacktestModel):
    """Assumptions and limitations the UI must show honestly."""

    execution_model: str
    fee_model: str
    data_basis: str
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class SignalEvent(BacktestModel):
    """One signal observed at a bar close and executed on the next bar."""

    signal_index: int = Field(ge=0)
    execution_index: int = Field(ge=0)
    signal_timestamp: str
    execution_timestamp: str
    signal_type: Literal[
        "long_entry",
        "short_entry",
        "long_exit",
        "short_exit",
        "stop_loss",
    ]
    direction: Literal["long_spread", "short_spread"]
    zscore_at_signal: float
    hedge_ratio_at_signal: float


class TradeLedgerRow(BacktestModel):
    """Round-trip trade row with fee-aware accounting details."""

    trade_id: int = Field(ge=1)
    direction: Literal["long_spread", "short_spread"]
    entry_signal_index: int = Field(ge=0)
    entry_execution_index: int = Field(ge=0)
    exit_signal_index: int = Field(ge=0)
    exit_execution_index: int = Field(ge=0)
    entry_timestamp: str
    exit_timestamp: str
    entry_reason: Literal["long_entry", "short_entry"]
    exit_reason: Literal["long_exit", "short_exit", "stop_loss"]
    bars_held: int = Field(ge=1)
    entry_zscore: float
    exit_zscore: float
    hedge_ratio: float
    quantity_asset1: float
    quantity_asset2: float
    entry_price_asset1: float = Field(gt=0)
    entry_price_asset2: float = Field(gt=0)
    exit_price_asset1: float = Field(gt=0)
    exit_price_asset2: float = Field(gt=0)
    allocated_capital: float = Field(gt=0)
    gross_pnl: float
    total_fees: float = Field(ge=0)
    net_pnl: float
    return_pct: float
    equity_after_trade: float = Field(gt=0)


class EquityPoint(BacktestModel):
    """Equity curve point for one timestamp."""

    index: int = Field(ge=0)
    timestamp: str
    equity: float = Field(gt=0)
    cash: float = Field(gt=0)
    unrealized_pnl: float
    position: Literal["flat", "long_spread", "short_spread"]


class MetricSummary(BacktestModel):
    """Backtest performance summary."""

    total_trades: int = Field(ge=0)
    winning_trades: int = Field(ge=0)
    losing_trades: int = Field(ge=0)
    win_rate: float = Field(ge=0, le=1)
    total_net_pnl: float
    total_return_pct: float
    average_trade_return_pct: float
    average_holding_period_bars: float
    max_drawdown_pct: float = Field(ge=0)
    profit_factor: float | None = None
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    final_equity: float = Field(gt=0)


class OverfitWarningThresholds(BacktestModel):
    """Tunable thresholds for overfitting detection heuristics."""

    sharpe_threshold: float = 3.0
    profit_factor_threshold: float = 5.0
    profit_factor_min_trades: int = 20
    winrate_threshold: float = 0.85
    winrate_min_trades: int = 10
    smooth_equity_max_drawdown: float = 0.01
    smooth_equity_min_sharpe: float = 2.0


class BacktestResult(BacktestModel):
    """Top-level engine output for API and UI layers."""

    status: Literal["ok", "blocked"]
    params: StrategyParameters
    preflight: DataQualityReport
    warnings: list[EngineWarning] = Field(default_factory=list)
    footer: HonestReportingFooter
    spread_mean: float | None = None
    spread_std: float | None = None
    signals: list[SignalEvent] = Field(default_factory=list)
    trades: list[TradeLedgerRow] = Field(default_factory=list)
    equity_curve: list[EquityPoint] = Field(default_factory=list)
    metrics: MetricSummary


# ---------------------------------------------------------------------------
# Grid Search models
# ---------------------------------------------------------------------------


class ParameterAxis(BacktestModel):
    """One axis of the grid search: a named parameter with min/max/step."""

    name: str = Field(description="Must be a valid StrategyParameters field name")
    min_value: float
    max_value: float
    step: float = Field(gt=0)

    @model_validator(mode="after")
    def _check_range(self) -> ParameterAxis:
        if self.min_value >= self.max_value:
            msg = f"min_value ({self.min_value}) must be less than max_value ({self.max_value})"
            raise ValueError(msg)
        return self


class GridSearchCell(BacktestModel):
    """One cell in the grid search result matrix."""

    params: dict[str, float] = Field(description="Axis name → parameter value")
    metrics: MetricSummary
    trade_count: int = Field(ge=0)
    status: Literal["ok", "blocked", "no_trades"]


class WalkForwardFold(BacktestModel):
    """One train/test fold in a walk-forward validation run."""

    fold_index: int = Field(ge=0)
    train_start_idx: int = Field(ge=0)
    train_end_idx: int = Field(ge=0)
    test_start_idx: int = Field(ge=0)
    test_end_idx: int = Field(ge=0)
    train_bars: int = Field(ge=0)
    test_bars: int = Field(ge=0)
    best_params: dict[str, float] = Field(
        default_factory=dict,
        description="Axis name → optimized value from train-window grid search",
    )
    train_metrics: MetricSummary
    test_metrics: MetricSummary
    train_trade_count: int = Field(ge=0)
    test_trade_count: int = Field(ge=0)
    status: Literal["ok", "no_train_trades", "no_test_trades", "blocked"] = "ok"


class WalkForwardResult(BacktestModel):
    """Aggregated walk-forward validation output."""

    folds: list[WalkForwardFold]
    fold_count: int = Field(ge=0)
    train_pct: float = Field(gt=0, lt=1)
    axes: list[ParameterAxis]
    aggregate_train_sharpe: float | None = None
    aggregate_test_sharpe: float | None = None
    train_test_divergence: float | None = Field(
        default=None,
        description="Ratio of test Sharpe to train Sharpe — <0.5 is suspicious",
    )
    stability_verdict: Literal["stable", "moderate", "fragile"] = "fragile"
    warnings: list[EngineWarning] = Field(default_factory=list)
    execution_time_ms: float = Field(ge=0)


class GridSearchResult(BacktestModel):
    """Complete grid search output with robustness and overfitting analysis."""

    cells: list[GridSearchCell]
    grid_shape: list[int] = Field(description="Per-axis dimension count")
    axes: list[ParameterAxis]
    best_cell_index: int | None = None
    best_cell: GridSearchCell | None = None
    optimize_metric: str
    total_combinations: int = Field(ge=0)
    robustness_score: float | None = Field(
        default=None,
        description="Fraction of best-cell neighbors within 80% of best metric",
    )
    warnings: list[EngineWarning] = Field(default_factory=list)
    execution_time_ms: float = Field(ge=0)
