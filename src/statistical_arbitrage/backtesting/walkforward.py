"""Walk-forward validation engine.

Splits historical data into rolling train/test windows, runs grid-search
optimization on each train window, evaluates the best parameters on the
corresponding test window, and aggregates results with a stability verdict.

Pure-Python orchestration — no Dash, no IO beyond ``run_backtest()`` and
``run_grid_search()``.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from typing import Any

import numpy as np
import polars as pl

from statistical_arbitrage.backtesting.engine import run_backtest
from statistical_arbitrage.backtesting.models import (
    EngineWarning,
    MetricSummary,
    ParameterAxis,
    StrategyParameters,
    WalkForwardFold,
    WalkForwardResult,
)
from statistical_arbitrage.backtesting.optimization import run_grid_search

logger = logging.getLogger(__name__)


def _empty_metrics(initial_capital: float) -> MetricSummary:
    """Return zero-trade metrics for a blocked or empty fold."""
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
        final_equity=initial_capital,
    )


def run_walk_forward(
    timestamps: Sequence[Any] | np.ndarray | pl.Series,
    prices1: Sequence[Any] | np.ndarray | pl.Series,
    prices2: Sequence[Any] | np.ndarray | pl.Series,
    axes: list[ParameterAxis],
    base_params: StrategyParameters,
    fold_count: int = 5,
    train_pct: float = 0.6,
    optimize_metric: str = "sharpe_ratio",
    max_combinations_per_fold: int = 500,
) -> WalkForwardResult:
    """Run walk-forward validation over rolling train/test windows.

    For each fold:
    1. Slice data into non-overlapping train and test windows.
    2. Run ``run_grid_search()`` on the train window to find the best params.
    3. Run ``run_backtest()`` with those best params on the test window.
    4. Collect per-fold train and test metrics.

    After all folds, compute aggregate Sharpe, train-test divergence, and
    a stability verdict.

    Args:
        timestamps: Aligned timestamp series for the pair.
        prices1: Close prices for asset 1.
        prices2: Close prices for asset 2.
        axes: Parameter axes to sweep in each fold's grid search.
        base_params: Base strategy parameters — axis fields are overridden.
        fold_count: Number of train/test folds (minimum 2).
        train_pct: Fraction of each fold's window used for training (0.3–0.9).
        optimize_metric: ``MetricSummary`` field to maximize.
        max_combinations_per_fold: Hard limit on grid combos per fold.

    Returns:
        ``WalkForwardResult`` with per-fold details and aggregate summary.

    Raises:
        ValueError: When fold_count < 2 or train_pct out of range.
    """
    start_time = time.perf_counter()

    # --- Input validation ---
    if fold_count < 2:
        raise ValueError(f"fold_count must be >= 2, got {fold_count}")
    if not (0.3 <= train_pct <= 0.9):
        raise ValueError(f"train_pct must be between 0.3 and 0.9, got {train_pct}")

    # Convert to numpy for slicing
    ts = np.asarray(timestamps)
    p1 = np.asarray(prices1, dtype=np.float64)
    p2 = np.asarray(prices2, dtype=np.float64)
    n = len(ts)

    # --- Compute fold windows ---
    # min_window = minimum total bars per fold (train + test)
    # We need at least lookback_window + 10 bars in the test portion,
    # and at least lookback_window + 10 in the train portion.
    min_test_bars = base_params.lookback_window + 10
    min_train_bars = base_params.lookback_window + 10
    min_window = min_train_bars + min_test_bars

    if n < min_window:
        raise ValueError(
            f"Not enough data: {n} bars, need at least {min_window} "
            f"(lookback_window={base_params.lookback_window})"
        )

    # Step size so folds advance through the data
    # With fold_count folds, we need fold_count windows that advance
    # step = how much the window start advances per fold
    step = (n - min_window) // (fold_count - 1) if fold_count > 1 else 0

    if step < 1 and fold_count > 1:
        # Not enough data for the requested fold count — reduce to what fits
        step = 1

    warnings: list[EngineWarning] = []
    folds: list[WalkForwardFold] = []

    for fold_idx in range(fold_count):
        train_start = fold_idx * step
        # Total window size for this fold = remaining bars from train_start
        remaining = n - train_start
        train_bars = max(int(remaining * train_pct), min_train_bars)
        train_end = train_start + train_bars

        test_start = train_end
        # Test window extends to the earlier of: data end, or a proportional test size
        test_bars_target = max(int(remaining * (1 - train_pct)), min_test_bars)
        test_end = min(test_start + test_bars_target, n)
        test_bars = test_end - test_start

        # Clamp train_end to avoid exceeding data
        if train_end > n:
            train_end = n
            train_bars = train_end - train_start

        # Skip folds where test window is empty
        if test_start >= n or test_bars <= 0:
            warnings.append(
                EngineWarning(
                    code="wf_fold_skipped",
                    severity="warning",
                    message=f"Fold {fold_idx}: test window extends beyond data, skipped.",
                    details={"fold_index": fold_idx, "train_start": train_start},
                )
            )
            continue

        # Warn if test window is very short
        if test_bars < base_params.lookback_window + 10:
            warnings.append(
                EngineWarning(
                    code="wf_short_test_window",
                    severity="warning",
                    message=(
                        f"Fold {fold_idx}: test window has only {test_bars} bars "
                        f"(need {base_params.lookback_window + 10} for warmup + trades). "
                        f"Results may be unreliable."
                    ),
                    details={
                        "fold_index": fold_idx,
                        "test_bars": test_bars,
                        "min_recommended": base_params.lookback_window + 10,
                    },
                )
            )

        # --- Train: grid search on train window ---
        train_ts = ts[train_start:train_end]
        train_p1 = p1[train_start:train_end]
        train_p2 = p2[train_start:train_end]

        fold_status = "ok"
        best_params: dict[str, float] = {}
        train_metrics = _empty_metrics(base_params.initial_capital)
        train_trade_count = 0

        try:
            grid_result = run_grid_search(
                timestamps=train_ts,
                prices1=train_p1,
                prices2=train_p2,
                axes=axes,
                base_params=base_params,
                optimize_metric=optimize_metric,
                max_combinations=max_combinations_per_fold,
            )

            if grid_result.best_cell is not None:
                best_params = grid_result.best_cell.params
                train_metrics = grid_result.best_cell.metrics
                train_trade_count = grid_result.best_cell.trade_count
                if train_trade_count == 0:
                    fold_status = "no_train_trades"
            else:
                fold_status = "no_train_trades"

        except Exception:
            logger.exception("Fold %d: grid search failed on train window", fold_idx)
            fold_status = "blocked"

        # --- Test: run backtest with best params on test window ---
        test_ts = ts[test_start:test_end]
        test_p1 = p1[test_start:test_end]
        test_p2 = p2[test_start:test_end]

        test_metrics = _empty_metrics(base_params.initial_capital)
        test_trade_count = 0

        if fold_status not in ("blocked",):
            # Apply best params to base params
            test_params = base_params.model_copy(update=best_params)

            try:
                test_result = run_backtest(
                    timestamps=test_ts,
                    asset1_prices=test_p1,
                    asset2_prices=test_p2,
                    params=test_params,
                )
                test_metrics = test_result.metrics
                test_trade_count = test_result.metrics.total_trades

                if test_trade_count == 0 and fold_status == "ok":
                    fold_status = "no_test_trades"

            except Exception:
                logger.exception("Fold %d: test backtest failed", fold_idx)
                if fold_status == "ok":
                    fold_status = "blocked"

        folds.append(
            WalkForwardFold(
                fold_index=fold_idx,
                train_start_idx=train_start,
                train_end_idx=train_end,
                test_start_idx=test_start,
                test_end_idx=test_end,
                train_bars=train_end - train_start,
                test_bars=test_bars,
                best_params=best_params,
                train_metrics=train_metrics,
                test_metrics=test_metrics,
                train_trade_count=train_trade_count,
                test_trade_count=test_trade_count,
                status=fold_status,
            )
        )

    # --- Aggregate metrics ---
    train_sharpes: list[float] = []
    test_sharpes: list[float] = []

    for fold in folds:
        if fold.status == "ok" and fold.train_metrics.sharpe_ratio is not None:
            train_sharpes.append(fold.train_metrics.sharpe_ratio)
        if fold.status == "ok" and fold.test_metrics.sharpe_ratio is not None:
            test_sharpes.append(fold.test_metrics.sharpe_ratio)

    aggregate_train_sharpe = float(np.mean(train_sharpes)) if train_sharpes else None
    aggregate_test_sharpe = float(np.mean(test_sharpes)) if test_sharpes else None

    # Train-test divergence: ratio of test Sharpe to train Sharpe
    train_test_divergence: float | None = None
    if aggregate_train_sharpe is not None and aggregate_test_sharpe is not None:
        if aggregate_train_sharpe > 0:
            train_test_divergence = aggregate_test_sharpe / aggregate_train_sharpe
        elif aggregate_train_sharpe == 0:
            # If train Sharpe is 0, divergence is undefined
            train_test_divergence = None
        else:
            # Negative train Sharpe: strategy is bad in-sample too
            train_test_divergence = None

    # Stability verdict
    valid_test_folds = len(test_sharpes)
    if valid_test_folds < 3 or train_test_divergence is None:
        stability_verdict = "fragile"
    elif train_test_divergence >= 0.5:
        stability_verdict = "stable"
    elif train_test_divergence >= 0.25:
        stability_verdict = "moderate"
    else:
        stability_verdict = "fragile"

    # --- Generate aggregate warnings ---
    if train_test_divergence is not None and train_test_divergence < 0.5:
        warnings.append(
            EngineWarning(
                code="wf_train_test_divergence",
                severity="warning",
                message=(
                    f"Train-test divergence is {train_test_divergence:.2f} "
                    f"(test Sharpe {aggregate_test_sharpe:.2f} vs train Sharpe "
                    f"{aggregate_train_sharpe:.2f}). This suggests the optimized "
                    f"parameters may not generalize."
                ),
                details={
                    "train_test_divergence": round(train_test_divergence, 4),
                    "aggregate_train_sharpe": round(aggregate_train_sharpe, 4) if aggregate_train_sharpe is not None else None,
                    "aggregate_test_sharpe": round(aggregate_test_sharpe, 4) if aggregate_test_sharpe is not None else None,
                },
            )
        )

    zero_test_folds = [f for f in folds if f.test_trade_count == 0 and f.status != "blocked"]
    if zero_test_folds:
        warnings.append(
            EngineWarning(
                code="wf_zero_test_trades",
                severity="warning",
                message=(
                    f"{len(zero_test_folds)} of {len(folds)} folds produced zero "
                    f"test trades. The strategy may be too restrictive or the test "
                    f"windows too short."
                ),
                details={
                    "fold_indices": [f.fold_index for f in zero_test_folds],
                },
            )
        )

    if valid_test_folds < 3:
        warnings.append(
            EngineWarning(
                code="wf_insufficient_valid_folds",
                severity="warning",
                message=(
                    f"Only {valid_test_folds} of {len(folds)} folds produced valid "
                    f"test Sharpe ratios. Aggregate metrics are unreliable."
                ),
                details={
                    "valid_folds": valid_test_folds,
                    "total_folds": len(folds),
                },
            )
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "Walk-forward complete: %d folds, train_pct=%.2f, verdict=%s, divergence=%s, %.1fms",
        len(folds),
        train_pct,
        stability_verdict,
        f"{train_test_divergence:.3f}" if train_test_divergence is not None else "N/A",
        elapsed_ms,
    )

    return WalkForwardResult(
        folds=folds,
        fold_count=len(folds),
        train_pct=train_pct,
        axes=axes,
        aggregate_train_sharpe=round(aggregate_train_sharpe, 4) if aggregate_train_sharpe is not None else None,
        aggregate_test_sharpe=round(aggregate_test_sharpe, 4) if aggregate_test_sharpe is not None else None,
        train_test_divergence=round(train_test_divergence, 4) if train_test_divergence is not None else None,
        stability_verdict=stability_verdict,
        warnings=warnings,
        execution_time_ms=round(elapsed_ms, 2),
    )
