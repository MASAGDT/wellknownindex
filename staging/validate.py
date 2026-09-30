"""Validation rules for WellKnownIndex staged registry submissions.

Rulebook for the ceremony: an agent POSTs a JSON registry entry, this module
decides whether it may wait in the queue for human review.

The JSON Schema check loads the *published* schema file
(../static/schema/registry-entry.json), so the code and the schema cannot
drift apart. The extra rules (method vocabulary, duplicates, abuse controls)
live here in code, and are documented on the Ceremony Blueprint page.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

BASE = Path(__file__).resolve().parent
SCHEMA_PATH = BASE.parent / "static" / "schema" / "registry-entry.json"
REGISTRY_DIR = BASE.parent / "content" / "registry"
PENDING_DIR = BASE / "queue" / "pending"

SCHEMA = json.loads(SCHEMA_PATH.read_text())

# The wiki's method vocabulary. Update when a method page ships.
KNOWN_METHODS = [
    "machine-readable-primer",
    "scoped-ai-grants",
    "stage-and-approve",
    "well-known-discovery",
    "agent-credentials",
    "no-simulated-execution",
    "mcp-bridge",
    "querying-the-registry",
    "retrofit-ladder",
    "primer-file-format",
    "oauth-scoped-grants",
    "flask-stage-and-approve",
    "ceremony-blueprint",
    "matrix",
]

# Auth schemes seen in the wild. Unknown ones warn; they don't fail —
# the registry is supposed to learn new schemes.
KNOWN_AUTH_SCHEMES = [
    "ai-access-grant",
    "bearer-session",
    "owner-pairing",
    "invitation-link",
    "agent-credential",
    "agent-api-credential",
]

MAX_BODY_BYTES = 32 * 1024
SCRIPT_RE = re.compile(r"<\s*script", re.IGNORECASE)


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def _existing_entries():
    """Yield (title, site_url) for live registry entries and queued submissions."""
    seen = []
    if REGISTRY_DIR.is_dir():
        for md in sorted(REGISTRY_DIR.glob("*.md")):
            fm = _frontmatter(md)
            seen.append((str(fm.get("title", "")), fm.get("site_url")))
    if PENDING_DIR.is_dir():
        for q in sorted(PENDING_DIR.glob("*.json")):
            try:
                entry = json.loads(q.read_text(encoding="utf-8")).get("entry", {})
                seen.append((str(entry.get("title", "")), entry.get("site_url")))
            except (json.JSONDecodeError, OSError):
                continue
    return seen


def _norm_url(u) -> str:
    return (u or "").strip().rstrip("/").lower()


def validate_entry(entry, raw_body=None) -> dict:
    """Validate a submitted registry entry.

    Returns {"ok": bool, "errors": [...], "warnings": [...]}.
    `entry` must be a dict; `raw_body` (bytes) enables the abuse checks.
    """
    errors, warnings = [], []

    # Rule 6 (abuse): oversized bodies never get far.
    if raw_body is not None and len(raw_body) > MAX_BODY_BYTES:
        errors.append(f"body exceeds {MAX_BODY_BYTES // 1024}KB limit")
    if not isinstance(entry, dict):
        return {"ok": False,
                "errors": errors + ["submission must be a JSON object"],
                "warnings": warnings}

    # Rule 1: shape — the published JSON Schema is the authority.
    validator = Draft202012Validator(SCHEMA)
    for err in sorted(validator.iter_errors(entry), key=lambda e: list(e.path)):
        where = ".".join(str(p) for p in err.path) or "entry"
        errors.append(f"schema: {where}: {err.message}")

    # Rule 6 (abuse): no markup in text fields.
    for field in ("title", "summary", "cost"):
        val = entry.get(field)
        if isinstance(val, str) and SCRIPT_RE.search(val):
            errors.append(f"abuse: {field} contains markup")

    # Rule 2: URLs.
    site_url = entry.get("site_url")
    if site_url is not None:
        if not isinstance(site_url, str) or not site_url.startswith("https://"):
            errors.append("urls: site_url must be an https:// URL or null")
    for i, proto in enumerate(entry.get("protocols") or []):
        if not isinstance(proto, dict):
            continue
        url = proto.get("url", "")
        if not (isinstance(url, str)
                and (url.startswith("https://") or url.startswith("/"))):
            errors.append(
                f"urls: protocols[{i}].url must be absolute https:// or site-relative /...")

    # Rule 3: methods must exist in the wiki's vocabulary.
    for slug in entry.get("methods_implemented") or []:
        if slug not in KNOWN_METHODS:
            close = [m for m in KNOWN_METHODS if slug in m or m in slug]
            hint = f" (did you mean: {', '.join(close)})" if close else ""
            errors.append(f"methods: unknown method slug '{slug}'{hint}")

    # Rule 4: auth schemes may be new — warn, don't fail.
    for scheme in entry.get("auth_schemes") or []:
        if scheme not in KNOWN_AUTH_SCHEMES:
            warnings.append(
                f"auth: new scheme '{scheme}' — a human should confirm it")

    # Rule 5: no duplicates, against the live registry and the queue.
    title = str(entry.get("title", "")).strip().lower()
    surl = _norm_url(site_url) if isinstance(site_url, str) else ""
    for etitle, esurl in _existing_entries():
        if title and title == str(etitle).strip().lower():
            errors.append(
                f"duplicate: title '{entry.get('title')}' is already registered")
            break
        if surl and surl == _norm_url(esurl):
            errors.append(
                f"duplicate: site_url '{site_url}' is already registered")
            break

    return {"ok": not errors, "errors": errors, "warnings": warnings}
