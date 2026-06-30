# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for _uv_sync and related uv sync functionality."""

from pathlib import Path
from typing import cast

import pytest

import appenv


def test_uv_sync_with_extras(tmp_path, monkeypatch, make_mock_uv):
    """Line 1087: _uv_sync with extras setting."""
    # Create settings with extras
    settings = appenv.AppEnvSettings(
        verbose=False,
        extras=["dev", "test"],
        basedir=tmp_path,
    )
    env = appenv.AppEnv(Path.cwd(), settings)

    # Mock uv.cmd to capture sync args
    sync_calls = []

    uv = make_mock_uv(
        cmd_fn=lambda args, **kwargs: sync_calls.append(list(args)) or "",
    )
    env._uv_sync(dev_mode=True, uv=cast("appenv.UvBin", uv))

    # Verify extras were added to sync command
    assert len(sync_calls) == 1
    sync_args = sync_calls[0]
    assert "--extra" in sync_args
    extra_idx = sync_args.index("--extra")
    assert sync_args[extra_idx + 1] == "dev,test"


def test_uv_sync_stale_lockfile_exits(tmp_path, monkeypatch, make_mock_uv, capsys):
    """_uv_sync exits when lock --check detects stale lockfile."""
    settings = appenv.AppEnvSettings(
        verbose=False,
        extras=[],
        basedir=tmp_path,
    )
    env = appenv.AppEnv(Path.cwd(), settings)

    stale_lockfile_msg = "lockfile needs to be updated"

    def mock_cmd(args, **kwargs):
        if args[:2] == ["lock", "--check"]:
            raise appenv.CommandError(stale_lockfile_msg, 1)
        return ""

    uv = make_mock_uv(cmd_fn=mock_cmd)

    with pytest.raises(SystemExit) as exc_info:
        env._uv_sync(dev_mode=False, uv=cast("appenv.UvBin", uv))

    assert exc_info.value.code == appenv.EXIT_CODE_DATAERR
    captured = capsys.readouterr()
    assert "stale" in captured.out.lower()
    assert "update-lockfile" in captured.out


def test_uv_sync_valid_lockfile_proceeds(tmp_path, monkeypatch, make_mock_uv):
    """_uv_sync proceeds with --frozen when lock --check passes."""
    settings = appenv.AppEnvSettings(
        verbose=False,
        extras=[],
        basedir=tmp_path,
    )
    env = appenv.AppEnv(Path.cwd(), settings)

    sync_calls = []

    def mock_cmd(args, **kwargs):
        sync_calls.append(list(args))
        return ""

    uv = make_mock_uv(cmd_fn=mock_cmd)
    env._uv_sync(dev_mode=False, uv=cast("appenv.UvBin", uv))

    # Should have two calls: lock --check, then sync --no-dev --frozen
    assert len(sync_calls) == 2
    assert sync_calls[0] == ["lock", "--check"]
    assert sync_calls[1] == ["sync", "--no-dev", "--frozen"]
