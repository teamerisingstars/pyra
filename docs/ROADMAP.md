# Roadmap

Pyra is built in phases that map to the manifesto. This document is the **single source of truth** for what's done, what's next, and what's open for contribution.

Status legend: `✅ done`  `🟡 in progress`  `⬜ open`  `🔜 next-up`

---

## Phase 1 — Foundations + security spine

| Status | Item | Notes |
|---|---|---|
| ✅ | Reactive engine: `Signal`, `Computed`, `Effect`, `batch` | `src/pyra/reactive.py` |
| ✅ | Signed WebSocket transport (HMAC-SHA256, monotonic msg_id, replay rejection) | `src/pyra/transport.py` |
| ✅ | Component primitives: `Text`, `Button`, `VStack`, `HStack`, `Input` | `src/pyra/components.py` |
| ✅ | Diff-based reconciler (init/replace_text/set_attr/remove_attr/handler ops/replace_node) | `src/pyra/reconciler.py` |
| ✅ | Per-session `State` (hook-style, ContextVar-driven) | `src/pyra/state.py` |
| ✅ | End-to-end counter example | `examples/counter/` |
| ✅ | 33 tests (reactive, reconciler, state, transport, E2E WebSocket) | `tests/` |
| 🟡 | CSP-strict JS runtime + Trusted Types | dev runtime is permissive; need build pipeline |
| ⬜ | Stable error code catalog (skeleton) | `framework-mcp` will consume |
| ⬜ | Schema introspection API (Pydantic-backed) | every component exposes `.schema()` |

## Phase 2 — Reactivity, routing, AuthN/AuthZ, AI-build surface

🔜 **Next up — pick from here.**

| Status | Item | Priority | Good first? | Notes |
|---|---|---|---|---|
| ⬜ | File-based routing (`pages/foo.py` → `/foo`) | P0 |   | Module loader + URL → renderer map |
| ⬜ | `Form` primitive with validation | P0 |   | Pydantic-backed |
| ⬜ | Server-side rendering on initial GET | P1 |   | Render once before the WebSocket connects |
| ⬜ | Optimistic UI primitives | P1 |   | `optimistic=` arg on `on_click` |
| ⬜ | AuthN: OAuth + PKCE adapter | P0 |   | `Authlib` |
| ⬜ | AuthN: Passkeys (WebAuthn) adapter | P0 |   | `webauthn` library |
| ⬜ | AuthN: Magic-link adapter | P1 |   | Email + signed token |
| ⬜ | AuthZ: RBAC + capability tokens | P0 |   | New package: `framework-security` |
| ⬜ | Audit log skeleton | P1 |   | Postgres + hash-chained entries |
| ⬜ | MCP server (`framework-mcp`) skeleton | P0 |   | Exposes `list_components`, `get_schema`, `lookup_error` |
| ⬜ | `llms.txt` generator | P1 | ✅ | Read schemas, write canonical spec |
| ⬜ | `pyra fix <error_code>` deterministic patch CLI | P2 |   | Reads error catalog, proposes diff |
| ⬜ | Keyed list reconciliation | P1 |   | Replace "child-count differs → replace_node" with keyed diff |
| ⬜ | Hot reload via watchfiles | P1 | ✅ | Watch source, restart Effect |
| ⬜ | Add components: `Image`, `Link`, `Heading`, `Card`, `Badge`, `Spinner` | P2 | ✅ | Each in `components.py`, with tests |
| ⬜ | Add example: `todo-app` | P2 | ✅ | Lists, optimistic UI, persistence stub |
| ⬜ | Add example: `chat` (no AI yet) | P2 | ✅ | Multi-user via `scope="room"` (precursor) |

## Phase 3 — AI runtime + AI security

