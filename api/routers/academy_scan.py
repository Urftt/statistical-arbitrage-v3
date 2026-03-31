"""Academy pair scan + live data fetch endpoints.

Scans cached pairs for cointegration and returns categorized results.
Automatically fetches fresh data from Bitvavo when cache is stale.
"""

import logging
import time
from itertools import combinations

import polars as pl
from fastapi import APIRouter, Depends, Query

from api.schemas import numpy_to_python
from src.statistical_arbitrage.analysis.cointegration import PairAnalysis
from src.statistical_arbitrage.data.cache_manager import (
    DataCacheManager,
    get_cache_manager,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/academy", tags=["academy"])

# In-memory caches with TTL
_scan_cache: dict[str, dict] = {}
_scan_cache_ts: dict[str, float] = {}
SCAN_CACHE_TTL = 300  # 5 minutes — scan results are cached briefly


def _get_cache_mgr() -> DataCacheManager:
    return get_cache_manager()


def _symbol_to_dash(symbol: str) -> str:
    return symbol.replace("/", "-")


# ---------------------------------------------------------------------------
# POST /api/academy/fetch — Fetch fresh data from Bitvavo
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
    """
    try:
        # Get available EUR pairs from Bitvavo
        available = cache_mgr.get_available_pairs()
        symbols = available["symbol"].to_list()[:max_coins]

        fetched = []
        for symbol in symbols:
            try:
                df = cache_mgr.get_candles(symbol, timeframe, days_back=days_back)
                fetched.append({
                    "symbol": symbol,
                    "candles": len(df),
                    "timeframe": timeframe,
                })
            except Exception as e:
                logger.warning("Failed to fetch %s: %s", symbol, e)
                fetched.append({
                    "symbol": symbol,
                    "candles": 0,
                    "timeframe": timeframe,
                    "error": str(e),
                })

        # Clear scan cache so next scan uses fresh data
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
# GET /api/academy/scan — Scan pairs for cointegration (auto-refreshes data)
# ---------------------------------------------------------------------------


@router.get("/scan")
def scan_pairs(
    timeframe: str = Query(default="1h", description="Timeframe to test"),
    days_back: int = Query(default=90, ge=7, le=365, description="Days of history"),
    max_pairs: int = Query(default=20, ge=2, le=50, description="Max base assets to scan"),
    fresh: bool = Query(default=True, description="Auto-fetch fresh data from Bitvavo"),
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> dict:
    """Scan pairs for cointegration with automatic data freshness.

    When fresh=True (default), automatically fetches the latest data from
    Bitvavo before scanning. This ensures the Academy always shows live,
    up-to-date data.

    Returns pairs sorted by p-value, categorized into 'cointegrated'
    (p < 0.05) and 'not_cointegrated' groups.
    """
    cache_key = f"{timeframe}-{days_back}-{max_pairs}-{fresh}"
    now = time.time()

    # Return cached results if fresh enough
    if cache_key in _scan_cache and (now - _scan_cache_ts.get(cache_key, 0)) < SCAN_CACHE_TTL:
        return _scan_cache[cache_key]

    # 1. Determine which symbols to scan
    if fresh:
        # Get all available EUR pairs from Bitvavo and fetch fresh data
        try:
            available = cache_mgr.get_available_pairs()
            symbols = available["symbol"].to_list()[:max_pairs]
            logger.info("Fetching fresh data for %d symbols...", len(symbols))
        except Exception:
            logger.warning("Could not get Bitvavo pairs, falling back to cache")
            symbols = []
            fresh = False

        if fresh:
            for symbol in symbols:
                try:
                    cache_mgr.get_candles(symbol, timeframe, days_back=days_back)
                except Exception:
                    logger.warning("Failed to refresh %s", symbol)

    # 2. Find available base assets from cache
    cached = cache_mgr.list_cached()
    base_assets: set[str] = set()
    for info in cached:
        symbol: str = info["symbol"]
        tf: str = info["timeframe"]
        if tf == timeframe and "/" in symbol:
            base = symbol.split("/")[0]
            base_assets.add(base)

    base_list = sorted(base_assets)[:max_pairs]

    if len(base_list) < 2:
        return {"cointegrated": [], "not_cointegrated": [], "scanned": 0, "timeframe": timeframe}

    # 3. Pre-load close price series, filtering for data quality
    series_map: dict[str, pl.DataFrame] = {}
    min_completeness = 0.90  # Require 90%+ data completeness for clean charts

    for base in base_list:
        symbol = f"{base}/EUR"
        try:
            df = cache_mgr.get_candles(symbol, timeframe, days_back=days_back)
            if len(df) < 100:
                continue

            # Check data completeness — reject gappy altcoins
            ts = df["timestamp"].sort().to_list()
            total_hours = (ts[-1] - ts[0]) / 3_600_000
            expected = max(int(total_hours), 1)
            completeness = len(df) / expected

            if completeness < min_completeness:
                logger.info(
                    "Skipping %s — %.1f%% complete (need %.0f%%)",
                    symbol, completeness * 100, min_completeness * 100,
                )
                continue

            series_map[base] = df
        except Exception:
            logger.warning("Failed to load %s", symbol)

    # 4. Test all combinations
    results = []
    available_bases = list(series_map.keys())

    for asset1, asset2 in combinations(available_bases, 2):
        try:
            df1 = series_map[asset1]
            df2 = series_map[asset2]

            # Align on timestamp
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

            results.append({
                "asset1": f"{asset1}/EUR",
                "asset2": f"{asset2}/EUR",
                "p_value": coint["p_value"],
                "is_cointegrated": coint["is_cointegrated"],
                "hedge_ratio": coint["hedge_ratio"],
                "half_life": half_life,
                "correlation": correlation,
                "cointegration_score": coint["cointegration_score"],
                "observations": len(joined),
            })
        except Exception:
            logger.warning("Scan failed for %s/%s", asset1, asset2, exc_info=True)

    # 5. Sort and categorize
    results.sort(key=lambda r: r["p_value"])

    cointegrated = [r for r in results if r["is_cointegrated"]]
    not_cointegrated = [r for r in results if not r["is_cointegrated"]]

    response = {
        "cointegrated": cointegrated,
        "not_cointegrated": not_cointegrated,
        "scanned": len(results),
        "timeframe": timeframe,
        "base_assets": len(available_bases),
    }

    # Cache the result
    _scan_cache[cache_key] = response
    _scan_cache_ts[cache_key] = now
    return response
