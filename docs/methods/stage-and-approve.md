# Stage and Approve

> The assist-only pattern — the agent stages a draft as a pending record; nothing goes live until the human clicks approve.

HTML: https://masagdt.github.io/wellknownindex/methods/stage-and-approve/
JSON: https://masagdt.github.io/wellknownindex/methods/stage-and-approve.json

---

# Stage and Approve

**What it is:** the agent never publishes directly. It prepares a draft and submits it to a staging endpoint, which creates a *pending* record and returns a one-time review link. The human owner opens the link, reviews the draft, and clicks Publish (or Reject). Only that click creates the public object.

**Why it matters:** it draws the brightest possible line between assistance and authority. The agent can do all the cognitive work — drafting, citing, structuring — while the consequential act stays human. It also kills an entire class of agent failure: the "I posted it" hallucination, because the protocol makes "staged" and "published" visibly different states with different receipts.

## The pattern

1. **A staging endpoint, not a publishing one.** E.g. `POST /api/ai/stage` with the intended action (`post.create`) and payload. The response is `201` with `ok: true`, a pending record id, and an approval URL — never a public URL.
2. **One-time review tokens.** The approval link carries a single-use token; the server stores only a hash and consumes it on publish, reject, or expiry.
3. **Explicit human action.** Publish Live and Reject Draft are the only exits. Expiry publishes nothing.
4. **Distinct states, distinct language.** The API — and the agent's vocabulary — must distinguish *staged* from *published*. Agents are forbidden from claiming publication without a verified live receipt.
5. **Preflight before staging.** Validate route, scope, required fields, and citations before creating the pending record, so the human reviews something already sane.

## Real example

CivCharter's assist-only MCP bridge (`stage_civic_action` → `POST /api/ai/stage`, scope `post.create`) returns `/ai/review?token=…` for the human owner. Posts in its public feed carry the footer "Created by … under AI Access Grant by …" — the provenance is part of the record. Four AI systems have staged through it; every public post was human-approved.

## Design notes

- This is the right default for any *irreversible or public* agent action. For reversible, low-stakes actions inside a simulation, [authoritative tick resolution](/methods/no-simulated-execution/) can play the same role.
- Keep the review UI dead simple: show the exact draft, the citations, and two buttons. Every extra step is a chance for the human to stop paying attention.
- Pending records should expire. A draft that sits for weeks is a liability, not a feature.
