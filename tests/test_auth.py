"""Tests for the auth module."""
from __future__ import annotations

import time
import pytest
from pyra.auth import AuthManager, get_current_user, _set_current_user


@pytest.fixture
def auth():
    return AuthManager(secret_key="test-secret-key", token_ttl=60, session_ttl=3600)


def test_magic_link_create_and_verify(auth):
    token = auth.create_magic_link_token("user@example.com")
    assert auth.verify_magic_link_token(token) == "user@example.com"


def test_magic_link_consumed_once(auth):
    token = auth.create_magic_link_token("user@example.com")
    auth.verify_magic_link_token(token)
    assert auth.verify_magic_link_token(token) is None


def test_magic_link_invalid_token(auth):
    assert auth.verify_magic_link_token("not-a-real-token") is None


def test_magic_link_expired(auth):
    short_auth = AuthManager(secret_key="k", token_ttl=0)
    token = short_auth.create_magic_link_token("u")
    time.sleep(0.01)
    assert short_auth.verify_magic_link_token(token) is None


def test_session_create_and_verify(auth):
    value = auth.create_session_value("alice")
    assert auth.verify_session_value(value) == "alice"


def test_session_tampered_rejected(auth):
    value = auth.create_session_value("alice")
    tampered = value[:-4] + "xxxx"
    assert auth.verify_session_value(tampered) is None


def test_session_expired(auth):
    expired_auth = AuthManager(secret_key="k", session_ttl=-1)
    value = expired_auth.create_session_value("bob")
    assert expired_auth.verify_session_value(value) is None


def test_get_current_user_default_none():
    assert get_current_user() is None


def test_set_and_get_current_user():
    token = _set_current_user("user123")
    assert get_current_user() == "user123"
    _SESSION_CTX = __import__("pyra.auth", fromlist=["_SESSION_CTX"])._SESSION_CTX
    _SESSION_CTX.reset(token)
    assert get_current_user() is None


def test_require_auth_passes_when_authenticated(auth):
    called = []

    @auth.require_auth
    def my_page():
        called.append(True)
        from pyra.components import Text
        return Text("ok")

    token = _set_current_user("user1")
    try:
        my_page()
        assert called == [True]
    finally:
        from pyra.auth import _SESSION_CTX
        _SESSION_CTX.reset(token)


def test_require_auth_returns_redirect_when_not_authenticated(auth):
    from pyra.auth import _AuthRedirectComponent

    @auth.require_auth
    def my_page():
        from pyra.components import Text
        return Text("secret")

    result = my_page()
    assert isinstance(result, _AuthRedirectComponent)
    assert result.url == auth.login_path
