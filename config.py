"""Paramètres configurables du projet."""

from pathlib import Path

# Répertoires
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
IMAGES_DIR = DATA_DIR / "images"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = ROOT_DIR / "logs"

# Création automatique des répertoires nécessaires
for _dir in (RAW_DIR, IMAGES_DIR, PROCESSED_DIR, LOGS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# Téléchargement d'images
IMAGE_DOWNLOAD_TIMEOUT = 10       # secondes
IMAGE_DOWNLOAD_RETRIES = 3        # tentatives max
IMAGE_DOWNLOAD_BACKOFF = 2.0      # facteur de backoff exponentiel

# Vérification d'accessibilité des URL d'images (HEAD request)
# Désactivé par défaut : trop coûteux pour Fakeddit (~1M records).
# Activer ponctuellement pour RSS ou en mode sampling.
# Surcharger via variable d'environnement : IMAGE_CHECK_ACCESSIBLE=true
import os as _os
IMAGE_CHECK_ACCESSIBLE: bool = _os.getenv("IMAGE_CHECK_ACCESSIBLE", "false").lower() == "true"

# Flux RSS (ajouter/supprimer une entrée pour modifier les sources)
RSS_FEEDS = [
    {"url": "https://www.lemonde.fr/rss/une.xml",           "language": "fr", "label": "real"},
    {"url": "http://feeds.bbci.co.uk/news/rss.xml",          "language": "en", "label": "real"},
    {"url": "https://www.theguardian.com/world/rss",           "language": "en", "label": "real"},
    {"url": "https://www.snopes.com/feed/",                   "language": "en", "label": "auto"},
]

# Chemins des données brutes Fakeddit (CSV pré-téléchargés)
FAKEDDIT_RAW_DIR = RAW_DIR / "fakeddit"

# Dataset HuggingFace MMFakeBench
MMFAKEBENCH_DATASET_ID = "liuxuannan/MMFakeBench"

# Dataset HuggingFace MiRAGeNews
MIRAGENEWS_DATASET_ID = "anson-huang/mirage-news"

# Limites d'extraction par défaut (None = pas de limite)
DEFAULT_LIMITS: dict[str, int | None] = {
    "mmfakebench": None,    # ~11 000 entrées, dataset annoté de qualité
    "fakeddit":    10_000,  # dataset massif (>1M), sélection représentative
    "miragenews":  None,    # ~15 000 entrées, dataset AI-generated images
    "mediaeval":   None,    # ~2 177 entrées
    "rss":         500,     # flux live, qualité variable
}
