"""Normalisation des dates vers le format ISO 8601 (YYYY-MM-DDTHH:MM:SS)."""

import email.utils
from datetime import datetime, timezone


def normalize_date(date_str: str) -> str:
    """Normalise une date vers ISO 8601, quel que soit le format d'entrée.

    Formats supportés :
    - RFC 822 / email (ex: "Wed, 18 Mar 2026 09:10:08 +0100")
    - ISO 8601 (ex: "2026-03-18T09:10:08", "2026-03-18")
    - Timestamp UNIX entier ou flottant (ex: "1742287808")

    Args:
        date_str: Chaîne de date dans l'un des formats supportés.

    Returns:
        Date au format ISO 8601 (ex: "2026-03-18T09:10:08"), ou "" si invalide.
    """
    if not date_str or not isinstance(date_str, str):
        return ""

    value = date_str.strip()

    # Timestamp UNIX (entier ou flottant)
    if value.replace(".", "", 1).lstrip("-").isdigit():
        try:
            ts = float(value)
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        except (ValueError, OSError, OverflowError):
            pass

    # RFC 822 / email date
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        return parsed.strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        pass

    # ISO 8601 (complet ou date seule)
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            continue

    return ""
