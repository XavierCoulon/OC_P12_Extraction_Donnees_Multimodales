"""Types partagés entre tous les extracteurs."""

from typing import Literal, TypedDict


class ArticleRecord(TypedDict):
    """Schéma unifié retourné par chaque extracteur via normalize()."""

    id: str
    source: str
    title: str
    text: str
    image_url: str
    image_path: str
    label: Literal["real", "fake", "unknown"]
    label_confidence: Literal["high", "medium", "low"]
    language: str
    date: str
    url: str
    domain: str
    extraction_method: Literal["dataset", "rss"]


class ExtractionCounters(TypedDict):
    """Compteurs retournés par BaseExtractor.run()."""

    total: int
    success: int
    skipped: int
    errors: int
