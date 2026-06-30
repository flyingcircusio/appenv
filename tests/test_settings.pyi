import pytest
from pytest import MonkeyPatch

def _clear_appenv_settings_env(monkeypatch: MonkeyPatch) -> None: ...
def test_settings_from_env_defaults_when_unset(monkeypatch: MonkeyPatch) -> None: ...
@pytest.mark.parametrize(
    "value", ["1", "true", "yes", "0", "false", "verbose", "anything-non-empty"]
)
def test_settings_from_env_verbose_truthy_when_nonempty_stripped(
    monkeypatch: MonkeyPatch, value: str
) -> None: ...
@pytest.mark.parametrize("value", ["", "   ", "\t", " \n "])
def test_settings_from_env_verbose_false_when_empty_or_whitespace(
    monkeypatch: MonkeyPatch, value: str
) -> None: ...
def test_settings_from_env_verbose_false_when_unset(
    monkeypatch: MonkeyPatch,
) -> None: ...
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("dev", ["dev"]),
        ("dev,test", ["dev", "test"]),
        (" dev , test , docs ", ["dev", "test", "docs"]),
        ("dev,,test,", ["dev", "test"]),
        ("", []),
    ],
)
def test_settings_from_env_extras_parsing(
    monkeypatch: MonkeyPatch, raw: str, expected: list[str]
) -> None: ...
def test_settings_from_env_extras_unset_yields_empty(
    monkeypatch: MonkeyPatch,
) -> None: ...
def test_settings_from_env_extras_deduplicated(
    monkeypatch: MonkeyPatch,
) -> None: ...
def test_settings_from_env_basedir_from_env(monkeypatch: MonkeyPatch) -> None: ...
def test_settings_from_env_basedir_default_module_dir(
    monkeypatch: MonkeyPatch,
) -> None: ...
def test_settings_from_env_returns_frozen_dataclass(
    monkeypatch: MonkeyPatch,
) -> None: ...
