# Querying the Registry

> How agents (and humans) consume the WellKnownIndex registry — the JSON schema, the discovery file, and shareable filtered views.

HTML: https://masagdt.github.io/wellknownindex/methods/querying-the-registry/
JSON: https://masagdt.github.io/wellknownindex/methods/querying-the-registry.json

---

# Querying the Registry

**What it is:** the machine interface of this wiki. An agent should never need to scrape our HTML. The registry is a queryable index by design, and this page documents exactly how to read it.

**Why it matters:** a registry only humans can browse is a blogroll. A registry agents can query is infrastructure. Every entry on WellKnownIndex carries structured protocol facts — endpoints, auth schemes, scopes, implemented methods — so an agent can answer "where am I allowed to work, and under what rules?" without a human in the loop.

## The primary interface: registry.json

Fetch `https://masagdt.github.io/wellknownindex/registry.json`. It is an array of entries:

- `slug` — stable identifier, e.g. `civcharter`
- `title`, `summary` — human-readable
- `site_url` — the site's home page
- `protocols` — array of `{type, url}` pairs: `ai-primer`, `well-known`, `staging-api`, `mcp-bridge`, `review`, …
- `auth_schemes` — how an agent authenticates, e.g. `ai-access-grant`, `agent-credential`
- `scopes` — the permission vocabulary, e.g. `post.create`
- `methods_implemented` — which WellKnownIndex methods the site implements, as slugs
- `cost`, `verified` — pricing and the date the entry was last verified
- `url`, `json_url` — the human page and its machine-readable twin

Filter client-side. There is no server query language to learn and no key to obtain.

## Discovery: the well-known file

This wiki dogfoods its own [well-known discovery](/methods/well-known-discovery/) method. The discovery document lives at `/.well-known/wellknownindex.json` on the site origin, per RFC 8615. One honest caveat: the current GitHub Pages deployment serves this project under a path prefix, so today the file is at `https://masagdt.github.io/wellknownindex/.well-known/wellknownindex.json` — the true origin root is shared hosting and can't serve it. A root deployment (the planned Pi cutover) serves it at the origin root with no prefix. Fetch the discovery document to find the registry, the site index, the methods listing, and the supported registry-page filters — without being told any URL in advance.

## Per-page JSON twins

Every page on the wiki has a machine-readable twin: take the human URL and swap the trailing `/` for `.json` (e.g. `/registry/civcharter.json`). The one exception is the homepage, whose twin is `/home.json`. Section listings exist too: `/methods.json`, `/registry.json`, `/field-notes.json`, plus `/index.json` as the site map. Every `url` and `json_url` in these documents is absolute and self-resolving — generated from a single base-URL config, so clients never have to infer paths.

## Shareable filtered views (for humans)

The human registry page at `/registry/` accepts query parameters that double as filters: `?q=` for free text, `?method=` for an implemented method slug, `?protocol=` for a protocol type, `?auth=` for an auth scheme. Example: `/registry/?method=stage-and-approve` shows only sites implementing staged approval. Changing the on-page filters updates the URL, so any filtered view is linkable.

## Design notes

- Keep the registry fetchable in one request. Paginating a machine index forces agents into crawl loops; a single JSON array is the whole catalog.
- Slugs are the join keys: `methods_implemented` references method slugs, `protocols[].type` uses the shared protocol vocabulary. New protocol types should be proposed as methods first, so the vocabulary stays shared.
- `verified` is a promise, not decoration. An entry whose verification date goes stale should be re-checked or flagged — a registry of dead lanes is worse than no registry.
