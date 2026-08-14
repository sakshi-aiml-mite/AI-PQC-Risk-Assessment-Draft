"""Preprocessing and summary helpers."""

import pandas as pd

MODEL_COLUMNS = ["protocol_version", "key_exchange_algorithm", "key_size", "certificate_signature_algorithm", "cipher_suite", "rule_codes"]


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Median-impute key size, one-hot encode TLS fields, and min-max scale it."""
    data = df.loc[:, [column for column in MODEL_COLUMNS if column in df]].copy()
    data["key_size"] = pd.to_numeric(data["key_size"], errors="coerce")
    median = data["key_size"].median()
    data["key_size"] = data["key_size"].fillna(0 if pd.isna(median) else median)
    maximum, minimum = data["key_size"].max(), data["key_size"].min()
    data["key_size"] = 0.0 if maximum == minimum else (data["key_size"] - minimum) / (maximum - minimum)
    categorical = data.select_dtypes(include=["object", "string"]).columns
    data[categorical] = data[categorical].fillna("UNKNOWN")
    return pd.get_dummies(data, columns=categorical, dtype=float)


def summarize_findings(df: pd.DataFrame, findings_col: str = "rule_findings") -> dict:
    return df[findings_col].value_counts().to_dict()
