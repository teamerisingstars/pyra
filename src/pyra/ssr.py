"""Server-side rendering: component tree -> HTML string for initial GET response."""
from __future__ import annotations

import html as _html
from typing import Any

# HTML elements that must not have a closing tag
_VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})


def render_to_html(node: dict[str, Any]) -> str:
    """Convert a serialized render-tree node to an HTML string."""
    if node.get("type") == "text":
        return node.get("value", "")   # already html-escaped by render.py

    if node.get("type") == "element":
        tag = node["tag"]
        props = node.get("props") or {}
        attr_str = _build_attrs(props)
        children_html = "".join(render_to_html(c) for c in (node.get("children") or []))

        open_tag = f"<{tag}{attr_str}>"
        if tag in _VOID_TAGS:
            return open_tag  # no closing tag, no children
        return f"{open_tag}{children_html}</{tag}>"

    return ""


def _build_attrs(props: dict[str, Any]) -> str:
    if not props:
        return ""
    parts = []
    for k, v in props.items():
        safe_k = _html.escape(str(k), quote=True)
        safe_v = _html.escape(str(v), quote=True)
        parts.append(f' {safe_k}="{safe_v}"')
    return "".join(parts)
