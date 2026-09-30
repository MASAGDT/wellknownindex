#!/usr/bin/env python3
"""WellKnownIndex static site builder.

Renders content/**/*.md -> docs/ for GitHub Pages.
Every page becomes human-readable HTML (docs/<path>/index.html)
AND machine-readable JSON (docs/<path>.json).
Also emits docs/registry.json (queryable registry) and
docs/index.json (site map). Zero external dependencies.
"""
import html
import json
import re
import shutil
from datetime import date, datetime
from pathlib import Path


def json_default(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


def jdumps(o, **kw):
    return json.dumps(o, default=json_default, **kw)

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
DOCS = ROOT / "docs"

SECTIONS = {
    "methods": "Methods",
    "registry": "Registry",
    "field-notes": "Field notes",
}

SITE_TITLE = "WellKnownIndex"
SITE_TAGLINE = "A free, public index of agent-friendly web endpoints — and the methods for building them."
# Canonical origin of the published site. Update if a custom domain is added.
SITE_URL = "https://masagdt.github.io/wellknownindex"


# ---------------------------------------------------------------- frontmatter
def parse_md(path):
    text = path.read_text(encoding="utf-8")
    meta = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            import yaml
            meta = yaml.safe_load(text[3:end]) or {}
            body = text[end + 4 :].lstrip("\n")
    return meta, body


# ------------------------------------------------------- minimal markdown
def _check_protocol(md_path, pr):
    """WKI-03: exact endpoints, templates, and notes stay separated.

    `url` must be a clean absolute URL or absent; prose goes in `note`,
    URI templates go in `url_template` with a {placeholder}. An endpoint
    that cannot be established uses `status: unconfirmed` plus a `note`
    explaining what is unknown — never a guessed URL.
    """
    u = pr.get("url")
    t = pr.get("url_template")
    ptype = pr.get("type", "?")
    status = pr.get("status", "confirmed")
    if status not in ("confirmed", "unconfirmed"):
        raise SystemExit(
            f"ERROR {md_path}: protocol '{ptype}' has unknown status {status!r}; "
            "use 'confirmed' or 'unconfirmed'.")
    if u and (not re.match(r"^https?://\S+$", str(u)) or "..." in str(u)):
        raise SystemExit(
            f"ERROR {md_path}: protocol '{ptype}' url is not a clean absolute "
            f"URL: {u!r} — move prose to 'note', templates to 'url_template', "
            "unknowns to status 'unconfirmed'.")
    if status == "unconfirmed":
        if not pr.get("note"):
            raise SystemExit(
                f"ERROR {md_path}: protocol '{ptype}' is unconfirmed but has no "
                "'note' explaining what is unknown.")
        return
    if not u and not t:
        raise SystemExit(
            f"ERROR {md_path}: protocol '{ptype}' needs url or url_template; "
            "use status 'unconfirmed' with a note if the endpoint is unknown.")
    if u and (not re.match(r"^https?://\S+$", str(u)) or "..." in str(u)):
        raise SystemExit(
            f"ERROR {md_path}: protocol '{ptype}' url is not a clean absolute "
            f"URL: {u!r} — move prose to 'note', templates to 'url_template'.")
    if t and (" " in str(t) or "{" not in str(t)):
        raise SystemExit(
            f"ERROR {md_path}: protocol '{ptype}' url_template must contain "
            f"a {{placeholder}} and no spaces: {t!r}")
def _split_row(s):
    s = s.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_table_sep(s):
    cells = _split_row(s)
    return bool(cells) and all(re.match(r"^:?-+:?$", c) for c in cells)


def inline(md):
    md = html.escape(md)
    md = re.sub(r"`([^`]+?)`", r"<code>\1</code>", md)
    md = re.sub(r"\[([^\]]+?)\]\(([^)]+?)\)", r'<a href="\2">\1</a>', md)
    md = re.sub(r"\*\*([^*]+?)\*\*", r"<strong>\1</strong>", md)
    md = re.sub(r"\*([^*]+?)\*", r"<em>\1</em>", md)
    return md


def fix_links(html_text, depth):
    """Rewrite links to work with pretty URLs at any depth."""
    prefix = "../" * depth

    def repl(m):
        href = m.group(1)
        if href.startswith(("http://", "https://", "#", "mailto:")):
            return m.group(0)
        if href.startswith("/"):
            href = prefix + href.lstrip("/")
        elif href.endswith(".html"):
            href = href[: -len(".html")] + "/"
        elif href.endswith(".md"):
            href = href[: -len(".md")] + "/"
        return f'href="{href}"'

    return re.sub(r'href="([^"]+)"', repl, html_text)


def render_markdown(body, depth):
    lines = body.split("\n")
    out = []
    i = 0
    in_code = False
    code_lang = ""
    code_buf = []
    list_stack = []  # "ul" / "ol"

    def close_lists():
        while list_stack:
            out.append(f"</{list_stack.pop()}>")

    while i < len(lines):
        line = lines[i]
        # fenced code
        if line.strip().startswith("```"):
            if in_code:
                out.append(
                    "<pre><code>"
                    + html.escape("\n".join(code_buf))
                    + "</code></pre>"
                )
                code_buf = []
                in_code = False
            else:
                close_lists()
                in_code = True
                code_lang = line.strip()[3:].strip()
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue
        s = line.strip()
        if not s:
            close_lists()
            i += 1
            continue
        if re.match(r"^#{1,3}\s", s):
            close_lists()
            level = len(s) - len(s.lstrip("#"))
            out.append(f"<h{level}>{inline(s[level:].strip())}</h{level}>")
        elif s in ("---", "***"):
            close_lists()
            out.append("<hr>")
        elif s.startswith(">"):
            close_lists()
            out.append(f"<blockquote>{inline(s[1:].strip())}</blockquote>")
        elif re.match(r"^[-*]\s+", s):
            if not list_stack or list_stack[-1] != "ul":
                close_lists()
                out.append("<ul>")
                list_stack.append("ul")
            out.append(f"<li>{inline(s[2:].strip())}</li>")
        elif re.match(r"^\d+\.\s+", s):
            if not list_stack or list_stack[-1] != "ol":
                close_lists()
                out.append("<ol>")
                list_stack.append("ol")
            out.append(f"<li>{inline(re.sub(r'^\d+\.\s+', '', s))}</li>")
        elif s.startswith("|") and i + 1 < len(lines) and _is_table_sep(lines[i + 1]):
            close_lists()
            headers = _split_row(s)
            j = i + 2
            rows = []
            while j < len(lines) and lines[j].strip().startswith("|"):
                if _is_table_sep(lines[j]):
                    j += 1
                    continue
                rows.append(_split_row(lines[j].strip()))
                j += 1
            thead = "<tr>" + "".join(f"<th>{inline(c)}</th>" for c in headers) + "</tr>"
            tbody = "".join(
                "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                for r in rows
            )
            out.append(
                "<div class='tablewrap'><table><thead>"
                + thead + "</thead><tbody>" + tbody
                + "</tbody></table></div>"
            )
            i = j - 1
        else:
            close_lists()
            # gather paragraph lines
            para = [s]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not re.match(
                r"^(#{1,3}\s|```|>|[-*]\s+|\d+\.\s+|---$|\|)", lines[j].strip()
            ):
                para.append(lines[j].strip())
                j += 1
            out.append(f"<p>{inline(' '.join(para))}</p>")
            i = j - 1
        i += 1
    close_lists()
    return fix_links("\n".join(out), depth)


# ------------------------------------------------------- diagrams (inline SVG)
# Visual explainers, one per method page. Pure inline SVG — no external
# dependencies, no JS. Content opts in via frontmatter: `diagram: <name>`.


def _svg(inner, h=200):
    return (
        "<svg viewBox='0 0 640 " + str(h) + "' width='100%' role='img' "
        "style='display:block;height:auto'>"
        "<defs><marker id='arr' viewBox='0 0 10 10' refX='8' refY='5' "
        "markerWidth='6.5' markerHeight='6.5' orient='auto-start-reverse'>"
        "<path d='M0,0 L10,5 L0,10 z' fill='#8b95ad'/></marker></defs>"
        + inner + "</svg>"
    )


def _node(x, y, w, h, title, sub="", stroke="#6ee7ff"):
    cy = y + h / 2
    s = (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='10' "
         f"fill='#11151f' stroke='{stroke}' stroke-width='1.5'/>"
         f"<text x='{x + w / 2}' y='{cy - 2 if sub else cy + 5}' text-anchor='middle' "
         f"fill='#dbe2f0' font-size='14' font-weight='600'>{title}</text>")
    if sub:
        s += (f"<text x='{x + w / 2}' y='{cy + 18}' text-anchor='middle' "
              f"fill='#8b95ad' font-size='11'>{sub}</text>")
    return s


def _arrow(x1, y1, x2, y2, label="", lx=None, ly=None):
    s = (f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' "
         f"stroke='#8b95ad' stroke-width='1.5' marker-end='url(#arr)'/>")
    if label:
        tx = (x1 + x2) / 2 if lx is None else lx
        ty = (y1 + y2) / 2 - 8 if ly is None else ly
        s += (f"<text x='{tx}' y='{ty}' text-anchor='middle' "
              f"fill='#8b95ad' font-size='11'>{label}</text>")
    return s


def _cap(x, y, text, size=12, fill="#8b95ad"):
    return (f"<text x='{x}' y='{y}' text-anchor='middle' "
            f"fill='{fill}' font-size='{size}'>{text}</text>")


def _d_retrofit_ladder():
    rungs = [
        ("L0", "Hostile", "CAPTCHAs, bot walls — agents fight the site", "#8b95ad"),
        ("L1", "Tolerated", "browser automation works until it breaks", "#8b95ad"),
        ("L2", "Documented", "human docs agents can read; prose, not protocol", "#8b95ad"),
        ("L3", "Machine lane", "primer · scoped grants · staged approval", "#6ee7ff"),
        ("L4", "Agentic native", "agents are first-class actors", "#a78bfa"),
    ]
    parts = []
    for i, (lvl, name, desc, color) in enumerate(rungs):
        y = 8 + i * 56
        parts.append(
            f"<rect x='16' y='{y}' width='608' height='46' rx='10' "
            f"fill='#11151f' stroke='{color}' stroke-width='1.5'/>"
            f"<text x='36' y='{y + 29}' fill='{color}' font-size='14' "
            f"font-weight='700'>{lvl} — {name}</text>"
            f"<text x='604' y='{y + 28}' text-anchor='end' "
            f"fill='#8b95ad' font-size='11'>{desc}</text>")
    parts.append(_cap(320, 298, "Most of the web: L0–L1 · This wiki: the tools for L3"))
    return _svg("".join(parts), h=308)


def _d_primer():
    p = [_node(20, 60, 130, 70, "Website", "human HTML"),
         _node(255, 60, 130, 70, "Primer", "JSON rulebook", "#a78bfa"),
         _node(490, 60, 130, 70, "Agent", "acts within rules"),
         _arrow(150, 95, 250, 95, "publishes"),
         _arrow(385, 95, 485, 95, "agent reads"),
         _cap(320, 175, "The rules become data, not prose.")]
    return _svg("".join(p), h=190)


def _d_grants():
    p = ["<rect x='232' y='36' width='168' height='118' rx='12' fill='none' "
         "stroke='#8b95ad' stroke-width='1.5' stroke-dasharray='6 5'/>",
         _cap(316, 56, "scope fence", 11),
         _node(20, 60, 130, 70, "Human", "owns the account"),
         _node(250, 66, 132, 70, "Agent", "least privilege"),
         _arrow(150, 95, 245, 95, "grants scope"),
         "<text x='250' y='188' fill='#6ee7ff' font-size='12'>✓ can: post.create</text>",
         "<text x='250' y='210' fill='#8b95ad' font-size='12'>✗ cannot: everything else</text>"]
    return _svg("".join(p), h=224)


def _d_stage():
    p = [_node(15, 50, 110, 70, "Agent", "proposes"),
         _node(175, 50, 130, 70, "Staging", "PENDING", "#a78bfa"),
         _node(355, 50, 110, 70, "Human", "reviews"),
         _node(515, 50, 110, 70, "Live", "✓ published"),
         _arrow(125, 85, 170, 85, "stages"),
         _arrow(305, 85, 350, 85, "reviews"),
         _arrow(465, 85, 510, 85, "approves"),
         _node(355, 175, 110, 55, "Rejected", "discarded", "#8b95ad"),
         _arrow(410, 120, 410, 170),
         "<text x='424' y='150' fill='#8b95ad' font-size='11'>rejects</text>",
         _cap(320, 258, "Nothing goes live without a human decision.")]
    return _svg("".join(p), h=268)


def _d_status():
    p = [_node(20, 40, 100, 64, "Agent"),
         _arrow(120, 72, 150, 72, "polls"),
         _node(155, 40, 110, 64, "Status", "read-only", "#6ee7ff"),
         _arrow(265, 72, 295, 72, "returns"),
         _node(300, 40, 130, 64, "Receipt", "pending/decided"),
         _node(155, 150, 110, 55, "Human", "decides", "#a78bfa"),
         _arrow(210, 150, 210, 104, "", lx=222, ly=128),
         "<text x='222' y='128' fill='#8b95ad' font-size='11'>decides</text>",
         _cap(320, 252, "The agent reads outcomes with its own credential · the receipt is the audit trail.")]
    return _svg("".join(p), h=262)


def _d_ceremony():
    p = [_node(20, 50, 90, 64, "Agent"),
         _arrow(110, 82, 180, 82, "POSTs JSON"),
         _node(180, 50, 100, 64, "Listener", "validates"),
         _arrow(280, 82, 330, 82, "queues"),
         _node(330, 50, 95, 64, "Queue", "PENDING", "#a78bfa"),
         _arrow(425, 82, 480, 82, "reviews"),
         _node(480, 50, 100, 64, "Human", "decides", "#6ee7ff"),
         _arrow(530, 114, 530, 165, "approves", lx=566, ly=145),
         _node(480, 170, 100, 55, "Git", "commit → live"),
         _arrow(378, 114, 378, 165),
         _node(330, 170, 95, 55, "Rejected", "discarded", "#8b95ad"),
         "<text x='394' y='145' fill='#8b95ad' font-size='11'>rejects</text>",
         _cap(320, 262, "Agents propose · the listener validates · humans dispose.")]
    return _svg("".join(p), h=272)


def _d_oauth_grants():
    p = [_node(20, 40, 90, 64, "Owner"),
         _arrow(110, 72, 170, 72, "issues"),
         _node(170, 40, 110, 64, "Grant", "scoped"),
         _arrow(280, 72, 340, 72, "held by"),
         _node(340, 40, 90, 64, "Agent"),
         _arrow(430, 72, 500, 72, "calls"),
         _node(500, 40, 120, 64, "Endpoints", "scope-checked"),
         _node(340, 150, 90, 55, "Approve", "human only", "#a78bfa"),
         _arrow(385, 104, 385, 150),
         "<text x='420' y='132' fill='#8b95ad' font-size='11'>approve attempt → 403</text>",
         _cap(320, 248, "Grants are scoped and hashed · the approve endpoint only trusts human sessions.")]
    return _svg("".join(p), h=258)


def _d_flask_seq():
    steps = [("GET /ai/primer", "learn the rules", "#6ee7ff"),
             ("POST /api/ai/preflight", "what would happen", "#6ee7ff"),
             ("POST /api/ai/stage", "hold the draft", "#6ee7ff"),
             ("GET /ai/review?token=…", "human reads", "#6ee7ff"),
             ("POST /api/ai/approve", "human session only", "#a78bfa")]
    p = []
    y = 16
    for title, sub, stroke in steps:
        p.append(_node(170, y, 300, 46, title, sub, stroke))
        y += 46
        if (title, sub, stroke) != steps[-1]:
            p.append(_arrow(320, y, 320, y + 26))
            y += 26
    p.append(_cap(320, y + 30, "Read, preflight, stage, review, approve — the agent never touches the last step."))
    return _svg("".join(p), h=y + 40)


def _d_primer_anatomy():
    p = [_node(170, 16, 300, 52, "intent", "who this site is · schema v1.3.0"),
         _arrow(320, 68, 320, 92),
         _node(170, 92, 300, 52, "preconditions", "what the agent must know first"),
         _arrow(320, 144, 320, 168),
         _node(170, 168, 300, 52, "forbidden", "what the agent must never do", "#a78bfa"),
         _cap(320, 258, "Three sections, read top-down: identity, requirements, prohibitions.")]
    return _svg("".join(p), h=268)


def _d_wellknown():
    p = [_node(255, 15, 130, 60, "Agent", "arrives cold"),
         _node(225, 115, 190, 60, "well-known file", "/.well-known/x.json", "#a78bfa"),
         _node(40, 200, 150, 55, "Primer", "the rulebook"),
         _node(450, 200, 150, 55, "Staging API", "the lane"),
         _arrow(320, 75, 320, 110, "fetches", lx=352, ly=96),
         _arrow(280, 175, 130, 200),
         _arrow(360, 175, 510, 200),
         _cap(320, 288, "One fetch bootstraps the whole lane.")]
    return _svg("".join(p), h=298)


def _d_credentials():
    p = [_node(15, 60, 110, 70, "Owner", "authorizes"),
         _node(185, 60, 110, 70, "Agent", "redeems"),
         _node(355, 60, 170, 70, "Credential", "hashed · expiring · revocable", "#a78bfa"),
         _arrow(125, 95, 180, 95),
         _arrow(295, 95, 350, 95, "issues"),
         _cap(320, 178, "A single-use invite becomes a scoped credential — never a password.")]
    return _svg("".join(p), h=192)


def _d_nosim():
    p = [_cap(320, 22, "The agent's view vs. the authority's view", 12, "#dbe2f0"),
         _node(30, 40, 140, 60, "Submit order", "agent acts"),
         _node(250, 40, 140, 60, "QUEUED", "not yet real", "#a78bfa"),
         _arrow(170, 70, 245, 70),
         _node(30, 130, 140, 60, "Authority tick", "world resolves"),
         _node(250, 130, 140, 60, "CHANGED ✓", "receipt issued", "#6ee7ff"),
         _arrow(170, 160, 245, 160),
         "<text x='465' y='128' text-anchor='middle' fill='#a78bfa' "
         "font-size='30' font-weight='700'>≠</text>",
         _cap(320, 222, "Queued is not changed. Only the authority resolves.")]
    return _svg("".join(p), h=232)


def _d_mcp():
    p = [_node(20, 60, 120, 70, "Agent", "any model"),
         _node(260, 60, 120, 70, "Bridge", "scoped tools", "#a78bfa"),
         _node(500, 60, 120, 70, "Site", "your app"),
         _arrow(140, 88, 255, 88),
         _arrow(255, 104, 140, 104),
         _arrow(380, 88, 495, 88),
         _arrow(495, 104, 380, 104),
         _cap(200, 74, "MCP", 11),
         _cap(440, 74, "scoped calls", 11),
         _cap(320, 172, "MCP is transport; the scope model is the security.")]
    return _svg("".join(p), h=186)


def _d_query():
    p = [_node(255, 12, 130, 60, "Agent", "needs a lane"),
         _node(235, 105, 170, 60, "registry.json", "one request", "#6ee7ff"),
         _node(40, 190, 150, 55, "Site A lane", "primer + grants"),
         _node(450, 190, 150, 55, "Site B lane", "mcp bridge"),
         _arrow(320, 72, 320, 100, "fetches", lx=352, ly=90),
         _arrow(285, 165, 125, 190),
         _arrow(355, 165, 515, 190),
         _cap(320, 272, "One fetch. Every lane. No scraping.")]
    return _svg("".join(p), h=282)


DIAGRAMS = {
    "retrofit-ladder": _d_retrofit_ladder(),
    "machine-readable-primer": _d_primer(),
    "scoped-ai-grants": _d_grants(),
    "stage-and-approve": _d_stage(),
    "well-known-discovery": _d_wellknown(),
    "agent-credentials": _d_credentials(),
    "no-simulated-execution": _d_nosim(),
    "mcp-bridge": _d_mcp(),
    "querying-the-registry": _d_query(),
    "ceremony-blueprint": _d_ceremony(),
    "status-receipt": _d_status(),
    "oauth-scoped-grants": _d_oauth_grants(),
    "flask-stage-and-approve": _d_flask_seq(),
    "primer-file-format": _d_primer_anatomy(),
}


# "Which method do you need?" — a 3-question weighted quiz shown on the
# Methods index page. Weights point at method slugs; titles resolve at build.
QUIZ_QUESTIONS = [
    {"q": "What do you want agents to do with your site?",
     "opts": [
         {"t": "Read my content accurately",
          "w": {"machine-readable-primer": 2, "primer-file-format": 1,
                "well-known-discovery": 1}},
         {"t": "Take actions — post, book, change things",
          "w": {"stage-and-approve": 2, "flask-stage-and-approve": 1,
                "status-receipts": 1}},
         {"t": "Prove identity and get permission first",
          "w": {"oauth-scoped-grants": 2, "scoped-ai-grants": 1,
                "agent-credentials": 1}},
         {"t": "Not sure yet — where do I even start?",
          "w": {"retrofit-ladder": 3, "matrix": 1}},
     ]},
    {"q": "Who gives the final okay when an agent acts?",
     "opts": [
         {"t": "A human reviews each action",
          "w": {"stage-and-approve": 2, "ceremony-blueprint": 1}},
         {"t": "Pre-approved scopes decide",
          "w": {"oauth-scoped-grants": 2, "scoped-ai-grants": 1}},
         {"t": "It is read-only — no approval needed",
          "w": {"machine-readable-primer": 2, "well-known-discovery": 1}},
         {"t": "The agent reports back when it is done",
          "w": {"status-receipts": 2, "stage-and-approve": 1}},
     ]},
    {"q": "What kind of site is it?",
     "opts": [
         {"t": "A content or docs site",
          "w": {"machine-readable-primer": 2, "primer-file-format": 1}},
         {"t": "An app with user accounts",
          "w": {"stage-and-approve": 2, "oauth-scoped-grants": 1}},
         {"t": "I run tools over MCP, or want assist-only",
          "w": {"mcp-bridge": 3}},
         {"t": "I want my site listed in a registry",
          "w": {"ceremony-blueprint": 2, "querying-the-registry": 1}},
     ]},
]


def quiz_block(pages):
    """HTML + JS for the method-picker quiz (Methods index only)."""
    titles = {p["slug"].split("/")[-1]: p["title"] for p in pages
              if p["section"] == "methods"}
    questions = jdumps(QUIZ_QUESTIONS).replace("</", "<\\/")
    title_map = jdumps(titles).replace("</", "<\\/")
    html_part = (
        "<div class='card quiz' id='wki-quiz'>\n"
        "<h3>Which method do you need?</h3>\n"
        "<p class='meta'>Three questions, sixty seconds — "
        "we will point you at the right pattern.</p>\n"
        "<div id='quiz-body'></div>\n</div>\n"
    )
    js_part = (
        "<script>\n(function(){\n"
        "var root=document.getElementById('wki-quiz');if(!root)return;\n"
        "var body=document.getElementById('quiz-body');\n"
        f"var QUESTIONS={questions};\n"
        f"var TITLES={title_map};\n"
        "var scores={},qi=0;\n"
        "function esc(s){return String(s).replace(/[&<>]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}\n"
        "function renderQ(){\n"
        "var q=QUESTIONS[qi];\n"
        "var h='<div class=\"quiz-q\"><p>'+(qi+1)+'. '+esc(q.q)+'</p><div class=\"quiz-opts\">';\n"
        "q.opts.forEach(function(o,i){h+='<button type=\"button\" data-i=\"'+i+'\">'+esc(o.t)+'</button>';});\n"
        "body.innerHTML=h+'</div></div>';\n"
        "Array.prototype.forEach.call(body.querySelectorAll('button'),function(b){\n"
        "b.addEventListener('click',function(){\n"
        "var w=q.opts[+b.getAttribute('data-i')].w;\n"
        "for(var k in w){scores[k]=(scores[k]||0)+w[k];}\n"
        "qi++;\n"
        "if(qi<QUESTIONS.length){renderQ();}else{renderR();}\n"
        "});});}\n"
        "function renderR(){\n"
        "var ranked=Object.keys(scores).sort(function(a,b){return scores[b]-scores[a];}).slice(0,2);\n"
        "var h='<div class=\"quiz-result\"><p><strong>Start here:</strong></p><ul>';\n"
        "ranked.forEach(function(s){h+='<li><a href=\"./'+s+'/\">'+esc(TITLES[s]||s)+'</a></li>';});\n"
        "h+='</ul><p>Or climb the <a href=\"./retrofit-ladder/\">Retrofit Ladder</a> from the bottom, '\n"
        "+'or browse the <a href=\"./matrix/\">Methods Matrix</a> for the full map.</p>';\n"
        "h+='<div class=\"quiz-opts\"><button type=\"button\" id=\"quiz-again\">Start over</button></div>';\n"
        "body.innerHTML=h+'</div>';\n"
        "document.getElementById('quiz-again').addEventListener('click',function(){scores={};qi=0;renderQ();});}\n"
        "renderQ();\n})();\n</script>"
    )
    return html_part, js_part


# ---------------------------------------------------------------- template
CSS = """
:root{--bg:#0b0e14;--panel:#11151f;--line:#1e2636;--txt:#dbe2f0;--dim:#8b95ad;
--acc:#6ee7ff;--acc2:#a78bfa;--code:#0e1420;--head:#ffffff;--hbar:rgba(11,14,20,.92);color-scheme:dark}
[data-theme="light"]{--bg:#f5f8fd;--panel:#ffffff;--line:#dbe4f3;--txt:#1b2740;
--dim:#57688a;--acc:#0b6bcb;--acc2:#7c3aed;--code:#ebf1fa;--head:#0d1626;--hbar:rgba(245,248,253,.94);color-scheme:light}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);
font-family:ui-sans-serif,system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
line-height:1.65}
.wrap{max-width:760px;margin:0 auto;padding:0 1.25rem}
header.site{border-bottom:1px solid var(--line);background:var(--hbar)}
header.site .wrap{display:flex;align-items:center;gap:1.5rem;padding:1rem 1.25rem;flex-wrap:wrap}
.brand{font-weight:700;letter-spacing:.04em;color:var(--head);text-decoration:none;font-size:1.1rem}
.brand span{color:var(--acc)}
nav.main{display:flex;gap:1.1rem;margin-left:auto}
nav.main a{color:var(--dim);text-decoration:none;font-size:.95rem}
nav.main a:hover,nav.main a.on{color:var(--acc)}
main .wrap{padding-top:2rem;padding-bottom:3rem}
h1,h2,h3{color:var(--head);line-height:1.25}
h1{font-size:1.9rem;margin:.2em 0 .6em}
h2{font-size:1.35rem;margin-top:2em;border-bottom:1px solid var(--line);padding-bottom:.35em}
a{color:var(--acc)}
code{background:var(--code);border:1px solid var(--line);border-radius:4px;
padding:.1em .35em;font-size:.88em}
pre{background:var(--code);border:1px solid var(--line);border-radius:8px;
padding:1rem;overflow-x:auto}
pre code{background:none;border:none;padding:0}
blockquote{border-left:3px solid var(--acc2);margin:1.2em 0;padding:.2em 1em;
color:var(--dim);background:var(--panel);border-radius:0 8px 8px 0}
hr{border:none;border-top:1px solid var(--line);margin:2em 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;
padding:1.1rem 1.25rem;margin:1rem 0}
.card h3{margin:.1em 0 .3em;font-size:1.15rem}
.card h3 a{color:var(--head);text-decoration:none}
.card h3 a:hover{color:var(--acc)}
.card p{margin:.4em 0;color:var(--dim)}
.meta{font-size:.8rem;color:var(--dim)}
.tag{display:inline-block;font-size:.75rem;border:1px solid var(--line);
border-radius:20px;padding:.05em .7em;margin:.15em .25em .15em 0;color:var(--dim)}
footer.site{border-top:1px solid var(--line);color:var(--dim);font-size:.85rem}
footer.site .wrap{padding-top:1.2rem;padding-bottom:2rem;display:flex;
gap:1.5rem;flex-wrap:wrap;align-items:center}
footer.site .jsonlink{margin-left:auto}
input.filter,select.filter{background:var(--code);border:1px solid var(--line);
color:var(--txt);border-radius:8px;padding:.7rem 1rem;font-size:1rem}
input.filter{width:100%;margin:1rem 0}
.frow{display:flex;gap:.75rem;flex-wrap:wrap;margin:0 0 1rem}
.frow select{flex:1;min-width:9rem}
.kv{display:grid;grid-template-columns:11rem 1fr;gap:.3rem 1rem;margin:1em 0;
font-size:.92rem}
.kv dt{color:var(--dim)}
.kv dd{margin:0}
.stars{color:var(--acc2);letter-spacing:.3em;font-size:.8rem}
figure.diagram{margin:1.5rem 0;background:var(--panel);border:1px solid var(--line);
border-radius:12px;padding:1.25rem .75rem}
figure.diagram svg{display:block;width:100%;height:auto}
.tablewrap{overflow-x:auto;margin:1.2em 0;border:1px solid var(--line);border-radius:8px}
.tablewrap table{border-collapse:collapse;width:100%;font-size:.92rem;margin:0}
.tablewrap th,.tablewrap td{text-align:left;padding:.6em .9em;
border-bottom:1px solid var(--line);vertical-align:top}
.tablewrap thead th{background:var(--panel);color:var(--head);font-weight:600;white-space:nowrap}
.tablewrap tbody tr:last-child td{border-bottom:none}
.noresults{display:none}
.skip{position:absolute;left:-9999px;top:0;background:var(--acc);color:#0b0e14;
font-weight:700;padding:.6rem 1rem;z-index:100;border-radius:0 0 8px 0}
.skip:focus{left:0}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px;border-radius:4px}
.header-tools{display:flex;align-items:center;gap:.6rem;margin-left:auto}
nav.main{margin-left:0}
.hsearch{position:relative}
.hsearch input{background:var(--code);border:1px solid var(--line);color:var(--txt);
border-radius:20px;padding:.45rem 1rem;font-size:.9rem;width:11rem}
.hsearch input:focus{width:15rem;border-color:var(--acc)}
.sresults{position:absolute;top:calc(100% + .4rem);right:0;width:19rem;max-height:22rem;
overflow-y:auto;background:var(--panel);border:1px solid var(--line);border-radius:10px;
box-shadow:0 12px 32px rgba(0,0,0,.35);z-index:50}
.sresult{display:block;padding:.6rem .9rem;text-decoration:none;border-bottom:1px solid var(--line)}
.sresult:last-child{border-bottom:none}
.sresult:hover{background:var(--code)}
.sresult .st{display:block;color:var(--head);font-weight:600;font-size:.92rem}
.sresult .ss{font-size:.78rem;color:var(--dim);text-transform:capitalize}
.sresult.none{color:var(--dim);font-size:.9rem}
.themetoggle{background:var(--code);border:1px solid var(--line);color:var(--txt);
border-radius:50%;width:2.2rem;height:2.2rem;font-size:1.05rem;cursor:pointer;line-height:1}
.themetoggle:hover{border-color:var(--acc)}
.hero{text-align:center;padding:1.5rem 0 .5rem}
.hero .stars{margin-bottom:.5rem}
.quiz{border-color:var(--acc2)}
.quiz h3{margin-top:0}
.quiz-q{margin:1rem 0}
.quiz-q p{font-weight:600;color:var(--head);margin:.4em 0 .6em}
.quiz-opts{display:flex;flex-wrap:wrap;gap:.5rem}
.quiz-opts button{background:var(--code);border:1px solid var(--line);color:var(--txt);
border-radius:20px;padding:.5rem 1rem;font-size:.9rem;cursor:pointer}
.quiz-opts button:hover{border-color:var(--acc2);color:var(--head)}
.quiz-result p{color:var(--dim)}
.quiz-result strong{color:var(--head)}
@media (max-width:640px){
.hsearch input{width:8rem}
.hsearch input:focus{width:10rem}
.sresults{width:16rem;position:fixed;top:3.6rem;left:.75rem;right:.75rem;width:auto}
header.site .wrap{gap:.8rem}
}
"""

# Theme init runs before first paint so a saved light theme never flashes dark.
THEME_INIT = """<script>!function(){try{var s=localStorage.getItem("wki-theme");var t=s||(window.matchMedia("(prefers-color-scheme: light)").matches?"light":"dark");document.documentElement.dataset.theme=t;}catch(e){document.documentElement.dataset.theme="dark";}}();</script>"""

# Site-wide behavior: theme toggle + client-side search over search.json.
# Dependency-free, works on any static host.
GLOBAL_JS = """<script>
(function(){
var b=document.getElementById('themetoggle');
if(b){
function paint(){var t=document.documentElement.dataset.theme||'dark';
b.textContent=(t==='light')?'\\u2600':'\\u263e';
b.setAttribute('aria-pressed',(t==='light')?'true':'false');
b.setAttribute('aria-label',(t==='light')?'Switch to dark theme':'Switch to light theme');}
b.addEventListener('click',function(){
var t=(document.documentElement.dataset.theme==='light')?'dark':'light';
document.documentElement.dataset.theme=t;
try{localStorage.setItem('wki-theme',t);}catch(e){}
paint();});
paint();
}
var inp=document.getElementById('site-search');
if(!inp)return;
var box=document.getElementById('sresults'),data=null,items=[];
var root=inp.getAttribute('data-root')||'./';
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function load(cb){if(data){cb(data);return;}
fetch(root+'search.json').then(function(r){return r.json();}).then(function(j){data=j;cb(j);}).catch(function(){cb([]);});}
inp.addEventListener('input',function(){
var q=inp.value.trim().toLowerCase();
if(q.length<2){box.hidden=true;return;}
load(function(d){
items=d.filter(function(p){return (p.title+' '+p.summary+' '+p.section).toLowerCase().indexOf(q)>-1;}).slice(0,8);
if(!items.length){box.innerHTML='<div class="sresult none">No matches. Try the <a href="'+root+'registry/">registry</a> or <a href="'+root+'methods/">methods</a>.</div>';box.hidden=false;return;}
box.innerHTML=items.map(function(p){return '<a class="sresult" role="option" href="'+root+p.path+'"><span class="st">'+esc(p.title)+'</span><span class="ss">'+esc(p.section)+'</span></a>';}).join('');
box.hidden=false;});});
inp.addEventListener('keydown',function(e){
if(e.key==='Escape'){box.hidden=true;inp.blur();}
if(e.key==='Enter'&&items.length){window.location.href=root+items[0].path;}});
document.addEventListener('click',function(e){if(!e.target.closest('.hsearch'))box.hidden=true;});
})();
</script>"""

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · WellKnownIndex</title>
<meta name="description" content="{description}">
<meta name="theme-color" content="#0b0e14">
<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{root}favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="{root}apple-touch-icon.png">
<link rel="manifest" href="{root}site.webmanifest">
<meta property="og:type" content="website">
<meta property="og:site_name" content="WellKnownIndex">
<meta property="og:title" content="{title} · WellKnownIndex">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{page_url}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title} · WellKnownIndex">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{og_image}">
{theme_init}
<script type="application/ld+json">{jsonld}</script>
<style>{css}</style>
</head>
<body>
<header class="site"><div class="wrap">
<a class="skip" href="#main">Skip to content</a>
<a class="brand" href="{root}">WellKnown<span>Index</span></a>
<nav class="main" aria-label="Sections">
<a href="{root}methods/" class="{m_on}">Methods</a>
<a href="{root}registry/" class="{r_on}">Registry</a>
<a href="{root}field-notes/" class="{f_on}">Field notes</a>
</nav>
<div class="header-tools">
<div class="hsearch">
<input id="site-search" type="search" placeholder="Search the index&hellip;" aria-label="Search the index" autocomplete="off" data-root="{root}">
<div class="sresults" id="sresults" role="listbox" aria-label="Search results" hidden></div>
</div>
<button class="themetoggle" id="themetoggle" aria-label="Switch color theme">&#9681;</button>
</div>
</div></header>
<main id="main"><div class="wrap">
{body}
</div></main>
<footer class="site"><div class="wrap">
<span>WellKnownIndex — a free public commons. No ads, no tracking.</span>
<a href="{root}contribute/">Contribute</a>
<a href="{root}llms.txt">llms.txt</a>
<a class="jsonlink" href="{json_url}">machine-readable JSON &#8599;</a>
<a href="{md_url}">page as markdown &#8595;</a>
</div></div></footer>
{extra_js}{global_js}
</body>
</html>
"""


def page_html(title, body_html, section, root, json_url, extra_js="",
              page_url="", description="", md_url=""):
    on = {s: ("on" if s == section else "") for s in ("methods", "registry", "field-notes")}
    desc = description or SITE_TAGLINE
    jsonld = jdumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": desc,
        "url": page_url or SITE_URL + "/",
        "isPartOf": {
            "@type": "WebSite",
            "name": SITE_TITLE,
            "url": SITE_URL + "/",
            "description": SITE_TAGLINE,
        },
    }).replace("</", "<\\/")
    return TEMPLATE.format(
        title=html.escape(title), css=CSS, body=body_html, root=root,
        json_url=json_url, md_url=md_url, extra_js=extra_js,
        global_js=GLOBAL_JS, theme_init=THEME_INIT, jsonld=jsonld,
        page_url=page_url or SITE_URL + "/",
        description=html.escape(desc, quote=True),
        og_image=SITE_URL + "/og-image.jpg",
        m_on=on["methods"], r_on=on["registry"], f_on=on["field-notes"],
    )


# ------------------------------------------------------------------- build
def main():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    pages = []  # dicts: slug, section, title, summary, rel, meta

    for md_path in sorted(CONTENT.rglob("*.md")):
        rel = md_path.relative_to(CONTENT).with_suffix("")  # e.g. methods/x or index
        meta, body = parse_md(md_path)
        section = meta.get("section", "home")
        title = meta.get("title", rel.name)
        summary = meta.get("summary", "")
        depth = 0 if str(rel) == "index" else len(rel.parts)  # ../ levels to docs/
        root = "../" * depth if depth else "./"
        body_html = render_markdown(body, depth)

        # machine-readable fact box for registry entries
        if section == "registry":
            for pr in (meta.get("protocols") or []):
                _check_protocol(md_path, pr)
            facts = []
            for key in ("site_url", "cost"):
                if meta.get(key) is not None:
                    facts.append((key.replace("_", " ").title(), meta[key]))
            for key, label in (("protocols", "Protocols"), ("auth_schemes", "Auth"),
                               ("scopes", "Scopes"), ("methods_implemented", "Methods")):
                vals = meta.get(key) or []
                if vals:
                    if key == "protocols":
                        parts = []
                        for p in vals:
                            bits = f"<code>{html.escape(p.get('type', ''))}</code> "
                            if p.get("url"):
                                u = html.escape(p["url"])
                                bits += f"<a href='{u}'>{u}</a>"
                            if p.get("url_template"):
                                bits += ("<br><span class='meta'>template: "
                                         f"<code>{html.escape(p['url_template'])}</code></span>")
                            if p.get("version"):
                                bits += (f" <span class='meta'>v"
                                         f"{html.escape(str(p['version']))}</span>")
                            if p.get("note"):
                                bits += (f"<br><span class='meta'>"
                                         f"{html.escape(p['note'])}</span>")
                            parts.append(bits)
                        rendered = "<br>".join(parts)
                    else:
                        rendered = ", ".join(f"<code>{html.escape(str(v))}</code>" for v in vals)
                    facts.append((label, rendered))
            # WKI-04: verification is a date plus stated evidence, not a bare date
            if meta.get("verified") is not None:
                ev = "".join(
                    f"<li>{html.escape(str(e))}</li>"
                    for e in (meta.get("verified_evidence") or []))
                facts.append(("Verification",
                              html.escape(str(meta["verified"]))
                              + (f"<ul>{ev}</ul>" if ev else "")))
            if facts:
                rows = "".join(
                    f"<dt>{html.escape(k)}</dt><dd>{v if k in ('Protocols',) else html.escape(str(v)) if not str(v).startswith('<') else v}</dd>"
                    for k, v in facts
                )
                body_html += f"\n<h2>Machine-readable facts</h2>\n<dl class='kv'>{rows}</dl>"

        # visual explainer diagram (frontmatter: diagram: <name>)
        diagram_name = meta.get("diagram")
        if diagram_name and diagram_name in DIAGRAMS:
            fig = f"<figure class='diagram'>{DIAGRAMS[diagram_name]}</figure>"
            if "</h1>" in body_html:
                body_html = body_html.replace("</h1>", "</h1>\n" + fig, 1)
            else:
                body_html = fig + "\n" + body_html

        out_dir = DOCS if str(rel) == "index" else DOCS / rel
        out_dir.mkdir(parents=True, exist_ok=True)
        json_url = root + (str(rel) + ".json" if str(rel) != "index" else "home.json")
        md_url = root + (str(rel) + ".md" if str(rel) != "index" else "home.md")
        page_url = SITE_URL + ("/" if str(rel) == "index" else f"/{rel}/")
        html_page = page_html(title, body_html, section, root, json_url,
                              page_url=page_url, description=summary, md_url=md_url)
        (out_dir / "index.html").write_text(html_page, encoding="utf-8")

        # JSON twin — absolute, self-resolving URLs from the single base
        # config (WKI-02). Homepage twin is home.json: the documented exception.
        is_home = str(rel) == "index"
        twin = {
            "title": title, "section": section, "summary": summary,
            "url": SITE_URL + ("/" if is_home else f"/{rel}/"),
            "json_url": SITE_URL + ("/home.json" if is_home else f"/{rel}.json"),
            "body_markdown": body,
        }
        for k, v in meta.items():
            if k not in twin:
                twin[k] = v
        twin_path = DOCS / (str(rel) + ".json" if str(rel) != "index" else "home.json")
        twin_path.write_text(jdumps(twin, indent=2), encoding="utf-8")

        pages.append({"slug": str(rel), "section": section, "title": title,
                      "summary": summary, "meta": meta, "body": body})

    # section index pages (methods, registry, field-notes)
    for sec, sec_title in SECTIONS.items():
        items = [p for p in pages if p["section"] == sec]
        cards = []
        facet_methods, facet_protocols, facet_auth = [], [], []
        if sec == "registry":
            facet_methods = sorted({str(m) for p in items
                                    for m in (p["meta"].get("methods_implemented") or [])})
            facet_protocols = sorted({str(pr.get("type")) for p in items
                                      for pr in (p["meta"].get("protocols") or [])
                                      if pr.get("type")})
            facet_auth = sorted({str(a) for p in items
                                 for a in (p["meta"].get("auth_schemes") or [])})
        for p in sorted(items, key=lambda x: x["title"]):
            slug = p["slug"].split("/")[-1]
            tags = ""
            data_attrs = ""
            if sec == "registry":
                meths = p["meta"].get("methods_implemented") or []
                tags = "".join(f"<span class='tag'>{html.escape(m)}</span>" for m in meths)
                cost = p["meta"].get("cost")
                if cost:
                    tags += f"<span class='tag'>cost: {html.escape(str(cost))}</span>"
                ver = p["meta"].get("verified")
                if ver:
                    tags += f"<span class='tag'>verified {html.escape(str(ver))}</span>"
                meth_vals = " ".join(str(m).lower() for m in meths)
                prot_vals = " ".join(str(pr.get("type", "")).lower()
                                     for pr in (p["meta"].get("protocols") or []))
                auth_vals = " ".join(str(a).lower()
                                      for a in (p["meta"].get("auth_schemes") or []))
                data_attrs = (f" data-methods='{html.escape(meth_vals)}'"
                              f" data-protocols='{html.escape(prot_vals)}'"
                              f" data-auth='{html.escape(auth_vals)}'"
                              f" data-cost='{html.escape(str(cost or '').lower())}'")
            cards.append(
                f"<div class='card' data-search='{html.escape((p['title'] + ' ' + p['summary']).lower())}'{data_attrs}>"
                f"<h3><a href='./{slug}/'>{html.escape(p['title'])}</a></h3>"
                f"<p>{html.escape(p['summary'])}</p>{tags}</div>"
            )
        filter_box = ""
        extra_js = ""
        if sec == "registry":
            def _opts(vals):
                return "".join(
                    f"<option value='{html.escape(v)}'>{html.escape(v)}</option>"
                    for v in vals)
            filter_box = (
                "<input class='filter' id='q' type='search' "
                "placeholder='Filter registry — try \"primer\", \"free\", \"mcp-bridge\"…'>"
                "<div class='frow'>"
                f"<select class='filter' id='f_method'><option value=''>Method: all</option>{_opts(facet_methods)}</select>"
                f"<select class='filter' id='f_protocol'><option value=''>Protocol: all</option>{_opts(facet_protocols)}</select>"
                f"<select class='filter' id='f_auth'><option value=''>Auth: all</option>{_opts(facet_auth)}</select>"
                "</div>"
                "<p class='meta noresults' id='noresults'>No entries match those "
                "filters — try clearing one, or "
                "<a href='../contribute/'>propose the missing site</a>.</p>"
            )
            extra_js = """<script>
