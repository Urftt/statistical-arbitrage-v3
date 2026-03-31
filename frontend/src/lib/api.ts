/**
 * Typed API client for the FastAPI backend.
 *
 * Base URL defaults to http://localhost:8000, overridable via
 * NEXT_PUBLIC_API_URL environment variable.
 */

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export const TIMEFRAME_OPTIONS = [
  { label: '15 min', value: '15m' },
  { label: '1 hour', value: '1h' },
  { label: '4 hours', value: '4h' },
  { label: '1 day', value: '1d' },
] as const;

export interface StrategyParametersPayload {
  lookback_window: number;
  entry_threshold: number;
  exit_threshold: number;
  stop_loss: number;
  initial_capital: number;
  position_size: number;
  transaction_fee: number;
  min_trade_count_warning: number;
}

export const DEFAULT_STRATEGY_PARAMETERS: StrategyParametersPayload = {
  lookback_window: 60,
  entry_threshold: 2,
  exit_threshold: 0.5,
  stop_loss: 3,
  initial_capital: 10_000,
  position_size: 0.5,
  transaction_fee: 0.0025,
  min_trade_count_warning: 3,
};

// ---------------------------------------------------------------------------
// Interfaces — match FastAPI schemas (api/schemas.py)
// ---------------------------------------------------------------------------

export interface PairInfo {
  symbol: string;
  base: string;
  quote: string;
  timeframe: string;
  candles: number;
  start: string;
  end: string;
  file_size_mb: number;
}

export interface PairsListResponse {
  pairs: PairInfo[];
}

export interface OHLCVResponse {
  symbol: string;
  timeframe: string;
  count: number;
  timestamps: number[];
  open: number[];
  high: number[];
  low: number[];
  close: number[];
  volume: number[];
}

export interface CointegrationRequest {
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back?: number;
}

export interface CriticalValues {
  one_pct: number;
  five_pct: number;
  ten_pct: number;
}

export interface StationarityResult {
  name: string;
  adf_statistic: number;
  p_value: number;
  critical_values: CriticalValues;
  is_stationary: boolean;
  interpretation: string;
}

export interface SpreadProperties {
  mean: number;
  std: number;
  min: number;
  max: number;
  median: number;
  skewness: number;
  kurtosis: number;
  autocorr_lag1: number;
}

export interface CointegrationResponse {
  cointegration_score: number;
  p_value: number;
  critical_values: CriticalValues;
  is_cointegrated: boolean;
  hedge_ratio: number;
  intercept: number;
  spread: (number | null)[];
  zscore: (number | null)[];
  half_life: number | null;
  half_life_note: string | null;
  correlation: number;
  spread_stationarity: StationarityResult;
  spread_properties: SpreadProperties;
  interpretation: string;
  timestamps: number[];
}

export interface BacktestRequest {
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  strategy: StrategyParametersPayload;
}

export interface EngineWarningPayload {
  code: string;
  severity: 'warning' | 'blocking';
  message: string;
  details: Record<string, number | string | boolean | null | undefined>;
}

export interface DataQualityReportPayload {
  status: 'passed' | 'blocked';
  observations_total: number;
  observations_usable: number;
  warmup_bars: number;
  blockers: EngineWarningPayload[];
  warnings: EngineWarningPayload[];
}

export interface HonestReportingFooterPayload {
  execution_model: string;
  fee_model: string;
  data_basis: string;
  assumptions: string[];
  limitations: string[];
}

export interface SignalOverlayPointPayload {
  signal_index: number;
  execution_index: number;
  signal_timestamp: string;
  execution_timestamp: string;
  signal_type:
    | 'long_entry'
    | 'short_entry'
    | 'long_exit'
    | 'short_exit'
    | 'stop_loss';
  direction: 'long_spread' | 'short_spread';
  zscore_at_signal: number;
  hedge_ratio_at_signal: number;
}

