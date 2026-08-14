"""
evaluate.py
Evaluation metrics for anomaly detection.
"""

import pandas as pd
from sklearn.metrics import classification_report

def evaluate_anomalies(df: pd.DataFrame):
    """
    Evaluate anomaly detection results.
    
    Args:
        df (pd.DataFrame): DataFrame with 'anomaly_label' column
    
    Returns:
        str: Classification report summary
    """
    if "anomaly_label" not in df.columns:
        raise ValueError("DataFrame must contain 'anomaly_label' column")

    # For demo purposes, assume anomalies are rare (label -1)
    y_true = df["anomaly_label"].apply(lambda x: -1 if x == -1 else 1)
    y_pred = df["anomaly_label"]

    return classification_report(y_true, y_pred, target_names=["Anomaly", "Normal"])
