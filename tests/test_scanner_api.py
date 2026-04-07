"""Tests for the renamed Scanner API endpoints (Phase 06).

Covers:
- D-16: rename /api/academy/scan -> /api/scanner/scan
- D-17: drop fresh and coins[] parameters
- D-18: response gains cached_coin_count and dropped_for_completeness
- Pitfall 3 fix: completeness formula is timeframe-aware (1d returns non-empty)
- SCAN-01/02/04: response shape, categorization, error path

Uses httpx TestClient — requires the data cache to contain at least a few EUR pairs
on 1h and 1d timeframes (same constraint as the existing tests/test_api.py).
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Endpoint surface (D-16, D-17)
# ---------------------------------------------------------------------------


class TestScannerEndpoints:
    def test_new_scanner_scan_endpoint_exists(self):
        resp = client.get("/api/scanner/scan?timeframe=1h&days_back=90")
        assert resp.status_code == 200, resp.text

    def test_new_scanner_fetch_endpoint_exists(self):
        # POST /api/scanner/fetch is the renamed POST /api/academy/fetch
        # Use a tiny days_back to keep this fast in CI; allow non-200 only if Bitvavo unreachable
        resp = client.post("/api/scanner/fetch?timeframe=1h&days_back=7&max_coins=2")
        assert resp.status_code in (200, 502, 503), resp.text

    def test_old_academy_scan_endpoint_gone(self):
        resp = client.get("/api/academy/scan?timeframe=1h&days_back=90")
        assert resp.status_code in (404, 405)

    def test_old_academy_fetch_endpoint_gone(self):
        resp = client.post("/api/academy/fetch?timeframe=1h&days_back=7&max_coins=2")
        assert resp.status_code in (404, 405)


# ---------------------------------------------------------------------------
# Response shape (D-18, SCAN-01, SCAN-02)
# ---------------------------------------------------------------------------


class TestScannerScanResponse:
    def test_response_has_required_fields(self):
        resp = client.get("/api/scanner/scan?timeframe=1h&days_back=90")
        assert resp.status_code == 200
        data = resp.json()
        # Existing fields (SCAN-01, SCAN-02)
        assert "cointegrated" in data
        assert "not_cointegrated" in data
        assert "scanned" in data
        assert "timeframe" in data
        assert isinstance(data["cointegrated"], list)
        assert isinstance(data["not_cointegrated"], list)
        # New D-18 fields
        assert "cached_coin_count" in data
        assert "dropped_for_completeness" in data
        assert isinstance(data["cached_coin_count"], int)
        assert isinstance(data["dropped_for_completeness"], list)

    def test_response_categorizes_pairs(self):
        resp = client.get("/api/scanner/scan?timeframe=1h&days_back=90")
        data = resp.json()
        # Every cointegrated pair has p_value < 0.05; every not_cointegrated >= 0.05
        for pair in data["cointegrated"]:
            assert pair["p_value"] < 0.05, pair
            assert pair["is_cointegrated"] is True
        for pair in data["not_cointegrated"]:
            assert pair["p_value"] >= 0.05, pair
            assert pair["is_cointegrated"] is False

    def test_pair_row_has_all_columns(self):
        resp = client.get("/api/scanner/scan?timeframe=1h&days_back=90")
        data = resp.json()
        all_pairs = data["cointegrated"] + data["not_cointegrated"]
        if not all_pairs:
            pytest.skip("No pairs in cache to assert column shape")
        pair = all_pairs[0]
        for key in (
            "asset1", "asset2", "p_value", "is_cointegrated",
            "hedge_ratio", "half_life", "correlation",
            "cointegration_score", "observations",
        ):
            assert key in pair, f"missing column {key}"


# ---------------------------------------------------------------------------
# Removed parameters (D-17)
# ---------------------------------------------------------------------------


class TestRemovedParameters:
    def test_fresh_param_no_longer_referenced(self):
        # FastAPI silently ignores unknown query params, so this is a regression
        # check on the source: the route should NOT declare a `fresh` Query param.
        from inspect import signature
        from api.routers import scanner

        sig = signature(scanner.scan_pairs)
        assert "fresh" not in sig.parameters, "D-17: fresh param must be removed"

    def test_coins_param_was_never_added(self):
        from inspect import signature
        from api.routers import scanner

        sig = signature(scanner.scan_pairs)
        assert "coins" not in sig.parameters, "D-17: coins[] must not be added"


# ---------------------------------------------------------------------------
# Completeness formula fix (Pitfall 3 / D-29)
# ---------------------------------------------------------------------------


class TestCompletenessFormula:
    def test_one_day_timeframe_returns_non_empty(self):
        """The pre-fix bug: 1d timeframe always returned 0 results because the
        completeness check divided len(df) by hourly candle count.

        This test only meaningfully runs when 1d cache data exists. It will
        pytest.skip() if the cache is cold for 1d so CI doesn't false-fail on
        a clean checkout.
        """
        resp = client.get("/api/scanner/scan?timeframe=1d&days_back=365")
        assert resp.status_code == 200
        data = resp.json()
        if data["cached_coin_count"] < 2:
            pytest.skip("1d cache empty — fetch via /api/scanner/fetch first")
        # The fix: at least one pair must survive completeness for 1d
        total_pairs = len(data["cointegrated"]) + len(data["not_cointegrated"])
        assert total_pairs > 0, (
            "D-29 / Pitfall 3: completeness formula must be timeframe-aware "
            "so 1d cache produces non-empty scan results. "
            f"Got cached_coin_count={data['cached_coin_count']}, "
            f"dropped={data['dropped_for_completeness']}"
        )

    def test_dropped_for_completeness_distinguishes_from_cached_count(self):
        """cached_coin_count counts ALL coins in cache for the timeframe before filtering.
        dropped_for_completeness lists those that failed the 90% completeness check.
        scanned counts pairs C(remaining, 2) tested.
        """
        resp = client.get("/api/scanner/scan?timeframe=1h&days_back=90")
        data = resp.json()
        assert data["cached_coin_count"] >= 0
        # dropped count cannot exceed cached count
        assert len(data["dropped_for_completeness"]) <= data["cached_coin_count"]
