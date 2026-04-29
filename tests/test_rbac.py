"""Tests for RBAC RoleManager."""
from __future__ import annotations

import pytest
from pyra.rbac import RoleManager


@pytest.fixture
def roles():
    rm = RoleManager()
    rm.define("admin", permissions=["read", "write", "delete"])
    rm.define("editor", permissions=["read", "write"])
    rm.define("viewer", permissions=["read"])
    return rm


def test_assign_and_has_role(roles):
    roles.assign("alice", "editor")
    assert roles.has_role("alice", "editor")
    assert not roles.has_role("alice", "admin")


def test_revoke_role(roles):
    roles.assign("bob", "admin")
    roles.revoke("bob", "admin")
    assert not roles.has_role("bob", "admin")


def test_get_roles(roles):
    roles.assign("carol", "editor")
    roles.assign("carol", "viewer")
    assert roles.get_roles("carol") == {"editor", "viewer"}


def test_has_any_role(roles):
    roles.assign("dave", "editor")
    assert roles.has_any_role("dave", "admin", "editor")
    assert not roles.has_any_role("dave", "admin")


def test_has_permission(roles):
    roles.assign("eve", "editor")
    assert roles.has_permission("eve", "read")
    assert roles.has_permission("eve", "write")
    assert not roles.has_permission("eve", "delete")


def test_no_roles_no_permissions(roles):
    assert not roles.has_permission("unknown", "read")
    assert not roles.has_role("unknown", "viewer")


def test_get_permissions(roles):
    perms = roles.get_permissions("admin")
    assert "read" in perms
    assert "delete" in perms


def test_add_permission(roles):
    roles.define("custom")
    roles.add_permission("custom", "export")
    assert "export" in roles.get_permissions("custom")


def test_require_role_passes_when_authenticated(roles):
    from pyra.auth import _SESSION_CTX
    roles.assign("u1", "admin")
    called = []

    @roles.require_role("admin")
    def my_page():
        called.append(True)
        from pyra.components import Text
        return Text("ok")

    token = _SESSION_CTX.set("u1")
    try:
        my_page()
        assert called == [True]
    finally:
        _SESSION_CTX.reset(token)


def test_require_role_redirects_when_wrong_role(roles):
    from pyra.auth import _SESSION_CTX, _AuthRedirectComponent
    roles.assign("u2", "viewer")

    @roles.require_role("admin")
    def admin_page():
        from pyra.components import Text
        return Text("secret")

    token = _SESSION_CTX.set("u2")
    try:
        result = admin_page()
        assert isinstance(result, _AuthRedirectComponent)
    finally:
        _SESSION_CTX.reset(token)


def test_auth_manager_roles_property():
    from pyra.auth import AuthManager
    auth = AuthManager(secret_key="test")
    auth.roles.define("superuser", permissions=["all"])
    auth.roles.assign("u", "superuser")
    assert auth.roles.has_permission("u", "all")
