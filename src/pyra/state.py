"""Per-session state — the React-style hook pattern, adapted for Pyra.

Two ways to call `State(initial)`:

    # Module scope: returns a long-lived Signal shared across all connections.
    count = State(0)

    # Inside a @page render: returns a session-scoped Signal. Same Signal
    # across renders for this session; new Signal per connection.
    @page("/")
    def home():
        count = State(0)
        ...

Detection is automatic via a ContextVar. If a render context is active
(set by app.py per WebSocket connection), the call resolves to a hook
cell. If not, it returns a fresh Signal.

Hook rules (same as React):
    * Calls must happen in the same order across renders.
    * No conditional or looped State() calls. (Lint coming in Phase 4.)
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Optional, TypeVar

from pyra.reactive import Signal

T = TypeVar("T")


class SessionState:
    """Per-connection container for hook-style state cells."""

    __slots__ = ("_cells", "_index")

    def __init__(self) -> None:
        self._cells: list[Signal] = []
        self._index: int = 0

    def begin_render(self) -> None:
        """Reset the call cursor. Call once per render pass."""
        self._index = 0

    def cell(self, initial: Any) -> Signal:
        i = self._index
        self._index += 1
        if i >= len(self._cells):
            self._cells.append(Signal(initial))
        return self._cells[i]


_session_state: ContextVar[Optional[SessionState]] = ContextVar(
    "_session_state", default=None
)


def State(initial: T) -> Signal:
    """Reactive state. Behaves as a hook in render context; otherwise a fresh Signal."""
    ctx = _session_state.get()
    if ctx is not None:
        return ctx.cell(initial)
    return Signal(initial)


def _push_session(ctx: SessionState):
    """Internal: app.py uses this around each render pass."""
    return _session_state.set(ctx)


def _pop_session(token: Any) -> None:
    _session_state.reset(token)