const q=document.getElementById('q'),fm=document.getElementById('f_method'),
fp=document.getElementById('f_protocol'),fa=document.getElementById('f_auth');
function currentFilters(){return{q:q.value,method:fm.value,protocol:fp.value,auth:fa.value};}
function apply(){
  const f=currentFilters(),needle=f.q.toLowerCase();
  let vis=0;
  document.querySelectorAll('.card').forEach(c=>{
    const okT=!needle||c.dataset.search.includes(needle);
    const okM=!f.method||c.dataset.methods.split(' ').includes(f.method.toLowerCase());
    const okP=!f.protocol||c.dataset.protocols.split(' ').includes(f.protocol.toLowerCase());
    const okA=!f.auth||c.dataset.auth.split(' ').includes(f.auth.toLowerCase());
    const show=(okT&&okM&&okP&&okA);
    c.style.display=show?'':'none';
    if(show)vis++;
  });
  document.getElementById('noresults').style.display=vis?'none':'';
  const sp=new URLSearchParams();
  for(const kv of Object.entries(f)){if(kv[1])sp.set(kv[0],kv[1]);}
  history.replaceState(null,'',sp.toString()?('?'+sp.toString()):location.pathname);
}
[q,fm,fp,fa].forEach(el=>el.addEventListener('input',apply));
(function init(){
  const sp=new URLSearchParams(location.search);
  if(sp.get('q'))q.value=sp.get('q');
  for(const pair of[[fm,'method'],[fp,'protocol'],[fa,'auth']]){
    const v=sp.get(pair[1]);
    if(v&&[...pair[0].options].some(o=>o.value===v))pair[0].value=v;
  }
  apply();
})();
</script>"""
        add_line = ""
        if sec == "registry":
            add_line = ("<p class='meta'>Know an agent-friendly site? "
                        "<a href='../contribute/'>Add it to the registry</a>.</p>\n"
                        "<p class='meta'><strong>Most wanted:</strong> public MCP servers, "
                        "sites publishing agent docs or primers, staged-write APIs, "
                        "and credential/grant flows we haven't catalogued yet.</p>\n")
        body_html = (f"<div class='stars'>✦ ✦ ✦</div>\n<h1>{sec_title}</h1>\n"
                     f"{add_line}{filter_box}\n" + "\n".join(cards))
        if sec == "methods":
            quiz_html, quiz_js = quiz_block(pages)
            body_html = body_html.replace(
                f"<h1>{sec_title}</h1>\n",
                f"<h1>{sec_title}</h1>\n{quiz_html}", 1)
            extra_js = quiz_js + extra_js
        sec_dir = DOCS / sec
        sec_dir.mkdir(parents=True, exist_ok=True)
        (sec_dir / "index.html").write_text(
            page_html(sec_title, body_html, sec, "../", f"../{sec}.json", extra_js,
                      page_url=f"{SITE_URL}/{sec}/", description=SITE_TAGLINE,
                      md_url=f"../{sec}.md"),
            encoding="utf-8",
        )
        # section JSON listing — absolute URLs (WKI-02)
        sec_json = [{"slug": p["slug"], "title": p["title"], "summary": p["summary"],
                     "url": f"{SITE_URL}/{sec}/{p['slug'].split('/')[-1]}/",
                     "json_url": f"{SITE_URL}/{sec}/{p['slug'].split('/')[-1]}.json"}
                    for p in sorted(items, key=lambda x: x["title"])]
        (DOCS / f"{sec}.json").write_text(jdumps(sec_json, indent=2), encoding="utf-8")

    # registry.json — the queryable index
    registry = []
    for p in pages:
        if p["section"] != "registry":
            continue
        m = p["meta"]
        slug = p["slug"].split("/")[-1]
        registry.append({
            "slug": slug, "title": p["title"], "summary": p["summary"],
            "site_url": m.get("site_url"), "protocols": m.get("protocols") or [],
            "auth_schemes": m.get("auth_schemes") or [],
            "scopes": m.get("scopes") or [],
            "methods_implemented": m.get("methods_implemented") or [],
            "cost": m.get("cost"), "verified": m.get("verified"),
            "verified_evidence": m.get("verified_evidence") or [],
            "url": f"{SITE_URL}/registry/{slug}/",
            "json_url": f"{SITE_URL}/registry/{slug}.json",
        })
    (DOCS / "registry.json").write_text(jdumps(registry, indent=2), encoding="utf-8")

    # index.json — site map, absolute URLs (WKI-02)
    sitemap = {
        "site": SITE_TITLE, "tagline": SITE_TAGLINE,
        "generated": date.today().isoformat(),
        "sections": [{"slug": s, "title": t, "url": f"{SITE_URL}/{s}/",
                      "json_url": f"{SITE_URL}/{s}.json"}
                     for s, t in SECTIONS.items()],
        "pages": [{"slug": p["slug"], "section": p["section"], "title": p["title"],
                   "summary": p["summary"],
                   "url": SITE_URL + ("/" if p["slug"] == "index" else f"/{p['slug']}/"),
                   "json_url": SITE_URL + ("/home.json" if p["slug"] == "index"
                                           else f"/{p['slug']}.json")}
                  for p in sorted(pages, key=lambda x: x["slug"])],
        "registry": f"{SITE_URL}/registry.json",
    }
    (DOCS / "index.json").write_text(jdumps(sitemap, indent=2), encoding="utf-8")

    # static passthrough: files under static/ are copied verbatim into docs/
    static_dir = ROOT / "static"
    if static_dir.exists():
        for src in static_dir.rglob("*"):
            if src.is_file():
                dest = DOCS / src.relative_to(static_dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)

    # .well-known discovery file — the wiki dogfoods its own well-known-discovery method
    wk_dir = DOCS / ".well-known"
    wk_dir.mkdir(parents=True, exist_ok=True)
    discovery = {
        "service": SITE_TITLE,
        "description": SITE_TAGLINE,
        "version": "1.0",
        "updated": date.today().isoformat(),
        "endpoints": {
            "registry": f"{SITE_URL}/registry.json",
            "site_index": f"{SITE_URL}/index.json",
            "methods": f"{SITE_URL}/methods.json",
            "field_notes": f"{SITE_URL}/field-notes.json",
            "registry_human": f"{SITE_URL}/registry/",
            "contribute": f"{SITE_URL}/contribute/",
            "contribute_json": f"{SITE_URL}/contribute.json",
            "entry_schema": f"{SITE_URL}/schema/registry-entry.json",
            "llms_txt": f"{SITE_URL}/llms.txt",
            "llms_full_txt": f"{SITE_URL}/llms-full.txt",
            "search_index": f"{SITE_URL}/search.json",
        },
        "machine_surfaces": (
            "Every page is triple-rendered: human HTML, a .json twin, and a "
            ".md markdown twin. llms.txt summarizes the site for language "
            "models; llms-full.txt carries the complete text; search.json "
            "powers client-side search."
        ),
        "registry_page_filters": {
            "q": "free-text search",
            "method": "implemented method slug, e.g. stage-and-approve",
            "protocol": "protocol type, e.g. ai-primer",
            "auth": "auth scheme identifier",
        },
        "deployment": {
            "base_url": SITE_URL,
            "discovery_note": (
                "Project-path deployment on GitHub Pages: the discovery "
                "document lives under the project prefix, not the origin "
                "root. A root deployment serves it at "
                "/.well-known/wellknownindex.json per RFC 8615."
            ),
        },
        "contributing": "https://github.com/MASAGDT/wellknownindex/issues",
        "license": "https://github.com/MASAGDT/wellknownindex/blob/main/LICENSE",
        "license_note": "Free public commons. No ads, no tracking.",
    }
    (wk_dir / "wellknownindex.json").write_text(jdumps(discovery, indent=2), encoding="utf-8")
    # disable Jekyll so dot-directories like .well-known are served verbatim
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    # 404 page — GitHub Pages serves this for unknown paths
    notfound_body = (
        "<div class='stars'>✦ ✦ ✦</div>\n<h1>404 — lost in the index</h1>\n"
        "<p>That path isn't in the registry. Try the "
        "<a href='./'>home page</a>, the <a href='./methods/'>methods</a>, "
        "or the <a href='./registry/'>registry</a> — "
        "or <a href='./contribute/'>propose</a> the entry you were looking for.</p>\n"
    )
    (DOCS / "404.html").write_text(
        page_html("Not found", notfound_body, "home", "./", "./home.json",
                  page_url=SITE_URL + "/", description=SITE_TAGLINE,
                  md_url="./home.md"),
        encoding="utf-8",
    )

    # robots.txt + sitemap.xml for crawlers (human and machine)
    (DOCS / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )
    locs = [SITE_URL + "/"]
    locs += [f"{SITE_URL}/{p['slug']}/" for p in pages if p["slug"] != "index"]
    locs += [f"{SITE_URL}/{s}/" for s in SECTIONS]
    sitemap_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in locs)
        + "</urlset>\n"
    )
    (DOCS / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")

    # search.json — client-side search index (title, summary, section, path)
    search_index = [
        {"title": p["title"], "summary": p["summary"], "section": p["section"],
         "path": "" if p["slug"] == "index" else p["slug"] + "/"}
        for p in pages
    ]
    (DOCS / "search.json").write_text(jdumps(search_index, indent=2), encoding="utf-8")

    # per-page markdown twins — clean source text for agents and readers.
    # Mirrors the .json twin naming: home.md for the homepage.
    def _md_page(p):
        url = SITE_URL + ("/" if p["slug"] == "index" else f"/{p['slug']}/")
        jsu = SITE_URL + ("/home.json" if p["slug"] == "index" else f"/{p['slug']}.json")
        head = f"# {p['title']}\n"
        if p["summary"]:
            head += f"\n> {p['summary']}\n"
        head += f"\nHTML: {url}\nJSON: {jsu}\n\n---\n\n"
        return head + p["body"].rstrip() + "\n"

    for p in pages:
        md_path = DOCS / ("home.md" if p["slug"] == "index" else p["slug"] + ".md")
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(_md_page(p), encoding="utf-8")

    # section markdown listings (methods.md, registry.md, field-notes.md)
    for sec, sec_title in SECTIONS.items():
        items = [p for p in pages if p["section"] == sec]
        lines = [f"# {sec_title}\n", f"\n{SITE_URL}/{sec}/\n"]
        for p in sorted(items, key=lambda x: x["title"]):
            slug = p["slug"].split("/")[-1]
            lines.append(
                f"\n## {p['title']}\n\n{p['summary']}\n\n"
                f"- HTML: {SITE_URL}/{sec}/{slug}/\n"
                f"- JSON: {SITE_URL}/{sec}/{slug}.json\n"
                f"- Markdown: {SITE_URL}/{sec}/{slug}.md\n")
        (DOCS / f"{sec}.md").write_text("".join(lines), encoding="utf-8")

    # llms.txt — the agent-facing summary of the whole site
    llms_lines = [
        f"# {SITE_TITLE}\n",
        f"\n> {SITE_TAGLINE}\n",
        "\nEvery page on this site is triple-rendered: human HTML, a `.json` "
        "twin, and a `.md` markdown twin. Fetch `/llms-full.txt` for the "
        "complete text of every page, or `/index.json` for the "
        "machine-readable site map.\n",
    ]
    for sec, sec_title in SECTIONS.items():
        llms_lines.append(f"\n## {sec_title}\n")
        sec_items = sorted([p for p in pages if p["section"] == sec],
                           key=lambda x: x["title"])
        for p in sec_items:
            url = SITE_URL + ("/" if p["slug"] == "index" else f"/{p['slug']}/")
            llms_lines.append(f"- [{p['title']}]({url}): {p['summary']}\n")
    llms_lines.append(
        "\n## Contribute\n\n"
        f"- [Contribute]({SITE_URL}/contribute/): propose a registry entry, "
        "a method, or a field note.\n")
    (DOCS / "llms.txt").write_text("".join(llms_lines), encoding="utf-8")

    # llms-full.txt — the entire site as markdown, for agents that want it all
    full_lines = [
        f"# {SITE_TITLE} — complete text\n",
        f"\n> {SITE_TAGLINE}\n",
        f"\nSource: {SITE_URL}/ — generated {date.today().isoformat()}.\n",
    ]
    for p in sorted(pages, key=lambda x: x["slug"]):
        url = SITE_URL + ("/" if p["slug"] == "index" else f"/{p['slug']}/")
        full_lines.append(f"\n\n{'=' * 70}\n# {p['title']}\n{url}\n{'=' * 70}\n\n")
        if p["summary"]:
            full_lines.append(f"> {p['summary']}\n\n")
        full_lines.append(p["body"].rstrip() + "\n")
    (DOCS / "llms-full.txt").write_text("".join(full_lines), encoding="utf-8")

    print(f"built {len(pages)} pages -> {DOCS}")


if __name__ == "__main__":
    main()
