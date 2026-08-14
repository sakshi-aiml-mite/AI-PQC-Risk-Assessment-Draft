"""
evaluate.py
Evaluation metrics for risk classification.
"""

import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

def evaluate_classification(df: pd.DataFrame, target: str, prediction: str):
    """
    Evaluate classification results.
    
    Args:
        df (pd.DataFrame): DataFrame with target and prediction columns
        target (str): Ground truth column
        prediction (str): Predicted column
    
    Returns:
        dict: Evaluation metrics (classification report + confusion matrix)
    """
    if target not in df.columns or prediction not in df.columns:
        raise ValueError("DataFrame must contain target and prediction columns")

    report = classification_report(df[target], df[prediction], output_dict=True)
    matrix = confusion_matrix(df[target], df[prediction])

    return {
        "classification_report": report,
        "confusion_matrix": matrix.tolist()
    }
