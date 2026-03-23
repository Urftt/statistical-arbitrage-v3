"""Analysis endpoints: cointegration, spread, z-score, stationarity.

All endpoints wrap PairAnalysis and convert numpy types to native Python
for safe JSON serialization.
"""

import logging
from datetime import datetime, timedelta

import polars as pl
from fastapi import APIRouter, Depends, HTTPException

from api.schemas import (
    AnalysisRequest,
    CointegrationResponse,
    CriticalValues,
    SpreadProperties,
    SpreadRequest,
    SpreadResponse,
    StationarityRequest,
    StationarityResponse,
    StationarityResult,
    ZScoreRequest,
    ZScoreResponse,
    numpy_to_python,
)
from src.statistical_arbitrage.analysis.cointegration import PairAnalysis
from src.statistical_arbitrage.data.cache_manager import (
    DataCacheManager,
    get_cache_manager,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def _get_cache_mgr() -> DataCacheManager:
    """Dependency: returns the singleton DataCacheManager."""
    return get_cache_manager()


def _symbol_to_dash(symbol: str) -> str:
    """Convert internal symbol to dash format: ETH/EUR → ETH-EUR."""
    return symbol.replace("/", "-")


def _load_pair_data(
    asset1: str,
    asset2: str,
    timeframe: str,
    days_back: int,
    cache_mgr: DataCacheManager,
) -> tuple[pl.Series, pl.Series, list[int]]:
    """Load and align close-price series for two assets from parquet cache.

    Returns (asset1_close, asset2_close, timestamps).
    Raises HTTPException 404 if cache files are missing.
    """
    cache_dir = cache_mgr.cache_dir

    for symbol in (asset1, asset2):
        dash = _symbol_to_dash(symbol)
        path = cache_dir / f"{dash}_{timeframe}.parquet"
        if not path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Cache not found for {symbol} at {timeframe}",
            )

    # Read both parquet files
    df1 = pl.read_parquet(cache_dir / f"{_symbol_to_dash(asset1)}_{timeframe}.parquet")
    df2 = pl.read_parquet(cache_dir / f"{_symbol_to_dash(asset2)}_{timeframe}.parquet")

    # Filter by days_back
    cutoff_ms = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)
    df1 = df1.filter(pl.col("timestamp") >= cutoff_ms)
    df2 = df2.filter(pl.col("timestamp") >= cutoff_ms)

    if df1.is_empty() or df2.is_empty():
        raise HTTPException(
            status_code=404,
            detail=f"No data within {days_back} days for one or both assets.",
        )

    # Inner-join on timestamp to align both series
    joined = df1.select(
        pl.col("timestamp"),
        pl.col("close").alias("close_1"),
    ).join(
        df2.select(
            pl.col("timestamp"),
            pl.col("close").alias("close_2"),
        ),
        on="timestamp",
        how="inner",
    ).sort("timestamp")

    if joined.is_empty():
        raise HTTPException(
            status_code=404,
            detail="No overlapping timestamps between the two assets.",
        )

    return (
        joined["close_1"],
        joined["close_2"],
        joined["timestamp"].to_list(),
    )


def _build_critical_values(cv_dict: dict) -> CriticalValues:
    """Convert the critical_values dict from ADF/cointegration to CriticalValues model.

    Handles both '1%'/'5%'/'10%' keys (from test_cointegration)
    and Pandas-style '1%'/'5%'/'10%' keys (from adfuller).
    """
    cleaned = numpy_to_python(cv_dict)
    return CriticalValues(
        one_pct=cleaned.get("1%", cleaned.get("1%", 0.0)),
        five_pct=cleaned.get("5%", cleaned.get("5%", 0.0)),
        ten_pct=cleaned.get("10%", cleaned.get("10%", 0.0)),
    )


def _build_stationarity_result(raw: dict) -> StationarityResult:
    """Convert raw stationarity dict to StationarityResult model."""
    cleaned = numpy_to_python(raw)
    return StationarityResult(
        name=cleaned["name"],
        adf_statistic=cleaned["adf_statistic"],
        p_value=cleaned["p_value"],
        critical_values=_build_critical_values(cleaned["critical_values"]),
        is_stationary=cleaned["is_stationary"],
        interpretation=cleaned["interpretation"],
    )


# ---------------------------------------------------------------------------
# POST /api/analysis/cointegration
# ---------------------------------------------------------------------------


