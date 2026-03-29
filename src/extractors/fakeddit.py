"""Extracteur Fakeddit — dataset statique CSV + images.

Pré-requis : télécharger les CSV depuis https://fakeddit.netlify.app/
et les placer dans data/raw/fakeddit/ avant d'exécuter ce script.
"""

import uuid
from pathlib import Path
from typing import Iterator, Literal

import pandas as pd

from config import FAKEDDIT_RAW_DIR
from src.extractors.base import BaseExtractor
from src.extractors.types import ArticleRecord
from src.utils.image import is_valid_image_url

_LABEL_MAP: dict[int, Literal["real", "fake", "unknown"]] = {0: "fake", 1: "real"}


class FakedditExtractor(BaseExtractor):
    source_name = "fakeddit"

    def extract(self) -> Iterator[dict]:
        csv_files = list(FAKEDDIT_RAW_DIR.glob("*.csv")) + list(FAKEDDIT_RAW_DIR.glob("*.tsv"))
        if not csv_files:
            self.logger.error(
                "Aucun CSV trouvé dans %s. "
                "Téléchargez les fichiers sur https://fakeddit.netlify.app/",
                FAKEDDIT_RAW_DIR,
            )
            return

        for csv_path in csv_files:
            self.logger.info("Lecture CSV : %s", csv_path.name)
            sep = "\t" if csv_path.suffix == ".tsv" else ","
            try:
                df = pd.read_csv(csv_path, sep=sep, low_memory=False)
                for _, row in df.iterrows():
                    yield row.to_dict()
            except Exception as e:
                self.logger.warning("Erreur lecture %s : %s", csv_path.name, e)

    def normalize(self, raw: dict) -> ArticleRecord | None:
        # Champs obligatoires
        image_url = raw.get("image_url", "")
        text = str(raw.get("title", "")).strip()
        raw_label = raw.get("2_way_label")

        if not text or not is_valid_image_url(str(image_url) if not pd.isna(image_url) else ""):
            return None

        # Label : 0 = fake, 1 = real ; exclure non-verifiable (label 6 classes)
        six_class = str(raw.get("6_way_label", "")).lower()
        if six_class == "non-verifiable":
            return None

        label = _LABEL_MAP.get(int(raw_label), "unknown") if not pd.isna(raw_label) else "unknown"

        entry_id = str(raw.get("id", uuid.uuid4()))

        permalink = raw.get("permalink", "")
        url = f"https://reddit.com{permalink}" if permalink else ""
        date_raw = raw.get("created_utc", "")
        date = str(int(date_raw)) if not pd.isna(date_raw) else ""

        return {
            "id": entry_id,
            "source": self.source_name,
            "title": text,
            "text": text,
            "image_url": str(image_url),
            "image_path": "",
            "label": label,
            "label_confidence": "high",
            "language": "en",
            "date": date,
            "url": url,
            "domain": str(raw.get("domain", "")),
            "extraction_method": "dataset",
        }
