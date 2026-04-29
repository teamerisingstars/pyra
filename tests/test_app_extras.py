"""Tests for static file serving and error pages."""
from __future__ import annotations

import os
import tempfile

from starlette.testclient import TestClient

from pyra import App


def fresh_app() -> App:
    """Return a new App instance (avoids _PAGES global state pollution)."""
    return App()


def test_404_default():
    app = fresh_app()
    client = TestClient(app._starlette, raise_server_exceptions=False)
    resp = client.get("/no-such-page")
    assert resp.status_code == 404
    assert "404" in resp.text


def test_static_files_served():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write a test file
        test_file = os.path.join(tmpdir, "hello.txt")
        with open(test_file, "w") as f:
            f.write("hello static")

        app = fresh_app()
        app.mount_static("/static", directory=tmpdir)
        client = TestClient(app._starlette)
        resp = client.get("/static/hello.txt")
        assert resp.status_code == 200
        assert resp.text == "hello static"


def test_static_missing_file_404():
    with tempfile.TemporaryDirectory() as tmpdir:
        app = fresh_app()
        app.mount_static("/static", directory=tmpdir)
        client = TestClient(app._starlette, raise_server_exceptions=False)
        resp = client.get("/static/nope.txt")
        assert resp.status_code == 404
