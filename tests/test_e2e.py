"""End-to-end test: real WebSocket against the counter example.

Boots the app in a background thread, opens a WebSocket, exchanges messages,
asserts that the counter increments and the new tree streams back signed.
"""
import asyncio
import json
import threading
import time

import pytest
import uvicorn
import websockets

from pyra import App, Button, State, Text, VStack, page


@pytest.fixture(scope="module")
def server():
    @page("/")
    def home():
        counter = State(0)
        return VStack(
            Text(f"Count: {counter.value}"),
            Button("inc", on_click=lambda: counter.update(lambda c: c + 1)),
        )

    app = App()
    config = uvicorn.Config(
        app._starlette, host="127.0.0.1", port=7342, log_level="error"
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.05)

    yield "ws://127.0.0.1:7342/__pyra__/ws"

    server.should_exit = True
    thread.join(timeout=2)


async def _read_init(ws):
    msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
    op = msg["payload"]["ops"][0]
    assert op["op"] == "init"
    tree = op["tree"]
    text_node = tree["children"][0]["children"][0]
    button_node = tree["children"][1]
    return text_node["id"], button_node["handlers"]["click"], text_node["value"], msg


async def _click(ws, msg_id, handler_id):
    await ws.send(json.dumps({
        "msg_id": msg_id,
        "payload": {"type": "event", "handler_id": handler_id, "data": {}},
        "sig": "x",
    }))
    msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
    return msg["payload"]["ops"]


async def _async_e2e(url: str):
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"msg_id": 1, "payload": {"type": "hello"}, "sig": "x"}))
        text_id, click_handler, initial, first_msg = await _read_init(ws)
        assert first_msg["msg_id"] == 1
        assert "sig" in first_msg
        assert first_msg["payload"]["type"] == "patch"
        assert initial.startswith("Count: 0")

        ops = await _click(ws, 2, click_handler)
        assert any(
            o["op"] == "replace_text" and o["id"] == text_id and o["value"] == "Count: 1"
            for o in ops
        ), f"expected minimal replace_text patch, got {ops!r}"


async def _async_two_connections_independent(url: str):
    async with websockets.connect(url) as ws_a, websockets.connect(url) as ws_b:
        await ws_a.send(json.dumps({"msg_id": 1, "payload": {"type": "hello"}, "sig": "x"}))
        await ws_b.send(json.dumps({"msg_id": 1, "payload": {"type": "hello"}, "sig": "x"}))

        a_text, a_click, a_initial, _ = await _read_init(ws_a)
        b_text, b_click, b_initial, _ = await _read_init(ws_b)
        assert a_initial == "Count: 0"
        assert b_initial == "Count: 0"

        # Click A three times — B should be untouched.
        for i in range(2, 5):
            await _click(ws_a, i, a_click)

        # Click B once.
        ops_b = await _click(ws_b, 2, b_click)
        replace = next(o for o in ops_b if o["op"] == "replace_text")
        # B reads "Count: 1" — proving its state is independent of A's.
        assert replace["value"] == "Count: 1"


def test_counter_end_to_end(server):
    asyncio.run(_async_e2e(server))


def test_two_connections_have_independent_state(server):
    asyncio.run(_async_two_connections_independent(server))
