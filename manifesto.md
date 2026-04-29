# A Python-First, AI-Native, AI-Buildable, Security-First Full-Stack Framework

*A working manifesto — v0.4 (build-ready, security-hardened, AI-buildable)*

---

## North Star

We are building a full-stack framework where developers — and the AI agents that increasingly build alongside them — can ship modern, real-time, AI-powered applications in **only Python**, deployed to **web, desktop, and mobile** from a single codebase. The framework treats **AI as a first-class primitive**, **security as a foundational design constraint**, and **AI-buildability as a product requirement**: the API is small enough for a human to learn in an afternoon and consistent enough for an AI agent to author without hallucinating.

> **One language. One codebase. Every device. AI built in. AI builds it. Secure by default.**

---

## The whole thing in one paragraph

Pages return components. Components are Python functions or classes that return more components. State is reactive — when it changes, components that read it re-render. Events trigger Python functions on the server. AI primitives are components (`AIChat`, `AICompletion`) and tools (`@tool`-decorated functions an agent can call). Security is on by default. That is the entire mental model.

## Five concepts cover 90% of apps

```python
@page("/")                              # 1. Pages — routes
def home():
    return VStack(Text("Hello"))

@component                              # 2. Components — reusable UI
def Greeting(name: str):
    return Text(f"Hi, {name}")

count = State(0)                        # 3. State — reactive values

@on_event("click")                      # 4. Events — server-side handlers
def increment():
    count.set(count.value + 1)

@tool                                   # 5. AI — tools an agent can call
async def search(query: str): ...
```

Five concepts. Six decorators (the five above plus `@prompt`). About fifty components. One project layout. Everything else is depth you opt into when you need it.

This minimalism is not a marketing claim. It is **the architectural commitment** that makes the framework AI-buildable.

---

## Why now

**Python won the AI layer.** Every model, framework, eval harness, and orchestrator lives in Python. New software is increasingly shaped by model calls, retrieval, tools, and agents.

**Frontend complexity is collapsing.** A typical "modern" app needs a build system, bundler, router, state library, data layer, type contracts, mobile shells, desktop wrappers, and a security pipeline — all separate, all separately attacked, all separately learned by anyone (or anything) trying to write the app.

