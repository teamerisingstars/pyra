"""Tests for the diff-based reconciler."""
from pyra.reconciler import diff


def el(nid, tag, props=None, handlers=None, children=None):
    return {
        "type": "element",
        "id": nid,
        "tag": tag,
        "props": props or {},
        "handlers": handlers or {},
        "children": children or [],
    }


def text(nid, value):
    return {"type": "text", "id": nid, "value": value}


# ---------------------------------------------------------------------------
# Helpers for keyed children
# ---------------------------------------------------------------------------

def keyed_text(nid, key, value):
    return {"type": "text", "id": nid, "key": key, "value": value}


def keyed_el(nid, key, tag, children=None):
    return {
        "type": "element",
        "id": nid,
        "key": key,
        "tag": tag,
        "props": {},
        "handlers": {},
        "children": children or [],
    }


# ---------------------------------------------------------------------------
# Existing tests (unkeyed / structural)
# ---------------------------------------------------------------------------

def test_init_patch_when_old_is_none():
    new = el("n1", "div")
    ops = diff(None, new)
    assert ops == [{"op": "init", "tree": new}]


def test_no_ops_when_identical():
    tree = el("n1", "div", children=[text("n2", "hi")])
    assert diff(tree, tree) == []


def test_text_change():
    old = el("n1", "div", children=[text("n2", "Count: 0")])
    new = el("n1", "div", children=[text("n2", "Count: 1")])
    ops = diff(old, new)
    assert ops == [{"op": "replace_text", "id": "n2", "value": "Count: 1"}]


def test_attr_set_and_remove():
    old = el("n1", "input", props={"value": "a", "placeholder": "x"})
    new = el("n1", "input", props={"value": "b"})
    ops = diff(old, new)
    assert {"op": "remove_attr", "id": "n1", "key": "placeholder"} in ops
    assert {"op": "set_attr", "id": "n1", "key": "value", "value": "b"} in ops
    assert len(ops) == 2


def test_handler_set_and_remove():
    old = el("n1", "button", handlers={"click": "n1:click"})
    new = el("n1", "button", handlers={})
    ops = diff(old, new)
    assert ops == [{"op": "remove_handler", "id": "n1", "event": "click"}]


def test_handler_added():
    old = el("n1", "button")
    new = el("n1", "button", handlers={"click": "n1:click"})
    ops = diff(old, new)
    assert ops == [
        {"op": "set_handler", "id": "n1", "event": "click", "handler_id": "n1:click"}
    ]


def test_tag_change_replaces_node():
    old = el("n1", "div")
    new = el("n1", "span")
    ops = diff(old, new)
    assert ops == [{"op": "replace_node", "id": "n1", "node": new}]


def test_child_count_change_bails_to_replace_node():
    old = el("n1", "div", children=[text("n2", "a")])
    new = el("n1", "div", children=[text("n2", "a"), text("n3", "b")])
    ops = diff(old, new)
    assert ops == [{"op": "replace_node", "id": "n1", "node": new}]


def test_deep_text_change_minimal():
    old = el("n1", "div", children=[
        el("n2", "span", children=[text("n3", "hello")]),
        el("n4", "span", children=[text("n5", "world")]),
    ])
    new = el("n1", "div", children=[
        el("n2", "span", children=[text("n3", "hi")]),
        el("n4", "span", children=[text("n5", "world")]),
    ])
    ops = diff(old, new)
    # Only one minimal op — the deep text change.
    assert ops == [{"op": "replace_text", "id": "n3", "value": "hi"}]


def test_multiple_independent_changes():
    old = el("n1", "div", props={"class": "old"}, children=[
        text("n2", "A"),
        el("n3", "button", props={"disabled": "true"}, handlers={"click": "n3:click"}),
    ])
    new = el("n1", "div", props={"class": "new"}, children=[
        text("n2", "B"),
        el("n3", "button", handlers={"click": "n3:click"}),
    ])
    ops = diff(old, new)
    op_types = {(o["op"], o.get("id"), o.get("key") or o.get("event")) for o in ops}
    assert ("set_attr", "n1", "class") in op_types
    assert ("replace_text", "n2", None) in op_types
    assert ("remove_attr", "n3", "disabled") in op_types


