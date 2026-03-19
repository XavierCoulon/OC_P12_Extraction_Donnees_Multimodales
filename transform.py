"""CLI du pipeline de transformation.

Usage :
    uv run python transform.py
    uv run python transform.py --source mmfakebench rss
    uv run python transform.py --output data/processed/custom.parquet
"""

import argparse
import sys
from pathlib import Path

from src.transform.pipeline import SOURCES, run_pipeline
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline de transformation des données brutes vers Parquet."
    )
    parser.add_argument(
        "--source",
        nargs="+",
        choices=SOURCES + ["all"],
        default=["all"],
        metavar="SOURCE",
        help=f"Source(s) à traiter : {', '.join(SOURCES)} ou 'all' (défaut: all)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Chemin de sortie du fichier Parquet (défaut: data/processed/transformed.parquet)",
    )
    args = parser.parse_args()

    sources = SOURCES if "all" in args.source else args.source

    logger.info("Démarrage pipeline : sources=%s", sources)
    stats = run_pipeline(sources=sources, output_path=args.output)

    print(f"\n✓ Pipeline terminé")
    print(f"  Lus         : {stats['total_read']}")
    print(f"  Transformés : {stats['total_transformed']}")
    print(f"  Après dédup : {stats['total_after_dedup']}")
    print(f"  Exportés    : {stats['exported']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrompu par l'utilisateur.")
        sys.exit(0)
