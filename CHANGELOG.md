# Changelog

All notable changes to Pyra are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/) (we're pre-1.0 — minor bumps may break).

## [Unreleased]

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
