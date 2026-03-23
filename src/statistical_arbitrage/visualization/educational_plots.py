"""
Educational visualizations to explain cointegration concepts.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_cointegration_concept():
    """
    Visual explanation of cointegration vs correlation.

    Shows two examples:
    1. Correlated but NOT cointegrated (random walks)
    2. Cointegrated pair (mean-reverting spread)
    """
    np.random.seed(42)
    t = np.arange(200)

    # Example 1: Correlated but NOT cointegrated
    drift1 = np.cumsum(np.random.randn(200) * 0.5) + 100
    drift2 = drift1 + np.cumsum(np.random.randn(200) * 0.3)  # Follows asset1 but drifts
    spread_non_coint = drift2 - drift1

    # Example 2: Cointegrated (mean-reverting spread)
    base = np.cumsum(np.random.randn(200) * 0.5) + 100
    noise = np.sin(t / 10) * 5 + np.random.randn(200) * 2  # Oscillating spread
    asset1_coint = base
    asset2_coint = base + noise
    spread_coint = asset2_coint - asset1_coint

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "❌ Correlated but NOT Cointegrated",
            "Spread: Drifts Away (Non-Stationary)",
            "✅ Cointegrated Pair",
            "Spread: Mean-Reverting (Stationary)"
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.12,
    )

    # Non-cointegrated pair
    fig.add_trace(go.Scatter(x=t, y=drift1, name="Asset 1", line=dict(color="blue")), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=drift2, name="Asset 2", line=dict(color="orange")), row=1, col=1)

    # Non-stationary spread
    fig.add_trace(go.Scatter(
        x=t, y=spread_non_coint,
        name="Spread",
        line=dict(color="red", width=2),
        fill='tozeroy',
        fillcolor='rgba(255,0,0,0.1)'
    ), row=1, col=2)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=2)

    # Cointegrated pair
    fig.add_trace(go.Scatter(x=t, y=asset1_coint, name="Asset 1", line=dict(color="blue")), row=2, col=1)
    fig.add_trace(go.Scatter(x=t, y=asset2_coint, name="Asset 2", line=dict(color="orange")), row=2, col=1)

    # Stationary spread
    fig.add_trace(go.Scatter(
        x=t, y=spread_coint,
        name="Spread",
        line=dict(color="green", width=2),
        fill='tozeroy',
        fillcolor='rgba(0,255,0,0.1)'
    ), row=2, col=2)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=2)
    fig.add_hline(y=np.mean(spread_coint), line_dash="dot", line_color="darkgreen", row=2, col=2)

    # Add annotations
    fig.add_annotation(
        text="Spread keeps drifting<br>Can diverge forever!<br>❌ Can't trade this",
        xref="x2", yref="y2",
        x=150, y=max(spread_non_coint)*0.8,
        showarrow=True,
        arrowhead=2,
        ax=-40, ay=-40,
        bgcolor="rgba(255,200,200,0.8)",
        row=1, col=2
    )

    fig.add_annotation(
        text="Spread oscillates around mean<br>Always returns!<br>✅ Can trade this",
        xref="x4", yref="y4",
        x=150, y=max(spread_coint)*0.8,
        showarrow=True,
        arrowhead=2,
        ax=-40, ay=-40,
        bgcolor="rgba(200,255,200,0.8)",
        row=2, col=2
    )

    fig.update_layout(
        height=800,
        showlegend=False,
        title_text="Understanding Cointegration: The Key Difference",
        title_font_size=16,
    )

    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_xaxes(title_text="Time", row=2, col=2)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Price", row=2, col=1)
    fig.update_yaxes(title_text="Spread", row=1, col=2)
    fig.update_yaxes(title_text="Spread", row=2, col=2)

    return fig


def plot_regression_explained(x_data, y_data, hedge_ratio, intercept):
    """
    Explain the linear regression step-by-step.

    Shows:
    1. Scatter plot of prices
    2. Regression line (the relationship)
    3. Residuals (the spread)
    """
    # Calculate fitted values and residuals
    y_fitted = hedge_ratio * x_data + intercept
    residuals = y_data - y_fitted

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Step 1: Find Linear Relationship (Regression)",
            "Step 2: Calculate Spread (Residuals)"
        ),
        horizontal_spacing=0.15,
    )

    # Left plot: Scatter + regression line
    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=y_data,
            mode='markers',
            name='Actual Prices',
            marker=dict(size=5, color='blue', opacity=0.5)
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=y_fitted,
            mode='lines',
            name=f'Regression Line<br>y = {hedge_ratio:.2f}x + {intercept:.2f}',
            line=dict(color='red', width=3)
        ),
        row=1, col=1
    )

    # Add some residual lines to show the concept
    sample_idx = np.linspace(0, len(x_data)-1, 20, dtype=int)
    for idx in sample_idx:
        fig.add_shape(
            type="line",
            x0=x_data[idx], y0=y_data[idx],
            x1=x_data[idx], y1=y_fitted[idx],
            line=dict(color="orange", width=1, dash="dot"),
            row=1, col=1
        )

    # Right plot: Residuals over time
    fig.add_trace(
        go.Scatter(
            x=np.arange(len(residuals)),
            y=residuals,
            mode='lines',
            name='Spread = Actual - Fitted',
            line=dict(color='purple', width=2)
        ),
        row=1, col=2
    )

    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=2)
    fig.add_hline(
        y=np.mean(residuals),
        line_dash="dot",
        line_color="green",
        annotation_text="Mean",
        row=1, col=2
    )

    # Add explanation annotations
    fig.add_annotation(
        text="Orange lines = Residuals<br>(vertical distance from line)<br>These become our SPREAD",
        xref="x", yref="y",
        x=x_data[len(x_data)//2], y=max(y_data)*0.95,
        showarrow=True,
        arrowhead=2,
        bgcolor="rgba(255,255,200,0.8)",
        row=1, col=1
    )

    fig.add_annotation(
        text="If this spread is STATIONARY<br>(always returns to mean)<br>Then assets are COINTEGRATED",
        xref="x2", yref="y2",
        x=len(residuals)*0.7, y=max(residuals)*0.8,
        showarrow=True,
        arrowhead=2,
        bgcolor="rgba(255,200,255,0.8)",
        row=1, col=2
    )

    fig.update_xaxes(title_text="ETC Price", row=1, col=1)
    fig.update_yaxes(title_text="ETH Price", row=1, col=1)
    fig.update_xaxes(title_text="Time", row=1, col=2)
    fig.update_yaxes(title_text="Spread (Residual)", row=1, col=2)

    fig.update_layout(
        height=500,
        title_text="How We Calculate the Spread from Regression",
        showlegend=True,
    )

    return fig


def plot_adf_test_explained(spread):
    """
    Visualize what the ADF test is actually checking.

    Shows:
    1. Spread over time
    2. Changes in spread (Δspread)
    3. Relationship between spread(t-1) and Δspread(t)
    """
    # Calculate changes
    spread_lag = spread[:-1]
    spread_delta = np.diff(spread)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "The Spread Over Time",
            "Changes in Spread (Δspread)",
            "ADF Test: Does spread(t-1) predict Δspread(t)?",
            "Test Results Interpretation"
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.12,
        specs=[[{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "scatter"}, {"type": "table"}]]
    )

    # Spread over time
    fig.add_trace(
        go.Scatter(
            x=np.arange(len(spread)),
            y=spread,
            mode='lines',
            name='Spread',
            line=dict(color='purple', width=2)
        ),
        row=1, col=1
    )
    fig.add_hline(y=np.mean(spread), line_dash="dash", line_color="green", row=1, col=1)

    # Delta spread
    fig.add_trace(
        go.Scatter(
            x=np.arange(len(spread_delta)),
            y=spread_delta,
            mode='lines',
            name='Δspread',
            line=dict(color='orange', width=1.5)
        ),
        row=1, col=2
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=2)

    # Scatter plot showing mean reversion
    fig.add_trace(
        go.Scatter(
            x=spread_lag,
            y=spread_delta,
            mode='markers',
            name='Each point',
            marker=dict(size=4, color='blue', opacity=0.5)
        ),
        row=2, col=1
    )

    # Add regression line for visual
    coeffs = np.polyfit(spread_lag, spread_delta, 1)
    x_range = np.array([min(spread_lag), max(spread_lag)])
    y_range = coeffs[0] * x_range + coeffs[1]

    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=y_range,
            mode='lines',
            name=f'Regression: slope={coeffs[0]:.4f}',
            line=dict(color='red', width=3)
        ),
        row=2, col=1
    )

    # Add interpretation
    if coeffs[0] < -0.01:
        interpretation = "✅ MEAN REVERTING"
        details = f"Negative slope ({coeffs[0]:.4f})<br>When spread ↑, next change ↓<br>When spread ↓, next change ↑<br><b>Spread returns to mean!</b>"
        color = "lightgreen"
    else:
        interpretation = "❌ NOT MEAN REVERTING"
        details = f"Slope near zero ({coeffs[0]:.4f})<br>Past spread doesn't predict change<br><b>Random walk behavior!</b>"
        color = "lightcoral"

    fig.add_annotation(
        text=details,
        xref="x3", yref="y3",
        x=max(spread_lag)*0.7, y=max(spread_delta)*0.7,
        showarrow=True,
        arrowhead=2,
        bgcolor=f"rgba(255,255,200,0.8)",
        row=2, col=1
    )

    # Create results table
    from scipy.stats import norm
    # Simplified - in reality uses DF distribution
    t_stat = coeffs[0] / (np.std(spread_delta) / np.sqrt(len(spread_delta)))

    table_data = [
        ["Metric", "Value", "Meaning"],
        ["Slope (β)", f"{coeffs[0]:.4f}", "Mean reversion strength"],
        ["ADF Statistic*", f"{t_stat:.2f}", "Test statistic"],
        ["Critical (5%)", "-2.86", "Threshold for significance"],
        ["Result", interpretation, "Statistical decision"],
    ]

    fig.add_trace(
        go.Table(
            header=dict(
                values=table_data[0],
                fill_color='paleturquoise',
                align='left',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=list(zip(*table_data[1:])),
                fill_color=[['white', color, 'white', color]],
                align='left',
                font=dict(size=11)
            )
        ),
        row=2, col=2
    )

    fig.update_xaxes(title_text="Time", row=1, col=1)
    fig.update_yaxes(title_text="Spread Value", row=1, col=1)
    fig.update_xaxes(title_text="Time", row=1, col=2)
    fig.update_yaxes(title_text="Change in Spread", row=1, col=2)
    fig.update_xaxes(title_text="Spread(t-1)", row=2, col=1)
    fig.update_yaxes(title_text="Δspread(t)", row=2, col=1)

    fig.update_layout(
        height=800,
        title_text="How the ADF Test Checks for Mean Reversion",
        showlegend=True,
    )

    fig.add_annotation(
        text="*Simplified calculation for illustration",
        xref="paper", yref="paper",
        x=0.99, y=0.01,
        showarrow=False,
        font=dict(size=10, color="gray")
    )

    return fig
