# Pyra Chat Example

Demonstrates a multi-user real-time chat room using a shared module-scope `Signal` for the message list and per-session `State` for each user's username and draft message.

## Run

```bash
cd examples/chat
python main.py
```

Open **http://127.0.0.1:7340** in two or more browser tabs, pick different usernames, and send messages — every tab updates instantly without any polling or manual refresh.

## What to try

- Open two tabs, join with different usernames, and send messages back and forth to see real-time sync via the shared `Signal`.
- Notice that each tab tracks its own draft independently — that's per-session `State` at work.
- Inspect the DOM: each message `<div>` carries a `key` attribute, so Pyra's reconciler patches only changed nodes rather than re-rendering the whole list.
