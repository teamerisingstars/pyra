"""Diff-based reconciler.

Compares a new render tree against the previous one and produces minimal
patch ops. Every node carries a stable ID (depth-first counter), so the
client can locate the affected DOM node in O(1).

Patch op vocabulary (kept tiny on purpose):
    {"op": "init",           "tree": <node>}                      first render
    {"op": "replace_text",   "id": <id>, "value": <str>}          text node changed
    {"op": "set_attr",       "id": <id>, "key": <k>, "value": <v>}
    {"op": "remove_attr",    "id": <id>, "key": <k>}
    {"op": "set_handler",    "id": <id>, "event": <e>, "handler_id": <h>}
    {"op": "remove_handler", "id": <id>, "event": <e>}
    {"op": "replace_node",   "id": <id>, "node": <node>}          structural change

When child-count or child-structure differs at any element, we bail to
replace_node on the affected subtree. Phase 3 will add keyed children
diff for list reconciliation; for v0.0.2 this is correct but coarse.
"""
from __future__ import annotations

from typing import Any, Optional


def diff(old: Optional[dict[str, Any]], new: dict[str, Any]) -> list[dict[str, Any]]:
    """Return patch ops that transform `old` into `new`. `old=None` → init."""
    if old is None:
        return [{"op": "init", "tree": new}]
    ops: list[dict[str, Any]] = []
    _diff_node(old, new, ops)
    return ops


def _diff_node(old: dict, new: dict, ops: list[dict]) -> None:
    # Type or tag mismatch → replace whole subtree.
    if old.get("type") != new.get("type"):
        ops.append({"op": "replace_node", "id": old["id"], "node": new})
        return

    if old.get("type") == "text":
        if old.get("value") != new.get("value"):
            ops.append({"op": "replace_text", "id": old["id"], "value": new["value"]})
        return

    if old.get("tag") != new.get("tag"):
        ops.append({"op": "replace_node", "id": old["id"], "node": new})
        return

    nid = old["id"]

    # Diff props.
    old_props: dict = old.get("props") or {}
    new_props: dict = new.get("props") or {}
    for k in old_props:
        if k not in new_props:
            ops.append({"op": "remove_attr", "id": nid, "key": k})
    for k, v in new_props.items():
        if old_props.get(k) != v:
            ops.append({"op": "set_attr", "id": nid, "key": k, "value": v})

    # Diff handlers.
    old_handlers: dict = old.get("handlers") or {}
    new_handlers: dict = new.get("handlers") or {}
    for event in old_handlers:
        if event not in new_handlers:
            ops.append({"op": "remove_handler", "id": nid, "event": event})
    for event, hid in new_handlers.items():
        if old_handlers.get(event) != hid:
            ops.append(
                {"op": "set_handler", "id": nid, "event": event, "handler_id": hid}
            )

    # Diff children. If structure differs (length), bail to replace_node.
    old_children: list = old.get("children") or []
    new_children: list = new.get("children") or []
    if len(old_children) != len(new_children):
        ops.append({"op": "replace_node", "id": nid, "node": new})
        return
    for old_c, new_c in zip(old_children, new_children):
        _diff_node(old_c, new_c, ops)
