# Architecture

This document explains how Pyra's code is organized and what the boundaries are. The high-level vision lives in `../../manifesto.md` — this is the implementation-level companion.

## Layers

Pyra is a layered system. Each layer authenticates the next; each layer treats input from above as potentially hostile; each layer is testable in isolation.

```
Python application code
        ↓
Reactive runtime  ←  state.py (per-session hooks)
        ↓
Component tree   ←  components.py
        ↓
Render          ←  render.py (tree → JSON, sanitization)
        ↓
Reconciler      ←  reconciler.py (JSON tree → patch ops)
        ↓
Transport       ←  transport.py (HMAC sign, replay reject)
        ↓
WebSocket (Starlette / Uvicorn)
        ↓
Browser runtime (~150 lines TS, embedded in app.py for now)
        ↓
DOM
```

## Module map

```
src/pyra/
├── __init__.py        Public API surface (the user import)
├── reactive.py        Signal, Computed, Effect, batch — fine-grained reactivity
├── state.py           State (hook-style), SessionState container
├── components.py      Element, Text, Button, VStack, HStack, Input
├── render.py          Component tree → JSON dict, output sanitization
├── reconciler.py      diff(old_tree, new_tree) → list of patch ops
├── transport.py       HMAC signing, replay protection, Session
└── app.py             App class, @page decorator, WebSocket endpoint, browser runtime (TS string)
```

Future modules (one per manifesto package):

```
framework-security/     auth, capabilities, secrets, audit, sanitizers
framework-ai/           model gateway, agents, prompts, RAG, traces
framework-sandbox/      gVisor / Firecracker / WASM bridges
framework-mcp/          MCP server, schema introspection, error catalog
framework-desktop/      Tauri integration + native bridges + signing
framework-mobile/       Capacitor integration + native bridges + attestation
framework-runtime-js/   ~15KB CSP-strict browser runtime (currently inline in app.py)
framework-cli/          `pyra` command
framework-devtools/     trace viewer, hot reload, AI scaffolder
```

## Boundaries (what goes where)

- **`reactive.py` knows nothing about HTTP, JSON, or the DOM.** It's pure dependency tracking + observer notification. If you want to build a non-web reactive system on it, you can.
- **`components.py` knows nothing about reactivity or transport.** It's a typed dataclass tree.
- **`render.py` knows about components and JSON.** It does not subscribe to signals — it's invoked from inside an `Effect` whose body reads the signals as a side effect.
- **`reconciler.py` knows nothing about reactivity, signals, or HTTP.** Pure function over two JSON dicts.
- **`transport.py` knows nothing about components or reactivity.** Pure HMAC over JSON.
- **`app.py` is the only place that wires all the layers together.** WebSocket endpoint, render Effect, signed message dispatch.

This separation is the single most important thing to preserve. It's what makes the framework auditable, testable, and AI-buildable. **PRs that violate it will be rejected.**

## The render loop

```
1. WebSocket connects (app.py: _ws_endpoint)
2. New Connection state: handler_registry={}, last_tree=None, session_state=SessionState()
3. Effect(do_render) is created — runs the body once immediately:
       a. reset_id_counter()
       b. session_state.begin_render(); push to ContextVar
       c. renderer() runs the user's @page function, which:
          - Reads State() — returns hook cell, registers Effect as observer
          - Returns a Component tree
       d. render_tree(tree, registry) walks the tree, assigning IDs, registering handlers, sanitizing
       e. diff(last_tree, new_tree) → list of patch ops
       f. enqueue {"type": "patch", "ops": [...]} on send_queue
       g. update last_tree
4. Sender task drains send_queue, signs each message via transport.sign_outbound, sends over WebSocket
5. Browser applies ops, attaches event listeners with handler_id strings
6. User clicks → browser sends {"type": "event", "handler_id": "...", "data": {...}}
7. app.py looks up handler_id in registry, calls Python function
8. Handler calls signal.set(...) → notifies Effect → Effect re-runs do_render() → loop back to (3a)
```

## Security boundaries

The transport layer is the only place we trust on either side of the WebSocket — and only after HMAC verification passes. Specifically:

- **Server → client:** Every message is signed. Client verifies (Phase 2 in browser via SubtleCrypto).
- **Client → server:** Only `msg_id` is verified for monotonicity in v0.0.x. Phase 2 will add per-session client signing keys (issued during auth handshake).
- **AI output → DOM:** Goes through `html.escape` server-side; rendered via `textContent` client-side. There is no path where model-generated text reaches `innerHTML`. This is structural, not policy.
- **Tool calls:** Phase 3 — every tool call gated on a signed capability token. Tool arguments schema-validated before invocation.
- **Tenant scoping:** Phase 2 — every state object, vector embedding, prompt, trace carries a tenant tag enforced at the storage layer.

## How to add a feature

1. **Identify the layer.** Which module owns this concern?
2. **If it crosses a layer:** stop. Either you've found a missing primitive, or you're about to break the abstraction. Write an ADR (`docs/adr/`) before coding.
3. **Write the test first.** New behavior → new test in `tests/test_<module>.py`.
4. **Implement.** Stay inside the layer.
5. **Update `__init__.py`** if it's a new public symbol, and add it to `__all__`.
6. **Update `docs/ROADMAP.md`** to mark it done.
7. **Update `CHANGELOG.md`** under "Unreleased".

## Test strategy

- **Unit:** Each module has a `tests/test_<module>.py`. Pure logic, no I/O.
- **End-to-end:** `tests/test_e2e.py` boots a real Uvicorn server in a thread, opens a real WebSocket, exercises the full stack. **Every protocol change needs an E2E test.**
- **Security:** `tests/test_transport.py` covers signing, replay rejection, tampering. **No PR to transport.py merges without security tests.**
- **Future:** `tests/test_security/`, `tests/test_ai/`, fuzz suite for the reconciler, microbenchmarks under `benchmarks/`.

## Why server-driven UI

See manifesto. Short version: AI apps already require server compute on every interaction (model calls, tools, RAG). Co-locating model + state + UI on one Python process eliminates client/server type drift, hydration bugs, and an entire build pipeline. The cost is a persistent connection — a known, solved problem.

## Why signals (not VDOM diffing)

Fine-grained reactivity scales to AI streams. A `Text(stream=...)` node patches incrementally without restarting the render. Coarse re-render (React-style) saturates the wire on token streams.

## Why HMAC + monotonic msg_id

- **HMAC** — server proves messages are authentic. Tampering rejected.
- **Monotonic msg_id** — replay rejected. Out-of-order reordering rejected.
- **Together** — a hostile network cannot inject events or replay past ones.

Per-session keys are dev-default in v0.0.x; production deploys derive them from a KMS-managed master.
