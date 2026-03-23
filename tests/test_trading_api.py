"""Async API contract tests for the trading router.

Uses httpx.AsyncClient + ASGITransport to test the FastAPI app without
starting a server. Manually wires app.state since ASGITransport does NOT
trigger FastAPI lifespan events.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from api.main import app
from statistical_arbitrage.live_trading.engine import LiveTradingEngine
from statistical_arbitrage.live_trading.order_executor import MockOrderExecutor
from statistical_arbitrage.live_trading.risk_manager import RiskManager
from statistical_arbitrage.paper_trading.data_source import MockCandleDataSource
from statistical_arbitrage.paper_trading.persistence import PersistenceManager


@pytest_asyncio.fixture
async def client():
    """Create an httpx AsyncClient with manually wired app.state."""
    persistence = PersistenceManager(":memory:")
    await persistence.connect()

    data_source = MockCandleDataSource(candles=[], batch_size=1)
    order_executor = MockOrderExecutor()
    risk_manager = RiskManager(
        max_position_size_eur=25.0,
        max_concurrent_positions=2,
        daily_loss_limit_eur=50.0,
        min_order_size_eur=5.0,
    )

    engine = LiveTradingEngine(
        data_source=data_source,
        persistence=persistence,
        order_executor=order_executor,
        risk_manager=risk_manager,
    )

    app.state.engine = engine
    app.state.persistence = persistence

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    await engine.stop_all()
    await persistence.close()


# ---------------------------------------------------------------------------
# Helper to create a session via the API
# ---------------------------------------------------------------------------


async def _create_paper_session(client: AsyncClient) -> dict:
    """Create a paper session and return the response JSON."""
    resp = await client.post(
        "/api/trading/sessions",
        json={"asset1": "BTC", "asset2": "EUR", "is_live": False},
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_live_session(client: AsyncClient) -> dict:
    """Create a live session and return the response JSON."""
    resp = await client.post(
        "/api/trading/sessions",
        json={"asset1": "ETH", "asset2": "EUR", "is_live": True},
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_sessions_empty(client):
    """List sessions when none exist → 200, empty list."""
    resp = await client.get("/api/trading/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sessions"] == []


@pytest.mark.asyncio
async def test_create_paper_session(client):
    """Create a paper session → 201, correct fields."""
    data = await _create_paper_session(client)
    assert data["is_live"] is False
    assert data["status"] == "created"
    assert "session_id" in data
    assert data["config"]["asset1"] == "BTC"
    assert data["config"]["asset2"] == "EUR"
    assert data["current_equity"] == 10000.0
    assert data["total_trades"] == 0
    assert data["last_error"] is None


@pytest.mark.asyncio
async def test_create_live_session(client):
    """Create a live session → 201, is_live=True."""
    data = await _create_live_session(client)
    assert data["is_live"] is True
    assert data["status"] == "created"
    assert data["config"]["asset1"] == "ETH"
    assert data["config"]["is_live"] is True


@pytest.mark.asyncio
async def test_list_sessions_after_creates(client):
    """List sessions after creating two → 200, both sessions appear."""
    await _create_paper_session(client)
    await _create_live_session(client)

    resp = await client.get("/api/trading/sessions")
    assert resp.status_code == 200
    sessions = resp.json()["sessions"]
    assert len(sessions) == 2
    is_live_flags = {s["is_live"] for s in sessions}
    assert is_live_flags == {True, False}


@pytest.mark.asyncio
async def test_get_session_detail(client):
    """Get session detail → 200, includes empty positions/trades/equity/orders."""
    created = await _create_paper_session(client)
    sid = created["session_id"]

    resp = await client.get(f"/api/trading/sessions/{sid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sid
    assert data["positions"] == []
    assert data["trades"] == []
    assert data["equity_history"] == []
    assert data["orders"] == []


@pytest.mark.asyncio
async def test_get_session_detail_not_found(client):
    """Get session detail for nonexistent session → 404."""
    resp = await client.get("/api/trading/sessions/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_start_session(client):
    """Start a session → 200, status becomes running."""
    created = await _create_paper_session(client)
    sid = created["session_id"]

    resp = await client.post(f"/api/trading/sessions/{sid}/start")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_stop_session(client):
    """Stop a running session → 200, status becomes stopped."""
    created = await _create_paper_session(client)
    sid = created["session_id"]

    await client.post(f"/api/trading/sessions/{sid}/start")
    resp = await client.post(f"/api/trading/sessions/{sid}/stop")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "stopped"


@pytest.mark.asyncio
async def test_start_already_running_session(client):
    """Start an already-running session → 400."""
    created = await _create_paper_session(client)
    sid = created["session_id"]

    await client.post(f"/api/trading/sessions/{sid}/start")
    resp = await client.post(f"/api/trading/sessions/{sid}/start")
    assert resp.status_code == 400
    assert "already running" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_start_nonexistent_session(client):
    """Start a nonexistent session → 400."""
    resp = await client.post("/api/trading/sessions/nonexistent-id/start")
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_stop_nonexistent_session(client):
    """Stop a nonexistent session → 404."""
    resp = await client.post("/api/trading/sessions/nonexistent-id/stop")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_kill_switch_live_session(client):
    """Kill switch on live session (no positions) → 200, success=True."""
    created = await _create_live_session(client)
    sid = created["session_id"]

    resp = await client.post(f"/api/trading/sessions/{sid}/kill")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["session_id"] == sid
    assert data["positions_closed"] == 0
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_kill_switch_paper_session(client):
    """Kill switch on paper session → 400."""
    created = await _create_paper_session(client)
    sid = created["session_id"]

    resp = await client.post(f"/api/trading/sessions/{sid}/kill")
    assert resp.status_code == 400
    assert "paper" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_kill_switch_idempotent(client):
    """Kill switch called twice on killed session → 200 both times."""
    created = await _create_live_session(client)
    sid = created["session_id"]

    resp1 = await client.post(f"/api/trading/sessions/{sid}/kill")
    assert resp1.status_code == 200
    assert resp1.json()["success"] is True

    resp2 = await client.post(f"/api/trading/sessions/{sid}/kill")
    assert resp2.status_code == 200
    assert resp2.json()["success"] is True


@pytest.mark.asyncio
async def test_kill_switch_not_found(client):
    """Kill switch on nonexistent session → 404."""
    resp = await client.post("/api/trading/sessions/nonexistent-id/kill")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_session(client):
    """Delete a session → 204."""
    created = await _create_paper_session(client)
    sid = created["session_id"]

    resp = await client.delete(f"/api/trading/sessions/{sid}")
    assert resp.status_code == 204

    # Verify it's gone
    resp2 = await client.get(f"/api/trading/sessions/{sid}")
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_session(client):
    """Delete nonexistent session → 404."""
    resp = await client.delete("/api/trading/sessions/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_trades_empty(client):
    """Get trades for session (empty) → 200, empty list."""
    created = await _create_paper_session(client)
    sid = created["session_id"]

    resp = await client.get(f"/api/trading/sessions/{sid}/trades")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_equity_empty(client):
    """Get equity for session (empty) → 200, empty list."""
    created = await _create_paper_session(client)
    sid = created["session_id"]

    resp = await client.get(f"/api/trading/sessions/{sid}/equity")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_orders_empty(client):
    """Get orders for session (empty) → 200, empty list."""
    created = await _create_paper_session(client)
    sid = created["session_id"]

    resp = await client.get(f"/api/trading/sessions/{sid}/orders")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_trades_not_found(client):
    """Get trades for nonexistent session → 404."""
    resp = await client.get("/api/trading/sessions/nonexistent-id/trades")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_equity_not_found(client):
    """Get equity for nonexistent session → 404."""
    resp = await client.get("/api/trading/sessions/nonexistent-id/equity")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_orders_not_found(client):
    """Get orders for nonexistent session → 404."""
    resp = await client.get("/api/trading/sessions/nonexistent-id/orders")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_session_custom_params(client):
    """Create a session with custom strategy params → reflected in config."""
    resp = await client.post(
        "/api/trading/sessions",
        json={
            "asset1": "BTC",
            "asset2": "EUR",
            "lookback_window": 30,
            "entry_threshold": 1.5,
            "exit_threshold": 0.3,
            "stop_loss": 2.5,
            "initial_capital": 5000.0,
            "position_size": 0.3,
            "transaction_fee": 0.001,
        },
    )
    assert resp.status_code == 201
    config = resp.json()["config"]
    assert config["lookback_window"] == 30
    assert config["entry_threshold"] == 1.5
    assert config["exit_threshold"] == 0.3
    assert config["stop_loss"] == 2.5
    assert config["initial_capital"] == 5000.0
    assert config["position_size"] == 0.3
    assert config["transaction_fee"] == 0.001
