from collections.abc import Callable
from pathlib import Path

import pytest
from pytest import CaptureFixture, MonkeyPatch
from pytest_patterns.plugin import PatternsLib

from appenv import AppEnv

def test_run_sets_env_and_execs(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    app_env: Callable[..., AppEnv],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_run_missing_binary_shows_helpful_error(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    patterns: PatternsLib,
) -> None: ...
def test_run_missing_binary_empty_venv(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_run_uv_sets_environment_and_execs(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    app_env: Callable[..., AppEnv],
    no_ensure_python: None,
    mock_logdir: Path,
    make_pyproject: Callable[..., None],
) -> None: ...
@pytest.mark.parametrize(
    "remaining_args",
    [
        ["-c", "print(1)"],
        ["-m", "pdb", "script.py"],
    ],
)
def test_python_delegates_to_run(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    app_env: Callable[..., AppEnv],
    remaining_args: list[str],
) -> None: ...
def test_run_script_delegates(
    monkeypatch: MonkeyPatch, tmp_path: Path, app_env: Callable[..., AppEnv]
) -> None: ...
