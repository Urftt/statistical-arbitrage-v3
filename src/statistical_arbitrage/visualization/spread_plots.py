"""
Visualization tools for pairs trading analysis.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_price_comparison(
    dates,
    asset1_prices,
    asset2_prices,
    asset1_name="Asset 1",
    asset2_name="Asset 2",
):
    """
    Plot normalized price comparison for two assets.

    Args:
        dates: Datetime series
        asset1_prices: Price series for first asset
        asset2_prices: Price series for second asset
        asset1_name: Name of first asset
        asset2_name: Name of second asset

    Returns:
        Plotly figure
    """
    # Normalize prices to 100
    asset1_norm = (asset1_prices / asset1_prices[0]) * 100
    asset2_norm = (asset2_prices / asset2_prices[0]) * 100

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=asset1_norm,
            name=asset1_name,
            line=dict(color="blue", width=2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=asset2_norm,
            name=asset2_name,
            line=dict(color="orange", width=2),
        )
    )

    fig.update_layout(
        title=f"Normalized Price Comparison: {asset1_name} vs {asset2_name}",
        xaxis_title="Date",
        yaxis_title="Normalized Price (Base = 100)",
        height=500,
        hovermode="x unified",
        template="plotly_white",
    )

    return fig


def plot_spread_analysis(
    dates,
    spread,
    zscore,
    asset1_name="Asset 1",
    asset2_name="Asset 2",
    entry_threshold=2.0,
    exit_threshold=0.5,
):
    """
    Plot spread and z-score with entry/exit thresholds.

    Args:
        dates: Datetime series
        spread: Spread series
        zscore: Z-score series
        asset1_name: Name of first asset
        asset2_name: Name of second asset
        entry_threshold: Z-score threshold for entry
        exit_threshold: Z-score threshold for exit

    Returns:
        Plotly figure
    """
    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=(
            f"Spread: {asset1_name} - hedge_ratio × {asset2_name}",
            "Z-Score (Standardized Spread)",
        ),
        vertical_spacing=0.12,
        row_heights=[0.5, 0.5],
    )

    # Plot spread
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=spread,
            name="Spread",
            line=dict(color="purple", width=1.5),
        ),
        row=1,
        col=1,
    )

    # Add horizontal line at mean
    fig.add_hline(
        y=np.mean(spread),
        line_dash="dash",
        line_color="gray",
        annotation_text="Mean",
        annotation_position="right",
        row=1,
        col=1,
    )

    # Plot z-score
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=zscore,
            name="Z-Score",
            line=dict(color="darkblue", width=1.5),
        ),
        row=2,
        col=1,
    )

    # Add threshold lines for z-score
    fig.add_hline(
        y=entry_threshold,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Entry (+{entry_threshold}σ)",
        annotation_position="right",
        row=2,
        col=1,
    )
    fig.add_hline(
        y=-entry_threshold,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Entry (-{entry_threshold}σ)",
        annotation_position="right",
        row=2,
        col=1,
    )
    fig.add_hline(
        y=exit_threshold,
        line_dash="dot",
        line_color="green",
        annotation_text=f"Exit (+{exit_threshold}σ)",
        annotation_position="right",
        row=2,
        col=1,
    )
    fig.add_hline(
        y=-exit_threshold,
        line_dash="dot",
        line_color="green",
        annotation_text=f"Exit (-{exit_threshold}σ)",
        annotation_position="right",
        row=2,
        col=1,
    )
    fig.add_hline(y=0, line_color="gray", row=2, col=1)

    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Spread Value", row=1, col=1)
    fig.update_yaxes(title_text="Z-Score", row=2, col=1)

    fig.update_layout(
        height=800,
        hovermode="x unified",
        showlegend=True,
        template="plotly_white",
    )

    return fig


def plot_scatter_with_regression(
    asset2_prices,
    asset1_prices,
    hedge_ratio,
    intercept,
    asset1_name="Asset 1",
    asset2_name="Asset 2",
):
    """
    Plot scatter plot with OLS regression line.

    Args:
        asset2_prices: Price series for second asset (x-axis)
        asset1_prices: Price series for first asset (y-axis)
        hedge_ratio: Slope from regression
        intercept: Intercept from regression
        asset1_name: Name of first asset
        asset2_name: Name of second asset

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    # Scatter plot
    fig.add_trace(
        go.Scatter(
            x=asset2_prices,
            y=asset1_prices,
            mode="markers",
            name="Data Points",
            marker=dict(size=4, color="blue", opacity=0.5),
        )
    )

    # Regression line
    x_range = np.array([asset2_prices.min(), asset2_prices.max()])
    y_range = hedge_ratio * x_range + intercept

    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=y_range,
            mode="lines",
            name=f"OLS: y = {hedge_ratio:.4f}x + {intercept:.2f}",
            line=dict(color="red", width=3),
        )
    )

    fig.update_layout(
        title=f"Price Relationship: {asset1_name} vs {asset2_name}",
        xaxis_title=f"{asset2_name} Price",
        yaxis_title=f"{asset1_name} Price",
        height=500,
        template="plotly_white",
        hovermode="closest",
    )

    return fig


def plot_zscore_distribution(zscore, entry_threshold=2.0):
    """
    Plot histogram of z-score distribution.

    Args:
        zscore: Z-score series
        entry_threshold: Z-score threshold for highlighting

    Returns:
        Plotly figure
    """
    # Remove NaN values
    zscore_clean = zscore[~np.isnan(zscore)]

    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=zscore_clean,
            nbinsx=50,
            name="Z-Score Distribution",
            marker_color="steelblue",
        )
    )

    # Add vertical lines for thresholds
    fig.add_vline(
        x=entry_threshold,
        line_dash="dash",
        line_color="red",
        annotation_text=f"+{entry_threshold}σ",
    )
    fig.add_vline(
        x=-entry_threshold,
        line_dash="dash",
        line_color="red",
        annotation_text=f"-{entry_threshold}σ",
    )
    fig.add_vline(x=0, line_color="gray")

    fig.update_layout(
        title="Z-Score Distribution",
        xaxis_title="Z-Score",
        yaxis_title="Frequency",
        height=400,
        template="plotly_white",
        showlegend=False,
    )

    return fig
