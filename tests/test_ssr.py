"""Tests for the SSR renderer."""
from __future__ import annotations

from pyra.ssr import render_to_html


def el(tag, props=None, children=None):
    return {"type": "element", "id": "n1", "tag": tag,
            "props": props or {}, "handlers": {}, "children": children or []}


def text(value):
    return {"type": "text", "id": "n2", "value": value}


def test_text_node():
    assert render_to_html(text("hello")) == "hello"


def test_simple_element():
    assert render_to_html(el("div")) == "<div></div>"


def test_element_with_text_child():
    result = render_to_html(el("p", children=[text("hello")]))
    assert result == "<p>hello</p>"


def test_element_with_props():
    result = render_to_html(el("span", props={"style": "color:red"}))
    assert 'style="color:red"' in result


def test_void_element_no_closing_tag():
    result = render_to_html(el("img", props={"src": "/img.png", "alt": "x"}))
    assert "</img>" not in result
    assert result.startswith("<img")


def test_nested_elements():
    inner = el("span", children=[text("world")])
    outer = el("div", children=[inner])
    result = render_to_html(outer)
    assert result == "<div><span>world</span></div>"


def test_attrs_are_escaped():
    result = render_to_html(el("div", props={"title": '<script>'}))
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


def test_unknown_node_returns_empty():
    assert render_to_html({"type": "unknown", "id": "n1"}) == ""
