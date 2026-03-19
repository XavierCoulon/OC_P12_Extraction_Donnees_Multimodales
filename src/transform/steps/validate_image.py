"""Validation des champs image d'un enregistrement."""

from src.utils.image import is_valid_image_url


def validate_image_fields(record: dict) -> dict:
    """Valide les champs image et ajoute le booléen `image_valid`.

    Vérifie que `image_url` est une URL HTTP(S) avec extension image reconnue.
    Le champ `image_path` (référence interne HF) est considéré valide s'il est non vide.

    Args:
        record: Enregistrement unifié issu des extracteurs.

    Returns:
        Enregistrement enrichi du champ `image_valid: bool`.
    """
    image_url: str = record.get("image_url", "") or ""
    image_path: str = record.get("image_path", "") or ""

    if image_url:
        image_valid = is_valid_image_url(image_url)
    elif image_path:
        # image_path est une référence interne HF (ex: "images/foo.jpg")
        image_valid = bool(image_path.strip())
    else:
        image_valid = False

    return {**record, "image_valid": image_valid}
