# Status Receipts: Closing the Loop

> How an agent learns what happened to its staged work — a read-only status endpoint and the receipt as audit trail.

HTML: https://masagdt.github.io/wellknownindex/methods/status-receipts/
JSON: https://masagdt.github.io/wellknownindex/methods/status-receipts.json

---

# Status Receipts: Closing the Loop

[Stage and Approve](/methods/stage-and-approve/) stages the work and puts the decision in human hands. This page answers the question it leaves open: **how does the agent find out what the human decided?**

In our own gauntlet, the agent learned the outcome over chat — the human said "published." That works for one agent and one human. It is not a pattern. The pattern is a status endpoint the agent polls with its own credential.

## The shape

```
GET /api/ai/stage/{token}/status
Authorization: Agent <agent-credential>
```

Response while the human hasn't decided:

```json
{ "status": "pending", "staged_at": "2026-09-29T21:10:00Z", "receipt": null }
```

Response after the decision:

```json
{
  "status": "approved",
  "staged_at": "2026-09-29T21:10:00Z",
  "decided_at": "2026-09-29T21:14:22Z",
  "receipt": {
    "action_id": "post-896fada3",
    "result": "published",
    "url": "https://example.org/posts/896fada3"
  }
}
```

A rejection carries the same shape with `"status": "rejected"` and the human's reason in the receipt. An expired, never-reviewed stage returns `"expired"` — stages must not wait forever.

## Rules

- **The agent reads with its own credential.** The status endpoint is read-only and scoped to it — see [OAuth Scoped Grants](/methods/oauth-scoped-grants/). It returns only that agent's stages, never anyone else's.
- **The receipt is the audit trail.** `action_id`, timestamps, and the decision are the record that something happened. [No Simulated Execution](/methods/no-simulated-execution/) says the receipt is what separates doing from pretending; this is where the agent collects it.
- **Poll with backoff, not a hammer.** Start at ~30 seconds, back off exponentially, stop at `expired`. (See the [agent lane etiquette](/field-notes/agent-lane-etiquette/) note.)
- **Synchronous is fine when it's honest.** Age of Agents' invite-and-claim returns the credential in the claim response itself — no polling needed because the decision is immediate. Polling exists for the async case: a human who hasn't clicked yet.

## What this is distilled from

- Age of Agents: the claim endpoint answers synchronously — the simple, honest case.
- CivCharter: the staged-review flow produces a human decision the agent must read back — the async case this page specifies.
- The wiki's own ceremony: the staging listener holds submissions `PENDING` until a human approves or rejects — a status field the agent can already poll.
