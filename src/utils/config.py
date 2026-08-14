"""
config.py
Centralized configuration for the TLS risk assessment pipeline.
"""

import os

# Default paths
DATA_PATH = os.getenv("DATA_PATH", "data/example_tls.csv")
REPORT_PATH = os.getenv("REPORT_PATH", "results/report.pdf")

# Feature columns for ML models
FEATURE_COLUMNS = [
    "key_size",
    "protocol_version",
    "key_exchange_algorithm",
    "certificate_signature_algorithm"
]

# Target column for classification
TARGET_COLUMN = "risk_label"
