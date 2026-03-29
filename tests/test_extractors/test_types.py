"""Tests pour src/extractors/types.py — ArticleRecord et ExtractionCounters."""

from src.extractors.types import ArticleRecord, ExtractionCounters

ARTICLE_KEYS = set(ArticleRecord.__annotations__.keys())
COUNTER_KEYS = set(ExtractionCounters.__annotations__.keys())

VALID_LABELS = {"real", "fake", "unknown"}
VALID_CONFIDENCES = {"high", "medium", "low"}
VALID_EXTRACTION_METHODS = {"dataset", "rss"}


def _make_article(**overrides) -> ArticleRecord:
    base: ArticleRecord = {
        "id": "abc123",
        "source": "fakeddit",
        "title": "Test title",
        "text": "Test text",
        "image_url": "https://example.com/img.jpg",
        "image_path": "",
        "label": "real",
        "label_confidence": "high",
        "language": "en",
        "date": "2024-01-01",
        "url": "https://example.com",
        "domain": "example.com",
        "extraction_method": "dataset",
    }
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


# ── ArticleRecord ──────────────────────────────────────────────────────────────

def test_article_record_has_13_keys():
    assert len(ARTICLE_KEYS) == 13


def test_article_record_required_keys():
    expected = {
        "id", "source", "title", "text", "image_url", "image_path",
        "label", "label_confidence", "language", "date", "url",
        "domain", "extraction_method",
    }
    assert ARTICLE_KEYS == expected


def test_article_record_valid_label_values():
    for label in VALID_LABELS:
        record = _make_article(label=label)
        assert record["label"] == label


def test_article_record_valid_confidence_values():
    for conf in VALID_CONFIDENCES:
        record = _make_article(label_confidence=conf)
        assert record["label_confidence"] == conf


def test_article_record_valid_extraction_methods():
    for method in VALID_EXTRACTION_METHODS:
        record = _make_article(extraction_method=method)
        assert record["extraction_method"] == method


def test_article_record_all_fields_are_str():
    record = _make_article()
    for key, value in record.items():
        assert isinstance(value, str), f"Champ '{key}' doit être str, got {type(value)}"


# ── ExtractionCounters ────────────────────────────────────────────────────────

def test_extraction_counters_has_4_keys():
    assert len(COUNTER_KEYS) == 4


def test_extraction_counters_required_keys():
    assert COUNTER_KEYS == {"total", "success", "skipped", "errors"}


def test_extraction_counters_values_are_int():
    counters: ExtractionCounters = {
        "total": 10, "success": 8, "skipped": 1, "errors": 1
    }
    for key, value in counters.items():
        assert isinstance(value, int), f"Compteur '{key}' doit être int"
