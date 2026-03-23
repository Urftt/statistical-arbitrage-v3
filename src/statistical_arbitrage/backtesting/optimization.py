"""Bounded multi-parameter grid search over the backtest engine.

Pure-Python orchestration layer — no Dash, no IO beyond ``run_backtest()``.
Walk-forward (T03) will call ``run_grid_search()`` for train-window optimization.
"""

from __future__ import annotations

import itertools
import logging
import time
from collections.abc import Sequence
from typing import Any

import numpy as np
import polars as pl

from statistical_arbitrage.backtesting.engine import run_backtest
from statistical_arbitrage.backtesting.models import (
    EngineWarning,
    GridSearchCell,
    GridSearchResult,
    MetricSummary,
    ParameterAxis,
    StrategyParameters,
)
from statistical_arbitrage.backtesting.overfitting import (
    detect_fragility,
    detect_overfitting_warnings,
)

logger = logging.getLogger(__name__)


def _get_metric_value(metrics: MetricSummary, metric_name: str) -> float | None:
    """Extract a named metric field from a MetricSummary.

    Returns ``None`` when the field does not exist or its value is ``None``.
    """
    value = getattr(metrics, metric_name, None)
    if value is None:
        return None
    return float(value)


def _build_axis_values(axis: ParameterAxis) -> list[float]:
    """Generate the discrete values for one axis using numpy.arange."""
    values = np.arange(axis.min_value, axis.max_value + axis.step / 2, axis.step)
    return [round(float(v), 10) for v in values]


