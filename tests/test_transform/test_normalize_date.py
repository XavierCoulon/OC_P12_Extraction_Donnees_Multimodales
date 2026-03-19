"""Tests pour src/transform/steps/normalize_date.py"""

from src.transform.steps.normalize_date import normalize_date


def test_rfc822_format():
    result = normalize_date("Wed, 18 Mar 2026 09:10:08 +0100")
    assert result == "2026-03-18T09:10:08"


def test_iso8601_datetime():
    assert normalize_date("2026-03-18T09:10:08") == "2026-03-18T09:10:08"


def test_iso8601_date_only():
    assert normalize_date("2026-03-18") == "2026-03-18T00:00:00"


def test_unix_timestamp_integer():
    # 1742288408 = 2025-03-18T09:00:08 UTC
    result = normalize_date("1742288408")
    assert result.startswith("2025-03-18")


def test_unix_timestamp_float():
    result = normalize_date("1742288408.0")
    assert result.startswith("2025-03-18")


def test_unknown_format_returns_empty():
    assert normalize_date("not a date at all") == ""


def test_empty_string_returns_empty():
    assert normalize_date("") == ""


def test_none_returns_empty():
    assert normalize_date(None) == ""  # type: ignore[arg-type]
