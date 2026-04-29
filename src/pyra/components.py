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


def Heading(content: Any, level: int = 1) -> Element:
    clamped = max(1, min(6, level))
    return Element(tag=f"h{clamped}", children=[str(content)])


def Link(label: Any, href: str = "", external: bool = False) -> Element:
    props: dict[str, Any] = {"href": href}
    if external:
        props["rel"] = "noopener noreferrer"
    return Element(tag="a", props=props, children=[str(label)])


def Spinner(size: str = "24px", color: str = "#888") -> Element:
    # The pyra-spin @keyframes animation must live in global CSS (e.g. app.py's _INDEX_HTML).
    # This component sets the class and border-based visual; the browser applies the keyframe.
    style = (
        f"width:{size};height:{size};"
        f"border:3px solid #eee;border-top:3px solid {color};"
        f"border-radius:50%;animation:pyra-spin 0.8s linear infinite;"
    )
    return Element(tag="div", props={"class": "pyra-spinner", "style": style})
