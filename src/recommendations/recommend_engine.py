"""
recommend_engine.py
Generates migration guidance based on rule findings and NIST mappings.
"""

import pandas as pd
from .nist_mapper import map_vulnerability

def generate_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate PQC migration recommendations for each TLS record.
    
    Args:
        df (pd.DataFrame): TLS metadata with 'rule_findings' column
    
    Returns:
        pd.DataFrame: DataFrame with added 'recommendations' column
    """
    recs = []

    for _, row in df.iterrows():
        codes = str(row.get("rule_codes", ""))
        if not codes:
            recs.append("TLS configuration is PQC-ready")
        else:
            vuln_list = codes.split(";")
            mapped = [map_vulnerability(v) for v in vuln_list if v]
            recs.append("; ".join(mapped))

    df["recommendations"] = recs
    return df
