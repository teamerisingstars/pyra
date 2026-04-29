"""Database connectivity and PersistentState.

Zero-config SQLite for development; Postgres via PYRA_DB_URL in production.

Usage (simple KV persistence)::

    from pyra.db import PersistentState

    @page("/counter")
    async def counter():
        # Per-user persistent counter, survives restarts
        count = await PersistentState.get("global_count", default=0)
        ...

Usage (raw connection)::

    from pyra.db import get_connection

    async with get_connection() as conn:
        rows = await conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
"""
from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

_DB_URL: str | None = None
_ENGINE: Any = None  # aiosqlite connection or asyncpg pool


def _get_db_url() -> str:
    from pyra.config import config

    return config.db_url or f"sqlite:///{os.path.join(os.getcwd(), 'pyra_dev.db')}"


async def _ensure_kv_table(conn: Any, db_url: str) -> None:
    """Create the pyra_kv table if it doesn't exist."""
    if db_url.startswith("sqlite"):
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS pyra_kv "
            "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        await conn.commit()
    else:
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS pyra_kv "
            "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )


@asynccontextmanager
async def get_connection() -> AsyncIterator[Any]:
    """Async context manager for a database connection.

    For SQLite, returns an aiosqlite connection.
    For Postgres, returns an asyncpg connection from the pool.

    Requires aiosqlite or asyncpg to be installed.
    """
    db_url = _get_db_url()
    if db_url.startswith("sqlite"):
        try:
            import aiosqlite
        except ImportError as exc:
            raise ImportError(
                "aiosqlite is required for SQLite support. Install with: pip install aiosqlite"
            ) from exc
        db_path = db_url.replace("sqlite:///", "")
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await _ensure_kv_table(conn, db_url)
            yield conn
    else:
        try:
            import asyncpg
        except ImportError as exc:
            raise ImportError(
                "asyncpg is required for Postgres support. Install with: pip install asyncpg"
            ) from exc
        # Strip SQLAlchemy-style prefix if present
        pg_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(pg_url)
        try:
            await _ensure_kv_table(conn, db_url)
            yield conn
        finally:
            await conn.close()


class PersistentState:
    """A key-value store backed by the configured database.

    Values are JSON-serialized, so any JSON-compatible Python value is supported.

    All methods are async and must be awaited.
    """

    @staticmethod
    async def get(key: str, default: Any = None) -> Any:
        """Get a value by key, returning *default* if not found."""
        async with get_connection() as conn:
            db_url = _get_db_url()
            if db_url.startswith("sqlite"):
                cursor = await conn.execute(
                    "SELECT value FROM pyra_kv WHERE key = ?", (key,)
                )
                row = await cursor.fetchone()
            else:
                row = await conn.fetchrow(
                    "SELECT value FROM pyra_kv WHERE key = $1", key
                )
            if row is None:
                return default
            return json.loads(row["value"] if db_url.startswith("sqlite") else row[0])

    @staticmethod
    async def set(key: str, value: Any) -> None:
        """Persist *value* under *key*."""
        serialized = json.dumps(value)
        async with get_connection() as conn:
            db_url = _get_db_url()
            if db_url.startswith("sqlite"):
                await conn.execute(
                    "INSERT INTO pyra_kv (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, serialized),
                )
                await conn.commit()
            else:
                await conn.execute(
                    "INSERT INTO pyra_kv (key, value) VALUES ($1, $2) "
                    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                    key,
                    serialized,
                )

    @staticmethod
    async def delete(key: str) -> None:
        """Remove a key from the store."""
        async with get_connection() as conn:
            db_url = _get_db_url()
            if db_url.startswith("sqlite"):
                await conn.execute("DELETE FROM pyra_kv WHERE key = ?", (key,))
                await conn.commit()
            else:
                await conn.execute("DELETE FROM pyra_kv WHERE key = $1", key)

    @staticmethod
    async def all_keys() -> list[str]:
        """Return all stored keys."""
        async with get_connection() as conn:
            db_url = _get_db_url()
            if db_url.startswith("sqlite"):
                cursor = await conn.execute("SELECT key FROM pyra_kv")
                rows = await cursor.fetchall()
                return [r[0] for r in rows]
            else:
                rows = await conn.fetch("SELECT key FROM pyra_kv")
                return [r[0] for r in rows]
