"""Vérification du fichier Parquet produit par le pipeline de transformation.

Usage :
    uv run python verify.py
    uv run python verify.py --input data/processed/transformed.parquet
"""

import argparse
from pathlib import Path

import pandas as pd

from config import PROCESSED_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Rapport de vérification du Parquet transformé.")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DIR / "transformed.parquet",
        help="Chemin du fichier Parquet à vérifier",
    )
    args = parser.parse_args()

    path: Path = args.input
    if not path.exists():
        print(f"✗ Fichier introuvable : {path}")
        print("  Exécutez d'abord : make transform")
        return

    df = pd.read_parquet(path)

    print(f"\n{'='*60}")
    print(f"  Rapport — {path.name}")
    print(f"{'='*60}")

    # Shape
    print(f"\n📊 Dimensions")
    print(f"   {len(df):,} lignes × {len(df.columns)} colonnes")
    print(f"   Colonnes : {', '.join(df.columns.tolist())}")

    # Répartition labels
    if "label" in df.columns:
        print(f"\n🏷️  Labels (label)")
        counts = df["label"].value_counts()
        for label, count in counts.items():
            pct = count / len(df) * 100
            print(f"   {label:<10} : {count:>6,}  ({pct:.1f}%)")

    # Répartition sources
    if "source" in df.columns:
        print(f"\n🗂️  Sources")
        counts = df["source"].value_counts()
        for source, count in counts.items():
            pct = count / len(df) * 100
            print(f"   {source:<15} : {count:>6,}  ({pct:.1f}%)")

    # Colonnes dérivées
    print(f"\n🔍 Colonnes dérivées")
    for col in ("has_image", "image_valid", "text_image_ok"):
        if col in df.columns:
            n = df[col].sum()
            pct = n / len(df) * 100
            print(f"   {col:<20} : {n:>6,} / {len(df):,}  ({pct:.1f}%)")

    # Statistiques texte
    if "text_length" in df.columns:
        print(f"\n📝 Longueur du texte (text_length)")
        stats = df["text_length"].agg(["min", "mean", "max"])
        print(f"   min={stats['min']:.0f}  moy={stats['mean']:.0f}  max={stats['max']:.0f}")

    # Aperçu
    print(f"\n👁️  Aperçu (3 premières lignes)")
    preview_cols = [c for c in ("id", "source", "label", "label_int", "text_length", "has_image") if c in df.columns]
    print(df[preview_cols].head(3).to_string(index=False))

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