export interface TradeLogEntryPayload {
  trade_id: number;
  direction: 'long_spread' | 'short_spread';
  entry_signal_index: number;
  entry_execution_index: number;
  exit_signal_index: number;
  exit_execution_index: number;
  entry_timestamp: string;
  exit_timestamp: string;
  entry_reason: 'long_entry' | 'short_entry';
  exit_reason: 'long_exit' | 'short_exit' | 'stop_loss';
  bars_held: number;
  entry_zscore: number;
  exit_zscore: number;
  hedge_ratio: number;
  quantity_asset1: number;
  quantity_asset2: number;
  entry_price_asset1: number;
  entry_price_asset2: number;
  exit_price_asset1: number;
  exit_price_asset2: number;
  allocated_capital: number;
  gross_pnl: number;
  total_fees: number;
  net_pnl: number;
  return_pct: number;
  equity_after_trade: number;
}

export interface EquityCurvePointPayload {
  index: number;
  timestamp: string;
  equity: number;
  cash: number;
  unrealized_pnl: number;
  position: 'flat' | 'long_spread' | 'short_spread';
}

export interface MetricSummaryPayload {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_net_pnl: number;
  total_return_pct: number;
  average_trade_return_pct: number;
  average_holding_period_bars: number;
  max_drawdown_pct: number;
  profit_factor: number | null;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  final_equity: number;
}

export interface SpreadSummaryPayload {
  mean: number | null;
  std: number | null;
}

export interface BacktestResponse {
  status: 'ok' | 'blocked';
  request: BacktestRequest;
  data_quality: DataQualityReportPayload;
  warnings: EngineWarningPayload[];
  footer: HonestReportingFooterPayload;
  signal_overlay: SignalOverlayPointPayload[];
  trade_log: TradeLogEntryPayload[];
  equity_curve: EquityCurvePointPayload[];
  metrics: MetricSummaryPayload;
  spread_summary: SpreadSummaryPayload;
}

export interface ResearchTakeawayPayload {
  text: string;
  severity: 'green' | 'yellow' | 'red';
}

// ---------------------------------------------------------------------------
// Research module interfaces
// ---------------------------------------------------------------------------

export interface LookbackSweepRequest {
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  windows?: number[];
}

export interface LookbackWindowResultPayload {
  window: number;
  crossings_2: number;
  autocorrelation: number;
  skewness: number;
  kurtosis: number;
  zscore_std: number;
}

export interface LookbackSweepResponse {
  module: 'lookback_window';
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  observations: number;
  hedge_ratio: number;
  results: LookbackWindowResultPayload[];
  takeaway: ResearchTakeawayPayload;
  recommended_result: LookbackWindowResultPayload;
  recommended_backtest_params: BacktestRequest;
}

export interface RollingStabilityRequest {
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  window?: number;
}

export interface RollingStabilityResultPayload {
  timestamp: number;
  p_value: number | null;
  is_cointegrated: boolean;
  hedge_ratio: number | null;
  test_statistic: number | null;
}

export interface RollingStabilityResponse {
  module: 'rolling_stability';
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  observations: number;
  results: RollingStabilityResultPayload[];
  takeaway: ResearchTakeawayPayload;
  recommended_backtest_params: BacktestRequest | null;
}

export interface OOSValidationRequest {
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  split_ratios?: number[];
}

export interface OOSResultPayload {
  formation_p_value: number;
  formation_cointegrated: boolean;
  formation_hedge_ratio: number;
  trading_p_value: number;
  trading_cointegrated: boolean;
  trading_hedge_ratio: number;
  formation_adf_stat: number;
  trading_adf_stat: number;
  formation_n: number;
  trading_n: number;
  split_ratio: number;
}

export interface OOSValidationResponse {
  module: 'oos_validation';
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  observations: number;
  results: OOSResultPayload[];
  takeaway: ResearchTakeawayPayload;
  recommended_backtest_params: BacktestRequest | null;
}

export interface TimeframeRequest {
  asset1: string;
  asset2: string;
  days_back: number;
  timeframes?: string[];
}

export interface TimeframeResultPayload {
  timeframe: string;
  p_value: number | null;
  is_cointegrated: boolean;
  hedge_ratio: number | null;
  half_life: number | null;
  n_datapoints: number;
  adf_statistic: number | null;
}

