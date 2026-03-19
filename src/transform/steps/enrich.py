"""Enrichissement des enregistrements avec des colonnes dérivées."""


def enrich(record: dict) -> dict:
    """Ajoute des colonnes dérivées utiles pour le ML et le NLP.

    Colonnes ajoutées :
    - `text_length` : nombre de caractères du texte nettoyé
    - `word_count`  : nombre de mots (split sur espaces)
    - `has_image`   : True si l'enregistrement dispose d'une image valide

    Dépend de `image_valid` calculé par validate_image_fields.

    Args:
        record: Enregistrement unifié (doit contenir `text` et `image_valid`).

    Returns:
        Enregistrement enrichi des trois colonnes dérivées.
    """
    text: str = record.get("text") or ""
    text_length = len(text)
    word_count = len(text.split()) if text.strip() else 0
    has_image = bool(record.get("image_valid", False))

    return {**record, "text_length": text_length, "word_count": word_count, "has_image": has_image}
