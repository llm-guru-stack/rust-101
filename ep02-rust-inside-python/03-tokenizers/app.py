import orjson
from fastapi import FastAPI, Request
from fastapi.responses import Response
from tokenizers import Tokenizer

from models import Batch
from chunker import chunk_docs

app = FastAPI()
tok = Tokenizer.from_pretrained("bert-base-uncased")


@app.post("/ingest")
async def ingest(request: Request):
    batch = Batch.model_validate_json(await request.body())
    per_doc = chunk_docs([d.text for d in batch.docs])
    chunks = [c for doc_chunks in per_doc for c in doc_chunks]
    counts = [len(e.ids) for e in tok.encode_batch(chunks)]
    rows, k = [], 0
    for d, doc_chunks in zip(batch.docs, per_doc):
        for i, text in enumerate(doc_chunks):
            rows.append({"doc_id": d.id, "chunk": i, "text": text, "tokens": counts[k], "acl": d.acl})
            k += 1
    result = {"chunks": rows}
    return Response(orjson.dumps(result), media_type="application/json")
