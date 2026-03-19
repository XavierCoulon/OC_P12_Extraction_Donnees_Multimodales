"""Tests pour src/transform/steps/deduplicate.py"""

from src.transform.steps.deduplicate import deduplicate


def _make(source: str, text: str, **kwargs) -> dict:
    return {"source": source, "text": text, **kwargs}


def test_no_duplicates_unchanged():
    records = [_make("rss", "article A"), _make("rss", "article B")]
    result = deduplicate(records)
    assert len(result) == 2


def test_exact_duplicate_removed():
    records = [_make("rss", "article A", id="1"), _make("rss", "article A", id="2")]
    result = deduplicate(records)
    assert len(result) == 1
    assert result[0]["id"] == "1"  # première occurrence conservée


def test_same_text_different_source_kept():
    records = [_make("rss", "article A"), _make("fakeddit", "article A")]
    result = deduplicate(records)
    assert len(result) == 2


def test_empty_list():
    assert deduplicate([]) == []


def test_single_record():
    records = [_make("rss", "unique")]
    assert deduplicate(records) == records


def test_order_preserved():
    records = [_make("rss", f"article {i}") for i in range(5)]
    result = deduplicate(records)
    assert [r["text"] for r in result] == [f"article {i}" for i in range(5)]


def test_duplicate_at_end_removed():
    records = [
        _make("rss", "A"),
        _make("rss", "B"),
        _make("rss", "A"),  # doublon
    ]
    result = deduplicate(records)
    assert len(result) == 2
    assert result[0]["text"] == "A"
    assert result[1]["text"] == "B"
