import csv
import random

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

with open("data/example_tls.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["protocol_version", "key_exchange_algorithm", "key_size", "certificate_signature_algorithm", "cipher_suite"])
    
    for _ in range(1000):
        writer.writerow([
            random.choice(protocols),
            random.choice(algorithms),
            random.choice(key_sizes),
            random.choice(signatures),
            random.choice(cipher_suites)
        ])
