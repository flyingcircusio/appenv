from pathlib import Path

from pytest import CaptureFixture

def test_print_colored_diff_returns_true_when_changes(
    capsys: CaptureFixture[str],
) -> None: ...
def test_print_colored_diff_returns_false_when_no_changes(
    capsys: CaptureFixture[str],
) -> None: ...
def test_ensure_gitignore_returns_early_when_all_entries_exist(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None: ...
def test_gitignore_adds_trailing_newline(tmp_path: Path) -> None: ...
def test_gitignore_existing_updated_message(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None: ...
def test_gitignore_new_created_message(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None: ...
