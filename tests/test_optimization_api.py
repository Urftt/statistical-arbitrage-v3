"""API contract tests for the grid search optimization endpoint."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
PAIR = {
    "asset1": "ETH/EUR",
    "asset2": "ETC/EUR",
    "timeframe": "1h",
    "days_back": 365,
}


class TestGridSearchEndpoint:
    def test_grid_search_endpoint_returns_200(self):
        """POST with valid axes → 200 + correct response shape."""
        request = {
            **PAIR,
            "axes": [
                {"name": "entry_threshold", "min_value": 1.5, "max_value": 2.5, "step": 0.5},
                {"name": "exit_threshold", "min_value": 0.3, "max_value": 0.7, "step": 0.2},
            ],
            "optimize_metric": "sharpe_ratio",
            "max_combinations": 500,
        }

        response = client.post("/api/optimization/grid-search", json=request)

        assert response.status_code == 200
        data = response.json()

        # Structural shape checks
        assert data["total_combinations"] == 9  # 3 entry × 3 exit
        assert data["grid_shape"] == [3, 3]
        assert len(data["cells"]) == 9
        assert len(data["axes"]) == 2
        assert data["optimize_metric"] == "sharpe_ratio"
        assert isinstance(data["warnings"], list)
        assert data["execution_time_ms"] > 0

        # Footer is present
        assert "execution_model" in data["footer"]
        assert "limitations" in data["footer"]

        # Best cell is present (unless all combos failed)
        if data["best_cell_index"] is not None:
            assert data["best_cell"] is not None
            assert data["best_cell"]["status"] == "ok"
            assert data["robustness_score"] is not None
            assert 0.0 <= data["robustness_score"] <= 1.0

            # recommended_backtest_params is populated for best cell
            assert data["recommended_backtest_params"] is not None
            assert data["recommended_backtest_params"]["asset1"] == PAIR["asset1"]

        # Every cell has required fields
        for cell in data["cells"]:
            assert "params" in cell
            assert "metrics" in cell
            assert "trade_count" in cell
            assert cell["status"] in ("ok", "blocked", "no_trades")

    def test_grid_search_endpoint_too_many_combos_422(self):
        """POST with very large axes → 422 error."""
        request = {
            **PAIR,
            "axes": [
                {"name": "entry_threshold", "min_value": 0.1, "max_value": 10.0, "step": 0.1},
                {"name": "exit_threshold", "min_value": 0.1, "max_value": 10.0, "step": 0.1},
            ],
            "max_combinations": 500,
        }

        response = client.post("/api/optimization/grid-search", json=request)

        assert response.status_code == 422
        assert "exceeds the limit" in response.json()["detail"]

    def test_grid_search_openapi_schema_exposed(self):
        """The grid-search endpoint appears in the OpenAPI spec."""
        schema = app.openapi()
        assert "/api/optimization/grid-search" in schema["paths"]

    def test_grid_search_recommended_params_post_to_backtest(self):
        """recommended_backtest_params can be posted directly to /api/backtest."""
        grid_request = {
            **PAIR,
            "axes": [
                {"name": "entry_threshold", "min_value": 1.5, "max_value": 2.5, "step": 0.5},
            ],
            "optimize_metric": "sharpe_ratio",
        }

        grid_response = client.post("/api/optimization/grid-search", json=grid_request)
        assert grid_response.status_code == 200

        recommended = grid_response.json().get("recommended_backtest_params")
        if recommended is not None:
            backtest_response = client.post("/api/backtest", json=recommended)
            assert backtest_response.status_code == 200
            assert backtest_response.json()["status"] in ("ok", "blocked")
