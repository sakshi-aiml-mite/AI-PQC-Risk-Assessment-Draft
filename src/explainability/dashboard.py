"""
dashboard.py
Interactive dashboard using Plotly + Dash to visualize SHAP explanations.
"""

import shap
import dash
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

    app.layout = html.Div([
        html.H1("Explainability Dashboard"),
        dcc.Graph(figure=fig)
    ])

    app.run_server(debug=True)
