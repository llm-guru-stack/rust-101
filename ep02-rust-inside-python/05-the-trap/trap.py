"""The two traps from the video.

    cd 05-the-trap
    uv venv && uv pip install ./trapchunk   (or: pip install ./trapchunk)
    python trap.py

Trap 1 (the GIL): a background Python thread ticks every millisecond.
  We count how many ticks it manages while Rust is busy.
Trap 2 (the toll): crossing from Python into Rust costs something every time.
  Version 1 keeps the Python loop and calls Rust once per word.
  Version 2 hands Rust whole documents and lets Rust do the loop.
"""
import json
import statistics
import threading
import time
from pathlib import Path

import trapchunk

PAYLOAD = Path(__file__).resolve().parent.parent / "data" / "payload.json"
docs = [d["text"] for d in json.loads(PAYLOAD.read_text())["docs"]]


def ticks_while(fn):
    ticks, stop = 0, False

    def heartbeat():
        nonlocal ticks
        while not stop:
            ticks += 1
            time.sleep(0.001)

    th = threading.Thread(target=heartbeat)
    th.start()
    time.sleep(0.05)
    before = ticks
    t0 = time.perf_counter()
    fn()
    elapsed = time.perf_counter() - t0
    during = ticks - before
    stop = True
    th.join()
    return elapsed, during


def median_time(fn, n=5):
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


print("Trap 1: the GIL")
for name, fn in [("holds the GIL   ", trapchunk.chunk_docs_holding_gil), ("releases the GIL", trapchunk.chunk_docs)]:
    elapsed, ticks = ticks_while(lambda: fn(docs, 5, 1, 30))
    print(f"  {name}: {elapsed:.2f}s of Rust work, background thread ticked {ticks} times")

print("\nTrap 2: the toll (how many words are longer than 6 letters?)")
v1 = median_time(lambda: sum(1 for d in docs for w in d.split() if trapchunk.is_long_word(w)))
v2 = median_time(lambda: trapchunk.count_long_words(docs))
py = median_time(lambda: sum(1 for d in docs for w in d.split() if len(w) > 6))
calls = sum(len(d.split()) for d in docs)
print(f"  version 1: Python loop, Rust once per word ({calls:,} calls): {v1:.3f}s")
print(f"  version 2: Rust gets all documents (1 call):            {v2:.3f}s")
print(f"  plain Python, no Rust at all:                           {py:.3f}s")
print(f"  version 2 is {v1 / v2:.0f}x faster than version 1, and version 1 is slower than plain Python")
