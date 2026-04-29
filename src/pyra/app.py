"""App and @page - the user-facing surface.

Usage:
    from pyra import App, page, State, VStack, Text, Button

    @page("/")
    def home():
        count = State(0)
        return VStack(
            Text(f"Count: {count.value}"),
            Button("Increment", on_click=lambda: count.update(lambda c: c + 1)),
        )

    app = App()

    if __name__ == "__main__":
        app.run()
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Callable

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from pyra import render as render_module
from pyra.components import Component
from pyra.reactive import Effect
from pyra.reconciler import diff
from pyra.render import render_tree
from pyra.state import SessionState, _pop_session, _push_session
from pyra.transport import Session, new_session, sign_outbound

# Global page registry. Supports multiple registered paths.
_PAGES: dict[str, Callable[[], Component]] = {}


def page(path: str) -> Callable[[Callable[[], Component]], Callable[[], Component]]:
    """Register a function as the renderer for a route."""

    def decorator(fn: Callable[[], Component]) -> Callable[[], Component]:
        _PAGES[path] = fn
        return fn

    return decorator


_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Pyra</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 2rem; color: #111; }
    button { padding: 0.5rem 1rem; border-radius: 6px; border: 1px solid #ccc; background: #fafafa; cursor: pointer; }
    button:hover { background: #f0f0f0; }
    input { padding: 0.4rem 0.6rem; border-radius: 6px; border: 1px solid #ccc; font-size: 1rem; }
    @keyframes pyra-spin {
      to { transform: rotate(360deg); }
    }
  </style>
</head>
<body>
  <div id="pyra-root"><div style="opacity:0.5">Connecting...</div></div>
  <script type="module" src="/__pyra__/runtime.js"></script>
</body>
</html>
"""


