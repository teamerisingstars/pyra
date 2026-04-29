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
    FormField,
    Select,
    Checkbox,
    LoadingButton,
    FileInput,
)
from pyra.forms import validate, use_form
from pyra.app import App, page, get_upload
from pyra.auth import AuthManager, get_current_user
from pyra.config import config, Config
from pyra.db import PersistentState, get_connection
from pyra.oauth import GitHubOAuth, GoogleOAuth, register_oauth_routes
from pyra.email import ConsoleEmailSender, SMTPEmailSender, send_magic_link
from pyra.rbac import RoleManager

__version__ = "0.0.3"

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
    "FormField",
    "Select",
    "Checkbox",
    "LoadingButton",
    "FileInput",
    "validate",
    "use_form",
    "App",
    "page",
    "get_upload",
    "AuthManager",
    "get_current_user",
    "config",
    "Config",
    "PersistentState",
    "get_connection",
    "GitHubOAuth",
    "GoogleOAuth",
    "register_oauth_routes",
    "ConsoleEmailSender",
    "SMTPEmailSender",
    "send_magic_link",
    "RoleManager",
    "__version__",
]
