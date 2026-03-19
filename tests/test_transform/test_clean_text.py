"""Tests pour src/transform/steps/clean_text.py"""

import pytest

from src.transform.steps.clean_text import clean_text


def test_strip_html_tags():
    assert clean_text("<p>Bonjour <b>monde</b></p>") == "Bonjour monde"


def test_strip_self_closing_tags():
    assert clean_text("Texte<br/>suite") == "Texte suite"


def test_normalize_multiple_spaces():
    assert clean_text("un   deux   trois") == "un deux trois"


def test_normalize_nbsp():
    assert clean_text("un\xa0deux") == "un deux"


def test_remove_ctrl_chars():
    assert clean_text("texte\x00valide\x1f") == "textevalide"


def test_strip_leading_trailing_spaces():
    assert clean_text("  bonjour  ") == "bonjour"


def test_empty_string():
    assert clean_text("") == ""


def test_none_returns_empty():
    assert clean_text(None) == ""  # type: ignore[arg-type]


def test_html_only_returns_empty_or_spaces():
    result = clean_text("<div></div>")
    assert result == ""


def test_mixed_html_and_text():
    html = '<a href="https://example.com">Cliquez ici</a> pour lire.'
    assert clean_text(html) == "Cliquez ici pour lire."
