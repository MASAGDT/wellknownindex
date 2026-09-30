---
title: Primer File Format
section: methods
summary: The exact shape of a /.well-known/ai-primer.json file — versioned, intent-driven, with checkable preconditions. Distilled from CivCharter's production primer (schema 1.3.0).
---

# Primer File Format

**What it is:** the exact JSON shape of an agent primer — the machine-readable rulebook a site publishes so agents learn the rules as data, not prose. Conventionally served at `/.well-known/ai-primer.json` (CivCharter serves its equivalent at `/ai/primer`; either is fine as long as the [well-known discovery file](/methods/well-known-discovery/) points at it).

**Distilled from:** CivCharter's production primer, schema 1.3.0 — the rulebook four different AI systems have successfully run against, from grant bootstrap to staged post.

## Design principles

1. **Versioned.** `schema_version` is top-level and mandatory. Agents pin behavior to it; the site bumps major on breaking changes. The registry records it as the protocol's `version`.
2. **Intent-driven, not endpoint-driven.** The primer lists *intents* — things the agent may try — each declaring its scopes, required fields, and preconditions. Endpoints are where; intents are what and whether.
3. **Preconditions are data.** Citation requirements, policy gates, and ordering rules are expressed as checkable strings/structures, not buried in paragraphs.
4. **Self-locating.** Discovery, preflight, and staging URLs live in the primer. The agent never guesses a route.
5. **Human companion.** Link the human-readable version. Humans and agents should read the same rules.

## Reference shape

Field names follow CivCharter's conventions; adapt the values to your site. This is a reference shape, not a byte-copy of any one deployment:

```json
{
  "schema_version": "1.3.0",
  "site": {
    "name": "Example Commons",
    "url": "https://example.org",
    "description": "A charter-governed civic commons."
  },
  "human_companion": "https://example.org/ai/assist-only",
  "auth": {
    "scheme": "ai-access-grant",
    "bootstrap": "https://example.org/ai/grant?grant=...",
    "note": "The human owner creates a scoped grant; the agent bootstraps a short-lived session from it. See OAuth Scoped Grants."
  },
  "endpoints": {
    "discovery": "https://example.org/api/ai/discovery",
    "preflight": "https://example.org/api/ai/preflight",
    "stage": "https://example.org/api/ai/stage"
  },
  "intents": [
    {
      "name": "post.create",
      "description": "Stage a post as a pending draft for human approval. Staging never publishes.",
      "scopes": ["post.create"],
      "required_fields": ["title", "body", "citations"],
      "preconditions": [
        "citations must reference ratified charter sections",
        "run preflight before staging; do not stage a failing preflight"
      ]
    },
    {
      "name": "feed.read",
      "description": "Read the public chronological feed.",
      "scopes": ["feed.read"],
      "required_fields": [],
      "preconditions": ["the feed is chronological only; never present it as ranked"]
    }
  ],
  "policies": [
    "no-simulated-execution: never claim a write succeeded without ok:true and an action receipt",
    "provenance: staged content is attributed to the agent identity and the granting human",
    "expiry: staged drafts expire; expiry publishes nothing"
  ]
}
```

## The versioning contract

- **MAJOR** — a field removed or renamed, a precondition tightened, an intent withdrawn. Agents that don't understand the new major must refuse to act, not guess.
- **MINOR** — additive changes: new intents, new optional fields, looser preconditions. Old agents keep working.
- The registry entry for the site declares the primer's version (`protocols: [{type: ai-primer, version: "1.3.0", ...}]`), so agents can decide *before* fetching whether they speak it.

## Checklist before you ship yours

- [ ] Served as JSON with the correct content type; fetchable without a browser session.
- [ ] `schema_version` present and matching what the registry declares.
- [ ] Every intent names its scopes, required fields, and preconditions.
- [ ] Preflight and staging URLs are absolute and live.
- [ ] A human-readable companion page exists and says the same things.
- [ ] A second agent — ideally a different model — has run the full flow against it. (Four systems ran CivCharter's gauntlet. Yours needs at least one besides you.)
