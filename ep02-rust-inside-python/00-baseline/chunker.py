"""Pure-Python chunking and token counting (the slow baseline).

Rules (same as the Rust version in 04-pyo3-chunker):
  * split a document into sentences, each ending in . ! or ?
  * group `size` sentences per chunk, overlapping by `overlap` sentences
"""
from transformers import BertTokenizer

# The "slow" BERT tokenizer is written in pure Python (it is what use_fast=False gives you).
slow_tokenize = BertTokenizer.from_pretrained("bert-base-uncased").encode


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


def count_tokens(chunks: list[str]) -> list[int]:
    counts = []
    for chunk in chunks:
        pieces = slow_tokenize(chunk)   # pure Python
        counts.append(len(pieces))
    return counts
