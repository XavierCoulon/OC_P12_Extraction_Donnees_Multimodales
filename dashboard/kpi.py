"""Chargement des KPIs depuis PostgreSQL (articles + pipeline_runs)."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Connexion
# ---------------------------------------------------------------------------

def get_engine():
    """Crée un engine SQLAlchemy depuis DATA_POSTGRES_URL."""
    db_url = os.environ.get("DATA_POSTGRES_URL")
    if not db_url:
        raise EnvironmentError(
            "Variable DATA_POSTGRES_URL non définie. "
            "Exemple : postgresql+psycopg2://etl_user:pwd@localhost/multimodal"
        )
    return create_engine(db_url)


# ---------------------------------------------------------------------------
# KPIs qualité — table articles
# ---------------------------------------------------------------------------

_QUALITY_SQL = """
SELECT
    source,
    COUNT(*)                                      AS total,
    SUM(image_valid::int)                         AS image_valid_count,
    SUM(text_image_ok::int)                       AS text_image_ok_count,
    SUM(has_image::int)                           AS has_image_count,
    ROUND(AVG(text_length)::numeric, 0)           AS avg_text_length,
    ROUND(AVG(word_count)::numeric, 0)            AS avg_word_count
FROM articles
GROUP BY source
ORDER BY source;
"""

_LABEL_SQL = """
SELECT source, label, COUNT(*) AS count
FROM articles
GROUP BY source, label
ORDER BY source, label;
"""


def load_quality_kpis() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retourne (df_quality, df_labels) depuis la table articles.

    Returns:
        df_quality : métriques par source (image_valid_pct, text_image_ok_pct, …)
        df_labels  : distribution labels par source
    """
    engine = get_engine()
    with engine.connect() as conn:
        df_q = pd.read_sql(text(_QUALITY_SQL), conn)
        df_l = pd.read_sql(text(_LABEL_SQL), conn)

    # Calcul pourcentages
    df_q["image_valid_pct"] = (df_q["image_valid_count"] / df_q["total"] * 100).round(1)
    df_q["text_image_ok_pct"] = (df_q["text_image_ok_count"] / df_q["total"] * 100).round(1)
    df_q["has_image_pct"] = (df_q["has_image_count"] / df_q["total"] * 100).round(1)

    return df_q, df_l


# ---------------------------------------------------------------------------
# KPIs performance — table pipeline_runs
# ---------------------------------------------------------------------------

_RUNS_SQL = """
SELECT
    run_id,
    run_date,
    task,
    source,
    total,
    success,
    skipped,
    errors,
    duration_s,
    parquet_rows,
    parquet_mb
FROM pipeline_runs
ORDER BY run_date, task;
"""

_RUNS_EXISTS_SQL = """
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_name = 'pipeline_runs'
);
"""


def load_run_history() -> pd.DataFrame:
    """Retourne l'historique complet des runs depuis pipeline_runs.

    Retourne un DataFrame vide si la table n'existe pas encore.
    """
    engine = get_engine()
    with engine.connect() as conn:
        exists = conn.execute(text(_RUNS_EXISTS_SQL)).scalar()
        if not exists:
            return pd.DataFrame()
        df = pd.read_sql(text(_RUNS_SQL), conn)

    if df.empty:
        return df

    df["run_date"] = pd.to_datetime(df["run_date"])
    df["error_rate"] = (df["errors"] / df["total"].replace(0, 1) * 100).round(1)
    return df


def load_latest_run(df_history: pd.DataFrame) -> pd.DataFrame:
    """Filtre les lignes du dernier run depuis le DataFrame historique."""
    if df_history.empty:
        return df_history
    latest = df_history["run_date"].max()
    return df_history[df_history["run_date"] == latest].copy()


# ---------------------------------------------------------------------------
# Fallback : lecture depuis Parquet (sans PostgreSQL)
# ---------------------------------------------------------------------------

def load_quality_kpis_parquet(parquet_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fallback : calcule les KPIs qualité depuis le Parquet transformé."""
    df = pd.read_parquet(parquet_path)

    df_q = (
        df.groupby("source")
        .agg(
            total=("id", "count"),
            image_valid_count=("image_valid", "sum"),
            text_image_ok_count=("text_image_ok", "sum"),
            has_image_count=("has_image", "sum"),
            avg_text_length=("text_length", "mean"),
            avg_word_count=("word_count", "mean"),
        )
        .reset_index()
    )
    df_q["image_valid_pct"] = (df_q["image_valid_count"] / df_q["total"] * 100).round(1)
    df_q["text_image_ok_pct"] = (df_q["text_image_ok_count"] / df_q["total"] * 100).round(1)
    df_q["has_image_pct"] = (df_q["has_image_count"] / df_q["total"] * 100).round(1)

    df_l = df.groupby(["source", "label"]).size().reset_index(name="count")

    return df_q, df_l
