# Glossary: The Vocabulary

> Every slug, scheme, and term the wiki uses — method, protocol, auth, ceremony — defined in one place.

HTML: https://masagdt.github.io/wellknownindex/methods/glossary/
JSON: https://masagdt.github.io/wellknownindex/methods/glossary.json

---

# Glossary: The Vocabulary

The wiki uses a small, deliberate vocabulary. These are the terms, exactly as the [registry schema](/schema/registry-entry.json) and the method pages use them.

**Agent lane** — the narrow, machine-readable path a site offers agents, distinct from its human UI. The alternative to agents driving a browser aimed at humans.

**Method** — a reusable integration pattern, named by a slug like `stage-and-approve` or `well-known-discovery`. Methods are what the [Methods](/methods/) section catalogs.

**Protocol** — a concrete machine-readable contract a site publishes, named by a `type` slug plus a `url`: e.g. `{type: "ai-primer", url: "https://example.org/ai/primer"}`. A site can publish several; each may declare a `version`.

**Protocol version** — the `version` field on a protocol entry (e.g. `"1.3.0"`). Lets an agent pin behavior before it fetches.

**Auth scheme** — how an agent proves who it is: a slug like `agent-bearer`, `oauth-scoped-grant`, or `invite-claim`. Normalized to lowercase slugs in the registry.

**Scope** — a named permission boundary on a credential (`draft:write`, `stage:submit`). Scopes are enforced at every endpoint, not just at issuance.

**Grant** — an issued credential plus its scopes: what the agent actually holds.

**Credential species** — the idea that agent credentials are a different *kind* of credential from human sessions, not just a different value. Separate issuance, separate storage (hashes, never plaintext), separate revocation — see [Agent Credentials](/methods/agent-credentials/).

**Primer** — the machine-readable file (usually `/.well-known/ai-primer.json`) where a site tells agents what it is, what it allows, and what it forbids — see [Primer File Format](/methods/primer-file-format/).

**Preflight** — the check-before-you-act call: the agent submits intent, the server answers what *would* happen, nothing is persisted.

**Stage** — the agent's proposed work, held in a pending state. Staging never publishes.

**Receipt** — the record of a decision: what was approved or rejected, when, and by whom. Collected via [Status Receipts](/methods/status-receipts/).

**Ceremony** — the full propose → verify → publish pipeline with human approval in the middle. The wiki's own submission flow is the reference implementation — see [Ceremony Blueprint](/methods/ceremony-blueprint/).

**Retrofit ladder** — the L0–L4 scale for how agent-ready a site is: L0 Hostile, L1 Tolerated, L2 Documented, L3 Machine lane, L4 Agentic native. See [Retrofit Ladder](/methods/retrofit-ladder/).

**Registry entry** — one site's machine-readable record in the [registry](/registry/): site URL, protocols, auth schemes, scopes, methods implemented, cost, and verification status.

**Machine-readable twin** — the JSON version of every wiki page, served alongside the human HTML. The wiki dogfoods its own thesis: humans read the page, agents read the twin.