export interface TimeframeResponse {
  module: 'timeframe_comparison';
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  observations: number;
  results: TimeframeResultPayload[];
  takeaway: ResearchTakeawayPayload;
  recommended_backtest_params: BacktestRequest | null;
}

export interface SpreadMethodRequest {
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
}

export interface SpreadMethodResultPayload {
  method: string;
  adf_statistic: number;
  adf_p_value: number;
  is_stationary: boolean;
  spread_std: number;
  spread_skewness: number;
  spread_kurtosis: number;
}

export interface SpreadMethodResponse {
  module: 'spread_method';
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  observations: number;
  results: SpreadMethodResultPayload[];
  takeaway: ResearchTakeawayPayload;
  recommended_backtest_params: BacktestRequest | null;
}

export interface ZScoreThresholdRequest {
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  entry_range?: number[];
  exit_range?: number[];
  lookback_window?: number;
}

export interface ThresholdResultPayload {
  entry: number;
  exit: number;
  total_trades: number;
  avg_duration: number | null;
  max_duration: number | null;
}

export interface ZScoreThresholdResponse {
  module: 'zscore_threshold';
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  observations: number;
  results: ThresholdResultPayload[];
  takeaway: ResearchTakeawayPayload;
  recommended_backtest_params: BacktestRequest | null;
}

export interface TxCostRequest {
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  fee_levels?: number[];
  entry_threshold?: number;
  exit_threshold?: number;
  lookback_window?: number;
}

export interface TxCostResultPayload {
  fee_pct: number;
  round_trip_pct: number;
  total_trades: number;
  profitable_trades: number;
  avg_spread_pct: number;
  min_profitable_spread_pct: number;
  net_profitable_pct: number;
}

export interface TxCostResponse {
  module: 'tx_cost';
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  observations: number;
  results: TxCostResultPayload[];
  takeaway: ResearchTakeawayPayload;
  recommended_backtest_params: BacktestRequest | null;
}

export interface CointMethodRequest {
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
}

export interface CointMethodResultPayload {
  method: string;
  is_cointegrated: boolean;
  detail: string;
  statistic: number;
  critical_value: number | null;
}

export interface CointMethodResponse {
  module: 'coint_method';
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  observations: number;
  results: CointMethodResultPayload[];
  takeaway: ResearchTakeawayPayload;
  recommended_backtest_params: BacktestRequest | null;
}

// ---------------------------------------------------------------------------
// Optimization interfaces
// ---------------------------------------------------------------------------

export interface ParameterAxisPayload {
  name: string;
  min_value: number;
  max_value: number;
  step: number;
}

export interface GridSearchCellPayload {
  params: Record<string, number>;
  metrics: MetricSummaryPayload;
  trade_count: number;
  status: 'ok' | 'blocked' | 'no_trades';
}

export interface GridSearchRequest {
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  axes: ParameterAxisPayload[];
  base_strategy?: StrategyParametersPayload;
  optimize_metric?: string;
  max_combinations?: number;
}

export interface GridSearchResponse {
  grid_shape: number[];
  axes: ParameterAxisPayload[];
  cells: GridSearchCellPayload[];
  best_cell_index: number | null;
  best_cell: GridSearchCellPayload | null;
  optimize_metric: string;
  total_combinations: number;
  robustness_score: number | null;
  warnings: EngineWarningPayload[];
  execution_time_ms: number;
  footer: HonestReportingFooterPayload;
  recommended_backtest_params: BacktestRequest | null;
}

export interface WalkForwardFoldPayload {
  fold_index: number;
  train_start_idx: number;
  train_end_idx: number;
  test_start_idx: number;
  test_end_idx: number;
  train_bars: number;
  test_bars: number;
  best_params: Record<string, number>;
  train_metrics: MetricSummaryPayload;
  test_metrics: MetricSummaryPayload;
  train_trade_count: number;
  test_trade_count: number;
  status: 'ok' | 'no_train_trades' | 'no_test_trades' | 'blocked';
}

export interface WalkForwardRequest {
  asset1: string;
  asset2: string;
  timeframe: string;
  days_back: number;
  axes: ParameterAxisPayload[];
  base_strategy?: StrategyParametersPayload;
  fold_count?: number;
  train_pct?: number;
  optimize_metric?: string;
  max_combinations_per_fold?: number;
}

