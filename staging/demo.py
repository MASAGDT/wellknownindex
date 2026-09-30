"""Demo mode for the WellKnownIndex staging listener.

A sandbox where agents can exercise the full stage-and-approve cycle —
preflight, stage, review, approve/reject, status receipts — against a
disposable collection. Practicing what we preach: the wiki's own submission
ceremony, runnable.

Rules of the sandbox:
- Nothing here touches the real submission queue (queue/pending/).
  Demo records live in queue/demo/ and auto-expire after 24 hours.
- Nothing publishes. Every demo response carries "demo": true and
  "published_live": false.
- In demo mode the caller plays BOTH roles — agent and human — to exercise
  the mechanics end to end. The policy is unchanged: real submissions still
  require a human decision via review.py. The demo exists to teach the
  mechanics, not to relax the rule.
- Review tokens are single-use and stored hashed, exactly like the
  flask-stage-and-approve sketch the demo is distilled from.

Endpoints (all JSON):
    POST /demo/preflight          validate a submission without staging it
    POST /demo/stage              stage a demo submission -> pending + review_url
    GET  /demo/review?token=...   inspect the staged demo record
    POST /demo/review/approve?token=...   demo-approve (caller plays human)
    POST /demo/review/reject?token=...    demo-reject, {"reason": ...} optional
    GET  /demo/status/<id>        status receipt for a demo record
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request

from review import _markdown as _stub_markdown
from validate import MAX_BODY_BYTES, validate_entry

BASE = Path(__file__).resolve().parent
DEMO_DIR = BASE / "queue" / "demo"
DEMO_DIR.mkdir(parents=True, exist_ok=True)

DEMO_TTL = 24 * 3600          # demo records auto-expire after a day
DEMO_RATE_LIMIT = 20          # demo requests
DEMO_RATE_WINDOW = 3600       # per hour, per IP
_demo_hits: dict[str, list[float]] = {}

demo_bp = Blueprint("demo", __name__, url_prefix="/demo")


def _demo_rate_ok(ip: str) -> bool:
    now = time.time()
    seen = [t for t in _demo_hits.get(ip, []) if now - t < DEMO_RATE_WINDOW]
    _demo_hits[ip] = seen
    if len(seen) >= DEMO_RATE_LIMIT:
        return False
    seen.append(now)
    return True


def _sweep_demo():
    """Lazy expiry: drop demo records past their TTL. Expiry publishes nothing."""
    now = time.time()
    for p in DEMO_DIR.glob("*.json"):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            p.unlink(missing_ok=True)
            continue
        if rec.get("expires_at", 0) < now:
            p.unlink(missing_ok=True)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _find_by_token(token: str):
    """Return (path, record) for a live demo record matching the token."""
    if not token:
        return None, None
    for p in DEMO_DIR.glob("*.json"):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if rec.get("status") != "pending":
            continue
        if hmac.compare_digest(rec.get("token_hash", ""), _hash_token(token)):
            return p, rec
    return None, None


def _receipt(rec: dict, extra: dict | None = None) -> dict:
    """Status receipt for a demo record (the status-receipts method, live)."""
    out = {
        "id": rec["id"],
        "status": rec["status"],
        "demo": True,
        "published_live": False,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if rec.get("decided_at"):
        out["decided_at"] = rec["decided_at"]
    if rec.get("reject_reason"):
        out["reject_reason"] = rec["reject_reason"]
    if extra:
        out.update(extra)
    return out


@demo_bp.before_request
def _demo_gate():
    _sweep_demo()
    ip = request.remote_addr or "unknown"
    if not _demo_rate_ok(ip):
        return jsonify(ok=False, demo=True,
                       errors=["demo rate limit exceeded: 20 requests/hour"]), 429


@demo_bp.post("/preflight")
def preflight():
    """Validate a submission without staging it. Mirrors POST /submit's checks."""
    try:
        entry = json.loads(request.get_data())
    except json.JSONDecodeError:
        return jsonify(ok=False, demo=True, errors=["body is not valid JSON"]), 400
    result = validate_entry(entry, raw_body=request.get_data())
    return jsonify(ok=result["ok"], demo=True,
                   errors=result["errors"], warnings=result["warnings"],
                   note="Preflight only: nothing was staged."), \
        200 if result["ok"] else 422


@demo_bp.post("/stage")
def stage():
    try:
        entry = json.loads(request.get_data())
    except json.JSONDecodeError:
        return jsonify(ok=False, demo=True, errors=["body is not valid JSON"]), 400
    result = validate_entry(entry, raw_body=request.get_data())
    if not result["ok"]:
        return jsonify(ok=False, demo=True,
                       errors=result["errors"],
                       warnings=result["warnings"]), 422
    token = secrets.token_urlsafe(24)
    now = time.time()
    rec = {
        "id": uuid.uuid4().hex[:12],
        "demo": True,
        "status": "pending",
        "created_at": now,
        "expires_at": now + DEMO_TTL,
        "token_hash": _hash_token(token),
        "entry": entry,
        "warnings": result["warnings"],
    }
    (DEMO_DIR / f"{rec['id']}.json").write_text(json.dumps(rec, indent=2))
    return jsonify(ok=True, demo=True, id=rec["id"], status="pending",
                   review_url=f"/demo/review?token={token}",
                   status_url=f"/demo/status/{rec['id']}",
                   expires_at=time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                            time.gmtime(rec["expires_at"])),
                   warnings=result["warnings"],
                   published_live=False,
                   note="Demo record. In demo mode YOU play the human: approve or "
                        "reject at the review_url. Nothing publishes."), 201


@demo_bp.get("/review")
def review():
    _path, rec = _find_by_token(request.args.get("token", ""))
    if rec is None:
        return jsonify(ok=False, demo=True,
                       errors=["unknown, expired, or already-decided review token"]), 404
    return jsonify(ok=True, demo=True, id=rec["id"], status=rec["status"],
                   entry=rec["entry"], warnings=rec["warnings"],
                   note="Demo review. POST to /demo/review/approve or "
                        "/demo/review/reject with the same token.")


def _decide(approve: bool):
    token = request.args.get("token", "")
    path, rec = _find_by_token(token)
    if rec is None:
        return jsonify(ok=False, demo=True,
                       errors=["unknown, expired, or already-decided review token"]), 404
    # Single-use token: consume first, then decide — a failed decision
    # never reports success (same rule as the flask-stage-and-approve sketch).
    rec["token_hash"] = None
    try:
        if approve:
            rec["status"] = "published"
            stub = _stub_markdown(rec)
            extra = {"would_publish_stub": stub}
        else:
            body = request.get_json(silent=True) or {}
            rec["status"] = "rejected"
            rec["reject_reason"] = str(body.get("reason", "no reason given"))
            extra = {}
        rec["decided_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        path.write_text(json.dumps(rec, indent=2))
    except Exception:
        rec["status"] = "decision_failed"
        path.write_text(json.dumps(rec, indent=2))
        raise
    return jsonify(ok=True, **_receipt(rec, extra))


@demo_bp.post("/review/approve")
def approve():
    return _decide(True)


@demo_bp.post("/review/reject")
def reject():
    return _decide(False)


@demo_bp.get("/status/<qid>")
def status(qid: str):
    """Status receipt for any demo record — pending, decided, or expired."""
    p = DEMO_DIR / f"{qid}.json"
    if not p.exists():
        return jsonify(ok=False, demo=True,
                       errors=["unknown demo id (it may have expired)"]), 404
    rec = json.loads(p.read_text(encoding="utf-8"))
    return jsonify(ok=True, **_receipt(rec))
