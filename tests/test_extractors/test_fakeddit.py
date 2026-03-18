"""Tests pour src/extractors/fakeddit.py."""

import pytest
from unittest.mock import patch
import math

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


def test_normalize_label_0_is_fake(tmp_path):
    extractor = FakedditExtractor()
    raw = _make_raw(label_2way=0)
    with patch("src.extractors.fakeddit.download_image", return_value=True), \
         patch("src.extractors.fakeddit.IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)
    assert result is not None
    assert result["label"] == "fake"


def test_normalize_label_1_is_real(tmp_path):
    extractor = FakedditExtractor()
    raw = _make_raw(label_2way=1, label_6way="true")
    with patch("src.extractors.fakeddit.download_image", return_value=True), \
         patch("src.extractors.fakeddit.IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)
    assert result is not None
    assert result["label"] == "real"


def test_normalize_non_verifiable_returns_none(tmp_path):
    extractor = FakedditExtractor()
    raw = _make_raw(label_6way="non-verifiable")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_empty_image_url_returns_none(tmp_path):
    extractor = FakedditExtractor()
    raw = _make_raw(image_url="")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_nan_image_url_returns_none(tmp_path):
    extractor = FakedditExtractor()
    raw = _make_raw()
    raw["image_url"] = float("nan")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_empty_title_returns_none(tmp_path):
    extractor = FakedditExtractor()
    raw = _make_raw(title="")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_image_download_fails_returns_none(tmp_path):
    extractor = FakedditExtractor()
    raw = _make_raw()
    with patch("src.extractors.fakeddit.download_image", return_value=False), \
         patch("src.extractors.fakeddit.IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)
    assert result is None


def test_normalize_output_schema(tmp_path):
    extractor = FakedditExtractor()
    raw = _make_raw()
    with patch("src.extractors.fakeddit.download_image", return_value=True), \
         patch("src.extractors.fakeddit.IMAGES_DIR", tmp_path):
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
