"""
ingest_logs.py
Parses TLS metadata logs from CSV/JSON files into a DataFrame.
"""

import pandas as pd

def ingest_csv(file_path: str) -> pd.DataFrame:
    """Load TLS metadata from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise RuntimeError(f"Error reading CSV: {e}")

def ingest_json(file_path: str) -> pd.DataFrame:
    """Load TLS metadata from a JSON file."""
    try:
        df = pd.read_json(file_path)
        return df
    except Exception as e:
        raise RuntimeError(f"Error reading JSON: {e}")
