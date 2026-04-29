# Security Policy

Pyra treats security as a foundational design constraint, not a feature. This document covers (1) how to report a vulnerability, (2) the threat model we're designing against, and (3) what secure-by-default actually means here.

## Reporting a vulnerability

**Do not open a public issue.** Instead, email **security@pyra.dev** (placeholder until we have the domain — for now, open a private GitHub Security Advisory on the repo).

Include:
- A description of the vulnerability and its impact.
- Steps to reproduce, or a proof-of-concept.
- The version (or commit SHA) you tested against.
- Your name/handle if you'd like credit.

We commit to:
- An acknowledgment within **72 hours**.
- A triage decision within **7 days**.
- A fix or mitigation within **30 days** for critical issues, **90 days** otherwise.
- Public credit (if you want it) in the release notes and a `SECURITY-ADVISORIES.md` log.

## Scope

In scope:
- The Pyra framework itself (this repo).
- Default configurations and starter templates.
- Documentation that, if followed, leads to insecure deployments.

Out of scope:
- Third-party dependencies (report upstream).
- User application code built on Pyra (unless caused by a framework bug).
- Issues requiring physical access or already-compromised credentials.

## Threat model (priority order)

1. **Prompt injection** (direct + indirect via RAG, tools, web pages, files).
2. **Tool-call exfiltration** — agent leaks data via a tool with network or storage access.
3. **Cross-tenant data leak** — bug or compromise lets one tenant read another's data.
4. **Output-rendered XSS / SQLi / SSRF** — AI-generated content becomes an injection vector.
5. **Cost-based DoS** — adversary triggers expensive model calls.
6. **Session hijacking on the persistent socket** — stolen cookies, replayed events.
7. **Supply chain compromise** — malicious dependency, typosquat.
8. **Sandbox escape** — agent-executed code escapes to host.
9. **Credential theft** — secrets leak into prompts, logs, traces.
10. **Insider abuse** — operators misuse legitimate access.

## Defense principles

The architecture is built around six principles. New code that violates any of these will be rejected at review.

1. **Zero-trust runtime.** Every layer authenticates the next.
2. **Capability-scoped tools.** No ambient authority. Tools require explicit, signed, time-bound capability tokens.
3. **Untrusted AI output by default.** Every byte from a model is treated as hostile input.
4. **Sandboxed tool execution.** Tools that run model-generated code, browse, or touch the filesystem run in isolation.
5. **Multi-tenant by default.** Every state object, embedding, prompt, trace, log line carries a tenant tag enforced at storage.
6. **Encrypted everywhere.** TLS 1.3 in transit. AES-256-GCM at rest. Per-tenant keys from KMS.

## Current security posture (v0.0.2)

What's already in:
- **HMAC-SHA256 signed transport** with monotonic `msg_id` (replay-resistant). 6 tests.
- **Output sanitization** — `html.escape` server-side, `textContent` client-side. No `innerHTML` ever.
- **No homegrown crypto** — uses `cryptography` library and `hmac.compare_digest`.
- **Prop allowlist** in render — only safe HTML attributes pass through.

What's still pending (see `docs/ROADMAP.md`):
- Per-session client signing keys (currently `client-unsigned-v002` placeholder).
- AuthN (OAuth, passkeys, magic link).
- AuthZ (RBAC, capability tokens).
- Tenant scoping at the data layer.
- Sandboxed tool execution.
- AI-specific guards (injection classifier, output secret scanner).
- Code signing + SBOM + Sigstore for releases.

**Pyra is not production-ready for sensitive workloads at v0.0.x.** It is, however, designed so that production-readiness is additive — no security primitive will require an architectural rewrite.

## Secure coding rules for contributors

- **No `innerHTML`** in JS. Ever.
- **No raw model output to the DOM.** Pipe through `render._safe_props` and the output sanitizer.
- **No homegrown crypto.** Use `cryptography`, `hmac.compare_digest`, `secrets`.
- **No secrets in source.** Use the (forthcoming) KMS adapter. Use environment variables for dev only.
- **No new ambient authorities.** New side-effects need a capability token.
- **No `eval`, `exec`, `pickle.loads` on untrusted input.** No exceptions.
- **Every PR to `transport.py`, `render.py` (sanitization), `state.py` (scope), or future security packages requires two reviewers.**

## Coordinated disclosure

We follow [coordinated disclosure](https://en.wikipedia.org/wiki/Coordinated_vulnerability_disclosure). Critical issues get private patches first, public disclosure after a reasonable embargo (typically 30 days from fix availability, longer for ecosystem-wide impact).
