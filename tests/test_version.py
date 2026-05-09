"""Tests for heventure_search_mcp package metadata."""

import re

from heventure_search_mcp import __author__, __description__, __version__


def test_version_format():
    """__version__ should be a valid semver-ish string or 0.0.0 fallback."""
    assert isinstance(__version__, str), "__version__ must be a string"
    assert len(__version__) > 0, "__version__ must not be empty"
    # Match X.Y.Z or X.Y.Z+something, or the fallback 0.0.0
    assert re.match(r"^\d+\.\d+\.\d+", __version__), (
        f"__version__ '{__version__}' doesn't look like a version"
    )


def test_author():
    assert __author__ == "HughesCuit"


def test_description():
    assert isinstance(__description__, str)
    assert len(__description__) > 0
