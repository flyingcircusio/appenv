import appenv
import io
import unittest.mock
import os
import pytest
import shutil
import sys


def test_init_and_create_lockfile(workdir, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('ducker\nducker<2.0.2\n\n'))

    env = appenv.AppEnv(os.path.join(workdir, 'ducker'))
    env.init()

    lockfile = os.path.join(workdir, "ducker", "requirements.lock")
    assert not os.path.exists(lockfile)

    env.update_lockfile()

    assert os.path.exists(lockfile)
    with open(lockfile) as f:
        lockfile_content = f.read()
    assert (lockfile_content == """\
# appenv-requirements-hash: ffa75c00de4879b41008d0e9f6b9953cf7d65bb5f5b85d1d049e783b2486614d
ducker==2.0.1
""")  # noqa


@pytest.mark.skipif(
    sys.version_info[0:2] != (3, 6), reason='Isolated CI builds')
def test_update_lockfile_minimal_python(workdir, monkeypatch):
    """It uses the minimal python version even if it is not best python."""
    monkeypatch.setattr('sys.stdin',
                        io.StringIO('pytest\npytest==6.1.2\nppytest\n'))

    env = appenv.AppEnv(os.path.join(workdir, 'ppytest'))
    env.init()

    lockfile = os.path.join(workdir, "ppytest", "requirements.lock")
    requirements_file = os.path.join(workdir, "ppytest", "requirements.txt")

    with open(requirements_file, "r+") as f:
        lines = f.readlines()
        lines.insert(0, "# appenv-python-preference: 3.8,3.6,3.9\n")
        f.seek(0)
        f.writelines(lines)

    env.update_lockfile()

    assert os.path.exists(lockfile)
    with open(lockfile) as f:
        lockfile_content = f.read()
    # replace underscore with dashes for python 3.6 testing
    # some versions do not normalize the name like newer python versions
    lockfile_content = lockfile_content.replace("_", "-")
    assert "pytest==6.1.2" in lockfile_content
    assert "importlib-metadata==" in lockfile_content
    assert "typing-extensions==" in lockfile_content


@pytest.mark.skipif(
    sys.version_info[0:2] < (3, 8), reason='Isolated CI builds')
def test_update_lockfile_missing_minimal_python(workdir, monkeypatch):
    """It raises an error if the minimal python is not available."""
    monkeypatch.setattr('sys.stdin',
                        io.StringIO('pytest\npytest==6.1.2\nppytest\n'))

    env = appenv.AppEnv(os.path.join(workdir, 'ppytest'))
    env.init()

    requirements_file = os.path.join(workdir, "ppytest", "requirements.txt")

    with open(requirements_file, "r+") as f:
        lines = f.readlines()
        lines[0] = "# appenv-python-preference: 3.8,3.6,3.9\n"
        f.seek(0)
        f.writelines(lines)

    old_which = shutil.which

    def new_which(string):
        if string == "python3.6":
            return None
        else:
            return old_which(string)

    with unittest.mock.patch('shutil.which') as which:
        which.side_effect = new_which
        with pytest.raises(SystemExit) as e:
            env.update_lockfile()
    assert e.value.code == 66
