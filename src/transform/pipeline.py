"""Pipeline de transformation : lit les JSONL bruts et exporte un Parquet consolidé."""

from pathlib import Path

import pandas as pd

from config import PROCESSED_DIR
from src.transform.steps.check_association import check_text_image_association
from src.transform.steps.clean_text import clean_text
from src.transform.steps.deduplicate import deduplicate
from src.transform.steps.enrich import enrich
from src.transform.steps.map_labels import map_label
from src.transform.steps.normalize_date import normalize_date
from src.transform.steps.validate_image import validate_image_fields
from src.utils.io import read_jsonl
from src.utils.logger import get_logger

logger = get_logger(__name__)

SOURCES = ["mmfakebench", "fakeddit", "miragenews", "mediaeval", "rss"]


def _transform_record(record: dict) -> dict:
    """Applique toutes les étapes de transformation à un enregistrement."""
    record = {**record, "text": clean_text(record.get("text", "") or "")}
    record = {**record, "title": clean_text(record.get("title", "") or "")}
    record = {**record, "date": normalize_date(record.get("date", "") or "")}
    record = validate_image_fields(record)
    record = check_text_image_association(record)
    record = map_label(record)
    record = enrich(record)
    return record


def run_pipeline(
    sources: list[str] | None = None,
    output_path: Path | None = None,
    input_dir: Path | None = None,
) -> dict:
    """Exécute le pipeline de transformation complet.

    Étapes :
    1. Lecture des JSONL bruts (une par source)
    2. Transformation de chaque enregistrement
    3. Déduplication inter-sources
    4. Export en Parquet

    Args:
        sources: Liste de sources à traiter (défaut : toutes).
        output_path: Chemin de sortie du fichier Parquet.
        input_dir: Répertoire contenant les JSONL bruts (défaut : PROCESSED_DIR).

    Returns:
        Dictionnaire de stats : total_read, total_transformed, total_after_dedup, exported.
    """
    sources = sources or SOURCES
    output_path = output_path or PROCESSED_DIR / "transformed.parquet"
    read_dir = Path(input_dir) if input_dir else PROCESSED_DIR

    all_records: list[dict] = []
    total_read = 0

    for source in sources:
        jsonl_path = read_dir / f"{source}.jsonl"
        if not jsonl_path.exists():
            logger.warning("Fichier absent, source ignorée : %s", jsonl_path)
            continue

        source_count = 0
        for raw in read_jsonl(jsonl_path):
            total_read += 1
            source_count += 1
            try:
                transformed = _transform_record(raw)
                all_records.append(transformed)
            except Exception as exc:
                logger.error("Erreur transformation enregistrement %s : %s", raw.get("id", "?"), exc)

        logger.info("Source %s : %d enregistrements lus", source, source_count)

    total_transformed = len(all_records)
    logger.info("Total lu : %d | Transformés : %d", total_read, total_transformed)

    # Déduplication
    unique_records = deduplicate(all_records)
    total_after_dedup = len(unique_records)
    removed = total_transformed - total_after_dedup
    if removed:
        logger.info("Déduplication : %d doublons supprimés → %d enregistrements", removed, total_after_dedup)

    # Export Parquet
    df = pd.DataFrame(unique_records)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info("Export Parquet → %s (%d lignes, %d colonnes)", output_path, len(df), len(df.columns))

    return {
        "total_read": total_read,
        "total_transformed": total_transformed,
        "total_after_dedup": total_after_dedup,
        "exported": len(df),
    }
