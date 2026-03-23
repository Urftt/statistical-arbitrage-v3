"""
Research analysis functions — empirical testing of stat-arb assumptions.

Each function is self-contained, takes data in, returns structured results.
No Dash dependencies — these are pure analysis functions for testability.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np
import polars as pl
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.tsa.vector_ar.vecm import coint_johansen


# ─── Data structures ─────────────────────────────────────────────────────────


@dataclass
class Takeaway:
    """Auto-generated one-line insight from research results."""

    text: str
    severity: Literal["green", "yellow", "red"]


# ─── Rolling Cointegration Stability ─────────────────────────────────────────


def rolling_cointegration(
    prices1: np.ndarray,
    prices2: np.ndarray,
    timestamps: list | np.ndarray,
    window: int = 90,
    step: int = 1,
) -> pl.DataFrame:
    """
    Compute rolling cointegration test over a sliding window.

    Args:
        prices1: Price series for asset 1.
        prices2: Price series for asset 2.
        timestamps: Corresponding timestamps (same length as prices).
        window: Rolling window size in number of observations.
        step: Step size between windows (1 = every observation, higher = faster).

    Returns:
        Polars DataFrame with columns:
            timestamp, p_value, is_cointegrated, hedge_ratio, test_statistic
    """
    n = len(prices1)
    if n != len(prices2) or n != len(timestamps):
        raise ValueError(
            f"Length mismatch: prices1={len(prices1)}, prices2={len(prices2)}, timestamps={len(timestamps)}"
        )
    if n < window:
        raise ValueError(f"Not enough data: {n} observations < {window} window size")

    results = []
    for i in range(window, n, step):
        p1_window = prices1[i - window : i]
        p2_window = prices2[i - window : i]

        try:
            score, p_value, _ = coint(p1_window, p2_window)
            # Hedge ratio via OLS
            hedge_ratio = float(np.polyfit(p2_window, p1_window, 1)[0])

            results.append({
                "timestamp": timestamps[i - 1],
                "p_value": float(p_value),
                "is_cointegrated": p_value < 0.05,
                "hedge_ratio": hedge_ratio,
                "test_statistic": float(score),
            })
        except Exception:
            results.append({
                "timestamp": timestamps[i - 1],
                "p_value": None,
                "is_cointegrated": False,
                "hedge_ratio": None,
                "test_statistic": None,
            })

    return pl.DataFrame(results)


def rolling_cointegration_takeaway(results: pl.DataFrame) -> Takeaway:
    """
    Generate a one-line takeaway from rolling cointegration results.

    Args:
        results: DataFrame from rolling_cointegration().

    Returns:
        Takeaway with text and severity (green/yellow/red).
    """
    if results.is_empty():
        return Takeaway(text="No results to analyze.", severity="red")

    valid = results.filter(pl.col("p_value").is_not_null())
    if valid.is_empty():
        return Takeaway(text="All cointegration tests failed — data may be insufficient.", severity="red")

    total = len(valid)
    cointegrated_count = valid.filter(pl.col("is_cointegrated") == True).height
    pct = cointegrated_count / total * 100

    # Count transitions: cointegrated → not cointegrated
    is_coint = valid["is_cointegrated"].to_list()
    breakdowns = sum(
        1 for a, b in zip(is_coint[:-1], is_coint[1:]) if a and not b
    )

    if pct >= 80 and breakdowns <= 1:
        return Takeaway(
            text=f"✅ Stable cointegration — significant {pct:.0f}% of the time with {breakdowns} breakdown(s).",
            severity="green",
        )
    elif pct >= 50:
        return Takeaway(
            text=f"⚠️ Intermittent cointegration — significant {pct:.0f}% of the time with {breakdowns} breakdown(s). Relationship is unreliable.",
            severity="yellow",
        )
    else:
        return Takeaway(
            text=f"⚡ Weak cointegration — significant only {pct:.0f}% of the time with {breakdowns} breakdown(s). Not suitable for trading.",
            severity="red",
        )


# ─── Out-of-Sample Validation ────────────────────────────────────────────────


@dataclass
class OOSResult:
    """Results from out-of-sample validation."""

    formation_p_value: float
    formation_cointegrated: bool
    formation_hedge_ratio: float
    trading_p_value: float
    trading_cointegrated: bool
    trading_hedge_ratio: float
    formation_adf_stat: float
    trading_adf_stat: float
    formation_n: int
    trading_n: int
    split_ratio: float


def out_of_sample_validation(
    prices1: np.ndarray,
    prices2: np.ndarray,
    split_ratios: list[float] | None = None,
) -> list[OOSResult]:
    """
    Test whether in-sample cointegration predicts out-of-sample behavior.

    Splits data into formation (in-sample) and trading (out-of-sample) periods
    at multiple split points.

    Args:
        prices1: Price series for asset 1.
        prices2: Price series for asset 2.
        split_ratios: Formation period fractions (default: [0.5, 0.6, 0.7, 0.8]).

    Returns:
        List of OOSResult for each split ratio.
    """
    if split_ratios is None:
        split_ratios = [0.5, 0.6, 0.7, 0.8]

    n = len(prices1)
    results = []

    for ratio in split_ratios:
        split_idx = int(n * ratio)
        if split_idx < 30 or (n - split_idx) < 30:
            continue

        # Formation period
        f_p1, f_p2 = prices1[:split_idx], prices2[:split_idx]
        # Trading period
        t_p1, t_p2 = prices1[split_idx:], prices2[split_idx:]

        try:
            f_score, f_pval, _ = coint(f_p1, f_p2)
            f_hr = float(np.polyfit(f_p2, f_p1, 1)[0])
            f_spread = f_p1 - f_hr * f_p2
            f_adf = adfuller(f_spread, autolag="AIC")[0]
        except Exception:
            continue

        try:
            t_score, t_pval, _ = coint(t_p1, t_p2)
            t_hr = float(np.polyfit(t_p2, t_p1, 1)[0])
            # Use formation hedge ratio on trading data for true OOS test
            t_spread_oos = t_p1 - f_hr * t_p2
            t_adf = adfuller(t_spread_oos, autolag="AIC")[0]
        except Exception:
            continue

        results.append(OOSResult(
            formation_p_value=float(f_pval),
            formation_cointegrated=f_pval < 0.05,
            formation_hedge_ratio=f_hr,
            trading_p_value=float(t_pval),
            trading_cointegrated=t_pval < 0.05,
            trading_hedge_ratio=t_hr,
            formation_adf_stat=float(f_adf),
            trading_adf_stat=float(t_adf),
            formation_n=split_idx,
            trading_n=n - split_idx,
            split_ratio=ratio,
        ))

    return results


def oos_validation_takeaway(results: list[OOSResult]) -> Takeaway:
    """Generate takeaway from out-of-sample validation results."""
    if not results:
        return Takeaway(text="Insufficient data for out-of-sample validation.", severity="red")

    # Count how many splits maintain cointegration
    in_sample_coint = [r for r in results if r.formation_cointegrated]
    if not in_sample_coint:
        return Takeaway(
            text="❌ Not cointegrated in-sample at any split — out-of-sample validation not applicable.",
            severity="red",
        )

    oos_survived = [r for r in in_sample_coint if r.trading_cointegrated]
    survival_rate = len(oos_survived) / len(in_sample_coint) * 100

    if survival_rate >= 75:
        return Takeaway(
            text=f"✅ Robust — cointegration holds out-of-sample in {survival_rate:.0f}% of splits ({len(oos_survived)}/{len(in_sample_coint)}).",
            severity="green",
        )
    elif survival_rate >= 40:
        return Takeaway(
            text=f"⚠️ Mixed — cointegration holds out-of-sample in only {survival_rate:.0f}% of splits ({len(oos_survived)}/{len(in_sample_coint)}). Results are period-dependent.",
            severity="yellow",
        )
    else:
        return Takeaway(
            text=f"⚡ Fragile — cointegration fails out-of-sample in {100 - survival_rate:.0f}% of splits. In-sample results don't generalize.",
            severity="red",
        )


# ─── Spread Construction Comparison ──────────────────────────────────────────


@dataclass
class SpreadMethodResult:
    """Results for one spread construction method."""

    method: str
    adf_statistic: float
    adf_p_value: float
    is_stationary: bool
    spread_std: float
    spread_skewness: float
    spread_kurtosis: float
    spread: np.ndarray


def compare_spread_methods(
    prices1: np.ndarray,
    prices2: np.ndarray,
) -> list[SpreadMethodResult]:
    """
    Compare spread construction methods by stationarity.

    Tests three approaches:
    - Price-level: spread = p1 - β * p2 (OLS hedge ratio)
    - Log-price: spread = log(p1) - β * log(p2)
    - Price ratio: spread = p1 / p2

    Args:
        prices1: Price series for asset 1.
        prices2: Price series for asset 2.

    Returns:
        List of SpreadMethodResult, one per method.
    """
    from scipy.stats import skew, kurtosis

    results = []

    # Method 1: Price-level OLS
    hr_price = float(np.polyfit(prices2, prices1, 1)[0])
    spread_price = prices1 - hr_price * prices2
    adf_price = adfuller(spread_price, autolag="AIC")
    results.append(SpreadMethodResult(
        method="Price-level (OLS)",
        adf_statistic=float(adf_price[0]),
        adf_p_value=float(adf_price[1]),
        is_stationary=adf_price[1] < 0.05,
        spread_std=float(np.std(spread_price)),
        spread_skewness=float(skew(spread_price)),
        spread_kurtosis=float(kurtosis(spread_price)),
        spread=spread_price,
    ))

    # Method 2: Log-price OLS
    if np.all(prices1 > 0) and np.all(prices2 > 0):
        log_p1 = np.log(prices1)
        log_p2 = np.log(prices2)
        hr_log = float(np.polyfit(log_p2, log_p1, 1)[0])
        spread_log = log_p1 - hr_log * log_p2
        adf_log = adfuller(spread_log, autolag="AIC")
        results.append(SpreadMethodResult(
            method="Log-price (OLS)",
            adf_statistic=float(adf_log[0]),
            adf_p_value=float(adf_log[1]),
            is_stationary=adf_log[1] < 0.05,
            spread_std=float(np.std(spread_log)),
            spread_skewness=float(skew(spread_log)),
            spread_kurtosis=float(kurtosis(spread_log)),
            spread=spread_log,
        ))

    # Method 3: Price ratio
    if np.all(prices2 != 0):
        spread_ratio = prices1 / prices2
        adf_ratio = adfuller(spread_ratio, autolag="AIC")
        results.append(SpreadMethodResult(
            method="Price ratio",
            adf_statistic=float(adf_ratio[0]),
            adf_p_value=float(adf_ratio[1]),
            is_stationary=adf_ratio[1] < 0.05,
            spread_std=float(np.std(spread_ratio)),
            spread_skewness=float(skew(spread_ratio)),
            spread_kurtosis=float(kurtosis(spread_ratio)),
            spread=spread_ratio,
        ))

    return results


def spread_methods_takeaway(results: list[SpreadMethodResult]) -> Takeaway:
    """Generate takeaway from spread method comparison."""
    if not results:
        return Takeaway(text="No spread methods could be computed.", severity="red")

    stationary = [r for r in results if r.is_stationary]
    best = min(results, key=lambda r: r.adf_p_value)

    if len(stationary) == len(results):
        return Takeaway(
            text=f"✅ All {len(results)} methods produce stationary spreads. Best: {best.method} (ADF p={best.adf_p_value:.4f}).",
            severity="green",
        )
    elif stationary:
        return Takeaway(
            text=f"⚠️ Only {len(stationary)}/{len(results)} methods produce stationary spreads. Best: {best.method} (ADF p={best.adf_p_value:.4f}).",
            severity="yellow",
        )
    else:
        return Takeaway(
            text=f"⚡ No method produces a stationary spread. Best attempt: {best.method} (ADF p={best.adf_p_value:.4f}). Pair may not be cointegrated.",
            severity="red",
        )


# ─── Cointegration Test Method Comparison ────────────────────────────────────


@dataclass
class CointMethodResult:
    """Results from one cointegration test method."""

    method: str
    is_cointegrated: bool
    detail: str  # human-readable detail
    statistic: float
    critical_value: float | None  # for comparison


def compare_cointegration_methods(
    prices1: np.ndarray,
    prices2: np.ndarray,
) -> list[CointMethodResult]:
    """
    Compare Engle-Granger and Johansen cointegration tests.

    Args:
        prices1: Price series for asset 1.
        prices2: Price series for asset 2.

    Returns:
        List of CointMethodResult for each method (and direction for EG).
    """
    results = []

    # EG: asset1 ~ asset2
    try:
        score_12, p_12, _ = coint(prices1, prices2)
        results.append(CointMethodResult(
            method="Engle-Granger (A1 ~ A2)",
            is_cointegrated=p_12 < 0.05,
            detail=f"p-value={p_12:.4f}, test stat={score_12:.4f}",
            statistic=float(score_12),
            critical_value=None,
        ))
    except Exception as e:
        results.append(CointMethodResult(
            method="Engle-Granger (A1 ~ A2)", is_cointegrated=False,
            detail=f"Failed: {e}", statistic=0.0, critical_value=None,
        ))

    # EG: asset2 ~ asset1 (reversed)
    try:
        score_21, p_21, _ = coint(prices2, prices1)
        results.append(CointMethodResult(
            method="Engle-Granger (A2 ~ A1)",
            is_cointegrated=p_21 < 0.05,
            detail=f"p-value={p_21:.4f}, test stat={score_21:.4f}",
            statistic=float(score_21),
            critical_value=None,
        ))
    except Exception as e:
        results.append(CointMethodResult(
            method="Engle-Granger (A2 ~ A1)", is_cointegrated=False,
            detail=f"Failed: {e}", statistic=0.0, critical_value=None,
        ))

    # Johansen trace test
    try:
        data = np.column_stack([prices1, prices2])
        joh = coint_johansen(data, det_order=0, k_ar_diff=1)
        # Trace statistic for r=0 (no cointegration) at 5% level
        trace_stat = float(joh.lr1[0])  # trace stat for r=0
        trace_crit_5 = float(joh.cvt[0, 1])  # 5% critical value for r=0
        results.append(CointMethodResult(
            method="Johansen (trace, r=0)",
            is_cointegrated=trace_stat > trace_crit_5,
            detail=f"trace stat={trace_stat:.4f}, 5% critical={trace_crit_5:.4f}",
            statistic=trace_stat,
            critical_value=trace_crit_5,
        ))
    except Exception as e:
        results.append(CointMethodResult(
            method="Johansen (trace, r=0)", is_cointegrated=False,
            detail=f"Failed: {e}", statistic=0.0, critical_value=None,
        ))

    # Johansen max eigenvalue test
    try:
        data = np.column_stack([prices1, prices2])
        joh = coint_johansen(data, det_order=0, k_ar_diff=1)
        max_eig_stat = float(joh.lr2[0])  # max eigenvalue stat for r=0
        max_eig_crit_5 = float(joh.cvm[0, 1])  # 5% critical value
        results.append(CointMethodResult(
            method="Johansen (max-eig, r=0)",
            is_cointegrated=max_eig_stat > max_eig_crit_5,
            detail=f"max-eig stat={max_eig_stat:.4f}, 5% critical={max_eig_crit_5:.4f}",
            statistic=max_eig_stat,
            critical_value=max_eig_crit_5,
        ))
    except Exception as e:
        results.append(CointMethodResult(
            method="Johansen (max-eig, r=0)", is_cointegrated=False,
            detail=f"Failed: {e}", statistic=0.0, critical_value=None,
        ))

    return results


def coint_methods_takeaway(results: list[CointMethodResult]) -> Takeaway:
    """Generate takeaway from cointegration method comparison."""
    if not results:
        return Takeaway(text="No cointegration tests could be run.", severity="red")

    agree_yes = sum(1 for r in results if r.is_cointegrated)
    agree_no = sum(1 for r in results if not r.is_cointegrated)
    total = len(results)

    # Check EG direction sensitivity
    eg_results = [r for r in results if r.method.startswith("Engle-Granger")]
    eg_disagree = len(eg_results) == 2 and eg_results[0].is_cointegrated != eg_results[1].is_cointegrated

    if agree_yes == total:
        extra = " EG is direction-sensitive here." if eg_disagree else ""
        return Takeaway(
            text=f"✅ All {total} tests agree: cointegrated.{extra}",
            severity="green",
        )
    elif agree_no == total:
        return Takeaway(
            text=f"❌ All {total} tests agree: NOT cointegrated.",
            severity="red",
        )
    else:
        direction_note = " ⚠️ EG gives different results depending on variable order." if eg_disagree else ""
        return Takeaway(
            text=f"⚠️ Tests disagree — {agree_yes}/{total} say cointegrated, {agree_no}/{total} say not.{direction_note}",
            severity="yellow",
        )


# ─── Optimal Timeframe Comparison ────────────────────────────────────────────


@dataclass
class TimeframeResult:
    """Results for one timeframe."""

    timeframe: str
    p_value: float | None
    is_cointegrated: bool
    hedge_ratio: float | None
    half_life: float | None
    n_datapoints: int
    adf_statistic: float | None


def compare_timeframes(
    get_merged_fn,
    asset1: str,
    asset2: str,
    timeframes: list[str] | None = None,
) -> list[TimeframeResult]:
    """
    Compare cointegration across multiple timeframes.

    Args:
        get_merged_fn: Callable(asset1, asset2, timeframe) -> merged DataFrame or None.
            Must return df with "c1", "c2" columns or None on failure.
        asset1: Asset 1 symbol.
        asset2: Asset 2 symbol.
        timeframes: List of timeframes to test (default: ["15m", "1h", "4h", "1d"]).

    Returns:
        List of TimeframeResult.
    """
    if timeframes is None:
        timeframes = ["15m", "1h", "4h", "1d"]

    results = []
    for tf in timeframes:
        try:
            merged = get_merged_fn(asset1, asset2, tf)
            if merged is None or len(merged) < 30:
                results.append(TimeframeResult(
                    timeframe=tf, p_value=None, is_cointegrated=False,
                    hedge_ratio=None, half_life=None, n_datapoints=0, adf_statistic=None,
                ))
                continue

            p1 = merged["c1"].to_numpy()
            p2 = merged["c2"].to_numpy()

            score, p_value, _ = coint(p1, p2)
            hr = float(np.polyfit(p2, p1, 1)[0])
            spread = p1 - hr * p2
            adf_stat = float(adfuller(spread, autolag="AIC")[0])

            # Half-life
            spread_lag = np.roll(spread, 1)[1:]
            spread_delta = np.diff(spread)
            lam = -np.polyfit(spread_lag, spread_delta, 1)[0]
            hl = -np.log(2) / lam if lam > 0 else None

            results.append(TimeframeResult(
                timeframe=tf,
                p_value=float(p_value),
                is_cointegrated=p_value < 0.05,
                hedge_ratio=hr,
                half_life=hl if hl and 0 < hl < 10000 else None,
                n_datapoints=len(merged),
                adf_statistic=adf_stat,
            ))
        except Exception:
            results.append(TimeframeResult(
                timeframe=tf, p_value=None, is_cointegrated=False,
                hedge_ratio=None, half_life=None, n_datapoints=0, adf_statistic=None,
            ))

    return results


def timeframe_takeaway(results: list[TimeframeResult]) -> Takeaway:
    """Generate takeaway from timeframe comparison."""
    valid = [r for r in results if r.p_value is not None]
    if not valid:
        return Takeaway(text="No timeframes had sufficient data.", severity="red")

    coint_tfs = [r for r in valid if r.is_cointegrated]
    if len(coint_tfs) == len(valid):
        best = min(valid, key=lambda r: r.p_value)
        return Takeaway(
            text=f"✅ Cointegrated at all {len(valid)} timeframes. Strongest: {best.timeframe} (p={best.p_value:.4f}).",
            severity="green",
        )
    elif coint_tfs:
        tfs = ", ".join(r.timeframe for r in coint_tfs)
        return Takeaway(
            text=f"⚠️ Cointegrated at {len(coint_tfs)}/{len(valid)} timeframes: {tfs}. Relationship is timeframe-dependent.",
            severity="yellow",
        )
    else:
        best = min(valid, key=lambda r: r.p_value)
        return Takeaway(
            text=f"⚡ Not cointegrated at any timeframe. Closest: {best.timeframe} (p={best.p_value:.4f}).",
            severity="red",
        )


# ─── Z-score Threshold Optimization ──────────────────────────────────────────


@dataclass
class ThresholdResult:
    """Results for one entry/exit threshold combination."""

    entry: float
    exit: float
    total_trades: int
    avg_duration: float | None
    max_duration: int | None


def sweep_zscore_thresholds(
    zscore: np.ndarray,
    entry_range: list[float] | None = None,
    exit_range: list[float] | None = None,
) -> list[ThresholdResult]:
    """
    Sweep z-score entry/exit thresholds and count signals.

    Args:
        zscore: Z-score time series (NaNs will be removed).
        entry_range: Entry thresholds to test.
        exit_range: Exit thresholds to test.

    Returns:
        List of ThresholdResult for each valid entry/exit combination.
    """
    if entry_range is None:
        entry_range = [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
    if exit_range is None:
        exit_range = [0.0, 0.25, 0.5, 0.75, 1.0]

    z = zscore[~np.isnan(zscore)]
    if len(z) == 0:
        return []

    results = []
    for entry in entry_range:
        for exit_t in exit_range:
            if exit_t >= entry:
                continue
            trades, durations = _count_trades(z, entry, exit_t)
            results.append(ThresholdResult(
                entry=entry,
                exit=exit_t,
                total_trades=trades,
                avg_duration=round(float(np.mean(durations)), 1) if durations else None,
                max_duration=max(durations) if durations else None,
            ))
    return results


def _count_trades(zscore: np.ndarray, entry: float, exit_t: float) -> tuple[int, list[int]]:
    """Count round-trip trades for given thresholds. Returns (count, durations)."""
    in_position = False
    position_type = None
    entry_idx = 0
    trades = 0
    durations = []

    for i in range(len(zscore)):
        if not in_position:
            if zscore[i] >= entry:
                in_position, position_type, entry_idx = True, "short", i
            elif zscore[i] <= -entry:
                in_position, position_type, entry_idx = True, "long", i
        else:
            should_exit = (
                (position_type == "short" and zscore[i] <= exit_t)
                or (position_type == "long" and zscore[i] >= -exit_t)
            )
            if should_exit:
                trades += 1
                durations.append(i - entry_idx)
                in_position = False
                position_type = None

    return trades, durations


def zscore_threshold_takeaway(results: list[ThresholdResult]) -> Takeaway:
    """Generate takeaway from threshold sweep."""
    if not results:
        return Takeaway(text="No threshold combinations could be tested.", severity="red")

    with_trades = [r for r in results if r.total_trades > 0]
    if not with_trades:
        return Takeaway(text="⚡ No threshold combination produces any trades. Spread may not be mean-reverting.", severity="red")

    # Find the "sweet spot": reasonable trade count with moderate duration
    best = max(with_trades, key=lambda r: r.total_trades)
    balanced = [r for r in with_trades if r.avg_duration and 5 <= r.avg_duration <= 200]
    if balanced:
        best = max(balanced, key=lambda r: r.total_trades)

    return Takeaway(
        text=f"📊 Best signal: entry=±{best.entry}, exit=±{best.exit} → {best.total_trades} trades, avg {best.avg_duration:.0f} periods.",
        severity="green" if best.total_trades >= 10 else "yellow",
    )


# ─── Lookback Window Optimization ────────────────────────────────────────────


@dataclass
class LookbackResult:
    """Results for one lookback window size."""

    window: int
    crossings_2: int  # times z-score crosses ±2
    autocorrelation: float
    skewness: float
    kurtosis: float
    zscore_std: float


def sweep_lookback_windows(
    spread: np.ndarray,
    windows: list[int] | None = None,
) -> list[LookbackResult]:
    """
    Sweep lookback windows and measure z-score properties.

    Args:
        spread: Spread time series.
        windows: Window sizes to test.

    Returns:
        List of LookbackResult.
    """
    from scipy.stats import skew, kurtosis

    if windows is None:
        windows = [10, 20, 30, 40, 50, 60, 80, 100, 150, 200]

    spread_series = pl.Series(spread)
    results = []

    for w in windows:
        if w >= len(spread):
            continue

        rolling_mean = spread_series.rolling_mean(window_size=w)
        rolling_std = spread_series.rolling_std(window_size=w)
        zscore = ((spread_series - rolling_mean) / rolling_std).to_numpy()
        z = zscore[~np.isnan(zscore)]

        if len(z) < 10:
            continue

        # Crossings at ±2
        crossings = int(
            np.sum(np.abs(np.diff(np.sign(z - 2))) > 0)
            + np.sum(np.abs(np.diff(np.sign(z + 2))) > 0)
        )
        autocorr = float(np.corrcoef(z[:-1], z[1:])[0, 1]) if len(z) > 1 else 0.0

        results.append(LookbackResult(
            window=w,
            crossings_2=crossings,
            autocorrelation=autocorr,
            skewness=float(skew(z)),
            kurtosis=float(kurtosis(z)),
            zscore_std=float(np.std(z)),
        ))

    return results


def lookback_window_takeaway(results: list[LookbackResult]) -> Takeaway:
    """Generate takeaway from lookback window sweep."""
    if not results:
        return Takeaway(text="Not enough data to test any window size.", severity="red")

    # Find window with best balance: most crossings + high autocorrelation
    best_crossings = max(results, key=lambda r: r.crossings_2)
    # Windows where autocorrelation is high (smooth signals) and crossings are decent
    good = [r for r in results if r.autocorrelation > 0.9 and r.crossings_2 > 0]
    if good:
        best = max(good, key=lambda r: r.crossings_2)
    else:
        best = best_crossings

    return Takeaway(
        text=f"🪟 Best window: {best.window} periods — {best.crossings_2} signal crossings (±2σ), autocorr={best.autocorrelation:.2f}.",
        severity="green" if best.crossings_2 >= 5 else "yellow" if best.crossings_2 > 0 else "red",
    )


# ─── Transaction Cost Sensitivity ────────────────────────────────────────────


@dataclass
class TxCostResult:
    """Results for one fee level."""

    fee_pct: float  # one-way fee as percentage
    round_trip_pct: float  # total fee for entry + exit
    total_trades: int
    profitable_trades: int
    avg_spread_pct: float  # average spread move as % of position
    min_profitable_spread_pct: float  # minimum spread move to cover fees
    net_profitable_pct: float  # percentage of trades that clear fees


def transaction_cost_analysis(
    prices1: np.ndarray,
    prices2: np.ndarray,
    zscore: np.ndarray,
    entry_threshold: float = 2.0,
    exit_threshold: float = 0.5,
    fee_levels: list[float] | None = None,
) -> list[TxCostResult]:
    """
    Analyze how transaction costs affect profitability.

    Simulates trades at given thresholds and checks if spread moves
    are large enough to cover fees at various fee levels.

    Args:
        prices1: Price series for asset 1.
        prices2: Price series for asset 2.
        zscore: Z-score series (same length as prices, may contain NaN).
        entry_threshold: Z-score entry level.
        exit_threshold: Z-score exit level.
        fee_levels: One-way fee percentages to test (default: Bitvavo range).

    Returns:
        List of TxCostResult for each fee level.
    """
    if fee_levels is None:
        fee_levels = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]

    # Compute hedge ratio
    hr = float(np.polyfit(prices2, prices1, 1)[0])

    # Find trades using z-score signals
    z = zscore.copy()
    trades = []  # list of spread move percentages
    spread = prices1 - hr * prices2

    in_position = False
    position_type = None
    entry_idx = 0

    for i in range(len(z)):
        if np.isnan(z[i]):
            continue
        if not in_position:
            if z[i] >= entry_threshold:
                in_position, position_type, entry_idx = True, "short", i
            elif z[i] <= -entry_threshold:
                in_position, position_type, entry_idx = True, "long", i
        else:
            should_exit = (
                (position_type == "short" and z[i] <= exit_threshold)
                or (position_type == "long" and z[i] >= -exit_threshold)
            )
            if should_exit:
                # Calculate spread move as % of position value
                entry_value = abs(prices1[entry_idx]) + abs(hr * prices2[entry_idx])
                if entry_value > 0:
                    spread_pct = (abs(spread[i] - spread[entry_idx]) / entry_value) * 100
                    trades.append(spread_pct)
                in_position = False
                position_type = None

    if not trades:
        return [TxCostResult(
            fee_pct=f, round_trip_pct=f * 2, total_trades=0,
            profitable_trades=0, avg_spread_pct=0, min_profitable_spread_pct=f * 2,
            net_profitable_pct=0,
        ) for f in fee_levels]

    avg_spread = float(np.mean(trades))

    results = []
    for fee in fee_levels:
        round_trip = fee * 2  # buy + sell for both legs
        # Actually it's 4 transactions: buy A, sell B, then reverse
        total_fee_pct = fee * 4  # 4 one-way transactions
        profitable = sum(1 for t in trades if t > total_fee_pct)

        results.append(TxCostResult(
            fee_pct=fee,
            round_trip_pct=total_fee_pct,
            total_trades=len(trades),
            profitable_trades=profitable,
            avg_spread_pct=avg_spread,
            min_profitable_spread_pct=total_fee_pct,
            net_profitable_pct=(profitable / len(trades) * 100) if trades else 0,
        ))

    return results


def tx_cost_takeaway(results: list[TxCostResult]) -> Takeaway:
    """Generate takeaway from transaction cost analysis."""
    if not results or results[0].total_trades == 0:
        return Takeaway(text="No trades to analyze — try different thresholds.", severity="red")

    # Find Bitvavo's maker fee level (0.15%)
    bitvavo = next((r for r in results if abs(r.fee_pct - 0.15) < 0.01), None)
    if bitvavo is None:
        bitvavo = results[len(results) // 2]  # middle fee level

    if bitvavo.net_profitable_pct >= 70:
        return Takeaway(
            text=f"✅ At Bitvavo fees ({bitvavo.fee_pct}% maker), {bitvavo.net_profitable_pct:.0f}% of {bitvavo.total_trades} trades clear costs. Avg spread: {bitvavo.avg_spread_pct:.2f}%.",
            severity="green",
        )
    elif bitvavo.net_profitable_pct >= 40:
        return Takeaway(
            text=f"⚠️ At Bitvavo fees ({bitvavo.fee_pct}% maker), only {bitvavo.net_profitable_pct:.0f}% of {bitvavo.total_trades} trades clear costs. Marginal profitability.",
            severity="yellow",
        )
    else:
        return Takeaway(
            text=f"⚡ At Bitvavo fees ({bitvavo.fee_pct}% maker), only {bitvavo.net_profitable_pct:.0f}% of {bitvavo.total_trades} trades clear costs. Not profitable after fees.",
            severity="red",
        )
