"""Tests for package release metadata."""

from stanag4607 import __version__


def test_package_exposes_release_version() -> None:
    assert __version__ == "0.1.0"