export interface WalkForwardResponse {
  folds: WalkForwardFoldPayload[];
  fold_count: number;
  train_pct: number;
  axes: ParameterAxisPayload[];
  aggregate_train_sharpe: number | null;
  aggregate_test_sharpe: number | null;
  train_test_divergence: number | null;
  stability_verdict: 'stable' | 'moderate' | 'fragile';
  warnings: EngineWarningPayload[];
  execution_time_ms: number;
  footer: HonestReportingFooterPayload;
  recommended_backtest_params: BacktestRequest | null;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

interface ApiErrorPayload {
  detail?: string;
}

/** Convert "ETH/EUR" to "ETH-EUR" for URL path segments. */
function symbolToDash(symbol: string): string {
  return symbol.replace('/', '-');
}

/** Return a stable EUR-pair symbol from a base asset name. */
export function toEurSymbol(asset: string): string {
  return asset.includes('/') ? asset : `${asset}/EUR`;
}

/** Reduce "ETH/EUR" to "ETH". */
export function symbolToBaseAsset(symbol: string): string {
  return symbol.split('/')[0] ?? symbol;
}

/** Convert a backtest request into URL search params for shareable presets. */
export function buildBacktestSearchParams(
  request: BacktestRequest
): URLSearchParams {
  const params = new URLSearchParams();
  params.set('asset1', request.asset1);
  params.set('asset2', request.asset2);
  params.set('timeframe', request.timeframe);
  params.set('days_back', String(request.days_back));
  params.set('lookback_window', String(request.strategy.lookback_window));
  params.set('entry_threshold', String(request.strategy.entry_threshold));
  params.set('exit_threshold', String(request.strategy.exit_threshold));
  params.set('stop_loss', String(request.strategy.stop_loss));
  params.set('initial_capital', String(request.strategy.initial_capital));
  params.set('position_size', String(request.strategy.position_size));
  params.set('transaction_fee', String(request.strategy.transaction_fee));
  params.set(
    'min_trade_count_warning',
    String(request.strategy.min_trade_count_warning)
  );
  return params;
}

/** Fetch wrapper with error handling and JSON parsing. */
async function apiFetch<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, options);
  } catch (err) {
    const message = `API fetch failed: ${url} — ${err instanceof Error ? err.message : String(err)}`;
    console.error(message);
    throw new Error(message);
  }

  if (!response.ok) {
    let detail = '';
    try {
      const payload = (await response.json()) as ApiErrorPayload;
      if (payload.detail) {
        detail = ` — ${payload.detail}`;
      }
    } catch {
      // Ignore JSON parse failures
    }

    const message = `API error: ${response.status} ${response.statusText} — ${url}${detail}`;
    console.error(message);
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

export async function fetchPairs(): Promise<PairsListResponse> {
  return apiFetch<PairsListResponse>(`${API_BASE_URL}/api/pairs`);
}

export async function fetchOHLCV(
  symbol: string,
  timeframe: string,
  daysBack?: number
): Promise<OHLCVResponse> {
  const dashSymbol = symbolToDash(symbol);
  const params = new URLSearchParams({ timeframe });
  if (daysBack !== undefined) {
    params.set('days_back', String(daysBack));
  }
  return apiFetch<OHLCVResponse>(
    `${API_BASE_URL}/api/pairs/${dashSymbol}/ohlcv?${params.toString()}`
  );
}

export async function postCointegration(
  req: CointegrationRequest
): Promise<CointegrationResponse> {
  return apiFetch<CointegrationResponse>(
    `${API_BASE_URL}/api/analysis/cointegration`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }
  );
}

export async function postLookbackSweep(
  req: LookbackSweepRequest
): Promise<LookbackSweepResponse> {
  return apiFetch<LookbackSweepResponse>(
    `${API_BASE_URL}/api/research/lookback-window`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }
  );
}

