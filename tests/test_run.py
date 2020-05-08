import appenv
import io
import os.path
import subprocess


def test_bootstrap_lockfile_existing_venv_broken_python():
    pass


def test_bootstrap_lockfile_missing_dependency():
    pass


def test_bootstrap_and_run_with_lockfile(meta_args, workdir, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('batou\nbatou==2.0b7\n\n'))
    meta_args.appenvdir = os.path.join(workdir, 'batou', '.batou')
    meta_args.base = os.path.join(workdir, 'batou')
    meta_args.appname = 'batou'

    appenv.init([], meta_args)
    appenv.update_lockfile([], meta_args)
    os.chdir(workdir / 'batou')
    output = subprocess.check_output('./batou --help', shell=True)
    assert output.startswith(b'usage: batou')


def test_bootstrap_and_run_python_with_lockfile(meta_args, workdir,
                                                monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('batou\n\n\n'))
    meta_args.appenvdir = os.path.join(workdir, 'batou', '.batou')
    meta_args.base = os.path.join(workdir, 'batou')
    meta_args.appname = 'batou'

    appenv.init([], meta_args)
    appenv.update_lockfile([], meta_args)
    os.chdir(workdir / 'batou')
    output = subprocess.check_output(
        './batou appenv-python -c "print(1)"', shell=True)
    assert output == b'1\n'
