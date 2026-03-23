"""API contract tests for all 8 research modules."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.schemas import BacktestRequest

client = TestClient(app)
PAIR = {
    "asset1": "ETH/EUR",
    "asset2": "ETC/EUR",
    "timeframe": "1h",
    "days_back": 365,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_envelope(data: dict, module: str, *, has_backtest: bool) -> None:
    """Verify the standard research response envelope."""
    assert data["module"] == module
    assert data["asset1"] == PAIR["asset1"]
    assert data["asset2"] == PAIR["asset2"]
    assert data["observations"] > 0
    assert isinstance(data["results"], list)
    assert len(data["results"]) > 0
    assert data["takeaway"]["text"]
    assert data["takeaway"]["severity"] in {"green", "yellow", "red"}
    if has_backtest:
        assert data["recommended_backtest_params"] is not None
        rec = data["recommended_backtest_params"]
        assert rec["asset1"] == PAIR["asset1"]
        assert "strategy" in rec
    else:
        assert data["recommended_backtest_params"] is None


# ---------------------------------------------------------------------------
# Existing: Lookback Window (regression guard)
# ---------------------------------------------------------------------------


class TestLookbackWindowEndpoint:
    def test_lookback_window_returns_200_with_envelope(self):
        resp = client.post("/api/research/lookback-window", json=PAIR)
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "lookback_window"
        assert data["asset1"] == PAIR["asset1"]
        assert data["observations"] > 0
        assert len(data["results"]) > 0
        assert data["takeaway"]["severity"] in {"green", "yellow", "red"}
        assert data["recommended_backtest_params"] is not None
        # Recommendation round-trips as a valid BacktestRequest
        BacktestRequest.model_validate(data["recommended_backtest_params"])


# ---------------------------------------------------------------------------
# 1. Rolling Stability (diagnostic)
# ---------------------------------------------------------------------------


class TestRollingStabilityEndpoint:
    def test_rolling_stability_returns_200_with_envelope(self):
        resp = client.post("/api/research/rolling-stability", json=PAIR)
        assert resp.status_code == 200
        data = resp.json()
        _assert_envelope(data, "rolling_stability", has_backtest=False)
        # Check result row shape
        row = data["results"][0]
        assert "timestamp" in row
        assert "p_value" in row
        assert "is_cointegrated" in row


# ---------------------------------------------------------------------------
# 2. Out-of-Sample Validation (diagnostic)
# ---------------------------------------------------------------------------


class TestOOSValidationEndpoint:
    def test_oos_validation_returns_200_with_envelope(self):
        resp = client.post("/api/research/oos-validation", json=PAIR)
        assert resp.status_code == 200
        data = resp.json()
        _assert_envelope(data, "oos_validation", has_backtest=False)
        row = data["results"][0]
        assert "formation_p_value" in row
        assert "trading_p_value" in row
        assert "split_ratio" in row


# ---------------------------------------------------------------------------
# 3. Timeframe Comparison (diagnostic)
# ---------------------------------------------------------------------------


class TestTimeframeComparisonEndpoint:
    def test_timeframe_comparison_returns_200_with_envelope(self):
        # Timeframe module has no timeframe in request — uses asset1/asset2/days_back
        payload = {"asset1": PAIR["asset1"], "asset2": PAIR["asset2"], "days_back": 365}
        resp = client.post("/api/research/timeframe-comparison", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "timeframe_comparison"
        assert data["asset1"] == PAIR["asset1"]
        assert data["timeframe"] == "multi"
        assert isinstance(data["results"], list)
        assert len(data["results"]) > 0
        assert data["takeaway"]["severity"] in {"green", "yellow", "red"}
        assert data["recommended_backtest_params"] is None
        row = data["results"][0]
        assert "timeframe" in row
        assert "n_datapoints" in row


# ---------------------------------------------------------------------------
# 4. Spread Method Comparison (diagnostic)
# ---------------------------------------------------------------------------


class TestSpreadMethodEndpoint:
    def test_spread_method_returns_200_with_envelope(self):
        resp = client.post("/api/research/spread-method", json=PAIR)
        assert resp.status_code == 200
        data = resp.json()
        _assert_envelope(data, "spread_method", has_backtest=False)
        row = data["results"][0]
        assert "method" in row
        assert "adf_statistic" in row
        assert "adf_p_value" in row
        # Verify that the raw spread array is NOT in the payload
        assert "spread" not in row


# ---------------------------------------------------------------------------
# 5. Z-score Threshold Sweep (backtest handoff)
# ---------------------------------------------------------------------------


class TestZScoreThresholdEndpoint:
    def test_zscore_threshold_returns_200_with_backtest_params(self):
        resp = client.post("/api/research/zscore-threshold", json=PAIR)
        assert resp.status_code == 200
        data = resp.json()
        _assert_envelope(data, "zscore_threshold", has_backtest=True)
        row = data["results"][0]
        assert "entry" in row
        assert "exit" in row
        assert "total_trades" in row
        # Recommended params have entry/exit thresholds
        rec = data["recommended_backtest_params"]
        assert rec["strategy"]["entry_threshold"] > 0
        assert rec["strategy"]["exit_threshold"] >= 0
        BacktestRequest.model_validate(rec)


# ---------------------------------------------------------------------------
# 6. Transaction Cost Analysis (backtest handoff)
# ---------------------------------------------------------------------------


class TestTxCostEndpoint:
    def test_tx_cost_returns_200_with_backtest_params(self):
        resp = client.post("/api/research/tx-cost", json=PAIR)
        assert resp.status_code == 200
        data = resp.json()
        _assert_envelope(data, "tx_cost", has_backtest=True)
        row = data["results"][0]
        assert "fee_pct" in row
        assert "round_trip_pct" in row
        assert "total_trades" in row
        # Always returns backtest params with Bitvavo fee
        rec = data["recommended_backtest_params"]
        assert rec["strategy"]["transaction_fee"] == 0.0025
        BacktestRequest.model_validate(rec)


# ---------------------------------------------------------------------------
# 7. Cointegration Method Comparison (diagnostic)
# ---------------------------------------------------------------------------


class TestCointMethodEndpoint:
    def test_coint_method_returns_200_with_envelope(self):
        resp = client.post("/api/research/coint-method", json=PAIR)
        assert resp.status_code == 200
        data = resp.json()
        _assert_envelope(data, "coint_method", has_backtest=False)
        row = data["results"][0]
        assert "method" in row
        assert "is_cointegrated" in row
        assert "statistic" in row
        assert "detail" in row
