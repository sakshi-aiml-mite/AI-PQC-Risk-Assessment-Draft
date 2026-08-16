"""
test_pipeline.py
Unit tests for AI-PQC Risk Assessment pipeline.
"""

import os
import pandas as pd
import pytest

from src.data_ingestion.ingest_logs import ingest_csv
from src.data_ingestion.schema_validator import validate_schema
from src.rule_scanner.scanner import scan_tls_config
from src.anomaly_detection.isolation_forest import train_isolation_forest, detect_anomalies
from src.risk_classification.random_forest import train_random_forest, classify_risk
from src.recommendations.recommend_engine import generate_recommendations
from src.explainability.report_generator import _model_metrics
from src.model_evaluation import evaluate_models
from src.utils.helpers import preprocess_data

DATA_PATH = "data/example_tls.csv"

@pytest.fixture
def sample_df():
    """Load sample dataset for testing."""
    df = ingest_csv(DATA_PATH)
    validate_schema(df)
    return df

def test_ingestion(sample_df):
    """Test that ingestion loads data correctly."""
    assert isinstance(sample_df, pd.DataFrame)
    assert not sample_df.empty

def test_rule_scanner(sample_df):
    """Test rule scanner adds findings column."""
    df = scan_tls_config(sample_df)
    assert "rule_findings" in df.columns

def test_anomaly_detection(sample_df):
    """Test Isolation Forest anomaly detection."""
    df_clean = preprocess_data(sample_df)
    model = train_isolation_forest(df_clean, features=["key_size"])
    df = detect_anomalies(model, df_clean, features=["key_size"])
    assert "anomaly_label" in df.columns

def test_risk_classification(sample_df):
    """Test Random Forest risk classification."""
    df_clean = preprocess_data(sample_df)
    df_clean["risk_label"] = ["Low"] * len(df_clean)  # synthetic labels
    model = train_random_forest(df_clean, features=["key_size"], target="risk_label")
    df = classify_risk(model, df_clean, features=["key_size"])
    assert "predicted_risk" in df.columns

def test_recommendations(sample_df):
    """Test recommendation engine adds recommendations column."""
    df = scan_tls_config(sample_df)
    df = generate_recommendations(df)
    assert "recommendations" in df.columns


def test_model_metrics_include_classifier_and_anomaly_summaries():
    """The report metrics cover both models without fabricating anomaly labels."""
    frame = pd.DataFrame({
        "risk_label": ["High", "Low", "Low"],
        "predicted_risk": ["High", "Low", "High"],
        "anomaly_label": [-1, 1, 1],
        "anomaly_score": [0.4, -0.2, 0.1],
    })

    classifier, anomaly = _model_metrics(frame)

    assert classifier["samples"] == 3
    assert classifier["accuracy"] == pytest.approx(2 / 3)
    assert classifier["f1"] is not None
    assert classifier["confusion"] == (["High", "Low"], [[1, 0], [1, 1]])
    assert anomaly["samples"] == 3
    assert anomaly["accuracy"] == pytest.approx(1.0)
    assert anomaly["precision"] == pytest.approx(1.0)
    assert anomaly["recall"] == pytest.approx(1.0)
    assert anomaly["f1"] == pytest.approx(1.0)
    assert anomaly["confusion"] == (["Normal", "Anomaly"], [[2, 0], [0, 1]])


def test_cross_validated_evaluation_uses_supplied_anomaly_labels():
    features = pd.DataFrame({"key_size": [0.0, 0.1, 0.2, 0.3, 0.7, 0.8, 0.9, 1.0]})
    evaluation = evaluate_models(
        features,
        pd.Series(["Low", "Low", "Low", "Low", "High", "High", "High", "High"]),
        pd.Series([0, 0, 0, 0, 1, 1, 1, 1]),
    )

    assert "cross-validation" in evaluation["classification_method"]
    assert "cross-validation" in evaluation["anomaly_method"]
    assert evaluation["classification"]["confusion"] is not None
    assert evaluation["anomaly"]["confusion"] is not None
