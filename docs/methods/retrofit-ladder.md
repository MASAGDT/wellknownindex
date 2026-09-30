# The Retrofit Ladder

> A maturity model for retrofitting non-agent-centric websites — five rungs from hostile to agentic-native, what each rung costs, and how to climb.

HTML: https://masagdt.github.io/wellknownindex/methods/retrofit-ladder/
JSON: https://masagdt.github.io/wellknownindex/methods/retrofit-ladder.json

---

# The Retrofit Ladder

**What it is:** a maturity model for the central question of this wiki — *your website wasn't built for agents, now what?* The ladder has five rungs. Most of the web sits on rung zero or one. Every method in this wiki is a tool for climbing.

## The rungs

### L0 — Hostile

The site actively resists automation: CAPTCHAs, bot walls, fingerprinting, no API. Agents can't work here at all — or only by fighting the site. Fighting the site is not a lane.

### L1 — Tolerated

Nothing stops a browser-driving agent, but nothing helps it either. It works until a redesign, a CAPTCHA, or a rate limit breaks it. The permission model is "everything you can do" — the broadest, least auditable grant possible. Most agent deployments live here today, and it's the most expensive rung to *stay* on: every site change is a potential outage.

### L2 — Documented

The site publishes human docs an agent can read: API references, help centers, status pages. Better than nothing — agents can ground their actions in something real — but prose isn't a protocol. The agent still guesses at intent boundaries.

### L3 — Machine lane

The site speaks agent: a [machine-readable primer](/methods/machine-readable-primer/), [scoped credentials](/methods/scoped-ai-grants/), [staged writes with human approval](/methods/stage-and-approve/), [well-known discovery](/methods/well-known-discovery/). Least privilege, audit trails, no impersonation. **This is the wiki's home turf** — every method here is rung-3 technology, and it's the cheapest rung to *operate* on: explicit contracts replace fragile guessing.

### L4 — Agentic native

The site was designed for agents first: agents are first-class actors with identities, budgets, and reputations, and the human UI is the secondary interface. Almost nothing lives here yet. The top of the ladder is a research direction, not a product category.

## The economics of climbing

- **L0 → L1** is paid by the *agent builder* — proxies, solvers, retries, breakage.
- **L1 → L2** costs the *site* a little: write things down.
- **L2 → L3** costs the *site* real design work — and pays it back in support load, abuse reduction, and auditability.
- The key insight: **the cost of a rung is paid by whoever wants the capability.** Sites that want agent traffic will climb; agents will route around sites that don't.

## How to use the ladder

1. **Place your site honestly.** "We have docs" is L2, not L3. "Agents can use our site" via browser automation is L1.
2. **Climb one rung, not four.** L2 → L3 starts with a single primer and one scoped, staged write path — not a full rebuild.
3. **Measure the right things.** Time to first successful agent task, breakage rate per site deploy, support tickets caused by agents. If those don't improve, the rung isn't real.

## Design notes

- Rungs are about *contracts*, not technology. A GraphQL API with no scoping is L2 with better tooling.
- Skipping rungs fails: a well-known file (L3 tech) pointing at undocumented endpoints is decoration.
- The ladder is descriptive, not moral. L1 is fine for a weekend project; L3 is for anything agents touch daily.
- New here? Read the rung you're on, then read the method for the next one. That's the whole wiki, in order.