| Status | Item | Priority | Notes |
|---|---|---|---|
| ⬜ | Model gateway (provider-agnostic: Anthropic, OpenAI, Ollama, MLX) | P0 | New package: `framework-ai` |
| ⬜ | `AIChat` component with streaming | P0 |   |
| ⬜ | `AICompletion` component | P0 |   |
| ⬜ | `AIForm` component | P1 |   |
| ⬜ | Streaming-aware reconciler (token streams as first-class) | P0 |   |
| ⬜ | `DurableAgent` with Postgres checkpoint | P0 | Survives disconnects |
| ⬜ | `Approval` primitive (human-in-the-loop) | P0 |   |
| ⬜ | Prompt registry with versioning | P0 | `@prompt` decorator |
| ⬜ | `framework eval` CLI + safety eval suite | P1 |   |
| ⬜ | Vector store (pgvector default) with tenant scoping | P0 |   |
| ⬜ | Prompt-injection guards (structural, classifier, validator, scanner) | P0 | Layered defense |
| ⬜ | Capability-scoped `@tool` runtime | P0 | Signed tokens, policy enforcement |
| ⬜ | Sandboxed tool execution (gVisor + WASM) | P1 | New package: `framework-sandbox` |
| ⬜ | Cost ledger with hard caps | P0 |   |
| ⬜ | PII / secret redactor for traces and logs | P0 | `presidio` |
| ⬜ | Trace viewer in dev console | P1 |   |
| ⬜ | `pyra new "<intent>"` AI scaffolder | P2 | Uses MCP server's schema |

## Phase 4 — Cross-platform + production

| Status | Item | Priority | Notes |
|---|---|---|---|
| ⬜ | `pyra build pwa` (manifest, service worker, install prompt, push) | P0 |   |
| ⬜ | `pyra build desktop` (Tauri 2 wrapper, signed binaries) | P0 |   |
| ⬜ | `pyra build mobile` (Capacitor 6 → Xcode + Android Studio projects) | P0 |   |
| ⬜ | Native bridges: Camera, Microphone, Geolocation, Push, Biometric, FileSystem | P0 |   |
| ⬜ | `SecureStore` (Keychain / Keystore / Credential Manager) | P0 |   |
| ⬜ | Code signing + notarization in build pipeline | P0 |   |
| ⬜ | SBOM (CycloneDX) + Sigstore signing | P0 |   |
| ⬜ | Background jobs and scheduled tasks | P1 |   |
| ⬜ | Edge rendering / regional deploys | P1 |   |
| ⬜ | HIPAA-ready mode flag | P2 |   |
| ⬜ | SOC 2 evidence-collection skill | P2 |   |
| ⬜ | Documentation site, starter templates | P0 |   |

## Phase 5 — Ecosystem

| Status | Item | Priority | Notes |
|---|---|---|---|
| ⬜ | Plugin system | P1 |   |
| ⬜ | Component library (`pyra-ui`) | P1 |   |
| ⬜ | Agent recipes (research, support, coding, data analysis) | P1 |   |
| ⬜ | Stripe / auth / email / vector DB integrations | P2 |   |
| ⬜ | Mode B (embedded server) for offline desktop and mobile | P2 |   |
| ⬜ | Penetration test + third-party security audit | P0 | Before public 1.0 |

---

## Good first issues (curated)

These are scoped, well-understood, and don't require deep familiarity:

1. **Add a `Heading` component** with size variants (`h1`–`h6`). Mirror `Text` in `components.py`. Include tests.
2. **Add a `Link` component** with `href` and security defaults (`rel="noopener noreferrer"` for external links). Include tests.
3. **Add a `Spinner` component** (CSS-only). Include tests.
4. **Build the `todo-app` example** under `examples/todo-app/`. Should demonstrate per-session state, list rendering, optimistic UI (when available).
5. **Document the patch protocol formally** in `docs/PATCH_PROTOCOL.md`. Each op, its JSON shape, when emitted, how the client applies it.
6. **Add a microbenchmark** for the reconciler against a 1000-node tree. Put it in `benchmarks/`.
7. **Improve `_accepts_arg`** in `app.py` — it's a heuristic that breaks on `lambda evt: ...`. Replace with a proper signature inspection that handles lambdas.
8. **Write a contributor onboarding example** — a 30-minute "build your first Pyra component" tutorial in `docs/TUTORIAL.md`.

To claim one: open an issue titled `[good-first-issue] <task>` and link this section. We'll assign it.

---

## Decision log

Major architectural decisions (use ADR format in `docs/adr/` for new ones):

- **Server-driven UI** over client-side React-style. (Rationale: manifesto.)
- **Signals over VDOM** for fine-grained reactivity. (Rationale: streaming-aware reconciliation, manifesto.)
- **HMAC-SHA256 + monotonic msg_id** as the transport security baseline. Per-session keys derived in dev; production uses KMS.
- **Hook-style `State`** with ContextVar. React-style call-order discipline. (Rationale: explicit > magic.)
- **Custom durable execution** rather than Temporal/DBOS. (Rationale: lightweight v1; can swap later.)
- **Pydantic v2 as single source of truth** for schemas (IDE, runtime, MCP).
