"""Local Dash interface for offline TLS PQC risk assessments."""

import base64
import io
from datetime import datetime
from pathlib import Path

import dash
from dash import Input, Output, State, dcc, html
import pandas as pd
import plotly.graph_objects as go

from src.main import assess_dataframe
from src.explainability.report_generator import generate_report

RESULTS_DIR = Path("results")
REQUIRED_COLUMNS = ["protocol_version", "key_exchange_algorithm", "key_size", "certificate_signature_algorithm", "cipher_suite"]

# Updated Glassy Colors (More translucent, pastel, with bright borders)
RISK_COLORS = {
    "High": "rgba(255, 107, 139, 0.45)",   # Glassy Pink
    "Medium": "rgba(255, 187, 102, 0.45)", # Glassy Orange
    "Low": "rgba(102, 255, 191, 0.45)",    # Glassy Green
}
GLASS_BORDER_COLORS = {
    "High": "rgba(255, 220, 230, 0.95)",
    "Medium": "rgba(255, 235, 190, 0.95)",
    "Low": "rgba(200, 255, 230, 0.95)",
}
SIGNAL_COLOR = "rgba(160, 235, 255, 0.45)" # Glassy Cyan
SIGNAL_BORDER = "rgba(220, 250, 255, 0.95)"

app = dash.Dash(__name__, title="AI-PQC Risk Assessment", assets_folder=str(Path(__file__).resolve().parent / "assets"))
app.layout = html.Main([
    html.Div([html.Div("Q-SHIELD", className="brand"), html.Div("PQC readiness", className="tagline"), html.Div("LOCAL", className="privacy-badge")], className="topbar"),
    html.Section([
        html.Div([
            html.H1("PQC readiness"),
            html.P("Upload TLS metadata to assess exposure."),
            dcc.Upload(id="upload", children=html.Div([html.Strong("Upload CSV"), html.Span("Drop a file or browse")]), className="upload", multiple=False),
            html.Div(id="file-status"),
            html.Div(html.Button("Download Report", id="download-button", className="download", disabled=True), className="button-row"),
            dcc.Store(id="report-path"), dcc.Store(id="assessment-data"), dcc.Download(id="download-report"),
        ], className="hero-copy"),
    ], className="hero"),
    dcc.Loading(html.Div(id="results"), type="circle"),
], className="page")


def _decode_csv(contents: str) -> pd.DataFrame:
    _, encoded = contents.split(",", 1)
    return pd.read_csv(io.StringIO(base64.b64decode(encoded).decode("utf-8-sig")))


@app.callback(Output("file-status", "children"), Input("upload", "contents"), State("upload", "filename"))
def validate_upload(contents, filename):
    if not contents:
        return "Required columns: " + ", ".join(REQUIRED_COLUMNS)
    try:
        frame = _decode_csv(contents)
        missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
        if missing:
            return html.Div([html.Strong("Cannot use this file: "), "missing " + ", ".join(missing)], className="error")
        return html.Div([html.Strong(filename), f" — {len(frame):,} configurations ready"], className="success")
    except Exception as error:
        return html.Div(f"Could not read the CSV: {error}", className="error")


def _chart_layout(title):
    return dict(
        title=dict(text=title, font=dict(size=16, color="#F6F9FF", family="Inter, sans-serif"), x=.02),
        paper_bgcolor="rgba(0,0,0,0)", # Transparent for CSS glass effect
        plot_bgcolor="rgba(0,0,0,0)",   # Transparent for CSS glass effect
        font=dict(color="#D0E3FF", family="Inter, sans-serif"),
        margin=dict(l=45, r=25, t=48, b=42),
        legend=dict(orientation="h", y=-.2, font=dict(color="#E0F7FA")),
        hoverlabel=dict(
            bgcolor="rgba(20, 30, 60, 0.6)", # Glassy dark tooltip
            bordercolor="rgba(255, 255, 255, 0.3)",
            font_color="#FFFFFF",
            font=dict(family="Inter, sans-serif", size=12)
        )
    )


