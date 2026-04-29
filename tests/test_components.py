"""Tests for UI components: Badge, Card, Image, Heading, Link, Spinner, and Element.key."""
from __future__ import annotations

from pyra.components import Badge, Card, Element, Heading, Image, Link, Spinner, FormField, Select, Checkbox


# ---------------------------------------------------------------------------
# Badge
# ---------------------------------------------------------------------------

def test_badge_tag() -> None:
    b = Badge("new")
    assert b.tag == "span"


def test_badge_default_color_in_style() -> None:
    b = Badge("new")
    assert "#6366f1" in b.props["style"]


def test_badge_custom_color_in_style() -> None:
    b = Badge("hot", color="#ff0000")
    assert "#ff0000" in b.props["style"]


def test_badge_content_coerced_to_str() -> None:
    b = Badge(42)
    assert b.children == ["42"]


def test_badge_style_contains_border_radius() -> None:
    b = Badge("x")
    assert "border-radius:9999px" in b.props["style"]


# ---------------------------------------------------------------------------
# Card
# ---------------------------------------------------------------------------

def test_card_tag() -> None:
    c = Card()
    assert c.tag == "div"


def test_card_title_renders_h3() -> None:
    c = Card(title="Hello")
    assert len(c.children) == 1
    h3 = c.children[0]
    assert isinstance(h3, Element)
    assert h3.tag == "h3"
    assert h3.children == ["Hello"]


def test_card_no_title_no_extra_child() -> None:
    from pyra.components import Text
    child = Text("body")
    c = Card(child)
    # Only the one child we passed — no injected h3.
    assert len(c.children) == 1
    assert c.children[0] is child


def test_card_title_and_children_order() -> None:
    from pyra.components import Text
    child = Text("content")
    c = Card(child, title="My Card")
    assert len(c.children) == 2
    assert isinstance(c.children[0], Element)
    assert c.children[0].tag == "h3"
    assert c.children[1] is child


def test_card_style_prop_set() -> None:
    c = Card(style="color:red;")
    assert "border:1px solid #e5e7eb" in c.props["style"]
    assert "color:red;" in c.props["style"]


# ---------------------------------------------------------------------------
# Image
# ---------------------------------------------------------------------------

def test_image_tag() -> None:
    img = Image("https://example.com/img.png")
    assert img.tag == "img"


def test_image_src_in_props() -> None:
    img = Image("https://example.com/img.png")
    assert img.props["src"] == "https://example.com/img.png"


def test_image_alt_in_props() -> None:
    img = Image("x.png", alt="a photo")
    assert img.props["alt"] == "a photo"


def test_image_default_alt_empty() -> None:
    img = Image("x.png")
    assert img.props["alt"] == ""


def test_image_width_in_style() -> None:
    img = Image("x.png", width="200px")
    assert "width:200px" in img.props["style"]


def test_image_height_in_style() -> None:
    img = Image("x.png", height="100px")
    assert "height:100px" in img.props["style"]


def test_image_no_style_when_no_width_height() -> None:
    img = Image("x.png")
    assert "style" not in img.props


def test_image_width_and_height_combined() -> None:
    img = Image("x.png", width="80px", height="80px")
    assert "width:80px" in img.props["style"]
    assert "height:80px" in img.props["style"]


# ---------------------------------------------------------------------------
# Heading
# ---------------------------------------------------------------------------

def test_heading_default_level_is_h1() -> None:
    h = Heading("Title")
    assert h.tag == "h1"


def test_heading_level_3() -> None:
    h = Heading("Section", level=3)
    assert h.tag == "h3"


def test_heading_content_coerced_to_str() -> None:
    h = Heading(99)
    assert h.children == ["99"]


def test_heading_clamp_level_below_1() -> None:
    h = Heading("x", level=0)
    assert h.tag == "h1"


def test_heading_clamp_level_above_6() -> None:
    h = Heading("x", level=7)
    assert h.tag == "h6"


def test_heading_boundary_level_6() -> None:
    h = Heading("x", level=6)
    assert h.tag == "h6"


# ---------------------------------------------------------------------------
# Link
# ---------------------------------------------------------------------------

