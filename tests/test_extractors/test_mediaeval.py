"""Tests pour src/extractors/mediaeval.py.

Format TSV réel (MKLab-ITI/image-verification-corpus) :
  post_id  post_text  user_id  username  image_id  timestamp  label
"""

import pytest

from src.extractors.mediaeval import MediaEvalExtractor


def _make_raw(
    text="Tweet content about event",
    image_id="airstrikes_1",
    label="real",
    post_id="651118294447951872",
):
    return {
        "post_id":   post_id,
        "post_text": text,
        "user_id":   "383409726",
        "username":  "AlexArtAndros",
        "image_id":  image_id,
        "timestamp": "Mon Oct 05 19:34:33 +0000 2015",
        "label":     label,
    }


@pytest.mark.parametrize("label_raw,expected", [
    ("real",           "real"),
    ("fake",           "fake"),
    ("humor",          "fake"),
    ("non-verifiable", "unknown"),
    ("unknown_value",  "unknown"),
])
def test_normalize_label_mapping(label_raw, expected):
    extractor = MediaEvalExtractor()
    raw = _make_raw(label=label_raw)
    result = extractor.normalize(raw)
    assert result is not None
    assert result["label"] == expected


def test_normalize_missing_text_returns_none():
    extractor = MediaEvalExtractor()
    raw = _make_raw(text="")
    result = extractor.normalize(raw)
    assert result is None


def test_normalize_image_id_stored_in_image_path():
    """image_id TSV → image_path (identifiant local, pas une URL)."""
    extractor = MediaEvalExtractor()
    raw = _make_raw(image_id="boston_fake_14")
    result = extractor.normalize(raw)
    assert result is not None
    assert result["image_path"] == "boston_fake_14"
    assert result["image_url"] == ""


def test_normalize_post_url_constructed():
    extractor = MediaEvalExtractor()
    raw = _make_raw(post_id="651118294447951872")
    result = extractor.normalize(raw)
    assert result is not None
    assert "651118294447951872" in result["url"]


def test_normalize_id_uses_post_id():
    extractor = MediaEvalExtractor()
    raw = _make_raw(post_id="999111222")
    result = extractor.normalize(raw)
    assert result is not None
    assert result["id"] == "999111222"


def test_normalize_output_schema():
    extractor = MediaEvalExtractor()
    raw = _make_raw()
    result = extractor.normalize(raw)

    assert result is not None
    expected_keys = {"id", "source", "title", "text", "image_url", "image_path",
                     "label", "label_confidence", "language", "date", "url", "domain",
                     "extraction_method"}
    assert expected_keys.issubset(result.keys())
    assert result["source"] == "mediaeval"
    assert result["domain"] == "twitter.com"
    assert result["image_path"] == "airstrikes_1"
