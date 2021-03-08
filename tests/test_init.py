import io
import os

import appenv


def test_init(workdir, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("ducker\n\n\n"))

    assert not os.path.exists(os.path.join(workdir, "ducker"))

    env = appenv.AppEnv(os.path.join(workdir, 'ducker'))
    env.init()

    assert os.readlink(os.path.join(workdir, "ducker", "ducker")) == 'appenv'

    with open(os.path.join(workdir, "ducker", "appenv")) as f:
        ducker_appenv = f.read()
    with open(appenv.__file__) as f:
        original_appenv = f.read()
    assert ducker_appenv == original_appenv

    with open(os.path.join(workdir, "ducker", "requirements.txt")) as f:
        requirements = f.read()

    assert requirements == "ducker\n"

    # calling it again doesn't break:
    monkeypatch.setattr("sys.stdin", io.StringIO("ducker\n\n\n"))
    env.init()

    assert os.readlink(os.path.join(workdir, "ducker", "ducker")) == 'appenv'

    with open(os.path.join(workdir, "ducker", "appenv")) as f:
        ducker_appenv = f.read()
    with open(appenv.__file__) as f:
        original_appenv = f.read()
    assert ducker_appenv == original_appenv

    with open(os.path.join(workdir, "ducker", "requirements.txt")) as f:
        requirements = f.read()

    assert requirements == "ducker\n"


def test_init_explicit_target(workdir, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("ducker\n\nbaz\n"))

    env = appenv.AppEnv(os.path.join(workdir, 'ducker'))
    env.init()

    assert os.path.exists(os.path.join(workdir, "baz"))
    with open(os.path.join(workdir, "baz", "ducker")) as f:
        ducker_appenv = f.read()
    with open(appenv.__file__) as f:
        original_appenv = f.read()

    with open(os.path.join(workdir, "baz", "requirements.txt")) as f:
        requirements = f.read()

    assert requirements == "ducker\n"
    assert ducker_appenv == original_appenv


def test_init_explicit_package_and_target(workdir, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("foo\nbar\nbaz\n"))

    env = appenv.AppEnv(os.path.join(workdir, 'ducker'))
    env.init()

    assert os.path.exists(os.path.join(workdir, "baz"))
    with open(os.path.join(workdir, "baz", "foo")) as f:
        ducker_appenv = f.read()
    with open(appenv.__file__) as f:
        original_appenv = f.read()

    with open(os.path.join(workdir, "baz", "requirements.txt")) as f:
        requirements = f.read()

    assert requirements == "bar\n"
    assert ducker_appenv == original_appenv
