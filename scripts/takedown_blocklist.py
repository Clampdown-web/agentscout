"""Drop trademark-takedown listings during discovery and site builds.

Blocked slugs, names, and domains live in data/takedown_blocklist.json.
Matching is exact (case-insensitive) on the slug and name, and on the
registrable host of a URL, so nearby names are left alone.
"""
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "takedown_blocklist.json"


def _load():
    data = json.loads(PATH.read_text(encoding="utf-8"))
    slugs = {s.strip().lower() for s in data.get("slugs", []) if str(s).strip()}
    names = {s.strip().lower() for s in data.get("names", []) if str(s).strip()}
    domains = set()
    for raw in data.get("domains", []):
        host = _host(str(raw))
        if host:
            domains.add(host)
    return slugs, names, domains


def _host(url):
    if not url:
        return ""
    raw = str(url).strip()
    if "://" not in raw:
        raw = "https://" + raw
    host = (urlparse(raw).hostname or "").lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host


def blocked(name="", url="", website="", slug="", repo=""):
    """True when a candidate matches the takedown blocklist."""
    slugs, names, domains = _load()
    if slug and str(slug).strip().lower() in slugs:
        return True
    if name and str(name).strip().lower() in names:
        return True
    for candidate in (url, website, repo):
        host = _host(candidate)
        if not host:
            continue
        if host in domains or any(host.endswith("." + domain) for domain in domains):
            return True
    return False


def blocked_tool(tool):
    if not isinstance(tool, dict):
        return False
    return blocked(
        name=tool.get("name", ""),
        url=tool.get("url", ""),
        website=tool.get("website", ""),
        slug=tool.get("slug", ""),
        repo=tool.get("repo", ""),
    )
