"""Tests pour src/extractors/base.py — BaseExtractor.run()."""

import pytest
from pathlib import Path
from typing import Iterator

from src.extractors.base import BaseExtractor
from src.extractors.types import ArticleRecord, ExtractionCounters
from src.utils.io import read_jsonl


class _FakeExtractor(BaseExtractor):
    """Extracteur minimal pour tester BaseExtractor.run()."""

    source_name = "test"

    def __init__(self, raw_items: list[dict], normalize_fn=None):
        super().__init__()
        self._raw_items = raw_items
        self._normalize_fn = normalize_fn

    def extract(self) -> Iterator[dict]:
        yield from self._raw_items

    def normalize(self, raw: dict) -> ArticleRecord | None:
        if self._normalize_fn is not None:
            return self._normalize_fn(raw)
        return raw  # type: ignore[return-value]


def _valid_record(i: int) -> ArticleRecord:
    return {
        "id": str(i),
        "source": "test",
        "title": f"title {i}",
        "text": f"text {i}",
        "image_url": "",
        "image_path": "",
        "label": "real",
        "label_confidence": "high",
        "language": "en",
        "date": "",
        "url": "",
        "domain": "",
        "extraction_method": "dataset",
    }


def test_run_all_valid(tmp_path):
    items = [_valid_record(i) for i in range(3)]
    extractor = _FakeExtractor(items)
    output = tmp_path / "out.jsonl"

    counters = extractor.run(output)

    assert counters["total"] == 3
    assert counters["success"] == 3
    assert counters["skipped"] == 0
    assert counters["errors"] == 0
    assert list(read_jsonl(output)) == items


def test_run_normalize_returns_none_increments_skipped(tmp_path):
    def normalize_fn(raw):
        return None if raw.get("id") == "1" else raw

    items = [_valid_record(0), _valid_record(1), _valid_record(2)]
    extractor = _FakeExtractor(items, normalize_fn=normalize_fn)
    output = tmp_path / "out.jsonl"

    counters = extractor.run(output)

    assert counters["total"] == 3
    assert counters["success"] == 2
    assert counters["skipped"] == 1
    assert counters["errors"] == 0


def test_run_normalize_raises_increments_errors(tmp_path):
    def normalize_fn(raw):
        if raw.get("id") == "1":
            raise ValueError("Erreur simulée")
        return raw

    items = [_valid_record(0), _valid_record(1), _valid_record(2)]
    extractor = _FakeExtractor(items, normalize_fn=normalize_fn)
    output = tmp_path / "out.jsonl"

    counters = extractor.run(output)

    assert counters["total"] == 3
    assert counters["success"] == 2
    assert counters["errors"] == 1
    # Pas de crash
    result = list(read_jsonl(output))
    assert len(result) == 2


def test_run_with_limit(tmp_path):
    items = [_valid_record(i) for i in range(10)]
    extractor = _FakeExtractor(items)
    output = tmp_path / "out.jsonl"

    counters = extractor.run(output, limit=3)

    assert counters["success"] == 3
    assert len(list(read_jsonl(output))) == 3


def test_run_limit_counts_successes_only(tmp_path):
    """limit=2 doit produire 2 succès, même si des entrées sont skippées."""
    def normalize_fn(raw):
        # Skip les entrées impaires
        return None if int(raw["id"]) % 2 != 0 else raw

    items = [_valid_record(i) for i in range(10)]
    extractor = _FakeExtractor(items, normalize_fn=normalize_fn)
    output = tmp_path / "out.jsonl"

    counters = extractor.run(output, limit=2)

    assert counters["success"] == 2


def test_run_creates_output_file(tmp_path):
    extractor = _FakeExtractor([])
    output = tmp_path / "subdir" / "out.jsonl"
    extractor.run(output)
    assert output.exists()


def test_run_returns_dict_with_all_keys(tmp_path):
    extractor = _FakeExtractor([])
    output = tmp_path / "out.jsonl"
    counters = extractor.run(output)
    assert set(counters.keys()) == set(ExtractionCounters.__annotations__.keys())


def test_run_counters_are_int(tmp_path):
    items = [_valid_record(i) for i in range(3)]
    extractor = _FakeExtractor(items)
    counters = extractor.run(tmp_path / "out.jsonl")
    for key, value in counters.items():
        assert isinstance(value, int), f"compteur '{key}' doit être int"