def run_grid_search(
    timestamps: Sequence[Any] | np.ndarray | pl.Series,
    prices1: Sequence[Any] | np.ndarray | pl.Series,
    prices2: Sequence[Any] | np.ndarray | pl.Series,
    axes: list[ParameterAxis],
    base_params: StrategyParameters,
    optimize_metric: str = "sharpe_ratio",
    max_combinations: int = 500,
) -> GridSearchResult:
    """Run a bounded grid search over strategy parameters.

    For each combination of axis values, runs ``run_backtest()`` and collects
    the result into a flat cell list. Identifies the best cell by the optimize
    metric, computes a robustness score, and applies fragility + overfitting
    detection.

    Args:
        timestamps: Aligned timestamp series for the pair.
        prices1: Close prices for asset 1.
        prices2: Close prices for asset 2.
        axes: Parameter axes to sweep.
        base_params: Base strategy parameters — axis fields are overridden per cell.
        optimize_metric: ``MetricSummary`` field name to maximize (default: ``sharpe_ratio``).
        max_combinations: Hard limit on total parameter combinations.

    Returns:
        ``GridSearchResult`` with all cells, best cell, robustness score, and warnings.

    Raises:
        ValueError: When total combinations exceed ``max_combinations``.
    """
    start_time = time.perf_counter()

    # (a) Generate per-axis values and compute grid shape
    axis_values: list[list[float]] = [_build_axis_values(ax) for ax in axes]
    grid_shape = [len(vals) for vals in axis_values]
    total_combinations = 1
    for size in grid_shape:
        total_combinations *= size

    # (b) Guard against runaway computation
    if total_combinations > max_combinations:
        raise ValueError(
            f"Grid search would produce {total_combinations} combinations, "
            f"which exceeds the limit of {max_combinations}. Reduce axis ranges "
            f"or increase step sizes."
        )

    # (c) Sweep all combinations
    cells: list[GridSearchCell] = []
    for combo in itertools.product(*axis_values):
        # Build per-cell params by overriding the axis fields
        overrides: dict[str, float] = {}
        for axis, value in zip(axes, combo):
            overrides[axis.name] = value

        cell_params = base_params.model_copy(update=overrides)

        try:
            result = run_backtest(
                timestamps=timestamps,
                asset1_prices=prices1,
                asset2_prices=prices2,
                params=cell_params,
            )
        except Exception:
            logger.exception("Grid cell %s failed", overrides)
            # Treat unexpected failures as blocked
            cells.append(
                GridSearchCell(
                    params=overrides,
                    metrics=MetricSummary(
                        total_trades=0,
                        winning_trades=0,
                        losing_trades=0,
                        win_rate=0.0,
                        total_net_pnl=0.0,
                        total_return_pct=0.0,
                        average_trade_return_pct=0.0,
                        average_holding_period_bars=0.0,
                        max_drawdown_pct=0.0,
                        final_equity=base_params.initial_capital,
                    ),
                    trade_count=0,
                    status="blocked",
                )
            )
            continue

        if result.status == "blocked":
            status = "blocked"
        elif result.metrics.total_trades == 0:
            status = "no_trades"
        else:
            status = "ok"

        cells.append(
            GridSearchCell(
                params=overrides,
                metrics=result.metrics,
                trade_count=result.metrics.total_trades,
                status=status,
            )
        )

    # (e) Find the best cell by optimize_metric
    best_cell_index: int | None = None
    best_metric_value: float | None = None

    for i, cell in enumerate(cells):
        if cell.status not in ("ok",):
            continue
        metric_val = _get_metric_value(cell.metrics, optimize_metric)
        if metric_val is None:
            continue
        if best_metric_value is None or metric_val > best_metric_value:
            best_metric_value = metric_val
            best_cell_index = i

    best_cell = cells[best_cell_index] if best_cell_index is not None else None
    warnings: list[EngineWarning] = []

    # (f) Robustness score + fragility detection
    robustness_score: float | None = None
    if best_cell_index is not None and best_metric_value is not None:
        # Robustness: fraction of neighbors within 80% of best metric
        robustness_score = _compute_robustness(
            cells, best_cell_index, tuple(grid_shape), optimize_metric, best_metric_value
        )

        # Fragility detection from T01
        fragility_cells = [
            {"metric": _get_metric_value(c.metrics, optimize_metric)}
            for c in cells
        ]
        fragility_warnings = detect_fragility(
            cells=fragility_cells,
            best_index=best_cell_index,
            grid_shape=tuple(grid_shape),
        )
        warnings.extend(fragility_warnings)

        # (g) Overfitting warnings on best cell
        overfit_warnings = detect_overfitting_warnings(
            metrics=best_cell.metrics,
            trade_count=best_cell.trade_count,
        )
        warnings.extend(overfit_warnings)

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "Grid search complete: %d combinations, best_index=%s, robustness=%.3f, %.1fms",
        total_combinations,
        best_cell_index,
        robustness_score or 0.0,
        elapsed_ms,
    )

    return GridSearchResult(
        cells=cells,
        grid_shape=grid_shape,
        axes=axes,
        best_cell_index=best_cell_index,
        best_cell=best_cell,
        optimize_metric=optimize_metric,
        total_combinations=total_combinations,
        robustness_score=robustness_score,
        warnings=warnings,
        execution_time_ms=round(elapsed_ms, 2),
    )


def _compute_robustness(
    cells: list[GridSearchCell],
    best_index: int,
    grid_shape: tuple[int, ...],
    optimize_metric: str,
    best_metric_value: float,
) -> float:
    """Fraction of immediate neighbors whose metric is ≥ 80% of the best."""
    from statistical_arbitrage.backtesting.overfitting import _flat_to_nd, _nd_to_flat

    ndim = len(grid_shape)
    best_coords = _flat_to_nd(best_index, grid_shape)

    offsets = list(itertools.product([-1, 0, 1], repeat=ndim))
    offsets = [o for o in offsets if any(d != 0 for d in o)]

    good_count = 0
    neighbor_count = 0

    threshold = 0.8 * best_metric_value

    for offset in offsets:
        neighbor_coords = tuple(b + o for b, o in zip(best_coords, offset))
        if any(c < 0 or c >= s for c, s in zip(neighbor_coords, grid_shape)):
            continue

        neighbor_flat = _nd_to_flat(neighbor_coords, grid_shape)
        neighbor_count += 1

        cell = cells[neighbor_flat]
        metric_val = _get_metric_value(cell.metrics, optimize_metric)
        if metric_val is not None and metric_val >= threshold:
            good_count += 1

    if neighbor_count == 0:
        return 1.0  # No neighbors (single cell grid) — trivially robust

    return round(good_count / neighbor_count, 4)
