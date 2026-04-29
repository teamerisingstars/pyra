from __future__ import annotations

import pytest

from pyra.components import Element, Heading, Link, Spinner


# ---------------------------------------------------------------------------
# Heading
# ---------------------------------------------------------------------------

def test_heading_default_level() -> None:
    el = Heading("Hello")
    assert isinstance(el, Element)
    assert el.tag == "h1"
    assert el.children == ["Hello"]


def test_heading_level_3() -> None:
    el = Heading("Section", level=3)
    assert el.tag == "h3"
    assert el.children == ["Section"]


def test_heading_level_clamped_low() -> None:
    el = Heading("Too low", level=0)
    assert el.tag == "h1"


def test_heading_level_clamped_high() -> None:
    el = Heading("Too high", level=7)
    assert el.tag == "h6"


def test_heading_coerces_content_to_str() -> None:
    el = Heading(42)
    assert el.children == ["42"]


# ---------------------------------------------------------------------------
# Link
# ---------------------------------------------------------------------------

def test_link_internal() -> None:
    el = Link("Home", href="/")
    assert el.tag == "a"
    assert el.props["href"] == "/"
    assert "rel" not in el.props
    assert el.children == ["Home"]


def test_link_external_adds_rel() -> None:
    el = Link("Pyra", href="https://example.com", external=True)
    assert el.props["rel"] == "noopener noreferrer"
    assert el.props["href"] == "https://example.com"


def test_link_external_false_no_rel() -> None:
    el = Link("About", href="/about", external=False)
    assert "rel" not in el.props


def test_link_default_href_empty() -> None:
    el = Link("No href")
    assert el.props["href"] == ""


def test_link_coerces_label_to_str() -> None:
    el = Link(99)
    assert el.children == ["99"]


# ---------------------------------------------------------------------------
# Spinner
# ---------------------------------------------------------------------------

def test_spinner_tag() -> None:
    el = Spinner()
    assert isinstance(el, Element)
    assert el.tag == "div"


def test_spinner_class() -> None:
    el = Spinner()
    assert el.props.get("class") == "pyra-spinner"


def test_spinner_style_border_radius() -> None:
    el = Spinner()
    assert "border-radius:50%" in el.props["style"]


def test_spinner_custom_size_in_style() -> None:
    el = Spinner(size="48px")
    assert "width:48px" in el.props["style"]
    assert "height:48px" in el.props["style"]


def test_spinner_custom_color_in_style() -> None:
    el = Spinner(color="#ff0000")
    assert "#ff0000" in el.props["style"]


def test_spinner_no_children() -> None:
    el = Spinner()
    assert el.children == []
