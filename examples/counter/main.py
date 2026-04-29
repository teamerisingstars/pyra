"""The Pyra counter example — the "is the architecture sound?" checkpoint.

State() called inside @page is per-session: open two browser tabs, each
gets its own counter. (At module scope, State() returns a process-wide Signal.)

Run:
    cd examples/counter
    python main.py

Open http://127.0.0.1:7340 — open a second tab to confirm independent state.
"""
from pyra import App, Button, HStack, State, Text, VStack, page


@page("/")
def home():
    count = State(0)  # per-session — see top-level docstring
    return VStack(
        Text("Pyra v0.0.2 — counter"),
        Text(f"Count: {count.value}"),
        HStack(
            Button("−", on_click=lambda: count.update(lambda c: c - 1)),
            Button("+", on_click=lambda: count.update(lambda c: c + 1)),
            Button("Reset", on_click=lambda: count.set(0)),
        ),
    )


app = App()


if __name__ == "__main__":
    app.run()
