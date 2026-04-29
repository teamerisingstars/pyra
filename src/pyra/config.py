"""Runtime configuration loaded from environment variables.

Environment variables:
    PYRA_SECRET_KEY   — HMAC signing key for auth. Required in production.
                        Defaults to an insecure dev value with a loud warning.
    PYRA_DEBUG        — "true"/"1" enables debug mode (default: false in prod).
    PYRA_HOST         — Server bind host (default: "127.0.0.1").
    PYRA_PORT         — Server bind port (default: 7340).
    PYRA_DB_URL       — Database URL for persistent state (default: None).
    PYRA_ALLOWED_HOSTS — Comma-separated list of allowed Host header values (default: "*").
"""
from __future__ import annotations

import os
import warnings
from dataclasses import dataclass, field

_DEV_SECRET = "dev-insecure-key-set-PYRA_SECRET_KEY-in-production"


@dataclass
class Config:
    secret_key: str = field(default_factory=lambda: os.environ.get("PYRA_SECRET_KEY", _DEV_SECRET))
    debug: bool = field(default_factory=lambda: os.environ.get("PYRA_DEBUG", "").lower() in ("true", "1"))
    host: str = field(default_factory=lambda: os.environ.get("PYRA_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.environ.get("PYRA_PORT", "7340")))
    db_url: str | None = field(default_factory=lambda: os.environ.get("PYRA_DB_URL"))
    allowed_hosts: list[str] = field(
        default_factory=lambda: [
            h.strip() for h in os.environ.get("PYRA_ALLOWED_HOSTS", "*").split(",")
        ]
    )

    def check_production_secret(self) -> None:
        """Warn loudly if the default insecure secret is in use."""
        if self.secret_key == _DEV_SECRET:
            warnings.warn(
                "[pyra] PYRA_SECRET_KEY is not set. Using an insecure default — "
                "set it to a random 32-byte value before deploying to production.",
                stacklevel=3,
            )

    @property
    def is_dev_secret(self) -> bool:
        return self.secret_key == _DEV_SECRET


# Module-level singleton — reads env at import time.
# Tests can replace this or set env vars before importing.
config = Config()
