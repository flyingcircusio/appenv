from collections.abc import Callable
from pathlib import Path

import pytest
from pytest import CaptureFixture, LogCaptureFixture, MonkeyPatch

@pytest.fixture
def capture_execve(monkeypatch: MonkeyPatch) -> list[tuple[str, object, object]]: ...
def test_ensure_best_python_skips_when_env_set(
    tmp_path: Path, monkeypatch: MonkeyPatch, make_pyproject: Callable[..., None]
) -> None: ...
def test_ensure_best_python_already_running_best(
    tmp_path: Path, monkeypatch: MonkeyPatch, make_pyproject: Callable[..., None]
) -> None: ...
def test_ensure_best_python_execv_with_correct_args(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    make_pyproject: Callable[..., None],
    capture_execve: list[tuple[str, object, object]],
) -> None: ...
def test_ensure_best_python_respects_upper_bound(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    make_pyproject: Callable[..., None],
    capture_execve: list[tuple[str, object, object]],
) -> None: ...
def test_ensure_best_python_exits_65_no_python_found(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    capsys: CaptureFixture[str],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_ensure_best_python_exits_65_with_upper_bound(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    capsys: CaptureFixture[str],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_ensure_best_python_default_min_version(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    make_pyproject: Callable[..., None],
    capture_execve: list[tuple[str, object, object]],
) -> None: ...
def test_ensure_best_python_broken_python(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    make_pyproject: Callable[..., None],
    capture_execve: list[tuple[str, object, object]],
) -> None: ...
def test_no_compatible_python_not_leaked_to_verbose_stdout(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    capsys: CaptureFixture[str],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_ensure_best_python_skips_in_venv_with_compatible_python(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    make_pyproject: Callable[..., None],
    capture_execve: list[tuple[str, object, object]],
) -> None: ...
def test_ensure_best_python_searches_in_venv_with_incompatible_python(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    make_pyproject: Callable[..., None],
    capture_execve: list[tuple[str, object, object]],
) -> None: ...
def test_ensure_best_python_exits_in_venv_when_no_compatible_python(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    make_pyproject: Callable[..., None],
) -> None: ...
def test_ensure_best_python_already_running_best_logs(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    caplog: LogCaptureFixture,
    make_pyproject: Callable[..., None],
) -> None: ...
