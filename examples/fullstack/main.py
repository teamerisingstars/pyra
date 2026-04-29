"""Fullstack Task Board - demonstrates Pyra's full feature set.

Pages:
  /           -> landing page (public)
  /login      -> magic-link login form
  /dashboard  -> task board (auth required)
  /about      -> about page (public, multi-route demo)

Run:
    cd examples/fullstack
    python main.py

Open http://127.0.0.1:7340
"""
from __future__ import annotations

import secrets

from pyra import (
    App,
    Badge,
    Button,
    Card,
    Element,
    FormField,
    Heading,
    HStack,
    Image,
    Input,
    Link,
    Spinner,
    State,
    Text,
    VStack,
    page,
    validate,
)
from pyra.auth import AuthManager, get_current_user

auth = AuthManager(
    secret_key="dev-secret-change-in-prod",
    token_ttl=900,
    login_path="/login",
)


# ---------------------------------------------------------------------------
# Landing page - /
# ---------------------------------------------------------------------------

@page("/")
def landing():
    return VStack(
        HStack(
            Heading("Task Board"),
            Badge("v0.1", color="#10b981"),
        ),
        Text("A simple task manager built with Pyra - Python-first reactive UI."),
        Text("Login with a magic-link, add tasks, mark them done, delete them."),
        HStack(
            Link("Get started", href="/login"),
            Link("About", href="/about"),
        ),
        style="max-width:600px;",
    )


# ---------------------------------------------------------------------------
# About page - /about
# ---------------------------------------------------------------------------

@page("/about")
def about():
    return VStack(
        Heading("About Pyra"),
        Text("Pyra is a Python-first, AI-native full-stack framework."),
        Card(
            Text('Multi-page routing - register pages with @page("/path").'),
            title="Routing",
        ),
        Card(
            Text("Reactive State() signals - update a value, the UI patches itself."),
            title="Reactivity",
        ),
        Card(
            Text("Magic-link auth via AuthManager - no passwords required."),
            title="Auth",
        ),
        Card(
            Text("Card, Badge, Image, Heading, Link, FormField - all built in."),
            title="Components",
        ),
        Card(
            Text("SSR: pages are server-rendered to HTML before the WS connects."),
            title="SSR",
        ),
        Link("Back to home", href="/"),
        style="max-width:640px;",
    )


# ---------------------------------------------------------------------------
# Login page - /login (magic-link)
# ---------------------------------------------------------------------------

@page("/login")
def login():
    email = State("")
    sent = State(False)
    token_state = State("")
    email_error = State("")

    def send_link():
        val = email.value.strip()
        if not val or "@" not in val:
            email_error.set("Please enter a valid email address.")
            return
        email_error.set("")
        tok = auth.create_magic_link_token(val)
        token_state.set(tok)
        url = f"http://localhost:7340/auth/verify?token={tok}&next=/dashboard"
        print(f"[dev] Magic-link for {val}: {url}")
        sent.set(True)

    if sent.value:
        verify_url = (
            f"http://localhost:7340/auth/verify?token={token_state.value}&next=/dashboard"
        )
        return VStack(
            Heading("Check your inbox", level=2),
            Text(f"A magic-link was sent to {email.value}."),
            Card(
                Text("Dev mode - click the link below to log in:"),
                Element(
                    tag="a",
                    props={"href": verify_url, "style": "color:#6366f1;word-break:break-all;"},
                    children=[verify_url],
                ),
                title="Magic link",
                style="background:#f0fdf4;border-color:#10b981;",
            ),
            Button("Send another link", on_click=lambda: sent.set(False)),
            style="max-width:480px;",
        )

    return VStack(
        Heading("Sign in", level=2),
        Text("Enter your email - we'll send you a one-time login link."),
        FormField(
            name="email",
            label="Email address",
            value=email.value,
            on_input=lambda v: email.set(v),
            placeholder="you@example.com",
            input_type="email",
            error=email_error.value,
        ),
        Button("Send magic link", on_click=send_link),
        Link("Back to home", href="/"),
        style="max-width:400px;",
    )


# ---------------------------------------------------------------------------
# Dashboard - /dashboard (auth required, task board)
# ---------------------------------------------------------------------------

@page("/dashboard")
@auth.require_auth
def dashboard():
    user = get_current_user()
    tasks = State([])
    new_task_text = State("")

    def add_task():
        text = new_task_text.value.strip()
        if not text:
            return
        task_id = secrets.token_hex(4)
        tasks.update(lambda lst: lst + [{"id": task_id, "text": text, "done": False}])
        new_task_text.set("")

    def toggle_task(task_id: str):
        def updater(lst):
            return [
                {**t, "done": not t["done"]} if t["id"] == task_id else t
                for t in lst
            ]
        tasks.update(updater)

    def delete_task(task_id: str):
        tasks.update(lambda lst: [t for t in lst if t["id"] != task_id])

    done_count = sum(1 for t in tasks.value if t["done"])
    pending_count = len(tasks.value) - done_count

    task_cards = []
    for task in tasks.value:
        badge = (
            Badge("done", color="#10b981")
            if task["done"]
            else Badge("pending", color="#6366f1")
        )
        tid = task["id"]
        card = Card(
            HStack(
                Text(task["text"]),
                badge,
                Button(
                    "Mark done" if not task["done"] else "Mark undone",
                    on_click=lambda _id=tid: toggle_task(_id),
                ),
                Button("Delete", on_click=lambda _id=tid: delete_task(_id)),
                style="flex-wrap:wrap;",
            ),
        )
        wrapper = Element(
            tag="div",
            key=task["id"],
            children=[card],
        )
        task_cards.append(wrapper)

    return VStack(
        HStack(
            Heading("My Tasks"),
            Badge(f"{len(tasks.value)} total", color="#374151"),
            Badge(f"{done_count} done", color="#10b981"),
            Badge(f"{pending_count} pending", color="#6366f1"),
        ),
        Text(f"Logged in as: {user}"),
        HStack(
            Input(
                value=new_task_text.value,
                placeholder="New task...",
                on_input=lambda v: new_task_text.set(v),
            ),
            Button("Add task", on_click=add_task),
        ),
        *task_cards,
        Link("Back to home", href="/"),
        style="max-width:640px;",
    )


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

app = App()

if __name__ == "__main__":
    app.run()
