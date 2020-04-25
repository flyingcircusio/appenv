import appenv
import os
import io


def test_init(meta_args, workdir, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('ducker\n\n\n'))
    appenv.init([], meta_args)
    assert os.path.exists(os.path.join(workdir, 'ducker'))
    with open(os.path.join(workdir, 'ducker', 'ducker')) as f:
        ducker_appenv = f.read()
    with open(appenv.__file__) as f:
        original_appenv = f.read()

    with open(os.path.join(workdir, 'ducker', 'requirements.txt')) as f:
        requirements = f.read()

    assert requirements == 'ducker\n'
    assert ducker_appenv == original_appenv

    # calling it again doesn't break:
    monkeypatch.setattr('sys.stdin', io.StringIO('ducker\n\n\n'))

    os.chdir(workdir)
    assert os.path.exists(os.path.join(workdir, 'ducker'))
    with open(os.path.join(workdir, 'ducker', 'ducker')) as f:
        ducker_appenv = f.read()
    with open(appenv.__file__) as f:
        original_appenv = f.read()

    with open(os.path.join(workdir, 'ducker', 'requirements.txt')) as f:
        requirements = f.read()

    assert requirements == 'ducker\n'
    assert ducker_appenv == original_appenv


def test_init_explicit_target(meta_args, workdir, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('ducker\n\nbaz\n'))
    appenv.init([], meta_args)
    assert os.path.exists(os.path.join(workdir, 'baz'))
    with open(os.path.join(workdir, 'baz', 'ducker')) as f:
        ducker_appenv = f.read()
    with open(appenv.__file__) as f:
        original_appenv = f.read()

    with open(os.path.join(workdir, 'baz', 'requirements.txt')) as f:
        requirements = f.read()

    assert requirements == 'ducker\n'
    assert ducker_appenv == original_appenv


def test_init_explicit_package_and_target(meta_args, workdir, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('foo\nbar\nbaz\n'))
    appenv.init([], meta_args)
    assert os.path.exists(os.path.join(workdir, 'baz'))
    with open(os.path.join(workdir, 'baz', 'foo')) as f:
        ducker_appenv = f.read()
    with open(appenv.__file__) as f:
        original_appenv = f.read()

    with open(os.path.join(workdir, 'baz', 'requirements.txt')) as f:
        requirements = f.read()

    assert requirements == 'bar\n'
    assert ducker_appenv == original_appenv
