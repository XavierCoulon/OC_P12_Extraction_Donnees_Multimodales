"""Validation des champs image d'un enregistrement."""

from pathlib import Path

from config import IMAGE_CHECK_ACCESSIBLE
from src.utils.image import check_image_accessible, is_valid_image_url, validate_image


def validate_image_fields(record: dict) -> dict:
    """Valide les champs image et ajoute le booléen `image_valid`.

    Stratégie par type de source :

    - URL (fakeddit, rss) :
        - Vérifie le format via `is_valid_image_url()`
        - Si `IMAGE_CHECK_ACCESSIBLE=True`, vérifie l'accessibilité via HEAD request
    - Fichier local (miragenews) :
        - Vérifie l'intégrité via Pillow (`validate_image()`)
    - Référence interne (mmfakebench, mediaeval) :
        - Considéré valide si le champ est non vide (vérification réseau non applicable)

    Args:
        record: Enregistrement unifié issu des extracteurs.

    Returns:
        Enregistrement enrichi du champ `image_valid: bool`.
    """
    image_url: str = record.get("image_url", "") or ""
    image_path: str = record.get("image_path", "") or ""
    source: str = record.get("source", "") or ""

    if image_url:
        image_valid = is_valid_image_url(image_url)
        if image_valid and IMAGE_CHECK_ACCESSIBLE:
            image_valid = check_image_accessible(image_url)
    elif image_path:
        if source == "miragenews":
            image_valid = validate_image(Path(image_path))
        else:
            # mmfakebench (référence interne HF) et mediaeval (identifiant local)
            # — vérification réseau non applicable
            image_valid = bool(image_path.strip())
    else:
        image_valid = False

    return {**record, "image_valid": image_valid}
