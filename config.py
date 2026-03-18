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

# Flux RSS (ajouter/supprimer une entrée pour modifier les sources)
RSS_FEEDS = [
    {"url": "https://www.lemonde.fr/rss/une.xml",           "language": "fr", "label": "real"},
    {"url": "http://feeds.bbci.co.uk/news/rss.xml",          "language": "en", "label": "real"},
    {"url": "https://feeds.reuters.com/reuters/topNews",      "language": "en", "label": "real"},
    {"url": "https://www.snopes.com/feed/",                   "language": "en", "label": "auto"},
]

# Chemins des données brutes Fakeddit (CSV pré-téléchargés)
FAKEDDIT_RAW_DIR = RAW_DIR / "fakeddit"

# Dataset HuggingFace MMFakeBench
MMFAKEBENCH_DATASET_ID = "liuxuannan/MMFakeBench"
