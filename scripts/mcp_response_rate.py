#!/usr/bin/env python3
"""Probe listed MCP servers with initialize and tools/list. Never calls a tool.

History is append-only JSONL under data/mcp-health/. The summary is derived.
See docs/mcp-response-rate.md.

  python3 scripts/mcp_response_rate.py --limit 20 --dry-run
  python3 scripts/mcp_response_rate.py --limit 200
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

USER_AGENT = "AgentScoutBot/1.0 (+https://agentscouthq.com)"
PROTOCOL = "2025-06-18"
FALLBACK_PROTOCOL = "2024-11-05"
ALLOWED_METHODS = frozenset({"initialize", "notifications/initialized", "tools/list"})
REGISTRY = "https://registry.modelcontextprotocol.io/v0.1/servers"
MIN_PROBES = 3
MAX_BODY = 2_000_000
DEFAULT_LIMIT = 200
DEFAULT_PER_HOST = 8
DEFAULT_RPS = 5.0
DEFAULT_TIMEOUT = 10.0
DEFAULT_REGISTRY_PAGES = 1200
RISKY_QUERY = re.compile(r"(?i)(?:^|&)(?:api[_-]?key|access[_-]?token|token|secret|password|sig)=")
AUTH_ERROR = re.compile(
    r"unauthori[sz]ed|forbidden|auth(?:entication|orization)?\s+required|"
    r"invalid[_ ]token|no api key|not authenticated|login required",
    re.I,
)
RECORD_KEYS = (
    "endpoint",
    "http_status",
    "latency_ms",
    "outcome",
    "protocol_version",
    "reason",
    "slug",
    "tool_count",
    "transport",
    "ts",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(value: str) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_json(path: Path, default):
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def load_tools(path: Path) -> list:
    data = load_json(path, [])
    if isinstance(data, dict):
        data = data.get("tools") or []
    return data if isinstance(data, list) else []


def github_key(value: str | None) -> str | None:
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if text.lower().startswith(("http://", "https://", "git@")) or "github.com" in text.lower():
        match = re.search(r"github\.com[:/]+([^/\s:#]+)/([^/\s:#?]+)", text, re.I)
        if not match:
            return None
        owner, repo = match.group(1), match.group(2)
    elif text.count("/") == 1 and " " not in text:
        owner, repo = text.split("/", 1)
    else:
        return None
    if repo.endswith(".git"):
        repo = repo[:-4]
    owner, repo = owner.strip().lower(), repo.strip().lower()
    if not owner or not repo:
        return None
    return f"{owner}/{repo}"


def norm_page(url: str | None) -> str | None:
    """Identity for a listing URL. Query and fragment are ignored."""
    if not url or not isinstance(url, str):
        return None
    try:
        parts = urllib.parse.urlsplit(url.strip())
    except ValueError:
        return None
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return None
    host = parts.hostname.lower().rstrip(".")
    port = parts.port
    netloc = host
    if port and not ((parts.scheme == "https" and port == 443) or (parts.scheme == "http" and port == 80)):
        netloc = f"{host}:{port}"
    path = parts.path or ""
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return f"{parts.scheme}://{netloc}{path}"


def host_of(url: str | None) -> str:
    if not url:
        return ""
    try:
        return (urllib.parse.urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def strip_fragment(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))


def risky_query(url: str) -> bool:
    try:
        query = urllib.parse.urlsplit(url).query
    except ValueError:
        return True
    return bool(RISKY_QUERY.search(query))


def concrete_remote(remote: dict) -> tuple[str, str] | None:
    kind = remote.get("type")
    if kind not in ("streamable-http", "sse"):
        return None
    url = remote.get("url")
    if not isinstance(url, str) or not url:
        return None
    variables = remote.get("variables") if isinstance(remote.get("variables"), dict) else {}

    def repl(match: re.Match) -> str:
        spec = variables.get(match.group(1))
        default = spec.get("default") if isinstance(spec, dict) else None
        if not isinstance(default, str) or not default or "{" in default or "}" in default:
            return match.group(0)
        return default

    filled = re.sub(r"\{([A-Za-z0-9_]+)\}", repl, url)
    if "{" in filled or not filled.startswith(("http://", "https://")):
        return None
    return kind, strip_fragment(filled)


def prepare_registry_server(item: dict) -> dict | None:
    server = item.get("server") if isinstance(item.get("server"), dict) else item
    if not isinstance(server, dict):
        return None
    choices = []
    for remote in server.get("remotes") or []:
        if isinstance(remote, dict):
            picked = concrete_remote(remote)
            if picked:
                choices.append(picked)
    choices.sort(key=lambda item: (0 if item[0] == "streamable-http" else 1, item[1]))
    endpoint, transport = (choices[0][1], choices[0][0]) if choices else (None, None)
    packages = [pkg for pkg in (server.get("packages") or []) if isinstance(pkg, dict)]
    templated_remote = False
    if endpoint is None:
        for remote in server.get("remotes") or []:
            if isinstance(remote, dict) and isinstance(remote.get("url"), str) and remote.get("url").startswith("http"):
                templated_remote = True
    stdio_only = bool(packages) and not templated_remote and endpoint is None and all(
        (pkg.get("transport") or {}).get("type") == "stdio" for pkg in packages
    )
    site = norm_page(server.get("websiteUrl"))
    repo = github_key(((server.get("repository") or {}) if isinstance(server.get("repository"), dict) else {}).get("url"))
    return {
        "endpoint": endpoint,
        "transport": transport,
        "stdio_only": stdio_only,
        "site": site,
        "repo": repo,
    }


def _unique(groups: dict[str, list]) -> dict[str, dict]:
    return {key: rows[0] for key, rows in groups.items() if len(rows) == 1}


class Classification:
    def __init__(self, slug: str, disposition: str, endpoint: str | None, transport: str | None):
        self.slug = slug
        self.disposition = disposition
        self.endpoint = endpoint
        self.transport = transport
        self.host = host_of(endpoint)


def classify_rich(mcp: dict) -> Classification | None:
    if not isinstance(mcp, dict):
        return None
    endpoint = mcp.get("endpoint")
    transport = str(mcp.get("transport") or "")
    if not endpoint and not transport:
        return None
    endpoint = str(endpoint or "").strip()
    if endpoint.startswith(("http://", "https://")):
        kind = "sse" if re.search(r"\bsse\b", transport, re.I) and "streamable" not in transport.lower() else "streamable-http"
        return Classification("", "remote", strip_fragment(endpoint), kind)
    return Classification("", "local_only", None, "stdio")


def match_listings(tools: list, rich: dict, registry_servers: list) -> dict[str, Classification]:
    prepared = []
    for item in registry_servers:
        if isinstance(item, dict):
            row = prepare_registry_server(item)
            if row:
                prepared.append(row)
    by_site: dict[str, list] = defaultdict(list)
    by_repo: dict[str, list] = defaultdict(list)
    for row in prepared:
        if row["site"]:
            by_site[row["site"]].append(row)
        if row["repo"]:
            by_repo[row["repo"]].append(row)
    site_one = _unique(by_site)
    repo_one = _unique(by_repo)

    our_sites: dict[str, list] = defaultdict(list)
    our_repos: dict[str, list] = defaultdict(list)
    listings = []
    seen = set()
    for tool in tools:
        if not isinstance(tool, dict) or tool.get("category") != "MCP servers":
            continue
        slug = tool.get("slug")
        if not isinstance(slug, str) or not slug or slug in seen:
            continue
        seen.add(slug)
        listings.append(tool)
        for field in ("url", "website"):
            key = norm_page(tool.get(field))
            if key:
                our_sites[key].append(slug)
        repo = github_key(tool.get("github")) or github_key(tool.get("repo"))
        if repo:
            our_repos[repo].append(slug)
    unique_sites = {key: slugs[0] for key, slugs in our_sites.items() if len(set(slugs)) == 1}
    unique_repos = {key: slugs[0] for key, slugs in our_repos.items() if len(set(slugs)) == 1}

    out: dict[str, Classification] = {}
    for tool in listings:
        slug = tool["slug"]
        rich_row = rich.get(slug) if isinstance(rich, dict) else None
        mcp = rich_row.get("mcp") if isinstance(rich_row, dict) else None
        rich_cls = classify_rich(mcp) if isinstance(mcp, dict) else None
        if rich_cls is not None:
            rich_cls.slug = slug
            if rich_cls.disposition == "remote" and risky_query(rich_cls.endpoint or ""):
                continue
            out[slug] = rich_cls
            continue
        site_keys = [norm_page(tool.get(field)) for field in ("url", "website")]
        match = None
        for key in site_keys:
            if key and unique_sites.get(key) == slug and key in site_one:
                match = site_one[key]
                break
        if match is None:
            repo = github_key(tool.get("github")) or github_key(tool.get("repo"))
            if repo and unique_repos.get(repo) == slug and repo in repo_one:
                match = repo_one[repo]
        if not match:
            continue
        if match["endpoint"] and not risky_query(match["endpoint"]):
            out[slug] = Classification(slug, "remote", match["endpoint"], match["transport"])
        elif match["stdio_only"]:
            out[slug] = Classification(slug, "local_only", None, "stdio")
    return out


class Limiter:
    """Global requests/second cap, plus a per-host gap. Sleep happens outside the lock."""

    def __init__(self, rps: float = DEFAULT_RPS, per_host_interval: float = 1.0, now=None, sleep=None):
        self.gap = (1.0 / rps) if rps else 0.0
        self.per_host_interval = per_host_interval
        self._now = now or time.monotonic
        self._sleep = sleep or time.sleep
        self._lock = threading.Lock()
        self._next = 0.0
        self._host_next: dict[str, float] = {}

    def wait(self, host: str, *, per_host: bool = True) -> None:
        with self._lock:
            now = self._now()
            host_at = self._host_next.get(host, 0.0) if per_host else now
            slot = max(self._next, host_at, now)
            self._next = slot + self.gap
            if per_host:
                self._host_next[host] = slot + self.per_host_interval
            delay = slot - now
        if delay > 0:
            self._sleep(delay)


def _chain(exc: BaseException):
    seen = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        yield current
        seen.add(id(current))
        nxt = getattr(current, "reason", None)
        if not isinstance(nxt, BaseException) or nxt is current:
            nxt = current.__cause__ if isinstance(current.__cause__, BaseException) else None
        current = nxt


def reason_for_exception(exc: BaseException) -> str:
    for current in _chain(exc):
        if isinstance(current, (TimeoutError, socket.timeout)):
            return "timeout"
        if isinstance(current, socket.gaierror):
            return "dns"
        if isinstance(current, ssl.SSLError):
            return "tls"
        text = str(current).lower()
        if "timed out" in text or "timeout" in text:
            return "timeout"
        if "non-public" in text:
            return "non_public"
        if "certificate" in text or "tls" in text or "ssl" in text:
            return "tls"
        if "name or service not known" in text or "nodename nor servname" in text or "temporary failure in name resolution" in text:
            return "dns"
    return "connection"


def screen_endpoint(url: str) -> str | None:
    """None when the URL is a public http(s) host. Reuses the link checker's address rule."""
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return "non_public"
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return "non_public"
    try:
        infos = socket.getaddrinfo(parts.hostname, None)
    except socket.gaierror:
        return "dns"
    except UnicodeError:
        return "dns"
    if not infos:
        return "dns"
    import check_mcp_links

    if not check_mcp_links.public(url):
        return "non_public"
    return None


