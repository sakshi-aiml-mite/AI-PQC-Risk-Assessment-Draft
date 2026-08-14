"""
schema_validator.py
Validates TLS metadata schema before processing.
"""

import pandas as pd

REQUIRED_COLUMNS = [
    "protocol_version",
    "key_exchange_algorithm",
    "key_size",
    "certificate_signature_algorithm",
    "cipher_suite"
]

def validate_schema(df: pd.DataFrame) -> bool:
    """Check if DataFrame contains required columns."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True
