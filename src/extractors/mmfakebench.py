"""Extracteur MMFakeBench — HuggingFace datasets (ICLR 2025).

Pré-requis :
- Avoir un compte HuggingFace et accepté le Data Usage Protocol sur :
  https://huggingface.co/datasets/liuxuannan/MMFakeBench
- Définir HF_TOKEN dans .env
"""

import io
import os
import uuid
from typing import Iterator

from dotenv import load_dotenv

from config import IMAGES_DIR, MMFAKEBENCH_DATASET_ID
from src.extractors.base import BaseExtractor

load_dotenv()

_LABEL_MAP = {0: "fake", 1: "real"}


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

        self.logger.info("Chargement dataset HuggingFace : %s", MMFAKEBENCH_DATASET_ID)
        try:
            dataset = load_dataset(MMFAKEBENCH_DATASET_ID, token=token, trust_remote_code=False)
        except Exception as e:
            self.logger.error("Erreur chargement dataset HF : %s", e)
            return

        for split_name, split in dataset.items():
            self.logger.info("Split '%s' : %d entrées", split_name, len(split))
            for row in split:
                yield dict(row)

    def normalize(self, raw: dict) -> dict | None:
        from PIL import Image

        text = str(raw.get("text") or raw.get("caption") or "").strip()
        title = str(raw.get("title") or "").strip()
        raw_label = raw.get("label")

        if not text:
            return None

        label = _LABEL_MAP.get(int(raw_label), "unknown") if raw_label is not None else "unknown"
        entry_id = str(raw.get("id") or uuid.uuid4())

        # L'image est un objet PIL intégré dans le dataset HF
        pil_image = raw.get("image")
        image_path = IMAGES_DIR / "mmfakebench" / f"{entry_id}.jpg"
        image_url = str(raw.get("image_url") or "")

        if pil_image is not None:
            try:
                image_path.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(pil_image, Image.Image):
                    pil_image.convert("RGB").save(image_path, "JPEG")
                else:
                    return None
            except Exception as e:
                self.logger.debug("Erreur sauvegarde image %s : %s", entry_id, e)
                return None
        elif image_url:
            from src.utils.image import download_image
            if not download_image(image_url, image_path):
                self.logger.debug("Image inaccessible, entrée ignorée : %s", image_url)
                return None
        else:
            return None

        return {
            "id": entry_id,
            "source": self.source_name,
            "title": title,
            "text": text,
            "image_url": image_url,
            "image_path": str(image_path),
            "label": label,
            "label_confidence": "high",
            "language": "en",
            "date": str(raw.get("date") or ""),
            "url": str(raw.get("url") or ""),
            "domain": str(raw.get("source") or ""),
            "extraction_method": "dataset",
        }
