"""Tests pour config.py — DEFAULT_LIMITS."""

from config import DEFAULT_LIMITS


_KNOWN_SOURCES = {"mmfakebench", "fakeddit", "hemt_fake", "mediaeval", "rss"}


def test_default_limits_covers_all_sources():
    assert _KNOWN_SOURCES == set(DEFAULT_LIMITS.keys())


def test_default_limits_values_are_none_or_positive_int():
    for source, limit in DEFAULT_LIMITS.items():
        assert limit is None or (isinstance(limit, int) and limit > 0), (
            f"{source}: limite invalide ({limit!r})"
        )


def test_fakeddit_has_limit():
    """Fakeddit est massif (>1M) — doit avoir une limite explicite."""
    assert DEFAULT_LIMITS["fakeddit"] is not None


def test_rss_has_limit():
    """RSS est un flux live de qualité variable — doit avoir une limite explicite."""
    assert DEFAULT_LIMITS["rss"] is not None
