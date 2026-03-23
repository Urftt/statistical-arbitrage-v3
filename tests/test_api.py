"""Tests for the Statistical Arbitrage API endpoints.

Uses httpx TestClient with the FastAPI app — no live server needed.
"""

import json
import math

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.schemas import numpy_to_python

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert isinstance(data["pairs_cached"], int)
        assert data["pairs_cached"] > 0

    def test_health_cors_header(self):
        resp = client.get(
            "/api/health", headers={"Origin": "http://localhost:3000"}
        )
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "http://localhost:3000"


# ---------------------------------------------------------------------------
# Pairs list endpoint
# ---------------------------------------------------------------------------


class TestPairsList:
    def test_pairs_list_returns_data(self):
        resp = client.get("/api/pairs")
        assert resp.status_code == 200
        data = resp.json()
        assert "pairs" in data
        assert len(data["pairs"]) > 0

    def test_pairs_have_required_fields(self):
        resp = client.get("/api/pairs")
        pair = resp.json()["pairs"][0]
        for field in ("symbol", "base", "quote", "timeframe", "candles", "start", "end", "file_size_mb"):
            assert field in pair, f"Missing field: {field}"

    def test_pairs_symbol_format(self):
        resp = client.get("/api/pairs")
        for pair in resp.json()["pairs"]:
            assert "/" in pair["symbol"], f"Symbol should use slash format: {pair['symbol']}"

    def test_pairs_start_end_are_iso_strings(self):
        resp = client.get("/api/pairs")
        pair = resp.json()["pairs"][0]
        # ISO format check — should contain 'T' separator
        assert "T" in pair["start"]
        assert "T" in pair["end"]


# ---------------------------------------------------------------------------
# OHLCV endpoint
# ---------------------------------------------------------------------------


class TestOHLCV:
    def test_ohlcv_returns_data(self):
        resp = client.get("/api/pairs/ETH-EUR/ohlcv?timeframe=1h")
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "ETH/EUR"
        assert data["timeframe"] == "1h"
        assert data["count"] > 0

    def test_ohlcv_has_all_columns(self):
        resp = client.get("/api/pairs/ETH-EUR/ohlcv?timeframe=1h")
        data = resp.json()
        for col in ("timestamps", "open", "high", "low", "close", "volume"):
            assert col in data, f"Missing column: {col}"
            assert len(data[col]) == data["count"]

    def test_ohlcv_values_are_native_types(self):
        resp = client.get("/api/pairs/ETH-EUR/ohlcv?timeframe=1h&days_back=7")
        data = resp.json()
        assert isinstance(data["timestamps"][0], int)
        assert isinstance(data["open"][0], float)
        assert isinstance(data["volume"][0], float)

    def test_ohlcv_days_back_filter(self):
        resp_short = client.get("/api/pairs/ETH-EUR/ohlcv?timeframe=1h&days_back=7")
        resp_long = client.get("/api/pairs/ETH-EUR/ohlcv?timeframe=1h&days_back=90")
        assert resp_short.json()["count"] < resp_long.json()["count"]

    def test_ohlcv_4h_timeframe(self):
        resp = client.get("/api/pairs/ETH-EUR/ohlcv?timeframe=4h")
        assert resp.status_code == 200
        assert resp.json()["timeframe"] == "4h"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class TestErrors:
    def test_error_invalid_symbol_404(self):
        resp = client.get("/api/pairs/FAKE-COIN/ohlcv?timeframe=1h")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_error_invalid_timeframe_404(self):
        resp = client.get("/api/pairs/ETH-EUR/ohlcv?timeframe=99z")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_error_response_is_json(self):
        resp = client.get("/api/pairs/NONEXISTENT/ohlcv?timeframe=1h")
        assert resp.status_code == 404
        data = resp.json()
        assert isinstance(data["detail"], str)


# ---------------------------------------------------------------------------
# numpy_to_python converter
# ---------------------------------------------------------------------------


class TestNumpyToPython:
    def test_float64(self):
        assert numpy_to_python(np.float64(3.14)) == 3.14
        assert isinstance(numpy_to_python(np.float64(3.14)), float)

    def test_int64(self):
        assert numpy_to_python(np.int64(42)) == 42
        assert isinstance(numpy_to_python(np.int64(42)), int)

    def test_bool_(self):
        assert numpy_to_python(np.bool_(True)) is True
        assert isinstance(numpy_to_python(np.bool_(False)), bool)

    def test_inf_becomes_none(self):
        assert numpy_to_python(np.float64(np.inf)) is None
        assert numpy_to_python(float("inf")) is None

    def test_nan_becomes_none(self):
        assert numpy_to_python(np.float64(np.nan)) is None
        assert numpy_to_python(float("nan")) is None

    def test_ndarray(self):
        arr = np.array([1.0, 2.0, 3.0])
        result = numpy_to_python(arr)
        assert result == [1.0, 2.0, 3.0]
        assert isinstance(result[0], float)

    def test_nested_dict(self):
        data = {
            "score": np.float64(-3.5),
            "critical_values": {
                "1%": np.float64(-3.9),
                "5%": np.float64(-3.4),
            },
            "is_ok": np.bool_(True),
        }
        result = numpy_to_python(data)
        assert result["score"] == -3.5
        assert result["critical_values"]["1%"] == -3.9
        assert result["is_ok"] is True
        # Verify JSON-serializable
        json.dumps(result)

    def test_ndarray_with_nan(self):
        arr = np.array([1.0, np.nan, 3.0])
        result = numpy_to_python(arr)
        assert result == [1.0, None, 3.0]
        json.dumps(result)

    def test_python_types_passthrough(self):
        assert numpy_to_python("hello") == "hello"
        assert numpy_to_python(42) == 42
        assert numpy_to_python(None) is None


