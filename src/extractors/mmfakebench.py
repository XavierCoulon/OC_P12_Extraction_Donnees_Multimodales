"""Extracteur MMFakeBench — HuggingFace datasets (ICLR 2025).

Pré-requis :
- Avoir un compte HuggingFace et accepté le Data Usage Protocol sur :
  https://huggingface.co/datasets/liuxuannan/MMFakeBench
- Définir HF_TOKEN dans .env

Champs du dataset :
  text, image_path, text_source, image_source, gt_answers, fake_cls

Les images restent dans le repo HuggingFace — image_path est une référence
interne accessible via load_dataset() au moment de l'entraînement.
"""

import os
import uuid
from typing import Iterator

from dotenv import load_dotenv

from config import MMFAKEBENCH_DATASET_ID
from src.extractors.base import BaseExtractor
from src.utils.image import is_valid_image_url

load_dotenv()

# gt_answers : "True" = contenu authentique, "Fake" = contenu manipulé
# (valeurs réelles observées dans le dataset, pas "False")
_LABEL_MAP = {"True": "real", "Fake": "fake", "False": "fake"}


class MMFakeBenchExtractor(BaseExtractor):
    source_name = "mmfakebench"

    def extract(self) -> Iterator[dict]:
        token = os.getenv("HF_TOKEN")
        if not token:
            self.logger.error(
                "HF_TOKEN manquant. Définissez-le dans .env "
                "(voir .env.example et https://huggingface.co/settings/tokens)"
            )
            return

        try:
            from datasets import load_dataset
        except ImportError:
            self.logger.error("Package 'datasets' non installé. Lancez : uv sync")
            return

        configs = ["MMFakeBench_val", "MMFakeBench_test"]
        for config_name in configs:
            self.logger.info("Chargement dataset HuggingFace : %s / %s", MMFAKEBENCH_DATASET_ID, config_name)
            try:
                dataset = load_dataset(MMFAKEBENCH_DATASET_ID, config_name, token=token, trust_remote_code=False)
            except Exception as e:
                self.logger.error("Erreur chargement dataset HF (%s) : %s", config_name, e)
                continue

            for split_name, split in dataset.items():
                self.logger.info("Config '%s' / split '%s' : %d entrées", config_name, split_name, len(split))
                yield from (dict(row) for row in split)

    def normalize(self, raw: dict) -> dict | None:
        text = str(raw.get("text") or "").strip()
        if not text:
            return None

        image_path = str(raw.get("image_path") or "").strip()
        if not image_path:
            return None

        raw_label = str(raw.get("gt_answers") or "").strip()
        label = _LABEL_MAP.get(raw_label, "unknown")

        return {
            "id": str(uuid.uuid4()),
            "source": self.source_name,
            "title": "",
            "text": text,
            "image_url": "",
            "image_path": image_path,
            "label": label,
            "label_confidence": "high",
            "language": "en",
            "date": "",
            "url": "",
            "domain": str(raw.get("text_source") or ""),
            "extraction_method": "dataset",
        }