_RUNTIME_JS = r"""
// Pyra browser runtime - v0.0.2
// Connects to /__pyra__/ws, applies signed patch ops, forwards events.

(() => {
  const root = document.getElementById("pyra-root");
  const wsProto = location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(`${wsProto}//${location.host}/__pyra__/ws`);

  const idMap = new Map();
  const listeners = new WeakMap();

  let lastMsgId = 0;
  let sessionMsgId = 0;

  const decoder = document.createElement("textarea");
  function decodeText(s) { decoder.innerHTML = s; return decoder.value; }

  function attachHandler(el, event, handlerId) {
    let map = listeners.get(el);
    if (!map) { map = {}; listeners.set(el, map); }
    if (map[event]) el.removeEventListener(event, map[event]);
    const fn = (ev) => {
      const data = {};
      if (event === "input" || event === "change") data.value = ev.target.value;
      send({type: "event", handler_id: handlerId, data});
    };
    map[event] = fn;
    el.addEventListener(event, fn);
  }

  function detachHandler(el, event) {
    const map = listeners.get(el);
    if (!map || !map[event]) return;
    el.removeEventListener(event, map[event]);
    delete map[event];
  }

  function setProp(el, key, value) {
    if (key === "value" && (el.tagName === "INPUT" || el.tagName === "TEXTAREA")) {
      el.value = value;
    } else {
      el.setAttribute(key, value);
    }
  }

  function buildNode(node) {
    if (node.type === "text") {
      const t = document.createTextNode(decodeText(node.value));
      idMap.set(node.id, t);
      return t;
    }
    if (node.type === "element") {
      const el = document.createElement(node.tag);
      el.dataset.pyraId = node.id;
      idMap.set(node.id, el);
      for (const [k, v] of Object.entries(node.props || {})) setProp(el, k, v);
      for (const [event, hid] of Object.entries(node.handlers || {})) {
        attachHandler(el, event, hid);
      }
      for (const c of node.children || []) el.appendChild(buildNode(c));
      return el;
    }
    return document.createTextNode("");
  }

  function unindexSubtree(domNode) {
    if (domNode.dataset && domNode.dataset.pyraId) idMap.delete(domNode.dataset.pyraId);
    if (domNode.childNodes) {
      for (const c of domNode.childNodes) unindexSubtree(c);
    }
  }

  function applyOps(ops) {
    for (const op of ops) {
      if (op.op === "init") {
        root.innerHTML = "";
        idMap.clear();
        const el = buildNode(op.tree);
        root.appendChild(el);
      } else if (op.op === "replace_text") {
        const t = idMap.get(op.id);
        if (t) t.textContent = decodeText(op.value);
      } else if (op.op === "set_attr") {
        const el = idMap.get(op.id);
        if (el && el.setAttribute) setProp(el, op.key, op.value);
      } else if (op.op === "remove_attr") {
        const el = idMap.get(op.id);
        if (el && el.removeAttribute) el.removeAttribute(op.key);
      } else if (op.op === "set_handler") {
        const el = idMap.get(op.id);
        if (el && el.addEventListener) attachHandler(el, op.event, op.handler_id);
      } else if (op.op === "remove_handler") {
        const el = idMap.get(op.id);
        if (el && el.removeEventListener) detachHandler(el, op.event);
      } else if (op.op === "replace_node") {
        const old = idMap.get(op.id);
        if (old) {
          unindexSubtree(old);
          const fresh = buildNode(op.node);
          old.replaceWith(fresh);
        }
      } else if (op.op === "insert_node") {
        const parent = idMap.get(op.parent_id);
        if (parent) {
          const newNode = buildNode(op.node);
          const ref = parent.childNodes[op.index] || null;
          parent.insertBefore(newNode, ref);
        }
      } else if (op.op === "remove_node") {
        const el = idMap.get(op.id);
        if (el) {
          unindexSubtree(el);
          el.parentNode && el.parentNode.removeChild(el);
        }
      }
    }
  }

  function send(payload) {
    sessionMsgId += 1;
    ws.send(JSON.stringify({
      msg_id: sessionMsgId,
      payload,
      sig: "client-unsigned-v002"
    }));
  }

  ws.addEventListener("open", () => { send({type: "hello", path: window.location.pathname}); });

  ws.addEventListener("message", (evt) => {
    let msg;
    try { msg = JSON.parse(evt.data); } catch { return; }
    if (typeof msg.msg_id !== "number" || msg.msg_id <= lastMsgId) return;
    lastMsgId = msg.msg_id;
    const p = msg.payload;
    if (!p || typeof p !== "object") return;
    if (p.type === "patch" && Array.isArray(p.ops)) applyOps(p.ops);
    else if (p.type === "redirect" && typeof p.url === "string") {
      window.location.href = p.url;
    }
  });

  ws.addEventListener("close", () => {
    root.innerHTML = '<div style="opacity:0.5">Disconnected. Reload to reconnect.</div>';
  });
})();
"""


