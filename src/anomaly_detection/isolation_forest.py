"""Isolation Forest anomaly detection for prepared TLS feature vectors."""

import pandas as pd
from sklearn.ensemble import IsolationForest


def train_isolation_forest(df: pd.DataFrame, features: list[str], random_state: int = 42):
    model = IsolationForest(contamination="auto", random_state=random_state)
    model.fit(df[features].fillna(0))
    return model


def detect_anomalies(model, df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    result = df.copy()
    values = result[features].fillna(0)
    result["anomaly_label"] = model.predict(values)
    result["anomaly_score"] = -model.decision_function(values)
    return result
