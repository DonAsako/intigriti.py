"""Smoke tests for the package metadata."""

import pytest

import intigriti


@pytest.mark.unit
def test_version_is_exposed() -> None:
    """The package exposes a version string."""
    assert isinstance(intigriti.__version__, str)
    assert intigriti.__version__
