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
    {"op": "replace_node",   "id": <id>, "node": <node>}          structural change (unkeyed)
    {"op": "insert_node",    "parent_id": <id>, "index": <int>, "node": <node>}   keyed insert
    {"op": "remove_node",    "id": <id>}                                           keyed remove

When child-count or child-structure differs at any unkeyed element, we bail to
replace_node on the affected subtree. When all children in both old and new carry
a ``key`` field, keyed reconciliation is used instead: nodes are matched by key,
missing keys emit remove_node, new keys emit insert_node, and matched keys are
recursively diffed in-place.
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


def _all_keyed(children: list[dict]) -> bool:
    """Return True if every child in *children* has a non-None ``key`` field."""
    return len(children) > 0 and all(c.get("key") is not None for c in children)


def _diff_keyed_children(
    parent_id: Any,  # stable ID of the parent element
    old_children: list[dict],
    new_children: list[dict],
    ops: list[dict],
) -> None:
    """Reconcile two child lists whose every member carries a unique ``key``.

    Algorithm:
    1. Build lookup maps from key → node for old and new lists.
    2. Emit remove_node for every key present in old but absent from new.
    3. Walk new_children in order:
       - If the key existed before, recursively diff old vs new node.
       - If the key is new, emit insert_node at the current index.

    remove_node ops are emitted first to avoid ID collisions with inserts.
    """
    old_map: dict[str, dict] = {c["key"]: c for c in old_children}
    new_map: dict[str, dict] = {c["key"]: c for c in new_children}

    # Phase 1 – removals first to avoid ID collisions.
    for key, old_child in old_map.items():
        if key not in new_map:
            ops.append({"op": "remove_node", "id": old_child["id"]})

    # Phase 2 – inserts and in-place diffs.
    for index, new_child in enumerate(new_children):
        key = new_child["key"]
        if key in old_map:
            _diff_node(old_map[key], new_child, ops)
        else:
            ops.append({"op": "insert_node", "parent_id": parent_id, "index": index, "node": new_child})


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

    # Diff children.
    # If every child in both lists carries a key, use keyed reconciliation.
    # Otherwise fall back to positional diffing; bail to replace_node on count mismatch.
    old_children: list = old.get("children") or []
    new_children: list = new.get("children") or []

    if _all_keyed(old_children) and _all_keyed(new_children):
        _diff_keyed_children(nid, old_children, new_children, ops)
    else:
        if len(old_children) != len(new_children):
            ops.append({"op": "replace_node", "id": nid, "node": new})
            return
        for old_c, new_c in zip(old_children, new_children):
            _diff_node(old_c, new_c, ops)
