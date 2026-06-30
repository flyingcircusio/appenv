import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest
from pytest import CaptureFixture, LogCaptureFixture, MonkeyPatch
from pytest_patterns.plugin import PatternsLib

from appenv import AppEnv

def test_init_fresh_start_interactive(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    patterns: PatternsLib,
) -> None: ...
def test_init_fresh_start_explicit_dependency(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_init_unlink_broken_symlink(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_init_refuses_existing_project_section(
    workdir: Path,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    patterns: PatternsLib,
) -> None: ...
@pytest.mark.parametrize("command_name", ["app", ""])
def test_init_empty_command_name_defaults_to_app(
    command_name: str,
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_init_with_path_creates_directory(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_init_with_path_shows_relative_symlink_path(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
@pytest.mark.parametrize(
    ("path", "command_name", "pre_create"),
    [
        pytest.param("some/nested/path", "nestedapp", False, id="nested"),
        pytest.param("existing", "existingapp", True, id="pre-existing"),
    ],
)
def test_init_with_path_creates_or_uses_directory(
    path: str,
    command_name: str,
    pre_create: bool,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_init_without_path_uses_current_directory(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_init_appenv_script_already_exists(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_init_warns_on_version_mismatch(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_init_existing_pyproject_no_project_section(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_init_binary_without_dep_new_project(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None: ...
@pytest.mark.parametrize(
    ("binary", "dangerous"),
    [("../escape", "../escape"), ("/etc/evil", "/etc/evil")],
    ids=["path-traversal", "absolute"],
)
def test_init_rejects_non_bare_binary_name(
    binary: str,
    dangerous: str,
    workdir: Path,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    patterns: PatternsLib,
) -> None: ...
@pytest.mark.parametrize("kind", ["user-file", "foreign-symlink"])
def test_init_refuses_to_clobber_non_appenv_entry(
    kind: str,
    workdir: Path,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    patterns: PatternsLib,
) -> None: ...
def test_init_relinks_existing_appenv_symlink(
    workdir: Path, capsys: CaptureFixture[str], app_env: Callable[..., AppEnv]
) -> None: ...
def test_init_relinks_broken_symlink_at_target(
    workdir: Path, capsys: CaptureFixture[str], app_env: Callable[..., AppEnv]
) -> None: ...
def test_init_dedupes_duplicate_deps_noninteractive(
    workdir: Path, app_env: Callable[..., AppEnv]
) -> None: ...
@pytest.mark.parametrize(
    "binary",
    [
        pytest.param("my binary", id="space-in-name"),
        pytest.param("rm -rf", id="space-in-name-shell-token"),
    ],
)
def test_init_rejects_binary_name_with_whitespace(
    binary: str,
    workdir: Path,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_init_rejects_empty_binary_name(
    workdir: Path, capsys: CaptureFixture[str], app_env: Callable[..., AppEnv]
) -> None: ...
def test_init_rejects_empty_dependency(
    workdir: Path,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    mock_uv_lock: None,
) -> None: ...
@pytest.mark.parametrize(
    ("exc", "expected_raises", "check_log"),
    [
        pytest.param(
            subprocess.CalledProcessError(returncode=1, cmd=["uv", "lock"]),
            subprocess.CalledProcessError,
            True,
            id="lock-failure",
        ),
        pytest.param(
            KeyboardInterrupt(), KeyboardInterrupt, False, id="keyboard-interrupt"
        ),
    ],
)
def test_init_restores_pyproject_on_failure(
    exc: BaseException,
    expected_raises: type[BaseException],
    check_log: bool,
    workdir: Path,
    capsys: CaptureFixture[str],
    caplog: LogCaptureFixture,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_init_deletes_partial_state_on_lock_failure(
    workdir: Path,
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_init_keeps_preexisting_command_link_on_lock_failure(
    workdir: Path,
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_init_non_interactive_no_existing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None: ...
def test_init_no_tty_exits(
    tmp_path: Path, monkeypatch: MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None: ...
def test_init_interactive_new_with_deps_and_binary(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None: ...
def test_init_interactive_new_default_binary(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None: ...
def test_init_interactive_eof_exits_64_new(
    tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None: ...
