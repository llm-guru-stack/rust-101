# Episode 3: How to use all CPU cores in Python (with Rust)

Your laptop has several CPU cores, and plain Python code uses one of them. This folder has
everything from the video: Python threads vs multiprocessing vs Rust + rayon, an honest
core-scaling benchmark, the same Rust library called from Node.js, and the event-loop trap.

```
ep03-all-cores/
├── data/make_docs.py      # deterministic test documents → data/docs.json
├── fastchunk-core/        # plain Rust chunking logic (no Python, no Node), uses rayon
├── py/                    # PyO3 wrapper → Python package `fastchunk`
├── node/                  # napi-rs wrapper → Node package, async (Promise) and sync versions
├── bench/run_threads.py   # Python 1 thread vs N threads vs N processes vs Rust + rayon
├── bench/run_cores.py     # rayon on 1, 2, 4, 8 cores, and the part that can't be split
└── api/                   # episode 2's FastAPI app; the import doesn't change
```

## Setup

You need Python 3.12, [uv](https://docs.astral.sh/uv/), [Rust](https://rustup.rs) and, for the
JavaScript part, Node.js 20+.

```bash
cd ep03-all-cores
python data/make_docs.py          # 10,000 documents (use --docs 2000 on a slow machine)
uv venv && source .venv/bin/activate
uv pip install ./py               # builds the Rust extension with maturin
```

For development, `cd py && maturin develop --release` rebuilds in place after you change the Rust.

## 1. Python threads don't help (the GIL)

```bash
python bench/run_threads.py --threads 1
python bench/run_threads.py --threads 8
```

For CPU work, 8 threads take about as long as 1, sometimes longer. Only the thread holding the
GIL (Python's global lock) can run Python code, so the threads take turns.

Optional experiment: Python 3.14 has an officially supported *free-threaded* build without the
GIL (`python3.14t`). It's optional, not the default, so install it separately and see how far
the threads get.

## 2. Multiprocessing, and what it costs

```bash
python bench/run_threads.py --workers 8     # set this to your core count
```

Example output format:

```
mode                             time   speed-up  same output
Python, 1 thread               …s       1.0×  yes
Python, 8 threads              …s       …×    yes
Python, 8 processes            …s       …×    yes
Rust + rayon, 8 threads        …s       …×    yes
```

Processes don't share memory, so every document is pickled, sent to a worker, unpickled, and the
result is sent back the same way. Faster than one thread, but nowhere near N times faster.
Every row must say `same output: yes`.

## 3. Rayon: one word, every core

The whole change from episode 2 is in [`py/src/lib.rs`](py/src/lib.rs):

```diff
+use rayon::prelude::*;
 ...
-        docs.iter()
+        docs.par_iter()
             .map(|doc| fastchunk_core::chunk(doc, size, overlap))
             .collect()
```

`par_iter()` hands the documents to one worker thread per core. When a worker runs out of work,
it steals half of a busy worker's queue (work stealing). The call still releases the GIL with
`py.allow_threads`, so your other Python threads keep running meanwhile. (PyO3 0.26 and later
call this `py.detach`.)

The chunking logic itself lives in [`fastchunk-core/src/lib.rs`](fastchunk-core/src/lib.rs), with
tests that check the parallel and single-core results are identical:

```bash
cd fastchunk-core && cargo test
```

## 4. The honest benchmark

```bash
RAYON_NUM_THREADS=4 python bench/run_cores.py   # one run, 4 cores
python bench/run_cores.py --all                 # 1, 2, 4, 8 cores as a table
```

`--all` prints the total time, the time spent inside Rust only, and the difference: the
**serial part**, where Python hands every string to Rust and gets the chunks back. That part runs
on one core however many you have, so the total stops scaling even when the Rust part keeps
going. Amdahl's law: if a fraction *s* of the job is serial, the speed-up can never exceed 1/*s*.

Your numbers depend on your CPU. Laptops that mix performance and efficiency cores scale less
evenly, and all cores share the same memory bandwidth.

## 5. Back in the API

[`api/app.py`](api/app.py) is episode 2's final app. The import is the same; the chunker now uses
every core.

```bash
cd api
uv venv && uv pip install -r requirements.txt
python ../../ep02-rust-inside-python/data/make_payload.py
.venv/bin/uvicorn app:app --port 8000
# in another terminal:
curl -s -o /dev/null -w "%{time_total}s\n" -X POST localhost:8000/ingest \
     -d @../../ep02-rust-inside-python/data/payload.json
```

The chunking step gets much faster; the whole request improves less, because chunking was only
one slice of it. Profile first.

## 6. Same Rust from JavaScript (napi-rs)

```bash
cd node
npm install
npm run build        # writes index.js, index.d.ts (TypeScript types) and the native .node file
npm run bench
```

```js
const { chunkDocs } = require("./index.js");
const chunks = await chunkDocs(docs, 5, 1);   // a Promise: runs off the event loop, on all cores
```

`bench.mjs` shows the event-loop trap. A timer ticks every millisecond while Rust works.
Example run:

```
sync  (blocks the event loop): 1.16s, timer ticked 1 times
async (AsyncTask + rayon):     0.85s, timer ticked 275 times
same output: yes · 40,000 documents
```

`chunkDocsSync` runs on Node's main thread, so nothing else gets answered until it finishes.
`chunkDocs` uses napi-rs's `AsyncTask`: the work runs on a background thread (where rayon uses
every core) and Node gets a Promise back.

## Versions

Rust 1.80+, rayon 1.10, PyO3 0.22, maturin 1.x, napi-rs 3, Python 3.12, Node.js 20+.
