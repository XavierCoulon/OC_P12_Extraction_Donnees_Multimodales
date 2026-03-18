"""Fixtures partagées pour tous les tests."""

import io
import pytest
from PIL import Image


@pytest.fixture
def fake_image_bytes() -> bytes:
    """Retourne les bytes d'une image JPEG minimale valide."""
    buf = io.BytesIO()
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    img.save(buf, format="JPEG")
    return buf.getvalue()
