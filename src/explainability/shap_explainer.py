"""
shap_explainer.py
Generates SHAP values to explain Random Forest risk classification.
"""

import shap
import pandas as pd

def explain_model(model, df: pd.DataFrame, features: list):
    """
    Generate SHAP values for the trained model.
    
    Args:
        model: Trained RandomForestClassifier
        df (pd.DataFrame): TLS metadata DataFrame
        features (list): Feature columns
    
    Returns:
        shap.Explanation: SHAP values object
    """
    X = df[features].fillna(-1)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X)
    return shap_values
