"""Mapping des labels textuels vers des entiers."""

_LABEL_MAP: dict[str, int] = {
    "real": 1,
    "fake": 0,
    "unknown": -1,
}


def map_label(record: dict) -> dict:
    """Ajoute `label_int` (entier) correspondant au label textuel.

    Mapping :
    - "real"    → 1
    - "fake"    → 0
    - "unknown" → -1
    - Autre     → -1 (valeur de sécurité)

    Args:
        record: Enregistrement unifié contenant le champ `label`.

    Returns:
        Enregistrement enrichi du champ `label_int: int`.
    """
    label = (record.get("label") or "").lower().strip()
    label_int = _LABEL_MAP.get(label, -1)
    return {**record, "label_int": label_int}
