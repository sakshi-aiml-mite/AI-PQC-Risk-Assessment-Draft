# Methodology

## Overview
This project implements an **AI-driven Post-Quantum Cryptography (PQC) Risk Assessment Pipeline**. The methodology combines deterministic rule scanning, anomaly detection, risk classification, recommendations, and explainability to evaluate TLS configurations and guide secure migration paths.

---

## 1. Data Ingestion
- **Source formats**: CSV and JSON logs, plus synthetic SIEM-style records.
- **Schema validation**: Ensures required fields exist (`protocol_version`, `key_exchange_algorithm`, `key_size`, `certificate_signature_algorithm`, `cipher_suite`).
- **Preprocessing**: Handles null values, encodes categorical variables, and prepares features for ML models.

---

## 2. Rule-Based Scanning
- Deterministic rules flag insecure configurations:
  - RSA/DH with 1024-bit keys
  - SHA1 signatures
  - Missing/null cryptographic parameters
- Output: `rule_findings` column with human-readable vulnerability notes.

---

## 3. Anomaly Detection
- **Model**: Isolation Forest
- **Features**: Primarily `key_size` and related cryptographic parameters.
- **Purpose**: Detect unusual or suspicious TLS configurations compared to baseline.
- Output: `anomaly_label` column (`-1` = anomaly, `1` = normal).

---

## 4. Risk Classification
- **Model**: Random Forest Classifier
- **Target**: `risk_label` (e.g., High, Medium, Low).
- **Features**: Key size, algorithm type, signature scheme.
- Output: `predicted_risk` column with risk scores.

---

## 5. Recommendations
- Vulnerabilities mapped to **NIST PQC migration paths**:
  - Replace RSA/DH 1024 → CRYSTALS-Kyber
  - Replace SHA1 → SHA-3 or SHA-2 family
  - Null values → enforce PQC algorithm selection (Kyber, Dilithium)
- Output: `recommendations` column with actionable guidance.

---

## 6. Explainability
- **SHAP values**: Explain why the model flagged certain risks.
- **Dashboard**: Interactive visualization of feature importance.
- **Reports**: PDF summaries combining findings and recommendations for stakeholders.

---

## 7. End-to-End Pipeline
- Orchestrated in `main.py` and `notebooks/demo_pipeline.ipynb`.
- Steps:
  1. Ingest → Validate → Preprocess
  2. Rule Scanner → Anomaly Detection → Risk Classification
  3. Recommendations → Explainability → Report Generation

---

## 8. Testing & Validation
- **Unit tests** (`tests/test_pipeline.py`) ensure each module works independently.
- **CI/CD** integration (optional) with GitHub Actions for automated testing.
- **Evaluation metrics**: Classification report, confusion matrix, anomaly detection precision/recall.

---

## 9. Deliverables
- Modular Python codebase (`src/`).
- Large dataset (`data/example_tls.csv`) with 1000+ rows and null values.
- Interactive Jupyter notebook (`notebooks/demo_pipeline.ipynb`).
- PDF risk assessment reports (`results/report.pdf`).
