"""
Cointegration analysis for pairs trading.

This module provides tools for testing cointegration between asset pairs,
calculating spreads, and analyzing mean-reversion properties.
"""

from typing import Literal

import numpy as np
import polars as pl
from scipy import stats
from statsmodels.tsa.stattools import adfuller, coint


class PairAnalysis:
    """
    Analyze cointegration and spread properties for a pair of assets.
    """

    def __init__(self, asset1_prices: pl.Series, asset2_prices: pl.Series):
        """
        Initialize pair analysis.

        Args:
            asset1_prices: Price series for first asset
            asset2_prices: Price series for second asset
        """
        self.asset1 = asset1_prices.to_numpy()
        self.asset2 = asset2_prices.to_numpy()
        self.hedge_ratio = None
        self.spread = None

    def test_stationarity(self, series: np.ndarray, name: str = "Series") -> dict:
        """
        Perform Augmented Dickey-Fuller test for stationarity.

        Args:
            series: Time series to test
            name: Name of the series for reporting

        Returns:
            Dictionary with test results
        """
        result = adfuller(series, autolag="AIC")

        return {
            "name": name,
            "adf_statistic": result[0],
            "p_value": result[1],
            "critical_values": result[4],
            "is_stationary": result[1] < 0.05,  # p-value < 0.05
            "interpretation": (
                "Stationary (reject null hypothesis)"
                if result[1] < 0.05
                else "Non-stationary (fail to reject null hypothesis)"
            ),
        }

    def test_cointegration(self) -> dict:
        """
        Test for cointegration between the two assets using Engle-Granger test.

        Returns:
            Dictionary with cointegration test results
        """
        # Perform Engle-Granger cointegration test
        score, p_value, crit_values = coint(self.asset1, self.asset2)

        # Calculate hedge ratio using OLS regression
        # asset1 = hedge_ratio * asset2 + intercept
        coeffs = np.polyfit(self.asset2, self.asset1, 1)
        self.hedge_ratio = coeffs[0]
        intercept = coeffs[1]

        # Calculate spread
        self.spread = self.asset1 - self.hedge_ratio * self.asset2

        # Test if spread is stationary
        spread_stationarity = self.test_stationarity(self.spread, "Spread")

        return {
            "cointegration_score": score,
            "p_value": p_value,
            "critical_values": {
                "1%": crit_values[0],
                "5%": crit_values[1],
                "10%": crit_values[2],
            },
            "is_cointegrated": p_value < 0.05,
            "hedge_ratio": self.hedge_ratio,
            "intercept": intercept,
            "spread_stationarity": spread_stationarity,
            "interpretation": (
                f"Assets ARE cointegrated (p={p_value:.4f} < 0.05)"
                if p_value < 0.05
                else f"Assets are NOT cointegrated (p={p_value:.4f} >= 0.05)"
            ),
        }

    def calculate_spread(self, method: Literal["ols", "ratio"] = "ols") -> np.ndarray:
        """
        Calculate spread between assets.

        Args:
            method: Method to calculate spread
                - 'ols': Use OLS regression hedge ratio
                - 'ratio': Simple price ratio

        Returns:
            Spread series
        """
        if method == "ols":
            if self.hedge_ratio is None:
                # Calculate hedge ratio if not already done
                self.test_cointegration()
            self.spread = self.asset1 - self.hedge_ratio * self.asset2
        elif method == "ratio":
            self.spread = self.asset1 / self.asset2
        else:
            raise ValueError(f"Unknown method: {method}")

        return self.spread

    def calculate_zscore(self, window: int = 60) -> np.ndarray:
        """
        Calculate rolling z-score of the spread.

        Args:
            window: Rolling window size for mean and std calculation

        Returns:
            Z-score series
        """
        if self.spread is None:
            self.calculate_spread()

        # Convert to Polars for rolling operations
        spread_series = pl.Series(self.spread)

        # Calculate rolling mean and std
        rolling_mean = spread_series.rolling_mean(window_size=window)
        rolling_std = spread_series.rolling_std(window_size=window)

        # Calculate z-score
        zscore = (spread_series - rolling_mean) / rolling_std

        return zscore.to_numpy()

    def analyze_spread_properties(self) -> dict:
        """
        Analyze statistical properties of the spread.

        Returns:
            Dictionary with spread statistics
        """
        if self.spread is None:
            self.calculate_spread()

        return {
            "mean": np.mean(self.spread),
            "std": np.std(self.spread),
            "min": np.min(self.spread),
            "max": np.max(self.spread),
            "median": np.median(self.spread),
            "skewness": stats.skew(self.spread),
            "kurtosis": stats.kurtosis(self.spread),
            "autocorr_lag1": np.corrcoef(self.spread[:-1], self.spread[1:])[0, 1],
        }

    def calculate_half_life(self) -> float:
        """
        Calculate half-life of mean reversion using Ornstein-Uhlenbeck process.

        Returns:
            Half-life in number of periods
        """
        if self.spread is None:
            self.calculate_spread()

        # Calculate lagged spread
        spread_lag = np.roll(self.spread, 1)[1:]
        spread_delta = np.diff(self.spread)

        # Regression: spread_delta = lambda * (spread_lag - mean) + noise
        # Simplified: spread_delta = a + b * spread_lag
        coeffs = np.polyfit(spread_lag, spread_delta, 1)
        lambda_param = -coeffs[0]

        # Half-life = -ln(2) / lambda
        if lambda_param > 0:
            half_life = -np.log(2) / lambda_param
        else:
            half_life = np.inf  # No mean reversion

        return half_life

    def get_correlation(self) -> float:
        """
        Calculate Pearson correlation between assets.

        Returns:
            Correlation coefficient
        """
        return np.corrcoef(self.asset1, self.asset2)[0, 1]


