# SPDX-FileCopyrightText: 2020 Flying Circus
"""Unit tests for LockFile: read_lockfile_lines, diff_summary, and diff.

LockFile is a self-contained class (src/appenv.py:700) backing the
update-lockfile workflow. Existing coverage in test_update_lockfile.py only
exercises it through AppEnv.update_lockfile() with substring checks. These
tests target the class directly to pin the set/diff semantics and edge cases.
"""

import logging
from pathlib import Path
from typing import cast

import pytest

import appenv

from .conftest import strip_ansi_codes


def _write_old_lockfile(base, content):
    """Create uv.lock + a minimal pyproject.toml so LockFile.diff can copy it."""
    (base / "uv.lock").write_text(content)
    (base / "pyproject.toml").write_text('[project]\nname = "t"\n')


def _mock_uv_lock_writes(make_mock_uv, new_lock_content):
    """Build a mock uv whose `lock` cmd writes new_lock_content into its cwd."""

    def cmd_fn(args, verbose=False, **kwargs):
        if "lock" in args:
            (Path(kwargs["cwd"]) / "uv.lock").write_text(new_lock_content)
        return ""

    return make_mock_uv(cmd_fn=cmd_fn)


# ==============================================================================
# read_lockfile_lines — pure, only needs tmp_path
# ==============================================================================


def test_read_lockfile_lines_strips_and_filters(tmp_path):
    (tmp_path / "uv.lock").write_text("version = 1\n\n# comment\n  pkg = x  \n")
    lockfile = appenv.LockFile(tmp_path)
    assert lockfile.read_lockfile_lines() == {"version = 1", "pkg = x"}


def test_read_lockfile_lines_missing_file(tmp_path):
    lockfile = appenv.LockFile(tmp_path)
    assert lockfile.read_lockfile_lines() == set()


@pytest.mark.characterization
def test_read_lockfile_lines_inline_hash_kept(tmp_path):
    """Characterization: only a LEADING `#` filters a line; inline `#` stays.

    Guards against someone "simplifying" to `line.split("#")[0]`, which would
    drop the inline comment and corrupt the set diff.
    """
    (tmp_path / "uv.lock").write_text("pkg = x # inline\n")
    lockfile = appenv.LockFile(tmp_path)
    assert lockfile.read_lockfile_lines() == {"pkg = x # inline"}


def test_read_lockfile_lines_empty_file(tmp_path):
    (tmp_path / "uv.lock").write_text("")
    lockfile = appenv.LockFile(tmp_path)
    assert lockfile.read_lockfile_lines() == set()


def test_read_lockfile_lines_returns_set(tmp_path):
    (tmp_path / "uv.lock").write_text("version = 1\n")
    lockfile = appenv.LockFile(tmp_path)
    assert isinstance(lockfile.read_lockfile_lines(), set)


# ==============================================================================
# diff_summary — pure set logic; new lockfile written to self.path
# ==============================================================================


@pytest.mark.parametrize(
    ("file_content", "input_set", "expected"),
    [
        ("a\nb\n", {"a", "b"}, "No changes"),
        ("a\nb\n", {"a"}, "\u2713 Updated (+1 / -0 lines)"),
        ("a\n", {"a", "b"}, "\u2713 Updated (+0 / -1 lines)"),
        ("a\nc\n", {"a", "b"}, "\u2713 Updated (+1 / -1 lines)"),
    ],
    ids=["no_changes", "added_only", "removed_only", "both"],
)
def test_diff_summary_updated(tmp_path, file_content, input_set, expected):
    (tmp_path / "uv.lock").write_text(file_content)
    lockfile = appenv.LockFile(tmp_path)
    result = strip_ansi_codes(lockfile.diff_summary(input_set))
    assert result == expected


def test_diff_summary_created(tmp_path):
    (tmp_path / "uv.lock").write_text("a\nb\nc\n")
    lockfile = appenv.LockFile(tmp_path)
    result = strip_ansi_codes(lockfile.diff_summary(set()))
    assert "Created" in result
    assert "+3" in result
    assert "-" not in result


