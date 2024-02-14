import os
import appenv
import io


def test_prepare_creates_envdir(workdir, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('ducker\nducker<2.0.2\n\n'))
    os.makedirs(os.path.join(workdir, 'ducker'))

    env = appenv.AppEnv(os.path.join(workdir, 'ducker'))
    env.init()
    assert not os.path.exists(env.appenv_dir)
    env.update_lockfile()
    env.prepare()
    assert os.path.exists(env.appenv_dir)
