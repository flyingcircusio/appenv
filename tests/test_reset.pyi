from collections.abc import Callable
from pathlib import Path

from pytest import CaptureFixture, MonkeyPatch
from pytest_patterns.plugin import PatternsLib

from appenv import AppEnvSettings

def test_reset_nonexisting_envdir_silent(
    tmp_path: Path, test_settings: Callable[..., AppEnvSettings]
) -> None: ...
def test_reset_removes_envdir_with_subdirs(
    tmp_path: Path, test_settings: Callable[..., AppEnvSettings]
) -> None: ...
def test_reset_warns_about_unmanaged_real_venv(
    tmp_path: Path,
    capsys: CaptureFixture[str],
    test_settings: Callable[..., AppEnvSettings],
    patterns: PatternsLib,
) -> None: ...
def test_reset_removes_venv_symlink_and_managed_venv(
    tmp_path: Path,
    capsys: CaptureFixture[str],
    test_settings: Callable[..., AppEnvSettings],
    patterns: PatternsLib,
) -> None: ...
def test_reset_unlinks_file_in_appenv(
    workdir: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None: ...
def test_reset_removes_real_venv(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    test_settings: Callable[..., AppEnvSettings],
) -> None: ...
def test_reset_keeps_uv_binary(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    test_settings: Callable[..., AppEnvSettings],
) -> None: ...
