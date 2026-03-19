"""Nettoyage du champ texte : suppression HTML, normalisation espaces, caractères ctrl."""

import re

# Balises HTML (y compris auto-fermantes)
_RE_HTML = re.compile(r"<[^>]+>", re.DOTALL)
# Caractères de contrôle (hors \n\r\t)
_RE_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# Espaces multiples (incluant non-breaking space \xa0)
_RE_SPACES = re.compile(r"[ \t\xa0]+")


def clean_text(text: str) -> str:
    """Nettoie un texte brut : strip HTML, normalise les espaces, supprime les ctrl chars.

    Args:
        text: Texte brut potentiellement contenant du HTML.

    Returns:
        Texte nettoyé, ou chaîne vide si l'entrée est invalide.
    """
    if not text or not isinstance(text, str):
        return ""
    result = _RE_HTML.sub(" ", text)
    result = _RE_CTRL.sub("", result)
    result = _RE_SPACES.sub(" ", result)
    return result.strip()
