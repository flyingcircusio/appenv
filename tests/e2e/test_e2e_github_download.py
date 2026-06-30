# SPDX-FileCopyrightText: 2020 Flying Circus
"""E2E tests for GitHub UV download with local mock server.

Tests _try_uv_from_installer() and _uv_platform_triple() — the GitHub release
download fallback path in the uv discovery chain (lines 647-725 of appenv.py).

Uses a real local HTTP server serving a fake tarball to exercise the actual
download + extraction + validation code path.

Run with: uv run pytest tests/integration/test_e2e_github_download.py -v
"""

import io
import stat
import tarfile
import threading
from http import server

import pytest

from appenv import UvBin, UvVersion

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_fake_uv_binary(directory):
    """Create a minimal executable script that prints ``uv 0.5.0``."""
    directory.mkdir(parents=True, exist_ok=True)
    binary = directory / "uv"
    binary.write_text("#!/bin/sh\necho 'uv 0.5.0'\n")
    binary.chmod(binary.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return binary


def _create_fake_tarball(triple, fake_binary):
    """Package *fake_binary* as ``uv-{triple}/uv`` inside a tar.gz."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tar.gettarinfo(str(fake_binary), arcname=f"uv-{triple}/uv")
        info.mode = 0o755
        with open(str(fake_binary), "rb") as fh:
            tar.addfile(info, fh)
    return buf.getvalue()


class _FakeReleaseHandler(server.BaseHTTPRequestHandler):
    """Serves a static tarball blob for every GET request."""

    tarball_data: bytes = b""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/gzip")
        self.send_header("Content-Length", str(len(self.tarball_data)))
        self.end_headers()
        self.wfile.write(self.tarball_data)

    def log_message(self, format, *args):
        pass  # silence per-request logs


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_github_server(tmp_path):
    """Local HTTP server serving a fake uv release tarball.

    Yields ``(base_url, triple)`` and shuts down the server on teardown.
    """
    triple = UvBin._uv_platform_triple()
    if not triple:
        pytest.skip("unsupported platform for mock server test")

    fake_binary = _create_fake_uv_binary(tmp_path / "_fake_uv_src")
    tarball = _create_fake_tarball(triple, fake_binary)
    _FakeReleaseHandler.tarball_data = tarball

    httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), _FakeReleaseHandler)
    httpd.timeout = 5
    port = httpd.server_address[1]

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}", triple

    httpd.shutdown()
    thread.join(timeout=5)
    httpd.server_close()


def _make_uv_bin(tmp_path):
    """Build a UvBin instance without triggering __init__ discovery."""
    appenv_dir = tmp_path / ".appenv"
    appenv_dir.mkdir(parents=True, exist_ok=True)

    uv_bin = UvBin.__new__(UvBin)
    uv_bin.appenv_dir = appenv_dir
    uv_bin.uv_dir = appenv_dir / ".uv"
    uv_bin.managed_uv = uv_bin.uv_dir / "bin" / "uv"
    return uv_bin


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_e2e_github_download_success(tmp_path, monkeypatch, mock_github_server):
    """Full E2E: download from mock server → extract → validate binary.

    Exercises lines 654-695 of _try_uv_from_installer().
    """
    server_url, _triple = mock_github_server

    uv_bin = _make_uv_bin(tmp_path)

    # Redirect urllib.request.urlopen to our local server
    import urllib.request

    real_urlopen = urllib.request.urlopen

    def _redirecting_urlopen(url, **kwargs):
        if "github.com" in str(url):
            return real_urlopen(server_url, **kwargs)
        return real_urlopen(url, **kwargs)

    monkeypatch.setattr("urllib.request.urlopen", _redirecting_urlopen)

    result = uv_bin._try_uv_from_installer()

    assert result is not None, "_try_uv_from_installer returned None"
    assert result == uv_bin.managed_uv
    assert result.exists(), f"extracted binary not found at {result}"

    # Binary must be executable
    assert result.stat().st_mode & stat.S_IEXEC

    # get_uv_version must succeed on the real extracted binary
    version = UvBin.get_uv_version(result)
    assert version.valid, f"version invalid: {version}"
    assert version == UvVersion(0, 5, 0)


def test_e2e_platform_triple():
    """_uv_platform_triple() returns a valid triple on the current platform.

    Exercises lines 705-725 of _uv_platform_triple().
    """
    import platform
    import sys

    triple = UvBin._uv_platform_triple()

    machine = platform.machine().lower()
    supported_machines = ("x86_64", "amd64", "aarch64", "arm64", "armv7l")

    if machine in supported_machines and sys.platform in ("linux", "darwin"):
        assert triple is not None, f"expected triple for {machine}/{sys.platform}"
        assert "-" in triple, f"triple should contain '-': {triple}"

        if sys.platform == "linux":
            assert "linux" in triple
        elif sys.platform == "darwin":
            assert "darwin" in triple


def test_e2e_github_download_unsupported_platform(tmp_path, monkeypatch):
    """_try_uv_from_installer returns None when platform triple is unsupported."""
    uv_bin = _make_uv_bin(tmp_path)

    # Return an exotic machine arch so _uv_platform_triple returns None
    monkeypatch.setattr("platform.machine", lambda: "riscv128")

    result = uv_bin._try_uv_from_installer()
    assert result is None


def test_e2e_github_download_network_error(tmp_path, monkeypatch):
    """_try_uv_from_installer returns None on URLError."""
    import urllib.error

    uv_bin = _make_uv_bin(tmp_path)

    def _failing_urlopen(url, **kwargs):
        reason = "Connection refused"
        raise urllib.error.URLError(reason)

    monkeypatch.setattr("urllib.request.urlopen", _failing_urlopen)

    result = uv_bin._try_uv_from_installer()
    assert result is None


def test_e2e_github_download_invalid_tarball(tmp_path, monkeypatch):
    """_try_uv_from_installer returns None when tarball data is corrupt."""
    uv_bin = _make_uv_bin(tmp_path)

    class _FakeResponse:
        def read(self):
            return b"this is not a valid tarball"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr("urllib.request.urlopen", lambda url, **kwargs: _FakeResponse())

    result = uv_bin._try_uv_from_installer()
    assert result is None


def test_e2e_github_download_tarball_without_uv_entry(tmp_path, monkeypatch):
    """_try_uv_from_installer returns None when tarball has no ``*/uv`` member."""
    uv_bin = _make_uv_bin(tmp_path)

    # Build a tarball with a file that does NOT end in /uv
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        data = b"dummy content\n"
        info = tarfile.TarInfo(name="uv-x86_64-unknown-linux-gnu/README.md")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    tarball = buf.getvalue()

    class _FakeResponse:
        def __init__(self, data):
            self._data = data

        def read(self):
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda url, **kwargs: _FakeResponse(tarball),
    )

    result = uv_bin._try_uv_from_installer()
    assert result is None
