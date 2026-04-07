"""Scanner endpoints — fetch fresh OHLCV from Bitvavo and scan cached pairs for cointegration.

Renamed from academy_scan.py in Phase 06 (D-16). Returns honest results: dropped-for-completeness
coins are surfaced to the caller instead of silently filtered.
"""

import logging
import time
from itertools import combinations

import polars as pl
from fastapi import APIRouter, Depends, Query

from api.schemas import ScanResponse, numpy_to_python
from statistical_arbitrage.analysis.cointegration import PairAnalysis
from statistical_arbitrage.data.cache_manager import (
    DataCacheManager,
    get_cache_manager,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scanner", tags=["scanner"])

# In-memory caches with TTL — preserve from academy_scan.py (D-21)
_scan_cache: dict[str, dict] = {}
_scan_cache_ts: dict[str, float] = {}
SCAN_CACHE_TTL = 300  # 5 minutes


def _get_cache_mgr() -> DataCacheManager:
    return get_cache_manager()


# ---------------------------------------------------------------------------
# POST /api/scanner/fetch — Fetch fresh data from Bitvavo
# ---------------------------------------------------------------------------


@router.post("/fetch")
def fetch_live_data(
    timeframe: str = Query(default="1h", description="Timeframe to fetch"),
    days_back: int = Query(default=90, ge=7, le=365, description="Days of history"),
    max_coins: int = Query(default=20, ge=2, le=50, description="Max coins to fetch"),
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> dict:
    """Fetch fresh OHLCV data from Bitvavo for top EUR pairs.

    Downloads data for up to max_coins EUR trading pairs and caches it.
    Uses incremental fetching — only downloads the delta since last cache.
    Clears the in-memory scan cache so the next scan reflects fresh data (D-21).
    """
    try:
        available = cache_mgr.get_available_pairs()
        symbols = available["symbol"].to_list()[:max_coins]

        fetched = []
        for symbol in symbols:
            try:
                df = cache_mgr.get_candles(symbol, timeframe, days_back=days_back)
                fetched.append(
                    {
                        "symbol": symbol,
                        "candles": len(df),
                        "timeframe": timeframe,
                    }
                )
            except Exception as e:
                logger.warning("Failed to fetch %s: %s", symbol, e)
                fetched.append(
                    {
                        "symbol": symbol,
                        "candles": 0,
                        "timeframe": timeframe,
                        "error": str(e),
                    }
                )

        # D-21: Clear scan cache so next scan uses fresh data
        _scan_cache.clear()
        _scan_cache_ts.clear()

        successful = [f for f in fetched if f["candles"] > 0]
        return {
            "fetched": len(successful),
            "failed": len(fetched) - len(successful),
            "total": len(fetched),
            "symbols": fetched,
            "timeframe": timeframe,
            "days_back": days_back,
        }

    except Exception:
        logger.exception("Fetch failed")
        raise


# ---------------------------------------------------------------------------
# GET /api/scanner/scan — Scan cached pairs for cointegration
# ---------------------------------------------------------------------------


@router.get("/scan", response_model=ScanResponse)
def scan_pairs(
    timeframe: str = Query(default="1h", description="Timeframe to test"),
    days_back: int = Query(default=90, ge=7, le=365, description="Days of history"),
    max_pairs: int = Query(default=20, ge=2, le=50, description="Max base assets to scan"),
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> ScanResponse:
    """Scan cached pairs for cointegration.

    D-17: This endpoint reads from the local cache only. To refresh data,
    call POST /api/scanner/fetch first. The `fresh` and `coins[]` query params
    that existed in academy_scan.py have been removed.

    D-18: Response includes `cached_coin_count` (coins in cache before filtering)
    and `dropped_for_completeness` (coins excluded by the 90% completeness check).
    """
    cache_key = f"{timeframe}-{days_back}-{max_pairs}"
    now = time.time()

    if cache_key in _scan_cache and (now - _scan_cache_ts.get(cache_key, 0)) < SCAN_CACHE_TTL:
        return _scan_cache[cache_key]

    # 1. Find available base assets from cache for this timeframe
    cached = cache_mgr.list_cached()
    base_assets: set[str] = set()
    for info in cached:
        symbol: str = info["symbol"]
        tf: str = info["timeframe"]
        if tf == timeframe and "/" in symbol:
            base = symbol.split("/")[0]
            base_assets.add(base)

    base_list = sorted(base_assets)[:max_pairs]
    cached_coin_count = len(base_list)  # D-18

    if len(base_list) < 2:
        empty = {
            "cointegrated": [],
            "not_cointegrated": [],
            "scanned": 0,
            "timeframe": timeframe,
            "cached_coin_count": cached_coin_count,
            "dropped_for_completeness": [],
        }
        _scan_cache[cache_key] = empty
        _scan_cache_ts[cache_key] = now
        return empty

    # 2. Pre-load close-price series with timeframe-aware completeness check
    # FIX (Pitfall 3 / D-29): The previous formula divided len(df) by hourly candle
    # count regardless of timeframe. For 1d data this gave ~4% completeness for
    # ANY coin and silently dropped everything. We now compute the expected
    # candle count based on the actual timeframe interval in milliseconds.
    series_map: dict[str, pl.DataFrame] = {}
    dropped_for_completeness: list[str] = []
    min_completeness = 0.90  # 90% completeness threshold preserved (D-23)

    timeframe_ms = DataCacheManager.TIMEFRAME_MS.get(timeframe, 3_600_000)

    for base in base_list:
        symbol = f"{base}/EUR"
        try:
            df = cache_mgr.get_candles(symbol, timeframe, days_back=days_back)
            if len(df) < 100:
                # Below cointegration minimum — not a "completeness" drop, just too short.
                continue

            ts = df["timestamp"].sort().to_list()
            span_ms = ts[-1] - ts[0]
            expected_candles = max(int(span_ms / timeframe_ms), 1)
            completeness = len(df) / expected_candles

            if completeness < min_completeness:
                logger.info(
                    "Dropping %s — %.1f%% complete (need %.0f%%) for tf=%s",
                    symbol,
                    completeness * 100,
                    min_completeness * 100,
                    timeframe,
                )
                dropped_for_completeness.append(symbol)
                continue

            series_map[base] = df
        except Exception:
            logger.warning("Failed to load %s", symbol)

    # 3. Test all combinations
    results: list[dict] = []
    available_bases = list(series_map.keys())

    for asset1, asset2 in combinations(available_bases, 2):
        try:
            df1 = series_map[asset1]
            df2 = series_map[asset2]

            joined = (
                df1.select(pl.col("timestamp"), pl.col("close").alias("close_1"))
                .join(
                    df2.select(pl.col("timestamp"), pl.col("close").alias("close_2")),
                    on="timestamp",
                    how="inner",
                )
                .sort("timestamp")
            )

            if len(joined) < 100:
                continue

            pa = PairAnalysis(joined["close_1"], joined["close_2"])
            coint = numpy_to_python(pa.test_cointegration())
            half_life = numpy_to_python(pa.calculate_half_life())
            correlation = numpy_to_python(pa.get_correlation())

            results.append(
                {
                    "asset1": f"{asset1}/EUR",
                    "asset2": f"{asset2}/EUR",
                    "p_value": coint["p_value"],
                    "is_cointegrated": coint["is_cointegrated"],
                    "hedge_ratio": coint["hedge_ratio"],
                    "half_life": half_life,
                    "correlation": correlation,
                    "cointegration_score": coint["cointegration_score"],
                    "observations": len(joined),
                }
            )
        except Exception:
            logger.warning("Scan failed for %s/%s", asset1, asset2, exc_info=True)

    # 4. Sort by p-value and categorize
    results.sort(key=lambda r: r["p_value"])
    cointegrated = [r for r in results if r["is_cointegrated"]]
    not_cointegrated = [r for r in results if not r["is_cointegrated"]]

    response = {
        "cointegrated": cointegrated,
        "not_cointegrated": not_cointegrated,
        "scanned": len(results),
        "timeframe": timeframe,
        "cached_coin_count": cached_coin_count,
        "dropped_for_completeness": dropped_for_completeness,
    }

    _scan_cache[cache_key] = response
    _scan_cache_ts[cache_key] = now
    return response
