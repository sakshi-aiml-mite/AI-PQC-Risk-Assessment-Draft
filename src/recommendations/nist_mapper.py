"""
nist_mapper.py
Maps vulnerabilities to NIST-aligned post-quantum cryptographic alternatives.
"""

# Example mapping dictionary
NIST_PQC_MAPPING = {
    "RSA_1024": "Replace with a hybrid key exchange using NIST FIPS 203 ML-KEM.",
    "DH_1024": "Replace with a hybrid key exchange using NIST FIPS 203 ML-KEM.",
    "SHA1": "Replace with SHA-3 or SHA-2 family",
    "NULL": "Validate the missing parameter and select compatible ML-KEM and ML-DSA algorithms.",
    "RSA_OR_DH": "Plan a hybrid TLS key exchange using NIST FIPS 203 ML-KEM.",
    "TLS_1_2": "Upgrade to TLS 1.3 before introducing a hybrid ML-KEM key exchange.",
    "WEAK_CIPHER": "Replace CBC suites with TLS 1.3 AEAD suites (AES-GCM or ChaCha20-Poly1305).",
}

def map_vulnerability(vuln_code: str) -> str:
    """
    Map vulnerability code to NIST PQC recommendation.
    
    Args:
        vuln_code (str): Vulnerability identifier
    
    Returns:
        str: Recommended PQC alternative
    """
    return NIST_PQC_MAPPING.get(vuln_code, "No specific recommendation available")
