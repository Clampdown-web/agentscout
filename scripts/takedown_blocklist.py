"""Drop trademark-takedown listings during discovery and site builds.

Blocked slugs, names, domains, and GitHub repos live in data/takedown_blocklist.json.
Matching is exact (case-insensitive) on the slug and name, and on the
registrable host of a URL, so nearby names are left alone. A repo matches
owner/name from a full_name or a github.com URL.
"""
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "takedown_blocklist.json"


def _repo_key(value):
    """owner/repo from a GitHub URL or a full_name. Empty when it is not a repo."""
    raw = str(value or "").strip().lower()
    raw = raw.replace("https://github.com/", "").replace("http://github.com/", "")
    raw = raw.strip("/")
    parts = [p for p in raw.split("/") if p]
    if len(parts) >= 2 and "." not in parts[0]:
        return parts[0] + "/" + parts[1].removesuffix(".git")
    return ""


def _load():
    data = json.loads(PATH.read_text(encoding="utf-8"))
    slugs = {s.strip().lower() for s in data.get("slugs", []) if str(s).strip()}
    names = {s.strip().lower() for s in data.get("names", []) if str(s).strip()}
    repos = {(_repo_key(s) or str(s).strip().lower()) for s in data.get("repos", []) if str(s).strip()}
    domains = set()
    for raw in data.get("domains", []):
        host = _host(str(raw))
        if host:
            domains.add(host)
    return slugs, names, domains, repos


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
    slugs, names, domains, repos = _load()
    if slug and str(slug).strip().lower() in slugs:
        return True
    if name and str(name).strip().lower() in names:
        return True
    keys = set()
    if repo:
        keys.add(_repo_key(repo) or str(repo).strip().lower())
    for candidate in (url, website, repo):
        host = _host(candidate)
        if host and (host in domains or any(host.endswith("." + domain) for domain in domains)):
            return True
        if "github.com" in str(candidate or "").lower():
            key = _repo_key(candidate)
            if key:
                keys.add(key)
    if any(k in repos for k in keys if k):
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
        repo=tool.get("repo") or tool.get("github") or "",
    )
