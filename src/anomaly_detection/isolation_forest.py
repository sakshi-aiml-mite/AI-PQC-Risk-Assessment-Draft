"""
isolation_forest.py
Implements Isolation Forest for anomaly detection on TLS metadata.
"""

import pandas as pd
from sklearn.ensemble import IsolationForest

def train_isolation_forest(df: pd.DataFrame, features: list, random_state: int = 42):
    """
    Train an Isolation Forest model.
    
    Args:
        df (pd.DataFrame): TLS metadata DataFrame
        features (list): List of feature column names
        random_state (int): Random seed
    
    Returns:
        model (IsolationForest): Trained model
    """
    X = df[features].fillna(-1)  # Replace nulls with -1 for training
    model = IsolationForest(random_state=random_state)
    model.fit(X)
    return model

def detect_anomalies(model, df: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Apply Isolation Forest to detect anomalies.
    
    Args:
        model (IsolationForest): Trained model
        df (pd.DataFrame): TLS metadata DataFrame
        features (list): Feature columns
    
    Returns:
        pd.DataFrame: DataFrame with anomaly labels (-1 = anomaly, 1 = normal)
    """
    X = df[features].fillna(-1)
    df["anomaly_label"] = model.predict(X)
    return df
