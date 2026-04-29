"""Tests for FileInput component and upload endpoint."""
from __future__ import annotations

import io
from starlette.testclient import TestClient

from pyra import App
from pyra.components import FileInput, LoadingButton
from pyra.app import get_upload


# --- Component tests ---

def test_loading_button_default():
    btn = LoadingButton("Save")
    assert btn.tag == "button"
    assert btn.children == ["Save"]
    assert "disabled" not in btn.props


def test_loading_button_shows_loading_label():
    btn = LoadingButton("Save", loading=True, loading_label="Saving…")
    assert btn.children == ["Saving…"]
    assert btn.props.get("disabled") == "true"


def test_loading_button_disabled_no_handler():
    called = []
    btn = LoadingButton("Save", on_click=lambda: called.append(1), loading=True)
    assert "click" not in btn.handlers


def test_file_input_tag():
    fi = FileInput()
    assert fi.tag == "input"
    assert fi.props.get("type") == "file"


def test_file_input_accept():
    fi = FileInput(accept="image/*")
    assert fi.props["accept"] == "image/*"


def test_file_input_multiple():
    fi = FileInput(multiple=True)
    assert fi.props.get("multiple") == "true"


# --- Upload endpoint tests ---

def test_upload_endpoint_no_file():
    app = App()
    client = TestClient(app._starlette, raise_server_exceptions=False)
    resp = client.post("/__pyra__/upload", data={})
    assert resp.status_code == 400


def test_upload_endpoint_with_file():
    app = App()
    client = TestClient(app._starlette)
    file_content = b"hello upload"
    resp = client.post(
        "/__pyra__/upload",
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "test.txt"
    assert data["size"] == len(file_content)
    assert "upload_id" in data
    assert "path" not in data   # server path must not leak to client


def test_get_upload_after_upload():
    app = App()
    client = TestClient(app._starlette)
    resp = client.post(
        "/__pyra__/upload",
        files={"file": ("hello.txt", io.BytesIO(b"data"), "text/plain")},
    )
    uid = resp.json()["upload_id"]
    meta = get_upload(uid)
    assert meta is not None
    assert meta["filename"] == "hello.txt"
    assert "path" in meta   # internal dict has full path
