# rust-101

Code for **Rust 101**, the series on the **LLM Guru** YouTube channel.
Every episode has its own folder, and every folder runs on its own.

> AI, explained from the inside.

## Episodes

| Episode | Folder | What you build |
| --- | --- | --- |
| 1. Why Rust is fast | *(no code)* | The ideas: no garbage collector, compiled ahead of time, zero-cost abstractions |
| 2. Speed up Python with Rust | [`ep02-rust-inside-python`](ep02-rust-inside-python) | A slow FastAPI ingestion API, made faster one change at a time, ending with your own Rust extension (PyO3 + maturin) |
| 3. Use every CPU core | [`ep03-all-cores`](ep03-all-cores) | Python threads vs multiprocessing vs Rust + rayon, Amdahl's law, and the same Rust called from Node.js (napi-rs) |
| 4. Ownership and the borrow checker | *coming next* | The rules behind "it doesn't compile", explained with pictures |

## What you need

| Tool | Why | Install |
| --- | --- | --- |
| Python 3.12 | The apps | [python.org](https://www.python.org/downloads/) |
| uv | One virtual environment per step, fast installs | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Rust | Building the PyO3 extensions | `curl https://sh.rustup.rs -sSf \| sh` |
| Node.js 20+ | Only for the JavaScript tooling race | [nodejs.org](https://nodejs.org) |

## Quick start

```bash
git clone https://github.com/llm-guru-stack/rust-101.git
cd rust-101/ep02-rust-inside-python
python data/make_payload.py      # creates the test payload
python bench/run_all.py          # runs every step and writes results.md
```

## Repository layout

```
rust-101/
├── README.md
├── LICENSE
├── .gitignore
├── ep02-rust-inside-python/
│   ├── README.md               # the full walkthrough for episode 2
│   ├── data/make_payload.py    # deterministic test payload
│   ├── bench/run_all.py        # runs every step, checks outputs match, writes results.md
│   ├── bench/load.py           # in-process load for py-spy
│   ├── 00-baseline/            # pure Python
│   ├── 01-orjson/              # + orjson
│   ├── 02-pydantic-v2/         # + Pydantic v2
│   ├── 03-tokenizers/          # + Hugging Face tokenizers
│   ├── 04-pyo3-chunker/        # + our own Rust chunker (PyO3 + maturin)
│   ├── 05-the-trap/            # the GIL trap and the per-call toll
│   ├── 06-io-bound/            # when Rust can't help
│   ├── js-tooling/             # ESLint vs Oxlint, Prettier vs Biome
│   └── bonus-polars/           # pandas vs Polars
└── ep03-all-cores/
    ├── README.md               # the full walkthrough for episode 3
    ├── data/make_docs.py       # test documents
    ├── fastchunk-core/         # plain Rust chunking logic (rayon)
    ├── py/                     # PyO3 wrapper (Python)
    ├── node/                   # napi-rs wrapper (Node.js)
    ├── bench/                  # threads vs processes vs rayon; core scaling
    └── api/                    # episode 2's app with the parallel chunker
```

## A note on numbers

Benchmarks depend on your CPU, core count, OS and Python version. Every number in the
videos comes from `bench/run_all.py`, so run it on your own machine and compare.
If you get very different results, open an issue with your `results.md`.

## License

MIT. See [LICENSE](LICENSE).
