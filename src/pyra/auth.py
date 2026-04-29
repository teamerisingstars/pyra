"""Authentication: magic-link tokens, signed sessions, require_auth decorator."""
from __future__ import annotations

import functools
import hashlib
import hmac
import json
import secrets
import time
from contextvars import ContextVar
from typing import Any, Callable

_SESSION_CTX: ContextVar[str | None] = ContextVar("pyra_user_id", default=None)
_AUTH_REDIRECT_SENTINEL = "__pyra_auth_redirect__"

_UNSET = object()


class AuthManager:
    """Manages magic-link tokens and signed session cookies.

    Args:
        secret_key: A secret string used to sign tokens and cookies. Must be kept private.
        token_ttl: Magic-link token lifetime in seconds (default: 900 = 15 min).
        session_ttl: Session cookie lifetime in seconds (default: 86400 = 24 h).
        login_path: Path to redirect to when auth fails (default: "/login").
        cookie_name: Name of the session cookie (default: "pyra_session").
    """

    def __init__(
        self,
        secret_key: str | object = _UNSET,
        token_ttl: int = 900,
        session_ttl: int = 86400,
        login_path: str = "/login",
        cookie_name: str = "pyra_session",
    ) -> None:
        from pyra.config import config as _cfg

        if secret_key is _UNSET:
            _cfg.check_production_secret()
            resolved_key = _cfg.secret_key
        else:
            resolved_key = str(secret_key)
        self._secret = resolved_key.encode()
        self._token_ttl = token_ttl
        self._session_ttl = session_ttl
        self.login_path = login_path
        self.cookie_name = cookie_name
        self._pending: dict[str, tuple[str, float]] = {}  # token -> (user_id, expires_at)

    # --- Magic-link tokens ---

    def create_magic_link_token(self, user_id: str) -> str:
        """Create a one-time magic-link token for *user_id*. Call your email sender with the result."""
        token = secrets.token_urlsafe(32)
        self._pending[token] = (user_id, time.monotonic() + self._token_ttl)
        return token

    def verify_magic_link_token(self, token: str) -> str | None:
        """Consume and verify a magic-link token. Returns user_id or None."""
        entry = self._pending.pop(token, None)
        if entry is None:
            return None
        user_id, expires_at = entry
        if time.monotonic() > expires_at:
            return None
        return user_id

    # --- Session cookies ---

    def create_session_value(self, user_id: str) -> str:
        """Create a signed session cookie value."""
        expires_at = int(time.time()) + self._session_ttl
        payload = json.dumps({"u": user_id, "e": expires_at})
        sig = self._sign(payload)
        # Format: base64url(payload) + "." + hex(sig)  — but simpler: payload|sig
        # Use a separator that won't appear in JSON
        return payload + "|" + sig

    def verify_session_value(self, value: str) -> str | None:
        """Verify a session cookie value. Returns user_id or None."""
        try:
            payload, sig = value.rsplit("|", 1)
        except ValueError:
            return None
        expected = self._sign(payload)
        if not hmac.compare_digest(sig, expected):
            return None
        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, ValueError):
            return None
        if int(time.time()) > data.get("e", 0):
            return None
        return data.get("u")

    def _sign(self, data: str) -> str:
        return hmac.new(self._secret, data.encode(), hashlib.sha256).hexdigest()

    # --- Route protection ---

    def require_auth(
        self,
        fn: Callable[..., Any] | None = None,
        *,
        redirect_to: str | None = None,
    ) -> Any:
        """Decorator for @page functions. Redirects to login if not authenticated.

        Usage::

            @page("/dashboard")
            @auth.require_auth
            def dashboard():
                user = get_current_user()
                return Text(f"Hello {user}")

            # Or with custom redirect:
            @page("/admin")
            @auth.require_auth(redirect_to="/403")
            def admin():
                ...
        """
        redirect = redirect_to or self.login_path

        def decorator(page_fn: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(page_fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if _SESSION_CTX.get() is None:
                    return _AuthRedirectComponent(redirect)
                return page_fn(*args, **kwargs)

            wrapper._requires_auth = True  # type: ignore[attr-defined]
            wrapper._auth_manager = self   # type: ignore[attr-defined]
            wrapper._redirect_to = redirect  # type: ignore[attr-defined]
            return wrapper

        if fn is not None:
            return decorator(fn)
        return decorator


def get_current_user() -> str | None:
    """Return the authenticated user ID for the current session, or None."""
    return _SESSION_CTX.get()


def _set_current_user(user_id: str | None) -> Any:
    """Set the current user in the ContextVar. Returns the token for cleanup."""
    return _SESSION_CTX.set(user_id)


class _AuthRedirectComponent:
    """Sentinel component returned by require_auth when unauthenticated."""

    def __init__(self, url: str) -> None:
        self.url = url
