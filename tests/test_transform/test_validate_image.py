"""Tests pour src/transform/steps/validate_image.py"""

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
