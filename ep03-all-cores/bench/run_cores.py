"""How does rayon scale with cores? And how much of the call can't be parallelised?

    RAYON_NUM_THREADS=4 python bench/run_cores.py   # one run with 4 cores
    python bench/run_cores.py --all                 # 1, 2, 4, 8 cores, as a table
"""
import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "data" / "docs.json"


def one_run():
    import fastchunk
    docs = json.loads(DOCS.read_text())
    totals, rust = [], []
    for _ in range(5):
        t0 = time.perf_counter()
        _, r = fastchunk.chunk_docs_timed(docs, 5, 1)
        totals.append(time.perf_counter() - t0)
        rust.append(r)
    return fastchunk.num_threads(), statistics.median(totals), statistics.median(rust)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if not DOCS.exists():
        sys.exit("Missing data/docs.json. Run: python data/make_docs.py")
    if a.json:
        print(json.dumps(one_run()))
        return
    if not a.all:
        n, total, rust = one_run()
        print(f"{n} core{'s' if n > 1 else ''}: {total:.3f}s total  (Rust part {rust:.3f}s, the rest is Python ↔ Rust conversion)")
        return
    rows = []
    for n in (1, 2, 4, 8):
        env = dict(os.environ, RAYON_NUM_THREADS=str(n))
        out = subprocess.run([sys.executable, __file__, "--json"], env=env, capture_output=True, text=True, check=True)
        rows.append(json.loads(out.stdout))
    base_t, base_r = rows[0][1], rows[0][2]
    print(f"{'cores':>5}{'total':>10}{'speed-up':>10}{'Rust part':>12}{'speed-up':>10}{'serial part':>13}")
    for n, total, rust in rows:
        print(f"{n:>5}{total:>9.3f}s{base_t / total:>9.1f}×{rust:>11.3f}s{base_r / rust:>9.1f}×{total - rust:>12.3f}s")
    print(f"\nThis machine has {os.cpu_count()} core(s). The 'serial part' (handing strings between Python and Rust)")
    print("doesn't shrink with more cores. That's Amdahl's law.")


if __name__ == "__main__":
    main()
