"""Extracteur MiRAGeNews — HuggingFace datasets.

Dataset : anson-huang/mirage-news
Paper   : MiRAGeNews: Multimodal Realistic AI-Generated News Detection (2024)
Accès   : Public, aucun token requis.

Structure du dataset :
  image : PIL.Image  — image réelle (label=0) ou générée par IA (label=1)
  text  : str        — dépêche textuelle (NYT, BBC, CNN)
  label : int        — 0 = real, 1 = fake (image AI-générée)

Splits disponibles :
  train (10k), validation (2.5k),
  test1_nyt_mj, test2_bbc_dalle, test3_cnn_dalle,
  test4_bbc_sdxl, test5_cnn_sdxl (500 chacun)

Images sauvegardées localement dans IMAGES_DIR/miragenews/<uuid>.jpg.
"""

import uuid
from pathlib import Path
from typing import Iterator

from config import IMAGES_DIR
from src.extractors.base import BaseExtractor

_DATASET_ID = "anson-huang/mirage-news"
_IMAGES_DIR = IMAGES_DIR / "miragenews"
_SPLITS = [
    "train",
    "validation",
    "test1_nyt_mj",
    "test2_bbc_dalle",
    "test3_cnn_dalle",
    "test4_bbc_sdxl",
    "test5_cnn_sdxl",
]


class MiRAGeNewsExtractor(BaseExtractor):
    source_name = "miragenews"

    def extract(self) -> Iterator[dict]:
        try:
            from datasets import load_dataset
        except ImportError:
            self.logger.error("Package 'datasets' non installé. Lancez : uv sync")
            return

        _IMAGES_DIR.mkdir(parents=True, exist_ok=True)

        for split_name in _SPLITS:
            self.logger.info("Chargement split : %s / %s", _DATASET_ID, split_name)
            try:
                split = load_dataset(
                    _DATASET_ID,
                    split=split_name,
                    trust_remote_code=False,
                )
            except Exception as e:
                self.logger.warning("Impossible de charger le split '%s' : %s", split_name, e)
                continue

            self.logger.info("Split '%s' : %d entrées", split_name, len(split))
            for row in split:
                yield {"_split": split_name, **row}

    def normalize(self, raw: dict) -> dict | None:
        text = str(raw.get("text") or "").strip()
        if not text:
            return None

        image = raw.get("image")
        if image is None:
            return None

        # Sauvegarde de l'image PIL sur disque
        entry_id = str(uuid.uuid4())
        image_filename = f"{entry_id}.jpg"
        image_path = _IMAGES_DIR / image_filename

        try:
            img = image.convert("RGB")
            img.save(image_path, format="JPEG", quality=90)
        except Exception as e:
            self.logger.debug("Erreur sauvegarde image %s : %s", image_filename, e)
            return None

        label_int = raw.get("label", -1)
        label = "real" if label_int == 0 else "fake" if label_int == 1 else "unknown"

        return {
            "id": entry_id,
            "source": self.source_name,
            "title": "",
            "text": text,
            "image_url": "",
            "image_path": str(image_path),
            "label": label,
            "label_confidence": "high",
            "language": "en",
            "date": "",
            "url": "",
            "domain": str(raw.get("_split", "")),
            "extraction_method": "dataset",
        }
