"""FastAPI application factory for the Statistical Arbitrage API."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import analysis, backtest, health, optimization, pairs, research, trading

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan — startup and shutdown events.

    Initializes the live trading engine and all its dependencies:
    - PersistenceManager (async SQLite)
    - CandleDataSource (CCXT-based)
    - MockOrderExecutor (default for dev; BitvavoOrderExecutor for production)
    - RiskManager (configurable limits from settings)
    - TelegramNotifier (graceful no-op when unconfigured)
    - LiveTradingEngine (composes all the above)

    On shutdown, stops all sessions and closes connections.
    """
    from config.settings import settings
    from statistical_arbitrage.live_trading import (
        LiveTradingEngine,
        MockOrderExecutor,
        RiskManager,
        TelegramNotifier,
    )
    from statistical_arbitrage.paper_trading.data_source import MockCandleDataSource
    from statistical_arbitrage.paper_trading.persistence import PersistenceManager

    # -- Persistence -------------------------------------------------------
    db_path = settings.data.data_root / "trading.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    persistence = PersistenceManager(db_path)
    await persistence.connect()

    # -- Data source -------------------------------------------------------
    # Default to empty mock for dev — real CandleDataSource is wired per-session
    data_source = MockCandleDataSource(candles=[], batch_size=1)

    # -- Order executor (mock for dev safety) ------------------------------
    order_executor = MockOrderExecutor()

    # -- Risk manager from settings ----------------------------------------
    risk_manager = RiskManager(
        max_position_size_eur=settings.live_trading.max_position_size_eur,
        max_concurrent_positions=settings.live_trading.max_concurrent_positions,
        daily_loss_limit_eur=settings.live_trading.daily_loss_limit_eur,
        min_order_size_eur=settings.live_trading.min_order_size_eur,
    )

    # -- Telegram notifier (no-op when unconfigured) -----------------------
    notifier = TelegramNotifier(
        bot_token=settings.telegram.telegram_bot_token,
        chat_id=settings.telegram.telegram_chat_id,
    )

    # -- Live trading engine -----------------------------------------------
    engine = LiveTradingEngine(
        data_source=data_source,
        persistence=persistence,
        order_executor=order_executor,
        risk_manager=risk_manager,
        notifier=notifier,
    )
    await engine.recover_sessions()

    # Attach to app.state for router access
    application.state.engine = engine
    application.state.persistence = persistence

    logger.info("🚀 Statistical Arbitrage API running (trading engine initialized)")
    yield

    # -- Shutdown ----------------------------------------------------------
    await engine.stop_all()
    await notifier.close()
    await order_executor.close()
    await persistence.close()
    logger.info("Trading engine shut down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Statistical Arbitrage API",
        version="1.0.0",
        description="REST API for statistical arbitrage research — pair data, OHLCV timeseries, and cointegration analysis.",
        root_path="",
        lifespan=lifespan,
    )

    # CORS — allow the React frontend at localhost:3000 and worktree at :3001
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    application.include_router(health.router)
    application.include_router(pairs.router)
    application.include_router(analysis.router)
    application.include_router(research.router)
    application.include_router(backtest.router)
    application.include_router(optimization.router)
    application.include_router(trading.router)

    return application


app = create_app()
