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
        else:
            close_lists()
            # gather paragraph lines
            para = [s]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not re.match(
                r"^(#{1,3}\s|```|>|[-*]\s+|\d+\.\s+|---$)", lines[j].strip()
            ):
                para.append(lines[j].strip())
                j += 1
            out.append(f"<p>{inline(' '.join(para))}</p>")
            i = j - 1
        i += 1
    close_lists()
    return fix_links("\n".join(out), depth)


# ---------------------------------------------------------------- template
CSS = """
:root{--bg:#0b0e14;--panel:#11151f;--line:#1e2636;--txt:#dbe2f0;--dim:#8b95ad;
--acc:#6ee7ff;--acc2:#a78bfa;--code:#0e1420}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);
font-family:ui-sans-serif,system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
line-height:1.65}
.wrap{max-width:760px;margin:0 auto;padding:0 1.25rem}
header.site{border-bottom:1px solid var(--line);background:rgba(11,14,20,.9)}
header.site .wrap{display:flex;align-items:center;gap:1.5rem;padding:1rem 1.25rem;flex-wrap:wrap}
.brand{font-weight:700;letter-spacing:.04em;color:#fff;text-decoration:none;font-size:1.1rem}
.brand span{color:var(--acc)}
nav.main{display:flex;gap:1.1rem;margin-left:auto}
nav.main a{color:var(--dim);text-decoration:none;font-size:.95rem}
nav.main a:hover,nav.main a.on{color:var(--acc)}
main .wrap{padding-top:2rem;padding-bottom:3rem}
h1,h2,h3{color:#fff;line-height:1.25}
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
.card h3 a{color:#fff;text-decoration:none}
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
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · WellKnownIndex</title>
<style>{css}</style>
</head>
<body>
<header class="site"><div class="wrap">
<a class="brand" href="{root}">WellKnown<span>Index</span></a>
<nav class="main">
<a href="{root}methods/" class="{m_on}">Methods</a>
<a href="{root}registry/" class="{r_on}">Registry</a>
<a href="{root}field-notes/" class="{f_on}">Field notes</a>
</nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer class="site"><div class="wrap">
<span>WellKnownIndex — a free public commons. No ads, no tracking.</span>
<a href="{root}contribute/">Contribute</a>
<a class="jsonlink" href="{json_url}">machine-readable JSON ↗</a>
</div></div></footer>
{extra_js}
</body>
</html>
"""


