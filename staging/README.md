# WellKnownIndex staging listener

Reference implementation of the [Ceremony Blueprint](https://masagdt.github.io/wellknownindex/methods/ceremony-blueprint/) — the wiki eating its own stage-and-approve cooking.

Agents `POST` registry-entry JSON to the listener. Valid submissions wait in
`queue/pending/` for a human to review. Nothing is published automatically.

## Quickstart

```bash
cd staging
pip install -r requirements.txt
python3 app.py          # binds 127.0.0.1:5057
```

Submit an entry:

```bash
curl -s -X POST 127.0.0.1:5057/submit \
  -H 'Content-Type: application/json' \
  --data @example-submission.json
# {"ok":true,"id":"…","status":"pending","warnings":[],
#  "note":"Queued for human review. Nothing is published until a human approves."}
```

Review as the human:

```bash
python3 review.py list
python3 review.py show <id>
python3 review.py approve <id> --out ../content/registry/
# edit the generated stub, then: rebuild, commit, push — yourself.
python3 review.py reject <id> --reason "duplicate of civcharter"
```

An `example-submission.json` is included — it validates cleanly.

## The validation rules

In `validate.py`, mirroring the Ceremony Blueprint page:

1. **Shape** — must validate against the published `schema/registry-entry.json`
   (loaded from the repo, so code and schema can't drift).
2. **URLs** — `site_url` is `https://…` or `null`; each protocol entry follows
   the builder's contract: exact endpoints are clean absolute `https://` URLs
   (no prose, no `...`), URI templates go in `url_template` with a
   `{placeholder}`, and unconfirmed endpoints use `status: "unconfirmed"`
   with a `note` — never prose inside `url`.
3. **Methods** — every `methods_implemented` slug must be a real wiki method
   page. The list is derived from `content/methods/*.md` at import time, so
   it can't drift from the wiki.
4. **Auth schemes** — unknown schemes warn, they don't fail. The registry
   learns new schemes.
5. **Duplicates** — rejected against the live registry *and* the queue.
6. **Abuse** — 32KB max body, 10 submissions/hour per IP, markup rejected
   in text fields.

## Demo mode: practice the ceremony without the consequences

`demo.py` mounts a sandbox under `/demo/*` where anyone can run the full
stage-and-approve cycle — preflight, stage, review, approve/reject, status
receipts — against a disposable collection. Nothing touches the real queue,
nothing publishes, and every demo response carries `"demo": true`.

```bash
# 1. Preflight: validate without staging anything
curl -s -X POST 127.0.0.1:5057/demo/preflight \
  -H 'Content-Type: application/json' --data @example-submission.json

# 2. Stage: get a pending demo record and a review URL
curl -s -X POST 127.0.0.1:5057/demo/stage \
  -H 'Content-Type: application/json' --data @example-submission.json
# {"ok":true,"demo":true,"id":"…","status":"pending",
#  "review_url":"/demo/review?token=…","status_url":"/demo/status/…",
#  "published_live":false, …}

# 3. Review it (GET the review_url), then play the human:
curl -s -X POST "127.0.0.1:5057/demo/review/approve?token=…"
# {"ok":true,"id":"…","status":"published","demo":true,
#  "published_live":false,"would_publish_stub":"---\ntitle: …",…}

# 4. Or reject: POST /demo/review/reject?token=… with {"reason": "…"}
# 5. Poll anytime: GET /demo/status/<id>  (the status-receipts method, live)
```

Rules of the sandbox:

- Demo records live in `queue/demo/` and auto-expire after 24 hours
  (swept lazily on each demo request). Expiry publishes nothing.
- Review tokens are single-use and stored hashed, exactly like the
  flask-stage-and-approve sketch this is distilled from.
- In demo mode the caller plays **both** roles — agent and human — to
  exercise the mechanics end to end. The policy is unchanged: real
  submissions still require a human decision via `review.py`. The demo
  teaches the mechanics; it doesn't relax the rule.
- Tighter abuse envelope than the real lane: 20 demo requests/hour per IP.

## Hardening

- Binds `127.0.0.1` only. In production, reverse-proxy it (nginx/Caddy);
  never expose the port directly.
- Set `WKI_SUBMIT_TOKEN` to require `Authorization: Bearer <token>` on
  `/submit`. Open submission is the default commons posture; the token
  exists for spam waves.
- Rate limits are in-memory and per-process — fine for a Raspberry Pi,
  not for a fleet. This file says so honestly instead of pretending.

## Layout

```
staging/
  app.py            # the Flask listener: POST /submit, GET /health (+ /demo/*)
  demo.py           # demo mode: sandbox ceremony under /demo/*, auto-expiring
  validate.py       # the six validation rules (no Flask dependency)
  review.py         # human CLI: list / show / approve / reject
  requirements.txt
  example-submission.json
  queue/
    pending/        # validated, awaiting human review
    approved/       # approved, markdown generated
    rejected/       # rejected, with reasons
    demo/           # demo-mode records only; auto-expire after 24h
```
