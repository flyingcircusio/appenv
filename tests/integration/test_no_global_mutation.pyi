from collections.abc import Callable
from pathlib import Path

from pytest import MonkeyPatch

from appenv import AppEnv
from tests.conftest import MockUvBin

def test_no_global_mutation_run_uv_leaves_uv_project_env_alone(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    app_env: Callable[..., AppEnv],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_no_global_mutation_prepare_leaves_uv_project_env_alone(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    mock_uv: MockUvBin,
    mock_cmd_python: None,
    make_pyproject: Callable[..., None],
    make_venv_creating_cmd: Callable[..., Callable[..., str]],
) -> None: ...
def test_no_global_mutation_main_does_not_pop_pythonpath(
    monkeypatch: MonkeyPatch, no_ensure_python: None, mock_logdir: Path
) -> None: ...
def test_no_global_mutation_run_leaves_appenv_basedir_alone(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    app_env: Callable[..., AppEnv],
    make_pyproject: Callable[..., None],
) -> None: ...
