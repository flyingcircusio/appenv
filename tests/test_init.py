# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for init command."""

import argparse
import logging
import os
import subprocess
from pathlib import Path

import pytest

import appenv


def _mock_uv():
    from unittest.mock import MagicMock

    return MagicMock(
        spec=appenv.UvBin,
        cmd=lambda a, **kw: "",
        version=appenv.UvVersion(0, 7, 0),
        bin=Path("/usr/bin/uv"),
    )


def _raise_on_uv_lock(monkeypatch, exc):
    """Patch ``AppEnv._uv_lock`` to raise ``exc``."""

    def _raise(self, uv, diff=False):
        raise exc

    monkeypatch.setattr(appenv.AppEnv, "_uv_lock", _raise)


def _init_namespace(**overrides):
    """Build the non-interactive ``init`` argparse.Namespace."""
    defaults = {
        "force": False,
        "binary": "http",
        "deps": ["httpie"],
        "name": "myproject",
        "python_version": "3.13",
        "description": None,
        "path": None,
    }
    return argparse.Namespace(**(defaults | overrides))


def test_init_fresh_start_interactive(tmp_path, monkeypatch, capsys, app_env, patterns):
    """Init fresh start flow with interactive inputs."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Inputs: deps (2), empty, command name, project name, desc, py version
    inputs = iter(
        [
            "requests",  # dependency 1
            "click",  # dependency 2
            "",  # empty line to finish dependencies
            "myapp",  # command name
            "myapp-project",  # project name
            "My test app",  # description
            "3.13",  # python version
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.init()

    # Verify pyproject.toml was created
    pyproject = (base / "pyproject.toml").read_text()
    assert 'name = "myapp-project"' in pyproject
    assert 'description = "My test app"' in pyproject
    assert '"requests"' in pyproject
    assert '"click"' in pyproject
    assert 'requires-python = ">=3.13"' in pyproject

    # Verify appenv script and symlink were created
    assert (base / "appenv").exists()
    assert (base / "myapp").exists()
    assert (base / "myapp").is_symlink()

    # Check the output with patterns
    captured = capsys.readouterr()
    patterns.any.optional("...")
    patterns.main.in_order(
        """\
Let's create a new appenv project in ...
I'll ask a few questions, then create pyproject.toml here
Enter dependencies (one per line, empty line to finish):
  Default: app
