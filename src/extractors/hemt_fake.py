"""Extracteur HEMT-Fake — Zenodo open access (DOI 10.5281/zenodo.11408513).

Le dataset est téléchargé automatiquement depuis Zenodo au premier lancement.
"""

import io
import json
import uuid
import zipfile
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

import requests

from config import RAW_DIR
from src.extractors.base import BaseExtractor

_ZENODO_URL = "https://zenodo.org/records/11408513/files/HEMT-Fake.zip?download=1"
_RAW_PATH = RAW_DIR / "hemt_fake" / "HEMT-Fake.zip"


def _ensure_downloaded() -> Path:
    """Télécharge le ZIP Zenodo si absent. Retourne le chemin du ZIP."""
    if _RAW_PATH.exists():
        return _RAW_PATH

    _RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(_ZENODO_URL, stream=True, timeout=120)
    response.raise_for_status()

    total = int(response.headers.get("Content-Length", 0))
    downloaded = 0
    with _RAW_PATH.open("wb") as f:
        for chunk in response.iter_content(chunk_size=65536):
            f.write(chunk)
            downloaded += len(chunk)

    return _RAW_PATH


class HemtFakeExtractor(BaseExtractor):
    source_name = "hemt_fake"

    def extract(self) -> Iterator[dict]:
        self.logger.info("Vérification/téléchargement HEMT-Fake depuis Zenodo…")
        try:
            zip_path = _ensure_downloaded()
        except Exception as e:
            self.logger.error("Impossible de télécharger HEMT-Fake : %s", e)
            return

        self.logger.info("Lecture du ZIP : %s", zip_path)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                json_files = [n for n in zf.namelist() if n.endswith(".json") and "__MACOSX" not in n]
                if not json_files:
                    self.logger.error("Aucun fichier JSON trouvé dans le ZIP")
                    return
                for json_name in json_files:
                    self.logger.info("Parsing : %s", json_name)
                    with zf.open(json_name) as jf:
                        try:
                            data = json.load(jf)
                        except json.JSONDecodeError as e:
                            self.logger.warning("JSON invalide %s : %s", json_name, e)
                            continue
                        items = data if isinstance(data, list) else data.get("data", [data])
                        for item in items:
                            yield item
        except zipfile.BadZipFile as e:
            self.logger.error("ZIP corrompu : %s", e)

    def normalize(self, raw: dict) -> dict | None:
        text = str(raw.get("text") or raw.get("content") or raw.get("body") or "").strip()
        title = str(raw.get("title") or "").strip()
        image_url = str(raw.get("image_url") or raw.get("image") or "").strip()
        label_raw = str(raw.get("label") or "").lower()
        language = str(raw.get("language") or "en").lower()
        source_url = str(raw.get("source_url") or raw.get("url") or "")

        if not text or not image_url:
            return None

        if label_raw in ("real", "true", "1"):
            label = "real"
        elif label_raw in ("fake", "false", "0"):
            label = "fake"
        else:
            label = "unknown"

        entry_id = str(raw.get("id") or uuid.uuid4())
        domain = urlparse(source_url).netloc if source_url else ""

        return {
            "id": entry_id,
            "source": self.source_name,
            "title": title,
            "text": text,
            "image_url": image_url,
            "image_path": "",
            "label": label,
            "label_confidence": "high",
            "language": language,
            "date": str(raw.get("date") or raw.get("published_date") or ""),
            "url": source_url,
            "domain": domain,
            "extraction_method": "dataset",
        }
