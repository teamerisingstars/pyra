"""Pyra CLI — scaffold, run, and manage Pyra applications."""
from __future__ import annotations

import argparse
import os
import sys
import textwrap


def cmd_new(args: argparse.Namespace) -> int:
    """Scaffold a new Pyra project."""
    name = args.name
    target = os.path.join(os.getcwd(), name)
    if os.path.exists(target):
        print(f"[pyra] Error: directory '{name}' already exists.", file=sys.stderr)
        return 1

    os.makedirs(target)
    os.makedirs(os.path.join(target, "static"), exist_ok=True)

    # main.py
    main_py = textwrap.dedent(f"""\
        from __future__ import annotations

        from pyra import App, Button, State, Text, VStack, page


        @page("/")
        def home():
            count = State(0)
            return VStack(
                Text(f"Hello from {{'{name}'}}! Count: {{count.value}}"),
                Button("+1", on_click=lambda: count.update(lambda c: c + 1)),
            )


        app = App()

        if __name__ == "__main__":
            app.run(reload=True)
        """)

    # requirements.txt
    requirements = "pyra\n"

    # .env.example
    env_example = textwrap.dedent("""\
        PYRA_SECRET_KEY=change-me-before-deploying
        PYRA_DEBUG=true
        PYRA_HOST=127.0.0.1
        PYRA_PORT=7340
        # PYRA_DB_URL=postgresql://user:pass@localhost/{name}
        """)

    # .gitignore
    gitignore = textwrap.dedent("""\
        __pycache__/
        .venv/
        *.pyc
        .env
        pyra_dev.db
        static/uploads/
        """)

    files = {
        "main.py": main_py,
        "requirements.txt": requirements,
        ".env.example": env_example,
        ".gitignore": gitignore,
    }
    for filename, content in files.items():
        with open(os.path.join(target, filename), "w") as f:
            f.write(content)

    print(f"[pyra] Created project '{name}'")
    print(f"  cd {name}")
    print("  pip install pyra")
    print("  python main.py")
    return 0


def cmd_dev(args: argparse.Namespace) -> int:
    """Start development server with auto-reload."""
    app_ref = args.app  # e.g. "main:app"
    host = args.host or os.environ.get("PYRA_HOST", "127.0.0.1")
    port = int(args.port or os.environ.get("PYRA_PORT", "7340"))

    try:
        import uvicorn
    except ImportError:
        print("[pyra] uvicorn is required. Install with: pip install pyra", file=sys.stderr)
        return 1

    module_name, _, attr = app_ref.partition(":")
    attr = attr or "app"
    starlette_ref = f"{module_name}:{attr}._starlette"

    print(f"[pyra] Starting dev server → http://{host}:{port}")
    uvicorn.run(starlette_ref, host=host, port=port, reload=True, log_level="info")
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    """Print the installed Pyra version."""
    from pyra import __version__
    print(f"pyra {__version__}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pyra",
        description="Pyra — Python-first, AI-native full-stack framework",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    # pyra new <name>
    p_new = sub.add_parser("new", help="Scaffold a new Pyra project")
    p_new.add_argument("name", help="Project directory name")
    p_new.set_defaults(func=cmd_new)

    # pyra dev [app] [--host] [--port]
    p_dev = sub.add_parser("dev", help="Start development server with auto-reload")
    p_dev.add_argument("app", nargs="?", default="main:app",
                       help="Module:variable path to the App instance (default: main:app)")
    p_dev.add_argument("--host", default=None)
    p_dev.add_argument("--port", default=None)
    p_dev.set_defaults(func=cmd_dev)

    # pyra version
    p_ver = sub.add_parser("version", help="Print installed version")
    p_ver.set_defaults(func=cmd_version)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
