"""Tests pour src/utils/image.py."""

import pytest
import responses as responses_lib

from src.utils.image import check_image_accessible, download_image, validate_image


IMAGE_URL = "https://example.com/photo.jpg"


@responses_lib.activate
def test_download_image_success(tmp_path, fake_image_bytes):
    responses_lib.add(
        responses_lib.GET,
        IMAGE_URL,
        body=fake_image_bytes,
        content_type="image/jpeg",
        status=200,
    )
    dest = tmp_path / "img.jpg"
    assert download_image(IMAGE_URL, dest) is True
    assert dest.exists()


@responses_lib.activate
def test_download_image_http_404(tmp_path):
    responses_lib.add(responses_lib.GET, IMAGE_URL, status=404)
    dest = tmp_path / "img.jpg"
    assert download_image(IMAGE_URL, dest) is False
    assert not dest.exists()


@responses_lib.activate
def test_download_image_non_image_content_type(tmp_path):
    responses_lib.add(
        responses_lib.GET,
        IMAGE_URL,
        body=b"<html></html>",
        content_type="text/html",
        status=200,
    )
    dest = tmp_path / "img.jpg"
    assert download_image(IMAGE_URL, dest) is False


@responses_lib.activate
def test_download_image_creates_parent_dirs(tmp_path, fake_image_bytes):
    responses_lib.add(
        responses_lib.GET,
        IMAGE_URL,
        body=fake_image_bytes,
        content_type="image/jpeg",
        status=200,
    )
    dest = tmp_path / "deep" / "nested" / "img.jpg"
    assert download_image(IMAGE_URL, dest) is True
    assert dest.exists()


def test_validate_image_valid_jpeg(tmp_path, fake_image_bytes):
    path = tmp_path / "img.jpg"
    path.write_bytes(fake_image_bytes)
    assert validate_image(path) is True


def test_validate_image_invalid_file(tmp_path):
    path = tmp_path / "not_an_image.jpg"
    path.write_bytes(b"this is not an image")
    assert validate_image(path) is False


@responses_lib.activate
def test_check_image_accessible_200():
    responses_lib.add(responses_lib.HEAD, IMAGE_URL, status=200)
    assert check_image_accessible(IMAGE_URL) is True


@responses_lib.activate
def test_check_image_accessible_404():
    responses_lib.add(responses_lib.HEAD, IMAGE_URL, status=404)
    assert check_image_accessible(IMAGE_URL) is False


@responses_lib.activate
def test_check_image_accessible_connection_error():
    responses_lib.add(responses_lib.HEAD, IMAGE_URL, body=Exception("timeout"))
    assert check_image_accessible(IMAGE_URL) is False
