"""Tests for rolling cointegration analysis functions."""

import numpy as np
import polars as pl
import pytest
from datetime import datetime, timedelta

from statistical_arbitrage.analysis.research import (
    Takeaway,
    rolling_cointegration,
    rolling_cointegration_takeaway,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────


def _make_timestamps(n: int) -> list[datetime]:
    """Generate n hourly timestamps."""
    base = datetime(2025, 1, 1)
    return [base + timedelta(hours=i) for i in range(n)]


def _make_cointegrated_pair(n: int, noise_std: float = 0.5, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a synthetic cointegrated pair.

    asset1 = 2 * asset2 + stationary_noise
    Both share a common random walk (non-stationary trend).
    """
    rng = np.random.default_rng(seed)
    # Common random walk
    trend = np.cumsum(rng.normal(0, 1, n))
    asset2 = 100 + trend
    asset1 = 200 + 2 * trend + np.cumsum(rng.normal(0, noise_std, n)) * 0  # stationary noise
    # Add mean-reverting noise to asset1
    noise = np.zeros(n)
    for i in range(1, n):
        noise[i] = 0.8 * noise[i - 1] + rng.normal(0, noise_std)
    asset1 = asset1 + noise
    return asset1, asset2


def _make_independent_pair(n: int, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Generate two independent random walks (not cointegrated)."""
    rng = np.random.default_rng(seed)
    asset1 = 100 + np.cumsum(rng.normal(0, 1, n))
    asset2 = 100 + np.cumsum(rng.normal(0, 1, n))
    return asset1, asset2


# ─── Tests: rolling_cointegration ────────────────────────────────────────────


class TestRollingCointegration:
    def test_basic_output_shape(self):
        """Result has expected columns and reasonable row count."""
        n = 200
        p1, p2 = _make_cointegrated_pair(n)
        ts = _make_timestamps(n)

        result = rolling_cointegration(p1, p2, ts, window=60, step=1)

        assert isinstance(result, pl.DataFrame)
        assert set(result.columns) == {"timestamp", "p_value", "is_cointegrated", "hedge_ratio", "test_statistic"}
        # With window=60 and step=1, we get n - window rows
        assert result.height == n - 60

    def test_cointegrated_pair_mostly_significant(self):
        """A strongly cointegrated pair should be significant most of the time."""
        n = 300
        p1, p2 = _make_cointegrated_pair(n, noise_std=0.3)
        ts = _make_timestamps(n)

        result = rolling_cointegration(p1, p2, ts, window=90, step=1)
        valid = result.filter(pl.col("p_value").is_not_null())
        cointegrated_pct = valid.filter(pl.col("is_cointegrated") == True).height / valid.height

        # Should be cointegrated at least 50% of the time (synthetic data is strongly coint)
        assert cointegrated_pct >= 0.5, f"Expected >=50% cointegrated, got {cointegrated_pct:.1%}"

    def test_independent_pair_mostly_not_significant(self):
        """Independent random walks should rarely appear cointegrated."""
        n = 300
        p1, p2 = _make_independent_pair(n)
        ts = _make_timestamps(n)

        result = rolling_cointegration(p1, p2, ts, window=90, step=1)
        valid = result.filter(pl.col("p_value").is_not_null())
        cointegrated_pct = valid.filter(pl.col("is_cointegrated") == True).height / valid.height

        # Should be cointegrated less than 30% (some false positives expected)
        assert cointegrated_pct <= 0.30, f"Expected <=30% cointegrated, got {cointegrated_pct:.1%}"

    def test_step_reduces_output_rows(self):
        """Larger step size produces fewer results."""
        n = 200
        p1, p2 = _make_cointegrated_pair(n)
        ts = _make_timestamps(n)

        result_1 = rolling_cointegration(p1, p2, ts, window=60, step=1)
        result_5 = rolling_cointegration(p1, p2, ts, window=60, step=5)

        assert result_5.height < result_1.height
        assert result_5.height == len(range(60, n, 5))

    def test_insufficient_data_raises(self):
        """Window larger than data should raise ValueError."""
        p1, p2 = _make_cointegrated_pair(50)
        ts = _make_timestamps(50)

        with pytest.raises(ValueError, match="Not enough data"):
            rolling_cointegration(p1, p2, ts, window=100)

    def test_length_mismatch_raises(self):
        """Mismatched input lengths should raise ValueError."""
        ts = _make_timestamps(100)
        with pytest.raises(ValueError, match="Length mismatch"):
            rolling_cointegration(np.ones(100), np.ones(90), ts, window=50)

    def test_hedge_ratio_reasonable(self):
        """Hedge ratio for a known 2:1 relationship should be near 2."""
        n = 300
        p1, p2 = _make_cointegrated_pair(n, noise_std=0.2)
        ts = _make_timestamps(n)

        result = rolling_cointegration(p1, p2, ts, window=90, step=10)
        valid = result.filter(pl.col("hedge_ratio").is_not_null())
        median_hr = valid["hedge_ratio"].median()

        # Should be near 2.0 (our synthetic pair has hedge_ratio ~2)
        assert 1.5 < median_hr < 2.5, f"Expected hedge ratio near 2.0, got {median_hr:.2f}"


# ─── Tests: rolling_cointegration_takeaway ───────────────────────────────────


class TestRollingCointegrationTakeaway:
    def test_empty_results(self):
        """Empty DataFrame produces red severity."""
        result = rolling_cointegration_takeaway(pl.DataFrame({
            "timestamp": [],
            "p_value": [],
            "is_cointegrated": [],
            "hedge_ratio": [],
            "test_statistic": [],
        }))
        assert result.severity == "red"

    def test_stable_cointegration_green(self):
        """Mostly cointegrated with few breakdowns → green."""
        n = 100
        result_df = pl.DataFrame({
            "timestamp": _make_timestamps(n),
            "p_value": [0.01] * n,
            "is_cointegrated": [True] * n,
            "hedge_ratio": [2.0] * n,
            "test_statistic": [-4.0] * n,
        })
        takeaway = rolling_cointegration_takeaway(result_df)
        assert takeaway.severity == "green"
        assert "100%" in takeaway.text

    def test_intermittent_cointegration_yellow(self):
        """50-80% cointegrated → yellow."""
        n = 100
        is_coint = [True] * 60 + [False] * 40
        p_vals = [0.01 if c else 0.1 for c in is_coint]
        result_df = pl.DataFrame({
            "timestamp": _make_timestamps(n),
            "p_value": p_vals,
            "is_cointegrated": is_coint,
            "hedge_ratio": [2.0] * n,
            "test_statistic": [-4.0] * n,
        })
        takeaway = rolling_cointegration_takeaway(result_df)
        assert takeaway.severity == "yellow"

    def test_weak_cointegration_red(self):
        """Less than 50% cointegrated → red."""
        n = 100
        is_coint = [True] * 20 + [False] * 80
        p_vals = [0.01 if c else 0.5 for c in is_coint]
        result_df = pl.DataFrame({
            "timestamp": _make_timestamps(n),
            "p_value": p_vals,
            "is_cointegrated": is_coint,
            "hedge_ratio": [2.0] * n,
            "test_statistic": [-4.0] * n,
        })
        takeaway = rolling_cointegration_takeaway(result_df)
        assert takeaway.severity == "red"

    def test_all_null_pvalues_red(self):
        """All null p-values → red."""
        result_df = pl.DataFrame({
            "timestamp": _make_timestamps(5),
            "p_value": [None] * 5,
            "is_cointegrated": [False] * 5,
            "hedge_ratio": [None] * 5,
            "test_statistic": [None] * 5,
        })
        takeaway = rolling_cointegration_takeaway(result_df)
        assert takeaway.severity == "red"

    def test_breakdown_count_in_text(self):
        """Takeaway mentions breakdown count."""
        n = 100
        # Pattern: cointegrated → not → cointegrated → not (2 breakdowns)
        is_coint = [True] * 30 + [False] * 20 + [True] * 30 + [False] * 20
        p_vals = [0.01 if c else 0.1 for c in is_coint]
        result_df = pl.DataFrame({
            "timestamp": _make_timestamps(n),
            "p_value": p_vals,
            "is_cointegrated": is_coint,
            "hedge_ratio": [2.0] * n,
            "test_statistic": [-4.0] * n,
        })
        takeaway = rolling_cointegration_takeaway(result_df)
        assert "2 breakdown" in takeaway.text
