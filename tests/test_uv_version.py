# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for UvVersion, version parsing, and version preference utilities."""

import re
from pathlib import Path

import pytest

import appenv
from appenv import UvVersion


@pytest.mark.parametrize(
    ("version_str", "expected"),
    [
        ("0.5.0", UvVersion(0, 5, 0)),
        ("0.10.3", UvVersion(0, 10, 3)),
        ("1.2.3", UvVersion(1, 2, 3)),
        ("0.5", None),
        ("1.2", None),
        ("1", None),
        ("invalid", None),
        ("", None),
        ("v0.5.0", None),
        ("v1.2.3", None),
    ],
)
def test_parse_uv_version(version_str, expected):
    if expected is not None:
        assert UvVersion.from_string(version_str) == expected
    else:
        with pytest.raises(appenv.NoValidUvError):
            UvVersion.from_string(version_str)


def test_uv_version_unknown():
    """Test UvVersion.unknown() returns zero version with 'unknown' str."""
    version = UvVersion.unknown()
    assert version.major == 0
    assert version.minor == 0
    assert version.patch == 0
    assert str(version) == "unknown"


def test_convert_version_preference_empty_versions():
    """Test convert_version_preference with empty versions list."""
    result = appenv.convert_version_preference([])
    assert result == (">=3.10", [])


def test_version_consistency():
    """Version in appenv.py matches version in appenv bootstrap script."""
    # Read version from appenv module
    module_version = appenv.__version__

    # Read version from src/appenv.py
    appenv_path = Path(__file__).parent.parent / "src" / "appenv.py"
    appenv_content = appenv_path.read_text()

    match = re.search(r'__version__ = "([^"]+)"', appenv_content)
    assert match, "Could not find __version__ in appenv file"
    file_version = match.group(1)

    assert module_version == file_version, (
        f"Version mismatch: module={module_version}, file={file_version}"
    )
