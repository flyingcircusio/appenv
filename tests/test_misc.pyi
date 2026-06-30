from collections.abc import Callable
from pathlib import Path

from pytest import CaptureFixture
from pytest_patterns.plugin import PatternsLib

from appenv import AppEnv

def test_show_version(
    tmp_path: Path,
    capsys: CaptureFixture[str],
    patterns: PatternsLib,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_lockfile_content_missing_file(tmp_path: Path) -> None: ...
def test_init_help_text_fits_max_length_and_mentions_noninteractive() -> None: ...
def test_remove_path(tmp_path: Path, path: str, should_exist: bool) -> None: ...