def test_diff_summary_empty_to_empty_reports_no_changes(tmp_path):
    """old empty AND new empty reports "No changes".

    The empty→empty case short-circuits before the "Created" branch, so a
    no-op `uv lock` on a project that never had a lockfile is not advertised
    as "+0 lines created".
    """
    (tmp_path / "uv.lock").write_text("")
    lockfile = appenv.LockFile(tmp_path)
    result = strip_ansi_codes(lockfile.diff_summary(set()))
    assert "No changes" in result


def test_diff_summary_counts_match_set_diff(tmp_path):
    (tmp_path / "uv.lock").write_text("a\nb\nc\nd\n")
    lockfile = appenv.LockFile(tmp_path)
    old = {"a", "b"}
    result = strip_ansi_codes(lockfile.diff_summary(old))
    assert f"+{len(set('abcd') - old)}" in result


# ==============================================================================
# diff — needs a mock uv that writes uv.lock into its cwd (tmpdir)
# ==============================================================================


def test_diff_returns_no_changes_when_identical(tmp_path, make_mock_uv, capsys):
    _write_old_lockfile(tmp_path, "v=1\n")
    uv = _mock_uv_lock_writes(make_mock_uv, "v=1\n")
    lockfile = appenv.LockFile(tmp_path)
    result = lockfile.diff(cast("appenv.UvBin", uv), tmp_path, verbose=False)
    assert result == "No changes"
    assert capsys.readouterr().out == ""


def test_diff_returns_changed_when_modified(tmp_path, make_mock_uv, capsys):
    _write_old_lockfile(tmp_path, "version = 1\n")
    uv = _mock_uv_lock_writes(
        make_mock_uv, "version = 2\n[[package]]\nname = 'click'\n"
    )
    lockfile = appenv.LockFile(tmp_path)
    result = lockfile.diff(cast("appenv.UvBin", uv), tmp_path, verbose=False)
    assert result == "Changed"
    assert "version = 2" in strip_ansi_codes(capsys.readouterr().out)


def test_diff_copies_pyproject_to_tmpdir(tmp_path, make_mock_uv):
    _write_old_lockfile(tmp_path, "v=1\n")
    # diff() runs uv inside a TemporaryDirectory that is deleted on context
    # exit, so we must observe pyproject.toml existence DURING the cmd call.
    pyproject_present: list[bool] = []

    def cmd_fn(args, verbose=False, **kwargs):
        pyproject_present.append((Path(kwargs["cwd"]) / "pyproject.toml").exists())
        # Write a uv.lock so diff() proceeds past the no-output guard
        # (see test_diff_when_uv_produces_no_lockfile_raises).
        (Path(kwargs["cwd"]) / "uv.lock").write_text("v=1\n")
        return ""

    uv = make_mock_uv(cmd_fn=cmd_fn)
    lockfile = appenv.LockFile(tmp_path)
    lockfile.diff(cast("appenv.UvBin", uv), tmp_path, verbose=False)
    assert pyproject_present, "uv lock was never invoked"
    assert pyproject_present[0] is True


def test_diff_does_not_modify_original_lockfile(tmp_path, make_mock_uv):
    original = "version = 1\n"
    _write_old_lockfile(tmp_path, original)
    uv = _mock_uv_lock_writes(make_mock_uv, "version = 2\n[[package]]\n")
    lockfile = appenv.LockFile(tmp_path)
    lockfile.diff(cast("appenv.UvBin", uv), tmp_path, verbose=False)
    assert (tmp_path / "uv.lock").read_text() == original


def test_diff_when_uv_produces_no_lockfile_raises(tmp_path, make_mock_uv, caplog):
    """diff raises CommandError when `uv lock` writes no uv.lock.

    uv exiting 0 without output is a uv bug or a silent network failure; appenv
    fails loudly (CODEX Art. 5) instead of rendering the old lockfile as
    removed. The error is logged before the raise so the failure is traceable.
    """
    _write_old_lockfile(tmp_path, "version = 1\n")
    uv = make_mock_uv(cmd_fn=lambda args, verbose=False, **kwargs: "")
    lockfile = appenv.LockFile(tmp_path)
    with (
        caplog.at_level(logging.ERROR, logger="appenv"),
        pytest.raises(appenv.CommandError),
    ):
        lockfile.diff(cast("appenv.UvBin", uv), tmp_path, verbose=False)
    assert "uv-lock-no-output:" in caplog.text
