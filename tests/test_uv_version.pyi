import pytest

@pytest.mark.parametrize(
    ("version_str", "expected"),
    [
        ("0.5.0", ...),
        ("0.10.3", ...),
        ("1.2.3", ...),
        ("0.5", None),
        ("1.2", None),
        ("1", None),
        ("invalid", None),
        ("", None),
        ("v0.5.0", None),
        ("v1.2.3", None),
    ],
)
def test_parse_uv_version(version_str: str, expected: object) -> None: ...
def test_uv_version_unknown() -> None: ...
def test_convert_version_preference_empty_versions() -> None: ...
def test_version_consistency() -> None: ...
