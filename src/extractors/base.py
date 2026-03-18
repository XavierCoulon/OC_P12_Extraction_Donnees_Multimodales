"""Classe abstraite commune à tous les extracteurs."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

from src.utils.io import write_jsonl
from src.utils.logger import get_logger


class BaseExtractor(ABC):
    """
    Contrat commun à tous les extracteurs.

    Sous-classes : implémenter `extract()` et `normalize()`.
    Appeler `run()` pour lancer l'extraction complète.
    """

    source_name: str = ""

    def __init__(self) -> None:
        self.logger = get_logger(f"extractor.{self.source_name}")

    @abstractmethod
    def extract(self) -> Iterator[dict]:
        """Lit la source brute et yield chaque enregistrement brut."""

    @abstractmethod
    def normalize(self, raw: dict) -> dict | None:
        """
        Convertit un enregistrement brut vers le schéma unifié.

        Retourne None si l'entrée doit être ignorée (champs obligatoires manquants,
        label invalide, image inaccessible…).
        """

    def run(self, output_path: Path, limit: int | None = None) -> dict:
        """
        Orchestre extract → normalize → save.

        Retourne un dict de compteurs : total, success, skipped, errors.
        """
        output_path = Path(output_path)
        records: list[dict] = []
        counters = {"total": 0, "success": 0, "skipped": 0, "errors": 0}

        self.logger.info("Démarrage extraction [%s]", self.source_name)

        for raw in self.extract():
            if limit is not None and counters["success"] >= limit:
                break

            counters["total"] += 1
            try:
                normalized = self.normalize(raw)
                if normalized is None:
                    counters["skipped"] += 1
                else:
                    records.append(normalized)
                    counters["success"] += 1
            except Exception as e:
                counters["errors"] += 1
                self.logger.debug("Erreur normalisation entrée #%d : %s", counters["total"], e)

        written = write_jsonl(records, output_path)
        self.logger.info(
            "[%s] Terminé — total=%d success=%d skipped=%d errors=%d → %s (%d lignes)",
            self.source_name,
            counters["total"],
            counters["success"],
            counters["skipped"],
            counters["errors"],
            output_path,
            written,
        )
        return counters
