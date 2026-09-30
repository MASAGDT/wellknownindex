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
2. **URLs** — `site_url` is `https://…` or `null`; protocol URLs are absolute
   `https://` or site-relative `/…`. Plain `http://` is rejected.
3. **Methods** — every `methods_implemented` slug must be a real wiki method
   page (`KNOWN_METHODS`; update it when a method ships).
4. **Auth schemes** — unknown schemes warn, they don't fail. The registry
   learns new schemes.
5. **Duplicates** — rejected against the live registry *and* the queue.
6. **Abuse** — 32KB max body, 10 submissions/hour per IP, markup rejected
   in text fields.

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
  app.py            # the Flask listener: POST /submit, GET /health
  validate.py       # the six validation rules (no Flask dependency)
  review.py         # human CLI: list / show / approve / reject
  requirements.txt
  example-submission.json
  queue/
    pending/        # validated, awaiting human review
    approved/       # approved, markdown generated
    rejected/       # rejected, with reasons
```
