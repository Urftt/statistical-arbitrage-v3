"""Backtest execution endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.routers.analysis import _get_cache_mgr, _load_pair_data
from api.schemas import (
    BacktestRequest,
    BacktestResponse,
    DataQualityReportPayload,
    EngineWarningPayload,
    EquityCurvePointPayload,
    HonestReportingFooterPayload,
    MetricSummaryPayload,
    SignalOverlayPointPayload,
    SpreadSummaryPayload,
    TradeLogEntryPayload,
)
from src.statistical_arbitrage.data.cache_manager import DataCacheManager
from statistical_arbitrage.backtesting.engine import run_backtest
from statistical_arbitrage.backtesting.models import StrategyParameters

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.post("", response_model=BacktestResponse)
def execute_backtest(
    request: BacktestRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> BacktestResponse:
    """Execute a look-ahead-safe backtest using cached parquet data only."""
    close1, close2, timestamps = _load_pair_data(
        request.asset1,
        request.asset2,
        request.timeframe,
        request.days_back,
        cache_mgr,
    )

    try:
        result = run_backtest(
            timestamps=timestamps,
            asset1_prices=close1,
            asset2_prices=close2,
            params=StrategyParameters(**request.strategy.model_dump()),
        )
    except Exception as exc:
        logger.exception(
            "Backtest execution failed for %s / %s",
            request.asset1,
            request.asset2,
        )
        raise HTTPException(status_code=500, detail=f"Backtest failed: {exc}") from exc

    return BacktestResponse(
        status=result.status,
        request=request,
        data_quality=DataQualityReportPayload(**result.preflight.model_dump()),
        warnings=[
            EngineWarningPayload(**warning.model_dump())
            for warning in result.warnings
        ],
        footer=HonestReportingFooterPayload(**result.footer.model_dump()),
        signal_overlay=[
            SignalOverlayPointPayload(**signal.model_dump())
            for signal in result.signals
        ],
        trade_log=[
            TradeLogEntryPayload(**trade.model_dump())
            for trade in result.trades
        ],
        equity_curve=[
            EquityCurvePointPayload(**point.model_dump())
            for point in result.equity_curve
        ],
        metrics=MetricSummaryPayload(**result.metrics.model_dump()),
        spread_summary=SpreadSummaryPayload(
            mean=result.spread_mean,
            std=result.spread_std,
        ),
    )
