from collections.abc import Callable
from pathlib import Path

import pytest
from pytest import CaptureFixture, MonkeyPatch
from pytest_patterns.plugin import PatternsLib

from appenv import AppEnv
from tests.conftest import MockUvBin

def _setup_pyproject_project(
    workdir: Path, name: str = ..., deps: list[str] | None = ...
) -> Path: ...
def test_update_lockfile_pyproject_workflow(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    mock_uv: MockUvBin,
    app_env: Callable[..., AppEnv],
    patterns: PatternsLib,
) -> None: ...
@pytest.mark.parametrize("diff,verbose", [(False, False), (False, True), (True, False)])
def test_update_lockfile_no_changes(
    diff: bool,
    verbose: bool,
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    make_pyproject: Callable[..., None],
    mock_uv: MockUvBin,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_update_lockfile_pyproject_diff_mode(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    make_pyproject: Callable[..., None],
    mock_uv: MockUvBin,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_update_lockfile_pyproject_updated(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    make_pyproject: Callable[..., None],
    mock_uv: MockUvBin,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_update_lockfile_pyproject_diff_verbose(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    make_pyproject: Callable[..., None],
    mock_uv: MockUvBin,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_update_lockfile_pyproject_calls_uv_lock(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    make_pyproject: Callable[..., None],
    mock_uv: MockUvBin,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_update_lockfile_verbose_shows_running_uv_lock(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    make_pyproject: Callable[..., None],
    app_env: Callable[..., AppEnv],
) -> None: ...
