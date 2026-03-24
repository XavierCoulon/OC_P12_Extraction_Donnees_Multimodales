"""Extracteur RSS — flux publics de sources fiables."""

import uuid
from typing import Iterator
from urllib.parse import urlparse

import feedparser

from config import RSS_FEEDS
from src.extractors.base import BaseExtractor
from src.utils.image import is_valid_image_url

# Préfixes Snopes pour parser le label depuis le titre
_SNOPES_LABEL_MAP = {
    "true:": "real",
    "false:": "fake",
    "mostly true:": "real",
    "mostly false:": "fake",
    "mixture:": "unknown",
    "unproven:": "unknown",
    "miscaptioned:": "fake",
    "outdated:": "unknown",
    "scam:": "fake",
    "legend:": "unknown",
}


def _parse_snopes_label(title: str) -> str:
    """Extrait le label depuis un titre Snopes. Retourne 'unknown' si non reconnu."""
    lower = title.lower()
    for prefix, label in _SNOPES_LABEL_MAP.items():
        if lower.startswith(prefix):
            return label
    return "unknown"


def _extract_image_url(entry: dict) -> str | None:
    """Cherche une URL d'image dans les enclosures ou media_content d'une entrée RSS."""
    # Enclosures (RSS standard)
    for enc in entry.get("_enclosures", []):
        if enc.get("type", "").startswith("image/"):
            return enc.get("href") or enc.get("url")

    # media:content (Media RSS)
    for media in entry.get("_media_content", []):
        url = media.get("url")
        if url:
            return url

    # media:thumbnail
    thumbnails = entry.get("_media_thumbnail", [])
    if thumbnails:
        return thumbnails[0].get("url")

    return None


class RSSExtractor(BaseExtractor):
    source_name = "rss"

    def extract(self) -> Iterator[dict]:
        for feed_config in RSS_FEEDS:
            url = feed_config["url"]
            self.logger.info("Parsing flux RSS : %s", url)
            try:
                feed = feedparser.parse(url)
                if feed.bozo and not feed.entries:
                    self.logger.warning("Flux RSS invalide ou inaccessible : %s", url)
                    continue
                for entry in feed.entries:
                    # Extraire media_content et media_thumbnail avant conversion dict
                    # (feedparser stocke ces attributs dans un espace de noms spécial)
                    yield {
                        **dict(entry),
                        "_media_content": list(getattr(entry, "media_content", [])),
                        "_media_thumbnail": list(getattr(entry, "media_thumbnail", [])),
                        "_enclosures": list(getattr(entry, "enclosures", [])),
                        "_feed_config": feed_config,
                    }
            except Exception as e:
                self.logger.warning("Erreur lecture flux %s : %s", url, e)

    def normalize(self, raw: dict) -> dict | None:
        feed_config = raw.get("_feed_config", {})
        title = raw.get("title", "").strip()
        text = raw.get("summary", "").strip()
        url = raw.get("link", "")
        date = raw.get("published", "") or raw.get("updated", "")
        image_url = _extract_image_url(raw)

        if not text or not is_valid_image_url(image_url):
            return None

        # Label
        feed_label = feed_config.get("label", "real")
        if feed_label == "auto":
            label = _parse_snopes_label(title)
        else:
            label = feed_label

        domain = urlparse(url).netloc if url else ""
        entry_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"rss:{url or title}"))

        return {
            "id": entry_id,
            "source": self.source_name,
            "title": title,
            "text": text,
            "image_url": image_url,
            "image_path": "",
            "label": label,
            "label_confidence": "medium",
            "language": feed_config.get("language", "en"),
            "date": date,
            "url": url,
            "domain": domain,
            "extraction_method": "rss",
        }
