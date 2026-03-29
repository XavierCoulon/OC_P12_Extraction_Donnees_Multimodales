"""Tests pour src/extractors/miragenews.py.

Format du dataset HF :
  image : PIL.Image  — image réelle (label=0) ou générée par IA (label=1)
  text  : str        — dépêche textuelle
  label : int        — 0 = real, 1 = fake
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.extractors.miragenews import MiRAGeNewsExtractor
from src.extractors.types import ArticleRecord

_ARTICLE_KEYS = set(ArticleRecord.__annotations__.keys())


def _make_pil_image():
    """Crée une image PIL minimale 10×10 pour les tests."""
    try:
        from PIL import Image
        return Image.new("RGB", (10, 10), color=(128, 0, 0))
    except ImportError:
        return MagicMock()


def _make_raw(text="News article caption text", label=0, split="train"):
    return {
        "_split": split,
        "text": text,
        "image": _make_pil_image(),
        "label": label,
    }


@pytest.mark.parametrize("label_int,expected", [
    (0, "real"),
    (1, "fake"),
    (2, "unknown"),
    (-1, "unknown"),
])
def test_normalize_label_mapping(tmp_path, label_int, expected):
    extractor = MiRAGeNewsExtractor()
    raw = _make_raw(label=label_int)
    with patch("src.extractors.miragenews._IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)
    assert result is not None
    assert result["label"] == expected


def test_normalize_missing_text_returns_none(tmp_path):
    extractor = MiRAGeNewsExtractor()
    raw = _make_raw(text="")
    with patch("src.extractors.miragenews._IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)
    assert result is None


def test_normalize_missing_image_returns_none(tmp_path):
    extractor = MiRAGeNewsExtractor()
    raw = _make_raw()
    raw["image"] = None
    with patch("src.extractors.miragenews._IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)
    assert result is None


def test_normalize_image_saved_to_disk(tmp_path):
    extractor = MiRAGeNewsExtractor()
    raw = _make_raw()
    with patch("src.extractors.miragenews._IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)
    assert result is not None
    assert Path(result["image_path"]).exists()
    assert result["image_path"].endswith(".jpg")


def test_normalize_image_url_empty(tmp_path):
    """MiRAGeNews stocke les images localement, pas via URL."""
    extractor = MiRAGeNewsExtractor()
    raw = _make_raw()
    with patch("src.extractors.miragenews._IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)
    assert result is not None
    assert result["image_url"] == ""


def test_normalize_output_schema(tmp_path):
    extractor = MiRAGeNewsExtractor()
    raw = _make_raw()
    with patch("src.extractors.miragenews._IMAGES_DIR", tmp_path):
        result = extractor.normalize(raw)

    assert result is not None
    assert set(result.keys()) == _ARTICLE_KEYS
    assert result["source"] == "miragenews"
    assert result["language"] == "en"
    assert result["extraction_method"] == "dataset"
    assert result["label"] in {"real", "fake", "unknown"}
