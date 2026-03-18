"""Tests pour src/extractors/mediaeval.py."""

import pytest
from unittest.mock import patch

from src.extractors.mediaeval import MediaEvalExtractor


def _make_raw(
    text="Tweet content about event",
    image_url="https://pbs.twimg.com/media/img.jpg",
    label="real",
    tweet_id="123456789",
):
    return {
        "tweetId": tweet_id,
        "tweetText": text,
        "imageUrl": image_url,
        "label": label,
        "tweetDate": "2016-05-01",
    }


@pytest.mark.parametrize("label_raw,expected", [
    ("real", "real"),
    ("fake", "fake"),
    ("humor", "fake"),
    ("non-verifiable", "unknown"),
    ("unknown_value", "unknown"),
])
def test_normalize_label_mapping(label_raw, expected, tmp_path):
    extractor = MediaEvalExtractor()
    raw = _make_raw(label=label_raw)
    with patch("src.extractors.mediaeval.download_image", return_value=True), \
         patch("src.extractors.mediaeval.IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)
    assert result is not None
    assert result["label"] == expected


def test_normalize_missing_text_returns_none(tmp_path):
    extractor = MediaEvalExtractor()
    raw = _make_raw(text="")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_missing_image_url_returns_none(tmp_path):
    extractor = MediaEvalExtractor()
    raw = _make_raw(image_url="")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_image_download_fails_returns_none(tmp_path):
    extractor = MediaEvalExtractor()
    raw = _make_raw()
    with patch("src.extractors.mediaeval.download_image", return_value=False), \
         patch("src.extractors.mediaeval.IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)
    assert result is None


def test_normalize_uses_text_field_fallback(tmp_path):
    extractor = MediaEvalExtractor()
    raw = _make_raw(text="")
    raw.pop("tweetText")
    raw["text"] = "Fallback text field"
    with patch("src.extractors.mediaeval.download_image", return_value=True), \
         patch("src.extractors.mediaeval.IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)
    assert result is not None
    assert result["text"] == "Fallback text field"


def test_normalize_tweet_url_constructed(tmp_path):
    extractor = MediaEvalExtractor()
    raw = _make_raw(tweet_id="987654321")
    with patch("src.extractors.mediaeval.download_image", return_value=True), \
         patch("src.extractors.mediaeval.IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)
    assert result is not None
    assert "987654321" in result["url"]


def test_normalize_output_schema(tmp_path):
    extractor = MediaEvalExtractor()
    raw = _make_raw()
    with patch("src.extractors.mediaeval.download_image", return_value=True), \
         patch("src.extractors.mediaeval.IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)

    assert result is not None
    expected_keys = {"id", "source", "title", "text", "image_url", "image_path",
                     "label", "label_confidence", "language", "date", "url", "domain",
                     "extraction_method"}
    assert expected_keys.issubset(result.keys())
    assert result["source"] == "mediaeval"
    assert result["domain"] == "twitter.com"
