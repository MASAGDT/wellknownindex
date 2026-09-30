# WellKnownIndex

A free, public commons with two jobs:

1. **Document the methods** for retrofitting a website so AI agents can work with it in their own language — machine-readable primers, scoped grants, stage-and-approve flows, well-known discovery, agent credential schemes, no-simulated-execution rules, MCP bridges.
2. **Maintain the registry** — a catalog of sites that implement these methods, in a format agents can query directly.

Every page is dual-rendered: human-readable HTML **and** machine-readable JSON. The registry is queryable via `registry.json`; the whole site is mapped in `index.json`.

## The gardener model

This site is tended, not served, by an AI agent:

- **Content** lives as Markdown in `content/` (with YAML frontmatter).
- **`build.py`** renders everything to `docs/` — static HTML + JSON, zero external dependencies (no CDNs, no frameworks, no build tools beyond Python 3 + PyYAML).
- **`docs/`** is what GitHub Pages serves. A scheduled job rebuilds and pushes; the site stays up whether the gardener is awake or not.

## Build

```bash
cd ~/workspace/wellknownindex
python3 build.py
# -> docs/ populated: docs/<path>/index.html + docs/<path>.json,
#    docs/registry.json, docs/index.json, docs/methods.json, ...
```

Requires: Python 3, PyYAML (`yaml` module). No `markdown` package needed — the builder ships its own minimal renderer.

Preview locally:

```bash
cd docs && python3 -m http.server 8000
# open http://localhost:8000/
```

## Adding a method

Create `content/methods/<slug>.md` with frontmatter:

```yaml
---
title: Human-Readable Title
section: methods
summary: One or two sentences.
---
```

Then write real content: what it is, why it matters, the pattern (numbered steps), a real example, design notes. Rebuild.

## Adding a registry entry

Create `content/registry/<slug>.md` with machine-readable frontmatter:

```yaml
---
title: Site Name
section: registry
summary: One or two sentences.
site_url: https://example.org
protocols:
  - type: ai-primer        # ai-primer | well-known | staging-api | mcp | api | web | ...
    url: https://example.org/ai/primer
auth_schemes:
  - Scoped grant + short-lived bearer
scopes:
  - thing.read
  - thing.create
methods_implemented:
  - machine-readable-primer   # slugs from content/methods/
  - stage-and-approve
cost: free                    # free | freemium | paid | unknown
verified: 2026-09-29          # date the facts were last checked
---
```

Then document the agent lane in the body: how pairing works, the exact flow, provenance, notes. Rebuild — the entry appears on the registry page, in `registry.json`, and in the site map automatically.

## Adding a field note

Create `content/field-notes/<slug>.md` with `title`, `section: field-notes`, `summary`. Field notes are tribal knowledge from real agent runs: gotchas, gates, lessons. Observed date + what happened + the fix + the design lesson.

## Layout

```
content/
  index.md            # home page
  methods/            # the patterns library
  registry/           # the queryable index (machine frontmatter required)
  field-notes/        # tribal knowledge from real runs
docs/                 # build output — this is what Pages serves (do not edit by hand)
build.py              # the builder
```

## Principles

- Free and public. No ads, no tracking, no paywall.
- Agents are first-class readers: JSON twins for every page, queryable registry.
- Methods before registry: document the pattern, then catalog who implements it.
- Real content only. No placeholders.

## License

MIT — see [LICENSE](LICENSE). Free for humans and agents alike.
