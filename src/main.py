"""
main.py
Entry point for AI-PQC Risk Assessment pipeline.
"""

import argparse
import pandas as pd

# Import modules
from data_ingestion.ingest_logs import ingest_csv
from data_ingestion.schema_validator import validate_schema
from rule_scanner.scanner import scan_tls_config
from anomaly_detection.isolation_forest import train_isolation_forest, detect_anomalies
from risk_classification.random_forest import train_random_forest, classify_risk
from recommendations.recommend_engine import generate_recommendations
from explainability.shap_explainer import explain_model
from explainability.report_generator import generate_report
from utils.helpers import preprocess_data
from utils.config import FEATURE_COLUMNS, TARGET_COLUMN, REPORT_PATH
from utils.logger import get_logger

logger = get_logger("main")

def run_pipeline(input_path: str, output_path: str):
    # Step 1: Ingest data
    logger.info("Ingesting data...")
    df = ingest_csv(input_path)

    # Step 2: Validate schema
    logger.info("Validating schema...")
    validate_schema(df)

    # Step 3: Rule-based scanning
    logger.info("Running rule scanner...")
    df = scan_tls_config(df)

    # Step 4: Preprocess data
    logger.info("Preprocessing data...")
    df_clean = preprocess_data(df)

    # Step 5: Anomaly detection
    logger.info("Training Isolation Forest...")
    iso_model = train_isolation_forest(df_clean, features=["key_size"])
    df = detect_anomalies(iso_model, df_clean, features=["key_size"])

    # Step 6: Risk classification
    logger.info("Training Random Forest classifier...")
    # For demo, create synthetic risk labels if not present
    if TARGET_COLUMN not in df.columns:
        df[TARGET_COLUMN] = df["anomaly_label"].apply(lambda x: "High" if x == -1 else "Low")

    rf_model = train_random_forest(df, features=["key_size"], target=TARGET_COLUMN)
    df = classify_risk(rf_model, df, features=["key_size"])

    # Step 7: Recommendations
    logger.info("Generating recommendations...")
    df = generate_recommendations(df)

    # Step 8: Explainability
    logger.info("Generating SHAP explanations...")
    shap_values = explain_model(rf_model, df, features=["key_size"])

    # Step 9: Report generation
    logger.info("Generating PDF report...")
    generate_report(
        output_path,
        findings=df["rule_findings"].tolist(),
        recommendations=df["recommendations"].tolist()
    )

    logger.info("Pipeline completed successfully.")
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-PQC Risk Assessment Pipeline")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV file")
    parser.add_argument("--output", type=str, default=REPORT_PATH, help="Path to output PDF report")
    args = parser.parse_args()

    run_pipeline(args.input, args.output)
