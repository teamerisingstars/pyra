"""Multi-user real-time chat — demonstrates shared Signal state across sessions.

Every connected browser sees messages in real time because the module-scope
Signal triggers every active Effect when updated.
Open multiple tabs to test: each tab is an independent session with its own
username and draft, but all share the same message list.

Run:
    cd examples/chat
    python main.py

Open http://127.0.0.1:7340 in two browser tabs.
"""
from __future__ import annotations

import secrets

from pyra import (
    App,
    Badge,
    Button,
    Element,
    FormField,
    Heading,
    HStack,
    Input,
    State,
    Text,
    VStack,
    page,
)
from pyra.reactive import Signal

_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#3b82f6", "#8b5cf6", "#ec4899"]

# Module-scope Signal — shared across ALL sessions / browser tabs.
messages: Signal[list[dict]] = Signal([])


def _user_color(username: str) -> str:
    return _COLORS[hash(username) % len(_COLORS)]


@page("/")
def chat():
    username = State("")
    draft = State("")

    def send():
        if draft.value.strip() and username.value.strip():
            new_msgs = messages.value + [
                {
                    "id": secrets.token_hex(4),
                    "user": username.value,
                    "text": draft.value.strip(),
                }
            ]
            messages.set(new_msgs[-50:])
            draft.set("")

    if not username.value:
        return VStack(
            Heading("Pyra Chat", level=2),
            Text("Choose a username to join"),
            FormField(
                "username",
                value=username.value,
                on_input=username.set,
                placeholder="Your name",
            ),
            Button("Join", on_click=lambda: username.set(username.value.strip())),
            style="max-width:400px;",
        )

    msg_rows = [
        Element(
            tag="div",
            key=msg["id"],
            props={"style": "padding:4px 0;"},
            children=[
                HStack(
                    Badge(msg["user"], color=_user_color(msg["user"])),
                    Text(msg["text"]),
                    gap="8px",
                )
            ],
        )
        for msg in messages.value
    ]

    return VStack(
        HStack(
            Heading("Pyra Chat", level=2),
            Badge("Live", color="#10b981"),
        ),
        Element(
            tag="div",
            props={"style": "flex:1;overflow-y:auto;border:1px solid #e5e7eb;border-radius:8px;padding:12px;min-height:300px;max-height:500px;"},
            children=msg_rows,
        ),
        HStack(
            Input(draft.value, placeholder="Message…", on_input=draft.set),
            Button("Send", on_click=send),
        ),
        Text(f"Chatting as: {username.value}", style="color:#6b7280;font-size:0.875rem;"),
        style="max-width:640px;height:100vh;padding:24px;",
    )


app = App()

if __name__ == "__main__":
    app.run()
