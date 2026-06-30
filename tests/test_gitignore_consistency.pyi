from collections.abc import Callable
from pathlib import Path

from pytest import MonkeyPatch

from appenv import AppEnv

EXPECTED_GITIGNORE_ENTRIES: list[str]

def test_module_exposes_gitignore_entries_constant() -> None: ...
def test_init_writes_gitignore_entries(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    mock_uv_lock: None,
) -> None: ...
def test_migrate_writes_gitignore_entries(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    mock_uv_lock: None,
) -> None: ...
def test_init_and_migrate_write_identical_gitignore(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    mock_uv_lock: None,
) -> None: ...
def test_init_and_migrate_share_gitignore_entries_constant(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    mock_uv_lock: None,
) -> None: ...
