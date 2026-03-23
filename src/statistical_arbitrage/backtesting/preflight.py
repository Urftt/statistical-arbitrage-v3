"""Preflight validation for look-ahead-safe backtests."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import polars as pl

from statistical_arbitrage.backtesting.models import (
    DataQualityReport,
    EngineWarning,
    StrategyParameters,
)


def _to_float_array(values: Sequence[Any] | np.ndarray | pl.Series) -> np.ndarray:
    """Convert supported inputs to float arrays for validation."""
    if isinstance(values, np.ndarray):
        return values.astype(float, copy=False)
    if isinstance(values, pl.Series):
        return values.cast(pl.Float64).to_numpy()
    return np.asarray(values, dtype=float)


def _to_timestamp_list(values: Sequence[Any] | np.ndarray | pl.Series) -> list[Any]:
    """Convert supported timestamp inputs to a Python list."""
    if isinstance(values, pl.Series):
        return values.to_list()
    if isinstance(values, np.ndarray):
        return values.tolist()
    return list(values)


def _blocking(code: str, message: str, **details: Any) -> EngineWarning:
    return EngineWarning(
        code=code, severity="blocking", message=message, details=details
    )


def _warning(code: str, message: str, **details: Any) -> EngineWarning:
    return EngineWarning(
        code=code, severity="warning", message=message, details=details
    )


def run_preflight(
    timestamps: Sequence[Any] | np.ndarray | pl.Series,
    asset1_prices: Sequence[Any] | np.ndarray | pl.Series,
    asset2_prices: Sequence[Any] | np.ndarray | pl.Series,
    params: StrategyParameters,
) -> DataQualityReport:
    """Validate the minimum data quality required to run a trustworthy backtest."""
    timestamp_values = _to_timestamp_list(timestamps)
    prices1 = _to_float_array(asset1_prices)
    prices2 = _to_float_array(asset2_prices)

    lengths = {
        "timestamps": len(timestamp_values),
        "asset1_prices": len(prices1),
        "asset2_prices": len(prices2),
    }
    observations_total = min(lengths.values()) if lengths else 0
    warmup_bars = params.lookback_window
    blockers: list[EngineWarning] = []
    warnings: list[EngineWarning] = []

    if len(set(lengths.values())) != 1:
        blockers.append(
            _blocking(
                "length_mismatch",
                "Timestamps and price series must have identical lengths.",
                lengths=lengths,
            )
        )

    required_observations = params.lookback_window + 2
    if observations_total < required_observations:
        blockers.append(
            _blocking(
                "insufficient_observations",
                "Need at least lookback_window + 2 overlapping candles to compute a signal and execute it on the next bar.",
                observations_total=observations_total,
                required_observations=required_observations,
            )
        )

    if any(value is None or value == "" for value in timestamp_values):
        blockers.append(
            _blocking(
                "null_timestamps",
                "Timestamp series contains null or empty values.",
            )
        )

    null_price_mask = np.isnan(prices1) | np.isnan(prices2)
    if np.any(null_price_mask):
        blockers.append(
            _blocking(
                "null_price_gaps",
                "Price series contains null gaps; fill or drop them before backtesting.",
                null_rows=int(np.count_nonzero(null_price_mask)),
            )
        )

    finite_price_mask = np.isfinite(prices1) & np.isfinite(prices2)
    if not np.all(finite_price_mask):
        blockers.append(
            _blocking(
                "non_finite_prices",
                "Price series contains non-finite values.",
                bad_rows=int(
                    len(finite_price_mask) - np.count_nonzero(finite_price_mask)
                ),
            )
        )

    impossible_price_mask = (prices1 <= 0) | (prices2 <= 0)
    if np.any(impossible_price_mask):
        blockers.append(
            _blocking(
                "impossible_prices",
                "Backtests require strictly positive prices for both assets.",
                bad_rows=int(np.count_nonzero(impossible_price_mask)),
            )
        )

    if len(timestamp_values) >= 2:
        try:
            monotonic = all(
                a < b for a, b in zip(timestamp_values[:-1], timestamp_values[1:])
            )
        except TypeError:
            monotonic = False
        if not monotonic:
            blockers.append(
                _blocking(
                    "non_monotonic_timestamps",
                    "Timestamps must be strictly increasing.",
                )
            )

    observations_usable = max(observations_total - warmup_bars, 0)
    if (
        observations_total >= required_observations
        and observations_usable <= warmup_bars
    ):
        warnings.append(
            _warning(
                "limited_post_warmup_sample",
                "The usable sample after the rolling warmup is short relative to the lookback window; results may be unstable.",
                observations_usable=observations_usable,
                warmup_bars=warmup_bars,
            )
        )

    status = "blocked" if blockers else "passed"
    return DataQualityReport(
        status=status,
        observations_total=observations_total,
        observations_usable=observations_usable,
        warmup_bars=warmup_bars,
        blockers=blockers,
        warnings=warnings,
    )


def build_post_run_warnings(
    trade_count: int,
    params: StrategyParameters,
    dropped_terminal_signals: int = 0,
    open_position_at_end: bool = False,
) -> list[EngineWarning]:
    """Create non-blocking warnings after a run completes."""
    warnings: list[EngineWarning] = []

    if trade_count == 0:
        warnings.append(
            _warning(
                "no_completed_trades",
                "The strategy produced no completed trades; metrics are descriptive only.",
            )
        )
    elif trade_count < params.min_trade_count_warning:
        warnings.append(
            _warning(
                "too_few_trades",
                "The strategy produced too few completed trades to support strong conclusions.",
                trade_count=trade_count,
                minimum=params.min_trade_count_warning,
            )
        )

    if dropped_terminal_signals > 0:
        warnings.append(
            _warning(
                "dropped_terminal_signals",
                "Signals on the final bar were discarded because the next execution bar does not exist.",
                dropped_terminal_signals=dropped_terminal_signals,
            )
        )

    if open_position_at_end:
        warnings.append(
            _warning(
                "open_position_at_end",
                "The final open trade remains unrealized because the backtest does not force-close positions on the last bar.",
            )
        )

    return warnings
