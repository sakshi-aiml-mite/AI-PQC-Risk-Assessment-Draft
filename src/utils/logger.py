"""
logger.py
Configurable logging utility for the pipeline.
"""

import logging

def get_logger(name: str):
    """
    Create and configure a logger.
    
    Args:
        name (str): Logger name
    
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)

    # Attach handler
    if not logger.handlers:
        logger.addHandler(ch)

    return logger
