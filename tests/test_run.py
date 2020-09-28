import appenv
import io
import os.path
import subprocess
import sys


def test_bootstrap_lockfile_existing_venv_broken_python():
    pass


def test_bootstrap_lockfile_missing_dependency():
    pass


def test_bootstrap_and_run_with_lockfile(meta_args, workdir, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("ducker\nducker==2.0.1\n\n"))
    meta_args.appenvdir = os.path.join(workdir, "ducker", ".ducker")
    meta_args.base = os.path.join(workdir, "ducker")
    meta_args.appname = "ducker"

    appenv.init([], meta_args)
    appenv.update_lockfile([], meta_args)
    os.chdir(os.path.join(workdir, "ducker"))
    with open("ducker", "r") as f:
        # Ensure we're called with the Python-interpreter-under-test.
        script = "#!{}\n{}".format(sys.executable, f.read())
    with open("ducker", "w") as f:
        f.write(script)

    output = subprocess.check_output("./ducker --help", shell=True)
    assert output.startswith(b"usage: Ducker")


def test_bootstrap_and_run_python_with_lockfile(
    meta_args, workdir, monkeypatch
):
    monkeypatch.setattr("sys.stdin", io.StringIO("ducker\nducker==2.0.1\n\n"))
    meta_args.appenvdir = os.path.join(workdir, "ducker", ".ducker")
    meta_args.base = os.path.join(workdir, "ducker")
    meta_args.appname = "ducker"

    appenv.init([], meta_args)
    appenv.update_lockfile([], meta_args)
    os.chdir(os.path.join(workdir, "ducker"))
    with open("ducker", "r") as f:
        # Ensure we're called with the Python-interpreter-under-test.
        script = "#!{}\n{}".format(sys.executable, f.read())
    with open("ducker", "w") as f:
        f.write(script)

    output = subprocess.check_output(
        './ducker appenv-python -c "print(1)"', shell=True
    )
    assert output == b"1\n"


def test_bootstrap_and_run_cmd_with_lockfile(meta_args, workdir, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("ducker\nducker==2.0.1\n\n"))
    meta_args.appenvdir = os.path.join(workdir, "ducker", ".ducker")
    meta_args.base = os.path.join(workdir, "ducker")
    meta_args.appname = "ducker"

    appenv.init([], meta_args)
    appenv.update_lockfile([], meta_args)
    os.chdir(os.path.join(workdir, "ducker"))
    with open("ducker", "r") as f:
        # Ensure we're called with the Python-interpreter-under-test.
        script = "#!{}\n{}".format(sys.executable, f.read())
    with open("ducker", "w") as f:
        f.write(script)

    output = subprocess.check_output(
        './ducker appenv-run python -c "print(1)"', shell=True
    )
    assert output == b"1\n"
