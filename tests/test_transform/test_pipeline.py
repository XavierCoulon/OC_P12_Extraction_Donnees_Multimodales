"""Tests d'intégration pour src/transform/pipeline.py"""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.transform.pipeline import run_pipeline


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


@pytest.fixture()
def processed_dir(tmp_path):
    """Répertoire temporaire simulant data/processed/."""
    return tmp_path / "processed"


@pytest.fixture()
def sample_records():
    return [
        {
            "id": "1",
            "source": "rss",
            "text": "<p>Article sur les fake news</p>",
            "title": "Titre A",
            "image_url": "https://example.com/img.jpg",
            "image_path": "",
            "label": "real",
            "label_confidence": "medium",
            "language": "fr",
            "date": "Wed, 18 Mar 2026 09:10:08 +0100",
            "url": "https://example.com/a",
            "domain": "example.com",
            "extraction_method": "rss",
        },
        {
            "id": "2",
            "source": "rss",
            "text": "Fausse information propagée",
            "title": "Titre B",
            "image_url": "",
            "image_path": "",
            "label": "fake",
            "label_confidence": "high",
            "language": "fr",
            "date": "2026-03-17",
            "url": "https://example.com/b",
            "domain": "example.com",
            "extraction_method": "rss",
        },
    ]


def test_pipeline_produces_parquet(tmp_path, processed_dir, sample_records):
    _write_jsonl(processed_dir / "rss.jsonl", sample_records)
    output = tmp_path / "out.parquet"

    stats = run_pipeline(sources=["rss"], output_path=output, input_dir=processed_dir)

    assert output.exists()
    df = pd.read_parquet(output)
    assert len(df) == 2
    assert stats["exported"] == 2


def test_pipeline_stats_correct(tmp_path, processed_dir, sample_records):
    _write_jsonl(processed_dir / "rss.jsonl", sample_records)
    output = tmp_path / "out.parquet"

    stats = run_pipeline(sources=["rss"], output_path=output, input_dir=processed_dir)

    assert stats["total_read"] == 2
    assert stats["total_transformed"] == 2
    assert stats["total_after_dedup"] == 2


def test_pipeline_deduplication(tmp_path, processed_dir, sample_records):
    # Doublon : même source + même texte
    records = sample_records + [sample_records[0]]
    _write_jsonl(processed_dir / "rss.jsonl", records)
    output = tmp_path / "out.parquet"

    stats = run_pipeline(sources=["rss"], output_path=output, input_dir=processed_dir)

    assert stats["total_after_dedup"] == 2
    assert stats["exported"] == 2


def test_pipeline_cleans_html(tmp_path, processed_dir, sample_records):
    _write_jsonl(processed_dir / "rss.jsonl", sample_records)
    output = tmp_path / "out.parquet"

    run_pipeline(sources=["rss"], output_path=output, input_dir=processed_dir)

    df = pd.read_parquet(output)
    first_text = df[df["id"] == "1"]["text"].iloc[0]
    assert "<p>" not in first_text
    assert "Article sur les fake news" in first_text


def test_pipeline_label_int(tmp_path, processed_dir, sample_records):
    _write_jsonl(processed_dir / "rss.jsonl", sample_records)
    output = tmp_path / "out.parquet"

    run_pipeline(sources=["rss"], output_path=output, input_dir=processed_dir)

    df = pd.read_parquet(output)
    assert df[df["label"] == "real"]["label_int"].iloc[0] == 1
    assert df[df["label"] == "fake"]["label_int"].iloc[0] == 0


def test_pipeline_missing_source_skipped(tmp_path, processed_dir):
    output = tmp_path / "out.parquet"
    # Aucun fichier dans processed_dir

    stats = run_pipeline(sources=["rss"], output_path=output, input_dir=processed_dir)

    assert stats["total_read"] == 0
    assert stats["exported"] == 0
