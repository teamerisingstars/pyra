"""Tests for the forms validation helpers."""
from __future__ import annotations

import pytest
from pyra.forms import validate, use_form


def test_validate_success():
    try:
        from pydantic import BaseModel
    except ImportError:
        pytest.skip("pydantic not installed")

    class Schema(BaseModel):
        name: str
        age: int

    instance, errors = validate(Schema, {"name": "Alice", "age": 30})
    assert instance is not None
    assert instance.name == "Alice"
    assert errors == {}


def test_validate_failure():
    try:
        from pydantic import BaseModel
    except ImportError:
        pytest.skip("pydantic not installed")

    class Schema(BaseModel):
        email: str
        age: int

    instance, errors = validate(Schema, {"email": "x", "age": "not-a-number"})
    assert instance is None
    assert "age" in errors


def test_use_form_calls_handler_on_valid():
    try:
        from pydantic import BaseModel
    except ImportError:
        pytest.skip("pydantic not installed")

    class Schema(BaseModel):
        name: str

    called_with = []
    handler = use_form(Schema, lambda d: called_with.append(d.name))
    handler({"name": "Bob"})
    assert called_with == ["Bob"]


def test_use_form_returns_errors_on_invalid():
    try:
        from pydantic import BaseModel
    except ImportError:
        pytest.skip("pydantic not installed")

    class Schema(BaseModel):
        age: int

    handler = use_form(Schema, lambda d: None)
    result = handler({"age": "bad"})
    assert isinstance(result, dict)
    assert "age" in result
