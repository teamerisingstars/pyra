"""Render: component tree -> serializable JSON, with handler IDs for events.

Every node carries a stable ID so the diff reconciler can locate the affected
DOM node. Output sanitization (html.escape) runs on every text patch.
"""
from __future__ import annotations

import html
from itertools import count
from typing import Any, Callable

from pyra.components import Component, Element

_id_counter = count(1)


def _next_id() -> str:
    return f"n{next(_id_counter)}"


def render_tree(
    root: Component,
    handler_registry: dict[str, Callable[..., Any]],
) -> dict[str, Any]:
    handler_registry.clear()
    return _render_node(root, handler_registry)


def _render_node(
    node: Any,
    registry: dict[str, Callable[..., Any]],
) -> Any:
    nid = _next_id()

    if isinstance(node, (str, int, float, bool)):
        return {"type": "text", "id": nid, "value": html.escape(str(node))}

    if isinstance(node, Element):
        children = [_render_node(c, registry) for c in node.children]
        handlers: dict[str, str] = {}
        for event_name, fn in node.handlers.items():
            if fn is None:
                continue
            hid = f"{nid}:{event_name}"
            registry[hid] = fn
            handlers[event_name] = hid

        result: dict[str, Any] = {
            "type": "element",
            "id": nid,
            "tag": node.tag,
            "props": _safe_props(node.props),
            "handlers": handlers,
            "children": children,
        }
        if node.key is not None:
            result["key"] = node.key
        return result

    if isinstance(node, Component):
        raise TypeError(f"Component subclass {type(node).__name__} not renderable yet")

    raise TypeError(f"Unrenderable node: {node!r}")


_SAFE_PROP_KEYS = {
    "style", "value", "placeholder", "type", "name", "checked", "selected", "disabled",
    "href", "src", "alt", "title", "class", "id", "rel",
    "accept", "multiple", "aria-label", "data-upload-target",
}


def _safe_props(props: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in props.items():
        if k in _SAFE_PROP_KEYS:
            out[k] = v
    return out


def reset_id_counter() -> None:
    global _id_counter
    _id_counter = count(1)
