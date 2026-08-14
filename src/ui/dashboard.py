"""Local Dash interface for offline TLS PQC risk assessments."""

import base64
import io
from datetime import datetime
from pathlib import Path

import dash
from dash import Input, Output, State, dcc, html, dash_table
import pandas as pd

from src.main import assess_dataframe

RESULTS_DIR = Path("results")
REQUIRED_COLUMNS = ["protocol_version", "key_exchange_algorithm", "key_size", "certificate_signature_algorithm", "cipher_suite"]

app = dash.Dash(__name__, title="AI-PQC Risk Assessment")
app.layout = html.Main([
    html.Div([html.Div("AI-PQC", className="brand"), html.Div("Offline TLS cryptographic readiness assessment", className="tagline")], className="topbar"),
    html.Section([
        html.H1("Assess your TLS configurations"),
        html.P("Upload a CSV, review the AI-assisted risk results, then download an audit-ready PDF. All processing stays on this computer."),
        dcc.Upload(id="upload", children=html.Div([html.Strong("Choose a CSV file"), html.Span(" or drag it here")]), className="upload", multiple=False),
        html.Div(id="file-status"),
        html.Div([
            html.Button("Generate risk report", id="run", className="run", disabled=True),
            html.Button("Download PDF report", id="download-button", className="download", disabled=True),
        ], className="button-row"),
        dcc.Store(id="report-path"),
        dcc.Download(id="download-report"),
    ], className="hero"),
    dcc.Loading(html.Div(id="results"), type="circle"),
], className="page")


def _decode_csv(contents: str) -> pd.DataFrame:
    _, encoded = contents.split(",", 1)
    return pd.read_csv(io.StringIO(base64.b64decode(encoded).decode("utf-8-sig")))


@app.callback(Output("file-status", "children"), Output("run", "disabled"), Input("upload", "contents"), State("upload", "filename"))
def validate_upload(contents, filename):
    if not contents:
        return "Required columns: " + ", ".join(REQUIRED_COLUMNS), True
    try:
        frame = _decode_csv(contents)
        missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
        if missing:
            return html.Div([html.Strong("Cannot use this file: "), "missing " + ", ".join(missing)], className="error"), True
        return html.Div([html.Strong(filename), f" — {len(frame):,} configurations ready to assess"], className="success"), False
    except Exception as error:
        return html.Div(f"Could not read the CSV: {error}", className="error"), True


@app.callback(Output("results", "children"), Output("report-path", "data"), Output("download-button", "disabled"), Input("run", "n_clicks"), State("upload", "contents"), prevent_initial_call=True)
def assess_upload(_, contents):
    try:
        frame = _decode_csv(contents)
        RESULTS_DIR.mkdir(exist_ok=True)
        report_path = RESULTS_DIR / f"pqc_assessment_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        result = assess_dataframe(frame, report_path)
        counts = result["predicted_risk"].value_counts()
        cards = html.Div([
            html.Div([html.Span("Total"), html.Strong(str(len(result)))], className="card total"),
            html.Div([html.Span("High risk"), html.Strong(str(counts.get("High", 0)))], className="card high"),
            html.Div([html.Span("Medium risk"), html.Strong(str(counts.get("Medium", 0)))], className="card medium"),
            html.Div([html.Span("Low risk"), html.Strong(str(counts.get("Low", 0)))], className="card low"),
        ], className="cards")
        columns = ["protocol_version", "key_exchange_algorithm", "key_size", "predicted_risk", "risk_confidence", "rule_findings", "recommendations"]
        preview = result.loc[:, columns].copy()
        preview["risk_confidence"] = preview["risk_confidence"].map(lambda value: f"{value:.0%}")
        content = html.Section([html.H2("Assessment results"), cards, html.H3("Configuration-level findings"), dash_table.DataTable(preview.to_dict("records"), [{"name": column.replace("_", " ").title(), "id": column} for column in columns], page_size=10, style_table={"overflowX": "auto"}, style_cell={"textAlign": "left", "whiteSpace": "normal", "height": "auto", "fontFamily": "Arial", "fontSize": 13, "padding": "10px"}, style_header={"backgroundColor": "#102A43", "color": "white", "fontWeight": "bold"}, style_data_conditional=[{"if": {"filter_query": '{predicted_risk} = "High"', "column_id": "predicted_risk"}, "color": "#B42318", "fontWeight": "bold"}, {"if": {"filter_query": '{predicted_risk} = "Medium"', "column_id": "predicted_risk"}, "color": "#B54708", "fontWeight": "bold"}, {"if": {"filter_query": '{predicted_risk} = "Low"', "column_id": "predicted_risk"}, "color": "#027A48", "fontWeight": "bold"}])], className="results")
        return content, str(report_path), False
    except Exception as error:
        return html.Div([html.H2("Assessment could not be completed"), html.P(str(error), className="error")], className="results"), None, True


@app.callback(Output("download-report", "data"), Input("download-button", "n_clicks"), State("report-path", "data"), prevent_initial_call=True)
def download_report(_, report_path):
    if not report_path:
        return dash.no_update
    return dcc.send_file(report_path, filename="ai_pqc_tls_risk_report.pdf")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=False)
