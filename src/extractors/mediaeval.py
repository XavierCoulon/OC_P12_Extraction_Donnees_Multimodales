"""Extracteur MediaEval Verifying Multimedia Use (VMU) — archives 2015-2022.

Les données sont téléchargées depuis les archives GitHub MediaEval.
Édition utilisée par défaut : 2016 (première édition avec annotations stables).
"""

import json
import uuid
from typing import Iterator
from urllib.parse import urlparse

import requests

from config import RAW_DIR
from src.extractors.base import BaseExtractor

# Archives disponibles : ajuster selon l'édition souhaitée
_MEDIAEVAL_URLS = [
    "https://raw.githubusercontent.com/multimediaeval/2016-Fake-News-Detection/master/data/mediaeval2016_testset_gt.json",
    "https://raw.githubusercontent.com/multimediaeval/2016-Fake-News-Detection/master/data/mediaeval2016_devset_gt.json",
]

_RAW_DIR = RAW_DIR / "mediaeval"

_LABEL_MAP = {
    "real": "real",
    "fake": "fake",
    "humor": "fake",           # humour intentionnellement trompeur
    "non-verifiable": "unknown",
}


def _fetch_json(url: str) -> list[dict]:
    """Télécharge et parse un fichier JSON depuis une URL."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else data.get("data", [data])


class MediaEvalExtractor(BaseExtractor):
    source_name = "mediaeval"

    def extract(self) -> Iterator[dict]:
        _RAW_DIR.mkdir(parents=True, exist_ok=True)

        for url in _MEDIAEVAL_URLS:
            filename = url.split("/")[-1]
            local_path = _RAW_DIR / filename

            if local_path.exists():
                self.logger.info("Lecture cache local : %s", filename)
                try:
                    with local_path.open("r", encoding="utf-8") as f:
                        items = json.load(f)
                    items = items if isinstance(items, list) else items.get("data", [items])
                except Exception as e:
                    self.logger.warning("Erreur lecture cache %s : %s", filename, e)
                    continue
            else:
                self.logger.info("Téléchargement MediaEval : %s", filename)
                try:
                    items = _fetch_json(url)
                    with local_path.open("w", encoding="utf-8") as f:
                        json.dump(items, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    self.logger.warning("Impossible de récupérer %s : %s", url, e)
                    continue

            self.logger.info("%d entrées dans %s", len(items), filename)
            for item in items:
                yield item

    def normalize(self, raw: dict) -> dict | None:
        text = str(raw.get("tweetText") or raw.get("text") or "").strip()
        image_url = str(raw.get("imageUrl") or raw.get("image_url") or "").strip()
        tweet_id = str(raw.get("tweetId") or raw.get("id") or "")
        label_raw = str(raw.get("label") or "").lower().strip()
        date = str(raw.get("date") or raw.get("tweetDate") or "")

        if not text or not image_url:
            return None

        label = _LABEL_MAP.get(label_raw, "unknown")

        entry_id = tweet_id if tweet_id else str(uuid.uuid4())
        url = f"https://twitter.com/i/web/status/{tweet_id}" if tweet_id else ""

        return {
            "id": entry_id,
            "source": self.source_name,
            "title": "",
            "text": text,
            "image_url": image_url,
            "image_path": "",
            "label": label,
            "label_confidence": "high",
            "language": "en",
            "date": date,
            "url": url,
            "domain": "twitter.com",
            "extraction_method": "dataset",
        }
