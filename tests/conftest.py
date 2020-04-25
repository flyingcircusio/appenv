import pytest
import os.path


@pytest.yield_fixture
def workdir(tmpdir):
    old = os.getcwd()
    os.chdir(tmpdir)
    yield tmpdir
    os.chdir(old)


@pytest.fixture
def meta_args(tmpdir):
    class Args(object):
        pass
    m_args = Args()
    m_args.appenvdir = os.path.join(str(tmpdir), '.app')
    return m_args
