"""
rules.py
Defines deterministic vulnerability rules for TLS configurations.
"""

# Example rules dictionary
RULES = {
    "RSA_1024": "Weak key size (RSA 1024-bit is quantum-vulnerable)",
    "DH_1024": "Weak key size (DH 1024-bit is insecure)",
    "SHA1": "Weak signature algorithm (SHA1 is deprecated)",
    "NULL": "Missing or invalid cryptographic parameter"
}

def get_rules():
    """Return all defined rules."""
    return RULES
