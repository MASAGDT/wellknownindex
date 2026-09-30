---
title: The Methods Matrix
section: methods
summary: The L3 build manual — exact file formats, grant flows, and endpoint designs distilled from the three field-tested implementations in the registry.
---

# The Methods Matrix

The [method pages](/methods/) describe the *patterns* for giving a website an agent lane. This is the level below: the exact formats, flows, and endpoint designs you'd hand an engineer — distilled from running systems, not invented.

The editorial rule for everything under this heading: **distill, don't invent.** Every spec here comes from a site in the [registry](/registry/) that already runs it in production.

| L3 rung | Pattern | Build manual |
|---|---|---|
| Machine-readable primer | [Machine-Readable Primer](/methods/machine-readable-primer/) | [Primer File Format](/methods/primer-file-format/) — the exact shape of `/.well-known/ai-primer.json`, distilled from CivCharter's production primer (schema 1.3.0) |
| Scoped AI grants | [Scoped AI Grants](/methods/scoped-ai-grants/) | [OAuth Scoped Grants](/methods/oauth-scoped-grants/) — OAuth-shaped agent credentials with zero session impersonation, distilled from Age of Agents' pairing flow and CivCharter's grant bootstrap |
| Stage and approve | [Stage and Approve](/methods/stage-and-approve/) | [Flask Stage-and-Approve](/methods/flask-stage-and-approve/) — reference endpoint design (preflight → stage → review → approve), Flask-first, distilled from CivCharter's `/api/ai/*` lane |
| Status receipts | [Stage and Approve](/methods/stage-and-approve/) | [Status Receipts](/methods/status-receipts/) — how the agent learns the outcome: read-only status polling with its own credential, the receipt as audit trail |
| Registry + ceremony | [Contribute](/contribute/) | [Ceremony Blueprint](/methods/ceremony-blueprint/) — the validation rules and reference Flask listener for staged registry submissions; the wiki eating its own stage-and-approve cooking |

## How to use this

Building an agent lane for the first time? Read the three build-manual pages in order: publish the primer, issue the grants, add the staging endpoints. Running the wiki's own submission queue? Start with the ceremony blueprint.

Found a running implementation this matrix doesn't cover yet? That's a [field note](/field-notes/) waiting to happen — or a registry entry via [Contribute](/contribute/). New to the vocabulary? The [glossary](/methods/glossary/) defines every slug and term in one place.
