# SPDX-FileCopyrightText: 2020 Flying Circus
import subprocess

import pytest

import appenv

"""Tests for cmd() subprocess wrapper."""


# cmd() tests


def test_cmd_with_string_uses_shell():
    result = appenv.cmd("echo hello")
    assert b"hello" in result


def test_cmd_raises_value_error_on_failure():
    with pytest.raises(appenv.CommandError) as exc_info:
        appenv.cmd("exit 1", quiet=True)
    assert exc_info.value.returncode == 1


def test_cmd_with_list_no_shell():
    result = appenv.cmd(["echo", "world"])
    assert b"world" in result


def test_cmd_forwards_explicit_env(monkeypatch):
    """cmd() forwards an explicit env dict to subprocess.check_output."""
    captured: dict = {}

    def mock_check_output(cmd, **kwargs):
        captured.update(kwargs)
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)
    custom_env = {"PATH": "/bin", "FOO": "bar"}
    appenv.cmd(["echo", "hi"], env=custom_env)
    assert captured.get("env") == custom_env


def test_cmd_default_env_is_not_none(monkeypatch):
    """cmd() without env= still passes a non-None dict.

    Forbids the lazy env=None default that silently inherits os.environ —
    every subprocess boundary must be explicit.
    """
    captured: dict = {}

    def mock_check_output(cmd, **kwargs):
        captured.update(kwargs)
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)
    appenv.cmd(["echo", "hi"])
    assert captured.get("env") is not None
    assert isinstance(captured["env"], dict)


def test_cmd_error_output_not_quiet(capsys):
    """Lines 1237-1238: cmd() prints error output when not quiet."""
    with pytest.raises(appenv.CommandError) as exc_info:
        appenv.cmd("exit 42", quiet=False)

    assert exc_info.value.returncode == 42

    captured = capsys.readouterr()
    assert "exit 42" in captured.out
    assert "exit code 42" in captured.out
