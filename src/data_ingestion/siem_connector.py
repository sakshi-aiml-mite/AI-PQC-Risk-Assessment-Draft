"""
siem_connector.py
Mimics SIEM-style ingestion from logs/servers/devices.
"""

import pandas as pd
import random

def simulate_siem_ingestion(num_records: int = 100) -> pd.DataFrame:
    """
    Generate synthetic TLS metadata records to mimic SIEM ingestion.
    """
    protocols = ["TLS1.2", "TLS1.3"]
    algorithms = ["RSA", "ECDHE", "DH", None]
    key_sizes = [1024, 192, 256, 384, 2048, None]
    signatures = ["SHA1-RSA", "SHA256-RSA", "ECDSA-SHA256", "ECDSA-SHA384", "ECDSA-SHA512", None]
    cipher_suites = [
        "TLS_RSA_WITH_AES_256_GCM_SHA384",
        "TLS_RSA_WITH_AES_128_CBC_SHA",
        "TLS_DHE_RSA_WITH_AES_128_CBC_SHA",
        "TLS_DHE_RSA_WITH_AES_256_CBC_SHA",
        "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
        "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
        "TLS_AES_128_GCM_SHA256",
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256"
    ]

    records = []
    for _ in range(num_records):
        records.append({
            "protocol_version": random.choice(protocols),
            "key_exchange_algorithm": random.choice(algorithms),
            "key_size": random.choice(key_sizes),
            "certificate_signature_algorithm": random.choice(signatures),
            "cipher_suite": random.choice(cipher_suites)
        })

    return pd.DataFrame(records)
