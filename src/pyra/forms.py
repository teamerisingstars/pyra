"""Pydantic-backed form validation helpers."""
from __future__ import annotations

from typing import Any, Callable, TypeVar

T = TypeVar("T")


def validate(schema_class: type[T], data: dict[str, Any]) -> tuple[T | None, dict[str, str]]:
    """Validate *data* against a Pydantic model.

    Returns (instance, {}) on success or (None, {field: first_error}) on failure.
    Requires pydantic v2. Falls back gracefully if pydantic is not installed.
    """
    try:
        from pydantic import ValidationError
    except ImportError:
        return schema_class(**data), {}  # type: ignore[return-value]

    try:
        instance = schema_class(**data)
        return instance, {}
    except ValidationError as exc:
        errors: dict[str, str] = {}
        for err in exc.errors():
            loc = err.get("loc", ())
            field = str(loc[0]) if loc else "__root__"
            if field not in errors:
                errors[field] = err.get("msg", "invalid")
        return None, errors


def use_form(
    schema_class: type[T],
    on_valid: Callable[[T], Any],
) -> Callable[[dict[str, Any]], Any]:
    """Return an on_submit handler that validates then calls *on_valid* on success.

    Usage::

        submit = use_form(LoginSchema, lambda data: login(data.email, data.password))
        Button("Log in", on_click=lambda: submit({"email": email.value, "password": pw.value}))
    """
    def handler(data: dict[str, Any]) -> Any:
        instance, errors = validate(schema_class, data)
        if errors:
            return errors
        return on_valid(instance)  # type: ignore[arg-type]
    return handler
