# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for gitignore and diff utilities."""

import appenv

from .conftest import strip_ansi_codes


def test_print_colored_diff_returns_true_when_changes(capsys):
    old = "line1\nline2\n"
    new = "line1\nline3\n"

    result = appenv.print_colored_diff(old, new, "old.txt", "new.txt")

    assert result is True
    captured = capsys.readouterr()
    output = strip_ansi_codes(captured.out)

    expected = """\
--- old.txt
+++ new.txt
@@ -1,2 +1,2 @@
 line1
-line2
+line3
"""
    assert output == expected


def test_print_colored_diff_returns_false_when_no_changes(capsys):
    content = "line1\nline2\n"

    result = appenv.print_colored_diff(content, content, "same.txt", "same.txt")

    assert result is False
    captured = capsys.readouterr()
    assert captured.out == ""


def test_ensure_gitignore_returns_early_when_all_entries_exist(tmp_path, capsys):
    """Line 1294: ensure_gitignore returns early when all entries already exist."""
    base = tmp_path

    # Create .gitignore with all the entries we'll pass
    (base / ".gitignore").write_text(".venv\n.appenv\n.batou-lock\n")

    appenv.ensure_gitignore(base, [".venv", ".appenv", ".batou-lock"])

    # Should return early — no "Updated" or "Created" print
    captured = capsys.readouterr()
    assert "Updated" not in captured.out
    assert "Created" not in captured.out

    # File content unchanged
    assert (base / ".gitignore").read_text() == ".venv\n.appenv\n.batou-lock\n"


def test_gitignore_adds_trailing_newline(tmp_path):
    """Existing content without trailing newline gets one added."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("build/")
    appenv.ensure_gitignore(tmp_path, [".appenv/", ".venv/"])
    content = gitignore.read_text()
    assert ".appenv/" in content
    assert "build/" in content


def test_gitignore_existing_updated_message(tmp_path, capsys):
    """Existing gitignore shows 'Updated' message."""
    (tmp_path / ".gitignore").write_text("build/\n")
    appenv.ensure_gitignore(tmp_path, [".appenv/"])
    captured = capsys.readouterr()
    assert "Updated" in captured.out


def test_gitignore_new_created_message(tmp_path, capsys):
    """New gitignore shows 'Created' message."""
    appenv.ensure_gitignore(tmp_path, [".appenv/"])
    captured = capsys.readouterr()
    assert "Created" in captured.out
