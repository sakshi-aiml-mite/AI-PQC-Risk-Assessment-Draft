# AI-PQC Risk Assessment Pipeline

## Overview
This project implements an **AI-driven Post-Quantum Cryptography (PQC) Risk Assessment Pipeline** for TLS configurations.  
It combines deterministic rule scanning, anomaly detection, risk classification, recommendations, and explainability to guide secure migration paths aligned with NIST standards.

---

## Features
- **Data Ingestion**: Load TLS metadata from CSV/JSON or simulate SIEM logs.
- **Rule Scanner**: Deterministic checks for weak keys, deprecated algorithms, and null values.
- **Anomaly Detection**: Isolation Forest to flag unusual TLS configurations.
- **Risk Classification**: Random Forest classifier for risk scoring (High/Medium/Low).
- **Recommendations**: Maps vulnerabilities to NIST PQC migration paths.
- **Explainability**: SHAP-based insights, interactive dashboard, and PDF reports.
- **Utilities**: Config, logging, and preprocessing helpers.
- **Testing**: Unit tests with `pytest`.

---

## Project Structure

```text
data/
  example_tls.csv
src/
  data_ingestion/
  rule_scanner/
  anomaly_detection/
  risk_classification/
  recommendations/
  explainability/
  utils/
  main.py
notebooks/
  demo_pipeline.ipynb
tests/
  test_pipeline.py
docs/
  methodology.md
  architecture.png

```

## Installation
```bash
# Clone repo
git clone https://github.com/sakshi-aiml-mite/AI-PQC-Risk-Assessment-Draft
cd AI-PQC-Risk-Assessment-Draft

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

