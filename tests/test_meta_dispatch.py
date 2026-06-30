# SPDX-FileCopyrightText: 2020 Flying Circus
import os

import pytest

import appenv

from .conftest import MockUvBin

"""Tests for AppEnv.meta() dispatch and subcommand strictness."""


# meta() tests


def test_meta_calls_reset(monkeypatch, tmp_path, app_env):
    env = app_env()
    monkeypatch.setattr("sys.argv", ["appenv", "reset"])

    reset_called = []
    monkeypatch.setattr(
        env, "reset", lambda args=None, remaining=None: reset_called.append(True)
    )

    env.meta()

    assert reset_called == [True]


def test_meta_calls_prepare(monkeypatch, tmp_path, app_env):
    env = app_env()
    monkeypatch.setattr("sys.argv", ["appenv", "prepare"])

    prepare_called = []
    monkeypatch.setattr(
        env,
        "prepare",
        lambda args=None, remaining=None: prepare_called.append(True),
    )

    env.meta()

    assert prepare_called == [True]


def test_meta_calls_python(monkeypatch, tmp_path, app_env):
    env = app_env()
    monkeypatch.setattr("sys.argv", ["appenv", "python"])

    python_called = []
    monkeypatch.setattr(
        env,
        "python",
        lambda args, remaining: python_called.append((args, remaining)),
    )

    env.meta()

    assert len(python_called) == 1


def test_meta_calls_run_script(monkeypatch, tmp_path, app_env):
    env = app_env()
    monkeypatch.setattr("sys.argv", ["appenv", "run", "myscript"])

    run_called = []
    monkeypatch.setattr(
        env,
        "run_script",
        lambda args, remaining: run_called.append((args, remaining)),
    )

    env.meta()

    assert len(run_called) == 1
    assert run_called[0][1] == ["myscript"]


def test_meta_unrecognized_arguments(tmp_path, app_env, capsys):
    """Lines 791-793: meta() exits with USAGE on unrecognized arguments."""
    env = app_env()

    with pytest.raises(SystemExit) as exc_info:
        env.meta(remaining_args=["--totally-bogus-flag"])

    assert exc_info.value.code == appenv.EXIT_CODE_USAGE
    captured = capsys.readouterr()
    assert "Error: unrecognized arguments: --totally-bogus-flag" in captured.out


def test_meta_invalid_command_exits_usage(tmp_path, app_env, capsys):
    """Invalid subcommand name exits with EXIT_CODE_USAGE, not argparse's 2."""
    env = app_env()

    with pytest.raises(SystemExit) as exc_info:
        env.meta(remaining_args=["boguscommand"])

    assert exc_info.value.code == appenv.EXIT_CODE_USAGE
    captured = capsys.readouterr()
    assert "invalid choice" in captured.err
    assert "boguscommand" in captured.err


# python and uv subcommand dispatch tests


def test_meta_dispatches_python_subcommand(
    monkeypatch, tmp_path, app_env, no_ensure_python, mock_logdir
):
    """meta() dispatches 'python' subcommand to python() which calls run()."""
    monkeypatch.setattr("sys.argv", ["appenv", "python", "-c", "print(1)"])

    env = app_env()
    run_called = []
    monkeypatch.setattr(env, "run", lambda cmd, argv: run_called.append((cmd, argv)))

    env.meta()

    assert run_called == [("python", ["-c", "print(1)"])]


def test_meta_dispatches_uv_subcommand(
    monkeypatch, tmp_path, app_env, no_ensure_python, mock_logdir, make_pyproject
):
    """meta() dispatches 'uv' subcommand to run_uv() which execs uv binary."""
    monkeypatch.setattr("sys.argv", ["appenv", "uv", "pip", "list"])
    monkeypatch.delenv("UV_PROJECT_ENVIRONMENT", raising=False)

    make_pyproject(tmp_path, '[project]\nname = "test"\n')
    env = app_env(tmp_path)
    mock_uv = MockUvBin()
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: mock_uv)

    execve_called = []
    monkeypatch.setattr(
        os,
        "execve",
        lambda path, argv, env_dict: execve_called.append((path, argv, env_dict)),
    )
    monkeypatch.setattr(os, "chdir", lambda d: None)

    env.meta()

    assert len(execve_called) == 1
    path, argv, env_dict = execve_called[0]
    assert "uv" in path
    assert "pip" in argv
    assert "list" in argv
    # UV_PROJECT_ENVIRONMENT is in the env dict, not in os.environ
    assert env_dict.get("UV_PROJECT_ENVIRONMENT") == str(env.venv_real)
    assert os.environ.get("UV_PROJECT_ENVIRONMENT") is None


# ==============================================================================
# argparse post-parse strictness (fix-contract-treue::post-parse-strictness)
# ==============================================================================


@pytest.mark.parametrize(
    "subcommand",
    [
        "update-lockfile",
        "init",
        "migrate",
        "self-update",
        "reset",
        "version",
        "prepare",
    ],
)
def test_strict_subcommands_reject_unknown_flags(
    subcommand, tmp_path, app_env, capsys, mock_logdir
):
    """Non-passthrough subcommands exit 64 on unrecognized flags.

    Verifies fix-contract-treue::post-parse-strictness: these subcommands own
    their argument surface, so leftover flags are usage errors, not silently
    swallowed before dispatch.
    """
    env = app_env(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        env.meta(remaining_args=[subcommand, "--totally-unknown-flag"])

    assert exc_info.value.code == appenv.EXIT_CODE_USAGE
    captured = capsys.readouterr()
    assert "unrecognized arguments: --totally-unknown-flag" in captured.err


@pytest.mark.parametrize("subcommand", ["run", "uv", "python"])
def test_passthrough_subcommands_forward_unknown_flags(
    subcommand, monkeypatch, tmp_path, app_env, capsys, no_ensure_python, mock_logdir
):
    """Passthrough subcommands forward unknown flags to the wrapped tool.

    Verifies fix-contract-treue::post-parse-strictness preserves the passthrough
    contract (commands.md; fix-help-passthrough): run/uv/python must not reject
    flags they don't understand — those belong to the wrapped tool.
    """
    env = app_env(tmp_path)

    forwarded: list[str] = []

    def capture_run(cmd, argv):
        forwarded.append(cmd)
        forwarded.extend(argv)

    def capture_run_uv(_args, remaining):
        forwarded.extend(remaining)

    monkeypatch.setattr(env, "run", capture_run)
    monkeypatch.setattr(env, "run_uv", capture_run_uv)

    env.meta(remaining_args=[subcommand, "--forwarded-flag"])

    assert "--forwarded-flag" in forwarded
    captured = capsys.readouterr()
    assert "unrecognized arguments" not in captured.err
    assert "unrecognized arguments" not in captured.out
