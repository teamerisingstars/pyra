## Summary

<!-- One-paragraph description: what changed, why. -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor (no behavior change)
- [ ] Documentation
- [ ] Test only
- [ ] Security
- [ ] Breaking change

## Tests

- [ ] Unit tests added/updated
- [ ] E2E test added/updated (for protocol or transport changes)
- [ ] All tests pass locally (`pytest`)

## Architecture

- [ ] Stays within the layer it touches (see `docs/ARCHITECTURE.md`)
- [ ] No new public API, OR new API justified in this PR description
- [ ] No `innerHTML`, no homegrown crypto, no `eval`/`pickle.loads` on untrusted input

## Security review

<!-- Required if touching transport.py, render.py sanitization, state.py scope, or any framework-security/sandbox code. -->

- [ ] Threat model implications considered (see SECURITY.md)
- [ ] Two reviewers for security-sensitive changes

## Closes

<!-- e.g. Closes #123 -->

## Out of scope

<!-- What this PR deliberately doesn't do, that someone might expect it to. -->
