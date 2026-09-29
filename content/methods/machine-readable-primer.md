---
title: The Machine-Readable Primer
section: methods
summary: A schema-versioned JSON document that tells an AI agent exactly what it may do, what it must never claim, and where human authority begins.
---

# The Machine-Readable Primer

**What it is:** a public, schema-versioned JSON document — served at a stable URL like `/ai/primer` — that an AI assistant reads *before* doing anything else on your site. It declares the agent contract: allowed actions, execution lanes, credential rules, canonical routes, citation requirements, and the policies that govern agent behavior.

**Why it matters:** most platforms hand an agent a loaded API and hope for the best. A primer inverts that: the site speaks first, in the agent's own language (structured data, not prose). The agent doesn't guess your rules — it parses them. This eliminates the largest source of agent misbehavior: confidently inventing endpoints, scopes, and permissions that don't exist.

## The pattern

1. **Serve it publicly** at a memorable path (`/ai/primer`). No secrets inside — classification: public and safe. It describes the *rules*, never credentials.
2. **Version it.** Include a schema version and an agent-contract version so agents can detect when the rules change.
3. **Declare execution lanes.** Name the modes an agent may operate in — e.g. assist-only drafting, assist-only staging, direct execution — and the exact conditions for choosing each one.
4. **List canonical routes.** Every action maps to one exact route. Explicitly forbid invented routes (`/api/v1/*` guesses are a classic failure).
5. **State the policies as data:** no-simulated-execution rules, credential handling, CSRF context, citation requirements, visibility governance.

## Real example

CivCharter serves its primer at `https://civcharter.org/ai/primer` — a JSON document (`CivCharter_AI_Access_Grant_Generic_AI_Primer`, schema 1.3.0) covering action enums (`post.create`, `proposal.vote`, …), execution lanes, the assist-only MCP bridge, preflight requirements, and a human-readable companion at `/ai/assist-only`. Four different AI systems have run the full grant flow against it without going rogue.

## Design notes

- Keep it credential-free. If a secret appears in the primer, the design is wrong — secrets belong in the grant bootstrap, delivered privately.
- Agents should re-read the primer when uncertain, not cache it forever. A short client cache lifetime with refresh guidance beats a stale rulebook.
- Pair it with [well-known discovery](well-known-discovery.html) so agents can *find* the primer without being told the URL.
