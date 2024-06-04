import os.path

import appenv


def test_reset_nonexisting_envdir_silent(tmpdir):
    env = appenv.AppEnv(os.path.join(tmpdir, 'ducker'), os.getcwd())
    assert not os.path.exists(env.appenv_dir)
    env.reset()
    assert not os.path.exists(env.appenv_dir)
    assert os.path.exists(str(tmpdir))


def test_reset_removes_envdir_with_subdirs(tmpdir):
    env = appenv.AppEnv(os.path.join(tmpdir, 'ducker'), os.getcwd())
    os.makedirs(env.appenv_dir)
    assert os.path.exists(env.appenv_dir)
    env.reset()
    assert not os.path.exists(env.appenv_dir)
    assert os.path.exists(str(tmpdir))
