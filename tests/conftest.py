import os.path

import pytest


@pytest.yield_fixture
def workdir(tmpdir):
    old = os.getcwd()
    os.chdir(str(tmpdir))
    yield str(tmpdir)
    os.chdir(old)
