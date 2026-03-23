"""Overfitting and fragility detection for backtest results.

Pure functions — no Dash, no IO, no side effects.
"""

from __future__ import annotations

import itertools
from typing import Any

from statistical_arbitrage.backtesting.models import (
    EngineWarning,
    MetricSummary,
    OverfitWarningThresholds,
)

_DEFAULT_THRESHOLDS = OverfitWarningThresholds()


def _warning(code: str, message: str, **details: Any) -> EngineWarning:
    return EngineWarning(
        code=code, severity="warning", message=message, details=details
    )


def detect_overfitting_warnings(
    metrics: MetricSummary,
    trade_count: int,
    thresholds: OverfitWarningThresholds | None = None,
) -> list[EngineWarning]:
    """Screen backtest metrics for suspiciously good results.

    Args:
        metrics: Performance summary from a completed backtest.
        trade_count: Number of completed round-trip trades.
        thresholds: Optional custom thresholds; uses conservative defaults.

    Returns:
        List of structured ``EngineWarning`` objects with ``overfit_*`` codes.
    """
    t = thresholds or _DEFAULT_THRESHOLDS
    warnings: list[EngineWarning] = []

    # 1. Suspiciously high Sharpe ratio
    if metrics.sharpe_ratio is not None and metrics.sharpe_ratio > t.sharpe_threshold:
        warnings.append(
            _warning(
                "overfit_high_sharpe",
                f"Sharpe ratio ({metrics.sharpe_ratio:.2f}) exceeds the "
                f"suspicious threshold ({t.sharpe_threshold:.1f}). In-sample "
                "Sharpe this high rarely survives out-of-sample testing.",
                sharpe_ratio=metrics.sharpe_ratio,
                threshold=t.sharpe_threshold,
            )
        )

    # 2. Suspiciously high profit factor with few trades
    if (
        metrics.profit_factor is not None
        and metrics.profit_factor > t.profit_factor_threshold
        and trade_count < t.profit_factor_min_trades
    ):
        warnings.append(
            _warning(
                "overfit_high_profit_factor",
                f"Profit factor ({metrics.profit_factor:.2f}) looks excellent "
                f"but is based on only {trade_count} trades (threshold: "
                f"{t.profit_factor_min_trades}). Small samples inflate this metric.",
                profit_factor=metrics.profit_factor,
                trade_count=trade_count,
                threshold=t.profit_factor_threshold,
                min_trades=t.profit_factor_min_trades,
            )
        )

    # 3. Suspiciously high win rate with few trades
    if (
        metrics.win_rate > t.winrate_threshold
        and trade_count < t.winrate_min_trades
    ):
        warnings.append(
            _warning(
                "overfit_high_winrate",
                f"Win rate ({metrics.win_rate:.0%}) with only {trade_count} "
                f"trades (threshold: {t.winrate_min_trades}). Small samples "
                "easily produce misleadingly high win rates.",
                win_rate=metrics.win_rate,
                trade_count=trade_count,
                threshold=t.winrate_threshold,
                min_trades=t.winrate_min_trades,
            )
        )

    # 4. Suspiciously smooth equity curve (low drawdown + high Sharpe)
    if (
        metrics.max_drawdown_pct < t.smooth_equity_max_drawdown
        and metrics.sharpe_ratio is not None
        and metrics.sharpe_ratio > t.smooth_equity_min_sharpe
    ):
        warnings.append(
            _warning(
                "overfit_smooth_equity",
                f"Equity curve looks suspiciously smooth: max drawdown "
                f"({metrics.max_drawdown_pct:.4f}) with Sharpe "
                f"({metrics.sharpe_ratio:.2f}). Real markets produce rougher "
                "equity curves — this pattern often signals curve-fitting.",
                max_drawdown_pct=metrics.max_drawdown_pct,
                sharpe_ratio=metrics.sharpe_ratio,
                drawdown_threshold=t.smooth_equity_max_drawdown,
                sharpe_threshold=t.smooth_equity_min_sharpe,
            )
        )

    return warnings


def detect_fragility(
    cells: list[dict[str, Any]],
    best_index: int,
    grid_shape: tuple[int, ...],
) -> list[EngineWarning]:
    """Detect when the best grid-search cell is surrounded by poor neighbors.

    A "fragile" best cell is one whose neighbors mostly have < 50% of its
    primary metric, suggesting the optimum is a narrow spike rather than a
    robust plateau.

    Args:
        cells: Flat list of per-cell metric dicts. Each must have a ``metric``
            key with the primary optimization metric value (or ``None`` for
            failed cells).
        best_index: Index into *cells* of the best-performing cell.
        grid_shape: Shape of the n-dimensional parameter grid (e.g. ``(5, 4)``
            for a 5×4 grid). ``prod(grid_shape)`` must equal ``len(cells)``.

    Returns:
        List containing at most one ``fragile_best_cell`` warning.
    """
    if not cells or best_index < 0 or best_index >= len(cells):
        return []

    best_metric = cells[best_index].get("metric")
    if best_metric is None or best_metric <= 0:
        return []

    # Convert flat index → n-dimensional coordinate
    ndim = len(grid_shape)
    best_coords = _flat_to_nd(best_index, grid_shape)

    # Generate all neighbor offsets (exclude the origin)
    offsets = list(itertools.product([-1, 0, 1], repeat=ndim))
    offsets = [o for o in offsets if any(d != 0 for d in o)]

    poor_count = 0
    neighbor_count = 0

    for offset in offsets:
        neighbor_coords = tuple(b + o for b, o in zip(best_coords, offset))
        # Skip out-of-bounds neighbors (edge cells)
        if any(c < 0 or c >= s for c, s in zip(neighbor_coords, grid_shape)):
            continue

        neighbor_flat = _nd_to_flat(neighbor_coords, grid_shape)
        neighbor_count += 1

        neighbor_metric = cells[neighbor_flat].get("metric")
        if neighbor_metric is None or neighbor_metric <= 0:
            poor_count += 1
        elif neighbor_metric < 0.5 * best_metric:
            poor_count += 1

    if neighbor_count == 0:
        return []

    poor_ratio = poor_count / neighbor_count
    if poor_ratio > 0.5:
        return [
            _warning(
                "fragile_best_cell",
                f"The best parameter combination is fragile: "
                f"{poor_count}/{neighbor_count} neighboring cells perform "
                f"at less than 50% of its metric. This suggests the optimum "
                f"is a narrow spike rather than a robust region.",
                poor_neighbors=poor_count,
                total_neighbors=neighbor_count,
                poor_ratio=round(poor_ratio, 3),
                best_metric=best_metric,
            )
        ]

    return []


def _flat_to_nd(flat_index: int, shape: tuple[int, ...]) -> tuple[int, ...]:
    """Convert a flat index to n-dimensional coordinates (row-major)."""
    coords: list[int] = []
    remaining = flat_index
    for dim_size in reversed(shape):
        coords.append(remaining % dim_size)
        remaining //= dim_size
    return tuple(reversed(coords))


def _nd_to_flat(coords: tuple[int, ...], shape: tuple[int, ...]) -> int:
    """Convert n-dimensional coordinates to a flat index (row-major)."""
    flat = 0
    stride = 1
    for c, s in zip(reversed(coords), reversed(shape)):
        flat += c * stride
        stride *= s
    return flat
