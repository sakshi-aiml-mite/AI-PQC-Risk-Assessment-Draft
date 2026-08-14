"""
train.py
Training script for Random Forest risk classification.
"""

import pandas as pd
from .random_forest import train_random_forest

def run_training(data_path: str, features: list, target: str):
    """
    Train Random Forest classifier on given dataset.
    
    Args:
        data_path (str): Path to CSV dataset
        features (list): Feature columns
        target (str): Target column (risk label)
    
    Returns:
        model (RandomForestClassifier): Trained model
    """
    df = pd.read_csv(data_path)
    model = train_random_forest(df, features, target)
    return model
