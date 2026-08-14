# AI-PQC Risk Assessment

An offline application that evaluates TLS cryptographic configurations for post-quantum risk. It combines rule-based checks, Isolation Forest anomaly detection, Random Forest risk classification, NIST-aligned migration guidance, and a downloadable PDF audit report.

## What it does

- Imports TLS metadata from CSV, JSON, XLS, or XLSX files.
- Labels each configuration as Low, Medium, or High risk.
- Flags weak RSA/DH keys, SHA-1, missing cryptographic metadata, TLS 1.2, and CBC suites.
- Recommends migration actions such as TLS 1.3 adoption and hybrid ML-KEM key exchange planning.
- Provides a local browser UI with CSV upload, results preview, and PDF download.
- Runs locally; assessment data is not sent to an external service.

## Requirements

- Python 3.10 or later
- Git (only needed to clone the repository)
- A modern web browser for the dashboard

## Clone and run

```bash
git clone https://github.com/sakshi-aiml-mite/AI-PQC-Risk-Assessment-Draft.git
cd AI-PQC-Risk-Assessment-Draft
python -m venv .venv
```

Activate the virtual environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS or Linux
source .venv/bin/activate
```

Install dependencies and launch the local UI:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m src.ui.dashboard
```

Open `http://127.0.0.1:8050` in a browser. Upload a CSV, select **Generate risk report** to view the assessment, then select **Download PDF report** to download it. Stop the server with `Ctrl+C`.

## Input CSV schema

The dashboard requires these columns:

```text
protocol_version,key_exchange_algorithm,key_size,certificate_signature_algorithm,cipher_suite
```

Example:

```csv
TLS1.3,ECDHE,256,ECDSA-SHA256,TLS_AES_256_GCM_SHA384
TLS1.2,RSA,1024,SHA1-RSA,TLS_RSA_WITH_AES_128_CBC_SHA
```

## Sample files

Five small import-ready CSV files are in `sample_imports/`:

- `01_high_risk.csv`
- `02_mixed_risk.csv`
- `03_missing_metadata.csv`
- `04_tls12_upgrade.csv`
- `05_low_risk.csv`

## Command-line usage

To generate a report without opening the UI:

```bash
python -m src.main --input sample_imports/02_mixed_risk.csv --output results/assessment.pdf
```

## Tests

```bash
python -m pytest -q
```
