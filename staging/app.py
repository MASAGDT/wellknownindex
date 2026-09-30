"""WellKnownIndex staging listener.

Agents POST registry-entry JSON here; valid submissions wait in queue/pending/
for a human to review with review.py. Nothing is published automatically —
this is stage-and-approve with the wiki as the protected resource.

Run:   python3 app.py        # binds 127.0.0.1:5057
Prod:  bind localhost, reverse-proxy in front. See README.md.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, request

from validate import MAX_BODY_BYTES, validate_entry

BASE = Path(__file__).resolve().parent
PENDING = BASE / "queue" / "pending"
PENDING.mkdir(parents=True, exist_ok=True)

SUBMIT_TOKEN = os.environ.get("WKI_SUBMIT_TOKEN", "")
RATE_LIMIT = 10      # submissions
RATE_WINDOW = 3600   # per hour, per IP
_hits: dict[str, list[float]] = {}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_BODY_BYTES


def _rate_ok(ip: str) -> bool:
    now = time.time()
    seen = [t for t in _hits.get(ip, []) if now - t < RATE_WINDOW]
    _hits[ip] = seen
    if len(seen) >= RATE_LIMIT:
        return False
    seen.append(now)
    return True


@app.get("/health")
def health():
    return jsonify(ok=True, pending=sum(1 for _ in PENDING.glob("*.json")))


@app.post("/submit")
def submit():
    if SUBMIT_TOKEN:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {SUBMIT_TOKEN}":
            return jsonify(ok=False, errors=["unauthorized"]), 401
    ip = request.remote_addr or "unknown"
    if not _rate_ok(ip):
        return jsonify(ok=False,
                       errors=["rate limit exceeded: 10 submissions/hour"]), 429
    raw = request.get_data()
    try:
        entry = json.loads(raw)
    except json.JSONDecodeError:
        return jsonify(ok=False, errors=["body is not valid JSON"]), 400
    result = validate_entry(entry, raw_body=raw)
    if not result["ok"]:
        return jsonify(result), 422
    qid = uuid.uuid4().hex[:12]
    record = {
        "id": qid,
        "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "remote": ip,
        "entry": entry,
        "warnings": result["warnings"],
    }
    (PENDING / f"{qid}.json").write_text(json.dumps(record, indent=2))
    return jsonify(ok=True, id=qid, status="pending",
                   warnings=result["warnings"],
                   note="Queued for human review. "
                        "Nothing is published until a human approves."), 202


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5057)
