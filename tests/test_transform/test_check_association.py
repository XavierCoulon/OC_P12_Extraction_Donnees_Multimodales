"""Tests pour src/transform/steps/check_association.py"""

from src.transform.steps.check_association import check_text_image_association


def test_text_and_image_both_present():
    record = {"text": "Un article.", "image_valid": True}
    result = check_text_image_association(record)
    assert result["text_image_ok"] is True


def test_text_present_image_absent():
    record = {"text": "Un article.", "image_valid": False}
    result = check_text_image_association(record)
    assert result["text_image_ok"] is False


def test_text_absent_image_present():
    record = {"text": "", "image_valid": True}
    result = check_text_image_association(record)
    assert result["text_image_ok"] is False


def test_both_absent():
    record = {"text": "", "image_valid": False}
    result = check_text_image_association(record)
    assert result["text_image_ok"] is False


def test_text_whitespace_only():
    record = {"text": "   ", "image_valid": True}
    result = check_text_image_association(record)
    assert result["text_image_ok"] is False


def test_original_fields_preserved():
    record = {"text": "hello", "image_valid": True, "label": "real"}
    result = check_text_image_association(record)
    assert result["label"] == "real"
