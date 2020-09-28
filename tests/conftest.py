import pytest
import os.path


@pytest.yield_fixture
def workdir(tmpdir):
    old = os.getcwd()
    os.chdir(str(tmpdir))
    yield str(tmpdir)
    os.chdir(old)


@pytest.fixture
def meta_args(tmpdir):
    class Args(object):
        pass

    m_args = Args()
    m_args.appenvdir = os.path.join(str(tmpdir), ".app")
    m_args.base = str(tmpdir)
    m_args.unclean = False
    return m_args
