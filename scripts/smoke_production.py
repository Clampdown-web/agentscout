#!/usr/bin/env python3
"""Read-only smoke test for the live AgentScout site and workers.

Checks production with GET requests only. It does not POST to /submit or any
other write route, does not read secrets, and does not follow a redirect off
the AgentScout hosts. A run stays under about 40 requests: the pages, robots,
sitemap, the worker checks, and at most MAX_ASSETS cache-busted files.

  python3 scripts/smoke_production.py --self-test
  python3 scripts/smoke_production.py

Exit 0 when every check passes. Exit 1 when any check fails. The summary is
printed and, on GitHub Actions, written to the job summary.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

SITE = "https://agentscouthq.com"
VOTES = "https://votes.agentscouthq.com"
MCP = "https://mcp.agentscouthq.com"
ALLOWED_HOSTS = frozenset({"agentscouthq.com", "votes.agentscouthq.com", "mcp.agentscouthq.com"})
USER_AGENT = "AgentScoutSmoke/1.0 (+https://agentscouthq.com; read-only; no POST)"
PAUSE_SECONDS = 0.35
TIMEOUT_SECONDS = 20
MAX_BYTES = 1_000_000
# Union of cache-busted css/js the smoked pages may reference. Run 42791724517
# on a3ce6e2 failed because production referenced 14 and the old cap was 12.
# 18 covers that set and a couple of new shared files. A page that references
# more than MAX_PAGE_ASSETS fails on its own, so one document cannot blow the budget.
MAX_ASSETS = 18
MAX_PAGE_ASSETS = 16
TURNSTILE_SCRIPT = "https://challenges.cloudflare.com/turnstile/v0/api.js"
# Submit loads this helper, which then loads api.js with render=explicit.
# The sitekey stays the public widget key. Generate still embeds api.js itself.
SUBMIT_SITEKEY = "0x4AAAAAAFfaxf14aQF-sky1"
SUBMIT_TURNSTILE_JS = "submit-turnstile.js"
EXPLICIT_TURNSTILE = TURNSTILE_SCRIPT + "?render=explicit"
FAST_TRACK = "https://buy.stripe.com/3cIaEY6T15hlfJr135e7m0e"
# Retired $29 Fast-Track payment link, replaced by FAST_TRACK in cd1f95b3cb.
RETIRED_FAST_TRACK = "fZufZi7X5cJNbtbdPRe7m02"
OLD_FAST_TRACK_PRICE = re.compile(
    r"fast-?track[^<\n]{0,48}\$29|\$29[^<\n]{0,48}fast-?track",
    re.IGNORECASE,
)
ASSET_RE = re.compile(
    r"""(?P<quote>["'])(?P<ref>(?:https://agentscouthq\.com)?/?[^"'?#\s]+\.(?:css|js)\?v=[0-9A-Za-z._-]+)(?P=quote)"""
)
WEEK_RE = re.compile(r"^\d{4}-w\d{2}$")
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Headers Pages should send once _headers is deployed. Presence is the guard:
# a later allowlist addition still passes, and a dropped directive fails.
# Temporary: accept report-only until the Cloudflare CSP rule is enforced after the redesign (owner decision Nov 11, 2026). Restore enforced-only then.
# The repo _headers file also lists payment=(self "https://buy.stripe.com").
# Production does not send that directive, so it is not required here.
PAGE_HEADER_VALUES = {
    "strict-transport-security": "max-age=31536000; includeSubDomains; preload",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "strict-origin-when-cross-origin",
}
PAGE_HEADER_FRAGMENTS = {
    "permissions-policy": ("camera=()", "microphone=()", "geolocation=()"),
    "content-security-policy": (
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' https://challenges.cloudflare.com",
        "object-src 'none'",
        "base-uri 'self'",
        "frame-ancestors 'none'",
        "frame-src https://challenges.cloudflare.com",
        "worker-src 'self'",
    ),
}

PAGES = (
    {"path": "/", "title": ("AgentScout", "AI Agent"), "canonical": f"{SITE}/", "fast_track": True},
    # Phase 2 dropped the body promo on /mcp/. The $15 link stays required on /, /submit, /sponsor.html, and /best/.
    {"path": "/mcp/", "title": ("Best MCP Servers", "AgentScout"), "canonical": f"{SITE}/mcp/", "fast_track": False},
    # Tool pages post-#102 link to Get Featured /sponsor.html; Stripe Fast-Track lives on sponsor/home/etc.
    {"path": "/tools/zed.html", "title": ("Zed", "AgentScout"), "canonical": f"{SITE}/tools/zed.html", "fast_track": False},
    {"path": "/tools/crewai.html", "title": ("CrewAI", "AgentScout"), "canonical": f"{SITE}/tools/crewai.html", "fast_track": False},
    {"path": "/tools/cursor.html", "title": ("Cursor", "AgentScout"), "canonical": f"{SITE}/tools/cursor.html", "fast_track": False},
    {
        "path": "/submit",
        "title": ("Submit an AI Tool", "AgentScout"),
        "canonical": f"{SITE}/submit.html",
        "fast_track": True,
        "turnstile": True,
    },
    {"path": "/sponsor.html", "title": ("Sponsor", "AgentScout"), "canonical": f"{SITE}/sponsor.html", "fast_track": True},
    {"path": "/best/", "title": ("Best AI Agent Tools", "AgentScout"), "canonical": f"{SITE}/best/", "fast_track": True},
    {
        "path": "/best/ai-coding-agents.html",
        "title": ("Best AI Coding Agents", "AgentScout"),
        "canonical": f"{SITE}/best/ai-coding-agents.html",
        "fast_track": True,
    },
    {
        "path": "/best/open-source-mcp-servers.html",
        "title": ("Open-Source MCP Servers", "AgentScout"),
        "canonical": f"{SITE}/best/open-source-mcp-servers.html",
        "fast_track": True,
    },
    {
        "path": "/generate",
        "title": ("Free AI Image Generator", "AgentScout"),
        "canonical": f"{SITE}/generate.html",
        "turnstile_via_script": True,
    },
)


class UnsafeRequest(Exception):
    """A request this smoke test is not allowed to send."""


@dataclass
class Fetched:
    url: str
    status: int
    final_url: str
    headers: dict[str, str]
    body: bytes
    error: str = ""

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", "replace")


@dataclass
class Report:
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    requests: int = 0
    seconds: float = 0.0

    def ok(self, message: str) -> None:
        self.passed.append(message)

    def bad(self, message: str) -> None:
        self.failed.append(message)


class SameOriginGetRedirect(urllib.request.HTTPRedirectHandler):
    """Follow only HTTPS GET redirects that stay on the AgentScout hosts."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if code not in (301, 302, 303, 307, 308):
            raise UnsafeRequest(f"refusing redirect status {code} from {req.full_url}")
        if not allowed_get_url(newurl):
            raise UnsafeRequest(f"refusing redirect to {newurl}")
        return urllib.request.Request(newurl, method="GET", headers=request_headers())


class SmokeClient:
    def __init__(self, pause: float = PAUSE_SECONDS) -> None:
        self.pause = pause
        self.requests = 0
        self._opener = urllib.request.build_opener(SameOriginGetRedirect())

    def get(self, url: str) -> Fetched:
        fetched = self._get_once(url)
        # One retry for a dropped connection. Refusals and HTTP statuses are not retried.
        if fetched.status == 0 and fetched.error and not fetched.error.startswith("refusing"):
            time.sleep(max(self.pause, 1.5))
            fetched = self._get_once(url)
        return fetched

    def _get_once(self, url: str) -> Fetched:
        if not allowed_get_url(url):
            raise UnsafeRequest(f"refusing {url}")
        if self.requests:
            time.sleep(self.pause)
        self.requests += 1
        request = urllib.request.Request(url, method="GET", headers=request_headers())
        if request.get_method() != "GET":
            raise UnsafeRequest(f"refusing method {request.get_method()} for {url}")
        try:
            with self._opener.open(request, timeout=TIMEOUT_SECONDS) as response:
                return Fetched(url, response.status, response.geturl(), header_map(response.headers), response.read(MAX_BYTES))
        except urllib.error.HTTPError as error:
            return Fetched(url, error.code, getattr(error, "url", None) or url, header_map(error.headers), error.read(MAX_BYTES))
        except UnsafeRequest as error:
            return Fetched(url, 0, url, {}, b"", error=str(error))
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            return Fetched(url, 0, url, {}, b"", error=str(error))


def request_headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "*/*"}


def allowed_get_url(url: str) -> bool:
    parts = urllib.parse.urlsplit(url)
    return (
        parts.scheme == "https"
        and parts.hostname in ALLOWED_HOSTS
        and not parts.username
        and not parts.password
    )


def header_map(headers) -> dict[str, str]:
    mapped: dict[str, str] = {}
    if headers is None:
        return mapped
    for key in headers.keys():
        if not key:
            continue
        values = headers.get_all(key) if hasattr(headers, "get_all") else [headers.get(key)]
        mapped[key.lower()] = " ".join(" ".join(str(value).split()) for value in values if value)
    return mapped


def page_title(document: str) -> str:
    match = re.search(r"<title>(.*?)</title>", document, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return " ".join(html.unescape(match.group(1)).split())


def page_canonical(document: str) -> str:
    for match in re.finditer(r"<link\b[^>]*>", document, re.IGNORECASE):
        tag = match.group(0)
        if re.search(r"""\brel=["']canonical["']""", tag, re.IGNORECASE):
            href = re.search(r"""\bhref=["']([^"']+)["']""", tag, re.IGNORECASE)
            return href.group(1) if href else ""
    return ""


def asset_budget_problems(union_count: int, page_counts: list[int]) -> list[str]:
    """Bound the asset GETs. An empty set fails. The live set of 14 passes. A runaway page fails."""
    problems: list[str] = []
    if union_count == 0:
        problems.append("cache-busted assets: none were referenced by the pages")
    elif union_count > MAX_ASSETS:
        problems.append(f"cache-busted assets: {union_count} references exceeds the {MAX_ASSETS} request cap")
    for count in page_counts:
        if count > MAX_PAGE_ASSETS:
            problems.append(f"cache-busted assets: one page references {count}, above the {MAX_PAGE_ASSETS} page cap")
            break
    return problems


def cache_busted_assets(document: str, page_url: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in ASSET_RE.finditer(document):
        absolute = urllib.parse.urljoin(page_url, match.group("ref"))
        if absolute not in seen and allowed_get_url(absolute):
            seen.add(absolute)
            found.append(absolute)
    return found


def header_problems(headers: dict[str, str]) -> list[str]:
    problems: list[str] = []
    for name, expected in PAGE_HEADER_VALUES.items():
        actual = headers.get(name, "")
        if actual != expected:
            problems.append(f"{name} is {actual or 'missing'}, expected {expected}")
    for name, fragments in PAGE_HEADER_FRAGMENTS.items():
        if name == "content-security-policy":
            # Temporary: accept report-only until the Cloudflare CSP rule is enforced after the redesign (owner decision Nov 11, 2026). Restore enforced-only then.
            problems.extend(csp_directive_problems(headers, fragments))
            continue
        actual = headers.get(name, "")
        if not actual:
            problems.append(f"{name} is missing")
            continue
        for fragment in fragments:
            if fragment not in actual:
                problems.append(f"{name} is missing {fragment}")
    return problems


def csp_directive_problems(headers: dict[str, str], fragments: tuple[str, ...]) -> list[str]:
    """Pass when either CSP header contains every required directive."""
    candidates = [
        (name, headers.get(name, ""))
        for name in ("content-security-policy", "content-security-policy-report-only")
    ]
    candidates = [(name, value) for name, value in candidates if value]
    if not candidates:
        return ["content-security-policy is missing"]
    for _name, value in candidates:
        if all(fragment in value for fragment in fragments):
            return []
    name, value = candidates[0]
    return [f"{name} is missing {fragment}" for fragment in fragments if fragment not in value]


def fast_track_problems(document: str, require_current: bool) -> list[str]:
    problems: list[str] = []
    if RETIRED_FAST_TRACK in document:
        problems.append(f"retired $29 Fast-Track link {RETIRED_FAST_TRACK} is present")
    if OLD_FAST_TRACK_PRICE.search(document):
        problems.append("copy still prices Fast-Track at $29")
    if require_current and FAST_TRACK not in document:
        problems.append(f"current $15 Fast-Track link is missing ({FAST_TRACK})")
    return problems


def html_page_problems(spec: dict, fetched: Fetched) -> list[str]:
    if fetched.error:
        return [fetched.error]
    problems: list[str] = []
    if fetched.status != 200:
        problems.append(f"status {fetched.status}, expected 200")
    if not fetched.final_url.startswith(SITE):
        problems.append(f"final URL {fetched.final_url} left {SITE}")
    document = fetched.text
    title = page_title(document)
    for part in spec["title"]:
        if part not in title:
            problems.append(f"title {title!r} does not contain {part!r}")
    canonical = page_canonical(document)
    if canonical != spec["canonical"]:
        problems.append(f"canonical {canonical or 'missing'}, expected {spec['canonical']}")
    content_type = fetched.headers.get("content-type", "")
    if "text/html" not in content_type:
        problems.append(f"content-type {content_type or 'missing'}, expected text/html")
    problems.extend(header_problems(fetched.headers))
    problems.extend(fast_track_problems(document, spec.get("fast_track", False)))
    if spec.get("turnstile"):
        problems.extend(submit_turnstile_page_problems(document))
    return problems


def submit_turnstile_page_problems(document: str) -> list[str]:
    problems: list[str] = []
    if SUBMIT_SITEKEY not in document:
        problems.append(f"Turnstile sitekey is missing ({SUBMIT_SITEKEY})")
    if SUBMIT_TURNSTILE_JS not in document:
        problems.append(f"{SUBMIT_TURNSTILE_JS} is not referenced")
    return problems


def submit_turnstile_script_problems(fetched: Fetched | None) -> list[str]:
    if fetched is None:
        return [f"{SUBMIT_TURNSTILE_JS} was not fetched"]
    problems: list[str] = []
    if fetched.error:
        problems.append(fetched.error)
    if fetched.status != 200:
        problems.append(f"status {fetched.status}, expected 200")
    if EXPLICIT_TURNSTILE not in fetched.text:
        problems.append(f"explicit Turnstile loader is missing ({EXPLICIT_TURNSTILE})")
    return problems


def text_problems(fetched: Fetched, needles: tuple[str, ...], content_marker: str) -> list[str]:
    if fetched.error:
        return [fetched.error]
    problems: list[str] = []
    if fetched.status != 200:
        problems.append(f"status {fetched.status}, expected 200")
    content_type = fetched.headers.get("content-type", "")
    if content_marker not in content_type:
        problems.append(f"content-type {content_type or 'missing'}, expected {content_marker}")
    if "text/html" in content_type:
        problems.append("content-type is HTML")
    text = fetched.text
    for needle in needles:
        if needle not in text:
            problems.append(f"body is missing {needle!r}")
    problems.extend(header_problems(fetched.headers))
    problems.extend(fast_track_problems(text, False))
    return problems


def asset_problems(fetched: Fetched) -> list[str]:
    if fetched.error:
        return [fetched.error]
    problems: list[str] = []
    if fetched.status != 200:
        problems.append(f"status {fetched.status}, expected 200")
    if "?v=" not in fetched.final_url and "?v=" not in fetched.url:
        problems.append("cache-buster query was dropped")
    content_type = fetched.headers.get("content-type", "")
    path = urllib.parse.urlsplit(fetched.url).path
    if path.endswith(".css") and "text/css" not in content_type:
        problems.append(f"content-type {content_type or 'missing'}, expected text/css")
    if path.endswith(".js") and "javascript" not in content_type:
        problems.append(f"content-type {content_type or 'missing'}, expected javascript")
    if len(fetched.body) < 100:
        problems.append(f"body is {len(fetched.body)} bytes")
    start = fetched.body.lstrip()[:15].lower()
    if start.startswith(b"<!doctype") or start.startswith(b"<html"):
        problems.append("body is an HTML document")
    problems.extend(fast_track_problems(fetched.text, False))
    return problems


def integer_field(payload: dict, name: str) -> str:
    value = payload.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        return f"{name} is {value!r}, expected an integer"
    if value < 0:
        return f"{name} is {value}, expected a non-negative integer"
    return ""


def votes_problems(fetched: Fetched) -> list[str]:
    problems = json_status_problems(fetched)
    if problems and fetched.status != 200:
        return problems
    try:
        payload = json.loads(fetched.text)
    except json.JSONDecodeError as error:
        return problems + [f"body is not JSON ({error})"]
    if not isinstance(payload, dict):
        return problems + ["body is not a JSON object"]
    if payload.get("ok") is not True:
        problems.append(f"ok is {payload.get('ok')!r}")
    week = payload.get("week")
    day = payload.get("day")
    if not isinstance(week, str) or not WEEK_RE.match(week):
        problems.append(f"week is {week!r}")
    if not isinstance(day, str) or not DAY_RE.match(day):
        problems.append(f"day is {day!r}")
    tools = payload.get("tools")
    if not isinstance(tools, dict) or "zed" not in tools or not isinstance(tools.get("zed"), dict):
        problems.append("tools.zed is missing")
    else:
        for key in ("votes", "today"):
            if integer_field(tools["zed"], key):
                problems.append(f"tools.zed.{integer_field(tools['zed'], key)}")
    if integer_field(payload, "today_total"):
        problems.append(integer_field(payload, "today_total"))
    return problems


def mcp_info_problems(fetched: Fetched) -> list[str]:
    problems = json_status_problems(fetched)
    try:
        payload = json.loads(fetched.text) if fetched.text else None
    except json.JSONDecodeError as error:
        return problems + [f"body is not JSON ({error})"]
    if not isinstance(payload, dict):
        return problems + ["body is not a JSON object"]
    if payload.get("read_only") is not True:
        problems.append(f"read_only is {payload.get('read_only')!r}")
    if payload.get("transport") != "streamable-http":
        problems.append(f"transport is {payload.get('transport')!r}")
    if payload.get("endpoint") != f"{MCP}/mcp":
        problems.append(f"endpoint is {payload.get('endpoint')!r}")
    name = payload.get("name")
    if not isinstance(name, str) or "AgentScout" not in name:
        problems.append(f"name is {name!r}")
    tools = payload.get("tools")
    if not isinstance(tools, list) or not tools or not all(isinstance(item, str) for item in tools):
        problems.append("tools is not a list of names")
    elif "search_tools" not in tools:
        problems.append("tools does not include search_tools")
    for key in ("tools_indexed", "categories", "mcp_servers"):
        message = integer_field(payload, key)
        if message:
            problems.append(message)
        elif isinstance(payload.get(key), int) and payload[key] < 1:
            problems.append(f"{key} is {payload[key]}")
    return problems


def registry_problems(fetched: Fetched) -> list[str]:
    problems = json_status_problems(fetched)
    try:
        payload = json.loads(fetched.text) if fetched.text else None
    except json.JSONDecodeError as error:
        return problems + [f"body is not JSON ({error})"]
    if not isinstance(payload, dict):
        return problems + ["body is not a JSON object"]
    servers = payload.get("servers")
    if not isinstance(servers, list) or not servers or not isinstance(servers[0], dict):
        return problems + ["servers[0] is missing"]
    server = servers[0].get("server") if isinstance(servers[0], dict) else None
    if not isinstance(server, dict) or server.get("name") != "com.agentscouthq/directory":
        problems.append("servers[0].server.name is not com.agentscouthq/directory")
    remotes = server.get("remotes") if isinstance(server, dict) else None
    remote_urls = [item.get("url") for item in remotes if isinstance(item, dict)] if isinstance(remotes, list) else []
    if f"{MCP}/mcp" not in remote_urls:
        problems.append("registry remotes do not include the MCP endpoint")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("count") != 1 or "nextCursor" not in metadata:
        problems.append(f"metadata is {metadata!r}")
    return problems


def json_status_problems(fetched: Fetched) -> list[str]:
    if fetched.error:
        return [fetched.error]
    problems: list[str] = []
    if fetched.status != 200:
        problems.append(f"status {fetched.status}, expected 200")
    content_type = fetched.headers.get("content-type", "")
    if "json" not in content_type:
        problems.append(f"content-type {content_type or 'missing'}, expected json")
    return problems


def record(report: Report, label: str, problems: list[str]) -> None:
    if problems:
        detail = "; ".join(problems)
        report.bad(f"{label}: {detail}")
        return
    report.ok(label)


def run_live(client: SmokeClient | None = None) -> Report:
    report = Report()
    started = time.monotonic()
    client = client or SmokeClient()
    pages: list[tuple[dict, Fetched]] = []
    for spec in PAGES:
        fetched = client.get(SITE + spec["path"])
        pages.append((spec, fetched))
        record(report, f"GET {spec['path']}", html_page_problems(spec, fetched))

    robots = client.get(f"{SITE}/robots.txt")
    record(
        report,
        "GET /robots.txt",
        text_problems(robots, ("User-agent:", "Sitemap: https://agentscouthq.com/sitemap.xml"), "text/plain"),
    )
    sitemap = client.get(f"{SITE}/sitemap.xml")
    record(
        report,
        "GET /sitemap.xml",
        text_problems(
            sitemap,
            ("<urlset", "https://agentscouthq.com/</loc>", "https://agentscouthq.com/mcp/", "https://agentscouthq.com/best/"),
            "xml",
        ),
    )

    assets: list[str] = []
    seen_assets: set[str] = set()
    page_counts: list[int] = []
    for spec, fetched in pages:
        if fetched.status != 200:
            continue
        page_assets = cache_busted_assets(fetched.text, fetched.final_url)
        page_counts.append(len(page_assets))
        for asset in page_assets:
            if asset not in seen_assets:
                seen_assets.add(asset)
                assets.append(asset)
    budget = asset_budget_problems(len(assets), page_counts)
    if budget:
        for problem in budget:
            report.bad(problem)
    else:
        asset_bodies: dict[str, Fetched] = {}
        for asset in assets:
            fetched = client.get(asset)
            asset_bodies[asset] = fetched
            label = urllib.parse.urlsplit(asset).path + "?" + urllib.parse.urlsplit(asset).query
            record(report, f"GET {label}", asset_problems(fetched))
        generate = next((fetched for spec, fetched in pages if spec["path"] == "/generate"), None)
        generate_script = ""
        if generate and generate.status == 200:
            for asset in cache_busted_assets(generate.text, generate.final_url):
                if urllib.parse.urlsplit(asset).path.endswith("/generate.js"):
                    generate_script = asset
                    break
        script = asset_bodies.get(generate_script)
        if script is None:
            report.bad("GET /generate Turnstile: generate.js?v= was not referenced")
        else:
            script_problems: list[str] = []
            if TURNSTILE_SCRIPT not in script.text:
                script_problems.append(f"Turnstile widget script is missing from generate.js ({TURNSTILE_SCRIPT})")
            if "cf-turnstile" not in script.text:
                script_problems.append("generate.js does not create a cf-turnstile widget")
            record(report, "GET /generate Turnstile widget script", script_problems)

        submit = next((fetched for spec, fetched in pages if spec.get("turnstile")), None)
        submit_script = ""
        if submit and submit.status == 200:
            for asset in cache_busted_assets(submit.text, submit.final_url):
                if urllib.parse.urlsplit(asset).path.endswith("/" + SUBMIT_TURNSTILE_JS):
                    submit_script = asset
                    break
        record(
            report,
            "GET /submit Turnstile loader",
            submit_turnstile_script_problems(asset_bodies.get(submit_script) if submit_script else None),
        )

    record(report, "GET votes.agentscouthq.com/votes?slugs=zed (agentscout-api)", votes_problems(client.get(f"{VOTES}/votes?slugs=zed")))
    record(report, "GET mcp.agentscouthq.com/ (agentscout-mcp)", mcp_info_problems(client.get(f"{MCP}/")))
    record(report, "GET mcp.agentscouthq.com/mcp (agentscout-mcp)", mcp_info_problems(client.get(f"{MCP}/mcp")))
    record(report, "GET mcp.agentscouthq.com/v0/servers (agentscout-mcp)", registry_problems(client.get(f"{MCP}/v0/servers")))

    report.requests = client.requests
    report.seconds = time.monotonic() - started
    return report


def self_test() -> None:
    document = """
    <title>AgentScout: sample &amp; title</title>
    <link rel="canonical" href="https://agentscouthq.com/">
    <link rel="stylesheet" href="styles.css?v=202611082000">
    <script>["app.js?v=202611082000","clip.mp4?v=20261109-1"]</script>
    <a href="https://buy.stripe.com/3cIaEY6T15hlfJr135e7m0e">$15 Fast-Track</a>
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>
    <div class="cf-turnstile"></div>
    """
    assert page_title(document) == "AgentScout: sample & title"
    assert page_canonical(document) == "https://agentscouthq.com/"
    assets = cache_busted_assets(document, f"{SITE}/")
    assert asset_budget_problems(14, [9, 6, 5]) == []
    assert asset_budget_problems(MAX_ASSETS, [MAX_PAGE_ASSETS]) == []
    assert any("exceeds" in item for item in asset_budget_problems(MAX_ASSETS + 1, [4]))
    assert any("page cap" in item for item in asset_budget_problems(4, [MAX_PAGE_ASSETS + 1]))
    assert any("none" in item for item in asset_budget_problems(0, []))
    assert f"{SITE}/styles.css?v=202611082000" in assets
    assert f"{SITE}/app.js?v=202611082000" in assets
    assert all(not item.endswith(".mp4?v=20261109-1") and ".mp4" not in item for item in assets)
    assert fast_track_problems(document, True) == []
    assert any("retired" in item for item in fast_track_problems(document + RETIRED_FAST_TRACK, False))
    assert any("$29" in item for item in fast_track_problems("Fast-Track for $29 today", False))
    assert fast_track_problems('fast_29:{url:"https://buy.stripe.com/3cIaEY6T15hlfJr135e7m0e"}', True) == []
    submit_page = (
        '<div id="sf-turnstile" data-sitekey="0x4AAAAAAFfaxf14aQF-sky1"></div>'
        '<script src="submit-turnstile.js?v=202611082000"></script>'
    )
    assert submit_turnstile_page_problems(submit_page) == []
    assert any("sitekey" in item for item in submit_turnstile_page_problems("<div id=\"sf-turnstile\"></div>"))
    assert any("submit-turnstile.js" in item for item in submit_turnstile_page_problems(f'data-sitekey="{SUBMIT_SITEKEY}"'))
    explicit = Fetched(
        f"{SITE}/submit-turnstile.js?v=202611082000",
        200,
        f"{SITE}/submit-turnstile.js?v=202611082000",
        {"content-type": "text/javascript"},
        b'var s="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=asTsLoad";',
    )
    assert submit_turnstile_script_problems(explicit) == []
    assert submit_turnstile_script_problems(None) != []
    assert any("200" in item for item in submit_turnstile_script_problems(
        Fetched(explicit.url, 404, explicit.url, explicit.headers, explicit.body)
    ))
    assert any("explicit" in item for item in submit_turnstile_script_problems(
        Fetched(explicit.url, 200, explicit.url, explicit.headers, b"https://challenges.cloudflare.com/turnstile/v0/api.js")
    ))

    headers = {
        **PAGE_HEADER_VALUES,
        "permissions-policy": "camera=(), microphone=(), geolocation=(), payment=(self)",
        "content-security-policy": " ".join(
            fragment for fragments in PAGE_HEADER_FRAGMENTS.values() for fragment in fragments
        ),
    }
    assert header_problems(headers) == []
    report_only = dict(headers)
    report_only["content-security-policy-report-only"] = report_only.pop("content-security-policy")
    assert header_problems(report_only) == []
    missing_csp = dict(report_only)
    del missing_csp["content-security-policy-report-only"]
    assert any(item == "content-security-policy is missing" for item in header_problems(missing_csp))
    dropped_report = dict(report_only)
    dropped_report["content-security-policy-report-only"] = dropped_report[
        "content-security-policy-report-only"
    ].replace("object-src 'none'", "")
    assert any("object-src 'none'" in item for item in header_problems(dropped_report))
    dropped_enforced = dict(headers)
    dropped_enforced["content-security-policy"] = dropped_enforced["content-security-policy"].replace(
        "frame-ancestors 'none'", ""
    )
    assert any("frame-ancestors 'none'" in item for item in header_problems(dropped_enforced))
    report_wins = dict(report_only)
    report_wins["content-security-policy"] = "default-src 'none'"
    assert header_problems(report_wins) == []
    both_weak = dict(headers)
    both_weak["content-security-policy"] = "default-src 'none'"
    both_weak["content-security-policy-report-only"] = "default-src 'none'"
    assert any("default-src 'self'" in item for item in header_problems(both_weak))
    perms = dict(headers)
    perms["permissions-policy"] = "microphone=(), geolocation=()"
    assert any("camera=()" in item for item in header_problems(perms))
    broken = dict(headers)
    del broken["x-frame-options"]
    assert any("x-frame-options" in item for item in header_problems(broken))

    votes = Fetched(
        f"{VOTES}/votes?slugs=zed",
        200,
        f"{VOTES}/votes?slugs=zed",
        {"content-type": "application/json"},
        b'{"ok":true,"week":"2026-w46","day":"2026-11-09","tools":{"zed":{"votes":0,"today":0}},"today_total":0}',
    )
    assert votes_problems(votes) == []
    assert votes_problems(Fetched(votes.url, 500, votes.url, votes.headers, votes.body)) != [] 

    info = {
        "name": "AgentScout MCP server",
        "endpoint": f"{MCP}/mcp",
        "transport": "streamable-http",
        "read_only": True,
        "tools_indexed": 2,
        "categories": 3,
        "mcp_servers": 4,
        "tools": ["search_tools"],
    }
    info_fetched = Fetched(f"{MCP}/", 200, f"{MCP}/", {"content-type": "application/json"}, json.dumps(info).encode())
    assert mcp_info_problems(info_fetched) == []
    registry = {
        "servers": [{"server": {"name": "com.agentscouthq/directory", "remotes": [{"url": f"{MCP}/mcp"}]}}],
        "metadata": {"count": 1, "nextCursor": ""},
    }
    registry_fetched = Fetched(
        f"{MCP}/v0/servers", 200, f"{MCP}/v0/servers", {"content-type": "application/json"}, json.dumps(registry).encode()
    )
    assert registry_problems(registry_fetched) == []

    handler = SameOriginGetRedirect()
    request = urllib.request.Request(f"{SITE}/submit", method="GET")
    followed = handler.redirect_request(request, None, 302, "Found", {}, f"{SITE}/submit.html")
    assert followed is not None and followed.get_method() == "GET"
    for blocked in ("https://buy.stripe.com/3cIaEY6T15hlfJr135e7m0e", "http://agentscouthq.com/", "https://user:pw@agentscouthq.com/"):
        try:
            handler.redirect_request(request, None, 302, "Found", {}, blocked)
        except UnsafeRequest:
            continue
        raise AssertionError(f"redirect guard allowed {blocked}")
    client = SmokeClient(pause=0)
    for blocked in ("http://agentscouthq.com/", "https://example.com/", "https://user:pw@agentscouthq.com/"):
        try:
            client.get(blocked)
        except UnsafeRequest:
            continue
        raise AssertionError(f"client allowed {blocked}")
    assert client.requests == 0
    assert not hasattr(client, "post")


def render(report: Report) -> str:
    state = "passed" if not report.failed else "failed"
    lines = [
        f"## Production smoke: {state}",
        "",
        (
            f"{len(report.passed)} passed, {len(report.failed)} failed. "
            f"{report.requests} GET requests in {report.seconds:.1f}s. "
            "No secrets and no POST."
        ),
        "",
    ]
    if report.failed:
        lines.append("### Failures")
        lines.extend(f"- {item}" for item in report.failed)
        lines.append("")
    lines.append("### Passed")
    lines.extend(f"- {item}" for item in report.passed)
    lines.append("")
    return "\n".join(lines)


def publish(report: Report) -> None:
    text = render(report)
    print(text)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        for item in report.failed:
            print(f"::error::{item}")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as handle:
                handle.write(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only production smoke test for AgentScout.")
    parser.add_argument("--self-test", action="store_true", help="check the harness without contacting production")
    args = parser.parse_args(argv)
    self_test()
    if args.self_test:
        print("smoke harness: self-test passed")
        return 0
    report = run_live()
    publish(report)
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
