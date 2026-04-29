"""Tests for OAuth provider state and URL generation."""
from __future__ import annotations

import hashlib
import hmac as _hmac
import time

import pytest

from pyra.oauth import GitHubOAuth, GoogleOAuth


SECRET = b"test-secret"


@pytest.fixture
def github():
    return GitHubOAuth(client_id="test-id", client_secret="test-secret")


@pytest.fixture
def google():
    return GoogleOAuth(client_id="gid", client_secret="gsecret")


def test_github_auth_url_contains_client_id(github):
    url = github.authorization_url("state123", "http://localhost/cb")
    assert "client_id=test-id" in url
    assert "github.com" in url


def test_github_auth_url_contains_state(github):
    url = github.authorization_url("mystate", "http://localhost/cb")
    assert "state=mystate" in url


def test_google_auth_url_contains_access_type(google):
    url = google.authorization_url("s", "http://localhost/cb")
    assert "access_type=online" in url
    assert "accounts.google.com" in url


def test_state_roundtrip(github):
    state = github._make_state(SECRET, "/dashboard")
    next_url = github._verify_state(SECRET, state)
    assert next_url == "/dashboard"


def test_state_tampered_rejected(github):
    state = github._make_state(SECRET, "/dashboard")
    tampered = state[:-5] + "xxxxx"
    assert github._verify_state(SECRET, tampered) is None


def test_state_wrong_secret_rejected(github):
    state = github._make_state(b"other-secret", "/dashboard")
    assert github._verify_state(SECRET, state) is None


def test_state_expired_rejected(github):
    state = github._make_state(SECRET, "/dashboard")
    # Manually patch ts to be 700 seconds ago
    parts = state.split(".", 3)
    old_ts = str(int(time.time()) - 700)
    raw = f"{parts[0]}:{old_ts}:{parts[3]}"
    sig = _hmac.new(SECRET, raw.encode(), hashlib.sha256).hexdigest()[:16]
    expired_state = f"{parts[0]}.{old_ts}.{sig}.{parts[3]}"
    assert github._verify_state(SECRET, expired_state) is None


def test_github_default_scopes(github):
    assert "read:user" in github.scopes


def test_google_default_scopes(google):
    assert "openid" in google.scopes
    assert "email" in google.scopes
