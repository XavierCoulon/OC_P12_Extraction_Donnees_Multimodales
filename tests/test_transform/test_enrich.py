"""Tests pour src/transform/steps/enrich.py"""

from src.transform.steps.enrich import enrich


def test_text_length():
    record = {"text": "bonjour monde", "image_valid": False}
    assert enrich(record)["text_length"] == len("bonjour monde")


def test_word_count():
    record = {"text": "un deux trois", "image_valid": False}
    assert enrich(record)["word_count"] == 3


def test_word_count_empty_text():
    record = {"text": "", "image_valid": False}
    assert enrich(record)["word_count"] == 0


def test_has_image_true():
    record = {"text": "texte", "image_valid": True}
    assert enrich(record)["has_image"] is True


def test_has_image_false():
    record = {"text": "texte", "image_valid": False}
    assert enrich(record)["has_image"] is False


def test_missing_image_valid_defaults_false():
    record = {"text": "texte"}
    assert enrich(record)["has_image"] is False


def test_original_fields_preserved():
    record = {"text": "hello", "image_valid": True, "label": "real"}
    result = enrich(record)
    assert result["label"] == "real"
    assert result["text"] == "hello"
