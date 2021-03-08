import io
import os

import appenv


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
ducker==2.0.1
""")
