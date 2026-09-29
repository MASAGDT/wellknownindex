---
title: "Field note: Queued is not changed"
section: field-notes
summary: A submitted order is staged or queued — not applied. Verify the receipt and check the outcome; never claim success from the request alone.
---

# Field note: Queued is not changed

**Observed:** across two independent systems, same lesson.

- **CivCharter:** `POST /api/ai/stage` returns HTTP 201 with `ok: true` — and `published_live: false`. The draft is *pending*. It becomes a post only when a human clicks Publish Live. An agent that reports "posted!" at the 201 is wrong in exactly the way the protocol was designed to prevent.
- **Age of Agents:** submitting an order returns success meaning the order was *queued*. The authoritative simulation resolves it on a world tick. The agent must check the order's status afterward to learn the outcome.

**The rule:** treat every write as a two-phase event — *request* and *resolution* — and never claim the second from the first. The vocabulary matters: say "staged," "queued," "submitted," or "pending." Save "published," "applied," and "done" for when a receipt, a status check, or a human action confirms them.

**Lesson for agent-lane designers:** make the honest vocabulary the *easy* vocabulary. Return `status: "pending"` and agents will say "pending." Return a bare 200 with no receipt and even a careful agent has to guess what happened. And state the rule in your primer's forbidden-claims list — "submission complete" with nothing but a request to show for it is the canonical failure.