# ---------------------------------------------------------------------------
# Cointegration endpoint
# ---------------------------------------------------------------------------


class TestCointegration:
    def test_cointegration_returns_full_results(self):
        resp = client.post(
            "/api/analysis/cointegration",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h"},
        )
        assert resp.status_code == 200
        data = resp.json()

        # All required fields present
        for field in (
            "cointegration_score", "p_value", "critical_values",
            "is_cointegrated", "hedge_ratio", "intercept",
            "spread", "zscore", "half_life", "correlation",
            "spread_stationarity", "spread_properties",
            "interpretation", "timestamps",
        ):
            assert field in data, f"Missing field: {field}"

    def test_cointegration_types_are_native(self):
        resp = client.post(
            "/api/analysis/cointegration",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h"},
        )
        data = resp.json()

        # Scalars are native types
        assert isinstance(data["cointegration_score"], float)
        assert isinstance(data["p_value"], float)
        assert isinstance(data["is_cointegrated"], bool)
        assert isinstance(data["hedge_ratio"], float)
        assert isinstance(data["correlation"], float)

        # Arrays are lists of floats (or None for NaN)
        assert isinstance(data["spread"], list)
        assert isinstance(data["timestamps"], list)
        assert len(data["spread"]) == len(data["timestamps"])
        assert len(data["zscore"]) == len(data["timestamps"])

    def test_cointegration_critical_values_structure(self):
        resp = client.post(
            "/api/analysis/cointegration",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h"},
        )
        cv = resp.json()["critical_values"]
        assert "one_pct" in cv
        assert "five_pct" in cv
        assert "ten_pct" in cv
        assert all(isinstance(cv[k], float) for k in cv)

    def test_cointegration_spread_stationarity_structure(self):
        resp = client.post(
            "/api/analysis/cointegration",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h"},
        )
        ss = resp.json()["spread_stationarity"]
        assert "adf_statistic" in ss
        assert "p_value" in ss
        assert "is_stationary" in ss
        assert isinstance(ss["is_stationary"], bool)

    def test_cointegration_spread_properties_structure(self):
        resp = client.post(
            "/api/analysis/cointegration",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h"},
        )
        sp = resp.json()["spread_properties"]
        for field in ("mean", "std", "min", "max", "median", "skewness", "kurtosis", "autocorr_lag1"):
            assert field in sp, f"Missing spread_properties field: {field}"
            assert isinstance(sp[field], (float, int, type(None)))

    def test_cointegration_json_serializable(self):
        """Response must be fully JSON-serializable (no numpy types)."""
        resp = client.post(
            "/api/analysis/cointegration",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h"},
        )
        # json.loads succeeds without TypeError
        json.loads(resp.text)

    def test_cointegration_half_life_type(self):
        resp = client.post(
            "/api/analysis/cointegration",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h"},
        )
        data = resp.json()
        # half_life is either a float or null
        assert data["half_life"] is None or isinstance(data["half_life"], float)
        # If null, half_life_note explains why
        if data["half_life"] is None:
            assert data["half_life_note"] is not None
            assert "infinite" in data["half_life_note"].lower() or "no mean reversion" in data["half_life_note"].lower()

    def test_cointegration_days_back(self):
        resp_short = client.post(
            "/api/analysis/cointegration",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h", "days_back": 30},
        )
        resp_long = client.post(
            "/api/analysis/cointegration",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h", "days_back": 90},
        )
        assert resp_short.status_code == 200
        assert resp_long.status_code == 200
        assert len(resp_short.json()["timestamps"]) < len(resp_long.json()["timestamps"])


# ---------------------------------------------------------------------------
# Spread endpoint
# ---------------------------------------------------------------------------


