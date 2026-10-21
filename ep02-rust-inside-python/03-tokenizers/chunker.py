"""Pure-Python chunking (token counting now happens in HF tokenizers).

Rules (same as the Rust version in 04-pyo3-chunker):
  * split a document into sentences, each ending in . ! or ?
  * group `size` sentences per chunk, overlapping by `overlap` sentences
"""
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


def chunk_docs(texts: list[str], size: int = 5, overlap: int = 1) -> list[list[str]]:
    step = max(size - overlap, 1)
    out = []
    for doc in texts:
        sents = split_sentences(doc)
        chunks = []
        for i in range(0, len(sents), step):
            chunks.append("".join(sents[i:i + size]))
        out.append(chunks)
    return out
