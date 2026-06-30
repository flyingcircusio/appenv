import pytest
from pytest import MonkeyPatch

def test_find_available_pythons_sorting(monkeypatch: MonkeyPatch) -> None: ...
def test_find_available_pythons_bare_python3_fallback(
    monkeypatch: MonkeyPatch,
) -> None: ...
def test_find_available_pythons_bare_python3_deduplication(
    monkeypatch: MonkeyPatch,
) -> None: ...
def test_find_available_pythons_bare_python3_too_old(
    monkeypatch: MonkeyPatch,
) -> None: ...
def test_find_available_pythons_bare_python3_subprocess_fails(
    monkeypatch: MonkeyPatch,
) -> None: ...
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
def test_version_satisfies_constraints(
    version: str, min_ver: str, max_ver: str | None, expected: bool
) -> None: ...
