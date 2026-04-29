# Patch Protocol

## Overview

The patch protocol is the wire format through which the Pyra server drives UI updates in the browser. After each reactive state change the server's reconciler diffs the new render tree against the previous one, produces a minimal list of typed patch ops, and sends them to the browser over a WebSocket connection. The browser runtime applies those ops directly to the live DOM, avoiding full-page reloads and keeping DOM mutations to the smallest set necessary to reflect the new state.

## Transport envelope

Every WebSocket message — in both directions — is a JSON object with a `msg_id`, a `payload`, and a `sig`.

### Server to client

```json
{
  "msg_id": 3,
  "payload": { "type": "patch", "ops": [ ... ] },
  "sig": "a3f9...e1c2"
}
```

- `msg_id` — integer, monotonically increasing per session, starting at 1. Incremented by `sign_outbound` in `transport.py` on every outbound message.
- `payload` — the message body (see payload types below).
- `sig` — HMAC-SHA256 hex digest computed over the canonical JSON of `{"msg_id": <int>, "payload": {...}}` (keys sorted, no extra whitespace) using the per-session secret.
- `session_id` — not present in the signed envelope itself; it lives inside the `Session` object on the server and is used as a unique per-connection identifier (`secrets.token_urlsafe(24)`).

### Client to server

```json
{
  "msg_id": 1,
  "payload": { "type": "event", "handler_id": "n3:click", "data": {} },
  "sig": "client-unsigned-v002"
}
```

- `msg_id` — integer, monotonically increasing per browser session, starting at 1 and incremented by the client's `send()` helper.
- `sig` — the literal string `"client-unsigned-v002"` in v0.0.2 (client-to-server signing is a placeholder).

### Replay rejection

The server tracks `last_inbound_msg_id` on the `Session` object (initialized to `0`). Any inbound message whose `msg_id` is not strictly greater than that value is silently dropped:

```python
if not isinstance(inbound_id, int) or inbound_id <= session.last_inbound_msg_id:
    continue
```

The browser applies the same check in the opposite direction: it tracks `lastMsgId` (initialized to `0`) and ignores any server message where `msg.msg_id <= lastMsgId`.

## Render tree node shapes

The initial `init` op and the `replace_node` op both carry a full render tree node. There are exactly two node types.

### Element node

```json
{
  "type": "element",
  "id": "n7",
  "tag": "button",
  "props": {
    "class": "primary",
    "disabled": "true"
  },
  "handlers": {
    "click": "n7:click"
  },
  "children": [ ... ]
}
```

| Field | Type | Description |
|---|---|---|
| `type` | `"element"` | Discriminator. |
| `id` | string | Stable node ID for this render cycle (e.g. `"n7"`). |
| `tag` | string | HTML tag name (e.g. `"div"`, `"button"`, `"input"`). |
| `props` | object | Filtered HTML attributes (see `_safe_props` allowlist). |
| `handlers` | object | Map of event name → handler ID string. |
| `children` | array | Ordered child nodes (element or text). |

### Text node

```json
{
  "type": "text",
  "id": "n8",
  "value": "Hello &amp; welcome"
}
```

| Field | Type | Description |
|---|---|---|
| `type` | `"text"` | Discriminator. |
| `id` | string | Stable node ID for this render cycle. |
| `value` | string | HTML-escaped text content (via `html.escape`). |

### Node ID scheme

IDs are assigned by a depth-first, pre-order counter that resets to `1` at the start of each render cycle. The counter is a module-level `itertools.count(1)` in `render.py`, reset by `reset_id_counter()`. IDs have the form `"n<integer>"` (e.g. `"n1"`, `"n2"`, `"n42"`).

## Patch ops

All ops are objects with an `"op"` discriminator field. The full vocabulary is defined in `reconciler.py`.

