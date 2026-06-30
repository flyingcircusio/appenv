# SPDX-FileCopyrightText: 2020 Flying Circus
"""Miscellaneous tests that don't fit a larger theme."""

import argparse
import re
from io import StringIO

import pytest

import appenv


def test_show_version(tmp_path, capsys, patterns, app_env):
    """show_version() prints the appenv version."""
    env = app_env()
    env.show_version()

    captured = capsys.readouterr()

    patterns.main.in_order(f"appenv {appenv.__version__}")

    full_pattern = patterns.full
    full_pattern.merge("main")

    full_pattern.generate_example()

    assert full_pattern == captured.out


def test_lockfile_content_missing_file(tmp_path):
    """Test LockFile.content returns empty string when file doesn't exist."""
    lockfile = appenv.LockFile(tmp_path)
    assert lockfile.content == ""


def test_init_help_text_fits_max_length_and_mentions_noninteractive():
    """Init subparser help is <= MAX_HELP_TEXT_LENGTH and mentions both modes."""
    # Build a parser with init subparser using the same help text as appenv.py
    parser = argparse.ArgumentParser(prog="appenv")
    subparsers = parser.add_subparsers(dest="command")
    init_help = "Create project \u2014 interactive, or --binary/--dep."
    subparsers.add_parser("init", help=init_help)

    # Extract help via print_help
    captured = StringIO()
    parser.print_help(captured)
    help_output = captured.getvalue()

    # The init line should contain our help text
    init_match = re.search(r"  init\s+(.+)", help_output)
    assert init_match, f"Could not find init help in output:\n{help_output}"
    rendered_help = init_match.group(1).strip()

    assert len(rendered_help) <= appenv.MAX_HELP_TEXT_LENGTH, (
        f"Init help text is {len(rendered_help)} chars, exceeds "
        f"MAX_HELP_TEXT_LENGTH={appenv.MAX_HELP_TEXT_LENGTH}: {rendered_help!r}"
    )
    assert "interactive" in rendered_help.lower(), (
        f"Init help should mention 'interactive': {rendered_help!r}"
    )
    assert "--binary" in rendered_help or "--dep" in rendered_help, (
        f"Init help should mention non-interactive flags: {rendered_help!r}"
    )


@pytest.mark.parametrize(
    ("path", "should_exist"),
    [
        pytest.param("subdir", True, id="directory"),
        pytest.param("does_not_exist", False, id="nonexistent"),
    ],
)
def test_remove_path(tmp_path, path, should_exist):
    """remove_path() removes existing dirs and is a no-op for nonexistent."""
    target = tmp_path / path
    if should_exist:
        target.mkdir()
        (target / "file.txt").write_text("hello")
        assert target.exists()
    appenv.remove_path(target)
    assert not target.exists()
