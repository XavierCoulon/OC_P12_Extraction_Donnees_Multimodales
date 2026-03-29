"""Extracteur MediaEval Verifying Multimedia Use (VMU) 2016.

Source : https://github.com/MKLab-ITI/image-verification-corpus

Structure des données (TSV) — testset/posts_groundtruth.txt :
  post_id  post_text  user_id  username  image_id  timestamp  label

Champs utilisés :
  post_id   → id
  post_text → text
  image_id  → image_path (identifiant local, ex: "airstrikes_1")
  timestamp → date
  label     → real / fake / humor (→ fake)

Note : les images sont dans Mediaeval2016_TestSet_Images.zip (non téléchargé).
       image_path contient l'identifiant de l'image, pas un chemin absolu.
"""

import csv
import io
import uuid
from typing import Iterator, Literal

import requests

from config import RAW_DIR
from src.extractors.base import BaseExtractor
from src.extractors.types import ArticleRecord

_TESTSET_URL = (
    "https://raw.githubusercontent.com/MKLab-ITI/image-verification-corpus"
    "/master/mediaeval2016/testset/posts_groundtruth.txt"
)
_RAW_DIR = RAW_DIR / "mediaeval"
_CACHE_FILE = _RAW_DIR / "mediaeval2016_testset_groundtruth.txt"

_LABEL_MAP: dict[str, Literal["real", "fake", "unknown"]] = {
    "real": "real",
    "fake": "fake",
    "humor": "fake",
    "non-verifiable": "unknown",
}


def _fetch_tsv(url: str, cache_path) -> list[dict]:
    """Télécharge (ou lit depuis le cache) le TSV et retourne une liste de dicts."""
    if cache_path.exists():
        raw = cache_path.read_text(encoding="utf-8")
    else:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        raw = response.text
        cache_path.write_text(raw, encoding="utf-8")

    reader = csv.DictReader(io.StringIO(raw), delimiter="\t")
    return list(reader)


class MediaEvalExtractor(BaseExtractor):
    source_name = "mediaeval"

    def extract(self) -> Iterator[dict]:
        self.logger.info("Téléchargement/lecture MediaEval 2016 testset…")
        try:
            rows = _fetch_tsv(_TESTSET_URL, _CACHE_FILE)
        except Exception as e:
            self.logger.error("Impossible de récupérer le TSV MediaEval : %s", e)
            return

        self.logger.info("%d entrées dans le testset", len(rows))
        yield from rows

    def normalize(self, raw: dict) -> ArticleRecord | None:
        text = str(raw.get("post_text") or "").strip()
        if not text:
            return None

        post_id = str(raw.get("post_id") or "").strip()
        image_id = str(raw.get("image_id") or "").strip()
        timestamp = str(raw.get("timestamp") or "").strip()
        label_raw = str(raw.get("label") or "").lower().strip()

        label = _LABEL_MAP.get(label_raw, "unknown")
        entry_id = post_id if post_id else str(uuid.uuid4())
        url = f"https://twitter.com/i/web/status/{post_id}" if post_id else ""

        return {
            "id": entry_id,
            "source": self.source_name,
            "title": "",
            "text": text,
            "image_url": "",
            "image_path": image_id,  # identifiant local (ex: "airstrikes_1")
            "label": label,
            "label_confidence": "high",
            "language": "en",
            "date": timestamp,
            "url": url,
            "domain": "twitter.com",
            "extraction_method": "dataset",
        }
