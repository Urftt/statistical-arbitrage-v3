"""Research endpoints for connected research-to-backtest workflows."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import numpy as np
import polars as pl
from fastapi import APIRouter, Depends, HTTPException

from api.routers.analysis import _get_cache_mgr, _load_pair_data
from api.schemas import (
    BacktestRequest,
    CointMethodRequest,
    CointMethodResponse,
    CointMethodResultPayload,
    LookbackSweepRequest,
    LookbackSweepResponse,
    LookbackWindowResultPayload,
    OOSResultPayload,
    OOSValidationRequest,
    OOSValidationResponse,
    ResearchTakeawayPayload,
    RollingStabilityRequest,
    RollingStabilityResponse,
    RollingStabilityResultPayload,
    SpreadMethodRequest,
    SpreadMethodResponse,
    SpreadMethodResultPayload,
    StrategyParametersPayload,
    ThresholdResultPayload,
    TimeframeRequest,
    TimeframeResponse,
    TimeframeResultPayload,
    TxCostRequest,
    TxCostResponse,
    TxCostResultPayload,
    ZScoreThresholdRequest,
    ZScoreThresholdResponse,
    numpy_to_python,
)
from src.statistical_arbitrage.analysis.research import (
    LookbackResult,
    compare_cointegration_methods,
    compare_spread_methods,
    compare_timeframes,
    coint_methods_takeaway,
    lookback_window_takeaway,
    oos_validation_takeaway,
    out_of_sample_validation,
    rolling_cointegration,
    rolling_cointegration_takeaway,
    spread_methods_takeaway,
    sweep_lookback_windows,
    sweep_zscore_thresholds,
    timeframe_takeaway,
    transaction_cost_analysis,
    tx_cost_takeaway,
    zscore_threshold_takeaway,
)
from src.statistical_arbitrage.data.cache_manager import DataCacheManager
from statistical_arbitrage.backtesting.engine import default_strategy_parameters

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/research", tags=["research"])


def _pick_recommended_window(results: list[LookbackResult]) -> LookbackResult:
    """Match the research module's selection heuristic for a recommended preset."""
    good = [result for result in results if result.autocorrelation > 0.9 and result.crossings_2 > 0]
    if good:
        return max(good, key=lambda result: result.crossings_2)
    return max(results, key=lambda result: result.crossings_2)


