"""Tests for hook-style per-session State."""
from pyra.reactive import Signal
from pyra.state import SessionState, State, _pop_session, _push_session


def test_state_at_module_scope_returns_fresh_signal():
    a = State(0)
    b = State(0)
    assert isinstance(a, Signal) and isinstance(b, Signal)
    assert a is not b


def test_state_in_session_context_returns_same_cell_across_renders():
    ctx = SessionState()
    token = _push_session(ctx)
    try:
        # First render
        ctx.begin_render()
        a1 = State(0)
        b1 = State("hi")
        # Second render
        ctx.begin_render()
        a2 = State(0)
        b2 = State("hi")
    finally:
        _pop_session(token)
    assert a1 is a2
    assert b1 is b2
    assert a1 is not b1


def test_two_session_contexts_have_independent_state():
    ctx1 = SessionState()
    ctx2 = SessionState()

    t1 = _push_session(ctx1)
    ctx1.begin_render()
    a1 = State(0)
    _pop_session(t1)

    t2 = _push_session(ctx2)
    ctx2.begin_render()
    a2 = State(0)
    _pop_session(t2)

    assert a1 is not a2
    a1.set(5)
    assert a1.value == 5
    assert a2.value == 0  # untouched


def test_state_initial_value_used_only_on_first_render():
    ctx = SessionState()
    token = _push_session(ctx)
    try:
        ctx.begin_render()
        a = State(10)
        a.set(99)
        # Re-render: same cell, value preserved (initial=10 ignored).
        ctx.begin_render()
        a2 = State(10)
        assert a is a2
        assert a2.value == 99
    finally:
        _pop_session(token)


def test_state_call_order_must_match():
    """If hook order is stable, cells round-trip; if not, you get the wrong cell.
    This documents the React-style constraint."""
    ctx = SessionState()
    token = _push_session(ctx)
    try:
        ctx.begin_render()
        a = State(0)
        b = State("x")

        ctx.begin_render()
        # Same order — same cells.
        a2 = State(0)
        b2 = State("x")
        assert a is a2 and b is b2
    finally:
        _pop_session(token)
