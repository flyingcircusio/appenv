from collections.abc import Callable
from pathlib import Path

from pytest import CaptureFixture, MonkeyPatch
from pytest_patterns.plugin import PatternsLib

from appenv import AppEnvSettings

def test_self_update_rewrites_script_on_version_mismatch(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    test_settings: Callable[..., AppEnvSettings],
    patterns: PatternsLib,
) -> None: ...
def test_self_update_noop_on_same_version(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    test_settings: Callable[..., AppEnvSettings],
) -> None: ...
def test_self_update_check(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    test_settings: Callable[..., AppEnvSettings],
    script_content: str,
    expected_exit_code: int,
) -> None: ...
def test_self_update_no_script(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    test_settings: Callable[..., AppEnvSettings],
) -> None: ...
def test_self_update_unknown_version(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    test_settings: Callable[..., AppEnvSettings],
) -> None: ...
def test_self_update_with_explicit_path(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    test_settings: Callable[..., AppEnvSettings],
    path_arg: str,
) -> None: ...
def test_self_update_externally_managed_no_path_no_basedir(
    tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None: ...
def test_self_update_path_overrides_externally_managed(
    tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None: ...
def test_self_update_standalone_delegates_to_uvx(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None: ...
def test_self_update_standalone_delegates_to_uvx_with_check(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None: ...
def test_self_update_standalone_uvx_failure(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None: ...
def test_self_update_standalone_script(monkeypatch: MonkeyPatch) -> None: ...
