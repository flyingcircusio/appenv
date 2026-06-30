from collections.abc import Callable
from pathlib import Path

import pytest
from pytest import CaptureFixture, LogCaptureFixture, MonkeyPatch
from pytest_patterns.plugin import PatternsLib

from appenv import AppEnv
from tests.conftest import MockUvBin

def test_prepare_creates_envdir_and_venv_symlink(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    mock_uv: MockUvBin,
    mock_cmd_python: None,
    make_pyproject: Callable[..., None],
    make_venv_creating_cmd: Callable[..., Callable[..., str]],
) -> None: ...
def test_prepare_syncs_with_frozen_flag(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    mock_uv: MockUvBin,
    mock_cmd_python: None,
    make_pyproject: Callable[..., None],
    make_venv_creating_cmd: Callable[..., Callable[..., str]],
) -> None: ...
def test_prepare_verbose_output(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    patterns: PatternsLib,
    app_env: Callable[..., AppEnv],
    mock_uv: MockUvBin,
    mock_cmd_python: None,
    make_pyproject: Callable[..., None],
    make_venv_creating_cmd: Callable[..., Callable[..., str]],
    capture_appenv_logs: None,
) -> None: ...
def test_prepare_pyproject_mode_verbose(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    patterns: PatternsLib,
    app_env: Callable[..., AppEnv],
    mock_uv: MockUvBin,
    mock_cmd_python: None,
    make_pyproject: Callable[..., None],
    make_venv_creating_cmd: Callable[..., Callable[..., str]],
    capture_appenv_logs: None,
) -> None: ...
def test_prepare_pyproject_unlink_file_in_appenv(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    patterns: PatternsLib,
    app_env: Callable[..., AppEnv],
    make_pyproject: Callable[..., None],
    capture_appenv_logs: None,
) -> None: ...
def test_update_lockfile_exits_67_no_project(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_prepare_pyproject_cleanup_old_appenv(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_prepare_pyproject_removes_symlink_in_appenv(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    caplog: LogCaptureFixture,
    app_env: Callable[..., AppEnv],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_prepare_pyproject_keeps_appenv_if_requirements_exists(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_prepare_exits_without_project_files(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_prepare_pyproject_missing_uv_lock(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_prepare_pyproject_corrupted_venv(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    mock_uv: MockUvBin,
    make_pyproject: Callable[..., None],
) -> None: ...
def test_prepare_pyproject_does_not_leak_uv_project_environment(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_prepare_pyproject_updates_broken_symlink(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_prepare_pyproject_keeps_real_venv_directory(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_prepare_pyproject_keeps_dot_uv_dir(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    make_pyproject: Callable[..., None],
) -> None: ...
@pytest.mark.parametrize(
    ("writes_pyproject", "expected"),
    [
        pytest.param(True, True, id="pyproject"),
        pytest.param(False, False, id="none"),
    ],
)
def test_detect_project_type(
    tmp_path: Path, monkeypatch: MonkeyPatch, writes_pyproject: bool, expected: bool
) -> None: ...
def test_prepare_venv_replaces_current_symlink(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    make_mock_uv: Callable[..., MockUvBin],
    mock_cmd_python: None,
    make_pyproject: Callable[..., None],
    make_venv_creating_cmd: Callable[..., Callable[..., str]],
) -> None: ...
def test_prepare_venv_existing_venv(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    make_mock_uv: Callable[..., MockUvBin],
    mock_cmd_python: None,
    create_venv: Callable[..., Path],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_prepare_venv_current_is_directory(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    make_mock_uv: Callable[..., MockUvBin],
    mock_cmd_python: None,
    create_venv: Callable[..., Path],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_stale_venv_broken_python(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    mock_uv: MockUvBin,
    create_venv: Callable[..., Path],
    make_pyproject: Callable[..., None],
    make_venv_creating_cmd: Callable[..., Callable[..., str]],
) -> None: ...
def test_stale_venv_version_mismatch(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    mock_uv: MockUvBin,
    create_venv: Callable[..., Path],
    make_pyproject: Callable[..., None],
    make_venv_creating_cmd: Callable[..., Callable[..., str]],
) -> None: ...
def test_stale_venv_max_version_constraint(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    mock_uv: MockUvBin,
    create_venv: Callable[..., Path],
    make_pyproject: Callable[..., None],
    make_venv_creating_cmd: Callable[..., Callable[..., str]],
) -> None: ...
def test_extras_sync_args(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    mock_uv: MockUvBin,
    mock_cmd_python: None,
    make_pyproject: Callable[..., None],
    make_venv_creating_cmd: Callable[..., Callable[..., str]],
) -> None: ...
def test_prepare_venv_link_is_symlink_survives_unlink(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    mock_cmd_python: None,
    create_venv: Callable[..., Path],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_prepare_removes_legacy_current_symlink(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    mock_uv: MockUvBin,
    mock_cmd_python: None,
    make_pyproject: Callable[..., None],
    make_venv_creating_cmd: Callable[..., Callable[..., str]],
) -> None: ...
@pytest.mark.parametrize(
    ("command", "args"),
    [
        pytest.param("run_uv", ["pip", "install", "foo"], id="run_uv"),
        pytest.param("run_script", ["pytest"], id="run_script"),
    ],
)
def test_command_exits_67_no_pyproject(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    command: str,
    args: list[str],
) -> None: ...
