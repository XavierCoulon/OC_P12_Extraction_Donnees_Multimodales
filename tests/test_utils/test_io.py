"""Tests pour src/utils/io.py."""

import pytest
from src.utils.io import write_jsonl, read_jsonl


def test_write_then_read_roundtrip(tmp_path):
    records = [
        {"id": "1", "text": "hello", "label": "real"},
        {"id": "2", "text": "world", "label": "fake"},
    ]
    path = tmp_path / "out.jsonl"
    written = write_jsonl(records, path)

    assert written == 2
    result = list(read_jsonl(path))
    assert result == records


def test_write_creates_parent_dirs(tmp_path):
    path = tmp_path / "subdir" / "nested" / "out.jsonl"
    write_jsonl([{"id": "1"}], path)
    assert path.exists()


def test_write_returns_count(tmp_path):
    path = tmp_path / "out.jsonl"
    assert write_jsonl([], path) == 0
    assert write_jsonl([{"a": 1}, {"b": 2}, {"c": 3}], path) == 3


def test_utf8_preserved(tmp_path):
    records = [{"text": "café résumé 日本語 🎉"}]
    path = tmp_path / "out.jsonl"
    write_jsonl(records, path)
    result = list(read_jsonl(path))
    assert result[0]["text"] == "café résumé 日本語 🎉"


def test_read_skips_blank_lines(tmp_path):
    path = tmp_path / "out.jsonl"
    path.write_text('{"id":"1"}\n\n{"id":"2"}\n', encoding="utf-8")
    result = list(read_jsonl(path))
    assert len(result) == 2
