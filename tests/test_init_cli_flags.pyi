from collections.abc import Callable
from pathlib import Path

from pytest import CaptureFixture

from appenv import AppEnv

def test_init_rejects_malformed_python_version(
    bad_version: str,
    workdir: Path,
    app_env: Callable[..., AppEnv],
    capsys: CaptureFixture[str],
) -> None: ...
def test_init_accepts_major_minor_python_version(
    good_version: str, workdir: Path, app_env: Callable[..., AppEnv]
) -> None: ...
def test_init_help_lists_description_flag(
    workdir: Path, app_env: Callable[..., AppEnv], capsys: CaptureFixture[str]
) -> None: ...
def test_init_noninteractive_writes_description_flag(
    workdir: Path, app_env: Callable[..., AppEnv]
) -> None: ...
def test_init_description_stays_empty_when_flag_absent(
    workdir: Path, app_env: Callable[..., AppEnv]
) -> None: ...
def test_init_dep_without_binary_no_tty(
    workdir: Path,
    monkeypatch: object,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