def _check_method(body: dict) -> None:
    method = body.get("method")
    if method not in ALLOWED_METHODS:
        raise RuntimeError(f"refusing MCP method {method!r}")


def parse_messages(raw: bytes, content_type: str) -> list[dict]:
    if not raw:
        return []
    text = raw.decode("utf-8", "replace")
    stripped = text.strip()
    if not stripped:
        return []
    ctype = (content_type or "").lower()
    looks_sse = "text/event-stream" in ctype or stripped.startswith("event:") or stripped.startswith("data:")
    if looks_sse:
        return _parse_sse_blob(text)
    try:
        msg = json.loads(stripped)
    except json.JSONDecodeError:
        return []
    if isinstance(msg, list):
        return [item for item in msg if isinstance(item, dict)]
    if isinstance(msg, dict):
        return [msg]
    return []


def _parse_sse_blob(text: str) -> list[dict]:
    messages = []
    event = "message"
    data: list[str] = []

    def flush() -> None:
        nonlocal event, data
        if not data:
            event = "message"
            return
        blob = "\n".join(data).strip()
        event_name = event or "message"
        data = []
        event = "message"
        if not blob:
            return
        try:
            parsed = json.loads(blob)
        except json.JSONDecodeError:
            messages.append({"_event": event_name, "_data": blob})
            return
        if isinstance(parsed, dict):
            parsed = dict(parsed)
            parsed.setdefault("_event", event_name)
            messages.append(parsed)

    for line in text.splitlines():
        if line == "":
            flush()
            continue
        if line.startswith("event:"):
            event = line[6:].strip() or "message"
        elif line.startswith("data:"):
            data.append(line[5:].lstrip())
    flush()
    return messages


