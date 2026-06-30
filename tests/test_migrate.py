# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for migrate command."""

import argparse
from pathlib import Path

import pytest

import appenv


def test_migrate_uses_python_preference_from_requirements(
    tmp_path, monkeypatch, capsys, app_env
):
    """Migrate reads python preference from requirements.txt."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create requirements.txt with python preference (3.12 and 3.14, missing 3.13)
    (base / "requirements.txt").write_text(
        "# appenv-python-preference: 3.12,3.14\nrequests\n"
    )

    # Mock input to use defaults
    inputs = iter(["test-project"])  # project name
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.migrate()

    # Classic assertions for pyproject.toml with python version range specifier
    pyproject = (base / "pyproject.toml").read_text()
    assert 'requires-python = ">=3.12,<3.15"' in pyproject
    assert '"requests"' in pyproject

    # Simple assertions for console output
    captured = capsys.readouterr()
    assert "Found python preference: 3.12, 3.14" in captured.out
    assert "Migration completed" in captured.out

    # Verify note is printed about missing version (3.13 not in list)
    assert "Note: Versions 3.13" in captured.out


def test_migrate_existing_symlinks(tmp_path, monkeypatch, capsys, app_env):
    """Migrate detects and preserves existing symlinks during migration."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create requirements.txt and appenv script
    (base / "requirements.txt").write_text("requests\n")
    appenv_script = base / "appenv"
    appenv_script.write_text("#!/usr/bin/env python3\nprint('appenv')\n")
    appenv_script.chmod(0o755)

    # Create symlink pointing to appenv
    myapp_link = base / "myapp"
    myapp_link.symlink_to("appenv")

    # Mock input to use defaults
    inputs = iter(["myproject"])  # project name
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.migrate()

    # Simple assertion for console output
    captured = capsys.readouterr()
    assert "Migration completed" in captured.out

    # Verify symlink still exists and points to appenv
    assert myapp_link.exists()
    assert myapp_link.is_symlink()
    assert myapp_link.resolve() == appenv_script.resolve()


def test_migrate_empty_dependencies(tmp_path, monkeypatch, capsys, app_env):
    """Migrate handles requirements.txt with only comments (no dependencies)."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create requirements.txt with only comments
    (base / "requirements.txt").write_text(
        "# This is a comment\n# Another comment\n# No actual dependencies\n"
    )

    # Mock input to use defaults
    inputs = iter(["empty-project"])  # project name
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.migrate()

    # Check pyproject.toml was created with empty dependencies
    pyproject = (base / "pyproject.toml").read_text()
    assert "dependencies = []" in pyproject

    # Verify output mentions 0 dependencies found
    captured = capsys.readouterr()
    assert "0 dependency" in captured.out or "Found 0" in captured.out


def test_migrate_uses_directory_name(tmp_path, monkeypatch, capsys, app_env):
    """Migrate uses directory name as project name (non-interactive)."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create requirements.txt to trigger migration
    (base / "requirements.txt").write_text("requests>=2.0\n")

    env = app_env()
    env.migrate()

    # Verify pyproject.toml uses directory name as project name
    pyproject = (base / "pyproject.toml").read_text()
    assert f'name = "{base.name}"' in pyproject
    assert '"requests>=2.0"' in pyproject

    captured = capsys.readouterr()
    assert "Migrating" in captured.out


def test_migrate_already_exists(tmp_path, monkeypatch, capsys, patterns, app_env):
    """Migrate returns early when pyproject.toml already exists."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create existing pyproject.toml
    (base / "pyproject.toml").write_text(
        '[project]\nname = "existing"\ndependencies = []\n'
    )

    env = app_env()
    env.migrate()

    # Pattern-test for console output
    captured = capsys.readouterr()
    patterns.main.in_order(
        """\
pyproject.toml in ... already has a [project] section — nothing to migrate.
<empty-line>
`migrate` converts requirements.txt-based projects to pyproject.toml."""
    )

    full_pattern = patterns.full
    full_pattern.merge("main")

    full_pattern.generate_example()

    assert full_pattern == captured.out


def test_migrate_no_requirements_txt(workdir, monkeypatch, capsys, patterns, app_env):
    """Lines 888-890: migrate() returns early when requirements.txt not found."""
    Path(workdir)

    env = app_env()
    env.migrate()

    captured = capsys.readouterr()

    patterns.main.in_order(
        """\
