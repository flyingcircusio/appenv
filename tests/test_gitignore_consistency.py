# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for gitignore consistency between `init` and `migrate`.

SPEC: fix-gitignore-consistency::shared-gitignore-entries

`init` and `migrate` must write the same set of `.gitignore` entries
(`.venv`, `.appenv`, `.batou-lock`) sourced from a single module-level
constant `_GITIGNORE_ENTRIES` so a user running `git add -A` after either
command never silently commits the `.appenv/venv/` tree.
"""

import subprocess

import pytest

import appenv

EXPECTED_GITIGNORE_ENTRIES = appenv._GITIGNORE_ENTRIES


def test_module_exposes_gitignore_entries_constant():
    """`_GITIGNORE_ENTRIES` is defined at module scope with the canonical list.

    Requirement: the list lives in exactly one place in source.
    """
    assert hasattr(appenv, "_GITIGNORE_ENTRIES"), (
        "appenv must expose a module-level `_GITIGNORE_ENTRIES` constant "
        "(SPEC: fix-gitignore-consistency::shared-gitignore-entries)"
    )
    assert appenv._GITIGNORE_ENTRIES == EXPECTED_GITIGNORE_ENTRIES


def test_init_writes_gitignore_entries(tmp_path, monkeypatch, app_env, mock_uv_lock):
    """`init` writes `.venv`, `.appenv`, `.batou-lock` into `.gitignore`."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    inputs = iter(
        [
            "",  # no deps (defaults to "app")
            "myapp",  # command name
            "myapp-proj",  # project name
            "desc",  # description
            "3.13",  # python version
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.init()

    gitignore_lines = (base / ".gitignore").read_text().splitlines()
    for entry in EXPECTED_GITIGNORE_ENTRIES:
        assert entry in gitignore_lines, f"`init` must add {entry!r} to .gitignore"


def test_migrate_writes_gitignore_entries(tmp_path, monkeypatch, app_env, mock_uv_lock):
    """`migrate` writes the same three entries into `.gitignore` as `init`."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    (base / "requirements.txt").write_text("requests\n")

    inputs = iter(["myproject"])  # project name
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.migrate()

    gitignore_lines = (base / ".gitignore").read_text().splitlines()
    for entry in EXPECTED_GITIGNORE_ENTRIES:
        assert entry in gitignore_lines, f"`migrate` must add {entry!r} to .gitignore"


def test_init_and_migrate_write_identical_gitignore(
    tmp_path, monkeypatch, app_env, mock_uv_lock
):
    """`init` and `migrate` produce byte-identical `.gitignore` content."""
    init_dir = tmp_path / "init-project"
    init_dir.mkdir()
    monkeypatch.chdir(init_dir)
    init_inputs = iter(["", "myapp", "myapp-proj", "desc", "3.13"])
    monkeypatch.setattr("builtins.input", lambda _: next(init_inputs))
    app_env().init()
    init_gitignore = (init_dir / ".gitignore").read_text()

    migrate_dir = tmp_path / "migrate-project"
    migrate_dir.mkdir()
    (migrate_dir / "requirements.txt").write_text("requests\n")
    monkeypatch.chdir(migrate_dir)
    migrate_inputs = iter(["myproject"])
    monkeypatch.setattr("builtins.input", lambda _: next(migrate_inputs))
    app_env().migrate()
    migrate_gitignore = (migrate_dir / ".gitignore").read_text()

    assert init_gitignore == migrate_gitignore


def test_init_and_migrate_share_gitignore_entries_constant(
    tmp_path, monkeypatch, app_env, mock_uv_lock
):
    """Both `init` and `migrate` pass the SAME `_GITIGNORE_ENTRIES` object to
    `ensure_gitignore` — no inline-list duplication in source.

    Requirement: the list lives in exactly one place in source. Two inline
    list literals with equal values would be distinct objects and fail the
    identity check; only a single shared module-level constant satisfies it.
    """
    captured: list[list[str]] = []
    real_ensure_gitignore = appenv.ensure_gitignore

    def capture(base, entries):
        captured.append(entries)
        return real_ensure_gitignore(base, entries)

    monkeypatch.setattr(appenv, "ensure_gitignore", capture)

    init_dir = tmp_path / "init"
    init_dir.mkdir()
    monkeypatch.chdir(init_dir)
    init_inputs = iter(["", "myapp", "proj", "d", "3.13"])
    monkeypatch.setattr("builtins.input", lambda _: next(init_inputs))
    app_env().init()

    migrate_dir = tmp_path / "migrate"
    migrate_dir.mkdir()
    (migrate_dir / "requirements.txt").write_text("requests\n")
    monkeypatch.chdir(migrate_dir)
    migrate_inputs = iter(["myproject"])
    monkeypatch.setattr("builtins.input", lambda _: next(migrate_inputs))
    app_env().migrate()

    assert len(captured) == 2, (
        "both `init` and `migrate` must call ensure_gitignore exactly once"
    )
    init_entries, migrate_entries = captured
    assert init_entries is migrate_entries, (
        "`init` and `migrate` must pass the SAME list object "
        "(`_GITIGNORE_ENTRIES`), not two equivalent inline lists"
    )
    assert init_entries is appenv._GITIGNORE_ENTRIES
    assert init_entries == EXPECTED_GITIGNORE_ENTRIES


def test_migrate_writes_gitignore_even_when_uv_lock_fails(
    tmp_path, monkeypatch, app_env
):
    """reorder-migrate::gitignore-before-lock — ensure_gitignore runs BEFORE uv
    lock, so .gitignore is written even when uv lock crashes.

    Regression test for the original bug: migrate() called ensure_gitignore
    AFTER _uv_lock, so a lock failure (e.g. missing credentials for a private
    index) prevented .gitignore from being written.
    """
    base = tmp_path
    (base / "requirements.txt").write_text(
        "--extra-index-url https://deploy:s3cr3t@gitlab.example.com/simple\nrequests\n"
    )

    def _raise(self, uv, diff=False):
        raise subprocess.CalledProcessError(returncode=1, cmd=["uv", "lock"])

    monkeypatch.setattr(appenv.AppEnv, "_uv_lock", _raise)

    env = app_env(base)
    with pytest.raises(subprocess.CalledProcessError):
        env.migrate()

    # .gitignore was written despite the crash.
    gitignore = base / ".gitignore"
    assert gitignore.exists()
    gitignore_lines = gitignore.read_text().splitlines()
    for entry in EXPECTED_GITIGNORE_ENTRIES:
        assert entry in gitignore_lines, (
            f"migrate must add {entry!r} to .gitignore even when uv lock fails"
        )
