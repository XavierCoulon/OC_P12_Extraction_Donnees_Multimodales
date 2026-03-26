"""Export des métriques de run Airflow vers PostgreSQL (`pipeline_runs`)."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

from config import PROCESSED_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_PARQUET = PROCESSED_DIR / "transformed.parquet"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id       TEXT,
    run_date     TIMESTAMP,
    task         TEXT,
    source       TEXT,
    total        INTEGER,
    success      INTEGER,
    skipped      INTEGER,
    errors       INTEGER,
    duration_s   FLOAT,
    parquet_rows INTEGER,
    parquet_mb   FLOAT,
    PRIMARY KEY (run_id, task)
);
"""

_UPSERT_SQL = """
INSERT INTO pipeline_runs (
    run_id, run_date, task, source,
    total, success, skipped, errors,
    duration_s, parquet_rows, parquet_mb
) VALUES (
    :run_id, :run_date, :task, :source,
    :total, :success, :skipped, :errors,
    :duration_s, :parquet_rows, :parquet_mb
)
ON CONFLICT (run_id, task) DO NOTHING;
"""


def _parquet_stats(parquet_path: Path) -> tuple[int, float]:
    """Retourne (nb_lignes, taille_mb) du Parquet, ou (0, 0.0) si absent."""
    if not parquet_path.exists():
        return 0, 0.0
    import pandas as pd
    df = pd.read_parquet(parquet_path, columns=["id"])
    size_mb = round(parquet_path.stat().st_size / 1_048_576, 2)
    return len(df), size_mb


def insert_run_metrics(
    run_id: str,
    run_date: datetime,
    tasks_stats: dict[str, dict],
    parquet_path: Path = _DEFAULT_PARQUET,
) -> None:
    """Insère les métriques d'un run dans `pipeline_runs`.

    Args:
        run_id: Identifiant unique du DAG run.
        run_date: Date d'exécution du run.
        tasks_stats: Dict ``{task_id: {total, success, skipped, errors, duration_s}}``.
        parquet_path: Chemin du Parquet final pour récupérer les stats de sortie.
    """
    db_url = os.environ.get("DATA_POSTGRES_URL")
    if not db_url:
        logger.warning("DATA_POSTGRES_URL non définie — métriques non exportées.")
        return

    parquet_rows, parquet_mb = _parquet_stats(parquet_path)
    engine = create_engine(db_url)

    rows = []
    for task, stats in tasks_stats.items():
        # Source = partie après "extract_" pour les tâches d'extraction, sinon task
        source = task.replace("extract_", "") if task.startswith("extract_") else task
        rows.append({
            "run_id": run_id,
            "run_date": run_date,
            "task": task,
            "source": source,
            "total": stats.get("total") or stats.get("total_read") or stats.get("rows_read") or 0,
            "success": stats.get("success") or stats.get("total_transformed") or stats.get("rows_inserted") or 0,
            "skipped": stats.get("skipped", 0),
            "errors": stats.get("errors", 0),
            "duration_s": stats.get("duration_s", 0.0),
            "parquet_rows": parquet_rows,
            "parquet_mb": parquet_mb,
        })

    with engine.begin() as conn:
        conn.execute(text(_CREATE_TABLE_SQL))
        for row in rows:
            conn.execute(text(_UPSERT_SQL), row)

    logger.info("pipeline_runs : %d lignes insérées pour le run %s.", len(rows), run_id)
