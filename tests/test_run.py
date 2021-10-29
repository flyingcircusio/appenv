import pytest
import io
import os.path
import subprocess
import sys

import appenv


def test_bootstrap_lockfile_existing_venv_broken_python():
    pass


def test_bootstrap_lockfile_missing_dependency():
    pass


def test_bootstrap_and_run_with_lockfile(workdir, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("ducker\nducker==2.0.1\n\n"))

    env = appenv.AppEnv(os.path.join(workdir, 'ducker'))

    env.init()
    env.update_lockfile()

    os.chdir(os.path.join(workdir, "ducker"))
    with open("ducker", "r") as f:
        # Ensure we're called with the Python-interpreter-under-test.
        script = "#!{}\n{}".format(sys.executable, f.read())
    with open("ducker", "w") as f:
        f.write(script)

    output = subprocess.check_output("./ducker --help", shell=True)
    assert output.startswith(b"usage: Ducker")


def test_bootstrap_and_run_python_with_lockfile(workdir, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("ducker\nducker==2.0.1\n\n"))

    env = appenv.AppEnv(os.path.join(workdir, 'ducker'))

    env.init()
    env.update_lockfile()
    os.chdir(os.path.join(workdir, "ducker"))
    with open("ducker", "r") as f:
        # Ensure we're called with the Python-interpreter-under-test.
        script = "#!{}\n{}".format(sys.executable, f.read())
    with open("ducker", "w") as f:
        f.write(script)

    output = subprocess.check_output(
        './appenv python -c "print(1)"', shell=True)
    assert output == b"1\n"


def test_bootstrap_and_run_without_lockfile(workdir, monkeypatch):
    """It raises as error if no requirements.lock is present."""
    monkeypatch.setattr("sys.stdin", io.StringIO("ducker\nducker==2.0.1\n\n"))

    env = appenv.AppEnv(os.path.join(workdir, 'ducker'))

    env.init()

    os.chdir(os.path.join(workdir, "ducker"))
    with open("ducker", "r") as f:
        # Ensure we're called with the Python-interpreter-under-test.
        script = "#!{}\n{}".format(sys.executable, f.read())
    with open("ducker", "w") as f:
        f.write(script)

    with pytest.raises(subprocess.CalledProcessError) as err:
        subprocess.check_output(["./ducker", "--help"])
    assert err.value.output == (
        b"No requirements.lock found. Generate it using"
        b" ./appenv update-lockfile.\n")
