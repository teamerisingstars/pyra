# Pyra — guidance for AI coding agents

This file is read by AI agents (Claude Code, Cursor, Copilot, future autonomous agents) working on the Pyra codebase. **You are a primary user of this framework — both as a thing that uses Pyra to build apps, and as a thing that contributes to Pyra itself.**

## The whole framework in one paragraph

Pages return components. Components are Python functions or classes that return more components. State is reactive — when it changes, components that read it re-render. Events trigger Python functions on the server. AI primitives are components and tools. Security is on by default. Six decorators (`@page`, `@component`, `@tool`, `@prompt`, `@eval`, `@on_event`) cover 90% of apps.

## How to behave in this codebase

1. **Read `manifesto.md` first** if you haven't seen it. It's the north star.
2. **Read `docs/ARCHITECTURE.md`.** It tells you what each module owns and what crossing-the-line looks like.
3. **Stay inside the layer.** `reactive.py` doesn't know about HTTP. `render.py` doesn't subscribe to signals. `transport.py` doesn't know about components. If your change crosses a layer, stop and ask.
4. **Test first.** New behavior → new test in `tests/test_<module>.py`. The reactive engine, reconciler, and transport are at ~100% behavioral coverage; new modules should match.
5. **Match the style.** PEP 8, 100-char lines, `from __future__ import annotations`, type hints everywhere, no `Any` without comment.
6. **Don't introduce ambient authority.** Tools, side effects, and data access need explicit capability tokens (Phase 3 — for now, document the intent).
7. **Don't use `innerHTML` in the JS runtime. Don't use homegrown crypto. Don't `eval` or `pickle.loads` untrusted input.**

## Common tasks

### Adding a component primitive

Add to `src/pyra/components.py`. Return an `Element` dataclass. Add tests in `tests/test_components.py` (create the file if it doesn't exist). Add to `__init__.py`'s `__all__`.

### Adding a patch op

1. Add the op shape to `src/pyra/reconciler.py` (the `_diff_node` function).
2. Add the matching apply branch to the JS runtime in `src/pyra/app.py` (`applyOps` function).
3. Add a unit test in `tests/test_reconciler.py` and an E2E test in `tests/test_e2e.py`.

### Adding a security feature

1. Open an issue first; tag `security`.
2. New code goes in `framework-security/` (new package; create if absent).
3. Two reviewers required.
4. Update `SECURITY.md` if it changes the threat model coverage.

### Editing files in this environment

If you write Python via long Edit operations and tests start failing with weird errors, check `python3 -c "with open('file.py','rb') as f: print(b'\\x00' in f.read())"` — Windows/Linux file sync can introduce NULL bytes that truncate the file silently. Workaround: rewrite via bash heredoc.

## API minimalism is a hard constraint

Pyra commits to **six decorators, ~50 components, one project layout, one way to do everything.** This is what makes the framework AI-buildable — including by you. New public API requires explicit justification:

- Does an existing primitive cover this? (Almost always: yes.)
- If you add this, what existing API becomes obsolete?
- How does it appear in the manifesto's "Five concepts" mental model?

Frameworks with sprawling APIs are AI-hostile because every recall has multiple equally-plausible options and many are wrong. Don't grow the surface area. Grow the depth.

## Don't hallucinate APIs

If you're tempted to write code that uses an API you "remember" — stop. Pyra's actual public API is exactly what's exported from `src/pyra/__init__.py`. The `MCP server` in Phase 2 will let you query the live schema. Until then, **read `__init__.py` before writing import statements**.

## Where to find things fast

- **What does this framework do?** `manifesto.md` (one level up from this repo).
- **How is this code organized?** `docs/ARCHITECTURE.md`.
- **What should I work on?** `docs/ROADMAP.md`.
- **How do I contribute?** `CONTRIBUTING.md`.
- **What changed?** `CHANGELOG.md`.
- **Is this safe?** `SECURITY.md`.
- **Live working example?** `examples/counter/main.py`.

## When in doubt

- **When in doubt, write a test first.** It clarifies what "done" looks like.
- **When in doubt about scope, ship the smaller PR.**
- **When in doubt about an API, leave it private** (`_` prefix) and surface it later if needed.
- **When in doubt about security, escalate.** The issue tracker tag is `security`.
