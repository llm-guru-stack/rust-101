"""Run every step, check they all give the same answer, write results.md.

    python bench/run_all.py                 # all steps, 5 timed requests each
    python bench/run_all.py --n 3           # fewer requests
    python bench/run_all.py --only 00 04    # just some steps

Needs: uv (https://docs.astral.sh/uv/), a Rust toolchain for steps 04 and 06
(https://rustup.rs) and data/payload.json (python data/make_payload.py).
Each step gets its own .venv, because step 00 uses Pydantic v1 and the rest use v2.
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    ("00-baseline", "baseline"),
    ("01-orjson", "+ orjson"),
    ("02-pydantic-v2", "+ Pydantic v2"),
    ("03-tokenizers", "+ HF tokenizers"),
    ("04-pyo3-chunker", "+ PyO3 chunker"),
    ("06-io-bound", "+ a 1.5 s LLM call (06)"),
]


def venv_python(step_dir: Path) -> Path:
    return step_dir / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def setup(step_dir: Path) -> Path:
    py = venv_python(step_dir)
    if not py.exists():
        subprocess.run(["uv", "venv", "-q", "--python", "3.12", ".venv"], cwd=step_dir, check=True)
    subprocess.run(["uv", "pip", "install", "-q", "--python", str(py), "-r", "requirements.txt"], cwd=step_dir, check=True)
    return py


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_up(port: int, timeout: float = 120) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return
        except OSError:
            time.sleep(0.3)
    raise RuntimeError("server did not start")


def post(port: int, body: bytes) -> tuple[float, bytes]:
    req = urllib.request.Request(f"http://127.0.0.1:{port}/ingest", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=600) as r:
        data = r.read()
    return time.perf_counter() - t0, data


def fingerprint(data: bytes) -> str:
    d = json.loads(data)
    return hashlib.sha256(json.dumps(d["chunks"]).encode()).hexdigest()[:12]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--only", nargs="*", default=None, help="step prefixes, e.g. 00 03")
    a = ap.parse_args()
    if not (ROOT / "data" / "payload.json").exists():
        sys.exit("Missing data/payload.json. Run: python data/make_payload.py")
    if not shutil.which("uv"):
        sys.exit("This script needs uv: https://docs.astral.sh/uv/getting-started/installation/")
    body = (ROOT / "data" / "payload.json").read_bytes()
    print("running every step… results → results.md")
    rows, base, ref = [], None, None
    for step, label in STEPS:
        if a.only and not any(step.startswith(p) for p in a.only):
            continue
        step_dir = ROOT / step
        print(f"\n[{step}] installing…", flush=True)
        py = setup(step_dir)
        port = free_port()
        srv = subprocess.Popen([str(py), "-m", "uvicorn", "app:app", "--port", str(port), "--log-level", "warning"], cwd=step_dir)
        try:
            wait_up(port)
            _, data = post(port, body)  # warm-up (loads models, fills caches)
            times = []
            for i in range(a.n):
                dt, data = post(port, body)
                times.append(dt)
                print(f"  request {i + 1}: {dt:.3f}s", flush=True)
        finally:
            srv.terminate()
            srv.wait()
        med = statistics.median(times)
        fp = fingerprint(data)
        ref = ref or fp
        base = base or med
        d = json.loads(data)
        rows.append((label, med, base / med, fp == ref, len(d["chunks"])))
    lines = ["# Results", "",
             f"Machine: {platform.platform()}, {platform.processor() or platform.machine()}, Python {platform.python_version()}  ",
             f"Median of {a.n} requests after one warm-up. Each request: data/payload.json → /ingest.", "",
             "| Step | Median per request | Speed-up vs baseline | Same chunks + token counts |",
             "| --- | --- | --- | --- |"]
    for label, med, sp, same, _ in rows:
        lines.append(f"| {label} | {med:.3f} s | {sp:.2f}× | {'yes' if same else 'NO'} |")
    if rows:
        lines += ["", f"Chunks per request: {rows[0][4]:,}"]
    (ROOT / "results.md").write_text("\n".join(lines) + "\n")
    print("\n" + "\n".join(lines))


if __name__ == "__main__":
    main()
