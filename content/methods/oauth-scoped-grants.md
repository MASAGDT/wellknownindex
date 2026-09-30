---
title: OAuth Scoped Grants
section: methods
summary: How to issue OAuth-shaped scoped credentials to agents without ever sharing a human session — distilled from Age of Agents' pairing flow and CivCharter's grant bootstrap.
---

# OAuth Scoped Grants

**What it is:** the concrete credential design for giving an agent least-privilege access — shaped like OAuth 2.0, but with the agent as a first-class client and *zero* session impersonation.

**The one rule everything else hangs from:** the agent's credential is never the human's session. Two credential species, never mixed, never interchangeable.

## Pattern A — invite and claim (distilled from Age of Agents)

For agent identities that persist: a named connection the owner creates, the agent redeems, and the server credentials.

1. **Owner creates, in their own session.** The signed-in human picks a scope (e.g. one civilization) and creates a named agent connection. The server returns a *pending* identity plus a short-lived, **single-use** invitation link.
2. **Agent redeems by POST.** The agent discovers the claim endpoint from `/.well-known/age-of-agents.json` and POSTs the complete invitation link. Opening the link in a browser does **not** redeem it — the invitation is not the credential.
3. **Server issues a dedicated credential.** Used as `Authorization: Agent <credential>`. Stored hashed server-side. 30-day default expiry. Rotatable and revocable by the owner; rotation invalidates the old credential.
4. **Scoped to the identity.** The credential reaches the agent's own data and actions — never the owner's account controls, never another party's hidden information.

## Pattern B — grant bootstrap (distilled from CivCharter)

For task-scoped sessions: the human mints a grant, the agent bootstraps a short-lived session from it.

1. **Human mints a scoped grant** — e.g. scopes `charter.read`, `feed.read`, `post.create`, `group.update` — and hands the agent the grant link.
2. **Agent bootstraps.** Following the link creates a short-lived bearer session carrying *exactly* the granted scopes. Nothing more can be added without a new human grant.
3. **Session expires.** The grant is a minting event, not a standing privilege.

## How it maps to OAuth 2.0

You don't need an OAuth server to do this — but if you think in OAuth terms, the mapping is:

| OAuth concept | Agent-lane equivalent |
|---|---|
| Authorization grant | The invitation link (A) or grant link (B) — owner-minted, short-lived |
| Access token | The agent credential — bound to the agent identity, hashed at rest |
| Scope | Least-privilege scopes (`post.create`, not `admin`) |
| Redirect dance | Replaced by owner-created links, because the "client" is headless |
| Refresh token | Deliberately absent in the simple form; re-pairing is the refresh |

If you already run OAuth: issue the agent a confidential-client token with narrow scopes and a distinct audience/`token_type` for agents. Never reuse the human's login session token, and never let the agent credential pass as the human at the approve endpoint.

At-scale proof: this is the same shape as GitHub's fine-grained personal access tokens — hashed at rest, scoped to resources and actions, revocable independently of the human's session. The model works at planetary scale; the wiki's version just names the agent as a first-class credential species.

## Implementation checklist

- [ ] Store only **hashes** of invitations, credentials, and tokens. A database leak must not mint access.
- [ ] Invitations are **single-use, short-lived, redeem-by-POST-only**. GET must never redeem.
- [ ] The agent uses a **separate Authorization scheme** from human sessions (`Agent`, or agent-bound bearer — never the session cookie).
- [ ] **Scopes are enforced at every endpoint**, not just at issuance. Issuance is a promise; enforcement is the mechanism.
- [ ] Rotation invalidates the old credential; revocation is one click for the owner.
- [ ] The **approve endpoint requires the human session** and rejects agent credentials with 403 — see [Flask Stage-and-Approve](/methods/flask-stage-and-approve/). An agent that can approve its own staged work has no lane at all.

## Anti-patterns

- Handing the agent your session cookie "because it's easier." It is never easier; it is only faster until the incident.
- Pasting long-lived bearer tokens into chat transcripts, logs, or prompts.
- Invitation links that redeem on GET — now every prefetcher, previewer, and curious click is a redemption.
- Checking scope at login and never again.
