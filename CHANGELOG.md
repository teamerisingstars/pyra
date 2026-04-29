# Changelog

All notable changes to Pyra are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/) (we're pre-1.0 — minor bumps may break).

## [Unreleased]

## [0.0.3] - 2026-04-29

### Added
- Multi-page routing — `@page` now supports any path; path passed via `hello` WebSocket message
- Keyed list reconciliation — `insert_node`/`remove_node` ops; `key` prop on `Element`
- Server-side rendering (SSR) on initial GET — pages render to HTML before WebSocket connects
- Hot reload — `app.run(reload=True)` via uvicorn auto-reload
- Components: `Badge`, `Card`, `Image`, `Heading`, `Link`, `Spinner`, `FormField`, `Select`, `Checkbox`
- `key` prop on `Element` for keyed reconciliation
- `forms.py` — `validate()` and `use_form()` with Pydantic v2 backing
- `auth.py` — `AuthManager` with magic-link tokens, signed session cookies, `require_auth` decorator, `App.use_auth()`
- `config.py` — `Config` dataclass reading `PYRA_*` env vars; warns if `PYRA_SECRET_KEY` unset
- `ssr.py` — `render_to_html()` for SSR tree → HTML conversion
- `db.py` — `PersistentState` KV store backed by SQLite (default) or Postgres; `get_connection()` async context manager
- `App.mount_static(path, directory)` — serves static files via Starlette `StaticFiles`
- `App.set_error_page(404|500, renderer)` — custom error pages with SSR support; default 404/500 HTML fallbacks
- `App.use_auth(auth_manager)` — registers `/auth/verify` endpoint, HTTP-layer auth checks, WebSocket session injection
- `cli.py` — `pyra new <name>`, `pyra dev`, `pyra version` commands
- Deployment: `Dockerfile`, `.dockerignore`, `fly.toml`, `render.yaml`, `docs/DEPLOYMENT.md`
- Examples: `todo-app`, `fullstack` (task board with auth, multi-page, forms, keyed lists)
- Docs: `docs/TUTORIAL.md`, `docs/PATCH_PROTOCOL.md`
- Benchmarks: `benchmarks/bench_reconciler.py`

### Changed
- `_accepts_arg()` now uses `inspect.signature(fn).bind(None)` — correctly handles `lambda evt=None:` and `*args` handlers
- `render.py` — `key` field included in serialized element output when set; `_SAFE_PROP_KEYS` extended with `rel`, `selected`
- Browser runtime — handles `insert_node`, `remove_node`, `redirect` ops; spinner CSS keyframe added

### Security
- Session cookies set `httponly=True`, `samesite="lax"`
- Auth tokens are one-time-use with configurable TTL
- HMAC-SHA256 signing on all session values
- HTTP-layer auth redirect prevents SSR of protected pages for unauthenticated users

## [0.0.2] - 2026-04-29

### Added
- Diff-based reconciler (`src/pyra/reconciler.py`) with patch ops: `init`, `replace_text`, `set_attr`, `remove_attr`, `set_handler`, `remove_handler`, `replace_node`.
- Per-session `State` (`src/pyra/state.py`) — hook-style, ContextVar-driven. Two browser tabs see independent state.
- E2E test verifying two simultaneous WebSocket connections have independent counters.
- 11 new tests (10 reconciler + 5 state, minus replaced E2E logic).

### Changed
- Server → client protocol changed from `{"type": "render", "tree": ...}` to `{"type": "patch", "ops": [...]}`. **Breaking** for anyone who built on the v0.0.1 protocol.
- Browser runtime upgraded to apply patch ops (DOM `Map<id, Node>`, listener `WeakMap`).
- Text nodes now carry stable IDs for fine-grained diffing.
- Counter example updated to use per-session state.
- `State` is now a function (returns a Signal); was previously a class alias.

### Security
- All sanitization defaults preserved. `html.escape` server-side and `textContent` client-side enforced.

## [0.0.1] - 2026-04-29

### Added
- Reactive primitives: `Signal`, `Computed`, `Effect`, `batch`.
- Signed WebSocket transport: HMAC-SHA256, monotonic `msg_id`, replay rejection.
- Component primitives: `Text`, `Button`, `VStack`, `HStack`, `Input`.
- `App` class and `@page` decorator.
- Working counter example end-to-end.
- 17 tests (reactive, transport, E2E).
- MIT license.
