"""Tests pour src/transform/steps/validate_image.py"""

from unittest.mock import patch

import pytest

from src.transform.steps.validate_image import validate_image_fields


def test_valid_image_url_sets_true():
    record = {"image_url": "https://example.com/photo.jpg", "image_path": ""}
    result = validate_image_fields(record)
    assert result["image_valid"] is True


def test_invalid_image_url_sets_false():
    record = {"image_url": "not-a-url", "image_path": ""}
    result = validate_image_fields(record)
    assert result["image_valid"] is False


def test_empty_url_sets_false():
    record = {"image_url": "", "image_path": ""}
    result = validate_image_fields(record)
    assert result["image_valid"] is False


def test_image_path_nonempty_sets_true():
    record = {"image_url": "", "image_path": "images/abc.jpg"}
    result = validate_image_fields(record)
    assert result["image_valid"] is True


def test_both_empty_sets_false():
    record = {"image_url": "", "image_path": ""}
    result = validate_image_fields(record)
    assert result["image_valid"] is False


def test_original_fields_preserved():
    record = {"image_url": "https://example.com/img.png", "image_path": "", "text": "hello"}
    result = validate_image_fields(record)
    assert result["text"] == "hello"
    assert result["image_url"] == "https://example.com/img.png"


def test_miragenews_valid_image_path(tmp_path, fake_image_bytes):
    """image_path miragenews : appelle validate_image() sur le fichier local."""
    img = tmp_path / "img.jpg"
    img.write_bytes(fake_image_bytes)
    record = {"image_url": "", "image_path": str(img), "source": "miragenews"}
    result = validate_image_fields(record)
    assert result["image_valid"] is True


def test_miragenews_invalid_image_path(tmp_path):
    """image_path miragenews : fichier corrompu → False."""
    img = tmp_path / "bad.jpg"
    img.write_bytes(b"not an image")
    record = {"image_url": "", "image_path": str(img), "source": "miragenews"}
    result = validate_image_fields(record)
    assert result["image_valid"] is False


def test_mmfakebench_path_trusted():
    """image_path mmfakebench (ref interne HF) : non vide → True sans vérif fichier."""
    record = {"image_url": "", "image_path": "images/foo.jpg", "source": "mmfakebench"}
    result = validate_image_fields(record)
    assert result["image_valid"] is True


@patch("src.transform.steps.validate_image.IMAGE_CHECK_ACCESSIBLE", True)
@patch("src.transform.steps.validate_image.check_image_accessible", return_value=True)
def test_accessible_check_called_when_enabled(mock_check):
    record = {"image_url": "https://example.com/photo.jpg", "image_path": ""}
    result = validate_image_fields(record)
    mock_check.assert_called_once_with("https://example.com/photo.jpg")
    assert result["image_valid"] is True


@patch("src.transform.steps.validate_image.IMAGE_CHECK_ACCESSIBLE", True)
@patch("src.transform.steps.validate_image.check_image_accessible", return_value=False)
def test_accessible_check_false_when_unreachable(mock_check):
    record = {"image_url": "https://example.com/photo.jpg", "image_path": ""}
    result = validate_image_fields(record)
    assert result["image_valid"] is False


@patch("src.transform.steps.validate_image.IMAGE_CHECK_ACCESSIBLE", False)
@patch("src.transform.steps.validate_image.check_image_accessible")
def test_accessible_check_not_called_when_disabled(mock_check):
    record = {"image_url": "https://example.com/photo.jpg", "image_path": ""}
    validate_image_fields(record)
    mock_check.assert_not_called()
