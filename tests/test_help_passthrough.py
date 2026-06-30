# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for --help pass-through on the run/uv/python subcommands.

Verification for fix-help-passthrough.md: the `run`, `uv`, and `python`
subparsers exist only to delegate to a wrapped tool (uv run / uv / python),
so `--help` must fall through `parse_known_args` into `remaining` and reach
the wrapped tool instead of being swallowed by argparse's auto-added
`-h/--help` (which prints appenv's own empty `usage: appenv <cmd> [-h]`).
Subparsers that own their flags, like `init`, keep their own `--help`.
"""

import pytest


@pytest.mark.parametrize(
    ("delegate_method", "remaining_args", "expected_remaining", "usage_not_in"),
    [
        pytest.param(
            "run_uv",
            ["run", "--help"],
            ["run", "--help"],
            "usage: appenv run",
            id="run_help_routes_to_uv_run",
        ),
        pytest.param(
            "run_uv",
            ["uv", "--help"],
            ["--help"],
            "usage: appenv uv",
            id="uv_help_routes_to_uv",
        ),
        pytest.param(
            "run",
            ["python", "--help"],
            ["--help"],
            "usage: appenv python",
            id="python_help_routes_to_python",
        ),
    ],
)
def test_help_routes_to_delegate(
    monkeypatch,
    app_env,
    capsys,
    no_ensure_python,
    mock_logdir,
    delegate_method,
    remaining_args,
    expected_remaining,
    usage_not_in,
):
    """Parametrized: verify --help pass-through for delegated subcommands.

    ``appenv run --help``, ``appenv uv --help``, and ``appenv python --help``
    must forward --help to the wrapped tool (uv run, uv, python) instead of
    being swallowed by argparse's auto-added ``-h/--help``.
    """
    env = app_env()

    calls: list = []
    monkeypatch.setattr(env, delegate_method, lambda *a, **kw: calls.append(a))

    env.meta(remaining_args=remaining_args)

    captured = capsys.readouterr()

    assert calls
    _, remaining = calls[0]
    assert remaining == expected_remaining
    assert usage_not_in not in captured.out


def test_init_help_keeps_appenv_init_help(
    app_env, capsys, no_ensure_python, mock_logdir
):
    """`appenv init --help` still prints appenv's own init help (unchanged).

    init owns its flags and does not pass args through, so argparse keeps
    its auto-added --help — the fix must not touch non-passthrough subparsers.
    """
    env = app_env()

    with pytest.raises(SystemExit) as exc_info:
        env.meta(remaining_args=["init", "--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    # Python <3.14 renders "usage: appenv <COMMAND> init [-h] ..." (subparsers
    # title placeholder leaks into the usage line); Python 3.14+ collapses
    # it to "usage: appenv init ...". Both forms prove init's own subparser
    # help fired (NOT delegated to uv/python).
    assert "usage:" in captured.out
    assert "init" in captured.out
    assert "--binary" in captured.out
    assert "--python-version" in captured.out
