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
