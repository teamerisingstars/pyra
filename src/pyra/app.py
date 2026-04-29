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
  });

  ws.addEventListener("close", () => {
    root.innerHTML = '<div style="opacity:0.5">Disconnected. Reload to reconnect.</div>';
  });
})();
"""


@dataclass
class _Connection:
    websocket: WebSocket
    session: Session
    handler_registry: dict[str, Callable[..., Any]] = field(default_factory=dict)
    render_effect: Effect | None = None
    last_tree: dict[str, Any] | None = None
    session_state: SessionState = field(default_factory=SessionState)
    path: str = "/"


class App:
    def __init__(self) -> None:
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
        )

    async def _index(self, request: Any) -> HTMLResponse:
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

            def do_render() -> None:
                render_module.reset_id_counter()
                conn.session_state.begin_render()
                token = _push_session(conn.session_state)
                try:
                    new_tree = render_tree(renderer(), conn.handler_registry)
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

    def run(self, host: str = "127.0.0.1", port: int = 7340, reload: bool = False) -> None:
        """Start the Pyra application server.

        Args:
            host: The host address to bind to.
            port: The port to listen on.
            reload: Enable hot-reload via uvicorn's built-in reload mode.
                When reload=True, the app variable must be importable from __main__.
                Example usage::

                    app = App()
                    if __name__ == "__main__":
                        app.run(reload=True)
        """
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
                    host=host,
                    port=port,
                    reload=True,
                    log_level="info",
                )
            else:
                print("[pyra] reload=True requires app to be importable. Falling back to non-reload mode.")
                uvicorn.run(self._starlette, host=host, port=port, log_level="info")
        else:
            uvicorn.run(self._starlette, host=host, port=port, log_level="info")


def _accepts_arg(fn: Callable[..., Any]) -> bool:
    import inspect
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return False
    return any(
        p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        and p.default is p.empty
        for p in sig.parameters.values()
    )
