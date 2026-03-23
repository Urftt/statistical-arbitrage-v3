"""Pairs listing and OHLCV data endpoints."""

from datetime import datetime, timedelta

import polars as pl
from fastapi import APIRouter, Depends, HTTPException, Query

from api.schemas import OHLCVResponse, PairInfo, PairsListResponse
from src.statistical_arbitrage.data.cache_manager import (
    DataCacheManager,
    get_cache_manager,
)

router = APIRouter(prefix="/api/pairs", tags=["pairs"])


def get_cache_mgr() -> DataCacheManager:
    """Dependency: returns the singleton DataCacheManager."""
    return get_cache_manager()


def _symbol_url_to_internal(symbol_url: str) -> str:
    """Convert URL symbol format to internal format: ETH-EUR → ETH/EUR."""
    return symbol_url.replace("-", "/")


def _cache_path_for(cache_mgr: DataCacheManager, symbol_dash: str, timeframe: str):
    """Build the parquet cache path for a symbol/timeframe pair."""
    return cache_mgr.cache_dir / f"{symbol_dash}_{timeframe}.parquet"


@router.get("", response_model=PairsListResponse)
def list_pairs(
    cache_mgr: DataCacheManager = Depends(get_cache_mgr),
) -> PairsListResponse:
    """List all cached pair datasets with metadata."""
    cached = cache_mgr.list_cached()
    pairs = []
    for info in cached:
        symbol: str = info["symbol"]
        parts = symbol.split("/")
        base = parts[0] if len(parts) == 2 else symbol
        quote = parts[1] if len(parts) == 2 else ""

        # Convert datetime objects to ISO strings
        start_dt = info["start"]
        end_dt = info["end"]
        start_iso = start_dt.isoformat() if hasattr(start_dt, "isoformat") else str(start_dt)
        end_iso = end_dt.isoformat() if hasattr(end_dt, "isoformat") else str(end_dt)

        pairs.append(
            PairInfo(
                symbol=symbol,
                base=base,
                quote=quote,
                timeframe=info["timeframe"],
                candles=info["candles"],
                start=start_iso,
                end=end_iso,
                file_size_mb=info["file_size_mb"],
            )
        )
    return PairsListResponse(pairs=pairs)


@router.get("/{symbol}/ohlcv", response_model=OHLCVResponse)
def get_ohlcv(
    symbol: str,
    timeframe: str = Query(default="1h", description="Candle timeframe (e.g. 1h, 4h)"),
    days_back: int = Query(default=90, ge=1, le=3650, description="Days of history"),
    cache_mgr: DataCacheManager = Depends(get_cache_mgr),
) -> OHLCVResponse:
    """
    Get OHLCV timeseries data for a cached pair.

    Symbol uses dash format in URL: `ETH-EUR` (internally converted to `ETH/EUR`).
    Reads directly from parquet cache — never triggers Bitvavo API calls.
    """
    internal_symbol = _symbol_url_to_internal(symbol)
    cache_file = _cache_path_for(cache_mgr, symbol, timeframe)

    if not cache_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No cached data for {internal_symbol} at {timeframe}. "
            f"Expected file: {cache_file.name}",
        )

    # Read parquet directly — no API calls
    df = pl.read_parquet(cache_file)

    # Filter by days_back
    cutoff_ms = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)
    df = df.filter(pl.col("timestamp") >= cutoff_ms)

    if df.is_empty():
        raise HTTPException(
            status_code=404,
            detail=f"No data for {internal_symbol} at {timeframe} within the last {days_back} days.",
        )

    return OHLCVResponse(
        symbol=internal_symbol,
        timeframe=timeframe,
        count=len(df),
        timestamps=df["timestamp"].to_list(),
        open=df["open"].to_list(),
        high=df["high"].to_list(),
        low=df["low"].to_list(),
        close=df["close"].to_list(),
        volume=df["volume"].to_list(),
    )
