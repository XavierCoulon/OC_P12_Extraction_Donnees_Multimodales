"""Tests pour src/extractors/fakeddit.py."""

import pytest

from src.extractors.fakeddit import FakedditExtractor


def _make_raw(
    title="Fake news headline",
    image_url="https://i.redd.it/abc.jpg",
    label_2way=0,
    label_6way="fake",
    entry_id="post123",
):
    return {
        "id": entry_id,
        "title": title,
        "image_url": image_url,
        "2_way_label": label_2way,
        "6_way_label": label_6way,
        "permalink": "/r/test/comments/abc",
        "created_utc": 1700000000.0,
        "domain": "i.redd.it",
    }


def test_normalize_label_0_is_fake():
    extractor = FakedditExtractor()
    raw = _make_raw(label_2way=0)
    result = extractor.normalize(raw)
    assert result is not None
    assert result["label"] == "fake"


def test_normalize_label_1_is_real():
    extractor = FakedditExtractor()
    raw = _make_raw(label_2way=1, label_6way="true")
    result = extractor.normalize(raw)
    assert result is not None
    assert result["label"] == "real"


def test_normalize_non_verifiable_returns_none():
    extractor = FakedditExtractor()
    raw = _make_raw(label_6way="non-verifiable")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_empty_image_url_returns_none():
    extractor = FakedditExtractor()
    raw = _make_raw(image_url="")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_nan_image_url_returns_none():
    extractor = FakedditExtractor()
    raw = _make_raw()
    raw["image_url"] = float("nan")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_empty_title_returns_none():
    extractor = FakedditExtractor()
    raw = _make_raw(title="")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_invalid_image_url_returns_none():
    extractor = FakedditExtractor()
    raw = _make_raw(image_url="not-a-url")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_output_schema():
    extractor = FakedditExtractor()
    raw = _make_raw()
    result = extractor.normalize(raw)

    assert result is not None
    expected_keys = {"id", "source", "title", "text", "image_url", "image_path",
                     "label", "label_confidence", "language", "date", "url", "domain",
                     "extraction_method"}
    assert expected_keys.issubset(result.keys())
    assert result["source"] == "fakeddit"
    assert result["extraction_method"] == "dataset"
    assert result["language"] == "en"
    assert result["label_confidence"] == "high"
    assert result["image_path"] == ""
