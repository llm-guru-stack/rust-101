"""The pure-Python chunker from episode 2 (same rules as the Rust one)."""


def split_sentences(doc: str) -> list[str]:
    sents, cur = [], []
    for ch in doc:
        cur.append(ch)
        if ch in ".!?":
            sents.append("".join(cur))
            cur = []
    if cur:
        sents.append("".join(cur))
    return sents


def chunk_doc(doc: str, size: int = 5, overlap: int = 1) -> list[str]:
    step = max(size - overlap, 1)
    sents = split_sentences(doc)
    return ["".join(sents[i:i + size]) for i in range(0, len(sents), step)]
