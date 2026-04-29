# Fullstack Task Board

This example demonstrates Pyra's complete Phase 2 feature set: multi-page routing (`/`, `/login`, `/dashboard`, `/about`), reactive `State()` signals, magic-link authentication via `AuthManager`, keyed list rendering with `Element(key=...)` for efficient reconciliation, server-side rendering (SSR), form validation with `FormField`, and the full component library (`Card`, `Badge`, `Image`, `Heading`, `Link`, `Spinner`).

## How to run

```bash
cd examples/fullstack
python main.py
```

Open http://127.0.0.1:7340

## How to log in

1. Navigate to `/login` and enter any email address, then click **Send magic link**.
2. The magic-link URL is printed to the console **and** displayed in the UI (dev mode).
3. Click the link (or copy it into the browser) to be redirected to `/dashboard`.

## What to do

- On the dashboard, type a task in the input box and click **Add task**.
- Click **Mark done** to toggle a task's status (the Badge updates from "pending" to "done").
- Click **Delete** to remove a task from the list.
- Each task card is wrapped in a keyed `Element` so Pyra's reconciler moves/patches nodes correctly instead of rebuilding the whole list.

## Deploy

See [docs/DEPLOYMENT.md](../../docs/DEPLOYMENT.md) for full instructions covering Docker, Fly.io, Render, and reverse-proxy setups.

Quick start with Docker:

```bash
docker build -t my-app . && docker run -p 7340:7340 -e PYRA_SECRET_KEY=... my-app
```
