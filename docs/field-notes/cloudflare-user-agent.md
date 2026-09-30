# Field note: Cloudflare blocks Python's default User-Agent

> API calls from Python's urllib get HTTP 403 from Cloudflare; the same calls with a browser User-Agent succeed.

HTML: https://masagdt.github.io/wellknownindex/field-notes/cloudflare-user-agent/
JSON: https://masagdt.github.io/wellknownindex/field-notes/cloudflare-user-agent.json

---

# Field note: Cloudflare blocks Python's default User-Agent

**Observed:** 2026-09-29, against a small Flask site behind Cloudflare.

Authenticated `GET` requests to `/api/ai/*` routes made with Python's `urllib` failed with **HTTP 403 Forbidden** — even with a valid bearer token. The identical requests made with `curl` (or `urllib` with an overridden header) succeeded.

**Cause:** Cloudflare's bot management flagged the default `Python-urllib/3.x` User-Agent. The 403 came from the edge, not the application — the app never saw the request.

**Fix:** send a browser-like User-Agent:

```python
req = urllib.request.Request(url, headers={
    "Authorization": "Bearer " + token,
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
})
```

**Lesson for agent-lane designers:** if your API sits behind a bot-fighting CDN, *document the expected client behavior* in your primer — or better, allowlist your agent routes. An agent that did everything right (valid grant, valid token, canonical route) still got a 403 with no useful error body. The failure looked like an auth problem and was actually a fingerprinting problem. Distinguish the two in your error responses if you can.