No requirements.txt found in ...
Use 'init' to create a new project."""
    )

    full_pattern = patterns.full
    full_pattern.merge("main")

    full_pattern.generate_example()

    assert full_pattern == captured.out


def test_migrate_full_flow_pattern(
    tmp_path, monkeypatch, capsys, patterns, app_env, mock_uv_lock
):
    """Pattern-test for the full migration flow from requirements.txt."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    (base / "requirements.txt").write_text("requests\n")

    env = app_env()
    env.migrate()

    captured = capsys.readouterr()

    patterns.main.in_order(
        """\
Migrating from requirements.txt to pyproject.toml...
...
Preparing/cleaning .appenv directory ...
...

=== Pyproject Migration completed ===
...requirements.{txt,lock} kept as legacy..."""
    )

    patterns.any.optional("...")
    patterns.main.merge("any")

    full_pattern = patterns.full
    full_pattern.merge("main")

    full_pattern.generate_example()

    assert full_pattern == captured.out


def test_migrate_editable_missing_package_warns(
    tmp_path, monkeypatch, capsys, patterns, app_env
):
    """init_pyproject warns when editable path has no package metadata."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    empty_dir = base / "empty-dir"
    empty_dir.mkdir()

    (base / "requirements.txt").write_text("-e ./empty-dir\nrequests\n")

    inputs = iter(["myproject"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.migrate()

    captured = capsys.readouterr()

    patterns.any.optional("...")
    patterns.main.merge("any")
    patterns.main.in_order(
        """\