def rpc_for_id(messages: list[dict], rpc_id: int) -> dict | None:
    for msg in messages:
        if msg.get("id") == rpc_id or msg.get("id") == str(rpc_id):
            return msg
    rpcs = [msg for msg in messages if "result" in msg or "error" in msg]
    if len(rpcs) == 1:
        return rpcs[0]
    return None


def is_auth_error(msg: dict | None) -> bool:
    if not isinstance(msg, dict) or "error" not in msg:
        return False
    err = msg["error"]
    if isinstance(err, dict):
        text = f"{err.get('message', '')} {err.get('data', '')}"
    else:
        text = str(err)
    return bool(AUTH_ERROR.search(text))


def supported_versions(msg: dict | None) -> list[str]:
    if not isinstance(msg, dict) or not isinstance(msg.get("error"), dict):
        return []
    err = msg["error"]
    if "protocol" not in str(err.get("message") or "").lower():
        return []
    data = err.get("data")
    found = []
    if isinstance(data, dict):
        for key in ("supported", "supportedProtocolVersions", "versions"):
            value = data.get(key)
            if isinstance(value, list):
                found.extend(item for item in value if isinstance(item, str) and item)
    return found


def make_opener(allow):
    class Guard(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            if not allow(newurl):
                raise urllib.error.URLError("redirect to non-public address skipped")
            return super().redirect_request(req, fp, code, msg, hdrs, newurl)

    return urllib.request.build_opener(Guard())


class Session:
    def __init__(self, opener, limiter: Limiter, timeout: float):
        self.opener = opener
        self.limiter = limiter
        self.timeout = timeout
        self.session_id = None
        self.protocol = PROTOCOL
        self.rpc_id = 0
        self.events: list | None = None

    def next_id(self) -> int:
        self.rpc_id += 1
        return self.rpc_id

    def send(self, url: str, body: dict | None, *, method: str = "POST"):
        if body is not None:
            _check_method(body)
        host = host_of(url)
        self.limiter.wait(host, per_host=True)
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "Accept": "application/json, text/event-stream",
            "User-Agent": USER_AGENT,
            "Origin": "https://agentscouthq.com",
            "MCP-Protocol-Version": self.protocol,
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=self.timeout) as resp:
                raw = resp.read(MAX_BODY)
                status = getattr(resp, "status", 200)
                hdrs = {key.lower(): value for key, value in resp.headers.items()}
        except urllib.error.HTTPError as exc:
            raw = exc.read(MAX_BODY) if exc.fp else b""
            status = exc.code
            hdrs = {key.lower(): value for key, value in (exc.headers.items() if exc.headers else [])}
        except Exception as exc:
            return 0, {}, b"", exc
        sid = hdrs.get("mcp-session-id")
        if sid:
            self.session_id = sid
        return status, hdrs, raw, None


