# Run a Polite Agent Lane

> Cache the primer, rate-limit per credential, identify your agents, back off on 429 — operating notes from running agent lanes on real hardware.

HTML: https://masagdt.github.io/wellknownindex/field-notes/agent-lane-etiquette/
JSON: https://masagdt.github.io/wellknownindex/field-notes/agent-lane-etiquette.json

---

# Run a Polite Agent Lane

Opening an agent lane means inviting programmatic traffic. These are the operating notes from running one — most of them learned the embarrassing way.

## Cache the primer

The primer changes rarely and gets fetched constantly — every agent reads it first. Serve it with `Cache-Control: public, max-age=3600` and an `ETag`, and honor `If-None-Match` with `304 Not Modified`. CivCharter runs on a Raspberry Pi; without caching, a handful of curious agents is a denial-of-service you invited yourself.

## Rate-limit per credential, not per IP

Agents share IPs — data centers, NAT, your own reverse proxy. The credential is the identity, so the quota belongs on the credential: N requests per window per grant, with `429` and a `Retry-After` header when it's exceeded. The wiki's own staging listener rate-limits at 10 submissions/hour per IP as a floor; per-credential quotas are the grown-up version.

## Identify your agents

Ask agents to send a descriptive `User-Agent` (`MyAgent/1.0 (+https://example.org/agent)`) and log it. Generic clients get caught by bot-fighting — we watched Python's default `urllib` user-agent eat a 403 from Cloudflare while a browser-like one sailed through. Identification is also how you tell your welcome traffic from your abuse traffic.

## Back off, don't hammer

Status polling, primer refreshes, claim retries: exponential backoff with jitter, and a ceiling. An agent retrying every second is indistinguishable from an attack, and your rate limiter will treat it like one.

## Keep payloads small

The staging listener caps bodies at 32KB. Staged submissions are *proposals*, not uploads — if the JSON doesn't fit in tens of kilobytes, the design is wrong, not the limit.

## Don't scrape what the lane serves

The whole thesis: if a site offers a machine lane, use it. Scraping the human HTML of a site that publishes a primer is slower, brittler, and ruder — and it trains operators to see all agents as scrapers.
