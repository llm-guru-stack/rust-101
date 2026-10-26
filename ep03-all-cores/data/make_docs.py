"""Generate a deterministic list of documents: data/docs.json

    python data/make_docs.py              # 10,000 documents (~30 MB)
    python data/make_docs.py --docs 2000  # smaller, for slow machines
"""
import argparse, json, random
from pathlib import Path

WORDS = ("rust python api fast memory thread token chunk model server request response latency cache "
         "vector embedding search index query batch payload compile runtime loop object string bytes "
         "network disk queue worker deploy cluster kernel library function module package benchmark "
         "profile graph engine safety borrow owner lifetime trait struct enum error result value").split()
ENDS = [".", ".", ".", "!", "?"]


def sentence(rng):
    words = [rng.choice(WORDS) for _ in range(rng.randint(6, 18))]
    words[0] = words[0].capitalize()
    return " ".join(words) + rng.choice(ENDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    docs = [" ".join(sentence(rng) for _ in range(rng.randint(20, 60))) for _ in range(a.docs)]
    out = Path(__file__).parent / "docs.json"
    out.write_text(json.dumps(docs))
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {a.docs:,} docs)")


if __name__ == "__main__":
    main()