class TestSpread:
    def test_spread_ols(self):
        resp = client.post(
            "/api/analysis/spread",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h", "method": "ols"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["method"] == "ols"
        assert isinstance(data["spread"], list)
        assert len(data["spread"]) == len(data["timestamps"])

    def test_spread_ratio(self):
        resp = client.post(
            "/api/analysis/spread",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h", "method": "ratio"},
        )
        assert resp.status_code == 200
        assert resp.json()["method"] == "ratio"

    def test_spread_default_method(self):
        resp = client.post(
            "/api/analysis/spread",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR"},
        )
        assert resp.status_code == 200
        assert resp.json()["method"] == "ols"


# ---------------------------------------------------------------------------
# Z-score endpoint
# ---------------------------------------------------------------------------


class TestZScore:
    def test_zscore_returns_array(self):
        resp = client.post(
            "/api/analysis/zscore",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h", "lookback_window": 60},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["lookback_window"] == 60
        assert isinstance(data["zscore"], list)
        assert len(data["zscore"]) == len(data["timestamps"])

    def test_zscore_custom_window(self):
        resp = client.post(
            "/api/analysis/zscore",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "lookback_window": 30},
        )
        assert resp.status_code == 200
        assert resp.json()["lookback_window"] == 30

    def test_zscore_json_serializable(self):
        resp = client.post(
            "/api/analysis/zscore",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR"},
        )
        json.loads(resp.text)


# ---------------------------------------------------------------------------
# Stationarity endpoint
# ---------------------------------------------------------------------------


class TestStationarity:
    def test_stationarity_spread(self):
        resp = client.post(
            "/api/analysis/stationarity",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "adf_statistic" in data
        assert "p_value" in data
        assert "is_stationary" in data
        assert isinstance(data["is_stationary"], bool)

    def test_stationarity_asset1(self):
        resp = client.post(
            "/api/analysis/stationarity",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "series_name": "asset1"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "ETH/EUR"

    def test_stationarity_asset2(self):
        resp = client.post(
            "/api/analysis/stationarity",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "series_name": "asset2"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "ETC/EUR"

    def test_stationarity_critical_values(self):
        resp = client.post(
            "/api/analysis/stationarity",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR"},
        )
        cv = resp.json()["critical_values"]
        assert all(k in cv for k in ("one_pct", "five_pct", "ten_pct"))


# ---------------------------------------------------------------------------
# Analysis error cases
# ---------------------------------------------------------------------------


class TestAnalysisErrors:
    def test_error_missing_pair_404(self):
        resp = client.post(
            "/api/analysis/cointegration",
            json={"asset1": "FAKE/EUR", "asset2": "ETC/EUR"},
        )
        assert resp.status_code == 404
        assert "Cache not found" in resp.json()["detail"]

    def test_error_missing_pair_spread_404(self):
        resp = client.post(
            "/api/analysis/spread",
            json={"asset1": "FAKE/EUR", "asset2": "ETC/EUR"},
        )
        assert resp.status_code == 404

    def test_error_missing_pair_zscore_404(self):
        resp = client.post(
            "/api/analysis/zscore",
            json={"asset1": "FAKE/EUR", "asset2": "ETC/EUR"},
        )
        assert resp.status_code == 404

    def test_error_missing_pair_stationarity_404(self):
        resp = client.post(
            "/api/analysis/stationarity",
            json={"asset1": "FAKE/EUR", "asset2": "ETC/EUR"},
        )
        assert resp.status_code == 404

    def test_error_response_has_detail(self):
        resp = client.post(
            "/api/analysis/cointegration",
            json={"asset1": "NONEXISTENT/EUR", "asset2": "ETC/EUR"},
        )
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_error_missing_body_422(self):
        """POST analysis endpoints without a body returns 422 validation error."""
        resp = client.post("/api/analysis/cointegration")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Deep serialization safety — recursive numpy type walk
# ---------------------------------------------------------------------------


class TestSerializationSafety:
    """Recursively verify that no numpy types survive in API responses."""

    NUMPY_TYPES = (
        np.float64, np.float32, np.float16,
        np.int64, np.int32, np.int16, np.int8,
        np.uint64, np.uint32, np.uint16, np.uint8,
        np.bool_, np.str_, np.ndarray,
    )

    @classmethod
    def _assert_no_numpy(cls, obj, path: str = "root"):
        """Recursively walk a parsed JSON value and assert no numpy types."""
        assert not isinstance(obj, cls.NUMPY_TYPES), (
            f"Numpy type {type(obj).__name__} found at {path}: {obj!r}"
        )
        if isinstance(obj, dict):
            for k, v in obj.items():
                cls._assert_no_numpy(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                cls._assert_no_numpy(v, f"{path}[{i}]")

    def test_no_numpy_types_in_cointegration_response(self):
        """Walk the entire cointegration response tree and verify no numpy types."""
        resp = client.post(
            "/api/analysis/cointegration",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h"},
        )
        assert resp.status_code == 200
        data = resp.json()
        self._assert_no_numpy(data)

    def test_no_numpy_types_in_spread_response(self):
        resp = client.post(
            "/api/analysis/spread",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h"},
        )
        assert resp.status_code == 200
        self._assert_no_numpy(resp.json())

    def test_no_numpy_types_in_zscore_response(self):
        resp = client.post(
            "/api/analysis/zscore",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h"},
        )
        assert resp.status_code == 200
        self._assert_no_numpy(resp.json())

    def test_no_numpy_types_in_stationarity_response(self):
        resp = client.post(
            "/api/analysis/stationarity",
            json={"asset1": "ETH/EUR", "asset2": "ETC/EUR", "timeframe": "1h"},
        )
        assert resp.status_code == 200
        self._assert_no_numpy(resp.json())
