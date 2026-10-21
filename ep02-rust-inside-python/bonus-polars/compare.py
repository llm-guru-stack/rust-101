"""Bonus: pandas vs Polars (Rust) on a typical "chunk stats" job.

    uv venv && uv pip install -r requirements.txt && .venv/bin/python compare.py
"""
import time

import numpy as np
import pandas as pd
import polars as pl

N = 5_000_000
rng = np.random.default_rng(0)
data = {
    "doc_id": rng.integers(0, 200_000, N),
    "source": rng.choice(["confluence", "sharepoint", "gdrive", "intranet"], N),
    "tokens": rng.integers(20, 512, N),
}


def timed(label, fn):
    t0 = time.perf_counter()
    fn()
    dt = time.perf_counter() - t0
    print(f"{label:<8} {dt:.3f}s")
    return dt


pdf = pd.DataFrame(data)
plf = pl.DataFrame(data)
a = timed("pandas", lambda: pdf[pdf.tokens > 64].groupby(["source", "doc_id"]).tokens.agg(["sum", "mean", "count"]))
b = timed("polars", lambda: plf.lazy().filter(pl.col("tokens") > 64)
          .group_by(["source", "doc_id"]).agg(pl.col("tokens").sum().alias("sum"),
                                               pl.col("tokens").mean().alias("mean"),
                                               pl.len().alias("count")).collect())
print(f"polars is {a / b:.1f}x faster here")