def test_link_tag() -> None:
    lnk = Link("click me", href="/home")
    assert lnk.tag == "a"


def test_link_href_in_props() -> None:
    lnk = Link("go", href="/about")
    assert lnk.props["href"] == "/about"


def test_link_label_coerced_to_str() -> None:
    lnk = Link(42, href="/")
    assert lnk.children == ["42"]


def test_link_internal_no_rel() -> None:
    lnk = Link("home", href="/")
    assert "rel" not in lnk.props


def test_link_external_adds_rel() -> None:
    lnk = Link("ext", href="https://example.com", external=True)
    assert lnk.props.get("rel") == "noopener noreferrer"


def test_link_default_href_empty() -> None:
    lnk = Link("noop")
    assert lnk.props["href"] == ""


# ---------------------------------------------------------------------------
# Spinner
# ---------------------------------------------------------------------------

def test_spinner_tag() -> None:
    s = Spinner()
    assert s.tag == "div"


def test_spinner_class_prop() -> None:
    s = Spinner()
    assert s.props.get("class") == "pyra-spinner"


def test_spinner_style_border_radius() -> None:
    s = Spinner()
    assert "border-radius:50%" in s.props["style"]


def test_spinner_custom_size_in_style() -> None:
    s = Spinner(size="48px")
    assert "width:48px" in s.props["style"]
    assert "height:48px" in s.props["style"]


def test_spinner_custom_color_in_style() -> None:
    s = Spinner(color="#333")
    assert "#333" in s.props["style"]


# ---------------------------------------------------------------------------
# Element.key field
# ---------------------------------------------------------------------------

def test_element_key_default_none() -> None:
    e = Element(tag="div")
    assert e.key is None


def test_element_key_set_to_string() -> None:
    e = Element(tag="li", key="item-1")
    assert e.key == "item-1"


def test_element_key_not_in_props() -> None:
    """key must never bleed into props — it is reconciler metadata only."""
    e = Element(tag="div", key="k")
    assert "key" not in e.props


# ---------------------------------------------------------------------------
# FormField
# ---------------------------------------------------------------------------

def test_form_field_tag():
    assert FormField("email").tag == "div"


def test_form_field_has_input_child():
    ff = FormField("email", value="x")
    inputs = [c for c in ff.children if isinstance(c, Element) and c.tag == "input"]
    assert len(inputs) == 1
    assert inputs[0].props["value"] == "x"


def test_form_field_error_adds_span():
    ff = FormField("email", error="required")
    spans = [c for c in ff.children if isinstance(c, Element) and c.tag == "span"]
    assert any("required" in c.children for c in spans)


def test_form_field_no_error_no_span():
    ff = FormField("email")
    spans = [c for c in ff.children if isinstance(c, Element) and c.tag == "span"]
    assert len(spans) == 0


# ---------------------------------------------------------------------------
# Select
# ---------------------------------------------------------------------------

def test_select_returns_div():
    s = Select("color", [("r", "Red"), ("b", "Blue")])
    assert s.tag == "div"


def test_select_options_count():
    s = Select("color", [("r", "Red"), ("b", "Blue"), ("g", "Green")])
    selects = [c for c in s.children if isinstance(c, Element) and c.tag == "select"]
    assert len(selects[0].children) == 3


def test_select_marks_selected_value():
    s = Select("color", [("r", "Red"), ("b", "Blue")], value="b")
    sel_el = next(c for c in s.children if isinstance(c, Element) and c.tag == "select")
    opt_b = next(o for o in sel_el.children if o.props.get("value") == "b")
    assert opt_b.props.get("selected") == "true"


# ---------------------------------------------------------------------------
# Checkbox
# ---------------------------------------------------------------------------

def test_checkbox_tag():
    assert Checkbox("agree").tag == "div"


def test_checkbox_checked_prop():
    cb = Checkbox("agree", checked=True)
    inp = next(c for c in cb.children if isinstance(c, Element) and c.tag == "input")
    assert inp.props.get("checked") == "true"


def test_checkbox_unchecked_no_prop():
    cb = Checkbox("agree", checked=False)
    inp = next(c for c in cb.children if isinstance(c, Element) and c.tag == "input")
    assert "checked" not in inp.props
