"""
dashboard.py
Interactive dashboard using Plotly + Dash to visualize SHAP explanations.
"""

import shap
import dash
import pandas as pd
from dash import dcc, html
import plotly.express as px

def launch_dashboard(shap_values, df, features):
    """
    Launch a Dash dashboard to visualize SHAP values.

    Args:
        shap_values: SHAP values object
        df (pd.DataFrame): TLS metadata DataFrame
        features (list): Feature columns
    """
    app = dash.Dash(__name__)

    # Feature importance summary
    importance = shap_values.values.mean(axis=0)
    fig = px.bar(
        x=importance,
        y=features,
        orientation="h",
        title="Feature Importance (SHAP)"
    )
    fig.update_traces(
        marker_color="rgba(92, 211, 210, 0.68)",
        marker_line_color="rgba(213, 249, 245, 0.8)",
        marker_line_width=1.5,
        opacity=0.88
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#C4D3EA", family="Inter, sans-serif"),
        title_font=dict(size=16, color="#F6F9FF"),
        hoverlabel=dict(bgcolor="rgba(16, 26, 58, 0.82)", bordercolor="rgba(135, 220, 208, 0.5)", font_color="#FFFFFF")
    )

    app.layout = html.Div([
        html.H1("Explainability Dashboard"),
        dcc.Graph(figure=fig)
    ])

    app.run_server(debug=True)
