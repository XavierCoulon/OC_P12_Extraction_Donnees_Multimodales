"""Point d'entrée CLI — extraction automatisée de données multimodales.

Usage :
    python main.py --source rss --limit 10 --output data/processed/
    python main.py --source fakeddit --limit 5000 --output data/processed/
    python main.py --source all --output data/processed/
"""

import argparse
import sys
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger("main")

EXTRACTORS = {
    "rss":          ("src.extractors.rss",         "RSSExtractor"),
    "fakeddit":     ("src.extractors.fakeddit",    "FakedditExtractor"),
    "mmfakebench":  ("src.extractors.mmfakebench", "MMFakeBenchExtractor"),
    "hemt_fake":    ("src.extractors.hemt_fake",   "HemtFakeExtractor"),
    "mediaeval":    ("src.extractors.mediaeval",   "MediaEvalExtractor"),
}


def _load_extractor(name: str):
    """Importe et instancie dynamiquement un extracteur par son nom."""
    module_path, class_name = EXTRACTORS[name]
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)()


def _run_source(name: str, output_dir: Path, limit: int | None) -> dict:
    extractor = _load_extractor(name)
    output_path = output_dir / f"{name}.jsonl"
    return extractor.run(output_path=output_path, limit=limit)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extraction de données multimodales (texte + image) pour fake news detection.",
    )
    parser.add_argument(
        "--source",
        choices=[*EXTRACTORS.keys(), "all"],
        required=True,
        help="Source à extraire. 'all' lance tous les extracteurs.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Nombre maximum d'entrées valides à extraire par source.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed"),
        help="Dossier de sortie pour les fichiers .jsonl (défaut: data/processed/).",
    )

    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    sources = list(EXTRACTORS.keys()) if args.source == "all" else [args.source]
    total_counters = {"total": 0, "success": 0, "skipped": 0, "errors": 0}

    for source in sources:
        logger.info("=== Source : %s ===", source)
        try:
            counters = _run_source(source, args.output, args.limit)
            for k in total_counters:
                total_counters[k] += counters.get(k, 0)
        except Exception as e:
            logger.error("Erreur critique sur la source '%s' : %s", source, e)

    if len(sources) > 1:
        logger.info(
            "=== Bilan global === total=%d success=%d skipped=%d errors=%d",
            total_counters["total"],
            total_counters["success"],
            total_counters["skipped"],
            total_counters["errors"],
        )


if __name__ == "__main__":
    main()
