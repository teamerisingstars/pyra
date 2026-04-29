# Build Your First Pyra Component

A 30-minute walkthrough for new contributors. You will build a `Badge` component
from scratch — test-first, following the same process used for every component in
the framework. By the end you will have a passing test suite, a working example,
and a clear mental model of how the layers fit together.

**Prerequisites:** Python 3.10+, `git`, basic familiarity with Python dataclasses.

---

## 1. Set up your environment (5 min)

```bash
git clone https://github.com/<your-fork>/pyra.git
cd pyra
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -e ".[dev]"
```

Verify everything is wired up:

```bash
pytest          # 33 tests pass
python examples/counter/main.py   # open http://127.0.0.1:7340
```

You should see a counter with +/−/Reset buttons. Open two tabs — each tab has its
own independent counter. That is per-session reactive state in action.

---

## 2. Understand the stack in 90 seconds

Pyra is a server-driven UI. Your Python code runs on the server; the browser is a
thin patch-applier. The data flow on every state change:

```
@page function re-runs
  → Component tree (pure data, no I/O)
    → render.py turns it into a JSON dict and assigns stable IDs
      → reconciler.py diffs old dict vs new dict → list of patch ops
        → transport.py HMAC-signs the ops
          → WebSocket → browser applies minimal DOM mutations
```

Components live in `src/pyra/components.py`. They are **pure data** — no HTTP, no
reactivity, no I/O. A component is just a function that returns an `Element`:

```python
def Text(content: Any) -> Element:
    return Element(tag="span", children=[str(content)])
```

That is the whole pattern. `Element` holds a tag, props dict, children list, and
handlers dict. Everything else in the stack handles the rest.

---

## 3. Write the test first (10 min)

The project uses plain pytest. Tests live in `tests/` and mirror the source layout:
`src/pyra/components.py` → `tests/test_components.py`.

Open `tests/test_components.py` (create it if it does not exist) and add:

```python
from __future__ import annotations

from pyra.components import Badge, Element


def test_badge_returns_element():
    b = Badge("new")
    assert isinstance(b, Element)


def test_badge_tag_is_span():
    assert Badge("x").tag == "span"


def test_badge_content_in_children():
    assert Badge("new").children == ["new"]


def test_badge_default_color():
    style = Badge("x").props["style"]
    assert "background" in style


def test_badge_custom_color():
    style = Badge("x", color="#e00").props["style"]
    assert "#e00" in style


def test_badge_coerces_content_to_str():
    assert Badge(42).children == ["42"]
```

Run the tests — they should all **fail** because `Badge` does not exist yet:

```bash
pytest tests/test_components.py -v
```

This is the red step. Good.

---

## 4. Implement the component (5 min)

Open `src/pyra/components.py`. You will see the existing components at the bottom.
Add `Badge` after `Input`:

```python
def Badge(content: Any, color: str = "#6366f1") -> Element:
    style = (
        f"display:inline-block;padding:2px 8px;border-radius:9999px;"
        f"background:{color};color:#fff;font-size:0.75rem;font-weight:600;"
    )
    return Element(tag="span", props={"style": style}, children=[str(content)])
```

Run the tests again — they should all **pass**:

```bash
pytest tests/test_components.py -v
```

Run the full suite to make sure nothing regressed:

```bash
pytest
```

---

## 5. Export the new symbol (2 min)

New public components must be added to `src/pyra/__init__.py` in two places:

```python
# In the import block, add Badge to the components import:
from pyra.components import (
    Component,
    Element,
    Text,
    Button,
    VStack,
    HStack,
    Input,
    Badge,       # ← add this
)

# In __all__, add:
    "Badge",     # ← add this
```

Verify the public import works:

```python
python -c "from pyra import Badge; print(Badge('ok'))"
```

---

## 6. Use it in an example (5 min)

Open `examples/counter/main.py` and add a badge to the counter to see it live:

```python
from pyra import App, Badge, Button, HStack, State, Text, VStack, page


@page("/")
def home():
    count = State(0)
    badge = Badge("live", color="#10b981")
    return VStack(
        HStack(Text("Pyra counter"), badge),
        Text(f"Count: {count.value}"),
        HStack(
            Button("−", on_click=lambda: count.update(lambda c: c - 1)),
            Button("+", on_click=lambda: count.update(lambda c: c + 1)),
            Button("Reset", on_click=lambda: count.set(0)),
        ),
    )


app = App()

if __name__ == "__main__":
    app.run()
```

Run it:

```bash
cd examples/counter
python main.py
```

You should see a green "live" badge next to the title. The badge is a static
component — it holds no state, emits no events, just renders. That is the simplest
possible component.

---

## 7. Open a PR

The project asks for one PR per logical change and an issue opened first for
non-trivial work. For a component this size, you can open the PR directly.

```bash
git checkout -b feat/components-badge
git add src/pyra/components.py src/pyra/__init__.py tests/test_components.py
git commit -m "feat(components): add Badge primitive"
git push origin feat/components-badge
```

In your PR description include:

- **What:** one-line summary
- **Why:** links to the roadmap item
- **Tests:** how many added, what they cover
- **Risk:** none / low / medium — and why

---

## What you just learned

| Concept | Where it lives |
|---------|---------------|
| Components are pure data | `src/pyra/components.py` |
| `Element(tag, props, children, handlers)` | same |
| Tests mirror source layout | `tests/test_components.py` |
| Public API surface | `src/pyra/__init__.py` — `__all__` |
| Render (component → JSON) | `src/pyra/render.py` |
| Reconciler (JSON diff → patch ops) | `src/pyra/reconciler.py` |
| Transport (HMAC sign) | `src/pyra/transport.py` |
| Everything wired together | `src/pyra/app.py` |

The same pattern applies to more complex contributions:

- **A component with events** (like `Button`) — add a `handlers` dict, wire `on_click`
- **A layout primitive** (like `VStack`) — compose children, expose style props
- **A stateful page** (like the counter) — call `State(initial)` inside `@page`

Read `docs/ARCHITECTURE.md` before touching anything outside `components.py` — the
layer boundaries are strictly enforced and PRs that cross them are rejected.

---

## Next steps

- Pick a `good-first-issue` from `docs/ROADMAP.md`
- Read `CONTRIBUTING.md` for the full PR checklist
- Read `docs/ARCHITECTURE.md` before adding a feature that crosses modules
