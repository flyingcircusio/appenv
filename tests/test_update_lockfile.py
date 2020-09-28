import appenv
import os
import io


def test_init_and_create_lockfile(meta_args, workdir, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("ducker\nducker<2.0.2\n\n"))
    meta_args.appenvdir = os.path.join(workdir, "ducker", ".ducker")
    meta_args.base = os.path.join(workdir, "ducker")

    appenv.init([], meta_args)

    lockfile = os.path.join(workdir, "ducker", "requirements.lock")
    assert not os.path.exists(lockfile)

    appenv.update_lockfile([], meta_args)

    assert os.path.exists(lockfile)
    with open(lockfile) as f:
        lockfile_content = f.read()
    assert (
        lockfile_content
        == """\
ducker==2.0.1
"""
    )
