"""Configuration du logger partagé."""

import logging
import sys
from pathlib import Path

from config import LOGS_DIR


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger configuré (stdout INFO + fichier DEBUG)."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler console : INFO et au-dessus
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)

    # Handler fichier : DEBUG et au-dessus
    log_file = LOGS_DIR / "extraction.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    logger.addHandler(console)
    logger.addHandler(file_handler)

    return logger
