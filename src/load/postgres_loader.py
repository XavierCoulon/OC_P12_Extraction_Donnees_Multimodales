"""Chargement des données transformées (Parquet) vers PostgreSQL."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from config import PROCESSED_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_PARQUET = PROCESSED_DIR / "transformed.parquet"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id            TEXT PRIMARY KEY,
    source        TEXT,
    title         TEXT,
    text          TEXT,
    image_url     TEXT,
    image_path    TEXT,
    label         TEXT,
    label_int     INTEGER,
    label_confidence TEXT,
    language      TEXT,
    date          TEXT,
    url           TEXT,
    domain        TEXT,
    extraction_method TEXT,
    image_valid   BOOLEAN,
    has_image     BOOLEAN,
    text_image_ok BOOLEAN,
    text_length   INTEGER,
    word_count    INTEGER
);
"""

_UPSERT_SQL = """
INSERT INTO articles (
    id, source, title, text, image_url, image_path,
    label, label_int, label_confidence, language, date,
    url, domain, extraction_method,
    image_valid, has_image, text_image_ok, text_length, word_count
) VALUES (
    :id, :source, :title, :text, :image_url, :image_path,
    :label, :label_int, :label_confidence, :language, :date,
    :url, :domain, :extraction_method,
    :image_valid, :has_image, :text_image_ok, :text_length, :word_count
)
ON CONFLICT (id) DO NOTHING;
"""


def load_parquet_to_postgres(
    parquet_path: Path = _DEFAULT_PARQUET,
) -> dict:
    """Charge le Parquet transformé dans la table PostgreSQL `articles`.

    Idempotent : ON CONFLICT (id) DO NOTHING — les données source étant
    statiques, un re-run ne modifie pas les entrées existantes.

    Returns:
        dict avec les clés ``rows_read`` et ``rows_inserted``.
    """
    db_url = os.environ.get("DATA_POSTGRES_URL")
    if not db_url:
        raise EnvironmentError("Variable DATA_POSTGRES_URL non définie.")

    logger.info("Lecture Parquet : %s", parquet_path)
    df = pd.read_parquet(parquet_path)
    rows_read = len(df)
    logger.info("%d lignes lues.", rows_read)

    # Colonnes attendues (avec valeurs par défaut si absentes)
    defaults = {
        "title": "",
        "image_url": "",
        "image_path": "",
        "label_int": -1,
        "label_confidence": "low",
        "language": "en",
        "date": "",
        "url": "",
        "domain": "",
        "extraction_method": "",
        "image_valid": False,
        "has_image": False,
        "text_image_ok": False,
        "text_length": 0,
        "word_count": 0,
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    engine = create_engine(db_url)
    rows_inserted = 0

    with engine.begin() as conn:
        conn.execute(text(_CREATE_TABLE_SQL))
        for row in df.to_dict(orient="records"):
            result = conn.execute(text(_UPSERT_SQL), row)
            rows_inserted += result.rowcount

    logger.info("Insertion terminée : %d/%d lignes insérées.", rows_inserted, rows_read)
    return {"rows_read": rows_read, "rows_inserted": rows_inserted}
