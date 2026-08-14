"""
train.py
Training script for Isolation Forest anomaly detection.
"""

import pandas as pd
from .isolation_forest import train_isolation_forest

def run_training(data_path: str, features: list):
    """
    Train Isolation Forest on given dataset.
    
    Args:
        data_path (str): Path to CSV dataset
        features (list): Feature columns
    
    Returns:
        model (IsolationForest): Trained model
    """
    df = pd.read_csv(data_path)
    model = train_isolation_forest(df, features)
    return model
