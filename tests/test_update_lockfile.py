import appenv
import os
import io


def test_init_and_create_lockfile(meta_args, workdir, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('batou\n\n\n'))
    meta_args.appenvdir = os.path.join(workdir, 'batou', '.batou')
    meta_args.base = os.path.join(workdir, 'batou')

    appenv.init([], meta_args)

    lockfile = os.path.join(workdir, 'batou', 'requirements.lock')
    assert not os.path.exists(lockfile)

    appenv.update_lockfile([], meta_args)

    assert os.path.exists(lockfile)
    with open(lockfile) as f:
        lockfile_content = f.read()
    assert lockfile_content == """\
apipkg==1.5
batou==1.13.0
certifi==2020.4.5.1
chardet==3.0.4
execnet==1.7.1
idna==2.9
Jinja2==2.11.2
MarkupSafe==1.1.1
py==1.8.1
PyYAML==5.3.1
requests==2.23.0
urllib3==1.25.9
"""
