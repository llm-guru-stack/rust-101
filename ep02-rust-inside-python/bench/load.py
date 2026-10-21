"""Send the payload through one step's app in-process, so py-spy can profile it.

    cd 00-baseline
    pip install py-spy httpx
    py-spy record -o profile.svg -- python ../bench/load.py .
"""
import sys
from pathlib import Path

step = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
sys.path.insert(0, str(step))

from fastapi.testclient import TestClient  # noqa: E402
from app import app  # noqa: E402

body = (Path(__file__).resolve().parent.parent / "data" / "payload.json").read_bytes()
client = TestClient(app)
for i in range(3):
    r = client.post("/ingest", content=body)
    r.raise_for_status()
    print(f"request {i + 1}: {len(r.content) / 1e6:.1f} MB back")
