"""DAG Airflow — ETL multimodal (étape 4).

Orchestration :
    extract_rss ────────┐
    extract_fakeddit ───┤
    extract_mmfakebench ┼──► transform_data ──► load_to_postgres
    extract_miragenews ─┤
    extract_mediaeval ──┘

Chaque tâche d'extraction appelle directement l'extracteur correspondant
(PythonOperator simple, pas de BashOperator). La tâche de transformation
réutilise run_pipeline() de l'étape 3.
"""
from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

# ---------------------------------------------------------------------------
# Callables des tâches
# ---------------------------------------------------------------------------

def _extract_source(source_name: str, **context) -> dict:
    """Extrait une source et retourne les stats via XCom."""
    import sys
    sys.path.insert(0, "/opt/airflow")

    from main import EXTRACTORS
    import importlib

    from config import DEFAULT_LIMITS
    from pathlib import Path

    output_path = Path("/opt/airflow/data/processed") / f"{source_name}.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    module_path, class_name = EXTRACTORS[source_name]
    module = importlib.import_module(module_path)
    extractor_cls = getattr(module, class_name)
    extractor = extractor_cls()
    # Limites spécifiques au DAG : on plafonne les sources volumineuses
    # pour garder un run ETL < 10 min (l'extraction complète se fait via make extract)
    DAG_LIMITS: dict[str, int | None] = {
        "miragenews": 500,   # ~15 000 entrées → trop long via Docker volume
        "fakeddit":   2_000,
    }
    default_limit = DEFAULT_LIMITS.get(source_name)
    limit = DAG_LIMITS.get(source_name, default_limit)
    stats = extractor.run(output_path=output_path, limit=limit)
    return stats


def _transform(**context) -> dict:
    """Transforme tous les JSONL extraits → Parquet."""
    import sys
    sys.path.insert(0, "/opt/airflow")

    from src.transform.pipeline import run_pipeline
    return run_pipeline()


def _load(**context) -> dict:
    """Charge le Parquet transformé dans PostgreSQL."""
    import sys
    sys.path.insert(0, "/opt/airflow")

    from src.load.postgres_loader import load_parquet_to_postgres
    return load_parquet_to_postgres()


# ---------------------------------------------------------------------------
# DAG
# ---------------------------------------------------------------------------

with DAG(
    dag_id="etl_multimodal",
    description="ETL multimodal : extraction → transformation → chargement PostgreSQL",
    schedule=None,           # Déclenchement manuel depuis l'UI
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["etl", "multimodal"],
    default_args={"retries": 1},
) as dag:

    sources = ["rss", "fakeddit", "mmfakebench", "miragenews", "mediaeval"]

    extract_tasks = [
        PythonOperator(
            task_id=f"extract_{source}",
            python_callable=_extract_source,
            op_kwargs={"source_name": source},
        )
        for source in sources
    ]

    transform_task = PythonOperator(
        task_id="transform_data",
        python_callable=_transform,
    )

    load_task = PythonOperator(
        task_id="load_to_postgres",
        python_callable=_load,
    )

    extract_tasks >> transform_task >> load_task
