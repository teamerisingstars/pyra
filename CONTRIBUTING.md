# Contributing to Pyra

Thanks for thinking about contributing. Pyra is early — the architecture is real, the community is small, and your first PR can land in a day if it's well-scoped.

## Before you start

1. **Read the manifesto.** `../manifesto.md` is the north star. Decisions that contradict it need to argue with it explicitly.
2. **Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).** It explains how the code is organized and what the boundaries are.
3. **Read [`docs/ROADMAP.md`](docs/ROADMAP.md).** Pick something marked `good-first-issue` if it's your first PR. Open an issue if you want to claim it.

## Dev setup

```bash
git clone <your fork>
cd pyra
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

Python 3.10+ works locally; 3.12+ is the production target. The CI matrix runs both.

## The dev loop

- **Run the counter example:** `cd examples/counter && python main.py` → http://127.0.0.1:7340
- **Run tests:** `pytest`
- **Run a single test file:** `pytest tests/test_reconciler.py -v`
- **Test against multiple Python versions:** install [tox](https://tox.wiki) or just use `python3.10` and `python3.12` directly.

## What we care about

In rough priority order:

1. **Architectural integrity.** Does this fit the manifesto? Does it stay inside the layer it belongs to? (See `docs/ARCHITECTURE.md`.)
2. **Security defaults.** New features start secure. If a feature has an insecure mode, it must be opt-in and clearly marked.
3. **Test coverage.** New behavior needs tests. The reactive engine, reconciler, transport, and state primitives have ~100% behavioral coverage; new modules should match.
4. **API minimalism.** Six decorators, ~50 components, one project layout, one way to do everything. New public API requires explicit justification.
5. **Performance.** The reactive engine and reconciler are hot paths. PRs touching them should include a microbenchmark.

## Style

- **Python:** PEP 8, 4-space indent, 100-char lines, `from __future__ import annotations` at the top of every module.
- **Type hints everywhere.** They power IDE tooling, runtime validation, and the MCP schema introspection. No `Any` without comment.
- **No homegrown crypto.** Use `cryptography`. Use `hmac.compare_digest` for any signature comparison.
- **No `innerHTML`** in the JS runtime. Ever. Use `textContent` and `createElement`.
- **No raw model output to the DOM.** Everything goes through the output sanitizer.
- **Imports:** stdlib, third-party, local — separated by a blank line.
- **Tests:** mirror the source layout (`src/pyra/X.py` → `tests/test_X.py`).

## PR process

1. **Open an issue first** for anything non-trivial. It saves rework.
2. **One PR = one logical change.** Refactors and feature additions go in separate PRs.
3. **Write a real PR description.** What changed, why, what's tested, what's the risk, what's out of scope.
4. **Link the issue.** `Closes #123`.
5. **CI must be green.** No exceptions.
6. **Get one approving review.** Two for security-sensitive changes (anything in `framework-security`, `framework-sandbox`, or the transport layer).

## Commit messages

Conventional Commits. Examples:

```
feat(reactive): add Computed.subscribe for manual disposal
fix(transport): reject HMAC with timing-safe compare
docs: add example for streaming AIChat
test(reconciler): cover handler swap on same node
```

Allowed types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`, `security`.

## Security-sensitive changes

If your change touches:

- The transport layer (`src/pyra/transport.py`)
- The reconciler's output sanitization
- Any future code in `framework-security`, `framework-sandbox`, or the AI guards

…flag the PR with the `security` label. It needs a second reviewer and a brief threat-model note in the description.

For vulnerability reports, see [`SECURITY.md`](SECURITY.md). **Don't open a public issue.**

## Questions

Until we have a community channel, use a GitHub Discussion or open an issue tagged `question`. We try to respond within 48 hours.
