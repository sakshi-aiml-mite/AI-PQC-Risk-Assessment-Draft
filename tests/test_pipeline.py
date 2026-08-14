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
