# Contribute

> How to propose a registry entry, a method, or a field note — the submission ceremony, the entry schema, and the verification bar.

HTML: https://masagdt.github.io/wellknownindex/contribute/
JSON: https://masagdt.github.io/wellknownindex/contribute.json

---

# Contribute

**What it is:** the submission ceremony for WellKnownIndex. Anyone — human or agent — can propose a registry entry, a method, or a field note. Proposals are staged, verified, and published by a human gardener. Nothing lands in the registry unreviewed.

**Why a ceremony:** a registry is a trust surface. Agents will read these entries and act on them — fetching primers, requesting grants, staging writes. A wrong entry doesn't just misinform; it misdirects autonomous behavior. So every addition passes through verification before it publishes.

## The ceremony

1. **Propose.** Open an issue or pull request on [the GitHub repo](https://github.com/MASAGDT/wellknownindex) — or, while the community is small, drop it in the Facebook group. Include the entry fields below.
2. **Verify.** The gardener checks the verification bar: fetches the endpoints, confirms the agent lane actually works, dates the check.
3. **Publish.** Verified entries are merged, the site rebuilds, and the change goes live on GitHub Pages — usually within minutes. The `verified` date is part of the entry.

## What makes a registry entry

A registry entry needs these fields (frontmatter in `content/registry/<slug>.md`, or the same shape as JSON):

- `title` — the site's name
- `summary` — one or two sentences on what it is and what its agent lane does
- `site_url` — home page, or `null` if not publicly reachable
- `protocols` — array of endpoint records: `{type, url}`, with optional `version`, `url_template`, `note`, and `status`. Rules: `url` must be an exact callable absolute URL — never prose, never a placeholder. Explanations go in `note`; URI templates go in `url_template` with a `{placeholder}`; an endpoint that can't be established uses `status: unconfirmed` plus a `note` saying what's unknown. Declare `version` whenever the site publishes one.
- `auth_schemes` — array of slugs: how an agent authenticates (`ai-access-grant`, `agent-credential`, …)
- `scopes` — the permission vocabulary, if any
- `methods_implemented` — which WellKnownIndex method slugs the site implements
- `cost` — `free`, `unknown`, or a pricing note
- `verified` — date of last verification, `YYYY-MM-DD`
- `verified_evidence` — what the check actually covered, one line per check: which endpoints were fetched, which flows were confirmed, what's still unknown

The machine-readable schema lives at [/schema/registry-entry.json](/schema/registry-entry.json). Validate against it before submitting.

## The verification bar

An entry counts as verified when someone has:

- **Fetched the endpoints** — the primer, the well-known file, the staging route — and confirmed they respond.
- **Confirmed the lane works** — not just documented. A primer nobody can read or a grant flow nobody can complete doesn't count.
- **Checked the claims** — auth schemes, scopes, and implemented methods match what the site actually does.
- **Dated the check** — `verified` is a promise with an expiry. Stale entries get re-checked or flagged.
- **Stated the evidence** — `verified_evidence` says what was actually checked. "Reachable URL" is not "working lane": distinguish documentation review, endpoint reachability, and demonstrated execution. Dates reflect the last real check and are never advanced by a rebuild.

## Proposing a method or field note

- **Methods** document a reusable pattern. A good method has a name, a problem, the pattern itself, and at least one site implementing it. Speculation without an implementation is a field note, not a method.
- **Field notes** are tribal knowledge from real agent runs: gotchas, gates, surprises. They need a date, what happened, and what it taught.

## The future: staged agent submissions

The ceremony above runs on GitHub today. The endgame is the wiki eating its own cooking: a staged submission endpoint where an agent POSTs a candidate entry, it lands in a review queue, a human approves or rejects, and approval publishes it — the [stage-and-approve](/methods/stage-and-approve/) method applied to the registry itself. That design is now written up as the [Ceremony Blueprint](/methods/ceremony-blueprint/), with a reference Flask listener in [`staging/`](https://github.com/MASAGDT/wellknownindex/tree/main/staging) ready for the Pi. Until it's deployed, issues and PRs are the staging area.

## Design notes

- Slugs are join keys: `methods_implemented` references method slugs, `protocols[].type` uses the shared protocol vocabulary. Propose new protocol types as methods first, so the vocabulary stays shared.
- One entry per site. If a site's agent lane changes materially, update the entry and re-date `verified` — don't fork it.
- Small and correct beats large and stale. Three verified entries are worth more than three hundred scraped ones.
