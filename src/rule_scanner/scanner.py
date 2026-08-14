"""
scanner.py
Applies deterministic rules to ingested TLS metadata.
"""

import pandas as pd
from .rules import RULES

def scan_tls_config(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scan TLS metadata DataFrame against deterministic rules.
    
    Args:
        df (pd.DataFrame): TLS metadata with columns:
            protocol_version, key_exchange_algorithm, key_size,
            certificate_signature_algorithm, cipher_suite
    
    Returns:
        pd.DataFrame: Original data with an added 'rule_findings' column.
    """
    findings = []

    for _, row in df.iterrows():
        row_findings = []

        # Rule: RSA 1024-bit
        if row["key_exchange_algorithm"] == "RSA" and row["key_size"] == 1024:
            row_findings.append(RULES["RSA_1024"])

        # Rule: DH 1024-bit
        if row["key_exchange_algorithm"] == "DH" and row["key_size"] == 1024:
            row_findings.append(RULES["DH_1024"])

        # Rule: SHA1 signatures
        if isinstance(row["certificate_signature_algorithm"], str) and "SHA1" in row["certificate_signature_algorithm"]:
            row_findings.append(RULES["SHA1"])

        # Rule: Null values
        if pd.isnull(row["key_exchange_algorithm"]) or pd.isnull(row["key_size"]) or pd.isnull(row["certificate_signature_algorithm"]):
            row_findings.append(RULES["NULL"])

        findings.append("; ".join(row_findings) if row_findings else "No issues")

    df["rule_findings"] = findings
    return df
