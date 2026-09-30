# Flask Stage-and-Approve

> A Flask-first reference for staged-write endpoints — preflight, stage, review, approve — distilled from CivCharter's /api/ai/* lane.

HTML: https://masagdt.github.io/wellknownindex/methods/flask-stage-and-approve/
JSON: https://masagdt.github.io/wellknownindex/methods/flask-stage-and-approve.json

---

# Flask Stage-and-Approve

**What it is:** the reference endpoint design for the [stage-and-approve](/methods/stage-and-approve/) pattern, written Flask-first — because the reference implementation (CivCharter) runs Flask on a Raspberry Pi, and most sites climbing the [retrofit ladder](/methods/retrofit-ladder/) start from something small.

**Distilled from:** CivCharter's `/api/ai/*` lane — `POST /api/ai/preflight`, `POST /api/ai/stage`, `/ai/review?token=…` — which has staged posts for four different AI systems without a single unauthorized publish.

## The five routes

| Route | Who calls it | What it does |
|---|---|---|
| `GET /ai/primer` | Agent | Serves the [primer file](/methods/primer-file-format/) (JSON). Also advertised at `/.well-known/ai-primer.json`. |
| `POST /api/ai/preflight` | Agent | Validates intent, scope, required fields, citations. Returns pass/fail **without changing any state**. |
| `POST /api/ai/stage` | Agent | Creates the pending record. `201`, `ok: true`, `published_live: false`, one-time review URL. |
| `GET /ai/review?token=…` | Human | Review page showing the exact draft, citations, and two buttons. Token is single-use, stored hashed. |
| `POST /ai/review/approve` (or `/reject`) | Human | The only exits. **Requires the human's login session; agent credentials get 403.** |

## Request and response shapes

Preflight — the agent checks before it stages:

```http
POST /api/ai/preflight
Authorization: Bearer <agent-session>

{"intent": "post.create",
 "payload": {"title": "...", "body": "..."},
 "citations": [{"section": "Article V, Section 2"}]}
```
```json
{"ok": true, "reasons": []}
```
```json
{"ok": false, "reasons": ["citations must reference ratified charter sections"]}
```

Stage — the pending record is born unpublished:

```http
POST /api/ai/stage
Authorization: Bearer <agent-session>

{"intent": "post.create",
 "payload": {"title": "...", "body": "..."},
 "citations": [{"section": "Article V, Section 2"}]}
```
```json
{"ok": true, "id": "9f2c…", "status": "pending",
 "review_url": "/ai/review?token=…", "published_live": false}
```

Note `published_live: false` in the success response. The agent's vocabulary — and yours — must keep *staged* and *published* as visibly different states. (See [No Simulated Execution](/methods/no-simulated-execution/).)

## The separation-of-powers rule

This is the load-bearing wall: **the approve endpoint must require the human's login session, and must reject agent credentials outright.** An agent that can approve its own staged work has no lane — it has a publishing API with extra steps. CivCharter's review page is human-session-only; the agent that staged the draft cannot touch it.

## The pending record (server side)

```python
{
  "id": "9f2c…",            # public handle
  "intent": "post.create",
  "payload": {...},         # the exact draft
  "citations": [...],
  "scopes_used": ["post.create"],
  "agent_id": "…",          # which agent staged it
  "grant_id": "…",          # which human grant authorized it
  "status": "pending",      # pending | published | rejected | expired
  "created_at": …,
  "expires_at": …,          # pending drafts expire; expiry publishes nothing
  "token_hash": "…",        # sha256 of the one-time review token
}
```

## Minimal Flask sketch

Illustrative — use a real store and your session machinery in production:

```python
from flask import Flask, request, jsonify, session, abort
import secrets, hashlib, time

app = Flask(__name__)
PENDING = {}  # replace with a real store

def _hash(t): return hashlib.sha256(t.encode()).hexdigest()

@app.post("/api/ai/preflight")
def preflight():
    data = request.get_json(force=True)
    reasons = run_preflight(data, agent_scopes(request))
    return jsonify(ok=not reasons, reasons=reasons)

@app.post("/api/ai/stage")
def stage():
    data = request.get_json(force=True)
    reasons = run_preflight(data, agent_scopes(request))
    if reasons:
        return jsonify(ok=False, reasons=reasons), 422
    token = secrets.token_urlsafe(32)
    rec = {"id": secrets.token_hex(8), "intent": data["intent"],
           "payload": data["payload"], "status": "pending",
           "created_at": time.time(), "expires_at": time.time() + 7*86400,
           "token_hash": _hash(token), "agent_id": agent_id(request)}
    PENDING[rec["id"]] = rec
    return jsonify(ok=True, id=rec["id"], status="pending",
                   review_url=f"/ai/review?token={token}",
                   published_live=False), 201

@app.post("/ai/review/approve")
def approve():
    if "human_user_id" not in session:
        abort(401)  # humans only: log in first
    if is_agent_credential(request):
        abort(403)  # agents cannot approve their own staged work
    rec = consume_token(request.args.get("token"))  # single-use, hashed
    try:
        live_url = publish(rec)
    except Exception:
        # The approval token is already spent. Never report "published"
        # for a publish that failed: park the record so a human can
        # re-approve, and let the error propagate.
        rec["status"] = "publish_failed"
        raise
    rec["status"] = "published"
    return jsonify(ok=True, live_url=live_url)
```

Run a sweeper (cron or thread) that marks unreviewed records `expired` past `expires_at`. Expiry publishes nothing — that's the whole point. This expiry rule is for staging lanes holding draft writes; the [Ceremony Blueprint](/methods/ceremony-blueprint/) submission queue is the deliberate exception — proposals are never auto-expired, because silently dropping someone's submission is worse than holding it.

## Field note from production

CivCharter's lane sits behind Cloudflare, which 403s Python's default `urllib` user-agent on `/api/ai/*` while a browser-like UA passes. Your preflight client should set an honest, identifiable user-agent — and your docs should say so. (See the [Cloudflare user-agent field note](/field-notes/cloudflare-user-agent/).)
