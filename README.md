# Pyra

**Python-first, AI-native, security-first full-stack framework.**

> One language. One codebase. Every device. AI built in. AI builds it. Secure by default.

The architectural manifesto lives in [`../manifesto.md`](../manifesto.md).

## Status — v0.0.2 (early, working)

- ✅ Reactive engine: `Signal`, `Computed`, `Effect`, `batch`
- ✅ Signed WebSocket transport (HMAC-SHA256, monotonic msg_id, replay rejection)
- ✅ Diff-based reconciler (minimal patch ops over the wire)
- ✅ Per-session `State` (hook-style, scoped per connection)
- ✅ Component primitives: `Text`, `Button`, `VStack`, `HStack`, `Input`
- ✅ Output sanitization on every patch (`textContent`, never `innerHTML`)
- ✅ 33 tests passing — reactive, reconciler, state, transport, end-to-end WebSocket
- 🔜 File-based routing, AuthN/AuthZ, MCP server (the AI-buildability layer)
- 🔜 AI runtime (`AIChat`, `DurableAgent`, prompt registry, evals)
- 🔜 Cross-platform builds (PWA, Tauri desktop, Capacitor mobile)

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the full plan.

## Five concepts

```python
from pyra import App, page, State, VStack, Text, Button

@page("/")
def home():
    count = State(0)        # per-session — each tab gets its own
    return VStack(
        Text(f"Count: {count.value}"),
        Button("+", on_click=lambda: count.update(lambda c: c + 1)),
    )

App().run()
```

## Quickstart

```bash
git clone <fork>
cd pyra
pip install -e ".[dev]"
cd examples/counter
python main.py
# open http://127.0.0.1:7340 — and a second tab to see independent counters
```

## Tests

```bash
pytest                # all 33 tests
pytest -v --tb=short  # verbose
```

## For contributors

| Document | What's in it |
|---|---|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Setup, dev loop, code style, PR process |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | How the code is organized; layer boundaries |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | What's done, what's next, good first issues |
| [`docs/PATCH_PROTOCOL.md`](docs/PATCH_PROTOCOL.md) | Wire format spec |
| [`SECURITY.md`](SECURITY.md) | Threat model, vulnerability reporting, secure-coding rules |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history |
| [`CLAUDE.md`](CLAUDE.md) | Guidance for AI coding agents working on Pyra |
| [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) | Community standards |

## Architecture (current vertical slice)

```
Browser  ──ws (signed)──▶  Starlette server
   ▲                          │
   │                          ▼
   │                     Effect (re-runs on signal change)
   │                          │
   │                          ▼
   │                  per-session State context
   │                          │
   │                          ▼
   │                     Component tree
   │                          │
   │                          ▼
   │                     render_tree → diff(old, new)
   │                          │
   │                          ▼
   │                     patch ops, signed
   │                          │
   └──────────  apply ops  ◀──┘
```

Every server → client message is HMAC-signed; `msg_id` is monotonic; tampering or replay is rejected. Text always rendered via `textContent` (no `innerHTML`) — XSS structurally impossible at the render layer.

## License

MIT — see [`LICENSE`](LICENSE).