@router.post("/cointegration", response_model=CointegrationResponse)
def run_cointegration(
    request: AnalysisRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> CointegrationResponse:
    """Run full cointegration analysis on a pair of assets.

    Returns Engle-Granger test results, hedge ratio, spread, z-score,
    half-life, correlation, spread stationarity, and spread properties.
    """
    close1, close2, timestamps = _load_pair_data(
        request.asset1, request.asset2, request.timeframe, request.days_back, cache_mgr
    )

    try:
        pa = PairAnalysis(close1, close2)
        coint_raw = pa.test_cointegration()
        spread_raw = pa.calculate_spread(method="ols")
        zscore_raw = pa.calculate_zscore(window=60)
        half_life_raw = pa.calculate_half_life()
        correlation_raw = pa.get_correlation()
        spread_props_raw = pa.analyze_spread_properties()
    except Exception as e:
        logger.exception("Analysis failed for %s / %s", request.asset1, request.asset2)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}") from e

    # Convert all numpy types
    coint = numpy_to_python(coint_raw)
    spread = numpy_to_python(spread_raw)
    zscore = numpy_to_python(zscore_raw)
    half_life = numpy_to_python(half_life_raw)
    correlation = numpy_to_python(correlation_raw)
    spread_props = numpy_to_python(spread_props_raw)

    # Handle infinite/None half-life
    half_life_note = None
    if half_life is None:
        half_life_note = "No mean reversion detected (half-life is infinite)"
        logger.warning(
            "Half-life is infinite for %s / %s — no mean reversion",
            request.asset1, request.asset2,
        )

    return CointegrationResponse(
        cointegration_score=coint["cointegration_score"],
        p_value=coint["p_value"],
        critical_values=_build_critical_values(coint["critical_values"]),
        is_cointegrated=coint["is_cointegrated"],
        hedge_ratio=coint["hedge_ratio"],
        intercept=coint["intercept"],
        spread=spread,
        zscore=zscore,
        half_life=half_life,
        half_life_note=half_life_note,
        correlation=correlation,
        spread_stationarity=_build_stationarity_result(coint["spread_stationarity"]),
        spread_properties=SpreadProperties(**spread_props),
        interpretation=coint["interpretation"],
        timestamps=timestamps,
    )


# ---------------------------------------------------------------------------
# POST /api/analysis/spread
# ---------------------------------------------------------------------------


@router.post("/spread", response_model=SpreadResponse)
def run_spread(
    request: SpreadRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> SpreadResponse:
    """Calculate spread between a pair of assets."""
    close1, close2, timestamps = _load_pair_data(
        request.asset1, request.asset2, request.timeframe, request.days_back, cache_mgr
    )

    try:
        pa = PairAnalysis(close1, close2)
        spread_raw = pa.calculate_spread(method=request.method)
    except Exception as e:
        logger.exception("Spread calculation failed for %s / %s", request.asset1, request.asset2)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}") from e

    spread = numpy_to_python(spread_raw)
    return SpreadResponse(spread=spread, method=request.method, timestamps=timestamps)


# ---------------------------------------------------------------------------
# POST /api/analysis/zscore
# ---------------------------------------------------------------------------


@router.post("/zscore", response_model=ZScoreResponse)
def run_zscore(
    request: ZScoreRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> ZScoreResponse:
    """Calculate rolling z-score of the spread between a pair of assets."""
    close1, close2, timestamps = _load_pair_data(
        request.asset1, request.asset2, request.timeframe, request.days_back, cache_mgr
    )

    try:
        pa = PairAnalysis(close1, close2)
        pa.calculate_spread(method="ols")
        zscore_raw = pa.calculate_zscore(window=request.lookback_window)
    except Exception as e:
        logger.exception("Z-score calculation failed for %s / %s", request.asset1, request.asset2)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}") from e

    zscore = numpy_to_python(zscore_raw)
    return ZScoreResponse(
        zscore=zscore,
        lookback_window=request.lookback_window,
        timestamps=timestamps,
    )


# ---------------------------------------------------------------------------
# POST /api/analysis/stationarity
# ---------------------------------------------------------------------------


@router.post("/stationarity", response_model=StationarityResponse)
def run_stationarity(
    request: StationarityRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> StationarityResponse:
    """Run ADF stationarity test on a specified series (asset1, asset2, or spread)."""
    close1, close2, timestamps = _load_pair_data(
        request.asset1, request.asset2, request.timeframe, request.days_back, cache_mgr
    )

    try:
        pa = PairAnalysis(close1, close2)

        if request.series_name == "asset1":
            series = pa.asset1
            name = request.asset1
        elif request.series_name == "asset2":
            series = pa.asset2
            name = request.asset2
        elif request.series_name == "spread":
            pa.calculate_spread(method="ols")
            series = pa.spread
            name = "Spread"
        else:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid series_name '{request.series_name}'. Must be 'asset1', 'asset2', or 'spread'.",
            )

        result_raw = pa.test_stationarity(series, name)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Stationarity test failed for %s / %s", request.asset1, request.asset2)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}") from e

    result = numpy_to_python(result_raw)
    return StationarityResponse(
        name=result["name"],
        adf_statistic=result["adf_statistic"],
        p_value=result["p_value"],
        critical_values=_build_critical_values(result["critical_values"]),
        is_stationary=result["is_stationary"],
        interpretation=result["interpretation"],
    )
