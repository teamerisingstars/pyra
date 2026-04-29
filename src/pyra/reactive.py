"""Reactive primitives: Signal, Computed, Effect.

Signals-based fine-grained reactivity (Solid/Svelte-inspired). Reading a signal
inside an observer (Effect or Computed) registers a dependency. Writing to a
signal notifies observers, which re-run.

Design notes:
- Synchronous propagation by default; async batching available via `batch()`.
- ContextVar-based observer stack means it works correctly across async tasks.
- Glitch-free: Computed is lazy, only recomputes when read after dirty.
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")

# The currently-executing observer (None at top level).
_current_observer: ContextVar[Optional["Observer"]] = ContextVar(
    "_current_observer", default=None
)

# Batching state.
_batch_queue: list["Effect"] = []
_batch_depth: int = 0


class Observer:
    """Anything that subscribes to signals and re-runs when they change."""

    __slots__ = ("_dependencies",)

    def __init__(self) -> None:
        self._dependencies: set = set()

    def _track(self, source: object) -> None:
        """Record a read dependency on `source`."""
        if source not in self._dependencies:
            self._dependencies.add(source)
            source._observers.add(self)  # type: ignore[attr-defined]

    def _untrack_all(self) -> None:
        for dep in self._dependencies:
            dep._observers.discard(self)  # type: ignore[attr-defined]
        self._dependencies.clear()

    def notify(self) -> None:
        raise NotImplementedError


class Signal(Generic[T]):
    """A reactive value.

    Reading `.value` inside an observer creates a dependency. Calling `.set()`
    or `.update()` notifies observers, which re-run.
    """

    __slots__ = ("_value", "_observers")

    def __init__(self, initial: T) -> None:
        self._value: T = initial
        self._observers: set[Observer] = set()

    @property
    def value(self) -> T:
        observer = _current_observer.get()
        if observer is not None:
            observer._track(self)
        return self._value

    def set(self, new_value: T) -> None:
        if new_value == self._value:
            return
        self._value = new_value
        self._notify_observers()

    def update(self, fn: Callable[[T], T]) -> None:
        self.set(fn(self._value))

    def _notify_observers(self) -> None:
        for observer in list(self._observers):
            observer.notify()

    def __repr__(self) -> str:
        return f"Signal({self._value!r})"


class Computed(Observer, Generic[T]):
    """A lazy derived value. Recomputes when its dependencies change AND when read."""

    __slots__ = ("_fn", "_value", "_dirty", "_observers")

    def __init__(self, fn: Callable[[], T]) -> None:
        super().__init__()
        self._fn = fn
        self._value: Optional[T] = None
        self._dirty: bool = True
        self._observers: set[Observer] = set()

    @property
    def value(self) -> T:
        outer = _current_observer.get()
        if outer is not None and outer is not self:
            outer._track(self)
        if self._dirty:
            self._recompute()
        return self._value  # type: ignore[return-value]

    def _recompute(self) -> None:
        self._untrack_all()
        token = _current_observer.set(self)
        try:
            self._value = self._fn()
            self._dirty = False
        finally:
            _current_observer.reset(token)

    def notify(self) -> None:
        if self._dirty:
            return
        self._dirty = True
        for observer in list(self._observers):
            observer.notify()


class Effect(Observer):
    """A side effect that re-runs when its signal/computed dependencies change."""

    __slots__ = ("_fn", "_disposed")

    def __init__(self, fn: Callable[[], None]) -> None:
        super().__init__()
        self._fn = fn
        self._disposed: bool = False
        self._run()

    def _run(self) -> None:
        if self._disposed:
            return
        self._untrack_all()
        token = _current_observer.set(self)
        try:
            self._fn()
        finally:
            _current_observer.reset(token)

    def notify(self) -> None:
        if _batch_depth > 0:
            if self not in _batch_queue:
                _batch_queue.append(self)
        else:
            self._run()

    def dispose(self) -> None:
        self._disposed = True
        self._untrack_all()


def batch(fn: Callable[[], None]) -> None:
    """Run `fn`, deferring effect re-runs until it completes.

    Useful when updating multiple signals and you want effects to see the
    consistent final state, not intermediate values.
    """
    global _batch_depth
    _batch_depth += 1
    try:
        fn()
    finally:
        _batch_depth -= 1
        if _batch_depth == 0:
            queue = list(_batch_queue)
            _batch_queue.clear()
            for effect in queue:
                effect._run()