**AI changes both what an "app" is and who builds it.** Agentic apps, streaming UIs, multimodal I/O, generative interfaces. And: AI coding agents (Claude Code, Cursor, Copilot, Devin, OpenAI's agents) now write a non-trivial share of production code. Frameworks designed before this moment treat AI authorship as an external concern. Frameworks designed for this moment treat it as a primary user.

The question isn't *whether* a Python-first, AI-native, AI-buildable, security-first framework should exist. It's *who builds the one that wins*.

---

## Naming proposals

Five candidates. Verify domain and PyPI availability before committing.

**1. Pyra** — Python + reactor. Reactive, slightly ancient. Best for a developer-tools brand.

**2. Cortex** — Neural, central, intelligent. Best for an AI-era brand.

**3. Conduit** — Source → channel → sink. Honest, technical.

**4. Resonant** — Names the deepest hard problem (signals, propagation).

**5. Aether** — The invisible medium. Disappearing-complexity story.

**Recommendation:** **Pyra** for developer-tools posture, **Cortex** for AI-era posture. The rest of this document uses *the framework* as a placeholder.

---

## The honest framing

Browsers natively run JavaScript and WebAssembly — not Python. We don't pretend otherwise.

What we do:

- Developers write **only Python**.
- A tiny (~15KB) JavaScript runtime in the browser/webview applies DOM patches and forwards events. Nothing else.
- All application logic — components, state, AI calls, agent loops — runs in Python on a server (cloud or embedded).
- The wire is a streaming, bidirectional protocol (WebSocket; SSE/HTTP fallback) that is signed, authenticated, and replay-resistant by default.

This is the **server-driven UI** pattern proven by Phoenix LiveView, Hotwire, and Livewire — adapted for Python, extended for AI workloads, hardened for adversarial environments, and shaped to be writable by AI coding agents.

---

## Architecture

A layered architecture with explicit trust boundaries and an explicit AI-build surface. Every layer authenticates the next; every layer treats input from above as potentially hostile; every layer is introspectable so AI agents can reason about it.

```
┌───────────────────────────────────────────────────────────────┐
│                    Edge / Ingress Layer                       │
│   TLS 1.3  •  WAF  •  DDoS  •  Rate limit  •  Request sign    │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                      Identity Layer                           │
│   AuthN: OAuth • Passkeys • SSO • MFA                         │
│   AuthZ: RBAC • ABAC • capability-scoped tokens               │
│   Session: signed, rotating, device-bound                     │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                  Python Application Layer                     │
│       pages • components • state • agents • prompts           │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                Reactive Python Runtime                        │
│       signals • effects • dependency graph • scheduler        │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                    AI Runtime Layer                           │
│   model gateway (cloud + local) • streaming                   │
│   durable agents • capability-scoped tools • RAG              │
│   prompt registry • evals • traces • cost ledger              │
│   prompt-injection guards • output sanitizer • approval flow  │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                Sandbox / Execution Isolation                  │
│   gVisor / Firecracker / WASM  •  network policy              │
│   per-tool capabilities  •  CPU / memory / time quotas        │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                    Data Layer                                 │
│   tenant-isolated state  •  vector store  •  object store     │
│   encryption at rest  •  field-level encryption for PII       │
│   tamper-evident audit log                                    │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                  UI Component Tree (VDOM)                     │
│       text • forms • multimodal • streams • approvals         │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│           Streaming-Aware Reconciler / Diff Engine            │
│       fine-grained tracking • backpressure • optimistic       │
│       output sanitization on every patch                      │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│         Transport: signed WebSocket / SSE / HTTP              │
│         message authentication • replay protection            │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│              Tiny Browser/Webview Runtime (~15KB)             │
│         CSP-strict • Trusted Types • SRI                      │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                       Build Targets                           │
│   browser  •  PWA  •  desktop (Tauri)  •  mobile (Capacitor)  │
│   code-signed binaries • notarized • SBOM • reproducible      │
└───────────────────────────────────────────────────────────────┘

  ┌────────────────────────────┐   ┌────────────────────────────┐
  │  Cross-Cutting:            │   │  Cross-Cutting:            │
  │  Observability             │   │  AI-Build Dev Surface      │
  │  • traces                  │   │  • MCP server              │
  │  • cost ledger             │   │  • llms.txt manifest       │
  │  • audit log               │   │  • schema introspection    │
  │  • metrics                 │   │  • stable error codes      │
  │  • PII redaction           │   │  • component registry      │
  │  • anomaly detection       │   │  • generative UI runtime   │
  └────────────────────────────┘   │  • hot fix loop            │
                                   │  • framework new / fix /ui │
                                   └────────────────────────────┘
```

The **AI-Build Dev Surface** is a peer to observability, not a feature inside it. Both are cross-cutting because they read from every layer. The AI-Build Dev Surface is what makes the framework writable by AI coding agents without hallucination — it's how Claude Code, Cursor, or any future agent connects to a running framework instance and learns it on the fly.

The AI Runtime Layer, the Sandbox Layer, and the Data Layer are *separate processes* in production, communicating over authenticated, capability-scoped channels. A compromise of the application layer cannot read another tenant's data, escape the sandbox, mint new tool capabilities, or tamper with the audit log.

---

## Designed for AI to build

The AI era doesn't just change what apps do — it changes who writes them. A framework optimized for this era treats AI coding agents as a primary user. That requires four things, all architectural:

### 1. A small, orthogonal API surface

**Six decorators. About fifty components. One project layout. One way to do everything.**

Every framework primitive does exactly one thing and composes with the others. There is no "old API and new API." There is no "preferred way and legacy way." There is one way. AI agents (and humans) trying to recall the right pattern always recall the same one.

The community has run this experiment many times. Frameworks with sprawling APIs (early Angular, late jQuery plugins, mid-era Webpack configs) are AI-hostile because every recall has multiple equally-plausible options and many of them are wrong. Frameworks with tight APIs (Tailwind utility classes, Rails conventions, Go's standard library) are AI-friendly because the right answer is also the only answer.

### 2. Native MCP server (the killer DX feature)

The framework ships a **Model Context Protocol** server out of the box. Claude Code, Cursor, Continue, and any other MCP-aware tool connect to a running dev server and gain:

- A live list of every component, tool, prompt, page, and state object in the project.
- The full schema for each (props, types, validators, examples).
- The framework's own component catalog with documentation.
- A `lookup_error(code)` tool that returns the canonical fix for any framework error.
- A `propose_patch(intent)` tool that returns a structured diff for a stated intent.
- A `run_eval(prompt)` tool that runs the eval suite and returns pass/fail.
- A `render_preview(component)` tool that renders a component to PNG or HTML for the agent to inspect.

This is the difference between "the AI guesses what your framework looks like" and "the AI reads what your framework actually is, right now, with your overrides applied." The MCP server is **a Phase 2 deliverable, not Phase 5.**

### 3. Self-describing everything (`llms.txt` and schema introspection)

The framework ships an `llms.txt` and `llms-full.txt` at the repo root and at the running server's `/.well-known/llms.txt` endpoint. These are the canonical, machine-readable, single-page descriptions of the entire framework — concepts, decorators, component catalog, conventions, idioms, anti-patterns. AI agents fetching one URL get a complete operating manual.

Every component, tool, prompt, and state object exposes a JSON Schema accessible via:

```python
framework.introspect(AIChat)
# returns: {"props": {...}, "events": {...}, "examples": [...]}
```

The schema flows from the same Python type hints the IDE and the runtime validator use. **One source of truth, three readers** (IDE, runtime, AI agent).

### 4. Stable error codes with AI-actionable hints

Every framework error has a stable code (`PYR-1042`), a one-line description, an explanation, a worked fix example, and a docs URL. Errors are designed to be read by AI agents:

```
PYR-1042: AIChat received unknown prop `streaming`.
  Did you mean `stream`? AIChat uses `stream=True` to enable token streaming.
  Fix:   AIChat(model=..., stream=True)
  Docs:  https://docs.framework.dev/errors/PYR-1042
```

When `framework fix` is run, it parses the traceback, extracts the error code, looks up the canonical fix from the catalog, and proposes a patch. AI agents using the framework's MCP server can do the same via `lookup_error("PYR-1042")`. **Hallucinated fixes are replaced with deterministic ones.**

### Putting it together: the AI-build loop

A typical AI-driven build session with this framework:

1. Developer (or autonomous agent) describes intent: *"a kanban board with auth, drag-and-drop, and an AI assistant that can move cards based on natural-language commands."*
2. `framework new` scaffolds the project from the description.
3. The AI coding tool (Claude Code, Cursor) connects to the running dev server's MCP endpoint and reads the component catalog, the project's existing schemas, and the conventions.
4. It writes Python that uses the right components and decorators because it can see them.
5. On error, the framework returns a stable code; the AI looks it up; the fix is deterministic.
6. The dev console shows traces; the AI reads them via the MCP server and iterates.
7. `framework eval` validates the AI's prompts; CI fails on regressions.

This loop is faster, more reliable, and more reproducible than any current AI-coding setup against a generic framework.

---

## Security as a first principle

Security is not a Phase 4 deliverable. The framework's first commit ships with a hardened transport, signed sessions, capability-scoped tools, and tenant isolation. Apps built on it inherit a strong default posture. **Insecure code requires explicit opt-out, not opt-in.**

### Threat model

In priority order:

1. **Prompt injection** (direct + indirect through RAG, tools, web pages, files).
2. **Tool-call exfiltration** — agent leaks data via a tool with network or storage access.
3. **Cross-tenant data leak** — a bug or compromise lets one tenant read another's data.
4. **Output-rendered XSS / SQLi / SSRF** — AI generates content that becomes an injection vector.
5. **Cost-based DoS** — adversary triggers expensive model calls.
6. **Session hijacking on the persistent socket** — stolen cookies, replayed events.
7. **Supply chain compromise** — malicious dependency, typosquat.
8. **Sandbox escape** — agent-executed code escapes to host.
9. **Credential theft** — secrets leak into prompts, logs, traces.
10. **Insider abuse** — operators misuse legitimate access.

### Six defense principles

**1. Zero-trust runtime.** Every layer authenticates the next. The application process holds no long-lived secrets. The sandbox refuses connections without a signed capability token. The data layer enforces tenant scoping at the query layer.

**2. Capability-scoped tools.** Tools are not "functions an agent can call" — they are *capabilities* the framework grants to a specific agent run, for a specific user, for a specific scope, for a specific time window. Inspectable, revocable, auditable.

```python
@tool(
    capability="email.send",
    scope=lambda ctx: f"user:{ctx.user.id}",
    rate_limit=Rate(10, per="hour"),
    requires_approval=True,
    network_policy=AllowList(["smtp.example.com"]),
)
async def send_email(to: str, body: str): ...
```

No ambient authority.

**3. Untrusted AI output by default.** Every byte produced by a model is treated as untrusted input. Strict text sanitization. Parameterized queries enforced. Tool arguments schema-validated. Model-generated code only ever runs in the sandbox layer. Secrets in outputs detected and redacted before traces are written.

**4. Sandboxed tool execution.** Tools that run model-generated code, browse the web, or touch the file system run in isolated sandboxes — gVisor on Linux, Firecracker microVMs for stronger isolation, WASM for lightweight cases. Network egress allowlisted per-tool. CPU, memory, wall-clock capped. The host process never executes model-generated code directly.

**5. Multi-tenant by default.** Every state object, vector embedding, prompt, trace, and log line carries a tenant tag enforced at the storage layer. Cross-tenant queries are physically impossible — the data layer rejects unscoped queries.

**6. Encrypted everywhere.** TLS 1.3 in transit. AES-256-GCM at rest. Per-tenant keys from a KMS-managed master. PII fields encrypted at the column level. Backups encrypted independently. AI traces encrypted in storage.

### AI-specific security primitives

- **Prompt-injection guards** — structural isolation of untrusted content, an injection-classifier on retrieved documents, tool-call validators, output secret scanners. Layered, not silver bullet.
- **Capability tokens for tools** — every tool call gated on a signed token from AuthZ.
- **Output sanitization on every render** — model output never reaches the DOM raw.
- **Rate and cost limiting** — every model call, tool invocation, embedding metered per-user and per-tenant. Hard budgets enforced.
- **Approval flows** — high-risk tools (`send_email`, `make_payment`, `delete_resource`, `execute_code`) require explicit user approval by default.
- **Trace and prompt redaction** — secrets and PII stripped before storage.

### Compliance posture

- **GDPR** — data residency per tenant, right-to-erasure across primary, vector, traces, backups within SLA.
- **SOC 2 readiness** — controls map to CC1–CC9, audit log + change management + access reviews built in, evidence-collection skill.
- **HIPAA-ready mode** — `framework.toml` flag enables stricter encryption, mandatory MFA, no third-party providers without BAA, redaction defaults tightened.
- **Configurable telemetry** — self-hosters can disable any external telemetry; default is opt-in usage analytics, off for content.

### Supply chain

Reproducible builds. SBOM (CycloneDX) per release. Sigstore-signed binaries and Python packages. Pinned, audited dependencies. Renovatebot + automated CVE scanning + manual review for new direct dependencies.

---

## What "AI-native" actually means

Eight primitives, designed in from day one. Each carries security as a property, not a postscript.

### 1. AI as built-in components

```python
@page("/chat")
def chat():
    return AIChat(
        model="claude-sonnet-4-6",
        system=registry["assistant_v2"],
        tools=[search_docs, create_ticket],
        accepts=["text", "image", "voice"],
        renders=["text", "image", "code", "citations"],
        stream=True,
        injection_guards=DEFAULTS,
    )
```

### 2. Streaming as a first-class transport concept

The reconciler understands token streams. Partial-JSON tool calls render structurally as they grow. Every patch passes through the output sanitizer.

### 3. Multimodal as a first-class concern

Camera, microphone, file upload, screen capture as native primitives. Uploads scanned (type, size, virus, EXIF) before reaching agents.

### 4. Durable agent execution

```python
agent = DurableAgent(
    model="claude-sonnet-4-6",
    tools=[search, browse, code_exec],
    memory=ConversationMemory(user.id),
    checkpoint=PostgresCheckpoint(),
    policy=AgentPolicy(
        max_steps=50,
        max_cost_usd=2.00,
        capabilities=["search", "browse"],
    ),
)
```

Survives disconnects, page reloads, server restarts. Encrypted, tenant-scoped checkpoints.

### 5. Human-in-the-loop primitives

```python
@tool(capability="email.send", requires_approval=True)
async def send_email(to: str, body: str):
    if not await Approval.request(
        f"Send email to {to}?",
        preview=Markdown(body),
        editable={"body": body},
    ):
        raise ToolRejected()
    return await mail.send(to=to, body=body)
```

Pauses agent server-side; no polling.

### 6. Prompts as versioned code with evals

Versioned, A/B-testable, eval-attached. **Safety evals** (jailbreak resistance, injection resistance, refusal calibration) on every prompt change in CI.

### 7. RAG and embeddings as builtins

```python
docs = VectorStore("knowledge_base", backend="pgvector", scope="tenant")
docs.index("./docs/**/*.md", classifier=InjectionClassifier())
```

Tenant-scoped. Poisoned docs flagged.

### 8. Local + cloud models with auto-routing

```python
agent = Agent(
    model=Auto(
        cloud="claude-sonnet-4-6",
        local="llama-3.2-3b",
        prefer="cloud",
        fallback_offline=True,
        require_baa=False,
    ),
    tools=[search, summarize],
)
```

---

## The reactive engine — the real hard problem

Rendering is not the hard part. **State synchronization across server/browser, sync/async, deterministic-UI/non-deterministic-AI — without trusting the boundary** is the hard part.

The runtime must solve fine-grained dependency tracking (signals, Solid/Svelte-inspired), streaming-aware reconciliation, backpressure on token streams, optimistic UI with reconciliation, multi-user state scoping, async consistency across `await` points, and authenticated patches that fail closed on tampering.

Get this right and the rest is craft. Get it wrong and the framework is a toy *or* a CVE.

---

## One codebase, every device

Four official build targets. Same Python application.

- **Browser** — `framework dev` / `framework deploy`. SSR + WebSocket. Default.
- **PWA** — `framework build pwa`. Manifest, service worker, install prompt, push, offline app-shell. CSP-strict.
- **Desktop** — `framework build desktop`. Tauri 2. 5–15 MB signed `.app` / `.exe` / `.deb` / `.AppImage`. Native menus, tray, file dialogs, deep links, biometric, keychain.
- **Mobile** — `framework build mobile`. Capacitor 6. Xcode + Android Studio projects. App attestation, certificate pinning, biometric, Secure Enclave/StrongBox, push.

### Where the server lives

- **Mode A — Cloud server (default).** Thin shell connects to hosted server.
- **Mode B — Embedded local server.** Bundles Python on-device. Fully offline. iOS via BeeWare/Briefcase.
- **Mode C — Hybrid (Phase 6+).** Cloud default, embedded fallback, sync on reconnect.

---

## Project layout (one true way)

Every project looks the same. AI agents and humans never have to relearn structure.

```
my-app/
├── framework.toml          # config (single file, declarative)
├── pyproject.toml
├── pages/                  # auto-routed: pages/users.py → /users
│   └── index.py
├── components/             # @component-decorated reusable UI
├── tools/                  # @tool-decorated agent capabilities
├── prompts/                # @prompt-decorated registered prompts
├── state/                  # State stores
├── tests/
├── public/                 # static assets
└── llms.txt                # auto-generated from your project
```

A new contributor (human or AI) reads `framework.toml`, glances at `llms.txt`, and is productive in minutes.

---

## Developer experience — the AI-built version

A real session showing how this is meant to feel:

```
$ framework new "research agent: chat UI, web search and summarize tools,
   require approval before sending emails, store conversation across sessions,
   ship to web + mobile"

✓ Project scaffolded at ./research-agent
✓ MCP server running at ws://localhost:7341/mcp
✓ Connected: Claude Code, Cursor

$ framework dev
✓ http://localhost:7340
✓ Hot reload
✓ Trace viewer at /__/traces
```

Open Claude Code in the project. It connects to the MCP endpoint, reads the project schema, and writes against it. When the developer says "add a button that exports the conversation as PDF," Claude Code:

- Looks up the `Button` component schema from the live MCP server.
- Looks up the `pdf` skill (if installed).
- Writes Python that uses the right primitives.
- The framework hot-reloads.
- If anything errors, the error code (e.g., `PYR-1042`) maps to a deterministic fix.

The developer writes intent. The agent writes code. The framework verifies. **The learning curve for the human is the five concepts above; the learning curve for the agent is one MCP connection.**

---

## What makes this different from Reflex, Solara, NiceGUI, FastHTML

These exist; some have streaming and AI helpers. The moat is five things:

1. **A signals-based reactive engine with streaming-aware, signature-verified reconciliation.** Nothing else in the Python web ecosystem does this.

2. **Durable agents, multimodal components, capability-scoped tools, approval flows, prompt registry, evals (including safety evals), cost ledger, trace replay, prompt-injection guards** — as runtime primitives.

3. **Security as a foundational design constraint.** Capability tokens, sandboxed tool execution, multi-tenant isolation by default, output sanitization on every patch, supply-chain signing.

4. **AI-buildability as a product requirement.** Six decorators. Fifty components. One layout. Native MCP server. `llms.txt`. Stable error codes with deterministic fixes. The framework is *designed to be written by AI*, not just *used to deploy AI*.

5. **One Python codebase shipping to web + PWA + desktop + mobile + offline-with-local-models, with code signing and platform secure storage, officially supported.**

The proof is one demo: a research agent with image input, voice output, durable state across reconnects, tool approvals, runtime cost capping, prompt-injection guards, multi-tenant deployment, and an audit log — running on a phone with a local model when offline, **scaffolded by an AI agent in under five minutes via the MCP server**. That demo cannot be built cleanly in any current Python framework.

---

## Build roadmap

Security primitives ship in Phase 1. The MCP server and llms.txt ship in Phase 2. Neither is bolted on later.

### Phase 1 — Foundations + security spine (Month 1)

- Component system, reconciler, transport, hot reload.
- Signed-message WebSocket transport. Authenticated patches.
- Session primitives (signed, rotating, device-bound).
- CSP-strict, Trusted-Types-enforced JS runtime.
- One end-to-end example app.
- **Stable error code catalog seeded.**
- **Schema introspection API for components.**

### Phase 2 — Reactivity, routing, AuthN/AuthZ, AI-Build Surface (Month 2)

- Signals-based reactive state.
- File-based routing.
- Forms + validation.
- SSR + hydration.
- Optimistic UI.
- AuthN: OAuth, passkeys, magic link.
- AuthZ: RBAC + capability tokens.
- Audit log skeleton.
- **MCP server (`framework mcp`) — exposes components, schemas, errors, eval runner.**
- **`llms.txt` generator — committed at build time + served at `/.well-known/llms.txt`.**
- **`framework fix` — deterministic patch from error code.**

### Phase 3 — AI runtime + AI security (Month 3)

- Model gateway (Anthropic, OpenAI, Ollama, MLX).
- `AIChat`, `AICompletion`, `AIForm`, multimodal I/O.
- Streaming-aware reconciler.
- `DurableAgent` with Postgres checkpoint.
- `Approval` primitive.
- Prompt registry + `framework eval` + safety evals.
- Vector store (pgvector default), tenant-scoped.
- Prompt-injection guards (structural isolation, classifier, validator, scanner).
- Capability-scoped tool runtime.
- Sandbox for tool execution (gVisor first; WASM lightweight path).
- Cost ledger with hard caps.
- PII/secret redactor for traces and logs.
- Trace viewer in dev console.
- **`framework new "<intent>"` — AI scaffolder that uses the MCP server's schema.**

### Phase 4 — Cross-platform & production (Months 4–6)

- `framework build pwa | desktop | mobile`.
- Tauri 2 + Capacitor 6 integration.
- Native bridges + `SecureStore`.
- Code signing + notarization in build pipeline.
- SBOM + Sigstore signing for releases.
- Background jobs and scheduled tasks.
- Edge rendering and regional deploys.
- AI-assisted scaffolding extended (`framework ui`, `framework refactor`).
- Documentation site, starter templates.
- HIPAA-ready mode flag.
- SOC 2 evidence-collection skill.

### Phase 5 — Ecosystem (Month 6+)

- Plugin system, component library, agent recipes.
- Stripe / auth / email / vector DB / observability integrations.
- Embedded-server Mode B for offline desktop and mobile.
- Penetration test + third-party security audit before public 1.0.

The Phase 3 milestone: *one developer (or one agent) ships a secure, multi-tenant AI app to production in a weekend.* End of Phase 4: *that app installs on a phone, works offline, and passes a baseline security review.*

---

## Tech stack — committed decisions

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.12+ | Async improvements, generics, faster interpreter |
| Async runtime | `asyncio` | Broad ecosystem; AI SDKs assume it |
| HTTP / WebSocket | Starlette + Uvicorn | Battle-tested, ASGI-native |
| Reactive engine | Custom signals (Solid/Svelte-inspired) | We own the core |
| Browser runtime | TypeScript, no framework, esbuild | <20 KB, CSP-strict, Trusted Types |
| AI providers | Anthropic SDK primary, OpenAI, Ollama, MLX | Provider-agnostic gateway |
| Local models | Ollama, MLX, llama.cpp | Cross-platform |
| Vector store | pgvector default, Chroma, Turbopuffer | Pluggable |
| Durable execution | Custom (Postgres-backed) | Lightweight; no Temporal dep |
| Database | SQLite (dev/embedded), Postgres (prod) | Standard |
| AuthN / AuthZ | Authlib, WebAuthn, custom RBAC + capability tokens | Standards-based |
| Crypto | `cryptography` (libsodium primitives), AES-256-GCM, Argon2id | No homegrown crypto |
| Secrets | AWS KMS / GCP KMS / Azure KV / Vault adapters | Never in code |
| Sandbox | gVisor (default), Firecracker (high-isolation), WASM (light) | Defense in depth |
| Audit log | Postgres + hash-chained entries → write-once S3 | Tamper-evident |
| PII / secret redaction | Microsoft Presidio + custom rules | Mature, extensible |
| Prompt-injection classifier | Distilled small model + heuristics | Cheap, on-path |
| **AI-Build Surface** | **MCP (Model Context Protocol) server, llms.txt** | **Standards-based agent integration** |
| **Schema source** | **Pydantic v2 — one source of truth for IDE, runtime, MCP** | **Single source of truth** |
| **Error catalog** | **Versioned YAML, embedded in package** | **Deterministic, AI-readable** |
| Desktop wrapper | Tauri 2 | 5–15 MB, system webview |
| Mobile wrapper | Capacitor 6 | Mature stores ecosystem |
| Mobile Python (Mode B) | BeeWare/Briefcase | Only credible iOS path |
| Build CLI | Python (`framework`) | Calls esbuild, Tauri CLI, Capacitor CLI |
| Build signing | Sigstore (cosign), Apple notarization, Microsoft Authenticode | Supply chain integrity |
| SBOM | Syft → CycloneDX | Standard format |
| Testing | `pytest` + Playwright + `bandit` + `semgrep` + `trivy` | Standard + security |
| Trace storage | Postgres + S3, encrypted | Cost-effective, compliant |

---

## Repository structure

```
framework/
├── pyproject.toml
├── SECURITY.md                    # threat model + reporting
├── llms.txt                       # canonical machine-readable framework spec
├── llms-full.txt                  # full reference (ships in package)
├── docs/
├── packages/
│   ├── framework-core/            # signals, reconciler, scheduler, transport
│   ├── framework-ai/              # gateway, agents, prompts, RAG, traces
│   ├── framework-security/        # auth, capabilities, secrets, audit, sanitizers
│   ├── framework-sandbox/         # gVisor / Firecracker / WASM bridges
│   ├── framework-mcp/             # MCP server, schema introspection, error catalog
│   ├── framework-runtime-js/      # ~15KB CSP-strict browser runtime
│   ├── framework-cli/             # `framework` command
│   ├── framework-desktop/         # Tauri integration + native bridges + signing
│   ├── framework-mobile/          # Capacitor integration + native bridges + attestation
│   └── framework-devtools/        # trace viewer, hot reload, scaffolder
├── examples/
│   ├── counter/
│   ├── chat/
│   ├── research-agent/            # the moat demo
│   └── kanban/
├── tests/
├── benchmarks/
└── security/
    ├── threat-model.md
    ├── soc2-controls.md
    ├── hipaa-mode.md
    └── audit-runbooks/
```

`framework-mcp` is its own first-class package. `llms.txt` lives at the repo root, generated from the same Pydantic schemas used by the IDE and runtime.

---

## First sprint — Week 1 deliverables

The "is the architecture sound?" checkpoint.

1. **`framework-core/reactive`** — `Signal`, `Effect`, `Computed` with dependency tracking and microtask-batched scheduler. Diamond-dependency tests pass.
2. **`framework-runtime-js`** — TypeScript module: opens WebSocket, applies JSON-patch protocol to DOM, forwards events. <20 KB minified. CSP-strict.
3. **`framework-core/transport`** — Starlette/Uvicorn server: WebSocket connections, per-connection session state, HMAC-signed patches, replay-resistant message IDs.
4. **`framework-core/components`** — `Text`, `Button`, `VStack`, `HStack`, `Input`. Output of `Text` goes through the sanitizer before patching. Every component has a Pydantic schema.
5. **`framework-security/session`** — Signed, rotating session tokens with device binding. Cookies `HttpOnly` / `Secure` / `SameSite=Strict`.
6. **`framework-mcp/skeleton`** — MCP server stub that exposes `list_components()`, `get_schema(name)`, `lookup_error(code)`. Even if minimal, prove the surface from day one.
7. **`examples/counter`** — End-to-end. Signed transport. CSP active. Counter increments. Patches signed and verified. Schema introspectable via MCP.

Pass this checkpoint, the rest is execution.

---

## Strategic positioning

**Don't say:** "Python replacing JavaScript."

**Do say:** "The full-stack Python framework for the AI era — one codebase, every device, **secure by default, AI builds it for you**."

**Audience priority:**

1. AI engineers shipping agentic products who currently glue together LangChain + FastAPI + Streamlit + custom auth + half a dozen SaaS for guardrails.
2. Backend Python teams in regulated industries (fintech, healthtech, govtech) needing security + compliance in the box.
3. Solo founders building AI products needing web + mobile from day one, who can't afford a separate security or frontend engineer.
4. Teams already pairing with AI coding agents (Claude Code, Cursor, Copilot) who want a framework where the AI doesn't hallucinate the API.
5. Data scientists shipping internal tools touching sensitive data.

Security-first **plus** AI-native **plus** AI-buildable is a rare triple. Most AI frameworks are research-grade; most security-grade frameworks are pre-AI; most "AI-friendly" frameworks ignore security. We sit in the gap, on purpose.

---

## Risks & honest tradeoffs

- **Server-driven UI requires a connection.** Mitigation: graceful degradation; embedded-server Mode B.
- **The reactive engine is research disguised as engineering.** Mitigation: study existing systems, prototype this first.
- **AI providers shift fast.** Mitigation: provider-agnostic gateway from day one.
- **"Yet another Python web framework."** Mitigation: the moat is the reactive engine + AI runtime + security spine + AI-build surface + cross-platform story. Ship the demo.
- **Persistent connections cost more than stateless HTTP.** Mitigation: known, solved (Phoenix runs millions of sockets per node). Document.
- **iOS Python embedding is hard.** Mitigation: defer Mode B on iOS to Phase 5; rely on Mode A for v1.
- **Security adds friction to DX.** Mitigation: secure defaults that don't get in the way; one-flag HIPAA mode for highest-friction case.
- **Capability-token system is complex.** Mitigation: ship sensible defaults; developers customize only when scoping tighter.
- **Sandbox layer adds operational complexity.** Mitigation: gVisor in managed runtime; WASM for light path.
- **Prompt-injection defenses are imperfect.** Mitigation: layered defenses, documented as defense-in-depth.
- **MCP is young as a standard.** Mitigation: it's stabilizing fast and Anthropic + Cursor + Continue + others have committed; we'd rather be early on the right standard than late on a wrong one. Adapter pattern lets us swap implementations.
- **A small API surface limits power-user flexibility.** Mitigation: explicit "advanced" escape hatches (raw transport, custom reconciler hooks, raw model client) — opt-in, well-marked, AI agents are taught to avoid them by default.

---

## What success looks like at 12 months

- An AI-native app — chat, agent, RAG, streaming, multimodal, offline-capable — under 100 lines of Python, running end-to-end, shipping to web + desktop + mobile from one codebase, passing a baseline penetration test, **scaffolded by an AI coding agent in under five minutes via the MCP server**.
- A developer with no JavaScript, no security, and no React shipping a real product to real users on the App Store, with auth, audit, encryption, and prompt-injection defense all default-on.
- An AI coding agent (Claude Code, Cursor) authoring a non-trivial feature against the framework with **zero hallucinated APIs**, because the schema, error catalog, and llms.txt are live and authoritative.
- A trace viewer so good for debugging AI apps that AI engineers adopt the framework even if they were never going to build a web app.
- A starter ecosystem: 10 templates, 50 components, 5 agents, all security-reviewed, all introspectable.
- A passed third-party security audit and a published threat model.
- Enough early adopters that the next wave hears about it from someone — or some agent — they trust.

---

## The opportunity

Python won AI. Frontend complexity is collapsing. AI changed what an "app" is. AI is changing who writes apps. Cross-platform shipping is still a tax. Security is becoming an existential requirement.

Build the reactive engine. Make AI primitives feel inevitable. Make security the path of least resistance. Make the API small enough that an AI agent never has to guess. Ship the demo that makes someone say *"wait, that's it?"* — and that runs on their phone, their laptop, and their browser, securely, **and that an AI scaffolded for them while they were still typing**.

That is the framework. Time to build it.
