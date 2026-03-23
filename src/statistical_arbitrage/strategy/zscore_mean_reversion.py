"""Pure z-score mean-reversion strategy logic."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import polars as pl

from statistical_arbitrage.backtesting.models import SignalEvent, StrategyParameters


def _to_numpy(values: Sequence[Any] | np.ndarray | pl.Series) -> np.ndarray:
    """Convert supported series-like inputs to a numpy float array."""
    if isinstance(values, np.ndarray):
        return values.astype(float, copy=False)
    if isinstance(values, pl.Series):
        return values.cast(pl.Float64).to_numpy()
    return np.asarray(values, dtype=float)


def normalize_timestamps(
    timestamps: Sequence[Any] | np.ndarray | pl.Series,
) -> list[str]:
    """Convert supported timestamp inputs to a list of strings."""
    if isinstance(timestamps, pl.Series):
        values = timestamps.to_list()
    elif isinstance(timestamps, np.ndarray):
        values = timestamps.tolist()
    else:
        values = list(timestamps)
    return [str(value) for value in values]


def calculate_hedge_ratio(
    asset1_prices: Sequence[Any] | np.ndarray | pl.Series,
    asset2_prices: Sequence[Any] | np.ndarray | pl.Series,
) -> float:
    """Compute the project-standard OLS hedge ratio for a single window."""
    prices1 = _to_numpy(asset1_prices)
    prices2 = _to_numpy(asset2_prices)
    return float(np.polyfit(prices2, prices1, 1)[0])


def calculate_spread(
    asset1_prices: Sequence[Any] | np.ndarray | pl.Series,
    asset2_prices: Sequence[Any] | np.ndarray | pl.Series,
    hedge_ratio: float,
) -> np.ndarray:
    """Calculate price-level spread using a supplied hedge ratio."""
    prices1 = _to_numpy(asset1_prices)
    prices2 = _to_numpy(asset2_prices)
    return prices1 - (hedge_ratio * prices2)


def build_rolling_strategy_data(
    asset1_prices: Sequence[Any] | np.ndarray | pl.Series,
    asset2_prices: Sequence[Any] | np.ndarray | pl.Series,
    lookback_window: int,
) -> dict[str, np.ndarray]:
    """Build look-ahead-safe hedge ratios, spreads, and z-scores.

    For each bar ``i`` with enough trailing history, the hedge ratio and z-score are
    estimated using only the trailing window ending at ``i``.
    """
    prices1 = _to_numpy(asset1_prices)
    prices2 = _to_numpy(asset2_prices)

    n = len(prices1)
    hedge_ratios = np.full(n, np.nan, dtype=float)
    spreads = np.full(n, np.nan, dtype=float)
    rolling_means = np.full(n, np.nan, dtype=float)
    rolling_stds = np.full(n, np.nan, dtype=float)
    zscores = np.full(n, np.nan, dtype=float)

    for index in range(lookback_window - 1, n):
        start = index - lookback_window + 1
        window_prices1 = prices1[start : index + 1]
        window_prices2 = prices2[start : index + 1]

        hedge_ratio = calculate_hedge_ratio(window_prices1, window_prices2)
        spread_window = calculate_spread(window_prices1, window_prices2, hedge_ratio)
        spread_mean = float(np.mean(spread_window))
        spread_std = float(np.std(spread_window, ddof=1))
        current_spread = float(spread_window[-1])

        hedge_ratios[index] = hedge_ratio
        spreads[index] = current_spread
        rolling_means[index] = spread_mean
        rolling_stds[index] = spread_std
        if spread_std > 0:
            zscores[index] = (current_spread - spread_mean) / spread_std

    return {
        "hedge_ratio": hedge_ratios,
        "spread": spreads,
        "rolling_mean": rolling_means,
        "rolling_std": rolling_stds,
        "zscore": zscores,
    }


def generate_signal_events(
    zscore: Sequence[Any] | np.ndarray | pl.Series,
    timestamps: Sequence[Any] | np.ndarray | pl.Series,
    params: StrategyParameters,
    hedge_ratios: Sequence[Any] | np.ndarray | pl.Series,
) -> tuple[list[SignalEvent], int]:
    """Generate next-bar executable signal events from a z-score series.

    Signals are observed using data available at bar close ``i`` and are executable only
    on bar ``i + 1``. The returned ``SignalEvent`` objects therefore carry both indices.

    Returns:
        A tuple of (events, dropped_terminal_signals).
    """
    zscores = _to_numpy(zscore)
    hedge_ratio_values = _to_numpy(hedge_ratios)
    normalized_timestamps = normalize_timestamps(timestamps)

    events: list[SignalEvent] = []
    dropped_terminal_signals = 0
    position = 0  # 0=flat, 1=long spread, -1=short spread

    for signal_index, z_value in enumerate(zscores):
        if np.isnan(z_value):
            continue

        hedge_ratio = hedge_ratio_values[signal_index]
        if np.isnan(hedge_ratio):
            continue

        signal_type: str | None = None
        direction: str | None = None

        if position == 0:
            if z_value <= -params.entry_threshold:
                signal_type = "long_entry"
                direction = "long_spread"
                position = 1
            elif z_value >= params.entry_threshold:
                signal_type = "short_entry"
                direction = "short_spread"
                position = -1
        elif position == 1:
            if z_value >= -params.exit_threshold:
                signal_type = "long_exit"
                direction = "long_spread"
                position = 0
            elif z_value <= -params.stop_loss:
                signal_type = "stop_loss"
                direction = "long_spread"
                position = 0
        else:
            if z_value <= params.exit_threshold:
                signal_type = "short_exit"
                direction = "short_spread"
                position = 0
            elif z_value >= params.stop_loss:
                signal_type = "stop_loss"
                direction = "short_spread"
                position = 0

        if signal_type is None or direction is None:
            continue

        execution_index = signal_index + 1
        if execution_index >= len(zscores):
            dropped_terminal_signals += 1
            continue

        events.append(
            SignalEvent(
                signal_index=signal_index,
                execution_index=execution_index,
                signal_timestamp=normalized_timestamps[signal_index],
                execution_timestamp=normalized_timestamps[execution_index],
                signal_type=signal_type,
                direction=direction,
                zscore_at_signal=float(z_value),
                hedge_ratio_at_signal=float(hedge_ratio),
            )
        )

    return events, dropped_terminal_signals
