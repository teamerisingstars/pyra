from __future__ import annotations

from pyra import App, Button, HStack, Input, State, Text, VStack, page


@page("/")
def home():
    todos = State([])
    new_text = State("")

    def add_todo():
        text = new_text.value.strip()
        if text:
            todos.update(lambda lst: lst + [text])
            new_text.set("")

    todo_rows = [
        HStack(
            Text(todo),
            Button("×", on_click=lambda i=i: todos.update(lambda lst: [x for j, x in enumerate(lst) if j != i])),
            gap=8,
        )
        for i, todo in enumerate(todos.value)
    ]

    return VStack(
        Text("Pyra — todo app"),
        HStack(
            Input(value=new_text.value, placeholder="New todo…", on_input=lambda v: new_text.set(v)),
            Button("Add", on_click=add_todo),
            gap=8,
        ),
        VStack(*todo_rows, gap=4),
        gap=12,
    )


app = App()


if __name__ == "__main__":
    app.run()
