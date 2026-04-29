"""Pyra - Python-first, AI-native, security-first full-stack framework.

The whole framework in five concepts:
    1. Pages return components.
    2. Components are functions/classes that return more components.
    3. State (signals) is reactive.
    4. Events trigger Python on the server.
    5. AI primitives are components and tools.

Six decorators cover 90% of apps: @page, @component, @tool, @prompt, @eval, @on_event.
"""
from pyra.reactive import Signal, Effect, Computed, batch
from pyra.state import State
from pyra.components import (
    Component,
    Element,
    Text,
    Button,
    VStack,
    HStack,
    Input,
    Badge,
    Card,
    Image,
    Heading,
    Link,
    Spinner,
)
from pyra.app import App, page

__version__ = "0.0.2"

__all__ = [
    "Signal",
    "State",
    "Effect",
    "Computed",
    "batch",
    "Component",
    "Element",
    "Text",
    "Button",
    "VStack",
    "HStack",
    "Input",
    "Badge",
    "Card",
    "Image",
    "Heading",
    "Link",
    "Spinner",
    "App",
    "page",
    "__version__",
]
