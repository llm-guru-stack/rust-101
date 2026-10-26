"""Python threads vs multiprocessing vs Rust + rayon, on the same documents.

    python bench/run_threads.py                 # every mode, 8 workers
    python bench/run_threads.py --threads 1     # just the pure-Python chunker on N threads
    python bench/run_threads.py --workers 4     # match your core count
"""
import argparse
import json
import os
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from chunker import chunk_doc  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent / "data" / "docs.json"


def timed(fn, n=3):
    times, out = [], None
    for _ in range(n):
        t0 = time.perf_counter()
        out = fn()
        times.append(time.perf_counter() - t0)
    return statistics.median(times), out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=None, help="only run the Python-threads test with N threads")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if not DOCS.exists():
        sys.exit("Missing data/docs.json. Run: python data/make_docs.py")
    docs = json.loads(DOCS.read_text())
    n = os.cpu_count()
    print(f"{len(docs):,} documents, {n} CPU core{'s' if n != 1 else ''} on this machine")

    if a.threads:
        with ThreadPoolExecutor(max_workers=a.threads) as pool:
            t, _ = timed(lambda: list(pool.map(chunk_doc, docs)))
        print(f"{a.threads} thread{'s' if a.threads > 1 else ''}:  {t:.2f}s")
        return

    w = a.workers
    rows = []
    t1, ref = timed(lambda: [chunk_doc(d) for d in docs])
    rows.append(("Python, 1 thread", t1, True))
    with ThreadPoolExecutor(max_workers=w) as pool:
        t, out = timed(lambda: list(pool.map(chunk_doc, docs)))
    rows.append((f"Python, {w} threads", t, out == ref))
    with ProcessPoolExecutor(max_workers=w) as pool:
        list(pool.map(chunk_doc, docs[:w], chunksize=1))  # start the workers first
        t, out = timed(lambda: list(pool.map(chunk_doc, docs, chunksize=max(1, len(docs) // (w * 4)))))
    rows.append((f"Python, {w} processes", t, out == ref))
    try:
        import fastchunk
        t, out = timed(lambda: fastchunk.chunk_docs(docs, 5, 1))
        nt = fastchunk.num_threads()
        rows.append((f"Rust + rayon, {nt} thread{'s' if nt != 1 else ''}", t, out == ref))
    except ImportError:
        print("(fastchunk not installed: cd py && maturin develop --release)")

    print(f"\n{'mode':<28}{'time':>9}{'speed-up':>11}  same output")
    for name, t, same in rows:
        print(f"{name:<28}{t:>8.3f}s{t1 / t:>10.1f}×  {'yes' if same else 'NO'}")


if __name__ == "__main__":
    main()
