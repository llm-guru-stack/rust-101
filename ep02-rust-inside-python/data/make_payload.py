"""Generate a deterministic test payload: data/payload.json

Documents look like what an intranet search ingester receives: text plus metadata and an ACL.

    python data/make_payload.py            # 2,000 documents (~5 MB)
    python data/make_payload.py --docs 500 # smaller, for slow machines
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
    ap.add_argument("--docs", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    groups = [f"group-{g}" for g in range(40)]
    docs = []
    for i in range(args.docs):
        docs.append({
            "id": f"doc-{i:05d}",
            "title": sentence(rng)[:-1],
            "text": " ".join(sentence(rng) for _ in range(rng.randint(20, 60))),
            "source": rng.choice(["confluence", "sharepoint", "gdrive", "intranet"]),
            "url": f"https://intranet.example.com/docs/{i}",
            "author": f"user{rng.randint(1, 500)}@example.com",
            "created_at": f"2026-{rng.randint(1, 9):02d}-{rng.randint(1, 28):02d}T{rng.randint(0, 23):02d}:00:00Z",
            "tags": rng.sample(WORDS, 4),
            "acl": rng.sample(groups, rng.randint(2, 6)),
        })
    out = Path(__file__).parent / "payload.json"
    out.write_text(json.dumps({"docs": docs}))
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {args.docs} docs)")


if __name__ == "__main__":
    main()
