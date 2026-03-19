"""Vérification de l'association texte-image d'un enregistrement."""


def check_text_image_association(record: dict) -> dict:
    """Vérifie la cohérence entre le texte et l'image d'un enregistrement.

    Un enregistrement est considéré valide (text_image_ok=True) si :
    - Le texte est non vide ET
    - Au moins une référence image est présente (image_url valide OU image_path non vide)

    Cette vérification utilise `image_valid` calculé par validate_image_fields.

    Args:
        record: Enregistrement enrichi (doit contenir `text` et `image_valid`).

    Returns:
        Enregistrement enrichi du champ `text_image_ok: bool`.
    """
    has_text = bool((record.get("text") or "").strip())
    has_image = record.get("image_valid", False)

    return {**record, "text_image_ok": has_text and has_image}
