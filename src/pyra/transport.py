"""Signed WebSocket transport.

Every server→client message is HMAC-signed with a session-derived key. The
client refuses messages without a valid signature. Message IDs are monotonic
within a session and used to reject replays.

For v0.0.1 the secret is per-process (regenerated on dev restart). Production
will derive per-session keys from a KMS-managed master.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Session:
    """Per-connection signing state."""

    session_id: str
    secret: bytes
    next_msg_id: int = 1
    last_inbound_msg_id: int = 0
    created_at: float = field(default_factory=time.time)


def new_session() -> Session:
    return Session(
        session_id=secrets.token_urlsafe(24),
        secret=secrets.token_bytes(32),
    )


def _canonical(payload: dict[str, Any]) -> bytes:
    """Stable JSON encoding for HMAC."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_outbound(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    """Wrap an outbound payload with a monotonic msg_id and HMAC signature."""
    msg_id = session.next_msg_id
    session.next_msg_id += 1
    body = {"msg_id": msg_id, "payload": payload}
    sig = hmac.new(session.secret, _canonical(body), hashlib.sha256).hexdigest()
    body["sig"] = sig
    return body


def verify_inbound(session: Session, message: dict[str, Any]) -> dict[str, Any]:
    """Verify an inbound message's signature and msg_id ordering.

    Raises ValueError on tamper, replay, or out-of-order.
    """
    if not isinstance(message, dict):
        raise ValueError("inbound message must be a dict")

    msg_id = message.get("msg_id")
    sig = message.get("sig")
    payload = message.get("payload")
    if not isinstance(msg_id, int) or not isinstance(sig, str) or payload is None:
        raise ValueError("malformed inbound message")

    if msg_id <= session.last_inbound_msg_id:
        raise ValueError(f"replay or out-of-order msg_id {msg_id}")

    expected = hmac.new(
        session.secret,
        _canonical({"msg_id": msg_id, "payload": payload}),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise ValueError("invalid signature")

    session.last_inbound_msg_id = msg_id
    return payload


def get_dev_secret() -> bytes:
    """Get a per-process dev secret. Override via PYRA_SECRET env in production."""
    env_secret = os.environ.get("PYRA_SECRET")
    if env_secret:
        return env_secret.encode("utf-8")
    return secrets.token_bytes(32)
