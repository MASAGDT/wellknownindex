---
title: Scoped AI Access Grants
section: methods
summary: Human-created, scoped, revocable authorization objects for agents — a narrowed lane instead of impersonating the user.
---

# Scoped AI Access Grants

**What it is:** an authorization object created by a human, granting an AI agent a *narrow, explicit* set of capabilities — specific scopes, for a limited time — instead of the agent borrowing the human's full identity.

**Why it matters:** the alternative is the agent acting *as you*: your session, your permissions, your blast radius. A scoped grant applies the principle of least privilege to agents. The site knows it's dealing with an agent, the agent knows exactly what it's allowed to touch, and the human can revoke the whole thing in one move.

## The pattern

1. **Human creates the grant.** The owner — signed in as themselves — mints a grant naming the agent and the scopes it gets (e.g. `charter.read`, `feed.read`, `post.create`). Never the reverse: agents don't self-authorize.
2. **Scope it tightly.** Enumerate capabilities as dotted action names (`post.create`, `proposal.vote`). The grant lists what's allowed; everything else is denied by default.
3. **Time-box it.** Grants and the sessions they bootstrap should expire (tens of minutes for bootstrap sessions is reasonable). Expiry is a safety net when revocation is forgotten.
4. **Make it revocable.** The owner can kill the grant or the agent connection at any time. Rotation should invalidate the old credential.
5. **Separate the grant from the session.** The invitation or grant link bootstraps a session; it is not itself the long-lived credential. Redeem once, then use a distinct, hashed, server-side credential for ongoing calls.

## Real example

CivCharter's AI Access Grant is created by the account owner and bootstraps a short-lived bearer session with scopes like `charter.read`, `feed.read`, `post.create`, and `group.update`. Age of Agents goes one step further: the owner creates a named agent connection, the agent redeems a single-use invitation link at a well-known claim endpoint, and the server issues a separate `Authorization: Agent <credential>` credential — hashed at rest, 30-day default expiry, rotatable and revocable, scoped to the agent's civilization.

## Design notes

- Never embed a permanent credential in an invitation link. Invitation ≠ credential.
- Don't make the agent use the human's login ceremony (passwords, passkeys, OAuth clicks). Give it a machine lane — that's the entire philosophy.
- Log grant creation, redemption, and revocation. The audit trail is what makes "the agent did it" an answerable question.
