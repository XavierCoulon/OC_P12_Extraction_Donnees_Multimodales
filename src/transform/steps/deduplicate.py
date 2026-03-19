"""Déduplication des enregistrements par hash contenu."""

import hashlib


def _record_hash(record: dict) -> str:
    """Calcule un hash MD5 basé sur la source et le début du texte."""
    source = record.get("source", "")
    text = (record.get("text") or "")[:200]
    key = f"{source}:{text}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def deduplicate(records: list[dict]) -> list[dict]:
    """Supprime les doublons d'une liste d'enregistrements.

    Deux enregistrements sont considérés identiques si leur source et les 200
    premiers caractères de leur texte produisent le même hash MD5.
    La première occurrence est conservée.

    Args:
        records: Liste d'enregistrements potentiellement dupliqués.

    Returns:
        Liste dédupliquée, ordre de première occurrence préservé.
    """
    seen: set[str] = set()
    unique: list[dict] = []
    for record in records:
        h = _record_hash(record)
        if h not in seen:
            seen.add(h)
            unique.append(record)
    return unique
