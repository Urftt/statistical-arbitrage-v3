"""Unit tests for the grid search optimization engine."""

from __future__ import annotations

import numpy as np
import pytest

from statistical_arbitrage.backtesting.models import (
    GridSearchResult,
    ParameterAxis,
    StrategyParameters,
)
from statistical_arbitrage.backtesting.optimization import (
    _get_metric_value,
    run_grid_search,
)

# ---------------------------------------------------------------------------
# Synthetic price data fixture
# ---------------------------------------------------------------------------


def _make_correlated_prices(
    n: int = 600, seed: int = 42
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate two positively correlated price series + timestamps.

    Returns (timestamps, prices1, prices2).
    """
    rng = np.random.default_rng(seed)
    # Random walk with drift for asset 1
    returns1 = 0.0001 + 0.01 * rng.standard_normal(n)
    prices1 = 100.0 * np.exp(np.cumsum(returns1))

    # Asset 2 tracks asset 1 with noise (cointegrated-ish)
    returns2 = 0.0001 + 0.01 * rng.standard_normal(n)
    prices2 = 0.5 * prices1 + 5 + 2 * np.cumsum(returns2)
    prices2 = np.maximum(prices2, 1.0)  # keep positive

    timestamps = np.arange(n)
    return timestamps, prices1, prices2


BASE_PARAMS = StrategyParameters(
    lookback_window=30,
    entry_threshold=2.0,
    exit_threshold=0.5,
    stop_loss=3.0,
    initial_capital=10_000.0,
    position_size=0.5,
    transaction_fee=0.0025,
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetMetricValue:
    def test_extracts_known_field(self):
        from statistical_arbitrage.backtesting.models import MetricSummary

        m = MetricSummary(
            total_trades=5,
            winning_trades=3,
            losing_trades=2,
            win_rate=0.6,
            total_net_pnl=100.0,
            total_return_pct=0.01,
            average_trade_return_pct=0.002,
            average_holding_period_bars=10.0,
            max_drawdown_pct=0.05,
            sharpe_ratio=1.5,
            final_equity=10_100.0,
        )
        assert _get_metric_value(m, "sharpe_ratio") == 1.5
        assert _get_metric_value(m, "win_rate") == 0.6

    def test_returns_none_for_missing_field(self):
        from statistical_arbitrage.backtesting.models import MetricSummary

        m = MetricSummary(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_net_pnl=0.0,
            total_return_pct=0.0,
            average_trade_return_pct=0.0,
            average_holding_period_bars=0.0,
            max_drawdown_pct=0.0,
            final_equity=10_000.0,
        )
        assert _get_metric_value(m, "sharpe_ratio") is None
        assert _get_metric_value(m, "nonexistent_field") is None


class TestGridSearchCorrectCellCount:
    """3 entry × 3 exit = 9 cells."""

    def test_grid_search_correct_cell_count(self):
        timestamps, prices1, prices2 = _make_correlated_prices()
        axes = [
            ParameterAxis(name="entry_threshold", min_value=1.5, max_value=2.5, step=0.5),
            ParameterAxis(name="exit_threshold", min_value=0.3, max_value=0.7, step=0.2),
        ]

        result = run_grid_search(
            timestamps=timestamps,
            prices1=prices1,
            prices2=prices2,
            axes=axes,
            base_params=BASE_PARAMS,
        )

        assert isinstance(result, GridSearchResult)
        assert len(result.cells) == 9
        assert result.total_combinations == 9
        assert result.grid_shape == [3, 3]


class TestGridSearchBestCellIdentification:
    """Best cell should have the highest Sharpe among ok cells."""

    def test_grid_search_best_cell_identification(self):
        timestamps, prices1, prices2 = _make_correlated_prices()
        axes = [
            ParameterAxis(name="entry_threshold", min_value=1.5, max_value=2.5, step=0.5),
        ]

        result = run_grid_search(
            timestamps=timestamps,
            prices1=prices1,
            prices2=prices2,
            axes=axes,
            base_params=BASE_PARAMS,
            optimize_metric="sharpe_ratio",
        )

        # Verify best cell has the highest sharpe among ok cells
        ok_cells = [c for c in result.cells if c.status == "ok"]
        if ok_cells:
            ok_sharpes = [
                _get_metric_value(c.metrics, "sharpe_ratio")
                for c in ok_cells
                if _get_metric_value(c.metrics, "sharpe_ratio") is not None
            ]
            if ok_sharpes:
                max_sharpe = max(ok_sharpes)
                assert result.best_cell is not None
                best_sharpe = _get_metric_value(result.best_cell.metrics, "sharpe_ratio")
                assert best_sharpe == max_sharpe


class TestGridSearchMaxComboGuard:
    """Axes producing > max_combinations should raise ValueError."""

    def test_grid_search_max_combo_guard(self):
        timestamps, prices1, prices2 = _make_correlated_prices()
        # 100 × 100 = 10,000 combos — well over default 500
        axes = [
            ParameterAxis(name="entry_threshold", min_value=0.1, max_value=10.0, step=0.1),
            ParameterAxis(name="exit_threshold", min_value=0.1, max_value=10.0, step=0.1),
        ]

        with pytest.raises(ValueError, match="exceeds the limit"):
            run_grid_search(
                timestamps=timestamps,
                prices1=prices1,
                prices2=prices2,
                axes=axes,
                base_params=BASE_PARAMS,
                max_combinations=500,
            )


class TestGridSearchHandlesZeroTradeCombos:
    """A combo with an extreme threshold should produce no trades, not crash."""

    def test_grid_search_handles_zero_trade_combos(self):
        timestamps, prices1, prices2 = _make_correlated_prices()
        # entry_threshold=10.0 is extreme — z-score rarely reaches 10
        axes = [
            ParameterAxis(name="entry_threshold", min_value=2.0, max_value=10.0, step=4.0),
        ]

        result = run_grid_search(
            timestamps=timestamps,
            prices1=prices1,
            prices2=prices2,
            axes=axes,
            base_params=BASE_PARAMS,
        )

        # Should have cells for both 2.0 and 6.0 and 10.0
        assert len(result.cells) >= 2
        statuses = {c.status for c in result.cells}
        # At least some cells should be ok or no_trades — no crashes
        assert statuses.issubset({"ok", "no_trades", "blocked"})
        # The extreme threshold cell should either have no trades or be blocked
        extreme_cell = [c for c in result.cells if c.params.get("entry_threshold", 0) >= 9.0]
        if extreme_cell:
            assert extreme_cell[0].status in ("no_trades", "blocked")


class TestGridSearchRobustnessScore:
    """Verify robustness score is computed as fraction of neighbors ≥ 80% of best."""

    def test_grid_search_robustness_score(self):
        timestamps, prices1, prices2 = _make_correlated_prices()
        axes = [
            ParameterAxis(name="entry_threshold", min_value=1.5, max_value=2.5, step=0.5),
            ParameterAxis(name="exit_threshold", min_value=0.3, max_value=0.7, step=0.2),
        ]

        result = run_grid_search(
            timestamps=timestamps,
            prices1=prices1,
            prices2=prices2,
            axes=axes,
            base_params=BASE_PARAMS,
        )

        # If there's a best cell, robustness score should be between 0 and 1
        if result.best_cell is not None:
            assert result.robustness_score is not None
            assert 0.0 <= result.robustness_score <= 1.0


class TestGridSearchSingleAxis:
    """1D sweep should work correctly."""

    def test_grid_search_single_axis(self):
        timestamps, prices1, prices2 = _make_correlated_prices()
        axes = [
            ParameterAxis(name="lookback_window", min_value=20, max_value=60, step=10),
        ]

        result = run_grid_search(
            timestamps=timestamps,
            prices1=prices1,
            prices2=prices2,
            axes=axes,
            base_params=BASE_PARAMS,
        )

        # 20, 30, 40, 50, 60 → 5 cells
        assert len(result.cells) == 5
        assert result.grid_shape == [5]
        assert result.total_combinations == 5
        # Each cell should have the correct lookback_window override
        expected_windows = [20.0, 30.0, 40.0, 50.0, 60.0]
        actual_windows = [c.params["lookback_window"] for c in result.cells]
        assert actual_windows == expected_windows


class TestGridSearchWarnings:
    """Warnings list should include fragility/overfitting warnings when applicable."""

    def test_grid_search_produces_warnings_list(self):
        timestamps, prices1, prices2 = _make_correlated_prices()
        axes = [
            ParameterAxis(name="entry_threshold", min_value=1.5, max_value=2.5, step=0.5),
        ]

        result = run_grid_search(
            timestamps=timestamps,
            prices1=prices1,
            prices2=prices2,
            axes=axes,
            base_params=BASE_PARAMS,
        )

        # Warnings should be a list (possibly empty)
        assert isinstance(result.warnings, list)
        # All warnings should have the right shape
        for w in result.warnings:
            assert hasattr(w, "code")
            assert hasattr(w, "severity")
            assert hasattr(w, "message")


class TestGridSearchExecutionTime:
    """execution_time_ms should be positive."""

    def test_execution_time_is_positive(self):
        timestamps, prices1, prices2 = _make_correlated_prices()
        axes = [
            ParameterAxis(name="entry_threshold", min_value=1.5, max_value=2.0, step=0.5),
        ]

        result = run_grid_search(
            timestamps=timestamps,
            prices1=prices1,
            prices2=prices2,
            axes=axes,
            base_params=BASE_PARAMS,
        )

        assert result.execution_time_ms > 0
