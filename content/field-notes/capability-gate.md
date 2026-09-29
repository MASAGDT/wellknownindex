---
title: "Field note: The capability gate"
section: field-notes
summary: A scope proves authorization MAY exist. It does not prove the agent can execute the action. Check capability, not just permission.
---

# Field note: The capability gate

**Observed:** 2026-09-29, while running an AI Access Grant flow with scopes including `post.create`.

The grant *authorized* `post.create`. But authorization and executability are different questions. Before attempting the write, the sane check is a capability gate — can the agent, from its actual environment, do all of the following?

- Open the grant/bootstrap safely and parse the machine-readable session material
- Keep raw grant tokens, bearer tokens, and authorization headers out of normal chat
- Make authenticated HTTPS requests itself (not merely describe commands)
- Call discovery and run preflight for the intended action
- Inspect the preflight verdict (`valid`, `safe_to_execute`)
- Submit only after preflight succeeds, and verify `ok: true` plus a receipt

**If any check fails, downgrade lanes** — don't push through. The honest fallbacks, in order: stage the draft for human approval, generate a human-runnable command packet, or drop to public-spec guidance. What the agent must *not* do is narrate a confident payload and call it execution.

**Lesson for agent-lane designers:** put the capability gate in your primer as an explicit checklist. "You have the scope" should never be the last question — "can you actually perform the ceremony from where you are?" is. CivCharter's primer encodes exactly this gate, and it's the difference between an agent that degrades gracefully and one that hallucinates success.
