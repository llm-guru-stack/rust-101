# Episode 2: Speed up Python with Rust (without rewriting your app)

One slow Python API, made faster one change at a time. Three changes use libraries that
already have Rust inside. The fourth is about 20 lines of Rust that we write ourselves.
The app stays Python the whole way.

Each numbered folder is the **complete app** with exactly **one change** from the folder
before it, so you can diff any two steps and see the whole fix:

```bash
diff 00-baseline/app.py 01-orjson/app.py
```

## The app

`POST /ingest` is the kind of endpoint an intranet search platform runs before embedding:

1. receive a big JSON payload of documents (text plus metadata and an access-control list),
2. validate it,
3. split each document into sentences and group them into overlapping chunks,
4. count the tokens in every chunk (BERT tokenizer),
5. send back every chunk as JSON.

## Run everything

```bash
python data/make_payload.py     # 2,000 documents, about 7 MB (use --docs 500 on slow machines)
python bench/run_all.py         # builds each step in its own .venv, times it, writes results.md
```

`run_all.py` sends the same payload to every step, takes the median of 5 requests after a
warm-up, and checks that every step returns **exactly the same chunks and token counts**.
A speed-up only counts if the answer is identical.

## The steps

| Folder | What changes | Rust inside? |
| --- | --- | --- |
| `00-baseline` | Pure Python: `json`, Pydantic v1, a hand-written chunking loop, the pure-Python BERT tokenizer | No |
| `01-orjson` | `json` → `orjson` | orjson is written in Rust |
| `02-pydantic-v2` | Pydantic v1 → v2, and `model_validate_json` parses and validates in one call | pydantic-core is written in Rust |
| `03-tokenizers` | The pure-Python tokenizer → Hugging Face `tokenizers`, one `encode_batch` call | tokenizers is written in Rust |
| `04-pyo3-chunker` | Our chunking loop → `fastchunk`, our own Rust extension | Yes, we wrote it |
| `05-the-trap` | Not an app: two scripts that show the PyO3 traps | Yes |
| `06-io-bound` | Step 04 plus a (simulated) LLM API call | Doesn't matter: it's waiting |

### 00 → 01: orjson

```diff
-import json
+import orjson
 ...
-    batch = Batch.parse_obj(json.loads(await request.body()))
+    batch = Batch.parse_obj(orjson.loads(await request.body()))
 ...
-    return Response(json.dumps(result), media_type="application/json")
+    return Response(orjson.dumps(result), media_type="application/json")
```

orjson helps most when **writing** large responses made of many small objects. Reading gets
a smaller boost.

### 01 → 02: Pydantic v2

```diff
-    batch = Batch.parse_obj(orjson.loads(await request.body()))
+    batch = Batch.model_validate_json(await request.body())
```

`models.py` is the same apart from the version comment. Pydantic v2's validation engine,
`pydantic-core`, is compiled Rust. Check for yourself:

```bash
python -c "import pydantic_core; print(pydantic_core._pydantic_core.__file__)"
# .../pydantic_core/_pydantic_core.cpython-312-x86_64-linux-gnu.so
```

### 02 → 03: Hugging Face tokenizers

```diff
-from chunker import chunk_docs, count_tokens
+from chunker import chunk_docs
+from tokenizers import Tokenizer
+tok = Tokenizer.from_pretrained("bert-base-uncased")
 ...
-    counts = count_tokens(chunks)
+    counts = [len(e.ids) for e in tok.encode_batch(chunks)]
```

Note the **whole batch in one call**. That matters again in step 05.

### 03 → 04: our own Rust (PyO3 + maturin)

The chunker is our own logic (split on `.` `!` `?`, 5 sentences per chunk, 1 sentence of
overlap), so no library has it. [`04-pyo3-chunker/fastchunk/src/lib.rs`](04-pyo3-chunker/fastchunk/src/lib.rs)
is the whole extension:

```rust
use pyo3::prelude::*;

#[pyfunction]
fn chunk_docs(py: Python<'_>, docs: Vec<String>, size: usize, overlap: usize) -> Vec<Vec<String>> {
    py.allow_threads(|| {
        docs.iter().map(|doc| {
            let sents: Vec<&str> = doc.split_inclusive(&['.', '!', '?'][..]).collect();
            let step = size.saturating_sub(overlap).max(1);
            (0..sents.len()).step_by(step)
                .map(|i| sents[i..(i + size).min(sents.len())].concat())
                .collect()
        }).collect()
    })
}

#[pymodule]
fn fastchunk(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(chunk_docs, m)?)
}
```

