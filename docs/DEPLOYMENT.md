# Deployment Guide

## Prerequisites

- Python 3.12+
- A `main.py` that exposes a `app` object (a Pyra `App` instance)
- For Docker: Docker 24+ installed
- For Fly.io: [`flyctl`](https://fly.io/docs/hands-on/install-flyctl/) CLI installed and authenticated
- For Render: A GitHub/GitLab repository connected to your Render account

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `PYRA_SECRET_KEY` | Secret key for signing sessions and tokens. Use a long random string in production. | Yes |
| `PYRA_DEBUG` | Enable debug mode (`true`/`false`). Must be `false` in production. | No (default: `false`) |
| `PYRA_HOST` | Host address the server binds to. | No (default: `127.0.0.1`) |
| `PYRA_PORT` | Port the server listens on. | No (default: `7340`) |
| `PYRA_DB_URL` | Database connection URL (e.g. `postgresql://user:pass@host/db`). | No |
| `PYRA_ALLOWED_HOSTS` | Comma-separated list of allowed hostnames for the `Host` header check. | No |

---

## Docker

Build the image:

```bash
docker build -t my-pyra-app .
```

Run the container:

```bash
docker run -p 7340:7340 \
  -e PYRA_SECRET_KEY=your-secret-here \
  -e PYRA_DEBUG=false \
  my-pyra-app
```

To pass additional environment variables, add more `-e KEY=value` flags.

---

## Fly.io

1. Initialize the app (first deploy only):

   ```bash
   fly launch
   ```

   When prompted, decline to overwrite `fly.toml` if it already exists.

2. Set the secret key:

   ```bash
   fly secrets set PYRA_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
   ```

3. Deploy:

   ```bash
   fly deploy
   ```

The app will be available at `https://your-pyra-app.fly.dev`.

---

## Render

1. Push your repository to GitHub or GitLab.
2. In the Render dashboard, click **New > Web Service** and connect your repository.
3. Render will detect `render.yaml` automatically and pre-fill the service settings.
4. In the **Environment** tab, manually set `PYRA_SECRET_KEY` to a strong random value (do not rely on `generateValue` for this in production; set it explicitly so you control it).
5. Click **Deploy**.

The service URL is shown in the Render dashboard after the first successful deploy.

---

## Behind a Reverse Proxy (nginx / Caddy)

When running behind a reverse proxy that terminates TLS, pass `--forwarded-allow-ips` to uvicorn so it trusts the `X-Forwarded-For` and `X-Forwarded-Proto` headers:

```bash
python -m uvicorn main:app._starlette --host 0.0.0.0 --port 7340 --forwarded-allow-ips "*"
```

For nginx, a minimal proxy configuration looks like:

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass         http://127.0.0.1:7340;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

Caddy handles HTTPS and headers automatically; a one-line `reverse_proxy localhost:7340` in your `Caddyfile` is sufficient.

---

## Production Checklist

- Set `PYRA_SECRET_KEY` to a strong, unique random value (at least 32 bytes of entropy).
- Serve the application over HTTPS only; never expose the Pyra port directly on the public internet.
- Set `PYRA_DEBUG=false`; debug mode may expose stack traces and internal state to users.
- Use a persistent external database (e.g. PostgreSQL via `PYRA_DB_URL`) rather than relying on in-memory state, which is lost on every restart.
- Restrict `PYRA_ALLOWED_HOSTS` to your actual domain(s) to prevent host-header injection.
- Review uvicorn worker settings (`--workers`, `--worker-class`) for your expected traffic load.