...warning: 1 editable install(s) skipped:
...- -e ./empty-dir
...add them manually to pyproject.toml if needed."""
    )

    patterns.no_errors.optional("...")
    patterns.no_errors.refused("...error...")
    patterns.no_errors.refused("...exception...")
    patterns.no_errors.refused("...traceback...")
    patterns.no_errors.refused("...failed...")

    full_pattern = patterns.full
    full_pattern.merge("main", "no_errors")

    full_pattern.generate_example()

    assert full_pattern == captured.out.lower()

    pyproject = (base / "pyproject.toml").read_text()
    assert '"requests"' in pyproject
    assert "[tool.uv.sources]" not in pyproject


def test_migrate_editable_mixed_valid_and_invalid(
    tmp_path, monkeypatch, capsys, patterns, app_env
):
    """init_pyproject handles mix of valid and invalid editables."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create valid package
    valid_pkg = base / "valid-pkg"
    valid_pkg.mkdir()
    (valid_pkg / "pyproject.toml").write_text(
        '[project]\nname = "valid-pkg"\nversion = "1.0.0"\n'
    )

    # Create empty invalid package
    empty_dir = base / "empty-dir"
    empty_dir.mkdir()

    (base / "requirements.txt").write_text("-e ./valid-pkg\n-e ./empty-dir\nrequests\n")

    inputs = iter(["myproject"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.migrate()

    captured = capsys.readouterr()

    patterns.any.optional("...")
    patterns.main.merge("any")
    patterns.main.in_order(
        """\
...warning: 2 editable install(s) skipped:
...- -e ./valid-pkg
...- -e ./empty-dir
...add them manually to pyproject.toml if needed."""
    )

    patterns.no_errors.optional("...")
    patterns.no_errors.refused("...error...")
    patterns.no_errors.refused("...exception...")
    patterns.no_errors.refused("...traceback...")
    patterns.no_errors.refused("...failed...")

    full_pattern = patterns.full
    full_pattern.merge("main", "no_errors")

    full_pattern.generate_example()

    assert full_pattern == captured.out.lower()

    # Check pyproject.toml
    pyproject = (base / "pyproject.toml").read_text()
    assert "requests" in pyproject


@pytest.mark.parametrize(
    "requirements,warning_pattern,regular_deps",
    [
        (
            "-e git+https://github.com/user/repo.git\nrequests\n",
            "...warning: 1 editable install(s) skipped:\n"
            "...- -e git+https://github.com/user/repo.git\n"
            "...add them manually to pyproject.toml if needed.",
            ['"requests"'],
        ),
        (
            "-e git+https://github.com/user/pkg.git"
            "\n-e package @ ./path"
            "\nrequests\nclick\n",
            "...warning: 2 editable install(s) skipped:\n"
            "...- -e git+https://github.com/user/pkg.git\n"
            "...- -e package @ ./path\n"
            "...add them manually to pyproject.toml if needed.",
            ['"requests"', '"click"'],
        ),
    ],
)
def test_migrate_editable_unsupported_warns(
    requirements,
    warning_pattern,
    regular_deps,
    tmp_path,
    monkeypatch,
    capsys,
    patterns,
    app_env,
):
    """init_pyproject warns about unsupported editable formats (git URLs, PEP 508)."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    (base / "requirements.txt").write_text(requirements)

    inputs = iter(["myproject"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.migrate()

    captured = capsys.readouterr()

    patterns.any.optional("...")
    patterns.main.merge("any")
    patterns.main.in_order(warning_pattern)

    patterns.no_errors.optional("...")
    patterns.no_errors.refused("...error...")
    patterns.no_errors.refused("...exception...")
    patterns.no_errors.refused("...traceback...")
    patterns.no_errors.refused("...failed...")

    full_pattern = patterns.full
    full_pattern.merge("main", "no_errors")

    full_pattern.generate_example()

    assert full_pattern == captured.out.lower()

    pyproject = (base / "pyproject.toml").read_text()
    assert "-e" not in pyproject
    for dep in regular_deps:
        assert dep in pyproject
    assert "[tool.uv.sources]" not in pyproject


def test_migrate_existing_pyproject_no_project_section(
    tmp_path, monkeypatch, capsys, patterns, app_env, mock_uv_lock
):
    """Line 884: migrate() when pyproject.toml exists but has no [project] section."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create pyproject.toml without [project] section (e.g., only tool config)
    (base / "pyproject.toml").write_text("[tool.ruff]\nline-length = 100\n")

    # Create requirements.txt to allow migration
    (base / "requirements.txt").write_text("requests\n")

    # Mock ensure_uv to prevent actual uv execution
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: None)

    # Mock migrate_from_requirements_txt to return a pyproject
    def mock_migrate(self):
        (base / "pyproject.toml").write_text(
            '[project]\nname = "test"\n[tool.ruff]\nline-length = 100\n'
        )
        return self

    monkeypatch.setattr(appenv.Pyproject, "migrate_from_requirements_txt", mock_migrate)

    # Mock print_migration_info
    monkeypatch.setattr(appenv.Pyproject, "print_migration_info", lambda self: None)

    env = app_env()
    env.migrate()

    captured = capsys.readouterr()
    assert "Adding [project] section to existing pyproject.toml" in captured.out


@pytest.mark.parametrize(
    (
        "script_content",
        "expects_update",
        "old_version_in_output",
        "expects_unknown",
        "expects_unchanged",
    ),
    [
        pytest.param(
            '#!/usr/bin/env python3\n__version__ = "0.0.1"\nprint("old")\n',
            True,
            "0.0.1",
            False,
            False,
            id="version-mismatch",
        ),
        pytest.param(
            "#!/usr/bin/env python3\n"
            f'__version__ = "{appenv.__version__}"\n'
            "print('current')\n",
            False,
            None,
            False,
            True,
            id="same-version",
        ),
        pytest.param(
            "#!/usr/bin/env python3\nprint('old')\n",
            True,
            None,
            True,
            False,
            id="without-version",
        ),
    ],
)
def test_migrate_appenv_script(
    tmp_path,
    monkeypatch,
    capsys,
    app_env,
    mock_uv_lock,
    script_content,
    expects_update,
    old_version_in_output,
    expects_unknown,
    expects_unchanged,
):
    """migrate replaces ./appenv when version differs: mismatch updates, same skips."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create requirements.txt
    (base / "requirements.txt").write_text("requests\n")

    # Create appenv script
    script = base / "appenv"
    script.write_text(script_content)
    script.chmod(0o755)

    if expects_unchanged:
        original_mtime = script.stat().st_mtime

    # Mock ensure_uv to prevent actual uv execution
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: None)

    inputs = iter(["myproject"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.migrate()

    captured = capsys.readouterr()

    if expects_update:
        assert "Updated" in captured.out
    else:
        assert "Updated" not in captured.out

    if old_version_in_output:
        assert old_version_in_output in captured.out
        assert appenv.__version__ in captured.out

        # The script should no longer contain the old version
        new_content = script.read_text()
        assert appenv.__version__ in new_content
        assert old_version_in_output not in new_content
    elif expects_unknown:
        assert "unknown" in captured.out
        assert appenv.__version__ in captured.out

        # The script should now contain the current version
        new_content = script.read_text()
        assert appenv.__version__ in new_content
    elif expects_unchanged:
        # File should be untouched
        assert script.stat().st_mtime == original_mtime


def test_migrate_with_path_argument(
    tmp_path, monkeypatch, capsys, app_env, mock_uv_lock
):
    """Lines 892-893: migrate() with --path creates target directory."""
    base = tmp_path

    # Create requirements.txt in a subdirectory that will be the path target
    subdir = base / "subdir"
    subdir.mkdir()
    (subdir / "requirements.txt").write_text("requests\n")

    env = app_env(base)

    args = argparse.Namespace(path="subdir")
    env.migrate(args)

    # Verify migration happened in target dir
    assert (subdir / "pyproject.toml").exists()
    pyproject = (subdir / "pyproject.toml").read_text()
    assert "requests" in pyproject


# -- PEP 508 pre-validation ---------------------------------------------------
# SPEC: migrate-pep508-validation — requirements.txt lines are validated against
# PEP 508 BEFORE pyproject.toml is written. appenv is zero-runtime-deps, so the
# check is a heuristic that rejects obviously malformed lines (e.g. `!!!x!!!`)
# early, instead of letting uv produce a confusing setuptools traceback at lock
# time. Authoritative validation remains uv's job; this gate catches the dumb
# cases up front.


def test_migrate_rejects_invalid_pep508_requirement(
    tmp_path, monkeypatch, capsys, app_env, mock_uv_lock
):
    """A non-PEP-508 line in requirements.txt must be rejected before any
    pyproject.toml is written.

    Observed bug: ``!!!invalid!!!`` was silently written into
    ``dependencies = ["!!!invalid!!!"]`` and only surfaced as a long
    uv/setuptools traceback at ``uv lock`` time — confusing and verbose.
    Expected: exit EXIT_CODE_USAGE with a short message naming the bad line
    and the file; no pyproject.toml written; no traceback reaches the user.
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / "requirements.txt").write_text("!!!invalid!!!\n")

    env = app_env()
    with pytest.raises(SystemExit) as exc_info:
        env.migrate()

    assert exc_info.value.code == appenv.EXIT_CODE_USAGE
    assert not (tmp_path / "pyproject.toml").exists()
    captured = capsys.readouterr()
    assert "requirements.txt" in captured.err, (
        f"error must name the source file; got: {captured.err!r}"
    )
    assert "!!!invalid!!!" in captured.err, (
        f"error must quote the offending line; got: {captured.err!r}"
    )
    assert "Migrating" not in captured.out, (
        "rejection must not show the 'Migrating...' banner; "
        f"got stdout: {captured.out!r}"
    )


