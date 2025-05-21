import os
import json
from pathlib import Path
import appenv


def test_prepare_writes_vscode_settings(tmp_path):
    project_dir = tmp_path / "risclog_test"
    project_dir.mkdir()
    (project_dir / ".appenv").write_text("lib/\n")

    lib_path = project_dir / "lib" / "python3.11" / "site-packages"
    ns_root = lib_path / "risclog_test"
    (ns_root / "subpackage").mkdir(parents=True)

    bin_dir = project_dir / "bin"
    bin_dir.mkdir(parents=True)
    python_path = bin_dir / "python"
    python_path.write_text("#!/bin/sh\necho fake-python\n")
    python_path.chmod(0o755)
    (project_dir / "pyvenv.cfg").write_text("")

    env = appenv.AppEnv(project_dir, os.getcwd())
    env.env_dir = project_dir

    env._ensure_namespace_roots()
    env._write_vscode_settings()

    assert (ns_root / "__init__.py").exists()
    settings_file = Path(".vscode", "settings.json")
    assert settings_file.exists()
    settings = json.loads(settings_file.read_text())
    settings_file.unlink()

    assert settings["python.defaultInterpreterPath"] == str(python_path)
    assert settings["python.analysis.extraPaths"] == [str(lib_path)]