def _base_result(url: str, transport: str, started: float) -> dict:
    return {
        "endpoint": strip_fragment(url),
        "transport": transport,
        "outcome": "failed",
        "http_status": None,
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "protocol_version": None,
        "tool_count": None,
        "reason": "connection",
    }


def _finish(result: dict, *, outcome: str, reason: str | None, status, protocol=None, tools=None, started: float) -> dict:
    result["outcome"] = outcome
    result["reason"] = reason
    result["http_status"] = status if isinstance(status, int) and status > 0 else None
    result["protocol_version"] = protocol
    result["tool_count"] = tools
    result["latency_ms"] = int((time.perf_counter() - started) * 1000)
    return result


def _auth(result, status, started, protocol=None):
    return _finish(result, outcome="needs_auth", reason="auth", status=status, protocol=protocol, started=started)


def _fail(result, reason, status, started, protocol=None):
    return _finish(result, outcome="failed", reason=reason, status=status, protocol=protocol, started=started)


def initialize_body(protocol: str, rpc_id: int) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "method": "initialize",
        "params": {
            "protocolVersion": protocol,
            "capabilities": {},
            "clientInfo": {"name": "AgentScoutBot", "version": "1.0"},
        },
    }


def _event_messages(item) -> list[dict]:
    try:
        parsed = json.loads(item[1])
    except (json.JSONDecodeError, TypeError):
        return []
    return [parsed] if isinstance(parsed, dict) else []


def _take_rpc(session: Session, url: str, body: dict):
    """POST one JSON-RPC message. A result may come back in the body or, for SSE, on the event stream."""
    cursor = len(session.events) if session.events is not None else 0
    status, hdrs, raw, err = session.send(url, body)
    if err is not None or status in (401, 403):
        return status, None, err
    rpc_id = body.get("id")
    if rpc_id is None:
        return status, None, None
    msg = rpc_for_id(parse_messages(raw, hdrs.get("content-type", "")), rpc_id)
    if msg is not None or session.events is None:
        return status, msg, None
    deadline = time.monotonic() + session.timeout

    def matches(item):
        return item[0] not in ("endpoint", "__eof__", "__error__") and rpc_for_id(_event_messages(item), rpc_id) is not None

    found = _wait_sse(session.events, cursor, matches, deadline)
    if found is None:
        return status, None, TimeoutError("timed out waiting for SSE response")
    if found[0] == "__error__":
        return status, None, found[1]
    if found[0] == "__eof__":
        return status, None, None
    return status, rpc_for_id(_event_messages(found), rpc_id), None


def _post_initialize(session: Session, url: str):
    """Returns (status, message, error) after at most one protocol retry."""
    protocol = PROTOCOL
    tried = set()
    last = (0, None, None)
    for attempt in range(2):
        session.protocol = protocol
        tried.add(protocol)
        status, msg, err = _take_rpc(session, url, initialize_body(protocol, session.next_id()))
        if err is not None or status in (401, 403):
            return status, msg, err
        last = (status, msg, None)
        versions = supported_versions(msg)
        if not versions:
            return last
        nxt = next((item for item in versions if item not in tried), None)
        if nxt is None or attempt == 1:
            return last
        protocol = nxt
    return last