def _build_dashboard(result: pd.DataFrame):
    counts = result["predicted_risk"].value_counts()
    total = len(result)
    high, medium, low = (counts.get(level, 0) for level in ("High", "Medium", "Low"))
    readiness = round((low + medium * .45) / max(total, 1) * 100)
    avg_confidence = float(result["risk_confidence"].mean())
    risk_share = high / max(total, 1)
    finding_series = result.get("rule_findings", pd.Series(dtype=str)).fillna("").astype(str)
    finding_counts = finding_series.str.split(";").explode().str.strip().replace("", pd.NA).dropna().value_counts().head(6)

    # 1. Risk Pie Chart
    risk_figure = go.Figure(go.Pie(
        labels=["High", "Medium", "Low"],
        values=[high, medium, low],
        hole=.65,
        marker=dict(
            colors=[RISK_COLORS["High"], RISK_COLORS["Medium"], RISK_COLORS["Low"]],
            line=dict(color="rgba(255, 255, 255, 0.6)", width=1.5) # Bright thin border for glass edge
        ),
        textinfo="percent",
        textfont=dict(color="#FFFFFF", size=13, family="Inter, sans-serif"),
        hovertemplate="%{label}: %{value} configurations (%{percent})<extra></extra>",
        pull=[0.02, 0.02, 0.02] # Slight separation for smooth floating look
    ))
    risk_figure.update_layout(**_chart_layout("Risk"), annotations=[dict(text=f"<b>{readiness}%</b><br>ready", x=.5, y=.5, showarrow=False, font=dict(size=18, color="#FFFFFF", family="Inter, sans-serif"))])

    # 2. Protocol Bar Chart
    protocol = result.groupby(["protocol_version", "predicted_risk"]).size().unstack(fill_value=0).reindex(columns=["High", "Medium", "Low"], fill_value=0)
    protocol_figure = go.Figure()
    for risk in ("High", "Medium", "Low"):
        protocol_figure.add_bar(
            name=risk,
            x=protocol.index.astype(str),
            y=protocol[risk],
            marker=dict(
                color=RISK_COLORS[risk],
                line=dict(color=GLASS_BORDER_COLORS[risk], width=1.5),
                opacity=0.9
            ),
            hovertemplate=f"{risk}: %{{y}}<extra></extra>"
        )
    protocol_figure.update_layout(**_chart_layout("Protocols"), barmode="stack", xaxis_title="TLS", yaxis_title="", xaxis=dict(showgrid=False), yaxis=dict(showgrid=False, zeroline=False))

    # 3. Signals Bar Chart
    finding_figure = go.Figure(go.Bar(
        x=finding_counts.values,
        y=finding_counts.index,
        orientation="h",
        marker=dict(
            color=SIGNAL_COLOR,
            line=dict(color=SIGNAL_BORDER, width=1.5),
            opacity=0.9
        ),
        text=finding_counts.values,
        textposition="outside",
        textfont=dict(color="#E0F7FA", family="Inter, sans-serif"),
        hovertemplate="%{y}: %{x}<extra></extra>"
    ))
    finding_figure.update_layout(**_chart_layout("Signals"), xaxis_title="", yaxis_title="", xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=False))

    # 4. Confidence Line Chart (Smooth Curves)
    confidence = result.groupby("predicted_risk")["risk_confidence"].mean().reindex(["High", "Medium", "Low"], fill_value=0)
    confidence_figure = go.Figure(go.Scatter(
        x=confidence.index,
        y=confidence.values * 100,
        mode="lines+markers+text",
        line=dict(color="rgba(160, 235, 255, 0.85)", width=4, shape="spline", smoothing=1.3), # Max smoothing
        marker=dict(
            size=14,
            color=[RISK_COLORS[risk] for risk in confidence.index],
            line=dict(color="rgba(255, 255, 255, 0.9)", width=2),
            opacity=0.95
        ),
        text=[f"{value:.0%}" for value in confidence.values],
        textposition="top center",
        textfont=dict(size=12, color="#FFFFFF", family="Inter, sans-serif"),
        fill="tozeroy",
        fillcolor="rgba(160, 235, 255, 0.15)", # Soft glassy fill
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    confidence_figure.update_layout(**_chart_layout("Confidence"), yaxis=dict(range=[0, 115], ticksuffix="%", showgrid=False, zeroline=False), xaxis_title="")

    cards = html.Div([
        html.Div([html.Span("Configurations"), html.Strong(f"{total:,}")], className="card total"),
        html.Div([html.Span("High risk"), html.Strong(f"{high:,}")], className="card high"),
        html.Div([html.Span("Readiness"), html.Strong(f"{readiness}%")], className="card readiness"),
        html.Div([html.Span("Confidence"), html.Strong(f"{avg_confidence:.0%}")], className="card confidence"),
    ], className="cards")
    return html.Section([
        html.Div([html.H2("Assessment"), html.Div("Complete", className="status-chip")], className="results-heading"), cards,
        html.Div([
            html.Div(dcc.Graph(figure=risk_figure, config={"displayModeBar": False, "responsive": True}), className="chart-panel risk-panel"),
            html.Div(dcc.Graph(figure=protocol_figure, config={"displayModeBar": False, "responsive": True}), className="chart-panel protocol-panel"),
            html.Div(dcc.Graph(figure=finding_figure, config={"displayModeBar": False, "responsive": True}), className="chart-panel signal-panel"),
            html.Div(dcc.Graph(figure=confidence_figure, config={"displayModeBar": False, "responsive": True}), className="chart-panel confidence-panel"),
        ], className="chart-grid"),
    ], className="results")


@app.callback(Output("results", "children"), Output("assessment-data", "data"), Output("report-path", "data"), Output("download-button", "disabled"), Input("upload", "contents"), prevent_initial_call=True)
def assess_upload(contents):
    if not contents:
        return dash.no_update, None, None, True
    try:
        result = assess_dataframe(_decode_csv(contents), generate_pdf=False)
        RESULTS_DIR.mkdir(exist_ok=True)
        report_path = RESULTS_DIR / f"pqc_assessment_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        counts = result["predicted_risk"].value_counts()
        stats = {"total": len(result), "high": counts.get("High", 0), "medium": counts.get("Medium", 0), "low": counts.get("Low", 0)}
        generate_report(report_path, result, stats)
        return _build_dashboard(result), result.to_json(date_format="iso", orient="split"), str(report_path), False
    except Exception as error:
        return html.Div([html.H2("Assessment could not be completed"), html.P(str(error), className="error")], className="results"), None, None, True


@app.callback(Output("download-report", "data"), Input("download-button", "n_clicks"), State("report-path", "data"), prevent_initial_call=True)
def download_report(_, report_path):
    return dash.no_update if not report_path else dcc.send_file(report_path, filename="ai_pqc_tls_risk_report.pdf")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=False)