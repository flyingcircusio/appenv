import appenv
import os.path


def test_new_venv(tmpdir):
    tmpdir = str(tmpdir)
    appenv.ensure_venv(os.path.join(tmpdir, 'venv'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'bin', 'pip3'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'bin', 'python'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'lib'))

    # doesn't break things
    appenv.ensure_venv(os.path.join(tmpdir, 'venv'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'bin', 'pip3'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'bin', 'python'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'lib'))


def test_new_broken_venv_recreated(tmpdir):
    tmpdir = str(tmpdir)
    appenv.ensure_venv(os.path.join(tmpdir, 'venv'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'bin', 'pip3'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'bin', 'python'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'lib'))

    os.unlink(os.path.join(tmpdir, 'venv', 'bin', 'pip3'))
    with open(os.path.join(tmpdir, 'venv', 'asdf'), 'w'):
        pass
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'asdf'))

    # re-creates the venv
    appenv.ensure_venv(os.path.join(tmpdir, 'venv'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'bin', 'pip3'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'bin', 'python'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'lib'))
    assert not os.path.exists(os.path.join(tmpdir, 'venv', 'asdf'))
