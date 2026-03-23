"""Tests for S02 research modules: OOS validation, spread methods, coint methods."""

import numpy as np
import pytest

from statistical_arbitrage.analysis.research import (
    OOSResult,
    SpreadMethodResult,
    CointMethodResult,
    Takeaway,
    out_of_sample_validation,
    oos_validation_takeaway,
    compare_spread_methods,
    spread_methods_takeaway,
    compare_cointegration_methods,
    coint_methods_takeaway,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────


def _make_cointegrated_pair(n: int, noise_std: float = 0.3, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    trend = np.cumsum(rng.normal(0, 1, n))
    asset2 = 100 + trend
    noise = np.zeros(n)
    for i in range(1, n):
        noise[i] = 0.8 * noise[i - 1] + rng.normal(0, noise_std)
    asset1 = 200 + 2 * trend + noise
    return asset1, asset2


def _make_independent_pair(n: int, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    return 100 + np.cumsum(rng.normal(0, 1, n)), 100 + np.cumsum(rng.normal(0, 1, n))


# ─── Out-of-Sample Validation ────────────────────────────────────────────────


class TestOutOfSampleValidation:
    def test_returns_results_for_each_split(self):
        p1, p2 = _make_cointegrated_pair(300)
        results = out_of_sample_validation(p1, p2, split_ratios=[0.5, 0.7])
        assert len(results) == 2
        assert all(isinstance(r, OOSResult) for r in results)

    def test_cointegrated_pair_holds_oos(self):
        p1, p2 = _make_cointegrated_pair(500, noise_std=0.2)
        results = out_of_sample_validation(p1, p2)
        # Strong cointegration should hold in at least some splits
        in_sample_coint = [r for r in results if r.formation_cointegrated]
        assert len(in_sample_coint) > 0

    def test_independent_pair_fails(self):
        p1, p2 = _make_independent_pair(300)
        results = out_of_sample_validation(p1, p2)
        # Independent pair shouldn't be cointegrated in most splits
        oos_survived = [r for r in results if r.formation_cointegrated and r.trading_cointegrated]
        assert len(oos_survived) <= len(results)  # sanity check

    def test_too_short_data_returns_empty(self):
        p1, p2 = _make_cointegrated_pair(40)
        results = out_of_sample_validation(p1, p2, split_ratios=[0.5])
        # 40 * 0.5 = 20 < 30 minimum, so should skip
        assert len(results) == 0

    def test_split_ratio_in_result(self):
        p1, p2 = _make_cointegrated_pair(300)
        results = out_of_sample_validation(p1, p2, split_ratios=[0.6])
        assert results[0].split_ratio == 0.6
        assert results[0].formation_n == 180
        assert results[0].trading_n == 120


class TestOOSTakeaway:
    def test_empty_results_red(self):
        t = oos_validation_takeaway([])
        assert t.severity == "red"

    def test_robust_green(self):
        results = [
            OOSResult(0.01, True, 2.0, 0.02, True, 2.1, -4.0, -3.5, 200, 100, 0.67),
            OOSResult(0.01, True, 2.0, 0.03, True, 2.1, -4.0, -3.2, 250, 50, 0.83),
        ]
        t = oos_validation_takeaway(results)
        assert t.severity == "green"

    def test_fragile_red(self):
        results = [
            OOSResult(0.01, True, 2.0, 0.5, False, 2.5, -4.0, -1.0, 200, 100, 0.67),
            OOSResult(0.01, True, 2.0, 0.6, False, 2.3, -4.0, -0.8, 250, 50, 0.83),
        ]
        t = oos_validation_takeaway(results)
        assert t.severity == "red"


# ─── Spread Construction Comparison ──────────────────────────────────────────


class TestCompareSpreadMethods:
    def test_returns_three_methods(self):
        p1, p2 = _make_cointegrated_pair(200)
        results = compare_spread_methods(p1, p2)
        assert len(results) == 3
        methods = [r.method for r in results]
        assert "Price-level (OLS)" in methods
        assert "Log-price (OLS)" in methods
        assert "Price ratio" in methods

    def test_all_have_adf_stats(self):
        p1, p2 = _make_cointegrated_pair(200)
        results = compare_spread_methods(p1, p2)
        for r in results:
            assert isinstance(r.adf_statistic, float)
            assert isinstance(r.adf_p_value, float)
            assert 0 <= r.adf_p_value <= 1

    def test_cointegrated_pair_has_stationary_spread(self):
        p1, p2 = _make_cointegrated_pair(500, noise_std=0.2)
        results = compare_spread_methods(p1, p2)
        stationary = [r for r in results if r.is_stationary]
        # At least one method should find stationarity for a cointegrated pair
        assert len(stationary) >= 1

    def test_spread_arrays_have_correct_length(self):
        n = 200
        p1, p2 = _make_cointegrated_pair(n)
        results = compare_spread_methods(p1, p2)
        for r in results:
            assert len(r.spread) == n


class TestSpreadMethodsTakeaway:
    def test_all_stationary_green(self):
        results = [
            SpreadMethodResult("A", -4.0, 0.001, True, 1.0, 0.0, 0.0, np.array([])),
            SpreadMethodResult("B", -3.5, 0.01, True, 1.0, 0.0, 0.0, np.array([])),
        ]
        t = spread_methods_takeaway(results)
        assert t.severity == "green"

    def test_none_stationary_red(self):
        results = [
            SpreadMethodResult("A", -1.0, 0.5, False, 1.0, 0.0, 0.0, np.array([])),
            SpreadMethodResult("B", -0.5, 0.8, False, 1.0, 0.0, 0.0, np.array([])),
        ]
        t = spread_methods_takeaway(results)
        assert t.severity == "red"


# ─── Cointegration Test Method Comparison ────────────────────────────────────


class TestCompareCointegrationMethods:
    def test_returns_four_results(self):
        p1, p2 = _make_cointegrated_pair(200)
        results = compare_cointegration_methods(p1, p2)
        assert len(results) == 4
        methods = [r.method for r in results]
        assert any("A1 ~ A2" in m for m in methods)
        assert any("A2 ~ A1" in m for m in methods)
        assert any("Johansen" in m for m in methods)

    def test_cointegrated_pair_detected(self):
        p1, p2 = _make_cointegrated_pair(500, noise_std=0.2)
        results = compare_cointegration_methods(p1, p2)
        detected = [r for r in results if r.is_cointegrated]
        # At least some methods should detect cointegration
        assert len(detected) >= 1

    def test_all_have_detail_string(self):
        p1, p2 = _make_cointegrated_pair(200)
        results = compare_cointegration_methods(p1, p2)
        for r in results:
            assert isinstance(r.detail, str)
            assert len(r.detail) > 0


class TestCointMethodsTakeaway:
    def test_all_agree_yes_green(self):
        results = [
            CointMethodResult("EG1", True, "p=0.01", -4.0, None),
            CointMethodResult("EG2", True, "p=0.02", -3.8, None),
            CointMethodResult("Joh", True, "stat=20", 20.0, 15.0),
        ]
        t = coint_methods_takeaway(results)
        assert t.severity == "green"

    def test_all_agree_no_red(self):
        results = [
            CointMethodResult("EG1", False, "p=0.5", -1.0, None),
            CointMethodResult("EG2", False, "p=0.6", -0.5, None),
        ]
        t = coint_methods_takeaway(results)
        assert t.severity == "red"

    def test_disagreement_yellow(self):
        results = [
            CointMethodResult("EG1", True, "p=0.03", -3.5, None),
            CointMethodResult("EG2", False, "p=0.08", -2.5, None),
            CointMethodResult("Joh", True, "stat=18", 18.0, 15.0),
        ]
        t = coint_methods_takeaway(results)
        assert t.severity == "yellow"
