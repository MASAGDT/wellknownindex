"""Human review CLI for the WellKnownIndex submission queue.

    python3 review.py list
    python3 review.py show <id>
    python3 review.py approve <id> [--out DIR]
    python3 review.py reject <id> [--reason TEXT]

Approval never pushes anywhere. It moves the submission to queue/approved/
and generates the registry markdown (frontmatter from the submission, stub
body for the human to flesh out). The human edits, commits, rebuilds, and
pushes — verification is not authorization, all the way down.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parent
PENDING = BASE / "queue" / "pending"
APPROVED = BASE / "queue" / "approved"
REJECTED = BASE / "queue" / "rejected"


def _load(qid: str):
    matches = list(PENDING.glob(f"{qid}*.json"))
    if not matches:
        raise SystemExit(f"no pending submission matching '{qid}'")
    if len(matches) > 1:
        raise SystemExit(f"ambiguous id '{qid}': {[m.stem for m in matches]}")
    return matches[0], json.loads(matches[0].read_text(encoding="utf-8"))


def _slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "entry"


def _markdown(record: dict) -> str:
    e = record["entry"]
    fm = {
        "title": e["title"],
        "section": "registry",
        "summary": e["summary"],
        "site_url": e.get("site_url"),
        "protocols": e.get("protocols", []),
        "auth_schemes": e.get("auth_schemes", []),
        "scopes": e.get("scopes", []),
        "methods_implemented": e.get("methods_implemented", []),
        "cost": e.get("cost"),
        "verified": e.get("verified"),
    }
    fm_text = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True)
    return (
        f"---\n{fm_text}---\n\n"
        f"# {e['title']}\n\n"
        f"<!-- Staged via the WellKnownIndex ceremony (queue id {record['id']}).\n"
        f"     Flesh out this stub before committing. -->\n\n"
        f"**{e.get('site_url') or ''}** — {e['summary']}\n"
    )


def cmd_list(_args):
    rows = []
    for p in sorted(PENDING.glob("*.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        e = rec.get("entry", {})
        rows.append((rec["id"], str(e.get("title", "?")),
                     str(e.get("site_url")), rec.get("received_at", "?")))
    if not rows:
        print("queue is empty")
        return
    for qid, title, url, ts in rows:
        print(f"{qid}  {ts}  {title}  <{url}>")


def cmd_show(args):
    _path, rec = _load(args.id)
    print(json.dumps(rec, indent=2))


def cmd_approve(args):
    APPROVED.mkdir(parents=True, exist_ok=True)
    path, rec = _load(args.id)
    slug = _slugify(str(rec["entry"].get("title", "entry")))
    md = _markdown(rec)
    path.rename(APPROVED / path.name)
    if args.out:
        outdir = Path(args.out)
        outdir.mkdir(parents=True, exist_ok=True)
        dest = outdir / f"{slug}.md"
        dest.write_text(md, encoding="utf-8")
        print(f"approved {rec['id']} -> {dest}", file=sys.stderr)
        print("edit the stub, then commit / rebuild / push yourself.", file=sys.stderr)
    else:
        print(f"# approved {rec['id']} -> suggested file: content/registry/{slug}.md",
              file=sys.stderr)
        print(md)


def cmd_reject(args):
    REJECTED.mkdir(parents=True, exist_ok=True)
    path, rec = _load(args.id)
    data = json.loads(path.read_text(encoding="utf-8"))
    if args.reason:
        data["reject_reason"] = args.reason
    (REJECTED / path.name).write_text(json.dumps(data, indent=2))
    path.unlink()
    print(f"rejected {rec['id']}" + (f": {args.reason}" if args.reason else ""))


def main():
    ap = argparse.ArgumentParser(description="Review the WellKnownIndex submission queue")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("show"); p.add_argument("id")
    p = sub.add_parser("approve"); p.add_argument("id"); p.add_argument("--out", default="")
    p = sub.add_parser("reject"); p.add_argument("id"); p.add_argument("--reason", default="")
    args = ap.parse_args()
    {"list": cmd_list, "show": cmd_show,
     "approve": cmd_approve, "reject": cmd_reject}[args.cmd](args)


if __name__ == "__main__":
    main()
