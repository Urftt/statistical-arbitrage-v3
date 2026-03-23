"""Trading router — session CRUD, lifecycle, kill switch, and data queries.

Thin-endpoint pattern (D031): no business logic here, just HTTP request
mapping → engine/persistence delegation → response serialization.

All endpoints are async and access the ``LiveTradingEngine`` and
``PersistenceManager`` via ``request.app.state``.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import Response

from api.schemas import (
    CreateSessionRequest,
    EquityPointResponse,
    KillSwitchResponse,
    OrderResponse,
    PositionResponse,
    SessionDetailResponse,
    SessionListResponse,
    SessionResponse,
    TradeResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trading", tags=["trading"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _session_to_response(session) -> SessionResponse:
    """Convert a PaperSession domain model to a SessionResponse."""
    return SessionResponse(
        session_id=session.session_id,
        config=session.config.model_dump(),
        status=session.status.value,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        current_equity=session.current_equity,
        total_trades=session.total_trades,
        last_error=session.last_error,
        is_live=session.is_live,
    )


def _position_to_response(pos) -> PositionResponse:
    """Convert a PaperPosition domain model to a PositionResponse."""
    return PositionResponse(
        session_id=pos.session_id,
        symbol=pos.symbol,
        direction=pos.direction,
        quantity_asset1=pos.quantity_asset1,
        quantity_asset2=pos.quantity_asset2,
        entry_price_asset1=pos.entry_price_asset1,
        entry_price_asset2=pos.entry_price_asset2,
        hedge_ratio=pos.hedge_ratio,
        entry_fee=pos.entry_fee,
        allocated_capital=pos.allocated_capital,
        opened_at=pos.opened_at.isoformat(),
    )


def _trade_to_response(trade) -> TradeResponse:
    """Convert a PaperTrade domain model to a TradeResponse."""
    return TradeResponse(
        session_id=trade.session_id,
        trade_id=trade.trade_id,
        direction=trade.direction,
        entry_timestamp=trade.entry_timestamp,
        exit_timestamp=trade.exit_timestamp,
        entry_reason=trade.entry_reason,
        exit_reason=trade.exit_reason,
        bars_held=trade.bars_held,
        entry_zscore=trade.entry_zscore,
        exit_zscore=trade.exit_zscore,
        hedge_ratio=trade.hedge_ratio,
        quantity_asset1=trade.quantity_asset1,
        quantity_asset2=trade.quantity_asset2,
        entry_price_asset1=trade.entry_price_asset1,
        entry_price_asset2=trade.entry_price_asset2,
        exit_price_asset1=trade.exit_price_asset1,
        exit_price_asset2=trade.exit_price_asset2,
        allocated_capital=trade.allocated_capital,
        gross_pnl=trade.gross_pnl,
        total_fees=trade.total_fees,
        net_pnl=trade.net_pnl,
        return_pct=trade.return_pct,
        equity_after_trade=trade.equity_after_trade,
    )


def _equity_to_response(ep) -> EquityPointResponse:
    """Convert a PaperEquityPoint domain model to an EquityPointResponse."""
    return EquityPointResponse(
        session_id=ep.session_id,
        timestamp=ep.timestamp,
        equity=ep.equity,
        cash=ep.cash,
        unrealized_pnl=ep.unrealized_pnl,
        position=ep.position,
    )


def _order_to_response(order) -> OrderResponse:
    """Convert a LiveOrder domain model to an OrderResponse."""
    return OrderResponse(
        order_id=order.order_id,
        session_id=order.session_id,
        side=order.side,
        symbol=order.symbol,
        requested_amount=order.requested_amount,
        filled_amount=order.filled_amount,
        fill_price=order.fill_price,
        fee=order.fee,
        status=order.status,
        created_at=order.created_at.isoformat(),
        filled_at=order.filled_at.isoformat() if order.filled_at else None,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(request: Request) -> SessionListResponse:
    """List all trading sessions."""
    engine = request.app.state.engine
    sessions = await engine.get_all_sessions()
    return SessionListResponse(
        sessions=[_session_to_response(s) for s in sessions],
    )


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    request: Request, body: CreateSessionRequest,
) -> SessionResponse:
    """Create a new paper or live trading session."""
    from statistical_arbitrage.paper_trading.models import SessionConfig

    engine = request.app.state.engine
    config = SessionConfig(
        asset1=body.asset1,
        asset2=body.asset2,
        timeframe=body.timeframe,
        is_live=body.is_live,
        lookback_window=body.lookback_window,
        entry_threshold=body.entry_threshold,
        exit_threshold=body.exit_threshold,
        stop_loss=body.stop_loss,
        initial_capital=body.initial_capital,
        position_size=body.position_size,
        transaction_fee=body.transaction_fee,
    )
    session = await engine.create_session(config)
    logger.info("Session created via API: session_id=%s, is_live=%s", session.session_id, session.is_live)
    return _session_to_response(session)


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(request: Request, session_id: str) -> SessionDetailResponse:
    """Get full session detail including positions, trades, equity, and orders."""
    persistence = request.app.state.persistence
    session = await persistence.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    positions = await persistence.get_positions(session_id)
    trades = await persistence.get_trades(session_id)
    equity_history = await persistence.get_equity_history(session_id)
    orders = await persistence.get_orders(session_id)

    return SessionDetailResponse(
        session_id=session.session_id,
        config=session.config.model_dump(),
        status=session.status.value,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        current_equity=session.current_equity,
        total_trades=session.total_trades,
        last_error=session.last_error,
        is_live=session.is_live,
        positions=[_position_to_response(p) for p in positions],
        trades=[_trade_to_response(t) for t in trades],
        equity_history=[_equity_to_response(e) for e in equity_history],
        orders=[_order_to_response(o) for o in orders],
    )


@router.post("/sessions/{session_id}/start", response_model=SessionResponse)
async def start_session(request: Request, session_id: str) -> SessionResponse:
    """Start a session's trading loop."""
    engine = request.app.state.engine
    try:
        await engine.start_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session = await engine.persistence.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    logger.info("Session started via API: session_id=%s", session_id)
    return _session_to_response(session)


