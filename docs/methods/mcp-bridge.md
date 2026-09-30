# The Assist-Only MCP Bridge

> Expose scoped staging tools over MCP so agents draft into a review queue — they can prepare anything, publish nothing.

HTML: https://masagdt.github.io/wellknownindex/methods/mcp-bridge/
JSON: https://masagdt.github.io/wellknownindex/methods/mcp-bridge.json

---

# The Assist-Only MCP Bridge

**What it is:** a Model Context Protocol server that exposes *staging* tools to AI agents — e.g. `stage_civic_action` — wired to the same pending-record + human-approval flow as the REST staging endpoint. The agent can prepare any in-scope action through its normal tool use; the tool can only ever create drafts awaiting human review.

**Why it matters:** many agents live inside MCP-capable hosts (Claude Code, Cursor, OpenClaw-style runtimes). Meeting them at the MCP layer means they don't need custom HTTP code — the scoped lane arrives as a *tool*, which is the native way agents act. And the tool's contract enforces the philosophy: its description says "assist only," its scope is declared, and its result is a review link, never a live object.

## The pattern

1. **One tool per stageable action.** `stage_civic_action` with an `action` enum (`post.create`, …) keeps the surface explicit. No generic "do anything" tool.
2. **Scope the tool, not just the server.** The tool declares its required scope; the server checks the caller's grant before accepting. A tool without a scope check is just an API with extra steps.
3. **Preflight inside the tool.** Validate route, scope, fields, and citations before creating the pending record — the same checks as the REST lane, so both lanes stay equivalent.
4. **Return the review link.** The tool result is the pending record plus the one-time approval URL for the human. The agent's job ends at handing that link over.
5. **Keep credentials out of tool I/O.** Tool arguments and results must never carry raw grant tokens or session bearers. The server holds the session; the tool carries the intent.

## Real example

CivCharter's assist-only MCP bridge (`mcp_bridge.py`, tool `stage_civic_action`, required scope `post.create`) stages drafts to `POST /api/ai/stage` and returns `/ai/review?token=…`. The platform's own telling of the story — *"MCP arrived like a protocol knight… 'I can carry drafts to the review chamber. I cannot crown them king.'"* — is the best documentation this pattern has.

## Design notes

- MCP is a transport, not a security model. Everything in [scoped grants](/methods/scoped-ai-grants/) and [agent credentials](/methods/agent-credentials/) still applies behind the tool.
- If your MCP host can't do authenticated HTTP at all, the bridge can run in degraded lanes: generate a command packet for the human operator, or accept pasted-back sanitized output. The primer should name these lanes explicitly.
- Version your tool schemas alongside your primer. An agent holding a stale tool definition is an agent about to be confused.
