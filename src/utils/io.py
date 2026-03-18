"""Lecture et écriture au format JSON Lines (.jsonl)."""

import json
from pathlib import Path
from typing import Iterator


def write_jsonl(records: list[dict], path: Path) -> int:
    """Écrit une liste de dicts en JSON Lines. Retourne le nombre d'entrées écrites."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def read_jsonl(path: Path) -> Iterator[dict]:
    """Lit un fichier JSON Lines et yield chaque entrée."""
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)
