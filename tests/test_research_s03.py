"""Tests for S03 research modules: timeframe, z-score threshold, lookback window."""

import numpy as np
import pytest

from statistical_arbitrage.analysis.research import (
    TimeframeResult,
    ThresholdResult,
    LookbackResult,
    compare_timeframes,
    timeframe_takeaway,
    sweep_zscore_thresholds,
    zscore_threshold_takeaway,
    sweep_lookback_windows,
    lookback_window_takeaway,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────


def _make_cointegrated_pair(n: int, seed: int = 42):
    rng = np.random.default_rng(seed)
    trend = np.cumsum(rng.normal(0, 1, n))
    asset2 = 100 + trend
    noise = np.zeros(n)
    for i in range(1, n):
        noise[i] = 0.8 * noise[i - 1] + rng.normal(0, 0.3)
    asset1 = 200 + 2 * trend + noise
    return asset1, asset2


# ─── Timeframe ───────────────────────────────────────────────────────────────


class TestCompareTimeframes:
    def test_returns_results_for_each_timeframe(self):
        import polars as pl
        p1, p2 = _make_cointegrated_pair(200)

        def mock_get(a1, a2, tf):
            return pl.DataFrame({"c1": p1, "c2": p2})

        results = compare_timeframes(mock_get, "A", "B", timeframes=["1h", "4h"])
        assert len(results) == 2
        assert all(isinstance(r, TimeframeResult) for r in results)

    def test_handles_none_return(self):
        def mock_get(a1, a2, tf):
            return None

        results = compare_timeframes(mock_get, "A", "B", timeframes=["1h"])
        assert len(results) == 1
        assert results[0].p_value is None


class TestTimeframeTakeaway:
    def test_all_cointegrated_green(self):
        results = [
            TimeframeResult("1h", 0.01, True, 2.0, 30.0, 200, -4.0),
            TimeframeResult("4h", 0.02, True, 2.1, 35.0, 100, -3.5),
        ]
        t = timeframe_takeaway(results)
        assert t.severity == "green"

    def test_none_cointegrated_red(self):
        results = [
            TimeframeResult("1h", 0.5, False, 2.0, None, 200, -1.0),
        ]
        t = timeframe_takeaway(results)
        assert t.severity == "red"

    def test_no_data_red(self):
        results = [TimeframeResult("1h", None, False, None, None, 0, None)]
        t = timeframe_takeaway(results)
        assert t.severity == "red"


# ─── Z-score Threshold ───────────────────────────────────────────────────────


class TestSweepZscoreThresholds:
    def test_returns_results(self):
        zscore = np.sin(np.linspace(0, 20, 500)) * 3  # oscillating signal
        results = sweep_zscore_thresholds(zscore)
        assert len(results) > 0
        assert all(isinstance(r, ThresholdResult) for r in results)

    def test_nan_handling(self):
        zscore = np.array([np.nan] * 10 + list(np.sin(np.linspace(0, 20, 200)) * 3))
        results = sweep_zscore_thresholds(zscore)
        assert len(results) > 0

    def test_empty_zscore(self):
        results = sweep_zscore_thresholds(np.array([np.nan, np.nan]))
        assert len(results) == 0

    def test_strong_signal_has_trades(self):
        zscore = np.sin(np.linspace(0, 40, 1000)) * 3
        results = sweep_zscore_thresholds(zscore)
        with_trades = [r for r in results if r.total_trades > 0]
        assert len(with_trades) > 0


class TestZscoreThresholdTakeaway:
    def test_no_trades_red(self):
        results = [ThresholdResult(2.0, 0.5, 0, None, None)]
        t = zscore_threshold_takeaway(results)
        assert t.severity == "red"

    def test_many_trades_green(self):
        results = [ThresholdResult(2.0, 0.5, 15, 50.0, 100)]
        t = zscore_threshold_takeaway(results)
        assert t.severity == "green"


# ─── Lookback Window ─────────────────────────────────────────────────────────


class TestSweepLookbackWindows:
    def test_returns_results(self):
        spread = np.cumsum(np.random.default_rng(42).normal(0, 1, 300))
        results = sweep_lookback_windows(spread)
        assert len(results) > 0
        assert all(isinstance(r, LookbackResult) for r in results)

    def test_short_data_skips_large_windows(self):
        spread = np.random.default_rng(42).normal(0, 1, 50)
        results = sweep_lookback_windows(spread, windows=[10, 20, 100, 200])
        windows_tested = [r.window for r in results]
        assert 200 not in windows_tested
        assert 10 in windows_tested


class TestLookbackWindowTakeaway:
    def test_no_results_red(self):
        t = lookback_window_takeaway([])
        assert t.severity == "red"

    def test_good_results_include_window_in_text(self):
        results = [LookbackResult(60, 10, 0.95, 0.1, 0.5, 1.0)]
        t = lookback_window_takeaway(results)
        assert "60" in t.text
