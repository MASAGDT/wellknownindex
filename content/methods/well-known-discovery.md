---
title: Well-Known Discovery
section: methods
summary: Advertise agent endpoints from /.well-known/ so agents can find the machine lane without being told the URL.
---

# Well-Known Discovery

**What it is:** a JSON document served from the `/.well-known/` path (per RFC 5785) that advertises where a site's agent-facing protocol lives — the claim endpoint, the primer, protocol version, and capabilities. Agents fetch it to bootstrap themselves instead of needing a human to paste URLs.

**Why it matters:** every agent integration today starts with a human handing the agent a link. Well-known discovery removes that step: the agent knows the *convention* (`/.well-known/<service>.json`) and derives everything else. It's how the web already does security.txt, ACME challenges, and OpenID configuration — agents deserve the same treatment.

## The pattern

1. **Pick a stable filename** under `/.well-known/` — e.g. `/.well-known/age-of-agents.json`. Stable across versions; version *inside* the document.
2. **Advertise, don't authorize.** The well-known file is public. It lists endpoints (claim, primer, discovery), the protocol version, and supported capabilities. It contains zero secrets.
3. **Point to the primer.** The well-known file is the signpost; the [machine-readable primer](machine-readable-primer.html) is the rulebook. Link them.
4. **Keep it cacheable but fresh.** These change rarely; HTTP caching is fine, with a version field agents can compare.

## Real example

Age of Agents advertises its agent protocol at `/.well-known/age-of-agents.json`, including the claim endpoint where an agent redeems its single-use invitation link. The agent needs no prior knowledge of the site's URL structure — the convention plus the domain is enough to begin pairing.

## Design notes

- The well-known file must never contain anything that lets an unauthenticated caller *do* something — only pointers to where authenticated flows begin.
- If you only adopt one discovery method in this wiki, make it this one. Conventions beat configuration.
- Consider also advertising the file from your human-facing docs and footer, so humans can point agents at it with a single domain.
