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
    key: Optional[str] = None


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


def Badge(content: Any, color: str = "#6366f1") -> Element:
    """An inline pill badge with a coloured background."""
    style = (
        f"display:inline-block;padding:2px 8px;border-radius:9999px;"
        f"background:{color};color:#fff;font-size:0.75rem;font-weight:600;"
    )
    return Element(tag="span", props={"style": style}, children=[str(content)])


def Card(*children: ChildLike, title: str = "", style: str = "") -> Element:
    """A bordered, padded container. An optional *title* is rendered as an h3 above children."""
    base = "border:1px solid #e5e7eb;border-radius:8px;padding:1rem;background:#fff;"
    inner: list[ChildLike] = []
    if title:
        inner.append(
            Element(
                tag="h3",
                props={"style": "margin:0 0 0.75rem;font-size:1rem;font-weight:600;"},
                children=[title],
            )
        )
    inner.extend(children)
    return Element(tag="div", props={"style": base + style}, children=inner)


def Image(
    src: str,
    alt: str = "",
    width: Optional[str] = None,
    height: Optional[str] = None,
) -> Element:
    """An <img> element with optional width/height applied as inline style."""
    props: dict[str, Any] = {"src": src, "alt": alt}
    style_parts = []
    if width:
        style_parts.append(f"width:{width}")
    if height:
        style_parts.append(f"height:{height}")
    if style_parts:
        props["style"] = ";".join(style_parts) + ";"
    return Element(tag="img", props=props)


def Heading(content: Any, level: int = 1) -> Element:
    """A heading element from h1 (default) to h6."""
    level = max(1, min(6, level))
    return Element(tag=f"h{level}", children=[str(content)])


def Link(label: Any, href: str = "", external: bool = False) -> Element:
    """An anchor element. Pass *external=True* to add rel="noopener noreferrer"."""
    props: dict[str, Any] = {"href": href}
    if external:
        props["rel"] = "noopener noreferrer"
    return Element(tag="a", props=props, children=[str(label)])


def Spinner(size: str = "24px", color: str = "#888") -> Element:
    """A CSS-animated spinner div."""
    style = (
        f"width:{size};height:{size};border:3px solid #eee;"
        f"border-top:3px solid {color};border-radius:50%;"
        f"animation:pyra-spin 0.8s linear infinite;"
    )
    return Element(tag="div", props={"class": "pyra-spinner", "style": style})


def FormField(
    name: str,
    label: str = "",
    value: Any = "",
    on_input: Optional[Callable[[str], Any]] = None,
    placeholder: str = "",
    error: str = "",
    input_type: str = "text",
) -> Element:
    """A labeled input row with an optional error message below."""
    label_el = Element(
        tag="label",
        props={"style": "font-size:0.875rem;font-weight:500;color:#374151;"},
        children=[label] if label else [],
    )
    input_el = Element(
        tag="input",
        props={
            "type": input_type,
            "name": name,
            "value": str(value),
            "placeholder": placeholder,
            "style": (
                "padding:0.4rem 0.6rem;border-radius:6px;"
                "border:1px solid #d1d5db;font-size:1rem;width:100%;"
                + ("border-color:#ef4444;" if error else "")
            ),
        },
        handlers={"input": on_input} if on_input else {},
    )
    children: list[ChildLike] = [label_el, input_el]
    if error:
        children.append(
            Element(
                tag="span",
                props={"style": "font-size:0.75rem;color:#ef4444;"},
                children=[error],
            )
        )
    return Element(
        tag="div",
        props={"style": "display:flex;flex-direction:column;gap:4px;"},
        children=children,
    )


def Select(
    name: str,
    options: list[tuple[str, str]],
    value: str = "",
    label: str = "",
    on_change: Optional[Callable[[str], Any]] = None,
) -> Element:
    """A labeled select/dropdown element."""
    label_el = Element(
        tag="label",
        props={"style": "font-size:0.875rem;font-weight:500;color:#374151;"},
        children=[label] if label else [],
    )
    option_els = [
        Element(
            tag="option",
            props={"value": v, **({"selected": "true"} if v == value else {})},
            children=[lbl],
        )
        for v, lbl in options
    ]
    select_el = Element(
        tag="select",
        props={
            "name": name,
            "style": "padding:0.4rem 0.6rem;border-radius:6px;border:1px solid #d1d5db;font-size:1rem;",
        },
        handlers={"change": on_change} if on_change else {},
        children=option_els,
    )
    children: list[ChildLike] = [label_el, select_el] if label else [select_el]
    return Element(
        tag="div",
        props={"style": "display:flex;flex-direction:column;gap:4px;"},
        children=children,
    )


def Checkbox(
    name: str,
    label: str = "",
    checked: bool = False,
    on_change: Optional[Callable[[str], Any]] = None,
) -> Element:
    """A checkbox with an optional label."""
    props: dict[str, Any] = {"type": "checkbox", "name": name}
    if checked:
        props["checked"] = "true"
    input_el = Element(
        tag="input",
        props=props,
        handlers={"change": on_change} if on_change else {},
    )
    label_el = Element(
        tag="label",
        props={"style": "font-size:0.875rem;color:#374151;"},
        children=[label] if label else [],
    )
    return Element(
        tag="div",
        props={"style": "display:flex;align-items:center;gap:8px;"},
        children=[input_el, label_el],
    )
