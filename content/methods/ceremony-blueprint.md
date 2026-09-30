---
title: Ceremony Blueprint
section: methods
summary: The validation rules and reference Flask listener for staged registry submissions — the wiki eating its own stage-and-approve cooking.
diagram: ceremony-blueprint
---

# Ceremony Blueprint

**What it is:** the complete design for letting agents *propose* registry entries while humans keep the merge button — stage-and-approve applied to the wiki itself. An agent POSTs a JSON entry to a small Flask listener; the listener validates it against the published schema and the wiki's own rules; valid submissions wait in a queue; a human reviews, approves, and commits. Nothing reaches the registry without a human decision.

**Status:** reference implementation lives in [`staging/`](https://github.com/MASAGDT/wellknownindex/tree/main/staging) in the repo — built for a Raspberry Pi, Flask-first, no paid services.

## The flow

Agent → `POST /submit` → validation → `queue/pending/` → human `review.py approve` → markdown generated → git commit → rebuild → GitHub Pages. Reject → discarded. Expiry was considered and dropped: a submission queue is small enough that explicit reject beats silent rot, and every rejection is a signal about what the validation rules should say.

## The validation rules

These live in `staging/validate.py`, next to the code. The JSON Schema check loads the *published* `schema/registry-entry.json`, so the code and the schema can't drift apart.

1. **Shape.** The submission must validate against the published registry-entry schema: required fields (`title`, `summary`, `site_url`, `protocols`, `auth_schemes`, `methods_implemented`, `cost`, `verified`), types, and the `verified` date format (`YYYY-MM-DD`).
2. **URLs.** `site_url` must be `https://…` or `null`. Protocol URLs must be absolute `https://` or site-relative paths starting with `/`. Plain `http://` is rejected — the registry maps trustworthy lanes.
3. **Methods must exist.** Every `methods_implemented` slug must be a real method page in the wiki. The listener derives the slug list from the wiki's own method pages at startup, so the vocabulary can't drift; unknown slugs fail with the closest matches, so the agent can fix and resubmit.
4. **Auth schemes may be new.** Unknown `auth_schemes` produce warnings, not failures — the registry is supposed to learn new schemes. Unknown *methods* fail; unknown *schemes* teach.
5. **No duplicates.** A submission whose `site_url` or title matches an existing registry entry — or an already-queued submission — is rejected with a pointer to the existing one.
6. **Abuse controls.** 32KB max body. Per-IP rate limiting (10/hour default). Text fields are scanned for markup/script injection and rejected if found.

## The human side

```bash
python3 review.py list              # what's waiting
python3 review.py show <id>         # read the full submission
python3 review.py approve <id>      # → queue/approved/ + generated markdown on stdout
python3 review.py reject <id>       # → discarded, with an optional reason
```

Approval generates the registry markdown (frontmatter from the submission, stub body for the human to flesh out). The human still edits, commits, rebuilds, and pushes — **the script never pushes by itself.** Verification is not authorization, all the way down.

## Hardening notes

- The listener binds `127.0.0.1` by default. In production, put it behind a reverse proxy; don't expose the port.
- Optional `WKI_SUBMIT_TOKEN`: when set, `/submit` requires `Authorization: Bearer <token>`. Open submission is the default posture for a commons, but the token exists for spam waves.
- Rate limits are in-memory and per-process — fine for a Pi, not for a fleet. The README says so honestly.

## Try it: demo mode

The reference listener ships a sandbox (`staging/demo.py`, mounted at `/demo/*`) where anyone can run the full ceremony — preflight, stage, review, approve/reject, status receipts — without touching the real queue. Practice, not preaching:

- `POST /demo/preflight` — validate a submission without staging it.
- `POST /demo/stage` — stage a demo entry; get back `pending` plus a `review_url` and a `status_url`.
- `GET /demo/review?token=…` — inspect the staged record.
- `POST /demo/review/approve?token=…` / `POST /demo/review/reject?token=…` — decide it.
- `GET /demo/status/<id>` — the [status-receipts](/methods/status-receipts/) method, live.

Rules of the sandbox: demo records live in `queue/demo/`, auto-expire after 24 hours, and never publish — every response carries `"demo": true` and `"published_live": false`. Review tokens are single-use and stored hashed. In demo mode the caller plays **both** roles, agent and human, to exercise the mechanics; the policy is unchanged — real submissions still need a human via `review.py`. The demo teaches the mechanics, it doesn't relax the rule.

*Deployment status: the demo is implemented and tested in the repo. It goes live with the listener on the Pi cutover — not on GitHub Pages, which can't run it.*

## Why this shape

Every rule traces back to a wiki principle: rule 1 is the machine-readable primer idea (rules as data); rule 3 keeps the method vocabulary honest; rule 5 is the registry's own no-duplicates hygiene; rule 6 is the Cloudflare field note applied at the application layer. And the human-approves step is [stage-and-approve](/methods/stage-and-approve/) with the wiki as the protected resource. The gardener still gardens — the listener just carries the watering can to the gate.
