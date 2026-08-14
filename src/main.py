"""Command-line entry point for the offline AI-PQC risk assessment pipeline."""

import argparse
from pathlib import Path

import pandas as pd

from src.anomaly_detection.isolation_forest import detect_anomalies, train_isolation_forest
from src.data_ingestion.ingest_logs import ingest_file
from src.data_ingestion.schema_validator import validate_schema
from src.explainability.report_generator import generate_report
from src.explainability.shap_explainer import explain_model
from src.recommendations.recommend_engine import generate_recommendations
from src.risk_classification.random_forest import classify_risk, train_random_forest
from src.rule_scanner.scanner import scan_tls_config
from src.utils.config import REPORT_PATH, TARGET_COLUMN
from src.utils.helpers import preprocess_data
from src.utils.logger import get_logger

logger = get_logger("ai_pqc")


def _bootstrap_risk_labels(df: pd.DataFrame) -> pd.Series:
    high = {"RSA_1024", "DH_1024", "SHA1", "NULL"}
    medium = {"RSA_OR_DH", "TLS_1_2", "WEAK_CIPHER"}

    def label(codes: str) -> str:
        values = set(filter(None, str(codes).split(";")))
        if values & high:
            return "High"
        if values & medium:
            return "Medium"
        return "Low"

    return df["rule_codes"].map(label)


def assess_dataframe(raw: pd.DataFrame, output_path: str | Path = REPORT_PATH) -> pd.DataFrame:
    """Assess a TLS metadata DataFrame and write an audit-ready PDF report."""
    validate_schema(raw)
    raw = scan_tls_config(raw.copy())
    features = preprocess_data(raw)
    feature_columns = features.columns.tolist()

    anomaly_model = train_isolation_forest(features, feature_columns)
    features = detect_anomalies(anomaly_model, features, feature_columns)
    raw[["anomaly_label", "anomaly_score"]] = features[["anomaly_label", "anomaly_score"]]

    if TARGET_COLUMN not in raw.columns:
        raw[TARGET_COLUMN] = _bootstrap_risk_labels(raw)
    features[TARGET_COLUMN] = raw[TARGET_COLUMN].values
    classifier = train_random_forest(features, feature_columns, TARGET_COLUMN)
    features = classify_risk(classifier, features, feature_columns)
    raw[["predicted_risk", "risk_confidence"]] = features[["predicted_risk", "risk_confidence"]]

    raw = generate_recommendations(raw)
    raw.attrs["shap_values"] = explain_model(classifier, features, feature_columns)
    counts = raw["predicted_risk"].value_counts()
    stats = {"total": len(raw), "high": counts.get("High", 0), "medium": counts.get("Medium", 0), "low": counts.get("Low", 0)}
    generate_report(output_path, raw, stats)
    logger.info("Assessment complete: %s", output_path)
    return raw


def run_pipeline(input_path: str | Path, output_path: str | Path = REPORT_PATH) -> pd.DataFrame:
    """Load a local TLS metadata file, assess it, and write a PDF report."""
    return assess_dataframe(ingest_file(input_path), output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Offline AI-PQC TLS risk assessment")
    parser.add_argument("--input", required=True, help="CSV, JSON, XLS, or XLSX TLS metadata file")
    parser.add_argument("--output", default=REPORT_PATH, help="Output PDF path")
    args = parser.parse_args()
    run_pipeline(args.input, args.output)
