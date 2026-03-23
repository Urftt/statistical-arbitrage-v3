"""Tests for overfitting and fragility detection."""

from __future__ import annotations

import pytest

from statistical_arbitrage.backtesting.models import (
    MetricSummary,
    OverfitWarningThresholds,
)
from statistical_arbitrage.backtesting.overfitting import (
    detect_fragility,
    detect_overfitting_warnings,
)


def _make_metrics(**overrides: object) -> MetricSummary:
    """Build a MetricSummary with sensible defaults, overriding as needed."""
    defaults = dict(
        total_trades=30,
        winning_trades=16,
        losing_trades=14,
        win_rate=0.53,
        total_net_pnl=120.0,
        total_return_pct=0.012,
        average_trade_return_pct=0.004,
        average_holding_period_bars=8.5,
        max_drawdown_pct=0.08,
        profit_factor=1.3,
        sharpe_ratio=1.1,
        sortino_ratio=1.4,
        final_equity=10120.0,
    )
    defaults.update(overrides)
    return MetricSummary(**defaults)


class TestHighSharpe:
    def test_high_sharpe_triggers_warning(self) -> None:
        metrics = _make_metrics(sharpe_ratio=4.5)
        warnings = detect_overfitting_warnings(metrics, trade_count=30)
        codes = [w.code for w in warnings]
        assert "overfit_high_sharpe" in codes
        w = next(w for w in warnings if w.code == "overfit_high_sharpe")
        assert w.details["sharpe_ratio"] == 4.5

    def test_normal_sharpe_no_warning(self) -> None:
        metrics = _make_metrics(sharpe_ratio=2.0)
        warnings = detect_overfitting_warnings(metrics, trade_count=30)
        codes = [w.code for w in warnings]
        assert "overfit_high_sharpe" not in codes

    def test_none_sharpe_no_warning(self) -> None:
        metrics = _make_metrics(sharpe_ratio=None)
        warnings = detect_overfitting_warnings(metrics, trade_count=0)
        codes = [w.code for w in warnings]
        assert "overfit_high_sharpe" not in codes


class TestHighProfitFactor:
    def test_high_profit_factor_with_few_trades(self) -> None:
        metrics = _make_metrics(profit_factor=8.0)
        warnings = detect_overfitting_warnings(metrics, trade_count=10)
        codes = [w.code for w in warnings]
        assert "overfit_high_profit_factor" in codes

    def test_high_profit_factor_with_many_trades_no_warning(self) -> None:
        metrics = _make_metrics(profit_factor=6.0)
        warnings = detect_overfitting_warnings(metrics, trade_count=50)
        codes = [w.code for w in warnings]
        assert "overfit_high_profit_factor" not in codes

    def test_normal_profit_factor_few_trades_no_warning(self) -> None:
        metrics = _make_metrics(profit_factor=2.0)
        warnings = detect_overfitting_warnings(metrics, trade_count=5)
        codes = [w.code for w in warnings]
        assert "overfit_high_profit_factor" not in codes


class TestHighWinrate:
    def test_high_winrate_with_few_trades(self) -> None:
        metrics = _make_metrics(win_rate=0.9, winning_trades=4, losing_trades=1)
        warnings = detect_overfitting_warnings(metrics, trade_count=5)
        codes = [w.code for w in warnings]
        assert "overfit_high_winrate" in codes

    def test_high_winrate_with_many_trades_no_warning(self) -> None:
        metrics = _make_metrics(win_rate=0.9, winning_trades=45, losing_trades=5)
        warnings = detect_overfitting_warnings(metrics, trade_count=50)
        codes = [w.code for w in warnings]
        assert "overfit_high_winrate" not in codes


class TestSmoothEquity:
    def test_smooth_equity_triggers(self) -> None:
        metrics = _make_metrics(max_drawdown_pct=0.005, sharpe_ratio=2.5)
        warnings = detect_overfitting_warnings(metrics, trade_count=30)
        codes = [w.code for w in warnings]
        assert "overfit_smooth_equity" in codes

    def test_normal_drawdown_no_warning(self) -> None:
        metrics = _make_metrics(max_drawdown_pct=0.05, sharpe_ratio=2.5)
        warnings = detect_overfitting_warnings(metrics, trade_count=30)
        codes = [w.code for w in warnings]
        assert "overfit_smooth_equity" not in codes


class TestHealthyMetrics:
    def test_healthy_metrics_no_warnings(self) -> None:
        """Normal, unsuspicious metrics should produce zero overfitting warnings."""
        metrics = _make_metrics()
        warnings = detect_overfitting_warnings(metrics, trade_count=30)
        assert warnings == []


class TestMultipleTriggers:
    def test_multiple_triggers(self) -> None:
        metrics = _make_metrics(
            sharpe_ratio=4.0,
            profit_factor=8.0,
            win_rate=0.95,
            max_drawdown_pct=0.005,
            winning_trades=8,
            losing_trades=2,
        )
        warnings = detect_overfitting_warnings(metrics, trade_count=5)
        codes = {w.code for w in warnings}
        # Should trigger at least 2 of the 4 rules
        assert len(codes) >= 2
        # Specifically: high sharpe, high profit factor, high winrate, smooth equity
        assert "overfit_high_sharpe" in codes
        assert "overfit_high_profit_factor" in codes
        assert "overfit_high_winrate" in codes
        assert "overfit_smooth_equity" in codes


