import appenv
import os.path


def test_reset_nonexisting_envdir_silent(meta_args, tmpdir):
    assert not os.path.exists(meta_args.appenvdir)
    appenv.reset([], meta_args)
    assert not os.path.exists(meta_args.appenvdir)
    assert os.path.exists(tmpdir)


def test_reset_removes_envdir_with_subdirs(meta_args, tmpdir):
    os.makedirs(meta_args.appenvdir)
    assert os.path.exists(meta_args.appenvdir)
    appenv.reset([], meta_args)
    assert not os.path.exists(meta_args.appenvdir)
    assert os.path.exists(tmpdir)
