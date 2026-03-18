"""Tests pour src/extractors/hemt_fake.py."""

import pytest

from src.extractors.hemt_fake import HemtFakeExtractor


def _make_raw(
    text="Article text content",
    image_url="https://example.com/img.jpg",
    label="real",
    entry_id="hemt001",
    language="en",
):
    return {
        "id": entry_id,
        "text": text,
        "title": "Article title",
        "image_url": image_url,
        "label": label,
        "language": language,
        "source_url": "https://example.com/article",
        "date": "2023-01-15",
    }


@pytest.mark.parametrize("label_raw,expected", [
    ("real", "real"),
    ("true", "real"),
    ("1", "real"),
    ("fake", "fake"),
    ("false", "fake"),
    ("0", "fake"),
    ("uncertain", "unknown"),
    ("", "unknown"),
])
def test_normalize_label_mapping(label_raw, expected):
    extractor = HemtFakeExtractor()
    raw = _make_raw(label=label_raw)
    result = extractor.normalize(raw)
    assert result is not None
    assert result["label"] == expected


def test_normalize_missing_text_returns_none():
    extractor = HemtFakeExtractor()
    raw = _make_raw(text="")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_missing_image_url_returns_none():
    extractor = HemtFakeExtractor()
    raw = _make_raw(image_url="")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_invalid_image_url_returns_none():
    extractor = HemtFakeExtractor()
    raw = _make_raw(image_url="not-a-valid-url")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_uses_content_field_as_text():
    extractor = HemtFakeExtractor()
    raw = _make_raw(text="")
    raw["content"] = "Content field text"
    result = extractor.normalize(raw)
    assert result is not None
    assert result["text"] == "Content field text"


def test_normalize_output_schema():
    extractor = HemtFakeExtractor()
    raw = _make_raw()
    result = extractor.normalize(raw)

    assert result is not None
    expected_keys = {"id", "source", "title", "text", "image_url", "image_path",
                     "label", "label_confidence", "language", "date", "url", "domain",
                     "extraction_method"}
    assert expected_keys.issubset(result.keys())
    assert result["source"] == "hemt_fake"
    assert result["extraction_method"] == "dataset"
    assert result["image_path"] == ""
