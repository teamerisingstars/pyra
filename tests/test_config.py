"""Tests for the config module."""
from __future__ import annotations

from pyra.config import Config, _DEV_SECRET


def test_defaults():
    c = Config()
    assert c.host == "127.0.0.1"
    assert c.port == 7340
    assert c.db_url is None
    assert c.debug is False


def test_env_override(monkeypatch):
    monkeypatch.setenv("PYRA_HOST", "0.0.0.0")
    monkeypatch.setenv("PYRA_PORT", "8080")
    monkeypatch.setenv("PYRA_DEBUG", "true")
    monkeypatch.setenv("PYRA_SECRET_KEY", "my-prod-secret")
    c = Config()
    assert c.host == "0.0.0.0"
    assert c.port == 8080
    assert c.debug is True
    assert c.secret_key == "my-prod-secret"
    assert not c.is_dev_secret


def test_dev_secret_detected():
    c = Config()
    c.secret_key = _DEV_SECRET
    assert c.is_dev_secret


def test_allowed_hosts_parsed(monkeypatch):
    monkeypatch.setenv("PYRA_ALLOWED_HOSTS", "example.com, api.example.com")
    c = Config()
    assert c.allowed_hosts == ["example.com", "api.example.com"]


def test_db_url_from_env(monkeypatch):
    monkeypatch.setenv("PYRA_DB_URL", "postgresql://localhost/mydb")
    c = Config()
    assert c.db_url == "postgresql://localhost/mydb"
