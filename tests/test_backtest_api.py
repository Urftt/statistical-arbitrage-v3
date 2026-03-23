"""API contract tests for the research-to-backtest handoff."""

from fastapi.testclient import TestClient

from api.main import app
from api.schemas import BacktestRequest, StrategyParametersPayload

client = TestClient(app)
PAIR = {
    "asset1": "ETH/EUR",
    "asset2": "ETC/EUR",
    "timeframe": "1h",
    "days_back": 365,
}


class TestBacktestSchemas:
    def test_backtest_request_serializes_and_round_trips(self):
        request = BacktestRequest(
            **PAIR,
            strategy=StrategyParametersPayload(
                lookback_window=60,
                entry_threshold=2.0,
                exit_threshold=0.5,
                stop_loss=3.0,
                initial_capital=10_000.0,
                position_size=0.5,
                transaction_fee=0.0025,
                min_trade_count_warning=3,
            ),
        )

        dumped = request.model_dump(mode="json")

        assert dumped["asset1"] == PAIR["asset1"]
        assert dumped["strategy"]["lookback_window"] == 60
        assert BacktestRequest.model_validate(dumped).model_dump() == request.model_dump()


class TestResearchToBacktestAPI:
    def test_openapi_exposes_research_and_backtest_contracts(self):
        schema = app.openapi()

        assert "/api/research/lookback-window" in schema["paths"]
        assert "/api/backtest" in schema["paths"]

        backtest_props = schema["components"]["schemas"]["BacktestResponse"]["properties"]
        assert "data_quality" in backtest_props
        assert "trade_log" in backtest_props
        assert "equity_curve" in backtest_props
        assert "metrics" in backtest_props
        assert "footer" in backtest_props

    def test_research_response_includes_real_results_and_recommended_preset(self):
        response = client.post("/api/research/lookback-window", json=PAIR)

        assert response.status_code == 200
        data = response.json()

        assert data["module"] == "lookback_window"
        assert data["asset1"] == PAIR["asset1"]
        assert data["asset2"] == PAIR["asset2"]
        assert data["timeframe"] == PAIR["timeframe"]
        assert data["observations"] > 0
        assert len(data["results"]) > 0
        assert data["takeaway"]["severity"] in {"green", "yellow", "red"}
        assert data["recommended_result"]["window"] >= 2
        assert data["recommended_backtest_params"]["asset1"] == PAIR["asset1"]
        assert data["recommended_backtest_params"]["strategy"]["lookback_window"] == data["recommended_result"]["window"]

    def test_research_recommendation_validates_as_a_backtest_request(self):
        research_response = client.post("/api/research/lookback-window", json=PAIR)
        recommended = research_response.json()["recommended_backtest_params"]

        request = BacktestRequest.model_validate(recommended)

        assert request.asset1 == PAIR["asset1"]
        assert request.strategy.lookback_window == recommended["strategy"]["lookback_window"]

    def test_research_recommendation_posts_directly_to_backtest(self):
        research_response = client.post("/api/research/lookback-window", json=PAIR)
        recommended = research_response.json()["recommended_backtest_params"]

        backtest_response = client.post("/api/backtest", json=recommended)

        assert backtest_response.status_code == 200
        assert backtest_response.json()["request"] == recommended


class TestBacktestExecutionAPI:
    def test_backtest_response_shape_for_recommended_request(self):
        research_response = client.post("/api/research/lookback-window", json=PAIR)
        recommended = research_response.json()["recommended_backtest_params"]

        response = client.post("/api/backtest", json=recommended)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["data_quality"]["status"] == "passed"
        assert isinstance(data["warnings"], list)
        assert "execution_model" in data["footer"]
        assert "limitations" in data["footer"]
        assert isinstance(data["signal_overlay"], list)
        assert isinstance(data["trade_log"], list)
        assert isinstance(data["equity_curve"], list)
        assert len(data["trade_log"]) > 0
        assert len(data["equity_curve"]) > 0
        assert data["metrics"]["total_trades"] == len(data["trade_log"])
        assert data["metrics"]["final_equity"] > 0
        assert set(data["spread_summary"].keys()) == {"mean", "std"}

    def test_blocked_preflight_returns_structured_payload_without_trades(self):
        blocked_request = {
            **PAIR,
            "strategy": {
                "lookback_window": 5000,
                "entry_threshold": 2.0,
                "exit_threshold": 0.5,
                "stop_loss": 3.0,
                "initial_capital": 10_000.0,
                "position_size": 0.5,
                "transaction_fee": 0.0025,
                "min_trade_count_warning": 3,
            },
        }

        response = client.post("/api/backtest", json=blocked_request)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "blocked"
        assert data["data_quality"]["status"] == "blocked"
        assert "insufficient_observations" in {
            blocker["code"] for blocker in data["data_quality"]["blockers"]
        }
        assert data["trade_log"] == []
        assert data["equity_curve"] == []
        assert data["signal_overlay"] == []
        assert data["metrics"]["total_trades"] == 0
        assert data["metrics"]["final_equity"] == blocked_request["strategy"]["initial_capital"]
