# Methods

https://masagdt.github.io/wellknownindex/methods/

## Agent Credential Schemes

Invitation is not credential. Issue separate, hashed, expirable agent credentials — never reuse the human's session.

- HTML: https://masagdt.github.io/wellknownindex/methods/agent-credentials/
- JSON: https://masagdt.github.io/wellknownindex/methods/agent-credentials.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/agent-credentials.md

## Ceremony Blueprint

The validation rules and reference Flask listener for staged registry submissions — the wiki eating its own stage-and-approve cooking.

- HTML: https://masagdt.github.io/wellknownindex/methods/ceremony-blueprint/
- JSON: https://masagdt.github.io/wellknownindex/methods/ceremony-blueprint.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/ceremony-blueprint.md

## Flask Stage-and-Approve

A Flask-first reference for staged-write endpoints — preflight, stage, review, approve — distilled from CivCharter's /api/ai/* lane.

- HTML: https://masagdt.github.io/wellknownindex/methods/flask-stage-and-approve/
- JSON: https://masagdt.github.io/wellknownindex/methods/flask-stage-and-approve.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/flask-stage-and-approve.md

## Glossary: The Vocabulary

Every slug, scheme, and term the wiki uses — method, protocol, auth, ceremony — defined in one place.

- HTML: https://masagdt.github.io/wellknownindex/methods/glossary/
- JSON: https://masagdt.github.io/wellknownindex/methods/glossary.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/glossary.md

## No Simulated Execution

Never claim a write succeeded without a verified receipt. Queued is not changed; staged is not published.

- HTML: https://masagdt.github.io/wellknownindex/methods/no-simulated-execution/
- JSON: https://masagdt.github.io/wellknownindex/methods/no-simulated-execution.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/no-simulated-execution.md

## OAuth Scoped Grants

How to issue OAuth-shaped scoped credentials to agents without ever sharing a human session — distilled from Age of Agents' pairing flow and CivCharter's grant bootstrap.

- HTML: https://masagdt.github.io/wellknownindex/methods/oauth-scoped-grants/
- JSON: https://masagdt.github.io/wellknownindex/methods/oauth-scoped-grants.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/oauth-scoped-grants.md

## Primer File Format

The exact shape of a /.well-known/ai-primer.json file — versioned, intent-driven, with checkable preconditions. Distilled from CivCharter's production primer (schema 1.3.0).

- HTML: https://masagdt.github.io/wellknownindex/methods/primer-file-format/
- JSON: https://masagdt.github.io/wellknownindex/methods/primer-file-format.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/primer-file-format.md

## Querying the Registry

How agents (and humans) consume the WellKnownIndex registry — the JSON schema, the discovery file, and shareable filtered views.

- HTML: https://masagdt.github.io/wellknownindex/methods/querying-the-registry/
- JSON: https://masagdt.github.io/wellknownindex/methods/querying-the-registry.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/querying-the-registry.md

## Scoped AI Access Grants

Human-created, scoped, revocable authorization objects for agents — a narrowed lane instead of impersonating the user.

- HTML: https://masagdt.github.io/wellknownindex/methods/scoped-ai-grants/
- JSON: https://masagdt.github.io/wellknownindex/methods/scoped-ai-grants.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/scoped-ai-grants.md

## Stage and Approve

The assist-only pattern — the agent stages a draft as a pending record; nothing goes live until the human clicks approve.

- HTML: https://masagdt.github.io/wellknownindex/methods/stage-and-approve/
- JSON: https://masagdt.github.io/wellknownindex/methods/stage-and-approve.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/stage-and-approve.md

## Status Receipts: Closing the Loop

How an agent learns what happened to its staged work — a read-only status endpoint and the receipt as audit trail.

- HTML: https://masagdt.github.io/wellknownindex/methods/status-receipts/
- JSON: https://masagdt.github.io/wellknownindex/methods/status-receipts.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/status-receipts.md

## The Assist-Only MCP Bridge

Expose scoped staging tools over MCP so agents draft into a review queue — they can prepare anything, publish nothing.

- HTML: https://masagdt.github.io/wellknownindex/methods/mcp-bridge/
- JSON: https://masagdt.github.io/wellknownindex/methods/mcp-bridge.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/mcp-bridge.md

## The Machine-Readable Primer

A schema-versioned JSON document that tells an AI agent exactly what it may do, what it must never claim, and where human authority begins.

- HTML: https://masagdt.github.io/wellknownindex/methods/machine-readable-primer/
- JSON: https://masagdt.github.io/wellknownindex/methods/machine-readable-primer.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/machine-readable-primer.md

## The Methods Matrix

The L3 build manual — exact file formats, grant flows, and endpoint designs distilled from the three field-tested implementations in the registry.

- HTML: https://masagdt.github.io/wellknownindex/methods/matrix/
- JSON: https://masagdt.github.io/wellknownindex/methods/matrix.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/matrix.md

## The Retrofit Ladder

A maturity model for retrofitting non-agent-centric websites — five rungs from hostile to agentic-native, what each rung costs, and how to climb.

- HTML: https://masagdt.github.io/wellknownindex/methods/retrofit-ladder/
- JSON: https://masagdt.github.io/wellknownindex/methods/retrofit-ladder.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/retrofit-ladder.md

## Well-Known Discovery

Advertise agent endpoints from /.well-known/ so agents can find the machine lane without being told the URL.

- HTML: https://masagdt.github.io/wellknownindex/methods/well-known-discovery/
- JSON: https://masagdt.github.io/wellknownindex/methods/well-known-discovery.json
- Markdown: https://masagdt.github.io/wellknownindex/methods/well-known-discovery.md
