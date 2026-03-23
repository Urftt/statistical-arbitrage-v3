"""Grid search and walk-forward optimization endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.routers.analysis import _get_cache_mgr, _load_pair_data
from api.schemas import (
    BacktestRequest,
    EngineWarningPayload,
    GridSearchCellPayload,
    GridSearchRequest,
    GridSearchResponse,
    HonestReportingFooterPayload,
    MetricSummaryPayload,
    ParameterAxisPayload,
    StrategyParametersPayload,
    WalkForwardFoldPayload,
    WalkForwardRequest,
    WalkForwardResponse,
)
from src.statistical_arbitrage.data.cache_manager import DataCacheManager
from statistical_arbitrage.backtesting.models import ParameterAxis, StrategyParameters
from statistical_arbitrage.backtesting.optimization import run_grid_search
from statistical_arbitrage.backtesting.walkforward import run_walk_forward

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/optimization", tags=["optimization"])


def _grid_search_footer() -> HonestReportingFooterPayload:
    """Honest reporting metadata for grid search results."""
    return HonestReportingFooterPayload(
        execution_model="Each grid cell runs a full look-ahead-safe backtest with signals at bar close and execution at the next bar's close.",
        fee_model="Transaction fees are charged on both legs at entry and exit using traded notional.",
        data_basis="All cells use the same price data and spread/z-score computation. The best cell is selected by in-sample metric only.",
        assumptions=[
            "Grid search optimizes over in-sample data — the best parameters may not generalize out-of-sample.",
            "Robustness score measures local smoothness, not predictive power.",
        ],
        limitations=[
            "This is a brute-force search; it does not explore the full continuous parameter space.",
            "Overfitting risk increases with the number of parameters and narrow grid steps.",
            "Walk-forward validation (separate endpoint) is recommended to assess out-of-sample stability.",
        ],
    )


@router.post("/grid-search", response_model=GridSearchResponse)
def execute_grid_search(
    request: GridSearchRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> GridSearchResponse:
    """Run a bounded multi-parameter grid search over strategy parameters.

    Returns per-cell metrics, best cell identification, robustness score,
    and overfitting/fragility warnings.
    """
    # Load pair data
    close1, close2, timestamps = _load_pair_data(
        request.asset1,
        request.asset2,
        request.timeframe,
        request.days_back,
        cache_mgr,
    )

    # Convert API types to engine types
    engine_axes = [
        ParameterAxis(
            name=ax.name,
            min_value=ax.min_value,
            max_value=ax.max_value,
            step=ax.step,
        )
        for ax in request.axes
    ]
    engine_params = StrategyParameters(**request.base_strategy.model_dump())

    try:
        result = run_grid_search(
            timestamps=timestamps,
            prices1=close1,
            prices2=close2,
            axes=engine_axes,
            base_params=engine_params,
            optimize_metric=request.optimize_metric,
            max_combinations=request.max_combinations,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "Grid search failed for %s / %s",
            request.asset1,
            request.asset2,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Grid search failed: {exc}",
        ) from exc

    # Build response cells
    response_cells = [
        GridSearchCellPayload(
            params=cell.params,
            metrics=MetricSummaryPayload(**cell.metrics.model_dump()),
            trade_count=cell.trade_count,
            status=cell.status,
        )
        for cell in result.cells
    ]

    # Build best cell payload
    best_cell_payload = None
    if result.best_cell is not None:
        best_cell_payload = GridSearchCellPayload(
            params=result.best_cell.params,
            metrics=MetricSummaryPayload(**result.best_cell.metrics.model_dump()),
            trade_count=result.best_cell.trade_count,
            status=result.best_cell.status,
        )

    # Build recommended backtest params from best cell
    recommended: BacktestRequest | None = None
    if result.best_cell is not None:
        recommended_strategy = StrategyParametersPayload(
            **engine_params.model_copy(update=result.best_cell.params).model_dump()
        )
        recommended = BacktestRequest(
            asset1=request.asset1,
            asset2=request.asset2,
            timeframe=request.timeframe,
            days_back=request.days_back,
            strategy=recommended_strategy,
        )

    response_axes = [
        ParameterAxisPayload(**ax.model_dump()) for ax in result.axes
    ]

    logger.info(
        "Grid search for %s/%s: %d combos, best_index=%s, robustness=%.3f, %.1fms",
        request.asset1,
        request.asset2,
        result.total_combinations,
        result.best_cell_index,
        result.robustness_score or 0.0,
        result.execution_time_ms,
    )

    return GridSearchResponse(
        grid_shape=result.grid_shape,
        axes=response_axes,
        cells=response_cells,
        best_cell_index=result.best_cell_index,
        best_cell=best_cell_payload,
        optimize_metric=result.optimize_metric,
        total_combinations=result.total_combinations,
        robustness_score=result.robustness_score,
        warnings=[
            EngineWarningPayload(**w.model_dump()) for w in result.warnings
        ],
        execution_time_ms=result.execution_time_ms,
        footer=_grid_search_footer(),
        recommended_backtest_params=recommended,
    )


def _walk_forward_footer() -> HonestReportingFooterPayload:
    """Honest reporting metadata for walk-forward validation results."""
    return HonestReportingFooterPayload(
        execution_model="Each fold runs grid search on its train window and evaluates the best parameters on a non-overlapping test window.",
        fee_model="Transaction fees are charged on both legs at entry and exit using traded notional.",
        data_basis="Train and test windows are sliced from the same cached price data with no overlap.",
        assumptions=[
            "Walk-forward uses rolling anchored windows — each fold starts later in the data.",
            "The stability verdict is based on the ratio of average test Sharpe to average train Sharpe.",
            "A 'stable' verdict does not guarantee future profitability.",
        ],
        limitations=[
            "Each fold's grid search optimizes in-sample; the test window evaluates only one set of best parameters.",
            "Small test windows may produce unreliable metrics due to insufficient trade count.",
            "Walk-forward does not account for regime changes within individual windows.",
        ],
    )


@router.post("/walk-forward", response_model=WalkForwardResponse)
def execute_walk_forward(
    request: WalkForwardRequest,
    cache_mgr: DataCacheManager = Depends(_get_cache_mgr),
) -> WalkForwardResponse:
    """Run walk-forward validation with rolling train/test windows.

    For each fold, optimizes parameters via grid search on the train window,
    then evaluates on the non-overlapping test window. Returns per-fold
    metrics, aggregate summary, and a stability verdict.
    """
    # Load pair data
    close1, close2, timestamps = _load_pair_data(
        request.asset1,
        request.asset2,
        request.timeframe,
        request.days_back,
        cache_mgr,
    )

    # Convert API types to engine types
    engine_axes = [
        ParameterAxis(
            name=ax.name,
            min_value=ax.min_value,
            max_value=ax.max_value,
            step=ax.step,
        )
        for ax in request.axes
    ]
    engine_params = StrategyParameters(**request.base_strategy.model_dump())

    try:
        result = run_walk_forward(
            timestamps=timestamps,
            prices1=close1,
            prices2=close2,
            axes=engine_axes,
            base_params=engine_params,
            fold_count=request.fold_count,
            train_pct=request.train_pct,
            optimize_metric=request.optimize_metric,
            max_combinations_per_fold=request.max_combinations_per_fold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "Walk-forward failed for %s / %s",
            request.asset1,
            request.asset2,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Walk-forward validation failed: {exc}",
        ) from exc

    # Build response folds
    response_folds = [
        WalkForwardFoldPayload(
            fold_index=fold.fold_index,
            train_start_idx=fold.train_start_idx,
            train_end_idx=fold.train_end_idx,
            test_start_idx=fold.test_start_idx,
            test_end_idx=fold.test_end_idx,
            train_bars=fold.train_bars,
            test_bars=fold.test_bars,
            best_params=fold.best_params,
            train_metrics=MetricSummaryPayload(**fold.train_metrics.model_dump()),
            test_metrics=MetricSummaryPayload(**fold.test_metrics.model_dump()),
            train_trade_count=fold.train_trade_count,
            test_trade_count=fold.test_trade_count,
            status=fold.status,
        )
        for fold in result.folds
    ]

    response_axes = [
        ParameterAxisPayload(**ax.model_dump()) for ax in result.axes
    ]

    # Build recommended backtest params from the best test fold (if stable/moderate)
    recommended: BacktestRequest | None = None
    if result.stability_verdict in ("stable", "moderate"):
        # Find the fold with the best test Sharpe
        best_fold = None
        best_test_sharpe: float | None = None
        for fold in result.folds:
            if fold.status == "ok" and fold.test_metrics.sharpe_ratio is not None:
                if best_test_sharpe is None or fold.test_metrics.sharpe_ratio > best_test_sharpe:
                    best_test_sharpe = fold.test_metrics.sharpe_ratio
                    best_fold = fold

        if best_fold is not None and best_fold.best_params:
            recommended_strategy = StrategyParametersPayload(
                **engine_params.model_copy(update=best_fold.best_params).model_dump()
            )
            recommended = BacktestRequest(
                asset1=request.asset1,
                asset2=request.asset2,
                timeframe=request.timeframe,
                days_back=request.days_back,
                strategy=recommended_strategy,
            )

    logger.info(
        "Walk-forward for %s/%s: %d folds, verdict=%s, divergence=%s, %.1fms",
        request.asset1,
        request.asset2,
        result.fold_count,
        result.stability_verdict,
        f"{result.train_test_divergence:.3f}" if result.train_test_divergence is not None else "N/A",
        result.execution_time_ms,
    )

    return WalkForwardResponse(
        folds=response_folds,
        fold_count=result.fold_count,
        train_pct=result.train_pct,
        axes=response_axes,
        aggregate_train_sharpe=result.aggregate_train_sharpe,
        aggregate_test_sharpe=result.aggregate_test_sharpe,
        train_test_divergence=result.train_test_divergence,
        stability_verdict=result.stability_verdict,
        warnings=[
            EngineWarningPayload(**w.model_dump()) for w in result.warnings
        ],
        execution_time_ms=result.execution_time_ms,
        footer=_walk_forward_footer(),
        recommended_backtest_params=recommended,
    )