def page_html(title, body_html, section, root, json_url, extra_js=""):
    on = {s: ("on" if s == section else "") for s in ("methods", "registry", "field-notes")}
    return TEMPLATE.format(
        title=html.escape(title), css=CSS, body=body_html, root=root,
        json_url=json_url, extra_js=extra_js,
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
            facts = []
            for key in ("site_url", "cost", "verified"):
                if meta.get(key) is not None:
                    facts.append((key.replace("_", " ").title(), meta[key]))
            for key, label in (("protocols", "Protocols"), ("auth_schemes", "Auth"),
                               ("scopes", "Scopes"), ("methods_implemented", "Methods")):
                vals = meta.get(key) or []
                if vals:
                    if key == "protocols":
                        rendered = "<br>".join(
                            f"<code>{html.escape(p.get('type',''))}</code> "
                            f"<a href='{html.escape(p.get('url',''))}'>{html.escape(p.get('url',''))}</a>"
                            for p in vals
                        )
                    else:
                        rendered = ", ".join(f"<code>{html.escape(str(v))}</code>" for v in vals)
                    facts.append((label, rendered))
            if facts:
                rows = "".join(
                    f"<dt>{html.escape(k)}</dt><dd>{v if k in ('Protocols',) else html.escape(str(v)) if not str(v).startswith('<') else v}</dd>"
                    for k, v in facts
                )
                body_html += f"\n<h2>Machine-readable facts</h2>\n<dl class='kv'>{rows}</dl>"

        out_dir = DOCS if str(rel) == "index" else DOCS / rel
        out_dir.mkdir(parents=True, exist_ok=True)
        json_url = root + (str(rel) + ".json" if str(rel) != "index" else "home.json")
        html_page = page_html(title, body_html, section, root, json_url)
        (out_dir / "index.html").write_text(html_page, encoding="utf-8")

        # JSON twin
        twin = {
            "title": title, "section": section, "summary": summary,
            "url": (str(rel) + "/") if str(rel) != "index" else "./",
            "body_markdown": body,
        }
        for k, v in meta.items():
            if k not in twin:
                twin[k] = v
        twin_path = DOCS / (str(rel) + ".json" if str(rel) != "index" else "home.json")
        twin_path.write_text(jdumps(twin, indent=2), encoding="utf-8")

        pages.append({"slug": str(rel), "section": section, "title": title,
                      "summary": summary, "meta": meta})

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
            )
            extra_js = """<script>
const q=document.getElementById('q'),fm=document.getElementById('f_method'),
fp=document.getElementById('f_protocol'),fa=document.getElementById('f_auth');
function currentFilters(){return{q:q.value,method:fm.value,protocol:fp.value,auth:fa.value};}
function apply(){
  const f=currentFilters(),needle=f.q.toLowerCase();
  document.querySelectorAll('.card').forEach(c=>{
    const okT=!needle||c.dataset.search.includes(needle);
    const okM=!f.method||c.dataset.methods.split(' ').includes(f.method.toLowerCase());
    const okP=!f.protocol||c.dataset.protocols.split(' ').includes(f.protocol.toLowerCase());
    const okA=!f.auth||c.dataset.auth.split(' ').includes(f.auth.toLowerCase());
    c.style.display=(okT&&okM&&okP&&okA)?'':'none';
  });
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
                        "<a href='../contribute/'>Add it to the registry</a>.</p>\n")
        body_html = (f"<div class='stars'>✦ ✦ ✦</div>\n<h1>{sec_title}</h1>\n"
                     f"{add_line}{filter_box}\n" + "\n".join(cards))
        sec_dir = DOCS / sec
        sec_dir.mkdir(parents=True, exist_ok=True)
        (sec_dir / "index.html").write_text(
            page_html(sec_title, body_html, sec, "../", f"../{sec}.json", extra_js),
            encoding="utf-8",
        )
        # section JSON listing
        sec_json = [{"slug": p["slug"], "title": p["title"], "summary": p["summary"],
                     "url": f"./{p['slug'].split('/')[-1]}/",
                     "json_url": f"./{p['slug'].split('/')[-1]}.json"}
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
            "url": f"./registry/{slug}/", "json_url": f"./registry/{slug}.json",
        })
    (DOCS / "registry.json").write_text(jdumps(registry, indent=2), encoding="utf-8")

    # index.json — site map
    sitemap = {
        "site": SITE_TITLE, "tagline": SITE_TAGLINE,
        "generated": date.today().isoformat(),
        "sections": [{"slug": s, "title": t, "url": f"./{s}/", "json_url": f"./{s}.json"}
                     for s, t in SECTIONS.items()],
        "pages": [{"slug": p["slug"], "section": p["section"], "title": p["title"],
                   "summary": p["summary"],
                   "url": "./" if p["slug"] == "index" else f"./{p['slug']}/",
                   "json_url": "./home.json" if p["slug"] == "index" else f"./{p['slug']}.json"}
                  for p in sorted(pages, key=lambda x: x["slug"])],
        "registry": "./registry.json",
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
        },
        "registry_page_filters": {
            "q": "free-text search",
            "method": "implemented method slug, e.g. stage-and-approve",
            "protocol": "protocol type, e.g. ai-primer",
            "auth": "auth scheme identifier",
        },
        "contributing": "https://github.com/MASAGDT/wellknownindex/issues",
        "license_note": "Free public commons. No ads, no tracking.",
    }
    (wk_dir / "wellknownindex.json").write_text(jdumps(discovery, indent=2), encoding="utf-8")
    # disable Jekyll so dot-directories like .well-known are served verbatim
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    print(f"built {len(pages)} pages -> {DOCS}")


if __name__ == "__main__":
    main()
