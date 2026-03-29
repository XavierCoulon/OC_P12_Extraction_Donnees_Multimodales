"""Tests pour src/extractors/rss.py."""

import pytest

from src.extractors.rss import RSSExtractor, _parse_snopes_label, _extract_image_url
from src.extractors.types import ArticleRecord

_ARTICLE_KEYS = set(ArticleRecord.__annotations__.keys())


# --- _parse_snopes_label ---

@pytest.mark.parametrize("title,expected", [
    ("False: Cette photo est un montage", "fake"),
    ("True: Le vaccin est efficace", "real"),
    ("Mostly True: Les chiffres sont approximatifs", "real"),
    ("Mostly False: La statistique est trompeuse", "fake"),
    ("Mixture: Des éléments vrais et faux", "unknown"),
    ("Unproven: Aucune preuve disponible", "unknown"),
    ("Miscaptioned: La photo est détournée", "fake"),
    ("Scam: Arnaque en ligne", "fake"),
    ("Titre quelconque sans préfixe", "unknown"),
    ("", "unknown"),
])
def test_parse_snopes_label(title, expected):
    assert _parse_snopes_label(title) == expected


def test_parse_snopes_label_case_insensitive():
    assert _parse_snopes_label("FALSE: test") == "fake"
    assert _parse_snopes_label("TRUE: test") == "real"


# --- _extract_image_url ---

def test_extract_image_url_from_enclosures():
    entry = {
        "_enclosures": [{"type": "image/jpeg", "href": "https://example.com/img.jpg"}],
        "_media_content": [],
        "_media_thumbnail": [],
    }
    assert _extract_image_url(entry) == "https://example.com/img.jpg"


def test_extract_image_url_from_media_content():
    entry = {
        "_enclosures": [],
        "_media_content": [{"url": "https://example.com/media.jpg"}],
        "_media_thumbnail": [],
    }
    assert _extract_image_url(entry) == "https://example.com/media.jpg"


def test_extract_image_url_from_media_thumbnail():
    entry = {
        "_enclosures": [],
        "_media_content": [],
        "_media_thumbnail": [{"url": "https://example.com/thumb.jpg"}],
    }
    assert _extract_image_url(entry) == "https://example.com/thumb.jpg"


def test_extract_image_url_enclosures_non_image_skipped():
    entry = {
        "_enclosures": [{"type": "audio/mp3", "href": "https://example.com/audio.mp3"}],
        "_media_content": [{"url": "https://example.com/img.jpg"}],
        "_media_thumbnail": [],
    }
    assert _extract_image_url(entry) == "https://example.com/img.jpg"


def test_extract_image_url_empty():
    entry = {"_enclosures": [], "_media_content": [], "_media_thumbnail": []}
    assert _extract_image_url(entry) is None


# --- normalize ---

def _make_raw_rss(
    text="Sample article text",
    image_url="https://example.com/img.jpg",
    label="real",
    title="Test title",
):
    return {
        "summary": text,
        "title": title,
        "link": "https://example.com/article",
        "published": "2024-01-01",
        "_enclosures": [{"type": "image/jpeg", "href": image_url}] if image_url else [],
        "_media_content": [],
        "_media_thumbnail": [],
        "_feed_config": {"label": label, "language": "en"},
    }


def test_rss_normalize_valid_entry():
    extractor = RSSExtractor()
    raw = _make_raw_rss()
    result = extractor.normalize(raw)

    assert result is not None
    assert set(result.keys()) == _ARTICLE_KEYS
    assert result["label"] == "real"
    assert result["text"] == "Sample article text"
    assert result["source"] == "rss"
    assert result["extraction_method"] == "rss"
    assert result["language"] == "en"
    assert result["image_path"] == ""
    assert result["label"] in {"real", "fake", "unknown"}


def test_rss_normalize_snopes_auto_label():
    extractor = RSSExtractor()
    raw = _make_raw_rss(title="False: Ce vaccin est dangereux", label="auto")
    result = extractor.normalize(raw)

    assert result is not None
    assert result["label"] == "fake"


def test_rss_normalize_no_text_returns_none():
    extractor = RSSExtractor()
    raw = _make_raw_rss(text="")
    result = extractor.normalize(raw)
    assert result is None


def test_rss_normalize_no_image_url_returns_none():
    extractor = RSSExtractor()
    raw = _make_raw_rss(image_url="")
    result = extractor.normalize(raw)
    assert result is None


def test_rss_normalize_invalid_image_url_returns_none():
    extractor = RSSExtractor()
    raw = _make_raw_rss(image_url="not-a-valid-url")
    result = extractor.normalize(raw)
    assert result is None
