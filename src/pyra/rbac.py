"""Role-Based Access Control (RBAC) for Pyra.

Roles are strings. Permissions are strings. A role grants a set of permissions.

Usage::

    from pyra.rbac import RoleManager

    roles = RoleManager()
    roles.define("admin", permissions=["read", "write", "delete"])
    roles.define("editor", permissions=["read", "write"])
    roles.define("viewer", permissions=["read"])

    # Assign roles (in-memory by default; use PersistentState for persistence)
    roles.assign("user-123", "editor")

    # Check
    roles.has_role("user-123", "editor")       # True
    roles.has_permission("user-123", "write")   # True
    roles.has_permission("user-123", "delete")  # False
"""
from __future__ import annotations

import functools
from typing import Any, Callable


class RoleManager:
    """Manages role definitions and user-role assignments.

    By default, all data is in-memory and lost on restart.
    Pass a `store` dict-like object to persist across restarts
    (e.g., backed by PersistentState with your own sync wrapper).
    """

    def __init__(self) -> None:
        self._role_permissions: dict[str, set[str]] = {}
        self._user_roles: dict[str, set[str]] = {}

    # --- Role definition ---

    def define(self, role: str, permissions: list[str] | None = None) -> None:
        """Define a role with optional permissions."""
        self._role_permissions[role] = set(permissions or [])

    def add_permission(self, role: str, permission: str) -> None:
        """Add a permission to an existing role."""
        self._role_permissions.setdefault(role, set()).add(permission)

    def get_permissions(self, role: str) -> set[str]:
        """Return all permissions for a role."""
        return frozenset(self._role_permissions.get(role, set()))  # type: ignore[return-value]

    # --- User-role assignment ---

    def assign(self, user_id: str, role: str) -> None:
        """Assign a role to a user."""
        self._user_roles.setdefault(user_id, set()).add(role)

    def revoke(self, user_id: str, role: str) -> None:
        """Remove a role from a user."""
        self._user_roles.get(user_id, set()).discard(role)

    def get_roles(self, user_id: str) -> set[str]:
        """Return all roles assigned to a user."""
        return frozenset(self._user_roles.get(user_id, set()))  # type: ignore[return-value]

    # --- Checks ---

    def has_role(self, user_id: str, role: str) -> bool:
        """Return True if user has the given role."""
        return role in self._user_roles.get(user_id, set())

    def has_any_role(self, user_id: str, *roles: str) -> bool:
        """Return True if user has at least one of the given roles."""
        user_roles = self._user_roles.get(user_id, set())
        return bool(user_roles.intersection(roles))

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Return True if any of the user's roles grants the given permission."""
        for role in self._user_roles.get(user_id, set()):
            if permission in self._role_permissions.get(role, set()):
                return True
        return False

    # --- Decorators ---

    def require_role(
        self,
        *roles: str,
        redirect_to: str = "/403",
    ) -> Callable[[Any], Any]:
        """Decorator for @page functions. Redirects if the current user lacks all given roles.

        Usage::

            @page("/admin")
            @roles.require_role("admin")
            def admin_panel():
                ...

            @page("/editor")
            @roles.require_role("admin", "editor")   # either role works
            def editor_page():
                ...
        """
        def decorator(page_fn: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(page_fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                from pyra.auth import get_current_user, _AuthRedirectComponent
                user_id = get_current_user()
                if user_id is None or not self.has_any_role(user_id, *roles):
                    return _AuthRedirectComponent(redirect_to)
                return page_fn(*args, **kwargs)

            wrapper._requires_role = roles  # type: ignore[attr-defined]
            return wrapper

        return decorator

    def require_permission(
        self,
        permission: str,
        redirect_to: str = "/403",
    ) -> Callable[[Any], Any]:
        """Decorator for @page functions. Redirects if the current user lacks the permission."""
        def decorator(page_fn: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(page_fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                from pyra.auth import get_current_user, _AuthRedirectComponent
                user_id = get_current_user()
                if user_id is None or not self.has_permission(user_id, permission):
                    return _AuthRedirectComponent(redirect_to)
                return page_fn(*args, **kwargs)

            wrapper._requires_permission = permission  # type: ignore[attr-defined]
            return wrapper

        return decorator
