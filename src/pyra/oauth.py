"""OAuth 2.0 social login providers (GitHub, Google)."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Any
from urllib.parse import urlencode


class OAuthProvider:
    """Base class for OAuth 2.0 providers."""

    name: str = "oauth"
    auth_url: str = ""
    token_url: str = ""
    profile_url: str = ""

    def __init__(self, client_id: str, client_secret: str, scopes: list[str] | None = None) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes or self._default_scopes()

    def _default_scopes(self) -> list[str]:
        return []

    def authorization_url(self, state: str, redirect_uri: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
            "response_type": "code",
        }
        return f"{self.auth_url}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> str:
        """Exchange authorization code for access token. Returns the token string."""
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            token = data.get("access_token")
            if not token:
                raise ValueError(f"No access_token in response: {data}")
            return str(token)

    async def get_user_id(self, token: str) -> str:
        """Fetch a stable, unique user identifier from the provider."""
        raise NotImplementedError

    def _make_state(self, secret: bytes, next_url: str) -> str:
        """Generate a signed state parameter to prevent CSRF."""
        nonce = secrets.token_hex(16)
        ts = str(int(time.time()))
        raw = f"{nonce}:{ts}:{next_url}"
        sig = hmac.new(secret, raw.encode(), hashlib.sha256).hexdigest()[:16]
        return f"{nonce}.{ts}.{sig}.{next_url}"

    def _verify_state(self, secret: bytes, state: str) -> str | None:
        """Verify state and return next_url, or None if invalid/expired."""
        try:
            parts = state.split(".", 3)
            if len(parts) != 4:
                return None
            nonce, ts, sig, next_url = parts
            raw = f"{nonce}:{ts}:{next_url}"
            expected = hmac.new(secret, raw.encode(), hashlib.sha256).hexdigest()[:16]
            if not hmac.compare_digest(sig, expected):
                return None
            if int(time.time()) - int(ts) > 600:  # 10-min window
                return None
            return next_url
        except (ValueError, OverflowError):
            return None


class GitHubOAuth(OAuthProvider):
    """GitHub OAuth provider."""

    name = "github"
    auth_url = "https://github.com/login/oauth/authorize"
    token_url = "https://github.com/login/oauth/access_token"
    profile_url = "https://api.github.com/user"

    def _default_scopes(self) -> list[str]:
        return ["read:user", "user:email"]

    async def get_user_id(self, token: str) -> str:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.profile_url,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            return f"github:{data['id']}"


class GoogleOAuth(OAuthProvider):
    """Google OAuth provider."""

    name = "google"
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    profile_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    def _default_scopes(self) -> list[str]:
        return ["openid", "email", "profile"]

    def authorization_url(self, state: str, redirect_uri: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
            "response_type": "code",
            "access_type": "online",
        }
        return f"{self.auth_url}?{urlencode(params)}"

    async def get_user_id(self, token: str) -> str:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.profile_url,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return f"google:{data['sub']}"


def register_oauth_routes(
    app: Any,  # pyra App instance
    provider: OAuthProvider,
    auth_manager: Any,  # pyra AuthManager instance
    base_url: str = "http://127.0.0.1:7340",
) -> None:
    """Register OAuth login and callback routes on a Pyra App.

    Usage::

        from pyra.oauth import GitHubOAuth, register_oauth_routes

        github = GitHubOAuth(client_id="...", client_secret="...")
        register_oauth_routes(app, github, auth, base_url="https://myapp.com")
        # Routes added:
        #   GET /auth/oauth/github/login?next=/dashboard
        #   GET /auth/oauth/github/callback
    """
    from starlette.requests import Request
    from starlette.responses import RedirectResponse
    from starlette.routing import Route

    redirect_uri = f"{base_url.rstrip('/')}/auth/oauth/{provider.name}/callback"

    async def login(request: Request) -> Any:  # returns Starlette Response
        next_url = request.query_params.get("next", "/")
        state = provider._make_state(auth_manager._secret, next_url)
        url = provider.authorization_url(state, redirect_uri)
        return RedirectResponse(url, status_code=302)

    async def callback(request: Request) -> Any:  # returns Starlette Response
        code = request.query_params.get("code", "")
        state = request.query_params.get("state", "")
        next_url = provider._verify_state(auth_manager._secret, state)
        if not next_url or not code:
            from starlette.responses import HTMLResponse

            return HTMLResponse("<h1>OAuth error: invalid state or missing code.</h1>", status_code=400)
        try:
            token = await provider.exchange_code(code, redirect_uri)
            user_id = await provider.get_user_id(token)
        except Exception as exc:
            from starlette.responses import HTMLResponse

            return HTMLResponse(f"<h1>OAuth error: {exc}</h1>", status_code=502)
        session_value = auth_manager.create_session_value(user_id)
        response = RedirectResponse(next_url, status_code=303)
        response.set_cookie(
            key=auth_manager.cookie_name,
            value=session_value,
            httponly=True,
            samesite="lax",
            max_age=auth_manager._session_ttl,
        )
        return response

    app._starlette.routes.insert(
        0, Route(f"/auth/oauth/{provider.name}/callback", callback, methods=["GET"])
    )
    app._starlette.routes.insert(
        0, Route(f"/auth/oauth/{provider.name}/login", login, methods=["GET"])
    )
