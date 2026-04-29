"""Microbenchmarks for the diff reconciler.

Run: python benchmarks/bench_reconciler.py
"""
from __future__ import annotations

import copy
import timeit

from pyra.reconciler import diff


# --- tree builders ---

def make_flat_tree(n: int, prefix: str = "v") -> dict:
    children = [
        {"type": "text", "id": f"t{i}", "value": f"{prefix}{i}"}
        for i in range(n)
    ]
    return {"type": "element", "id": "root", "tag": "div", "props": {}, "handlers": {}, "children": children}


def make_deep_tree(depth: int) -> dict:
    node: dict = {"type": "text", "id": f"leaf", "value": "hello"}
    for i in range(depth - 1, -1, -1):
        node = {
            "type": "element",
            "id": f"d{i}",
            "tag": "div",
            "props": {},
            "handlers": {},
            "children": [node],
        }
    return node


# --- benchmark runner ---

def bench(label: str, stmt, setup, number: int = 1000) -> None:
    t = timeit.timeit(stmt, setup=setup, number=number)
    per_call_us = (t / number) * 1_000_000
    print(f"{label:<45} {per_call_us:>8.1f} µs/call  ({number} calls)")


if __name__ == "__main__":
    N = 1000

    old_flat = make_flat_tree(N, prefix="v")
    new_flat_same = make_flat_tree(N, prefix="v")
    new_flat_all_changed = make_flat_tree(N, prefix="x")
    new_flat_last_changed = make_flat_tree(N, prefix="v")
    new_flat_last_changed["children"][-1]["value"] = "changed"

    deep_old = make_deep_tree(100)
    deep_new_changed = make_deep_tree(100)
    # Navigate to leaf and change value
    node = deep_new_changed
    while node.get("type") == "element":
        node = node["children"][0]
    node["value"] = "world"

    bench(
        "flat/1000 no-op diff",
        stmt=lambda: diff(old_flat, new_flat_same),
        setup="pass",
        number=1000,
    )

    bench(
        "flat/1000 all-text-change diff",
        stmt=lambda: diff(old_flat, new_flat_all_changed),
        setup="pass",
        number=1000,
    )

    bench(
        "flat/1000 single-last-text-change diff",
        stmt=lambda: diff(old_flat, new_flat_last_changed),
        setup="pass",
        number=1000,
    )

    bench(
        "deep/100-level chain leaf-text-change diff",
        stmt=lambda: diff(deep_old, deep_new_changed),
        setup="pass",
        number=1000,
    )
