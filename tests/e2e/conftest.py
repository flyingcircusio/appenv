# SPDX-FileCopyrightText: 2020 Flying Circus
"""Shared E2E test fixtures for integration tests."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _base_env(**overrides):
    """Hermetic environment for e2e subprocess/pexpect boundaries.

    Starts from ``os.environ`` and applies the test's intended overrides.
    ``APPENV_BEST_PYTHON`` prevents ensure_best_python re-exec;
    ``NO_COLOR`` disables argparse color output for stable assertions.
    """
    env = {**os.environ}
    env.update({"NO_COLOR": "1", "APPENV_BEST_PYTHON": "1"})
    env.update(overrides)
    return env


@pytest.fixture
def setup_isolated_appenv():
    """Copy appenv script to isolated directory for testing."""

    def _setup(target_path: Path) -> Path:
        import appenv

        src_appenv = Path(appenv.__file__).resolve()
        dst_appenv = target_path / "appenv"
        shutil.copy(src_appenv, dst_appenv)
        dst_appenv.chmod(0o755)
        return dst_appenv

    return _setup


@pytest.fixture
def setup_project_with_lockfile():
    """Create a minimal project with pyproject.toml + uv.lock."""

    def _setup(tmp_path: Path, app_name: str = "mycmd") -> Path:
        import appenv

        base = tmp_path / "project"
        base.mkdir(parents=True, exist_ok=True)

        src_appenv = Path(appenv.__file__).resolve()

        # Copy appenv as the application name
        dst_appenv = base / app_name
        shutil.copy(src_appenv, dst_appenv)
        dst_appenv.chmod(0o755)

        # Ensure "appenv" copy exists for lockfile generation
        appenv_script = base / "appenv"
        if not appenv_script.exists():
            shutil.copy(src_appenv, appenv_script)
            appenv_script.chmod(0o755)

        # Create a minimal package with a simple CLI
        pkg_dir = base / "mypkg"
        pkg_dir.mkdir(exist_ok=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "cli.py").write_text(
            "import sys\n"
            "def main():\n"
            '    if "--help" in sys.argv:\n'
            '        print("My CLI - help")\n'
            "        return 0\n"
            '    if "--version" in sys.argv:\n'
            '        print("1.0.0")\n'
            "        return 0\n"
            '    print("Hello from my CLI")\n'
            "    return 0\n"
            "\n"
            'if __name__ == "__main__":\n'
            "    sys.exit(main())\n"
        )

        # Create pyproject.toml with the package and console script
        (base / "pyproject.toml").write_text(
            "[build-system]\n"
            'requires = ["setuptools>=61.0"]\n'
            'build-backend = "setuptools.build_meta"\n'
            "\n"
            "[project]\n"
            'name = "test-app"\n'
            'version = "0.1.0"\n'
            'description = "Test application"\n'
            "dependencies = []\n"
            'requires-python = ">=3.10"\n'
            "\n"
            "[project.scripts]\n"
            f'{app_name} = "mypkg.cli:main"\n'
            "\n"
            "[tool.setuptools.packages.find]\n"
            'where = ["."]\n'
        )

        # Generate lockfile via appenv update-lockfile
        result = subprocess.run(
            [sys.executable, str(appenv_script), "update-lockfile"],
            capture_output=True,
            text=True,
            cwd=str(base),
            timeout=60,
            env=_base_env(),
        )
        assert result.returncode == 0, f"Lockfile failed: {result.stderr}"
        assert (base / "uv.lock").exists()

        return base

    return _setup


@pytest.fixture
def setup_prepared_project(setup_project_with_lockfile):
    """Full project with prepared venv.

    Calls setup_project_with_lockfile then appenv prepare.
    """

    def _setup(tmp_path: Path, app_name: str = "mycmd") -> Path:
        base = setup_project_with_lockfile(tmp_path, app_name)

        # Run appenv prepare via subprocess
        result = subprocess.run(
            [sys.executable, str(base / "appenv"), "prepare"],
            capture_output=True,
            text=True,
            cwd=str(base),
            timeout=60,
            env=_base_env(),
        )
        assert result.returncode == 0, f"Prepare failed: {result.stderr}"

        return base

    return _setup