def _handshake(session: Session, url: str, result: dict, started: float) -> dict:
    status, msg, err = _post_initialize(session, url)
    if err is not None:
        return _fail(result, reason_for_exception(err), status, started)
    if status in (401, 403) or is_auth_error(msg):
        return _auth(result, status, started)
    payload = msg.get("result") if isinstance(msg, dict) else None
    if not isinstance(payload, dict) or not isinstance(payload.get("protocolVersion"), str) or not payload.get("protocolVersion"):
        if isinstance(status, int) and status >= 500:
            return _fail(result, "http_5xx", status, started)
        if isinstance(status, int) and status >= 400:
            return _fail(result, "http_4xx", status, started)
        if isinstance(msg, dict) and "error" in msg:
            return _fail(result, "protocol", status, started)
        return _fail(result, "not_mcp", status, started)
    protocol_version = payload["protocolVersion"]
    session.protocol = protocol_version
    nstatus, _nmsg, nerr = _take_rpc(session, url, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    if nerr is not None:
        return _fail(result, reason_for_exception(nerr), nstatus, started, protocol_version)
    if nstatus in (401, 403):
        return _auth(result, nstatus, started, protocol_version)
    tstatus, tmsg, terr = _take_rpc(session, url, {"jsonrpc": "2.0", "id": session.next_id(), "method": "tools/list"})
    if terr is not None:
        return _fail(result, reason_for_exception(terr), tstatus, started, protocol_version)
    if tstatus in (401, 403) or is_auth_error(tmsg):
        return _auth(result, tstatus, started, protocol_version)
    tools = tmsg.get("result") if isinstance(tmsg, dict) else None
    if not isinstance(tools, dict) or not isinstance(tools.get("tools"), list):
        if isinstance(tstatus, int) and tstatus >= 500:
            return _fail(result, "http_5xx", tstatus, started, protocol_version)
        if isinstance(tstatus, int) and tstatus >= 400:
            return _fail(result, "http_4xx", tstatus, started, protocol_version)
        if isinstance(tmsg, dict) and "error" in tmsg:
            return _fail(result, "protocol", tstatus, started, protocol_version)
        return _fail(result, "not_mcp", tstatus, started, protocol_version)
    return _finish(
        result,
        outcome="responded",
        reason=None,
        status=tstatus,
        protocol=protocol_version,
        tools=len(tools["tools"]),
        started=started,
    )


def _read_sse(resp, out: list, stop: threading.Event) -> None:
    event = "message"
    data: list[str] = []

    def flush() -> None:
        nonlocal event, data
        if not data:
            event = "message"
            return
        blob = "\n".join(data)
        name = event or "message"
        data = []
        event = "message"
        out.append((name, blob))

    try:
        while not stop.is_set():
            line = resp.readline()
            if line == b"":
                break
            text = line.decode("utf-8", "replace").rstrip("\r\n")
            if text == "":
                flush()
                continue
            if text.startswith("event:"):
                event = text[6:].strip() or "message"
            elif text.startswith("data:"):
                data.append(text[5:].lstrip())
        flush()
    except Exception as exc:
        out.append(("__error__", exc))
    finally:
        out.append(("__eof__", None))


def _wait_sse(events: list, start: int, predicate, deadline: float):
    while time.monotonic() < deadline:
        for item in events[start:]:
            if item[0] == "__error__":
                return item
            if item[0] == "__eof__":
                return item
            if predicate(item):
                return item
        time.sleep(0.02)
    return None


def probe_sse(url: str, session: Session, allow, result: dict, started: float) -> dict:
    """Open an SSE stream, then POST initialize and tools/list to the endpoint event."""
    session.limiter.wait(host_of(url), per_host=True)
    headers = {
        "Accept": "text/event-stream",
        "User-Agent": USER_AGENT,
        "Origin": "https://agentscouthq.com",
        "MCP-Protocol-Version": session.protocol,
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        resp = session.opener.open(req, timeout=session.timeout)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return _auth(result, exc.code, started)
        reason = "http_5xx" if exc.code >= 500 else "http_4xx" if exc.code >= 400 else "not_mcp"
        return _fail(result, reason, exc.code, started)
    except Exception as exc:
        return _fail(result, reason_for_exception(exc), 0, started)
    events: list = []
    stop = threading.Event()
    reader = threading.Thread(target=_read_sse, args=(resp, events, stop), daemon=True)
    reader.start()
    try:
        sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
        if sid:
            session.session_id = sid
        session.events = events
        deadline = time.monotonic() + session.timeout
        found = _wait_sse(events, 0, lambda item: item[0] == "endpoint", deadline)
        if not found or found[0] != "endpoint":
            if found and found[0] == "__error__":
                return _fail(result, reason_for_exception(found[1]), getattr(resp, "status", 0), started)
            return _fail(result, "not_mcp", getattr(resp, "status", 200), started)
        post_url = urllib.parse.urljoin(url, str(found[1]).strip())
        if not allow(post_url):
            return _fail(result, "non_public", 0, started)
        result["endpoint"] = strip_fragment(post_url)
        return _handshake(session, post_url, result, started)
    finally:
        stop.set()
        try:
            resp.close()
        except Exception:
            pass
        reader.join(timeout=1)


def probe_server(url: str, transport: str, *, timeout: float, limiter: Limiter, allow, screen, opener=None) -> dict | None:
    if risky_query(url):
        return None
    started = time.perf_counter()
    result = _base_result(url, transport if transport in ("streamable-http", "sse") else "streamable-http", started)
    blocked = screen(url) if screen else None
    if blocked:
        return _fail(result, blocked, 0, started)
    opener = opener or make_opener(allow)
    session = Session(opener, limiter, timeout)
    if transport == "sse":
        return probe_sse(url, session, allow, result, started)
    return _handshake(session, url, result, started)


def default_fetch(url: str, limiter: Limiter) -> dict:
    limiter.wait(host_of(url) or "registry.modelcontextprotocol.io", per_host=False)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read(8_000_000).decode("utf-8"))


def fetch_registry_servers(fetch, max_pages: int, limiter: Limiter) -> tuple[list, bool]:
    servers = []
    cursor = None
    seen = set()
    complete = False
    for _page in range(max_pages):
        params = {"version": "latest", "limit": "100"}
        if cursor:
            params["cursor"] = cursor
        url = REGISTRY + "?" + urllib.parse.urlencode(params)
        try:
            payload = fetch(url, limiter)
        except Exception as exc:
            print(f"registry fetch stopped: {reason_for_exception(exc)}", flush=True)
            break
        batch = payload.get("servers") if isinstance(payload, dict) else None
        if not isinstance(batch, list):
            break
        servers.extend(batch)
        nxt = (payload.get("metadata") or {}).get("nextCursor") if isinstance(payload, dict) else None
        print(f"registry page servers={len(servers)}", flush=True)
        if not batch or not isinstance(nxt, str) or not nxt or nxt in seen:
            complete = True
            break
        seen.add(nxt)
        cursor = nxt
    else:
        complete = False
    return servers, complete


def select_batch(candidates: list[Classification], start_slug: str | None, deferred: list[str], limit: int, per_host: int):
    ordered = sorted(candidates, key=lambda item: item.slug)
    by_slug = {item.slug: item for item in ordered}
    ring = []
    seen = set()
    for slug in deferred:
        item = by_slug.get(slug)
        if item and slug not in seen:
            ring.append(item)
            seen.add(slug)
    if ordered:
        slugs = [item.slug for item in ordered]
        start = slugs.index(start_slug) if start_slug in by_slug else 0
        for offset in range(len(ordered)):
            item = ordered[(start + offset) % len(ordered)]
            if item.slug not in seen:
                ring.append(item)
                seen.add(item.slug)
    picked = []
    deferred_out = []
    hosts: dict[str, int] = {}
    for item in ring:
        if len(picked) >= limit:
            break
        host = item.host or ""
        if per_host and hosts.get(host, 0) >= per_host:
            deferred_out.append(item.slug)
            continue
        hosts[host] = hosts.get(host, 0) + 1
        picked.append(item)
    picked_set = {item.slug for item in picked}
    deferred_set = set(deferred_out)
    next_slug = start_slug
    if ordered:
        slugs = [item.slug for item in ordered]
        start = slugs.index(start_slug) if start_slug in by_slug else 0
        next_slug = slugs[start]
        for offset in range(len(ordered)):
            slug = slugs[(start + offset) % len(ordered)]
            if slug not in picked_set and slug not in deferred_set:
                next_slug = slug
                break
    return picked, next_slug, deferred_out


def history_path(directory: Path, when: datetime) -> Path:
    return directory / f"{when.strftime('%Y-%m')}.jsonl"


def load_history(directory: Path) -> list[dict]:
    rows = []
    if not directory.is_dir():
        return rows
    for path in sorted(directory.glob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and isinstance(row.get("slug"), str):
                rows.append(row)
    return rows


def append_history(directory: Path, rows: list[dict], when: datetime) -> None:
    if not rows:
        return
    directory.mkdir(parents=True, exist_ok=True)
    path = history_path(directory, when)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps({key: row.get(key) for key in RECORD_KEYS}, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()


def window_stats(records: list[dict], now: datetime, days: int) -> tuple[int, int, int, float | None]:
    cutoff = now - timedelta(days=days)
    ok = failed = auth = 0
    for row in records:
        ts = parse_ts(row.get("ts") or "")
        if ts is None or ts < cutoff or ts > now + timedelta(days=1):
            continue
        outcome = row.get("outcome")
        if outcome == "responded":
            ok += 1
        elif outcome == "failed":
            failed += 1
        elif outcome == "needs_auth":
            auth += 1
    counted = ok + failed
    rate = round(ok / counted, 3) if counted else None
    return ok, counted, auth, rate


def choose_display(probes_30: int, ok_30: int, n_30: int, auth_30: int) -> str:
    if probes_30 < MIN_PROBES:
        return "insufficient"
    if auth_30 == probes_30:
        return "needs_auth"
    if n_30 >= MIN_PROBES:
        return "rate"
    if auth_30 >= MIN_PROBES and ok_30 == 0:
        return "needs_auth"
    return "insufficient"


def badge_text(row: dict | None) -> str:
    if not isinstance(row, dict):
        return "Not yet checked"
    display = row.get("display")
    if display == "local_only":
        return "Local only"
    if display == "needs_auth":
        return "Needs auth"
    if display == "rate":
        return f"Responded {int(row.get('ok_30d') or 0)}/{int(row.get('n_30d') or 0)} checks in last 30 days"
    return "Not yet checked"


def build_summary(history: list[dict], classifications: dict[str, Classification], now: datetime, *, previous: dict | None, registry_complete: bool) -> dict:
    by_slug: dict[str, list] = defaultdict(list)
    for row in history:
        by_slug[row["slug"]].append(row)
    slugs = set(by_slug)
    for slug, item in classifications.items():
        if item.disposition in ("remote", "local_only"):
            slugs.add(slug)
    prev_servers = (previous or {}).get("servers") if isinstance(previous, dict) else None
    prev_servers = prev_servers if isinstance(prev_servers, dict) else {}
    if not registry_complete:
        for slug, row in prev_servers.items():
            if isinstance(row, dict) and row.get("disposition") == "local_only" and slug not in classifications:
                slugs.add(slug)
    servers = {}
    for slug in sorted(slugs):
        cls = classifications.get(slug)
        prev = prev_servers.get(slug) if isinstance(prev_servers.get(slug), dict) else {}
        records = sorted(by_slug.get(slug) or [], key=lambda row: row.get("ts") or "")
        if cls is not None and cls.disposition == "local_only":
            disposition, endpoint, transport = "local_only", None, "stdio"
        elif cls is None and not registry_complete and prev.get("disposition") == "local_only":
            disposition, endpoint, transport = "local_only", prev.get("endpoint"), prev.get("transport")
        else:
            disposition = "remote"
            endpoint = cls.endpoint if cls is not None else None
            transport = cls.transport if cls is not None else None
            if endpoint is None and records:
                endpoint = records[-1].get("endpoint")
                transport = transport or records[-1].get("transport")
        if disposition == "local_only":
            servers[slug] = {"disposition": "local_only", "display": "local_only", "probes": len(records)}
            continue
        ok7, n7, _auth7, rate7 = window_stats(records, now, 7)
        ok30, n30, auth30, rate30 = window_stats(records, now, 30)
        probes_30 = ok30 + n30 + auth30
        item = {
            "auth_30d": auth30,
            "disposition": "remote",
            "display": choose_display(probes_30, ok30, n30, auth30),
            "n_7d": n7,
            "n_30d": n30,
            "ok_7d": ok7,
            "ok_30d": ok30,
            "probes": len(records),
            "rate_7d": rate7,
            "rate_30d": rate30,
        }
        if endpoint:
            item["endpoint"] = endpoint
        if transport:
            item["transport"] = transport
        if records:
            last = records[-1]
            item["last_checked"] = last.get("ts")
            item["last_outcome"] = last.get("outcome")
            item["last_reason"] = last.get("reason")
            successes = [row.get("ts") for row in records if row.get("outcome") == "responded" and row.get("ts")]
            if successes:
                item["last_success"] = successes[-1]
        servers[slug] = item
    return {
        "generated": iso(now),
        "min_probes": MIN_PROBES,
        "registry_complete": registry_complete,
        "servers": servers,
    }


def execute(
    root: Path,
    *,
    limit: int = DEFAULT_LIMIT,
    dry_run: bool = False,
    registry_pages: int = DEFAULT_REGISTRY_PAGES,
    per_host: int = DEFAULT_PER_HOST,
    rps: float = DEFAULT_RPS,
    timeout: float = DEFAULT_TIMEOUT,
    registry: list | None = None,
    fetch=None,
    probe=None,
    now: datetime | None = None,
    limiter: Limiter | None = None,
) -> dict:
    now = now or utcnow()
    tools = load_tools(root / "tools.json")
    rich = load_json(root / "tool_rich.json", {})
    if not isinstance(rich, dict):
        rich = {}
    limiter = limiter or Limiter(rps=rps, per_host_interval=1.0)
    registry_complete = True
    if registry is None:
        registry, registry_complete = fetch_registry_servers(fetch or default_fetch, registry_pages, limiter)
    classifications = match_listings(tools, rich, registry)
    remote = [item for item in classifications.values() if item.disposition == "remote" and item.endpoint]
    local_only = sum(1 for item in classifications.values() if item.disposition == "local_only")
    mcp_total = sum(1 for tool in tools if isinstance(tool, dict) and tool.get("category") == "MCP servers")
    health = root / "data" / "mcp-health"
    state = load_json(health / "state.json", {}) if health.is_dir() else {}
    if not isinstance(state, dict):
        state = {}
    deferred = [slug for slug in (state.get("deferred") or []) if isinstance(slug, str)]
    picked, next_slug, deferred_out = select_batch(remote, state.get("next_slug"), deferred, limit, per_host)
    probe_fn = probe or _production_probe
    results = []
    skipped = 0
    for item in picked:
        try:
            probed = probe_fn(item.endpoint, item.transport or "streamable-http", timeout=timeout, limiter=limiter)
        except Exception as exc:
            probed = _base_result(item.endpoint, item.transport or "streamable-http", time.perf_counter())
            probed["reason"] = reason_for_exception(exc)
            probed["latency_ms"] = 0
        if not probed:
            skipped += 1
            print(f"{item.slug} skipped credential-like endpoint", flush=True)
            continue
        row = {key: probed.get(key) for key in RECORD_KEYS}
        row["slug"] = item.slug
        row["ts"] = iso(now)
        row["endpoint"] = probed.get("endpoint") or item.endpoint
        row["transport"] = probed.get("transport") or item.transport
        results.append(row)
        print(
            f"{item.slug} {row['outcome']} http={row['http_status']} {row['latency_ms']}ms {row['reason'] or ''} {row['endpoint']}",
            flush=True,
        )
    history = load_history(health)
    history.extend(results)
    previous = load_json(health / "summary.json", {})
    summary = build_summary(history, classifications, now, previous=previous, registry_complete=registry_complete)
    report = {
        "probed": len(results),
        "responded": sum(1 for row in results if row["outcome"] == "responded"),
        "needs_auth": sum(1 for row in results if row["outcome"] == "needs_auth"),
        "failed": sum(1 for row in results if row["outcome"] == "failed"),
        "skipped": skipped,
        "local_only": local_only,
        "remote_candidates": len(remote),
        "unknown": max(0, mcp_total - len(remote) - local_only),
        "registry_complete": registry_complete,
        "reasons": dict(sorted(_count(row.get("reason") for row in results if row.get("reason")).items())),
        "dry_run": dry_run,
    }
    if not dry_run:
        health.mkdir(parents=True, exist_ok=True)
        append_history(health, results, now)
        (health / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        state_out = {
            "deferred": deferred_out,
            "next_slug": next_slug,
            "remote_candidates": len(remote),
            "updated": iso(now),
        }
        (health / "state.json").write_text(json.dumps(state_out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    report["summary_servers"] = len(summary["servers"])
    return report


def _count(values) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for value in values:
        if value:
            counts[str(value)] += 1
    return counts


def _production_probe(url: str, transport: str, *, timeout: float, limiter: Limiter):
    def allow(target: str) -> bool:
        return screen_endpoint(target) is None

    return probe_server(url, transport, timeout=timeout, limiter=limiter, allow=allow, screen=screen_endpoint)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe public MCP endpoints with initialize and tools/list.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--per-host", type=int, default=DEFAULT_PER_HOST)
    parser.add_argument("--rps", type=float, default=DEFAULT_RPS)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--registry-pages", type=int, default=DEFAULT_REGISTRY_PAGES)
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.limit < 0 or args.per_host < 1 or args.rps <= 0 or args.timeout <= 0:
        print("limit, per-host, rps, and timeout must be positive", file=sys.stderr)
        return 2
    root = args.root or repo_root()
    if not (root / "tools.json").is_file():
        print(f"tools.json is missing under {root}", file=sys.stderr)
        return 1
    report = execute(
        root,
        limit=args.limit,
        dry_run=args.dry_run,
        registry_pages=args.registry_pages,
        per_host=args.per_host,
        rps=args.rps,
        timeout=args.timeout,
    )
    print(
        "classifications remote={remote_candidates} local_only={local_only} unknown={unknown} registry_complete={registry_complete}".format(**report),
        flush=True,
    )
    print(
        "probed={probed} responded={responded} needs_auth={needs_auth} failed={failed} skipped={skipped} reasons={reasons}".format(**report),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
