"""Component primitives.

Pyra v0.0.1 ships a tiny set: Text, Button, VStack, HStack, Input.
Components are pure data — they describe what to render. The runtime
turns them into a serializable tree and patches the DOM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union

# A component child is either another component or a primitive value (str/int/float/bool).
ChildLike = Union["Component", str, int, float, bool]


@dataclass
class Component:
    """Base class for all UI nodes."""

    pass


@dataclass
class Element(Component):
    """A DOM-mappable element."""

    tag: str
    props: dict[str, Any] = field(default_factory=dict)
    children: list[ChildLike] = field(default_factory=list)
    handlers: dict[str, Callable[..., Any]] = field(default_factory=dict)


def Text(content: Any) -> Element:
    """A text node. Always a span so it owns its own ID for fine-grained patches."""
    return Element(tag="span", children=[str(content)])


def Button(
    label: Any,
    on_click: Optional[Callable[..., Any]] = None,
) -> Element:
    handlers = {"click": on_click} if on_click else {}
    return Element(
        tag="button",
        props={},
        children=[str(label)],
        handlers=handlers,
    )


def VStack(*children: ChildLike, gap: str = "8px", style: str = "") -> Element:
    base = f"display:flex;flex-direction:column;gap:{gap};"
    return Element(
        tag="div",
        props={"style": base + style},
        children=list(children),
    )


def HStack(*children: ChildLike, gap: str = "8px", style: str = "") -> Element:
    base = f"display:flex;flex-direction:row;gap:{gap};align-items:center;"
    return Element(
        tag="div",
        props={"style": base + style},
        children=list(children),
    )


def Input(
    value: Any = "",
    placeholder: str = "",
    on_input: Optional[Callable[[str], Any]] = None,
) -> Element:
    handlers = {"input": on_input} if on_input else {}
    return Element(
        tag="input",
        props={"value": str(value), "placeholder": placeholder},
        handlers=handlers,
    )
