"""Téléchargement et validation d'images."""

import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, UnidentifiedImageError

from config import IMAGE_DOWNLOAD_BACKOFF, IMAGE_DOWNLOAD_RETRIES, IMAGE_DOWNLOAD_TIMEOUT
from src.utils.logger import get_logger

logger = get_logger(__name__)


def download_image(url: str, dest_path: Path, timeout: int = IMAGE_DOWNLOAD_TIMEOUT, retries: int = IMAGE_DOWNLOAD_RETRIES) -> bool:
    """
    Télécharge une image depuis une URL vers dest_path.

    Retourne True si succès, False sinon (après retries tentatives).
    Ne lève pas d'exception : les erreurs sont loggées.
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0 (compatible; academic-research-bot/1.0)"}

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=timeout, headers=headers, stream=True)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type and "octet-stream" not in content_type:
                logger.debug("URL ne retourne pas une image (%s) : %s", content_type, url)
                return False

            with dest_path.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            if validate_image(dest_path):
                return True
            else:
                dest_path.unlink(missing_ok=True)
                return False

        except requests.exceptions.HTTPError as e:
            logger.debug("HTTP %s sur %s (tentative %d/%d)", e.response.status_code, url, attempt, retries)
            return False  # Pas de retry sur les erreurs HTTP 4xx/5xx
        except requests.exceptions.ConnectionError:
            logger.debug("Erreur connexion sur %s (tentative %d/%d)", url, attempt, retries)
        except requests.exceptions.Timeout:
            logger.debug("Timeout sur %s (tentative %d/%d)", url, attempt, retries)
        except Exception as e:
            logger.debug("Erreur inattendue sur %s : %s (tentative %d/%d)", url, e, attempt, retries)

        if attempt < retries:
            time.sleep(IMAGE_DOWNLOAD_BACKOFF ** attempt)

    return False


_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif", ".svg"}


def is_valid_image_url(url: str) -> bool:
    """
    Vérifie qu'une URL pointe vers une image exploitable (format uniquement, sans réseau).

    Critères :
    - Schéma http ou https
    - Extension de fichier image reconnue dans le chemin, OU absence d'extension
      (CDNs et APIs servent souvent des images sans extension)
    """
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    if not parsed.netloc:
        return False
    path = parsed.path.lower()
    if "." in path.split("/")[-1]:
        ext = "." + path.rsplit(".", 1)[-1].split("?")[0]
        if ext not in _IMAGE_EXTENSIONS:
            return False
    return True


def validate_image(path: Path) -> bool:
    """
    Vérifie qu'un fichier est une image valide et non corrompue via Pillow.

    Retourne True si valide, False sinon.
    """
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, Exception):
        return False
