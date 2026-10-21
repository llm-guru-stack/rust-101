import orjson

from fastapi import FastAPI, Request
from fastapi.responses import Response

from models import Batch
from chunker import chunk_docs, count_tokens

app = FastAPI()


@app.post("/ingest")
async def ingest(request: Request):
    batch = Batch.parse_obj(orjson.loads(await request.body()))
    per_doc = chunk_docs([d.text for d in batch.docs])
    chunks = [c for doc_chunks in per_doc for c in doc_chunks]
    counts = count_tokens(chunks)
    rows, k = [], 0
    for d, doc_chunks in zip(batch.docs, per_doc):
        for i, text in enumerate(doc_chunks):
            rows.append({"doc_id": d.id, "chunk": i, "text": text, "tokens": counts[k], "acl": d.acl})
            k += 1
    result = {"chunks": rows}
    return Response(orjson.dumps(result), media_type="application/json")
