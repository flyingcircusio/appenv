# SPDX-FileCopyrightText: 2020 Flying Circus
import shutil
import subprocess

import pytest

import appenv

"""Tests for find_available_pythons() and version_satisfies_constraints()."""


# Tier 1: Quick Wins


def test_find_available_pythons_sorting(monkeypatch):
    """find_available_pythons returns versions sorted numerically, newest-first.

    This test includes 3.9 to catch lexikographic vs numeric sorting bugs:
    - Numeric: 3.10 > 3.9 (correct)
    - Lexikographic: "3.9" > "3.10" (wrong, but would pass with broken sort)
    """

    def mock_which(name):
        versions = {
            "python3.9": "/usr/bin/python3.9",
            "python3.10": "/usr/bin/python3.10",
            "python3.11": "/usr/bin/python3.11",
            "python3.12": "/usr/bin/python3.12",
            "python3.13": "/usr/bin/python3.13",
            "python3.14": "/usr/bin/python3.14",
        }
        return versions.get(name)

    monkeypatch.setattr(shutil, "which", mock_which)

    result = appenv.find_available_pythons()

    # Must be numerically sorted: 3.14, 3.13, 3.12, 3.11, 3.10
    # (lexikographic would be wrong: 3.9 > 3.10)
    versions = [v for v, _ in result]
    assert versions == ["3.14", "3.13", "3.12", "3.11", "3.10"]


def test_find_available_pythons_bare_python3_fallback(monkeypatch):
    """find_available_pythons discovers unversioned python3 (macOS Xcode).

    When python3 exists but no python3.X symlinks point to it, the function
    should still discover it via subprocess version detection.
    """

    def mock_which(name):
        if name == "python3":
            return "/usr/bin/python3"
        return None

    monkeypatch.setattr(shutil, "which", mock_which)
    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda cmd, **kwargs: b"Python 3.12.0",
    )

    result = appenv.find_available_pythons()

    assert len(result) == 1
    assert result[0] == ("3.12", "/usr/bin/python3")


def test_find_available_pythons_bare_python3_deduplication(monkeypatch):
    """find_available_pythons skips python3 if its path already in the list.

    On systems where python3 -> python3.12, the resolved path should be
    deduplicated so we don't list the same binary twice.
    """

    def mock_which(name):
        if name == "python3.12":
            return "/usr/bin/python3.12"
        if name == "python3":
            return "/usr/bin/python3.12"
        return None

    monkeypatch.setattr(shutil, "which", mock_which)
    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda cmd, **kwargs: b"Python 3.12.0",
    )

    result = appenv.find_available_pythons()

    # Should only appear once (deduplicated by resolved path)
    assert len(result) == 1
    assert result[0][0] == "3.12"


def test_find_available_pythons_bare_python3_too_old(monkeypatch):
    """find_available_pythons skips python3 if version < 3.10."""

    def mock_which(name):
        if name == "python3":
            return "/usr/bin/python3"
        return None

    monkeypatch.setattr(shutil, "which", mock_which)
    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda cmd, **kwargs: b"Python 2.7.18",
    )

    result = appenv.find_available_pythons()

    assert len(result) == 0


def test_find_available_pythons_bare_python3_subprocess_fails(monkeypatch):
    """find_available_pythons handles subprocess failure for python3."""

    def mock_which(name):
        if name == "python3":
            return "/usr/bin/python3"
        return None

    monkeypatch.setattr(shutil, "which", mock_which)
    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda cmd, **kwargs: (_ for _ in ()).throw(OSError("broken")),
    )

    result = appenv.find_available_pythons()
    assert len(result) == 0


@pytest.mark.parametrize(
    ("version", "min_ver", "max_ver", "expected"),
    [
        ("3.10", "3.10", None, True),
        ("3.14", "3.10", None, True),
        ("3.10.1", "3.10", None, True),
        ("3.9", "3.10", None, False),
        ("3.8", "3.10", None, False),
        ("3.11", "3.10", "3.14", True),
        ("3.13", "3.10", "3.14", True),
        ("3.10", "3.10", "3.14", True),
        ("3.14", "3.10", "3.14", False),
        ("3.15", "3.10", "3.14", False),
        ("3.9", "3.10", "3.14", False),
        ("3.10.5", "3.10.0", None, True),
        ("3.10.0", "3.10.5", None, False),
        ("3.10.1", "3.10", None, True),
        ("3.10", "3.10.0", None, False),
    ],
)
def test_version_satisfies_constraints(version, min_ver, max_ver, expected):
    result = appenv.version_satisfies_constraints(version, min_ver, max_ver)
    assert result is expected