# ---------------------------------------------------------------------------
# Keyed reconciliation tests
# ---------------------------------------------------------------------------

def test_keyed_no_change():
    """Identical keyed lists should produce zero ops."""
    tree = el("n1", "ul", children=[
        keyed_text("n2", "a", "Alpha"),
        keyed_text("n3", "b", "Beta"),
    ])
    assert diff(tree, tree) == []


def test_keyed_text_change():
    """A single value change in a keyed list emits only replace_text for that node."""
    old = el("n1", "ul", children=[
        keyed_text("n2", "a", "Alpha"),
        keyed_text("n3", "b", "Beta"),
    ])
    new = el("n1", "ul", children=[
        keyed_text("n2", "a", "Alpha"),
        keyed_text("n3", "b", "Beta CHANGED"),
    ])
    ops = diff(old, new)
    assert ops == [{"op": "replace_text", "id": "n3", "value": "Beta CHANGED"}]


def test_keyed_item_removed():
    """Removing keyed item B from [A, B, C] emits exactly one remove_node for B."""
    node_a = keyed_el("n2", "a", "li")
    node_b = keyed_el("n3", "b", "li")
    node_c = keyed_el("n4", "c", "li")

    old = el("n1", "ul", children=[node_a, node_b, node_c])
    new = el("n1", "ul", children=[node_a, node_c])

    ops = diff(old, new)
    assert {"op": "remove_node", "id": "n3"} in ops
    # No replace_node on parent.
    assert not any(o["op"] == "replace_node" for o in ops)


def test_keyed_item_added():
    """Adding keyed item X between A and B emits insert_node at index 1."""
    node_a = keyed_el("n2", "a", "li")
    node_b = keyed_el("n3", "b", "li")
    node_x = keyed_el("n4", "x", "li")

    old = el("n1", "ul", children=[node_a, node_b])
    new = el("n1", "ul", children=[node_a, node_x, node_b])

    ops = diff(old, new)
    assert {
        "op": "insert_node",
        "parent_id": "n1",
        "index": 1,
        "node": node_x,
    } in ops
    # No replace_node on parent.
    assert not any(o["op"] == "replace_node" for o in ops)


def test_keyed_reorder():
    """Reordering [A, B] → [B, A] diffs each matched pair; no replace_node on parent."""
    node_a = keyed_el("n2", "a", "li")
    node_b = keyed_el("n3", "b", "li")

    old = el("n1", "ul", children=[node_a, node_b])
    new = el("n1", "ul", children=[node_b, node_a])

    ops = diff(old, new)
    # The parent must NOT be replaced wholesale.
    assert not any(o["op"] == "replace_node" for o in ops)
    # No stray remove_node or insert_node — both keys exist on both sides.
    assert not any(o["op"] in {"remove_node", "insert_node"} for o in ops)


def test_unkeyed_still_uses_positional():
    """Unkeyed children with different counts still bail to replace_node."""
    old = el("n1", "div", children=[text("n2", "a")])
    new = el("n1", "div", children=[text("n2", "a"), text("n3", "b")])
    ops = diff(old, new)
    assert ops == [{"op": "replace_node", "id": "n1", "node": new}]


def test_partially_keyed_falls_back():
    """If only SOME children have keys, fall back to positional logic.

    With equal counts and matching structure there should be no ops; with
    different counts we should get a replace_node (not a keyed diff).
    """
    # Mixed: first child has a key, second does not.
    child_with_key = {"type": "text", "id": "n2", "key": "k1", "value": "A"}
    child_no_key = {"type": "text", "id": "n3", "value": "B"}

    old = el("n1", "div", children=[child_with_key, child_no_key])
    # Add a third unkeyed child — count mismatch should trigger replace_node.
    extra = {"type": "text", "id": "n4", "value": "C"}
    new = el("n1", "div", children=[child_with_key, child_no_key, extra])

    ops = diff(old, new)
    assert ops == [{"op": "replace_node", "id": "n1", "node": new}]
