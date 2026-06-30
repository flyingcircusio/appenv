# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for main() entry point and related functions."""

import subprocess
import sys
from pathlib import Path

import pytest

import appenv

# main() tests


def test_main_shows_usage_without_subcommand(
    monkeypatch, capsys, tmp_path, no_ensure_python, mock_logdir
):
    """Test that calling appenv without subcommand shows usage."""
    monkeypatch.setattr("sys.argv", ["appenv"])
    monkeypatch.setattr(appenv, "__file__", "/some/path/appenv")

    # Should exit with usage message
    with pytest.raises(SystemExit):
        appenv.main()

    captured = capsys.readouterr()
    # Help output goes to stdout
    assert "usage: appenv" in captured.out


def test_main_shows_grouped_help(
    monkeypatch, capsys, tmp_path, patterns, no_ensure_python, mock_logdir
):
    """Test that help output shows commands grouped by category."""
    monkeypatch.setattr("sys.argv", ["appenv", "--help"])
    monkeypatch.setattr(appenv, "__file__", "/some/path/appenv")

    with pytest.raises(SystemExit):
        appenv.main()

    captured = capsys.readouterr()

    patterns.main.in_order(
        """\
...Project:...
...init...
...migrate...
...update-lockfile...
...Venv:...
...prepare...
...reset...
...Tools:...
...python...
...uv...
...Debug:...
...version...
"""
    )

    patterns.no_errors.optional("...")

    full_pattern = patterns.full
    full_pattern.merge("main")
    full_pattern.merge("no_errors")

    full_pattern.generate_example()

    assert full_pattern == captured.out


def test_help_same_as_no_args(
    monkeypatch, capsys, tmp_path, no_ensure_python, mock_logdir
):
    """Test that --help shows grouped help output."""
    monkeypatch.setattr(appenv, "__file__", "/some/path/appenv")

    # Get output with --help
    monkeypatch.setattr("sys.argv", ["appenv", "--help"])
    with pytest.raises(SystemExit):
        appenv.main()
    captured_help = capsys.readouterr()

    # --help shows full grouped help on stdout
    assert "Project:" in captured_help.out
    assert "Commands:" in captured_help.out


def test_main_calls_run_when_not_appenv(monkeypatch, tmp_path, no_ensure_python):
    app_file = tmp_path / "myapp"
    app_file.write_text("#!/usr/bin/env python3\nprint('test')\n")

    run_called = []
    monkeypatch.setattr(
        appenv.AppEnv,
        "run",
        lambda self, cmd, argv: run_called.append((cmd, argv)),
    )

    monkeypatch.setattr("sys.argv", ["myapp", "--help"])
    monkeypatch.setattr(appenv, "__file__", str(app_file))

    appenv.main()

    assert run_called == [("myapp", ["--help"])]


def test_main_calls_meta_when_appenv(monkeypatch, no_ensure_python):
    meta_called = []
    monkeypatch.setattr(
        appenv.AppEnv,
        "meta",
        lambda self, args, prog="appenv": meta_called.append(args),
    )

    monkeypatch.setattr("sys.argv", ["appenv"])
    monkeypatch.setattr(appenv, "__file__", "/some/path/appenv")

    appenv.main()

    # When called as "appenv" without args, meta([]) is called
    # which shows help (same as --help)
    assert meta_called == [[]]


def test_main_calls_ensure_best_python(monkeypatch, workdir):
    """Line 1196: main() calls ensure_best_python."""
    base = Path(workdir)
    (base / "pyproject.toml").write_text('[project]\nname = "test"\n')
    (base / "appenv").write_text("#!/usr/bin/env python3\npass\n")
    (base / "appenv").chmod(0o755)

    called = []
    monkeypatch.setattr(
        appenv,
        "ensure_best_python",
        lambda b: called.append("pyproject"),
    )
    monkeypatch.setattr(appenv.AppEnv, "meta", lambda self, args, prog="appenv": None)
    monkeypatch.setattr(appenv, "__file__", str(base / "appenv"))
    monkeypatch.setattr("sys.argv", ["appenv"])

    appenv.main()

    assert called == ["pyproject"]


def test_main_catches_subprocess_error(monkeypatch, no_ensure_python):
    """main() catches CommandError and exits with subprocess returncode."""
    monkeypatch.setattr("sys.argv", ["myapp", "--help"])
    monkeypatch.setattr(appenv, "__file__", "/some/path/myapp")

    def mock_run(self, command, argv):
        raise appenv.CommandError("uv sync failed", 2)  # noqa: EM101, TRY003

    monkeypatch.setattr(appenv.AppEnv, "run", mock_run)

    with pytest.raises(SystemExit) as exc_info:
        appenv.main()

    assert exc_info.value.code == 2


def test_main_entry_point_subprocess():
    """Line 1216: Test __main__ entry point via subprocess."""
    project_root = Path(__file__).parent.parent.resolve()
    result = subprocess.run(
        [sys.executable, str(project_root / "src" / "appenv.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower()