def create_summary_report(pair_analysis: PairAnalysis, asset1_name: str, asset2_name: str) -> str:
    """
    Create a text summary report of pair analysis.

    Args:
        pair_analysis: PairAnalysis object with results
        asset1_name: Name of first asset
        asset2_name: Name of second asset

    Returns:
        Formatted report string
    """
    # Get all analysis results
    coint_results = pair_analysis.test_cointegration()
    spread_props = pair_analysis.analyze_spread_properties()
    half_life = pair_analysis.calculate_half_life()
    correlation = pair_analysis.get_correlation()

    report = f"""
╔════════════════════════════════════════════════════════════════╗
║          PAIRS TRADING ANALYSIS: {asset1_name} / {asset2_name}
╚════════════════════════════════════════════════════════════════╝

📊 CORRELATION ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pearson Correlation:    {correlation:.4f}

🔗 COINTEGRATION TEST (Engle-Granger)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Result:                 {coint_results['interpretation']}
P-value:                {coint_results['p_value']:.6f}
Test Statistic:         {coint_results['cointegration_score']:.4f}
Critical Values:
  - 1% level:           {coint_results['critical_values']['1%']:.4f}
  - 5% level:           {coint_results['critical_values']['5%']:.4f}
  - 10% level:          {coint_results['critical_values']['10%']:.4f}

📈 HEDGE RATIO & SPREAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hedge Ratio:            {coint_results['hedge_ratio']:.6f}
Intercept:              {coint_results['intercept']:.6f}
Equation:               {asset1_name} = {coint_results['hedge_ratio']:.4f} × {asset2_name} + {coint_results['intercept']:.2f}

📉 SPREAD STATIONARITY (ADF Test)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Result:                 {coint_results['spread_stationarity']['interpretation']}
ADF Statistic:          {coint_results['spread_stationarity']['adf_statistic']:.4f}
P-value:                {coint_results['spread_stationarity']['p_value']:.6f}

📊 SPREAD PROPERTIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mean:                   {spread_props['mean']:.4f}
Std Dev:                {spread_props['std']:.4f}
Min:                    {spread_props['min']:.4f}
Max:                    {spread_props['max']:.4f}
Median:                 {spread_props['median']:.4f}
Skewness:               {spread_props['skewness']:.4f}
Kurtosis:               {spread_props['kurtosis']:.4f}
Autocorrelation (lag1): {spread_props['autocorr_lag1']:.4f}

⏱️  MEAN REVERSION SPEED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Half-life:              {half_life:.2f} periods
                        {"(~{:.1f} hours for hourly data)".format(half_life) if half_life < 1000 else "(Very slow or no mean reversion)"}

✅ TRADING SUITABILITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    # Determine suitability
    suitable = True
    reasons = []

    if not coint_results['is_cointegrated']:
        suitable = False
        reasons.append("❌ Assets are NOT cointegrated")
    else:
        reasons.append("✅ Assets are cointegrated")

    if not coint_results['spread_stationarity']['is_stationary']:
        suitable = False
        reasons.append("❌ Spread is NOT stationary")
    else:
        reasons.append("✅ Spread is stationary")

    if half_life < 1 or half_life > 100:
        suitable = False
        if half_life < 1:
            reasons.append(f"❌ Half-life too short ({half_life:.1f} periods)")
        else:
            reasons.append(f"❌ Half-life too long ({half_life:.1f} periods)")
    else:
        reasons.append(f"✅ Reasonable half-life ({half_life:.1f} periods)")

    if correlation < 0.5:
        reasons.append(f"⚠️  Low correlation ({correlation:.2f})")
    else:
        reasons.append(f"✅ Good correlation ({correlation:.2f})")

    report += "\n".join(reasons)
    report += "\n\n"

    if suitable:
        report += "🎯 CONCLUSION: This pair shows promise for statistical arbitrage!\n"
    else:
        report += "⛔ CONCLUSION: This pair may NOT be suitable for statistical arbitrage.\n"

    report += "═" * 64 + "\n"

    return report