| Op | Additional fields | Emitted when | Client action |
|---|---|---|---|
| `init` | `tree: <node>` | `old` tree is `None` (first render) | Clear `#pyra-root`, build the full tree from `op.tree`, populate `idMap`. |
| `replace_text` | `id: str`, `value: str` | Text node exists in both trees but its `value` differs | Look up the DOM text node by `id` in `idMap`; set `textContent` to the decoded value. |
| `set_attr` | `id: str`, `key: str`, `value: any` | A prop key is new or its value changed | Call `setProp(el, key, value)`. For `key === "value"` on `INPUT`/`TEXTAREA`, sets `.value` directly; otherwise calls `setAttribute`. |
| `remove_attr` | `id: str`, `key: str` | A prop key present in the old tree is absent in the new tree | Call `el.removeAttribute(key)`. |
| `set_handler` | `id: str`, `event: str`, `handler_id: str` | An event handler is new or its handler ID changed | Detach any existing listener for that event, then attach a new listener that sends `{type: "event", handler_id, data}` to the server. |
| `remove_handler` | `id: str`, `event: str` | An event handler present in the old tree is absent in the new tree | Detach the listener for that event. |
| `replace_node` | `id: str`, `node: <node>` | Tag mismatch, `type` mismatch, or child-count difference at any element | Call `unindexSubtree(old)` to remove all old IDs from `idMap`, build the new subtree with `buildNode(op.node)`, then call `old.replaceWith(fresh)`. |

### Op JSON shapes

```json
{ "op": "init",           "tree": { "type": "element", ... } }
{ "op": "replace_text",   "id": "n8",  "value": "Count: 5" }
{ "op": "set_attr",       "id": "n3",  "key": "disabled", "value": "true" }
{ "op": "remove_attr",    "id": "n3",  "key": "disabled" }
{ "op": "set_handler",    "id": "n3",  "event": "click", "handler_id": "n3:click" }
{ "op": "remove_handler", "id": "n3",  "event": "click" }
{ "op": "replace_node",   "id": "n5",  "node": { "type": "element", ... } }
```

## Handler IDs

Handler IDs have the format `"<node-id>:<event-name>"`, e.g. `"n7:click"` or `"n12:input"`.

They are constructed in `render.py` when an `Element` with a non-`None` handler function is serialized:

```python
hid = f"{nid}:{event_name}"
registry[hid] = fn
handlers[event_name] = hid
```

The handler registry (`handler_registry`) is a plain `dict[str, Callable]` on the `_Connection` object, cleared and repopulated on every render cycle. When the browser fires an event it sends the handler ID back to the server in a `{"type": "event", "handler_id": "...", "data": {...}}` payload. The server looks the ID up in `conn.handler_registry` and calls the Python function.

For `input` and `change` events the browser includes `{"value": ev.target.value}` in the `data` field. For all other events `data` is `{}`.

## Security notes

### HMAC-SHA256 signing

All server-to-client messages are signed. `sign_outbound` in `transport.py` computes:

```
sig = HMAC-SHA256(session.secret, canonical_json({"msg_id": N, "payload": {...}}))
```

The canonical encoding uses `json.dumps(..., sort_keys=True, separators=(",", ":"))`. The per-session secret is 32 random bytes generated by `secrets.token_bytes(32)` at connection time.

### Replay rejection via monotonic `msg_id`

Both the server and the browser enforce a strictly-increasing `msg_id`. Any message with `msg_id <= last_seen` is dropped before the payload is inspected.

### `_safe_props` allowlist

The `_safe_props` function in `render.py` strips any prop key that is not in the following set before it is included in a rendered node or patch op:

| Allowed prop keys |
|---|
| `style` |
| `value` |
| `placeholder` |
| `type` |
| `name` |
| `checked` |
| `disabled` |
| `href` |
| `src` |
| `alt` |
| `title` |
| `class` |
| `id` |
| `rel` |

Any prop key outside this set is silently dropped at render time and never reaches the wire.

### Text sanitization

Text node values are passed through `html.escape` in `render.py` before serialization. The browser runtime inserts them via `textContent` (never `innerHTML`). There is no `set_innerHTML`, `eval`, or `attach_script` op in the vocabulary.

## Limitations (v0.0.2)

- **No keyed list diffing.** When the number of children at any element changes, the reconciler bails to a `replace_node` on the entire subtree rather than emitting targeted `insert_at` / `remove_at` ops. The comment in `reconciler.py` notes this will be addressed in Phase 3.
- **Client signature is a placeholder.** The `sig` field on client-to-server messages is always the literal string `"client-unsigned-v002"`. Server-side verification of inbound signatures (`verify_inbound` in `transport.py`) exists but is not called from the WebSocket handler in v0.0.2.
