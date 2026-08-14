"""Load TLS metadata from supported local structured files."""

from pathlib import Path
import pandas as pd


def ingest_csv(file_path: str | Path) -> pd.DataFrame:
    return pd.read_csv(file_path)


def ingest_json(file_path: str | Path) -> pd.DataFrame:
    return pd.read_json(file_path)


def ingest_file(file_path: str | Path) -> pd.DataFrame:
    """Load CSV, JSON, XLS, or XLSX data without making network calls."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {path}")
    readers = {".csv": pd.read_csv, ".json": pd.read_json, ".xls": pd.read_excel, ".xlsx": pd.read_excel}
    try:
        return readers[path.suffix.lower()](path)
    except KeyError as exc:
        raise ValueError("Supported input formats are CSV, JSON, XLS, and XLSX") from exc
