# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for logging, console formatting, and help formatter utilities."""

import argparse
import logging

import appenv

from .conftest import strip_ansi_codes


def test_grouped_help_formatter_skips_command_not_in_choices():
    """GroupedHelpFormatter skips commands not in action.choices (branch 68->67)."""
    formatter = appenv.GroupedHelpFormatter(prog="appenv")

    # Create a real argparse parser with subparsers
    parser = argparse.ArgumentParser(prog="appenv")
    subparsers = parser.add_subparsers(dest="command")

    # Add only 'init' and 'update-lockfile' subcommands (not 'migrate')
    subparsers.add_parser("init", help="Initialize project")
    subparsers.add_parser("update-lockfile", help="Update lockfile")
    # Note: 'migrate' is NOT added, though it's in the Project group

    # Get the _SubParsersAction from the parser
    subparsers_action = None
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            subparsers_action = action
            break

    # Skip test if no subparsers action found (shouldn't happen)
    assert subparsers_action is not None

    # Now call the formatter with this action
    result = formatter._format_action(subparsers_action)

    # 'init' and 'update-lockfile' should be in output
    assert "init" in result
    assert "update-lockfile" in result
    # 'migrate' should NOT be in output (it's not in action.choices)
    assert "migrate" not in result
    # Group header should still appear
    assert "Project:" in result


def test_grouped_help_formatter_truncates_long_help():
    """Line 71: GroupedHelpFormatter truncates long help text."""
    formatter = appenv.GroupedHelpFormatter(prog="appenv")

    parser = argparse.ArgumentParser(prog="appenv")
    subparsers = parser.add_subparsers(dest="command")

    # 'init' is in the Project group - give it help text > 50 chars
    long_help = "A" * 60
    subparsers.add_parser("init", help=long_help)

    subparsers_action = None
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            subparsers_action = action
            break

    assert subparsers_action is not None
    result = formatter._format_action(subparsers_action)

    # Help should be truncated to first 47 chars + "..."
    assert "A" * 60 not in result
    assert "A" * 47 + "..." in result


def test_colored_console_formatter_format():
    """ColoredConsoleFormatter renders message + arrow, no caller internals."""

    formatter = appenv.ColoredConsoleFormatter("%(message)s")

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=42,
        msg="test message",
        args=(),
        exc_info=None,
        func="test_func",
    )

    result = formatter.format(record)
    plain = strip_ansi_codes(result)

    # Message is rendered with the visual arrow prefix ...
    assert "test message" in plain
    assert "→" in plain
    # ... and NO funcName:lineno caller detail (that stays in the file log only).
    assert "test_func" not in plain
    assert "42" not in plain


def test_console_diagnostic_filter_hides_internal_diagnostics():
    """Console filter drops logging/argparse internals; keeps operational logs."""

    flt = appenv._ConsoleDiagnosticFilter()

    def make_record(msg: str) -> logging.LogRecord:
        return logging.LogRecord(
            name="appenv",
            level=logging.DEBUG,
            pathname="src/appenv.py",
            lineno=1,
            msg=msg,
            args=(),
            exc_info=None,
            func="f",
        )

    # Internal plumbing: logging setup and argparse Namespace reprs.
    assert (
        flt.filter(make_record("logging-configured: log_file=/x verbose=True")) is False
    )
    assert flt.filter(make_record("parsed-args: args=%s")) is False
    assert flt.filter(make_record("parsed-args-remaining: args=%s")) is False
    # Operational messages users act on pass through untouched.
    assert flt.filter(make_record("uv-cmd-started: args=uv lock")) is True
    assert flt.filter(make_record("creating-venv: python=/x path=/y")) is True


def test_setup_logging_verbose(tmp_path, caplog):
    """setup_logging adds a user-facing console handler when verbose=True."""
    _ = caplog  # Used for capturing logs

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True)

    # Clear any existing handlers (close first to avoid ResourceWarning)
    for handler in appenv.log.handlers[:]:
        handler.close()
    appenv.log.handlers.clear()

    appenv.setup_logging("test", log_dir, verbose=True)

    # Should have file handler and console handler
    assert len(appenv.log.handlers) == 2
    handler_types = {type(h).__name__ for h in appenv.log.handlers}
    assert "TimedRotatingFileHandler" in handler_types
    assert "StreamHandler" in handler_types

    console_handler = next(
        h for h in appenv.log.handlers if type(h).__name__ == "StreamHandler"
    )
    # Console handler renders user-facing output (no caller internals) ...
    assert isinstance(console_handler.formatter, appenv.ColoredConsoleFormatter)
    # ... and hides internal diagnostics while the file log keeps them.
    assert any(
        isinstance(f, appenv._ConsoleDiagnosticFilter) for f in console_handler.filters
    )

    # Close all handlers to avoid resource warnings
    for handler in appenv.log.handlers:
        handler.close()
    appenv.log.handlers.clear()