@router.post("/lookback-window", response_model=LookbackSweepResponse)
def run_lookback_window_sweep(
    request: LookbackSweepRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> LookbackSweepResponse:
    """Run the first real research module and emit a compatible backtest preset."""
    if request.windows is not None and any(window < 2 for window in request.windows):
        raise HTTPException(
            status_code=422,
            detail="All lookback windows must be at least 2 bars.",
        )

    close1, close2, _ = _load_pair_data(
        request.asset1,
        request.asset2,
        request.timeframe,
        request.days_back,
        cache_mgr,
    )

    try:
        prices1 = close1.to_numpy()
        prices2 = close2.to_numpy()
        hedge_ratio = float(np.polyfit(prices2, prices1, 1)[0])
        spread = prices1 - (hedge_ratio * prices2)
        raw_results = sweep_lookback_windows(spread, windows=request.windows)
    except Exception as exc:
        logger.exception(
            "Lookback sweep failed for %s / %s",
            request.asset1,
            request.asset2,
        )
        raise HTTPException(status_code=500, detail=f"Lookback sweep failed: {exc}") from exc

    if not raw_results:
        raise HTTPException(
            status_code=422,
            detail="Not enough overlapping data to compute any lookback window results.",
        )

    takeaway = lookback_window_takeaway(raw_results)
    recommended = _pick_recommended_window(raw_results)
    strategy_defaults = default_strategy_parameters().model_dump()
    strategy_defaults["lookback_window"] = recommended.window
    strategy_payload = StrategyParametersPayload(**strategy_defaults)
    recommended_request = BacktestRequest(
        asset1=request.asset1,
        asset2=request.asset2,
        timeframe=request.timeframe,
        days_back=request.days_back,
        strategy=strategy_payload,
    )

    results = [LookbackWindowResultPayload(**result.__dict__) for result in raw_results]

    return LookbackSweepResponse(
        asset1=request.asset1,
        asset2=request.asset2,
        timeframe=request.timeframe,
        days_back=request.days_back,
        observations=len(close1),
        hedge_ratio=hedge_ratio,
        results=results,
        takeaway=ResearchTakeawayPayload(
            text=takeaway.text,
            severity=takeaway.severity,
        ),
        recommended_result=LookbackWindowResultPayload(**recommended.__dict__),
        recommended_backtest_params=recommended_request,
    )


# ---------------------------------------------------------------------------
# Helper: pre-compute z-score from prices (used by threshold & tx-cost)
# ---------------------------------------------------------------------------


def _compute_zscore(
    prices1: np.ndarray, prices2: np.ndarray, lookback_window: int
) -> np.ndarray:
    """Compute z-score of the OLS spread using Polars rolling stats."""
    hedge_ratio = float(np.polyfit(prices2, prices1, 1)[0])
    spread = prices1 - hedge_ratio * prices2
    spread_series = pl.Series(spread)
    rolling_mean = spread_series.rolling_mean(window_size=lookback_window)
    rolling_std = spread_series.rolling_std(window_size=lookback_window)
    return ((spread_series - rolling_mean) / rolling_std).to_numpy()


# ---------------------------------------------------------------------------
# POST /api/research/rolling-stability
# ---------------------------------------------------------------------------


@router.post("/rolling-stability", response_model=RollingStabilityResponse)
def run_rolling_stability(
    request: RollingStabilityRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> RollingStabilityResponse:
    """Compute rolling cointegration stability over a sliding window."""
    close1, close2, timestamps = _load_pair_data(
        request.asset1, request.asset2, request.timeframe, request.days_back, cache_mgr,
    )

    try:
        prices1 = close1.to_numpy()
        prices2 = close2.to_numpy()
        result_df = rolling_cointegration(
            prices1, prices2, timestamps, window=request.window,
        )
    except Exception as exc:
        logger.exception("Rolling stability failed for %s / %s", request.asset1, request.asset2)
        raise HTTPException(status_code=500, detail=f"Rolling stability failed: {exc}") from exc

    takeaway = rolling_cointegration_takeaway(result_df)
    rows = result_df.to_dicts()
    results = [RollingStabilityResultPayload(**numpy_to_python(row)) for row in rows]

    return RollingStabilityResponse(
        asset1=request.asset1,
        asset2=request.asset2,
        timeframe=request.timeframe,
        days_back=request.days_back,
        observations=len(close1),
        results=results,
        takeaway=ResearchTakeawayPayload(text=takeaway.text, severity=takeaway.severity),
        recommended_backtest_params=None,
    )


# ---------------------------------------------------------------------------
# POST /api/research/oos-validation
# ---------------------------------------------------------------------------


@router.post("/oos-validation", response_model=OOSValidationResponse)
def run_oos_validation(
    request: OOSValidationRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> OOSValidationResponse:
    """Test whether in-sample cointegration holds out-of-sample."""
    close1, close2, _ = _load_pair_data(
        request.asset1, request.asset2, request.timeframe, request.days_back, cache_mgr,
    )

    try:
        prices1 = close1.to_numpy()
        prices2 = close2.to_numpy()
        raw_results = out_of_sample_validation(
            prices1, prices2, split_ratios=request.split_ratios,
        )
    except Exception as exc:
        logger.exception("OOS validation failed for %s / %s", request.asset1, request.asset2)
        raise HTTPException(status_code=500, detail=f"OOS validation failed: {exc}") from exc

    takeaway = oos_validation_takeaway(raw_results)
    results = [OOSResultPayload(**numpy_to_python(r.__dict__)) for r in raw_results]

    return OOSValidationResponse(
        asset1=request.asset1,
        asset2=request.asset2,
        timeframe=request.timeframe,
        days_back=request.days_back,
        observations=len(close1),
        results=results,
        takeaway=ResearchTakeawayPayload(text=takeaway.text, severity=takeaway.severity),
        recommended_backtest_params=None,
    )


# ---------------------------------------------------------------------------
# POST /api/research/timeframe-comparison
# ---------------------------------------------------------------------------


@router.post("/timeframe-comparison", response_model=TimeframeResponse)
def run_timeframe_comparison(
    request: TimeframeRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> TimeframeResponse:
    """Compare cointegration quality across multiple timeframes."""

    def get_merged_fn(a1: str, a2: str, tf: str):
        try:
            cache_dir = cache_mgr.cache_dir
            path1 = cache_dir / f"{a1.replace('/', '-')}_{tf}.parquet"
            path2 = cache_dir / f"{a2.replace('/', '-')}_{tf}.parquet"
            if not path1.exists() or not path2.exists():
                return None
            df1 = pl.read_parquet(path1)
            df2 = pl.read_parquet(path2)
            # Apply days_back filter
            cutoff_ms = int(
                (datetime.now() - timedelta(days=request.days_back)).timestamp() * 1000
            )
            df1 = df1.filter(pl.col("timestamp") >= cutoff_ms)
            df2 = df2.filter(pl.col("timestamp") >= cutoff_ms)
            merged = df1.select(
                [pl.col("timestamp"), pl.col("close").alias("c1")]
            ).join(
                df2.select([pl.col("timestamp"), pl.col("close").alias("c2")]),
                on="timestamp",
                how="inner",
            )
            return merged if len(merged) >= 30 else None
        except Exception:
            return None

    try:
        raw_results = compare_timeframes(
            get_merged_fn,
            request.asset1,
            request.asset2,
            timeframes=request.timeframes,
        )
    except Exception as exc:
        logger.exception(
            "Timeframe comparison failed for %s / %s", request.asset1, request.asset2,
        )
        raise HTTPException(
            status_code=500, detail=f"Timeframe comparison failed: {exc}",
        ) from exc

    takeaway = timeframe_takeaway(raw_results)
    total_obs = sum(r.n_datapoints for r in raw_results)
    results = [TimeframeResultPayload(**numpy_to_python(r.__dict__)) for r in raw_results]

    return TimeframeResponse(
        asset1=request.asset1,
        asset2=request.asset2,
        timeframe="multi",
        days_back=request.days_back,
        observations=total_obs,
        results=results,
        takeaway=ResearchTakeawayPayload(text=takeaway.text, severity=takeaway.severity),
        recommended_backtest_params=None,
    )


# ---------------------------------------------------------------------------
# POST /api/research/spread-method
# ---------------------------------------------------------------------------


@router.post("/spread-method", response_model=SpreadMethodResponse)
def run_spread_method_comparison(
    request: SpreadMethodRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> SpreadMethodResponse:
    """Compare spread construction methods by stationarity."""
    close1, close2, _ = _load_pair_data(
        request.asset1, request.asset2, request.timeframe, request.days_back, cache_mgr,
    )

    try:
        prices1 = close1.to_numpy()
        prices2 = close2.to_numpy()
        raw_results = compare_spread_methods(prices1, prices2)
    except Exception as exc:
        logger.exception("Spread method comparison failed for %s / %s", request.asset1, request.asset2)
        raise HTTPException(
            status_code=500, detail=f"Spread method comparison failed: {exc}",
        ) from exc

    takeaway = spread_methods_takeaway(raw_results)
    # Omit the raw spread array from the API payload — only scalar diagnostics
    results = [
        SpreadMethodResultPayload(
            method=r.method,
            adf_statistic=numpy_to_python(r.adf_statistic),
            adf_p_value=numpy_to_python(r.adf_p_value),
            is_stationary=r.is_stationary,
            spread_std=numpy_to_python(r.spread_std),
            spread_skewness=numpy_to_python(r.spread_skewness),
            spread_kurtosis=numpy_to_python(r.spread_kurtosis),
        )
        for r in raw_results
    ]

    return SpreadMethodResponse(
        asset1=request.asset1,
        asset2=request.asset2,
        timeframe=request.timeframe,
        days_back=request.days_back,
        observations=len(close1),
        results=results,
        takeaway=ResearchTakeawayPayload(text=takeaway.text, severity=takeaway.severity),
        recommended_backtest_params=None,
    )


# ---------------------------------------------------------------------------
# POST /api/research/zscore-threshold
# ---------------------------------------------------------------------------


@router.post("/zscore-threshold", response_model=ZScoreThresholdResponse)
def run_zscore_threshold_sweep(
    request: ZScoreThresholdRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> ZScoreThresholdResponse:
    """Sweep z-score entry/exit thresholds and count trading signals."""
    close1, close2, _ = _load_pair_data(
        request.asset1, request.asset2, request.timeframe, request.days_back, cache_mgr,
    )

    try:
        prices1 = close1.to_numpy()
        prices2 = close2.to_numpy()
        zscore = _compute_zscore(prices1, prices2, request.lookback_window)
        raw_results = sweep_zscore_thresholds(
            zscore,
            entry_range=request.entry_range,
            exit_range=request.exit_range,
        )
    except Exception as exc:
        logger.exception(
            "Z-score threshold sweep failed for %s / %s", request.asset1, request.asset2,
        )
        raise HTTPException(
            status_code=500, detail=f"Z-score threshold sweep failed: {exc}",
        ) from exc

    takeaway = zscore_threshold_takeaway(raw_results)
    observations = int(np.sum(~np.isnan(zscore)))
    results = [ThresholdResultPayload(**numpy_to_python(r.__dict__)) for r in raw_results]

    # Pick the threshold combo with max trades for recommended backtest
    recommended: BacktestRequest | None = None
    with_trades = [r for r in raw_results if r.total_trades > 0]
    if with_trades:
        best = max(with_trades, key=lambda r: r.total_trades)
        strategy_defaults = default_strategy_parameters().model_dump()
        strategy_defaults["entry_threshold"] = best.entry
        strategy_defaults["exit_threshold"] = best.exit
        strategy_defaults["lookback_window"] = request.lookback_window
        recommended = BacktestRequest(
            asset1=request.asset1,
            asset2=request.asset2,
            timeframe=request.timeframe,
            days_back=request.days_back,
            strategy=StrategyParametersPayload(**strategy_defaults),
        )

    return ZScoreThresholdResponse(
        asset1=request.asset1,
        asset2=request.asset2,
        timeframe=request.timeframe,
        days_back=request.days_back,
        observations=observations,
        results=results,
        takeaway=ResearchTakeawayPayload(text=takeaway.text, severity=takeaway.severity),
        recommended_backtest_params=recommended,
    )


# ---------------------------------------------------------------------------
# POST /api/research/tx-cost
# ---------------------------------------------------------------------------


@router.post("/tx-cost", response_model=TxCostResponse)
def run_tx_cost_analysis(
    request: TxCostRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> TxCostResponse:
    """Analyze how transaction costs affect profitability at various fee levels."""
    close1, close2, _ = _load_pair_data(
        request.asset1, request.asset2, request.timeframe, request.days_back, cache_mgr,
    )

    try:
        prices1 = close1.to_numpy()
        prices2 = close2.to_numpy()
        zscore = _compute_zscore(prices1, prices2, request.lookback_window)
        raw_results = transaction_cost_analysis(
            prices1,
            prices2,
            zscore,
            entry_threshold=request.entry_threshold,
            exit_threshold=request.exit_threshold,
            fee_levels=request.fee_levels,
        )
    except Exception as exc:
        logger.exception("Tx cost analysis failed for %s / %s", request.asset1, request.asset2)
        raise HTTPException(
            status_code=500, detail=f"Transaction cost analysis failed: {exc}",
        ) from exc

    takeaway = tx_cost_takeaway(raw_results)
    observations = int(np.sum(~np.isnan(zscore)))
    results = [TxCostResultPayload(**numpy_to_python(r.__dict__)) for r in raw_results]

    # Always return a BacktestRequest with Bitvavo fee (0.25%) and given thresholds
    strategy_defaults = default_strategy_parameters().model_dump()
    strategy_defaults["entry_threshold"] = request.entry_threshold
    strategy_defaults["exit_threshold"] = request.exit_threshold
    strategy_defaults["lookback_window"] = request.lookback_window
    strategy_defaults["transaction_fee"] = 0.0025  # Bitvavo 0.25%
    recommended = BacktestRequest(
        asset1=request.asset1,
        asset2=request.asset2,
        timeframe=request.timeframe,
        days_back=request.days_back,
        strategy=StrategyParametersPayload(**strategy_defaults),
    )

    return TxCostResponse(
        asset1=request.asset1,
        asset2=request.asset2,
        timeframe=request.timeframe,
        days_back=request.days_back,
        observations=observations,
        results=results,
        takeaway=ResearchTakeawayPayload(text=takeaway.text, severity=takeaway.severity),
        recommended_backtest_params=recommended,
    )


# ---------------------------------------------------------------------------
# POST /api/research/coint-method
# ---------------------------------------------------------------------------


@router.post("/coint-method", response_model=CointMethodResponse)
def run_coint_method_comparison(
    request: CointMethodRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> CointMethodResponse:
    """Compare Engle-Granger and Johansen cointegration tests."""
    close1, close2, _ = _load_pair_data(
        request.asset1, request.asset2, request.timeframe, request.days_back, cache_mgr,
    )

    try:
        prices1 = close1.to_numpy()
        prices2 = close2.to_numpy()
        raw_results = compare_cointegration_methods(prices1, prices2)
    except Exception as exc:
        logger.exception(
            "Cointegration method comparison failed for %s / %s",
            request.asset1, request.asset2,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Cointegration method comparison failed: {exc}",
        ) from exc

    takeaway = coint_methods_takeaway(raw_results)
    results = [CointMethodResultPayload(**numpy_to_python(r.__dict__)) for r in raw_results]

    return CointMethodResponse(
        asset1=request.asset1,
        asset2=request.asset2,
        timeframe=request.timeframe,
        days_back=request.days_back,
        observations=len(close1),
        results=results,
        takeaway=ResearchTakeawayPayload(text=takeaway.text, severity=takeaway.severity),
        recommended_backtest_params=None,
    )