Created .../appenv
Created .../pyproject.toml
Created ./myapp -> appenv (runs the myapp binary)
Generating new lock file ...
Updating lock file ...
Created .../.gitignore
=== Appenv project initialized ===
Use `./myapp` to run the myapp binary"""
    )
    patterns.main.merge("any")

    full_pattern = patterns.full
    full_pattern.merge("main")
    full_pattern.generate_example()
    assert full_pattern == captured.out


def test_init_fresh_start_explicit_dependency(tmp_path, monkeypatch, capsys, app_env):
    """Init fresh start with explicit dependency entered."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # No requirements.txt - triggers fresh start flow
    inputs = iter(
        [
            "requests",  # dependency 1
            "",  # empty line to finish dependencies
            "myapp",  # command name (real package)
            "",  # project name (use default: directory name)
            "",  # empty description
            "",  # python version (use default 3.13)
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.init()

    # Verify pyproject.toml was created
    pyproject = (base / "pyproject.toml").read_text()
    assert base.name in pyproject  # default is directory name
    assert '"requests"' in pyproject  # explicit dependency entered
    assert 'requires-python = ">=3.13"' in pyproject  # default version


def test_init_unlink_broken_symlink(workdir, monkeypatch, capsys, app_env):
    """Unlinks broken symlink before creating new one."""
    base = Path(workdir)

    broken_link = base / "myapp"
    broken_link.symlink_to("nonexistent_target")
    assert broken_link.is_symlink()
    assert not broken_link.exists()

    inputs = iter(
        [
            "",  # empty dependencies -> defaults to "app"
            "myapp",  # command name
            "",  # project name (default: directory name)
            "",  # description
            "",  # python version
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.init()

    assert (base / "myapp").is_symlink()
    assert (base / "myapp").exists()
    assert (base / "myapp").resolve() == (base / "appenv").resolve()


def test_init_refuses_existing_project_section(workdir, capsys, app_env, patterns):
    """init refuses to run when pyproject.toml already has a [project] section.

    The refusal is purely line-based (it scans for a ``[project]`` line; there is
    no tomllib code path), so it is uniform across every supported Python. The
    former ``..._python39`` variant asserted a tomllib fallback that does not
    exist in the code — it is folded in here, not re-added. Re-init used to
    silently drop fields appenv cannot round-trip; it now exits DATAERR (65),
    prints guidance, and leaves the file untouched.
    """
    base = Path(workdir)
    (base / "pyproject.toml").write_text(
        '[project]\nname = "myapp"\nversion = "1.2.3"\ndependencies = ["httpie>=3.0"]\n'
    )

    env = app_env()

    with pytest.raises(SystemExit) as exc_info:
        env.init()

    assert exc_info.value.code == appenv.EXIT_CODE_DATAERR  # 65
    captured = capsys.readouterr()
    patterns.main.in_order(
        """\
... already has a [project] section.
appenv ... no longer updates existing projects ...
...appenv uv add...directly."""
    )
    full = patterns.full
    full.merge("main")
    assert full == captured.out
    # The existing [project] section must survive the refusal untouched.
    pyproject = (base / "pyproject.toml").read_text()
    assert 'version = "1.2.3"' in pyproject
    assert '"httpie>=3.0"' in pyproject


@pytest.mark.parametrize("command_name", ["app", ""])
def test_init_empty_command_name_defaults_to_app(
    workdir, monkeypatch, capsys, app_env, command_name
):
    """init() uses 'app' as default when command name is empty or explicitly 'app'."""
    base = Path(workdir)

    # Empty deps -> defaults to "app"
    inputs = iter(
        [
            "",  # no dependencies -> defaults to "app"
            command_name,  # command name (empty -> default "app")
            "",  # project name (default: directory name)
            "test description",
            "",  # python version default
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.init()

    pyproject = (base / "pyproject.toml").read_text()
    assert base.name in pyproject  # default is directory name
    assert '"app"' in pyproject  # dependency also defaults to app


def test_init_with_path_creates_directory(tmp_path, monkeypatch, capsys, app_env):
    """init with path argument creates directory and initializes there."""
    base = tmp_path
    target_dir = base / "myproject"

    inputs = iter(
        [
            "myapp",  # dependency
            "",  # empty line to finish dependencies
            "myapp",  # command name
            "",  # project name (default: target directory name)
            "Test project",
            "",  # python version
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env(base)
    args = argparse.Namespace(path="myproject")
    env.init(args)

    # Verify directory was created
    assert target_dir.exists()
    assert target_dir.is_dir()

    # Verify pyproject.toml was created in target directory
    pyproject = (target_dir / "pyproject.toml").read_text()
    assert target_dir.name in pyproject
    assert '"myapp"' in pyproject

    # Verify appenv script and symlink are created in target directory
    assert (target_dir / "appenv").exists()
    assert (target_dir / "myapp").exists()
    assert (target_dir / "myapp").is_symlink()


def test_init_with_path_shows_relative_symlink_path(
    tmp_path, monkeypatch, capsys, app_env
):
    """init with a path shows the symlink path relative to the original CWD.

    When ``appenv init subdir/`` targets a subdirectory, the symlink lives in
    that subdirectory while the user ran the command from the parent. The
    ``Created``/``Use`` messages must show the path relative to the original
    CWD (``subdir/<binary>``), not a misleading ``./<binary>`` that would
    resolve against the     parent directory.
    """
    parent = tmp_path

    inputs = iter(
        [
            "myapp",  # dependency
            "",  # empty line to finish dependencies
            "myapp",  # command name
            "",  # project name (default: target directory name)
            "Test project",
            "",  # python version
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.chdir(parent)

    env = app_env(parent)
    args = argparse.Namespace(path="myproject")
    env.init(args)

    captured = capsys.readouterr()
    # original_cwd is the parent, symlink is in myproject/ -> relative path
    # includes the directory and gets no ./ prefix.
    assert "Created myproject/myapp -> appenv" in captured.out
    assert "Use `myproject/myapp` to run the myapp binary" in captured.out


@pytest.mark.parametrize(
    ("path", "command_name", "pre_create"),
    [
        pytest.param("some/nested/path", "nestedapp", False, id="nested"),
        pytest.param("existing", "existingapp", True, id="pre-existing"),
    ],
)
def test_init_with_path_creates_or_uses_directory(
    path, command_name, pre_create, tmp_path, monkeypatch, capsys, app_env
):
    """init with a target path either creates all parent directories (nested
    case) or initializes inside an already-existing directory.

    Both converge on the same post-condition: a pyproject.toml in the target
    directory whose body names that directory."""
    base = tmp_path
    target_dir = base / path
    if pre_create:
        target_dir.mkdir()

    inputs = iter(
        [
            "",  # empty dependencies -> defaults to "app"
            command_name,  # command name
            "",  # project name
            "Test project",
            "",  # python version
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env(base)
    args = argparse.Namespace(path=path)
    env.init(args)

    assert (target_dir / "pyproject.toml").exists()
    pyproject = (target_dir / "pyproject.toml").read_text()
    assert target_dir.name in pyproject


def test_init_without_path_uses_current_directory(
    tmp_path, monkeypatch, capsys, app_env
):
    """init without path argument uses current directory (original_cwd)."""
    base = tmp_path
    monkeypatch.chdir(base)

    inputs = iter(
        [
            "",  # empty dependencies -> defaults to "app"
            "cwdapp",  # command name
            "",  # project name
            "Current dir project",
            "",  # python version
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    # Call init without args (path=None is default)
    env.init()

    # Verify pyproject.toml was created in current directory (base)
    assert (base / "pyproject.toml").exists()
    pyproject = (base / "pyproject.toml").read_text()
    assert base.name in pyproject


def test_init_appenv_script_already_exists(workdir, monkeypatch, capsys, app_env):
    """Branch 882->889: init() skips appenv script creation when it already exists."""
    base = Path(workdir) / "myproject_init_exists"
    base.mkdir()
    os.chdir(base)

    env = app_env()

    # Create appenv script BEFORE calling init
    env.appenv_script.write_text("#!/usr/bin/env python3\nprint('existing')\n")
    env.appenv_script.chmod(0o755)

    original_content = env.appenv_script.read_text()
    original_mtime = env.appenv_script.stat().st_mtime

    # Inputs for init
    inputs = iter(
        [
            "",  # no dependencies -> defaults to "app"
            "myapp",  # command name
            "myapp-project",  # project name
            "test",  # description
            "3.13",  # python version
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env.init()

    # Verify appenv script was NOT overwritten
    assert env.appenv_script.read_text() == original_content
    assert env.appenv_script.stat().st_mtime == original_mtime

    # Verify pyproject.toml was still created
    assert (base / "pyproject.toml").exists()

    # Verify output does NOT say "Created appenv"
    captured = capsys.readouterr()
    assert "Created appenv" not in captured.out


def test_init_warns_on_version_mismatch(workdir, monkeypatch, capsys, app_env):
    """init warns when local ./appenv has a different version."""
    base = Path(workdir) / "myproject_init_version"
    base.mkdir()
    os.chdir(base)

    env = app_env()

    # Create appenv script with a different version
    env.appenv_script.write_text(
        '#!/usr/bin/env python3\n__version__ = "0.0.1"\nprint("old")\n'
    )
    env.appenv_script.chmod(0o755)

    original_content = env.appenv_script.read_text()

    # Inputs for init
    inputs = iter(
        [
            "",  # no dependencies -> defaults to "app"
            "myapp",  # command name
            "myapp-project",  # project name
            "test",  # description
            "3.13",  # python version
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env.init()

    # Verify appenv script was NOT overwritten (warn only, no update)
    assert env.appenv_script.read_text() == original_content

    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "0.0.1" in captured.out
    assert appenv.__version__ in captured.out
    assert "self-update" in captured.out


def test_init_existing_pyproject_no_project_section(
    tmp_path, monkeypatch, capsys, app_env
):
    """Line 833: init() with existing pyproject.toml without [project] section."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create pyproject.toml WITHOUT [project] section (e.g., only tool config)
    (base / "pyproject.toml").write_text("[tool.ruff]\nline-length = 100\n")

    inputs = iter(["", "myapp", "myproject", "Test", "3.13"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    env = app_env()
    env.init()

    captured = capsys.readouterr()
    assert "Adding [project] section to existing" in captured.out


def test_init_binary_without_dep_new_project(tmp_path, monkeypatch, capsys):
    """--binary without --dep on a new project gives a specific --dep error."""
    # No existing pyproject.toml → new project, deps cannot be sourced.
    settings = appenv.AppEnvSettings(verbose=False, extras=[], basedir=tmp_path)
    env = appenv.AppEnv(tmp_path, settings)

    args = argparse.Namespace(
        force=False,
        binary="http",
        deps=None,
        name=None,
        python_version=None,
        path=None,
    )

    with pytest.raises(SystemExit) as exc_info:
        env.init(args)
    assert exc_info.value.code == appenv.EXIT_CODE_USAGE
    captured = capsys.readouterr()
    assert "--dep is required" in captured.err


# SPEC: fix-init-safety-layer — input validation runs after params are resolved
# and before any file is written. Rejects path traversal, absolute paths, and
# clobbering of user files; lets appenv and broken symlinks refresh; dedups deps.


@pytest.mark.parametrize(
    ("binary", "dangerous"),
    [("../escape", "../escape"), ("/etc/evil", "/etc/evil")],
    ids=["path-traversal", "absolute"],
)
def test_init_rejects_non_bare_binary_name(
    binary, dangerous, workdir, capsys, app_env, patterns
):
    """--binary with a path separator is refused before any file is touched.

    Both inputs trip the single branch ``if "/" in name or "\\" in name or ...``
    via the substring-``/`` condition. The parametrization preserves the case
    count; the ``dangerous`` target each binary would have created must not exist.
    """
    base = Path(workdir)
    args = argparse.Namespace(
        force=False,
        binary=binary,
        deps=["httpie"],
        name="myproject",
        python_version="3.13",
        description=None,
        path=None,
    )

    env = app_env()
    with pytest.raises(SystemExit) as exc_info:
        env.init(args)

    assert exc_info.value.code == appenv.EXIT_CODE_USAGE
    # No symlink escaped outside the project, no pyproject written.
    assert not (base / dangerous).resolve().exists()
    assert not (base / "pyproject.toml").exists()
    captured = capsys.readouterr()
    patterns.main.in_order(
        "Error: --binary must be a bare name (no path, no whitespace), got ..."
    )
    full = patterns.full
    full.merge("main")
    assert full == captured.err


@pytest.mark.parametrize("kind", ["user-file", "foreign-symlink"])
def test_init_refuses_to_clobber_non_appenv_entry(
    kind, workdir, capsys, app_env, patterns
):
    """A non-appenv entry at the symlink target is refused, not overwritten.

    Both inputs trip the single ``not link.is_symlink() or readlink != "appenv"``
    branch: ``user-file`` via the ``not is_symlink()`` half, ``foreign-symlink``
    via the ``readlink != "appenv"`` half. Identical message, exit, and fs.
    """
    base = Path(workdir)
    if kind == "user-file":
        (base / "http").write_text("important user data")
    else:
        # Materialize a target so the symlink resolves (working, not broken).
        (base / "foreign-target").write_text("data")
        (base / "http").symlink_to("foreign-target")
    assert (base / "http").exists()

    args = argparse.Namespace(
        force=False,
        binary="http",
        deps=["httpie"],
        name="myproject",
        python_version="3.13",
        description=None,
        path=None,
    )

    env = app_env()
    with pytest.raises(SystemExit) as exc_info:
        env.init(args)

    assert exc_info.value.code == appenv.EXIT_CODE_USAGE
    # The pre-existing entry is left untouched, no pyproject written.
    assert not (base / "pyproject.toml").exists()
    if kind == "user-file":
        assert (base / "http").read_text() == "important user data"
    else:
        assert os.readlink(base / "http") == "foreign-target"
    captured = capsys.readouterr()
    patterns.main.in_order("Error: ... exists and is not an appenv symlink ...")
    full = patterns.full
    full.merge("main")
    assert full == captured.err


def test_init_relinks_existing_appenv_symlink(workdir, capsys, app_env):
    """An existing ``<name> -> appenv`` symlink is refreshed, not refused."""
    base = Path(workdir)
    # Materialize the appenv script so the symlink resolves (readlink == "appenv").
    (base / "appenv").write_bytes(Path(appenv.__file__).read_bytes())
    (base / "http").symlink_to("appenv")
    assert (base / "http").exists()
    assert os.readlink(base / "http") == "appenv"

    args = argparse.Namespace(
        force=False,
        binary="http",
        deps=["httpie"],
        name="myproject",
        python_version="3.13",
        description=None,
        path=None,
    )

    env = app_env()
    env.init(args)

    # Symlink was refreshed and still points at appenv.
    assert (base / "http").is_symlink()
    assert os.readlink(base / "http") == "appenv"
    assert (base / "pyproject.toml").exists()


def test_init_relinks_broken_symlink_at_target(workdir, capsys, app_env):
    """A broken symlink at the target is refreshed (matches historical behavior)."""
    base = Path(workdir)
    (base / "http").symlink_to("nonexistent_target")
    assert (base / "http").is_symlink()
    assert not (base / "http").exists()

    args = argparse.Namespace(
        force=False,
        binary="http",
        deps=["httpie"],
        name="myproject",
        python_version="3.13",
        description=None,
        path=None,
    )

    env = app_env()
    env.init(args)

    assert (base / "http").is_symlink()
    assert os.readlink(base / "http") == "appenv"
    assert (base / "pyproject.toml").exists()


def test_init_dedupes_duplicate_deps_noninteractive(workdir, app_env):
    """Repeated --dep entries collapse to a single occurrence in pyproject.toml."""
    base = Path(workdir)
    args = argparse.Namespace(
        force=False,
        binary="http",
        deps=["httpie", "httpie", "requests"],
        name="myproject",
        python_version="3.13",
        description=None,
        path=None,
    )

    env = app_env()
    env.init(args)

    content = (base / "pyproject.toml").read_text()
    assert content.count('"httpie"') == 1
    assert content.count('"requests"') == 1


# -- validation gaps in the safety layer ---------------------------------------
# SPEC: fix-init-safety-layer — these tests specify the CORRECT behavior for
# inputs the current validator does NOT yet reject. They are RED until
# _validate_init_params (src/appenv.py:1459) is extended. Each docstring names
# the concrete bug, the observed (wrong) behavior, and the expected fix.


@pytest.mark.parametrize(
    "binary",
    [
        pytest.param("my binary", id="space-in-name"),
        pytest.param("rm -rf", id="space-in-name-shell-token"),
    ],
)
def test_init_rejects_binary_name_with_whitespace(binary, workdir, capsys, app_env):
    """--binary with whitespace must be rejected before any file is written.

    A name like ``my binary`` or ``rm -rf`` can never exist in ``venv/bin/``
    (binaries are single path components), so the symlink would be dead on
    arrival. The current check ``if "/" in name or "\\\\" in name or name in
    {".", ".."}`` (src/appenv.py:1478) catches path traversal but misses
    whitespace entirely.

    Observed bug: ``--binary "my binary"`` is accepted and a symlink
    ``./my binary -> appenv`` is created. ``rm -rf`` likewise.
    Expected: exit EXIT_CODE_USAGE, no symlink, no pyproject.toml, error
    names --binary.
    """
    base = Path(workdir)
    args = argparse.Namespace(
        force=False,
        binary=binary,
        deps=["httpie"],
        name="myproject",
        python_version="3.13",
        description=None,
        path=None,
    )

    env = app_env()
    with pytest.raises(SystemExit) as exc_info:
        env.init(args)

    assert exc_info.value.code == appenv.EXIT_CODE_USAGE
    # No dead symlink was created, no pyproject written.
    assert not (base / binary).exists()
    assert not (base / "pyproject.toml").exists()
    captured = capsys.readouterr()
    assert "--binary" in captured.err, (
        f"rejection message should name --binary; got: {captured.err!r}"
    )


def test_init_rejects_empty_binary_name(workdir, capsys, app_env):
    """--binary "" must be rejected as a bare-name violation, not misparsed.

    ``self.base / ""`` collapses to ``self.base`` (the project dir itself),
    so the empty name trips the existing-entry conflict branch and emits a
    misleading ``<workdir> exists and is not an appenv symlink`` instead of a
    clear ``--binary must not be empty`` message.

    Observed bug: ``--binary ""`` produces ``/tmp/... exists and is not an
    appenv symlink`` because the validator never sees the empty string as
    invalid — it falls through to the workdir-conflict check.
    Expected: exit EXIT_CODE_USAGE with a clear empty-name message (NOT the
    workdir-conflict message), no pyproject.toml.
    """
    base = Path(workdir)
    args = argparse.Namespace(
        force=False,
        binary="",
        deps=["httpie"],
        name="myproject",
        python_version="3.13",
        description=None,
        path=None,
    )

    env = app_env()
    with pytest.raises(SystemExit) as exc_info:
        env.init(args)

    assert exc_info.value.code == appenv.EXIT_CODE_USAGE
    assert not (base / "pyproject.toml").exists()
    captured = capsys.readouterr()
    # The misleading workdir-conflict message must NOT appear — the empty
    # name should be rejected on its own merits, not mis-parsed as the
    # project directory.
    assert "exists and is not an appenv symlink" not in captured.err, (
        "empty --binary must not trip the workdir-conflict branch; got: "
        f"{captured.err!r}"
    )
    assert "--binary" in captured.err


def test_init_rejects_empty_dependency(workdir, capsys, app_env, mock_uv_lock):
    """--dep "" must be rejected before it reaches pyproject.toml.

    An empty dependency string is silently written into
    ``dependencies = [""]`` and only surfaces as a parse error at ``uv lock``
    time — too late and with a confusing message. The validator should reject
    it at the same early stage as path traversal.

    Observed bug: ``--dep ""`` is accepted; ``dependencies = [""]`` lands in
    pyproject.toml and fails later at ``uv lock``.
    Expected: exit EXIT_CODE_USAGE, no pyproject.toml written, error names
    --dep.
    """
    base = Path(workdir)
    args = argparse.Namespace(
        force=False,
        binary="http",
        deps=[""],
        name="myproject",
        python_version="3.13",
        description=None,
        path=None,
    )

    env = app_env()
    with pytest.raises(SystemExit) as exc_info:
        env.init(args)

    assert exc_info.value.code == appenv.EXIT_CODE_USAGE
    assert not (base / "pyproject.toml").exists()
    captured = capsys.readouterr()
    assert "--dep" in captured.err, (
        f"rejection message should name --dep; got: {captured.err!r}"
    )


@pytest.mark.parametrize(
    ("exc", "expected_raises", "check_log"),
    [
        pytest.param(
            subprocess.CalledProcessError(returncode=1, cmd=["uv", "lock"]),
            subprocess.CalledProcessError,
            True,
            id="lock-failure",
        ),
        pytest.param(
            KeyboardInterrupt(), KeyboardInterrupt, False, id="keyboard-interrupt"
        ),
    ],
)
def test_init_restores_pyproject_on_failure(
    exc, expected_raises, check_log, workdir, capsys, caplog, monkeypatch, app_env
):
    """Any failure mid uv-lock restores a pre-existing pyproject.toml byte-for-byte
    so its unrelated content (here ``[build-system]``) survives intact.

    ``except BaseException`` deliberately covers KeyboardInterrupt, not just
    CalledProcessError. When ``check_log`` is set the rollback must also be
    traceable from the log and stderr alone."""
    base = Path(workdir)
    original = (
        '[build-system]\nrequires = ["hatchling"]\nbuild-backend = "hatchling.build"\n'
    )
    (base / "pyproject.toml").write_text(original)

    _raise_on_uv_lock(monkeypatch, exc)

    caplog.set_level(logging.DEBUG, logger="appenv")
    env = app_env()
    with pytest.raises(expected_raises):
        env.init(_init_namespace())

    # Restored to the exact pre-init bytes — no half-written [project] remains.
    assert (base / "pyproject.toml").read_text() == original
    if check_log:
        captured = capsys.readouterr()
        assert "restored to previous state" in captured.err
        # Rollback is traceable from the log alone.
        assert "init-rollback" in caplog.text


def test_init_deletes_partial_state_on_lock_failure(
    workdir, capsys, monkeypatch, app_env
):
    """A uv-lock failure in a previously empty directory deletes BOTH halves of
    the partial state this run created: the freshly-written pyproject.toml AND
    the command symlink — the ``./http`` entry does not survive a failed init."""
    base = Path(workdir)
    _raise_on_uv_lock(
        monkeypatch,
        subprocess.CalledProcessError(returncode=1, cmd=["uv", "lock"]),
    )

    env = app_env()
    with pytest.raises(subprocess.CalledProcessError):
        env.init(_init_namespace())

    assert not (base / "pyproject.toml").exists()
    assert not (base / "http").is_symlink()
    assert not (base / "http").exists()


def test_init_keeps_preexisting_command_link_on_lock_failure(
    workdir, capsys, monkeypatch, app_env
):
    """A uv-lock failure does NOT remove a command symlink that pre-existed the
    run — rollback only unlinks what this run created (SPEC snapshot contract:
    ``command_link_existed`` gates the unlink)."""
    base = Path(workdir)
    # Materialize the appenv target so the symlink resolves and the validator
    # accepts it as a refresh-safe appenv link.
    (base / "appenv").write_bytes(Path(appenv.__file__).read_bytes())
    (base / "http").symlink_to("appenv")

    _raise_on_uv_lock(
        monkeypatch,
        subprocess.CalledProcessError(returncode=1, cmd=["uv", "lock"]),
    )

    env = app_env()
    with pytest.raises(subprocess.CalledProcessError):
        env.init(_init_namespace())

    # The pre-existing link survived rollback (still points at appenv).
    assert (base / "http").is_symlink()
    assert os.readlink(base / "http") == "appenv"


# Non-interactive and edge case init paths


def test_init_non_interactive_no_existing(tmp_path, monkeypatch):
    """Non-interactive init creates pyproject without existing file."""
    from unittest.mock import MagicMock

    monkeypatch.setattr(
        appenv,
        "ensure_uv",
        lambda d: MagicMock(
            spec=appenv.UvBin,
            cmd=lambda a, **kw: "",
            version=appenv.UvVersion(0, 7, 0),
            bin=Path("/usr/bin/uv"),
        ),
    )

    settings = appenv.AppEnvSettings(verbose=False, extras=[], basedir=tmp_path)
    env = appenv.AppEnv(tmp_path, settings)

    args = argparse.Namespace(
        force=False,
        binary="myapp",
        deps=["myapp"],
        name="myproject",
        python_version="3.12",
        description=None,
        path=None,
    )

    env.init(args)
    content = (tmp_path / "pyproject.toml").read_text()
    assert 'name = "myproject"' in content


def test_init_no_tty_exits(tmp_path, monkeypatch, capsys):
    """init without TTY and without required flags exits with usage."""
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    settings = appenv.AppEnvSettings(verbose=False, extras=[], basedir=tmp_path)
    env = appenv.AppEnv(tmp_path, settings)

    args = argparse.Namespace(
        force=False,
        binary=None,
        deps=None,
        name=None,
        python_version=None,
        path=None,
    )

    with pytest.raises(SystemExit) as exc_info:
        env.init(args)
    assert exc_info.value.code == appenv.EXIT_CODE_USAGE

    # The usage hint must list every non-interactive flag so users can
    # bootstrap without reading the source. Regression guard for drift
    # when new flags are added to the init subparser.
    captured = capsys.readouterr()
    assert "Required: --binary, --dep" in captured.err
    for flag in ("--name", "--python-version", "--description"):
        assert flag in captured.err, (
            f"no-TTY usage hint must mention optional flag {flag}"
        )


def test_init_interactive_new_with_deps_and_binary(tmp_path, monkeypatch):
    """Interactive wizard: deps and binary name are set correctly."""
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(appenv, "ensure_uv", lambda d: _mock_uv())

    inputs = iter(["mytool", "", "mytool", "proj", "Desc", "3.13"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    settings = appenv.AppEnvSettings(verbose=False, extras=[], basedir=tmp_path)
    env = appenv.AppEnv(tmp_path, settings)
    args = argparse.Namespace(
        force=False,
        binary=None,
        deps=None,
        name=None,
        python_version=None,
        path=None,
    )
    env.init(args)
    content = (tmp_path / "pyproject.toml").read_text()
    assert "mytool" in content


def test_init_interactive_new_default_binary(tmp_path, monkeypatch):
    """Interactive wizard: empty binary name defaults to 'app'."""
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(appenv, "ensure_uv", lambda d: _mock_uv())

    inputs = iter(["", "", "", "Desc", "3.13"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    settings = appenv.AppEnvSettings(verbose=False, extras=[], basedir=tmp_path)
    env = appenv.AppEnv(tmp_path, settings)
    args = argparse.Namespace(
        force=False,
        binary=None,
        deps=None,
        name=None,
        python_version=None,
        path=None,
    )
    env.init(args)
    content = (tmp_path / "pyproject.toml").read_text()
    assert "app" in content


def test_init_interactive_eof_exits_64_new(tmp_path, monkeypatch, capsys):
    """Interactive init with stdin EOF exits 64 with a usage hint, no traceback.

    Verifies fix-contract-treue::eof-clean-exit: a closed stdin during the
    wizard surfaces as a clean USAGE exit pointing at the non-interactive form,
    not a raw EOFError traceback.
    """
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)

    def raise_eof(*args, **kwargs):
        raise EOFError()

    monkeypatch.setattr("builtins.input", raise_eof)

    settings = appenv.AppEnvSettings(verbose=False, extras=[], basedir=tmp_path)
    env = appenv.AppEnv(tmp_path, settings)
    args = argparse.Namespace(
        force=False,
        binary=None,
        deps=None,
        name=None,
        python_version=None,
        path=None,
    )

    with pytest.raises(SystemExit) as exc_info:
        env.init(args)

    assert exc_info.value.code == appenv.EXIT_CODE_USAGE
    captured = capsys.readouterr()
    assert "end of input" in captured.err
    assert "appenv init --binary" in captured.err