Build it and use it like any Python package:

```bash
cd 04-pyo3-chunker
uv venv && source .venv/bin/activate
uv pip install maturin
cd fastchunk && maturin develop --release && cd ..
python -c "import fastchunk; print(fastchunk.chunk_docs(['A. B. C.'], 2, 1))"
# [['A. B.', ' B. C.', ' C.']]
```

`py.allow_threads` releases Python's global lock (the GIL) while Rust works. In PyO3
0.26 and later this method is called `py.detach`.

### 05: the two traps

```bash
cd 05-the-trap
uv venv && uv pip install ./trapchunk
.venv/bin/python trap.py
```

**Trap 1, the GIL.** A background Python thread ticks every millisecond while Rust chunks
the payload 30 times. With the GIL held, the thread is frozen for the whole call. With
`allow_threads`, it keeps ticking. Example run:

```
holds the GIL   : 0.58s of Rust work, background thread ticked 1 times
releases the GIL: 0.58s of Rust work, background thread ticked 499 times
```

**Trap 2, the toll.** Keeping the Python loop and calling Rust once per word is *slower than
plain Python*, because every crossing costs something. Handing Rust whole documents fixes it.
Example run:

```
version 1: Python loop, Rust once per word (958,869 calls): 0.074s
version 2: Rust gets all documents (1 call):            0.021s
plain Python, no Rust at all:                           0.057s
```

Crossing once per *document* barely matters, because each call already does plenty of work.
The rule: hand Rust big chunks of work.

### 06: when Rust won't help

Step 04 plus `await complete(...)`, a stand-in for an LLM API call that just waits 1.5 s
(set `FAKE_LLM_LATENCY` to change it). Profile it and the waiting dwarfs everything else.
Rust waits at exactly the same speed as Python.

## Profile it yourself (py-spy)

```bash
cd 00-baseline
uv venv && uv pip install -r requirements.txt py-spy httpx
source .venv/bin/activate
py-spy record -o profile.svg -- python ../bench/load.py .
```

Open `profile.svg` in a browser. On macOS, py-spy needs `sudo`. In some containers it needs
the `SYS_PTRACE` capability.

## JavaScript tooling race

```bash
cd js-tooling
npm install
npm run make-code     # writes 1,200 small modules to src/
npm run bench
```

Example run on one virtual CPU (the gap grows with more cores):

```
Linting
eslint (JavaScript)      5.37s
oxlint (Rust)            0.91s
Formatting check
prettier (JavaScript)    6.09s
biome (Rust)             0.41s
```

## Bonus: pandas vs Polars

```bash
cd bonus-polars
uv venv && uv pip install -r requirements.txt && .venv/bin/python compare.py
```

Polars is multi-threaded, so most of its advantage comes from extra cores. On a single
virtual CPU the two came out even (pandas 2.72 s, Polars 2.85 s). Run it on your laptop.

## Example results

One run of `bench/run_all.py --n 3` on a **single virtual CPU** in a cloud sandbox
(Python 3.12). Your machine will differ, so run it yourself:

| Step | Median per request | Speed-up vs baseline |
| --- | --- | --- |
| baseline | 12.83 s | 1.00× |
| + orjson | 12.47 s | 1.03× |
| + Pydantic v2 | 11.91 s | 1.08× |
| + HF tokenizers | 3.43 s | 3.74× |
| + PyO3 chunker | 3.25 s | 3.95× |
| + a 1.5 s LLM call (06) | 5.04 s | 2.55× |

20,719 chunks per request, identical output at every step.

What this run shows:

- **Profile first.** Most of the baseline's time is token counting, so the tokenizer swap is
  the big win. orjson and Pydantic v2 are free but small here.
- **Our Rust chunker made the chunking step itself about 8× faster** (0.16 s → 0.02 s in
  isolation), but chunking was a small slice of the request, so the end-to-end gain is small.
  A Rust rewrite only pays off as much as the share of time it replaces.
- **Waiting can't be compiled away.** Adding a 1.5 s API call cost 1.5 s, whatever the code
  around it is written in.

## Versions used

Python 3.12, FastAPI 0.110.3, Pydantic 1.10.17 / 2.8.2, orjson 3.10.7, tokenizers 0.19.1,
transformers 4.44.2 (only for the pure-Python baseline tokenizer), PyO3 0.22.6, maturin 1.x.
