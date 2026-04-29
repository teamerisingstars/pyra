"""Tests for PersistentState backed by SQLite (in-memory via temp file)."""
from __future__ import annotations

import pytest
from pyra.db import PersistentState


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    """Point PYRA_DB_URL at a temp SQLite file for isolation."""
    import importlib
    import sys

    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("PYRA_DB_URL", f"sqlite:///{db_path}")
    # Reset cached config so the new env var is picked up
    import pyra.config  # noqa: F401 — ensure the module is in sys.modules
    importlib.reload(sys.modules["pyra.config"])
    import pyra.db  # noqa: F401 — ensure the module is in sys.modules
    importlib.reload(sys.modules["pyra.db"])
    yield


@pytest.mark.asyncio
async def test_get_default():
    result = await PersistentState.get("missing", default=42)
    assert result == 42


@pytest.mark.asyncio
async def test_set_and_get():
    await PersistentState.set("name", "Alice")
    result = await PersistentState.get("name")
    assert result == "Alice"


@pytest.mark.asyncio
async def test_overwrite():
    await PersistentState.set("x", 1)
    await PersistentState.set("x", 2)
    assert await PersistentState.get("x") == 2


@pytest.mark.asyncio
async def test_delete():
    await PersistentState.set("y", "hello")
    await PersistentState.delete("y")
    assert await PersistentState.get("y") is None


@pytest.mark.asyncio
async def test_all_keys():
    await PersistentState.set("a", 1)
    await PersistentState.set("b", 2)
    keys = await PersistentState.all_keys()
    assert "a" in keys
    assert "b" in keys


@pytest.mark.asyncio
async def test_json_types():
    await PersistentState.set("obj", {"x": [1, 2, True, None]})
    result = await PersistentState.get("obj")
    assert result == {"x": [1, 2, True, None]}
