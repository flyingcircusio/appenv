from pathlib import Path

from pytest import CaptureFixture, MonkeyPatch
from pytest_patterns.plugin import PatternsLib

def test_main_shows_usage_without_subcommand(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    tmp_path: Path,
    no_ensure_python: None,
    mock_logdir: Path,
) -> None: ...
def test_main_shows_grouped_help(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    tmp_path: Path,
    patterns: PatternsLib,
    no_ensure_python: None,
    mock_logdir: Path,
) -> None: ...
def test_help_same_as_no_args(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    tmp_path: Path,
    no_ensure_python: None,
    mock_logdir: Path,
) -> None: ...
def test_main_calls_run_when_not_appenv(
    monkeypatch: MonkeyPatch, tmp_path: Path, no_ensure_python: None
) -> None: ...
def test_main_calls_meta_when_appenv(
    monkeypatch: MonkeyPatch, no_ensure_python: None
) -> None: ...
def test_main_calls_ensure_best_python(
    monkeypatch: MonkeyPatch, workdir: Path
) -> None: ...
def test_main_catches_subprocess_error(
    monkeypatch: MonkeyPatch, no_ensure_python: None
) -> None: ...
def test_main_entry_point_subprocess() -> None: ...
