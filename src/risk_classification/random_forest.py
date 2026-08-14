"""
random_forest.py
Implements Random Forest classifier for TLS risk scoring.
"""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

def train_random_forest(df: pd.DataFrame, features: list, target: str, random_state: int = 42):
    """
    Train a Random Forest classifier.
    
    Args:
        df (pd.DataFrame): TLS metadata DataFrame
        features (list): Feature column names
        target (str): Target column name (risk label)
        random_state (int): Random seed
    
    Returns:
        model (RandomForestClassifier): Trained model
    """
    X = df[features].fillna(0)
    y = df[target]
    model = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=random_state)
    model.fit(X, y)
    return model

def classify_risk(model, df: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Apply Random Forest classifier to predict risk levels.
    
    Args:
        model (RandomForestClassifier): Trained model
        df (pd.DataFrame): TLS metadata DataFrame
        features (list): Feature columns
    
    Returns:
        pd.DataFrame: DataFrame with predicted risk labels
    """
    result = df.copy()
    probabilities = model.predict_proba(result[features].fillna(0))
    result["predicted_risk"] = model.classes_[probabilities.argmax(axis=1)]
    result["risk_confidence"] = probabilities.max(axis=1)
    return result