export async function postBacktest(
  req: BacktestRequest
): Promise<BacktestResponse> {
  return apiFetch<BacktestResponse>(`${API_BASE_URL}/api/backtest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
}

export async function postRollingStability(
  req: RollingStabilityRequest
): Promise<RollingStabilityResponse> {
  return apiFetch<RollingStabilityResponse>(
    `${API_BASE_URL}/api/research/rolling-stability`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }
  );
}

export async function postOOSValidation(
  req: OOSValidationRequest
): Promise<OOSValidationResponse> {
  return apiFetch<OOSValidationResponse>(
    `${API_BASE_URL}/api/research/oos-validation`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }
  );
}

export async function postTimeframeComparison(
  req: TimeframeRequest
): Promise<TimeframeResponse> {
  return apiFetch<TimeframeResponse>(
    `${API_BASE_URL}/api/research/timeframe-comparison`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }
  );
}

export async function postSpreadMethodComparison(
  req: SpreadMethodRequest
): Promise<SpreadMethodResponse> {
  return apiFetch<SpreadMethodResponse>(
    `${API_BASE_URL}/api/research/spread-method`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }
  );
}

export async function postZScoreThreshold(
  req: ZScoreThresholdRequest
): Promise<ZScoreThresholdResponse> {
  return apiFetch<ZScoreThresholdResponse>(
    `${API_BASE_URL}/api/research/zscore-threshold`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }
  );
}

export async function postTxCost(
  req: TxCostRequest
): Promise<TxCostResponse> {
  return apiFetch<TxCostResponse>(
    `${API_BASE_URL}/api/research/tx-cost`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }
  );
}

export async function postCointMethodComparison(
  req: CointMethodRequest
): Promise<CointMethodResponse> {
  return apiFetch<CointMethodResponse>(
    `${API_BASE_URL}/api/research/coint-method`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }
  );
}

export async function postGridSearch(
  req: GridSearchRequest
): Promise<GridSearchResponse> {
  return apiFetch<GridSearchResponse>(
    `${API_BASE_URL}/api/optimization/grid-search`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }
  );
}

export async function postWalkForward(
  req: WalkForwardRequest
): Promise<WalkForwardResponse> {
  return apiFetch<WalkForwardResponse>(
    `${API_BASE_URL}/api/optimization/walk-forward`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }
  );
}

// ---------------------------------------------------------------------------
// Academy scan
// ---------------------------------------------------------------------------

export interface AcademyScanPair {
  asset1: string;
  asset2: string;
  p_value: number;
  is_cointegrated: boolean;
  hedge_ratio: number;
  half_life: number | null;
  correlation: number;
  cointegration_score: number;
  observations: number;
}

export interface AcademyScanResponse {
  cointegrated: AcademyScanPair[];
  not_cointegrated: AcademyScanPair[];
  scanned: number;
  timeframe: string;
}

/**
 * Scan pairs for cointegration with auto-refresh from Bitvavo.
 *
 * When fresh=true (default), the backend fetches latest data from Bitvavo
 * before scanning. This ensures the Academy always shows live data.
 */
export async function fetchAcademyScan(
  timeframe = '1h',
  daysBack = 90,
  fresh = true
): Promise<AcademyScanResponse> {
  const params = new URLSearchParams({
    timeframe,
    days_back: String(daysBack),
    fresh: String(fresh),
  });
  return apiFetch<AcademyScanResponse>(
    `${API_BASE_URL}/api/academy/scan?${params.toString()}`
  );
}

// ---------------------------------------------------------------------------
// Live data fetch
// ---------------------------------------------------------------------------

export interface FetchLiveDataResponse {
  fetched: number;
  failed: number;
  total: number;
  symbols: { symbol: string; candles: number; timeframe: string; error?: string }[];
  timeframe: string;
  days_back: number;
}

/** Fetch fresh OHLCV data from Bitvavo for top EUR pairs. */
export async function fetchLiveData(
  timeframe = '1h',
  daysBack = 90,
  maxCoins = 20
): Promise<FetchLiveDataResponse> {
  const params = new URLSearchParams({
    timeframe,
    days_back: String(daysBack),
    max_coins: String(maxCoins),
  });
  return apiFetch<FetchLiveDataResponse>(
    `${API_BASE_URL}/api/academy/fetch?${params.toString()}`,
    { method: 'POST' }
  );
}
