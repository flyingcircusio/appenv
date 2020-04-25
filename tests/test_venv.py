import appenv
import os.path


def test_new_venv(tmpdir):
    appenv.ensure_venv(os.path.join(tmpdir, 'venv'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'bin', 'pip3'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'bin', 'python'))
    assert os.path.exists(os.path.join(tmpdir, 'venv', 'lib'))
