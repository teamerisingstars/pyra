# Pyra Patch Protocol

The wire format between the Pyra server and the browser/webview runtime. Every server → client message is a **signed envelope** containing a `patch` payload with one or more **patch ops**.

## Signed envelope

```json
{
  "msg_id": <int>,            // monotonic per-session
  "payload": { ... },         // see below
  "sig": "<hex HMAC-SHA256>"  // over canonical(payload + msg_id)
}
```

The client rejects:
- Messages where `msg_id <= last_seen_msg_id` (replay).
- Messages whose signature does not verify (Phase 2: SubtleCrypto in browser).
- Messages where `msg_id` is not an integer or `sig` is missing/malformed.

## Payload types

### `patch`

Server-to-client. Contains a list of ops.

```json
{"type": "patch", "ops": [<op>, <op>, ...]}
```

### `event`

Client-to-server. Reports a UI event.

```json
{
  "type": "event",
  "handler_id": "<node_id>:<event_name>",
  "data": { "value": "...", ... }
}
```

The server resolves `handler_id` against its per-connection registry and invokes the Python handler.

### `hello`

Client-to-server, sent once on WebSocket open. Triggers nothing in v0.0.x — the initial render is pushed by the server's render Effect immediately on connection accept. Reserved for future handshake (auth token exchange, capability negotiation).

## Op vocabulary

Every op carries an `id` referring to a previously-emitted node. Ops are applied in order.

### `init`

Replaces the entire root with a new tree. Emitted on first render.

```json
{"op": "init", "tree": <node>}
```

Where `<node>` is one of:

```json
// Element
{
  "type": "element",
  "id": "n42",
  "tag": "div",
  "props": {"style": "...", "class": "..."},
  "handlers": {"click": "n42:click", "input": "n42:input"},
  "children": [<node>, ...]
}

// Text
{
  "type": "text",
  "id": "n43",
  "value": "Hello — already escaped"
}
```

### `replace_text`

Updates a text node's content.

```json
{"op": "replace_text", "id": "n43", "value": "New text"}
```

### `set_attr` / `remove_attr`

Sets or removes an attribute on an element.

```json
{"op": "set_attr",    "id": "n42", "key": "disabled", "value": "true"}
{"op": "remove_attr", "id": "n42", "key": "disabled"}
```

Special case: when `key === "value"` on an `<input>` or `<textarea>`, the runtime sets the `.value` property directly (so the DOM input field updates).

### `set_handler` / `remove_handler`

Attaches or detaches an event listener. The handler ID is opaque to the client — it's looked up server-side when the client sends an `event`.

```json
{"op": "set_handler",    "id": "n42", "event": "click", "handler_id": "n42:click"}
{"op": "remove_handler", "id": "n42", "event": "click"}
```

### `replace_node`

Wholesale replacement of the subtree rooted at `id`. Emitted when:
- An element's `tag` changes.
- An element's `children` count changes (v0.0.x — keyed list reconciliation will refine this).
- The reconciler can't safely express the change as smaller ops.

```json
{"op": "replace_node", "id": "n42", "node": <node>}
```

The runtime un-indexes the old subtree from its `idMap`, builds the new subtree, and calls `Element.replaceWith`.

## Sanitization invariant

Every text value the server emits has been passed through `html.escape`. The client uses `textContent` (never `innerHTML`) to insert it. Together this means: **AI-generated or user-supplied text cannot inject script content via the patch protocol.**

The protocol is *intentionally narrow*. There is no `set_innerHTML` op, no `eval` op, no `attach_script` op, and no allowlist-bypass for `props`. New ops must justify why no existing one suffices.

## Future ops (planned)

- `insert_at` / `remove_at` — keyed list reconciliation (Phase 2).
- `stream_text_append` — token-stream patches for AI streaming (Phase 3).
- `set_focus` — programmatic focus management (Phase 2).
- `scroll_to` — programmatic scroll (Phase 2).
