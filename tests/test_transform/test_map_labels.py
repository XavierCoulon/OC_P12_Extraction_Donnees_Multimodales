"""Tests pour src/transform/steps/map_labels.py"""

from src.transform.steps.map_labels import map_label


def test_real_maps_to_1():
    assert map_label({"label": "real"})["label_int"] == 1


def test_fake_maps_to_0():
    assert map_label({"label": "fake"})["label_int"] == 0


def test_unknown_maps_to_minus1():
    assert map_label({"label": "unknown"})["label_int"] == -1


def test_unexpected_label_maps_to_minus1():
    assert map_label({"label": "suspicious"})["label_int"] == -1


def test_empty_label_maps_to_minus1():
    assert map_label({"label": ""})["label_int"] == -1


def test_missing_label_maps_to_minus1():
    assert map_label({})["label_int"] == -1


def test_case_insensitive():
    assert map_label({"label": "Real"})["label_int"] == 1
    assert map_label({"label": "FAKE"})["label_int"] == 0


def test_original_fields_preserved():
    record = {"label": "real", "text": "article"}
    result = map_label(record)
    assert result["label"] == "real"
    assert result["text"] == "article"
