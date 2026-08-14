"""
helpers.py
General helper functions for preprocessing and pipeline utilities.
"""

import pandas as pd

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess TLS metadata:
    - Handle null values
    - Encode categorical variables
    
    Args:
        df (pd.DataFrame): Raw TLS metadata
    
    Returns:
        pd.DataFrame: Cleaned and encoded DataFrame
    """
    # Fill nulls
    df = df.fillna("MISSING")

    # Encode categorical columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype("category").cat.codes

    return df

def summarize_findings(df: pd.DataFrame, findings_col: str = "rule_findings"):
    """
    Summarize rule findings across dataset.
    
    Args:
        df (pd.DataFrame): TLS metadata with findings
        findings_col (str): Column containing findings
    
    Returns:
        dict: Summary counts of findings
    """
    return df[findings_col].value_counts().to_dict()
