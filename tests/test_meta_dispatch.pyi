from collections.abc import Callable
from pathlib import Path

import pytest
from pytest import CaptureFixture, MonkeyPatch

from appenv import AppEnv

def test_meta_calls_reset(
    monkeypatch: MonkeyPatch, tmp_path: Path, app_env: Callable[..., AppEnv]
) -> None: ...
def test_meta_calls_prepare(
    monkeypatch: MonkeyPatch, tmp_path: Path, app_env: Callable[..., AppEnv]
) -> None: ...
def test_meta_calls_python(
    monkeypatch: MonkeyPatch, tmp_path: Path, app_env: Callable[..., AppEnv]
) -> None: ...
def test_meta_calls_run_script(
    monkeypatch: MonkeyPatch, tmp_path: Path, app_env: Callable[..., AppEnv]
) -> None: ...
def test_meta_unrecognized_arguments(
    tmp_path: Path, app_env: Callable[..., AppEnv], capsys: CaptureFixture[str]
) -> None: ...
def test_meta_invalid_command_exits_usage(
    tmp_path: Path, app_env: Callable[..., AppEnv], capsys: CaptureFixture[str]
) -> None: ...
def test_meta_dispatches_python_subcommand(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    app_env: Callable[..., AppEnv],
    no_ensure_python: None,
    mock_logdir: Path,
) -> None: ...
def test_meta_dispatches_uv_subcommand(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    app_env: Callable[..., AppEnv],
    no_ensure_python: None,
    mock_logdir: Path,
    make_pyproject: Callable[..., None],
) -> None: ...
@pytest.mark.parametrize(
    "subcommand",
    [
        "update-lockfile",
        "init",
        "migrate",
        "self-update",
        "reset",
        "version",
        "prepare",
    ],
)
def test_strict_subcommands_reject_unknown_flags(
    subcommand: str,
    tmp_path: Path,
    app_env: Callable[..., AppEnv],
    capsys: CaptureFixture[str],
    mock_logdir: Path,
) -> None: ...
@pytest.mark.parametrize("subcommand", ["run", "uv", "python"])
def test_passthrough_subcommands_forward_unknown_flags(
    subcommand: str,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    app_env: Callable[..., AppEnv],
    capsys: CaptureFixture[str],
    no_ensure_python: None,
    mock_logdir: Path,
) -> None: ...
