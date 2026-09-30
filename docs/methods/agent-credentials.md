# Agent Credential Schemes

> Invitation is not credential. Issue separate, hashed, expirable agent credentials — never reuse the human's session.

HTML: https://masagdt.github.io/wellknownindex/methods/agent-credentials/
JSON: https://masagdt.github.io/wellknownindex/methods/agent-credentials.json

---

# Agent Credential Schemes

**What it is:** a credential system designed for agents rather than borrowed from humans: the agent authenticates with its *own* credential, on its *own* scheme, with its own lifecycle — instead of a bearer token minted from someone's login session.

**Why it matters:** agent credentials live in unusual places — transcripts, VM disks, tool outputs. They get copied, logged, and pasted far more casually than a human's session cookie. The scheme has to assume exposure and minimize blast radius: short lifetimes, easy rotation, instant revocation, and scopes that don't include "everything the owner can do."

## The pattern

1. **Separate invitation from credential.** The invitation link is single-use and short-lived; redeeming it *issues* the credential. The link is not the credential. (Opening the link in a browser must not redeem it — link prefetchers exist.)
2. **Distinct auth scheme.** E.g. `Authorization: Agent <credential>` rather than reusing `Bearer`. The scheme itself tells the server — and the logs — which kind of actor this is.
3. **Hash at rest.** Store only hashes server-side, like passwords. A database read shouldn't yield usable credentials.
4. **Expire by default.** Thirty days is a common default; shorter for high-stakes scopes. Expiry is the safety net; rotation is the practice.
5. **Rotate and revoke.** Rotation invalidates the old credential atomically. The owner can revoke the agent connection entirely, independent of their own session.
6. **Scope to the agent's world.** The credential authorizes the agent identity within its assigned scope (a civilization, a workspace) — never the owner's account controls, never another tenant's hidden data.

## Real example

Age of Agents: the agent POSTs its complete single-use invitation link to the claim endpoint from `/.well-known/age-of-agents.json`; the server returns a dedicated agent credential used as `Authorization: Agent <credential>`. Credentials are stored hashed, expire after 30 days by default, and can be rotated or revoked by the owner. Human-owner sessions and agent credentials are fully separate — an agent never gains the owner's account controls.

## Design notes

- The weakest link is the agent host's storage. Design as if the credential *will* leak: that's what expiry and revocation are for.
- Never put a permanent credential in a URL. URLs get logged by proxies, prefetchers, and chat transcripts.
- Audit credential issuance, use, rotation, and revocation. "Which agent did what, with which credential" should always be answerable.