class TestCustomThresholds:
    def test_custom_thresholds(self) -> None:
        """Non-default thresholds should be respected."""
        metrics = _make_metrics(sharpe_ratio=2.5)
        # Default threshold is 3.0 → no warning
        warnings = detect_overfitting_warnings(metrics, trade_count=30)
        assert all(w.code != "overfit_high_sharpe" for w in warnings)

        # Custom threshold is 2.0 → warning fires
        custom = OverfitWarningThresholds(sharpe_threshold=2.0)
        warnings = detect_overfitting_warnings(metrics, trade_count=30, thresholds=custom)
        codes = [w.code for w in warnings]
        assert "overfit_high_sharpe" in codes


class TestFragilityDetection:
    def test_fragility_surrounded_by_poor(self) -> None:
        """Best cell surrounded by poor neighbors → fragile_best_cell."""
        # 3×3 grid, best cell at center (index 4), neighbors all poor
        cells = [
            {"metric": 0.1},  # (0,0)
            {"metric": 0.1},  # (0,1)
            {"metric": 0.1},  # (0,2)
            {"metric": 0.1},  # (1,0)
            {"metric": 5.0},  # (1,1) — best
            {"metric": 0.1},  # (1,2)
            {"metric": 0.1},  # (2,0)
            {"metric": 0.1},  # (2,1)
            {"metric": 0.1},  # (2,2)
        ]
        warnings = detect_fragility(cells, best_index=4, grid_shape=(3, 3))
        codes = [w.code for w in warnings]
        assert "fragile_best_cell" in codes
        w = next(w for w in warnings if w.code == "fragile_best_cell")
        assert w.details["poor_neighbors"] == 8
        assert w.details["total_neighbors"] == 8

    def test_fragility_robust_cell(self) -> None:
        """Best cell with strong neighbors → no warning."""
        cells = [
            {"metric": 4.0},  # (0,0)
            {"metric": 4.5},  # (0,1)
            {"metric": 4.0},  # (0,2)
            {"metric": 4.2},  # (1,0)
            {"metric": 5.0},  # (1,1) — best
            {"metric": 4.8},  # (1,2)
            {"metric": 3.5},  # (2,0)
            {"metric": 4.0},  # (2,1)
            {"metric": 4.1},  # (2,2)
        ]
        warnings = detect_fragility(cells, best_index=4, grid_shape=(3, 3))
        assert warnings == []

    def test_fragility_edge_cell(self) -> None:
        """Best cell on edge should not be penalized for missing neighbors."""
        # 3×3 grid, best at corner (0,0) → only 3 neighbors
        cells = [
            {"metric": 5.0},  # (0,0) — best (corner)
            {"metric": 4.0},  # (0,1)
            {"metric": 3.5},  # (0,2)
            {"metric": 4.5},  # (1,0)
            {"metric": 4.0},  # (1,1)
            {"metric": 3.0},  # (1,2)
            {"metric": 2.0},  # (2,0)
            {"metric": 1.5},  # (2,1)
            {"metric": 1.0},  # (2,2)
        ]
        warnings = detect_fragility(cells, best_index=0, grid_shape=(3, 3))
        # Corner has 3 neighbors: (0,1)=4.0, (1,0)=4.5, (1,1)=4.0
        # All > 50% of 5.0 → robust
        assert warnings == []

    def test_fragility_1d_grid(self) -> None:
        """Fragility detection should work with 1-dimensional grids."""
        cells = [
            {"metric": 0.5},
            {"metric": 0.3},
            {"metric": 10.0},  # best, index 2
            {"metric": 0.2},
            {"metric": 0.1},
        ]
        warnings = detect_fragility(cells, best_index=2, grid_shape=(5,))
        codes = [w.code for w in warnings]
        assert "fragile_best_cell" in codes

    def test_fragility_3d_grid(self) -> None:
        """Fragility detection should work with 3-dimensional grids."""
        # 2×2×2 grid = 8 cells. Best at center-ish index 0.
        cells = [
            {"metric": 10.0},  # (0,0,0) — best
            {"metric": 1.0},   # (0,0,1) — poor
            {"metric": 1.0},   # (0,1,0) — poor
            {"metric": 1.0},   # (0,1,1) — poor
            {"metric": 1.0},   # (1,0,0) — poor
            {"metric": 1.0},   # (1,0,1) — poor
            {"metric": 1.0},   # (1,1,0) — poor
            {"metric": 1.0},   # (1,1,1) — poor
        ]
        warnings = detect_fragility(cells, best_index=0, grid_shape=(2, 2, 2))
        codes = [w.code for w in warnings]
        # Corner of 2×2×2: 3 neighbors, all poor → fragile
        assert "fragile_best_cell" in codes

    def test_fragility_none_metric_treated_as_poor(self) -> None:
        """Cells with None metric are counted as poor neighbors."""
        cells = [
            {"metric": None},
            {"metric": None},
            {"metric": 5.0},  # best
            {"metric": None},
            {"metric": None},
        ]
        warnings = detect_fragility(cells, best_index=2, grid_shape=(5,))
        codes = [w.code for w in warnings]
        assert "fragile_best_cell" in codes

    def test_fragility_empty_cells(self) -> None:
        warnings = detect_fragility([], best_index=0, grid_shape=(0,))
        assert warnings == []

    def test_fragility_invalid_best_index(self) -> None:
        cells = [{"metric": 1.0}]
        warnings = detect_fragility(cells, best_index=5, grid_shape=(1,))
        assert warnings == []
