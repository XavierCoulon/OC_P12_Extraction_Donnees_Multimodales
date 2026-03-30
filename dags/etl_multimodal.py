"""DAG Airflow — ETL multimodal (étape 4 + 5).

Orchestration :
    extract_rss ────────┐
    extract_fakeddit ───┤
    extract_mmfakebench ┼──► transform_data ──► load_to_postgres ──► export_metrics
    extract_miragenews ─┤
    extract_mediaeval ──┘

Chaque tâche d'extraction appelle directement l'extracteur correspondant
(PythonOperator simple, pas de BashOperator). La tâche de transformation
réutilise run_pipeline() de l'étape 3. La tâche export_metrics insère les
statistiques de run dans la table pipeline_runs (étape 5).
"""

from __future__ import annotations

import os
import time
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
        "miragenews": 500,  # ~15 000 entrées → trop long via Docker volume
        "fakeddit": 2_000,
    }
    default_limit = DEFAULT_LIMITS.get(source_name)
    limit = DAG_LIMITS.get(source_name, default_limit)

    start = time.perf_counter()
    stats = extractor.run(output_path=output_path, limit=limit)
    stats["duration_s"] = round(time.perf_counter() - start, 2)
    return stats


def _transform(**context) -> dict:
    """Transforme tous les JSONL extraits → Parquet."""
    import sys

    sys.path.insert(0, "/opt/airflow")

    from src.transform.pipeline import run_pipeline

    start = time.perf_counter()
    stats = run_pipeline()
    stats["duration_s"] = round(time.perf_counter() - start, 2)
    return stats


def _load(**context) -> dict:
    """Charge le Parquet transformé dans PostgreSQL."""
    import sys

    sys.path.insert(0, "/opt/airflow")

    from src.load.postgres_loader import load_parquet_to_postgres

    start = time.perf_counter()
    stats = load_parquet_to_postgres()
    stats["duration_s"] = round(time.perf_counter() - start, 2)
    return stats


def _export_metrics(**context) -> None:
    """Collecte les XCom de toutes les tâches et insère dans pipeline_runs."""
    import sys

    sys.path.insert(0, "/opt/airflow")

    from src.metrics.exporter import insert_run_metrics

    ti = context["task_instance"]
    dag_run = context["dag_run"]

    sources = ["rss", "fakeddit", "mmfakebench", "miragenews", "mediaeval"]
    tasks_stats: dict[str, dict] = {}

    for source in sources:
        task_id = f"extract_{source}"
        xcom = ti.xcom_pull(task_ids=task_id)
        if xcom:
            tasks_stats[task_id] = xcom

    for task_id in ("transform_data", "load_to_postgres"):
        xcom = ti.xcom_pull(task_ids=task_id)
        if xcom:
            tasks_stats[task_id] = xcom

    insert_run_metrics(
        run_id=dag_run.run_id,
        run_date=dag_run.execution_date,
        tasks_stats=tasks_stats,
    )


# ---------------------------------------------------------------------------
# DAG
# ---------------------------------------------------------------------------

with DAG(
    dag_id="etl_multimodal",
    description="ETL multimodal : extraction → transformation → chargement PostgreSQL → métriques",
    schedule=None,  # Déclenchement manuel depuis l'UI
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["etl", "multimodal"],
    default_args={
        "retries": 1,
        "retry_delay": 30,  # 30s pour la démo
        "email": [os.environ.get("AIRFLOW_ALERT_EMAIL", "")],
        "email_on_failure": True,
        "email_on_retry": False,
    },
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

    export_metrics_task = PythonOperator(
        task_id="export_metrics",
        python_callable=_export_metrics,
    )

    extract_tasks >> transform_task >> load_task >> export_metrics_task
