# Contributing to WellKnownIndex

WellKnownIndex is a free, public commons: a wiki of agent-access methods and a machine-queryable registry of sites that implement them. Contributions are welcome — entries, methods, field notes, and fixes.

## How it works

Content lives in `content/**/*.md` with YAML frontmatter. `python3 build.py` renders everything into `docs/` for GitHub Pages: human HTML plus a machine-readable JSON twin for every page, plus `registry.json`, `index.json`, and `/.well-known/wellknownindex.json`. Static assets under `static/` are copied through verbatim.

The gardener model: propose → verify → publish. Nothing lands in the registry without verification — see the [Contribute page](https://masagdt.github.io/wellknownindex/contribute/) for the ceremony and the verification bar.

## Adding a registry entry

1. Copy `content/registry/civcharter.md` as a template.
2. Fill in the frontmatter per the [entry schema](https://masagdt.github.io/wellknownindex/schema/registry-entry.json): `title`, `summary`, `site_url`, `protocols`, `auth_schemes`, `scopes`, `methods_implemented`, `cost`, `verified`.
3. Write the body: what the site is, and how its agent lane works, step by step.
4. Run `python3 build.py` and check your page renders.
5. Open a PR. The gardener verifies the endpoints before merge.

## Adding a method or field note

- Methods go in `content/methods/<slug>.md` with `section: methods`. A method needs a real implementation somewhere — speculation belongs in field notes.
- Field notes go in `content/field-notes/<slug>.md` with `section: field-notes`: the date, what happened, what it taught.

## Build & preview

```bash
python3 build.py
cd docs && python3 -m http.server 8000
```

Requires Python 3 and PyYAML. No other dependencies.

## Link conventions

Use root-absolute links (`/methods/stage-and-approve/`). The builder rewrites them to work at any page depth. Don't use relative `sibling.html` links — they resolve against the current page's directory and break.