_404_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>404 — Not Found</title>
<style>body{font-family:-apple-system,sans-serif;display:flex;align-items:center;
justify-content:center;min-height:100vh;margin:0;background:#f9fafb;}
.box{text-align:center;padding:2rem;}h1{font-size:2rem;color:#111;}
p{color:#6b7280;}a{color:#6366f1;}</style></head>
<body><div class="box"><h1>404</h1><p>Page not found.</p>
<a href="/">← Go home</a></div></body></html>"""

_500_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>500 — Server Error</title>
<style>body{font-family:-apple-system,sans-serif;display:flex;align-items:center;
justify-content:center;min-height:100vh;margin:0;background:#f9fafb;}
.box{text-align:center;padding:2rem;}h1{font-size:2rem;color:#111;}
p{color:#6b7280;}a{color:#6366f1;}</style></head>
<body><div class="box"><h1>500</h1><p>Something went wrong.</p>
<a href="/">← Go home</a></div></body></html>"""


def _render_ssr(renderer: Callable[[], Any]) -> str:
    """Render a page function to an HTML string for SSR. Never raises — caller handles exceptions."""
    from pyra.ssr import render_to_html
    from pyra.state import SessionState, _pop_session, _push_session

    render_module.reset_id_counter()
    ss = SessionState()
    ss.begin_render()
    token = _push_session(ss)
    try:
        tree = render_tree(renderer(), {})
    finally:
        _pop_session(token)
        render_module.reset_id_counter()
    return render_to_html(tree)


@dataclass
class _Connection:
    websocket: WebSocket
    session: Session
    handler_registry: dict[str, Callable[..., Any]] = field(default_factory=dict)
    render_effect: Effect | None = None
    last_tree: dict[str, Any] | None = None
    session_state: SessionState = field(default_factory=SessionState)
    path: str = "/"
    _user_token: Any = None


class App:
    def __init__(self) -> None:
        self._auth: Any = None
        self._error_pages: dict[int, Callable[[], Any]] = {}
        self._starlette = Starlette(
            debug=True,
            routes=[
                Route("/", self._index, methods=["GET"]),
                Route("/__pyra__/runtime.js", self._runtime, methods=["GET"]),
                WebSocketRoute("/__pyra__/ws", self._ws_endpoint),
                # Catch-all route: serve index HTML for any registered path
                # (must come after more specific /__pyra__/* routes)
                Route("/{path:path}", self._index, methods=["GET"]),
            ],
            exception_handlers={500: self._handle_500},
        )

    def mount_static(self, path: str = "/static", directory: str = "static") -> None:
        """Serve static files from *directory* at URL *path*.

        Example::

            app = App()
            app.mount_static("/static", directory="assets")
            # Files in assets/ are now served at /static/filename.ext

        Call before app.run(). The directory is resolved relative to the caller's CWD.
        """
        import os

        from starlette.routing import Mount
        from starlette.staticfiles import StaticFiles

        abs_dir = os.path.abspath(directory)
        if not os.path.isdir(abs_dir):
            os.makedirs(abs_dir, exist_ok=True)
        # Insert before the catch-all route (which must stay last)
        self._starlette.routes.insert(
            len(self._starlette.routes) - 1,
            Mount(path, app=StaticFiles(directory=abs_dir), name="static"),
        )

    def set_error_page(self, status_code: int, renderer: Callable[[], Any]) -> Callable[[], Any]:
        """Register a Pyra page function as the handler for an HTTP error code.

        Example::

            @app.set_error_page(404)  # use as decorator
            def not_found():
                return VStack(Heading("404"), Text("Page not found."), Link("Home", href="/"))
        """
        self._error_pages[status_code] = renderer
        return renderer  # allow use as decorator

    async def _handle_500(self, request: Any, exc: Exception) -> HTMLResponse:
        if 500 in self._error_pages:
            try:
                ssr_html = _render_ssr(self._error_pages[500])
                body = _INDEX_HTML.replace(
                    '<div id="pyra-root"><div style="opacity:0.5">Connecting...</div></div>',
                    f'<div id="pyra-root">{ssr_html}</div>',
                )
                return HTMLResponse(body, status_code=500)
            except Exception:
                pass
        return HTMLResponse(_500_HTML, status_code=500)

    def use_auth(self, auth_manager: Any) -> None:
        """Register auth routes and attach auth_manager to this App instance."""
        from pyra.auth import AuthManager
        if not isinstance(auth_manager, AuthManager):
            raise TypeError("auth_manager must be an AuthManager instance")
        self._auth = auth_manager
        # Register verify endpoint — must rebuild starlette routes
        from starlette.requests import Request
        from starlette.responses import RedirectResponse, HTMLResponse as _HTML

        async def verify(request: Request) -> Any:
            token = request.query_params.get("token", "")
            next_url = request.query_params.get("next", "/")
            user_id = auth_manager.verify_magic_link_token(token)
            if user_id is None:
                return _HTML("<h1>Invalid or expired link.</h1>", status_code=400)
            session_value = auth_manager.create_session_value(user_id)
            response = RedirectResponse(next_url, status_code=303)
            response.set_cookie(
                key=auth_manager.cookie_name,
                value=session_value,
                httponly=True,
                samesite="lax",
                max_age=auth_manager._session_ttl,
            )
            return response

        from starlette.routing import Route as _Route
        self._starlette.routes.insert(0, _Route("/auth/verify", verify, methods=["GET"]))

    async def _index(self, request: Any) -> HTMLResponse:
        # Determine path — handle both "/" and "/{path:path}" routes
        path = request.path_params.get("path", "")
        if not path:
            path = request.url.path
        if not path.startswith("/"):
            path = "/" + path
        if path == "":
            path = "/"

        renderer = _PAGES.get(path)

        # Auth check for protected pages (HTTP layer — before WebSocket)
        if renderer is not None and self._auth is not None:
            requires = getattr(renderer, "_requires_auth", False)
            if requires:
                cookie_val = request.cookies.get(self._auth.cookie_name, "")
                user_id = self._auth.verify_session_value(cookie_val) if cookie_val else None
                if user_id is None:
                    redirect_to = getattr(renderer, "_redirect_to", self._auth.login_path)
                    from starlette.responses import RedirectResponse
                    return RedirectResponse(redirect_to, status_code=303)

        if renderer is not None:
            try:
                ssr_html = _render_ssr(renderer)
            except Exception:
                ssr_html = None
        else:
            ssr_html = None

        if ssr_html:
            body = _INDEX_HTML.replace(
                '<div id="pyra-root"><div style="opacity:0.5">Connecting...</div></div>',
                f'<div id="pyra-root">{ssr_html}</div>',
            )
            return HTMLResponse(body)

        if renderer is None:
            # Custom 404 page
            if 404 in self._error_pages:
                try:
                    ssr_html = _render_ssr(self._error_pages[404])
                    body = _INDEX_HTML.replace(
                        '<div id="pyra-root"><div style="opacity:0.5">Connecting...</div></div>',
                        f'<div id="pyra-root">{ssr_html}</div>',
                    )
                    return HTMLResponse(body, status_code=404)
                except Exception:
                    pass
            return HTMLResponse(_404_HTML, status_code=404)

        return HTMLResponse(_INDEX_HTML)

    async def _runtime(self, request: Any) -> HTMLResponse:
        return HTMLResponse(
            _RUNTIME_JS,
            media_type="application/javascript; charset=utf-8",
        )

    async def _ws_endpoint(self, websocket: WebSocket) -> None:
        await websocket.accept()
        session = new_session()
        conn = _Connection(websocket=websocket, session=session)

        loop = asyncio.get_running_loop()
        send_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        # Store send_queue and loop on conn so _handle_inbound can use them
        conn._send_queue = send_queue  # type: ignore[attr-defined]
        conn._loop = loop  # type: ignore[attr-defined]

        async def sender() -> None:
            while True:
                payload = await send_queue.get()
                await self._send(conn, payload)

        sender_task = asyncio.create_task(sender())

        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                inbound_id = message.get("msg_id")
                if not isinstance(inbound_id, int) or inbound_id <= session.last_inbound_msg_id:
                    continue
                session.last_inbound_msg_id = inbound_id

                payload = message.get("payload") or {}
                should_close = await self._handle_inbound(conn, payload)
                if should_close:
                    break
        except WebSocketDisconnect:
            pass
        finally:
            sender_task.cancel()
            if conn.render_effect:
                conn.render_effect.dispose()
            if conn._user_token is not None:
                from pyra.auth import _SESSION_CTX
                _SESSION_CTX.reset(conn._user_token)

    async def _send(self, conn: _Connection, payload: dict[str, Any]) -> None:
        signed = sign_outbound(conn.session, payload)
        try:
            await conn.websocket.send_text(json.dumps(signed))
        except Exception:
            pass

    async def _handle_inbound(self, conn: _Connection, payload: dict[str, Any]) -> bool:
        """Handle an inbound message. Returns True if the connection should be closed."""
        ptype = payload.get("type")
        if ptype == "hello":
            path = payload.get("path", "/")
            conn.path = path
            renderer = _PAGES.get(path)
            if renderer is None:
                await self._send(conn, {"type": "error", "message": f"no page at {path}"})
                await conn.websocket.close()
                return True

            loop = conn._loop  # type: ignore[attr-defined]
            send_queue = conn._send_queue  # type: ignore[attr-defined]

            # Set session context from cookie
            if self._auth is not None:
                import http.cookies
                cookie_jar = http.cookies.SimpleCookie()
                cookie_jar.load(conn.websocket.headers.get("cookie", ""))
                cookie_val = cookie_jar.get(self._auth.cookie_name)
                user_id = self._auth.verify_session_value(cookie_val.value) if cookie_val else None
            else:
                user_id = None

            from pyra.auth import _set_current_user
            conn._user_token = _set_current_user(user_id)

            def do_render() -> None:
                render_module.reset_id_counter()
                conn.session_state.begin_render()
                token = _push_session(conn.session_state)
                try:
                    from pyra.auth import _AuthRedirectComponent
                    result = renderer()
                    if isinstance(result, _AuthRedirectComponent):
                        loop.call_soon_threadsafe(
                            send_queue.put_nowait,
                            {"type": "redirect", "url": result.url}
                        )
                        return
                    new_tree = render_tree(result, conn.handler_registry)
                finally:
                    _pop_session(token)
                ops = diff(conn.last_tree, new_tree)
                conn.last_tree = new_tree
                if not ops:
                    return
                try:
                    loop.call_soon_threadsafe(
                        send_queue.put_nowait, {"type": "patch", "ops": ops}
                    )
                except RuntimeError:
                    pass

            conn.render_effect = Effect(do_render)
            return False

        if ptype == "event":
            hid = payload.get("handler_id")
            data = payload.get("data") or {}
            handler = conn.handler_registry.get(hid)
            if handler is None:
                return False
            try:
                if _accepts_arg(handler):
                    result = handler(data)
                else:
                    result = handler()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"[pyra] handler {hid} raised: {e}")

        return False

    def run(self, host: str | None = None, port: int | None = None, reload: bool = False) -> None:
        """Start the Pyra application server.

        Args:
            host: The host address to bind to. Defaults to config.host (PYRA_HOST, "127.0.0.1").
            port: The port to listen on. Defaults to config.port (PYRA_PORT, 7340).
            reload: Enable hot-reload via uvicorn's built-in reload mode.
                When reload=True, the app variable must be importable from __main__.
                Example usage::

                    app = App()
                    if __name__ == "__main__":
                        app.run(reload=True)
        """
        from pyra.config import config

        config.check_production_secret()
        _host = host if host is not None else config.host
        _port = port if port is not None else config.port
        import uvicorn
        if reload:
            import sys
            main_module = sys.modules.get("__main__")
            app_var = None
            if main_module:
                for name, val in vars(main_module).items():
                    if val is self:
                        app_var = name
                        break
            if app_var:
                uvicorn.run(
                    f"__main__:{app_var}._starlette",
                    host=_host,
                    port=_port,
                    reload=True,
                    log_level="info",
                )
            else:
                print("[pyra] reload=True requires app to be importable. Falling back to non-reload mode.")
                uvicorn.run(self._starlette, host=_host, port=_port, log_level="info")
        else:
            uvicorn.run(self._starlette, host=_host, port=_port, log_level="info")


def _accepts_arg(fn: Callable[..., Any]) -> bool:
    import inspect
    try:
        inspect.signature(fn).bind(None)
        return True
    except TypeError:
        return False
    except (ValueError, Exception):
        return False