@router.post("/sessions/{session_id}/stop", response_model=SessionResponse)
async def stop_session(request: Request, session_id: str) -> SessionResponse:
    """Stop a session's trading loop."""
    engine = request.app.state.engine
    persistence = request.app.state.persistence

    session = await persistence.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    await engine.stop_session(session_id)

    session = await persistence.get_session(session_id)
    logger.info("Session stopped via API: session_id=%s", session_id)
    return _session_to_response(session)


@router.post("/sessions/{session_id}/kill", response_model=KillSwitchResponse)
async def kill_session(request: Request, session_id: str) -> KillSwitchResponse:
    """Emergency kill switch — flatten positions and kill a live session."""
    engine = request.app.state.engine
    persistence = request.app.state.persistence

    session = await persistence.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    if not session.is_live:
        raise HTTPException(
            status_code=400,
            detail=f"Kill switch is only available for live sessions (session {session_id} is paper)",
        )

    result = await engine.kill_session(session_id)
    logger.info(
        "Kill switch activated via API: session_id=%s, success=%s",
        session_id, result.success,
    )
    return KillSwitchResponse(
        success=result.success,
        session_id=result.session_id,
        orders_submitted=result.orders_submitted,
        orders_failed=result.orders_failed,
        positions_closed=result.positions_closed,
        errors=result.errors,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_session(request: Request, session_id: str) -> Response:
    """Delete a session and all associated data."""
    persistence = request.app.state.persistence

    session = await persistence.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Stop any running task first
    engine = request.app.state.engine
    task = engine._tasks.pop(session_id, None)
    if task:
        task.cancel()
        try:
            await task
        except Exception:
            pass

    await persistence.delete_session(session_id)
    logger.info("Session deleted via API: session_id=%s", session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sessions/{session_id}/trades", response_model=list[TradeResponse])
async def get_session_trades(request: Request, session_id: str) -> list[TradeResponse]:
    """Get all trades for a session."""
    persistence = request.app.state.persistence

    session = await persistence.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    trades = await persistence.get_trades(session_id)
    return [_trade_to_response(t) for t in trades]


@router.get("/sessions/{session_id}/equity", response_model=list[EquityPointResponse])
async def get_session_equity(request: Request, session_id: str) -> list[EquityPointResponse]:
    """Get equity history for a session."""
    persistence = request.app.state.persistence

    session = await persistence.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    equity = await persistence.get_equity_history(session_id)
    return [_equity_to_response(e) for e in equity]


@router.get("/sessions/{session_id}/orders", response_model=list[OrderResponse])
async def get_session_orders(request: Request, session_id: str) -> list[OrderResponse]:
    """Get all orders for a session."""
    persistence = request.app.state.persistence

    session = await persistence.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    orders = await persistence.get_orders(session_id)
    return [_order_to_response(o) for o in orders]