@pytest.mark.parametrize(
    "specifier",
    [
        pytest.param("requests", id="plain-name"),
        pytest.param("requests>=2.0", id="version-specifier"),
        pytest.param("requests[security]==2.31.0", id="extras-and-version"),
        pytest.param('requests>=2.0,<3.0; python_version>"3.10"', id="marker"),
    ],
)
def test_migrate_accepts_valid_pep508_specifiers(
    specifier, tmp_path, monkeypatch, app_env, mock_uv_lock
):
    """The PEP 508 pre-validation must not reject well-formed specifiers —
    names, version pins, extras, and environment markers all pass through to
    pyproject.toml as before (guards against false positives in the heuristic).
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / "requirements.txt").write_text(specifier + "\n")

    env = app_env()
    env.migrate()

    pyproject = (tmp_path / "pyproject.toml").read_text()
    assert f'"{specifier}"' in pyproject


@pytest.mark.parametrize(
    ("dep", "expected"),
    [
        # URL requirements: "name @ url" (PEP 508 direct reference) and VCS URLs
        pytest.param("requests @ https://example.com/r.tar.gz", True, id="name-at-url"),
        pytest.param("git+https://github.com/u/r.git", True, id="git-plus-url"),
        pytest.param("hg+https://example.com/repo", True, id="hg-plus-url"),
        # Bare URL requirements (no package name)
        pytest.param("https://example.com/package.tar.gz", True, id="https-url"),
        pytest.param("file:///local/path", True, id="file-url"),
        # Named requirements — representative sample (full coverage in the
        # migrate-level test_migrate_accepts_valid_pep508_specifiers)
        pytest.param("requests", True, id="plain-name"),
        pytest.param("requests[security]>=2.0", True, id="extras-and-version"),
        # Invalid: leading token does not match PEP 508 name pattern
        pytest.param("!!!invalid!!!", False, id="invalid-chars"),
        pytest.param("@broken", False, id="leading-at"),
        # Defensive: empty/whitespace — migrate() never reaches these (its
        # parsing loop filters empties), but the function guards against them.
        pytest.param("", False, id="empty"),
        pytest.param("   ", False, id="whitespace-only"),
    ],
)
def test_is_likely_valid_pep508_dep(dep, expected):
    """Unit-test the PEP 508 heuristic directly, covering all branches:
    URL/VCS forms, bare URLs, named requirements, and the defensive empty
    check that migrate() never reaches (its parser filters empties) but the
    function guards against for direct callers.
    """
    assert appenv._is_likely_valid_pep508_dep(dep) is expected
