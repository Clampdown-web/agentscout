#!/usr/bin/env python3
"""MCP response-rate probe, summary, and workflow. No live network."""
from __future__ import annotations

import json
import queue
import re
import socketserver
import tempfile
import threading
import time
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mcp_response_rate as mrr

NOW = datetime(2026, 11, 11, 15, 15, tzinfo=timezone.utc)


class Clock:
    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t

    def sleep(self, delay):
        self.t += delay


class QuietServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def _handler(mode: str):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            return

        def _read(self) -> dict:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            body = json.loads(raw.decode("utf-8")) if raw else {}
            self.server.calls.append(
                {
                    "method": body.get("method"),
                    "body": body,
                    "headers": {key.lower(): value for key, value in self.headers.items()},
                    "path": self.path,
                }
            )
            return body

        def _json(self, status: int, payload: dict, extra=None):
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            for key, value in (extra or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            body = self._read()
            if mode == "slow":
                time.sleep(0.8)
            if mode == "auth":
                self._json(401, {"error": "unauthorized"}, {"WWW-Authenticate": "Bearer"})
                return
            if mode == "html":
                raw = b"<!doctype html><title>Docs</title>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            if mode == "err":
                raw = b"unavailable"
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            if mode == "redirect":
                self.send_response(302)
                self.send_header("Location", "http://169.254.169.254/latest/meta-data")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            method = body.get("method")
            if mode == "protocol" and method == "initialize":
                version = (body.get("params") or {}).get("protocolVersion")
                if version != "2024-11-05":
                    self._json(
                        200,
                        {
                            "jsonrpc": "2.0",
                            "id": body.get("id"),
                            "error": {
                                "code": -32602,
                                "message": "Unsupported protocol version",
                                "data": {"supported": ["2024-11-05"]},
                            },
                        },
                    )
                    return
            if method == "initialize":
                extra = {"Mcp-Session-Id": "sess-1"} if mode == "session" else None
                version = "2024-11-05" if mode == "protocol" else "2025-06-18"
                self._json(
                    200,
                    {
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "result": {
                            "protocolVersion": version,
                            "capabilities": {},
                            "serverInfo": {"name": "mock", "version": "1"},
                        },
                    },
                    extra,
                )
                return
            if method == "notifications/initialized":
                self.send_response(202)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if method == "tools/list":
                if mode == "session" and self.headers.get("Mcp-Session-Id") != "sess-1":
                    self._json(400, {"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32000, "message": "missing session"}})
                    return
                tools = [] if mode == "empty" else [{"name": "alpha"}, {"name": "beta"}]
                self._json(200, {"jsonrpc": "2.0", "id": body.get("id"), "result": {"tools": tools}})
                return
            self._json(200, {"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32601, "message": "no"}})

        def do_GET(self):
            self._read_get()

        def _read_get(self):
            self.server.calls.append({"method": "GET", "path": self.path, "headers": {key.lower(): value for key, value in self.headers.items()}})
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

    return Handler


def _sse_handler():
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            return

        def do_GET(self):
            self.server.calls.append({"method": "GET", "path": self.path})
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(b"event: endpoint\ndata: /message\n\n")
            self.wfile.flush()
            while True:
                try:
                    chunk = self.server.outbox.get(timeout=0.2)
                except Exception:
                    if getattr(self.server, "done", False):
                        break
                    continue
                if chunk is None:
                    break
                try:
                    self.wfile.write(chunk)
                    self.wfile.flush()
                except Exception:
                    break

        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            body = json.loads(raw.decode("utf-8")) if raw else {}
            self.server.calls.append(
                {
                    "method": body.get("method"),
                    "body": body,
                    "headers": {key.lower(): value for key, value in self.headers.items()},
                    "path": self.path,
                }
            )
            self.send_response(202)
            self.send_header("Content-Length", "0")
            self.end_headers()
            method = body.get("method")
            msg = None
            if method == "initialize":
                msg = {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {"protocolVersion": "2025-06-18", "capabilities": {}, "serverInfo": {"name": "sse", "version": "1"}},
                }
            elif method == "tools/list":
                msg = {"jsonrpc": "2.0", "id": body.get("id"), "result": {"tools": [{"name": "alpha"}]}}
            if msg is not None:
                payload = json.dumps(msg).encode("utf-8")
                self.server.outbox.put(b"event: message\ndata: " + payload + b"\n\n")

    return Handler


class ServerCase(unittest.TestCase):
    def _probe(self, mode: str, transport: str = "streamable-http", timeout: float = 3):
        handler = _sse_handler() if mode == "sse" else _handler(mode)
        httpd = QuietServer(("127.0.0.1", 0), handler)
        httpd.calls = []
        httpd.outbox = queue.Queue()
        httpd.done = False
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        host, port = httpd.server_address
        url = f"http://{host}:{port}/mcp" if mode != "sse" else f"http://{host}:{port}/sse"
        try:
            limiter = mrr.Limiter(rps=1000, per_host_interval=0)

            def allow(target: str) -> bool:
                return urllib.parse.urlsplit(target).hostname == "127.0.0.1"

            result = mrr.probe_server(
                url,
                transport,
                timeout=timeout,
                limiter=limiter,
                allow=allow,
                screen=lambda _url: None,
            )
            return result, httpd.calls
        finally:
            httpd.done = True
            httpd.outbox.put(None)
            httpd.shutdown()
            httpd.server_close()

    def test_initialize_and_tools_list_count_as_responded(self):
        result, calls = self._probe("ok")
        methods = [call["method"] for call in calls]
        self.assertEqual(methods, ["initialize", "notifications/initialized", "tools/list"])
        self.assertEqual(result["outcome"], "responded")
        self.assertEqual(result["protocol_version"], "2025-06-18")
        self.assertEqual(result["tool_count"], 2)
        self.assertEqual(result["http_status"], 200)
        self.assertIsNone(result["reason"])
        self.assertNotIn("alpha", json.dumps(result))
        self.assertEqual(calls[0]["headers"]["user-agent"], mrr.USER_AGENT)
        for call in calls:
            self.assertNotIn("authorization", call["headers"])

    def test_empty_tool_list_still_responded(self):
        result, _calls = self._probe("empty")
        self.assertEqual(result["outcome"], "responded")
        self.assertEqual(result["tool_count"], 0)

    def test_auth_is_not_a_failure_and_stops_before_tools_list(self):
        result, calls = self._probe("auth")
        self.assertEqual(result["outcome"], "needs_auth")
        self.assertEqual(result["reason"], "auth")
        self.assertEqual(result["http_status"], 401)
        self.assertEqual([call["method"] for call in calls], ["initialize"])

    def test_html_page_is_not_mcp(self):
        result, _calls = self._probe("html")
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["reason"], "not_mcp")

    def test_http_500(self):
        result, _calls = self._probe("err")
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["reason"], "http_5xx")
        self.assertEqual(result["http_status"], 500)

    def test_timeout(self):
        result, _calls = self._probe("slow", timeout=0.2)
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["reason"], "timeout")

    def test_protocol_retry_uses_the_offered_version(self):
        result, calls = self._probe("protocol")
        inits = [call["body"] for call in calls if call["method"] == "initialize"]
        self.assertEqual([item["params"]["protocolVersion"] for item in inits], ["2025-06-18", "2024-11-05"])
        self.assertEqual(result["outcome"], "responded")
        self.assertEqual(result["protocol_version"], "2024-11-05")
        self.assertNotIn("tools/call", [call["method"] for call in calls])

    def test_session_header_is_echoed_and_not_stored(self):
        result, calls = self._probe("session")
        self.assertEqual(result["outcome"], "responded")
        listed = next(call for call in calls if call["method"] == "tools/list")
        self.assertEqual(listed["headers"].get("mcp-session-id"), "sess-1")
        self.assertNotIn("sess-1", json.dumps(result))

    def test_redirect_to_a_non_public_address_is_not_followed(self):
        result, calls = self._probe("redirect")
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["reason"], "non_public")
        self.assertEqual(len(calls), 1)
        self.assertNotIn("169.254.169.254", json.dumps(calls))

    def test_sse_endpoint_event_then_tools_list(self):
        result, calls = self._probe("sse", transport="sse")
        self.assertEqual(result["outcome"], "responded")
        self.assertEqual(result["tool_count"], 1)
        self.assertTrue(result["endpoint"].endswith("/message"))
        methods = [call["method"] for call in calls]
        self.assertEqual(methods[0], "GET")
        self.assertIn("initialize", methods)
        self.assertIn("tools/list", methods)
        self.assertNotIn("tools/call", methods)

    def test_refuses_any_method_outside_the_handshake(self):
        with self.assertRaises(RuntimeError):
            mrr._check_method({"jsonrpc": "2.0", "id": 1, "method": "tools/call"})

    def test_credential_query_is_not_requested(self):
        limiter = mrr.Limiter(rps=1000, per_host_interval=0)
        result = mrr.probe_server(
            "https://example.com/mcp?api_key=sekret",
            "streamable-http",
            timeout=1,
            limiter=limiter,
            allow=lambda _url: True,
            screen=lambda _url: None,
        )
        self.assertIsNone(result)


class ClassifyTests(unittest.TestCase):
    def test_unique_website_and_repo_and_stdio(self):
        tools = [
            {"slug": "remote-site", "category": "MCP servers", "url": "https://a.example/docs", "website": "https://a.example/docs", "github": ""},
            {"slug": "remote-repo", "category": "MCP servers", "url": "https://docs.b.example", "website": "", "github": "https://github.com/b/b"},
            {"slug": "local", "category": "MCP servers", "url": "https://c.example", "website": "https://c.example", "github": "https://github.com/c/c"},
            {"slug": "unknown", "category": "MCP servers", "url": "https://d.example", "website": "https://d.example", "github": ""},
            {"slug": "not-mcp", "category": "coding", "url": "https://a.example/docs", "github": "https://github.com/b/b"},
        ]
        registry = [
            {"server": {"websiteUrl": "https://a.example/docs/", "remotes": [{"type": "streamable-http", "url": "https://a.example/mcp"}]}},
            {"server": {"repository": {"url": "https://github.com/b/b.git"}, "remotes": [{"type": "sse", "url": "https://mcp.b.example/sse"}]}},
            {"server": {"repository": {"url": "https://github.com/c/c"}, "packages": [{"transport": {"type": "stdio"}}]}},
        ]
        found = mrr.match_listings(tools, {}, registry)
        self.assertEqual(found["remote-site"].endpoint, "https://a.example/mcp")
        self.assertEqual(found["remote-site"].transport, "streamable-http")
        self.assertEqual(found["remote-repo"].transport, "sse")
        self.assertEqual(found["local"].disposition, "local_only")
        self.assertNotIn("unknown", found)
        self.assertNotIn("not-mcp", found)

    def test_shared_registry_repo_is_not_a_join(self):
        tools = [
            {
                "slug": "mcp-registry",
                "category": "MCP servers",
                "url": "https://github.com/modelcontextprotocol/registry",
                "website": "",
                "github": "https://github.com/modelcontextprotocol/registry",
                "repo": "modelcontextprotocol/registry",
            }
        ]
        registry = [
            {"server": {"repository": {"url": "https://github.com/modelcontextprotocol/registry"}, "remotes": [{"type": "streamable-http", "url": "https://one.example/mcp"}]}},
            {"server": {"repository": {"url": "https://github.com/modelcontextprotocol/registry"}, "remotes": [{"type": "streamable-http", "url": "https://two.example/mcp"}]}},
        ]
        self.assertEqual(mrr.match_listings(tools, {}, registry), {})

    def test_template_default_is_filled_and_a_required_var_is_not_local(self):
        tools = [
            {"slug": "filled", "category": "MCP servers", "url": "https://filled.example", "website": "https://filled.example", "github": ""},
            {"slug": "open", "category": "MCP servers", "url": "https://open.example", "website": "https://open.example", "github": "https://github.com/o/o"},
        ]
        registry = [
            {
                "server": {
                    "websiteUrl": "https://filled.example",
                    "remotes": [
                        {
                            "type": "streamable-http",
                            "url": "https://svc.example/{env}/mcp",
                            "variables": {"env": {"default": "prod"}},
                        }
                    ],
                }
            },
            {
                "server": {
                    "repository": {"url": "https://github.com/o/o"},
                    "remotes": [{"type": "streamable-http", "url": "https://svc.example/{env}/mcp", "variables": {"env": {"isRequired": True}}}],
                    "packages": [{"transport": {"type": "stdio"}}],
                }
            },
        ]
        found = mrr.match_listings(tools, {}, registry)
        self.assertEqual(found["filled"].endpoint, "https://svc.example/prod/mcp")
        self.assertNotIn("open", found)

    def test_rich_endpoint_wins_and_stdio_is_local(self):
        tools = [
            {"slug": "hosted", "category": "MCP servers", "url": "https://hosted.example", "website": "https://hosted.example", "github": "https://github.com/h/h"},
            {"slug": "disk", "category": "MCP servers", "url": "https://disk.example", "website": "", "github": "https://github.com/d/d"},
        ]
        rich = {
            "hosted": {"mcp": {"endpoint": "https://hosted.example/api/mcp", "transport": "Streamable HTTP (remote)"}},
            "disk": {"mcp": {"endpoint": "Local stdio: npx -y example", "transport": "stdio (runs on your machine)"}},
        }
        registry = [
            {"server": {"repository": {"url": "https://github.com/h/h"}, "remotes": [{"type": "streamable-http", "url": "https://other.example/mcp"}]}},
            {"server": {"repository": {"url": "https://github.com/d/d"}, "remotes": [{"type": "streamable-http", "url": "https://disk.example/mcp"}]}},
        ]
        found = mrr.match_listings(tools, rich, registry)
        self.assertEqual(found["hosted"].endpoint, "https://hosted.example/api/mcp")
        self.assertEqual(found["disk"].disposition, "local_only")

    def test_shipped_rich_records_classify_without_network(self):
        rich = json.loads((ROOT / "tool_rich.json").read_text(encoding="utf-8"))
        tools = []
        for slug, row in rich.items():
            mcp = row.get("mcp") if isinstance(row, dict) else None
            if not isinstance(mcp, dict) or not mcp.get("endpoint"):
                continue
            tools.append({"slug": slug, "category": "MCP servers", "url": "https://example.com/" + slug, "website": "", "github": ""})
        found = mrr.match_listings(tools, rich, [])
        self.assertEqual(found["robottraining-jobs"].disposition, "remote")
        self.assertTrue(found["robottraining-jobs"].endpoint.startswith("https://"))
        local = [slug for slug, item in found.items() if item.disposition == "local_only"]
        self.assertTrue(local)
        self.assertTrue(all(item.endpoint is None for item in found.values() if item.disposition == "local_only"))


class SummaryTests(unittest.TestCase):
    def test_rates_exclude_auth_and_badges_wait_for_three_probes(self):
        def row(slug, outcome, days_ago, reason=None):
            return {
                "slug": slug,
                "ts": mrr.iso(NOW - timedelta(days=days_ago)),
                "endpoint": "https://example.com/mcp",
                "transport": "streamable-http",
                "outcome": outcome,
                "http_status": 200 if outcome == "responded" else 401 if outcome == "needs_auth" else 500,
                "latency_ms": 10,
                "protocol_version": "2025-06-18" if outcome == "responded" else None,
                "tool_count": 1 if outcome == "responded" else None,
                "reason": reason,
            }

        history = [
            row("mix", "responded", 1),
            row("mix", "responded", 2),
            row("mix", "responded", 3),
            row("mix", "failed", 4, "http_5xx"),
            row("mix", "needs_auth", 1, "auth"),
            row("mix", "needs_auth", 2, "auth"),
            row("mix", "failed", 8, "timeout"),
            row("auth", "needs_auth", 1, "auth"),
            row("auth", "needs_auth", 2, "auth"),
            row("auth", "needs_auth", 3, "auth"),
            row("thin", "responded", 1),
            row("thin", "responded", 2),
        ]
        summary = mrr.build_summary(history, {}, NOW, previous=None, registry_complete=True)
        mix = summary["servers"]["mix"]
        self.assertEqual(mix["ok_30d"], 3)
        self.assertEqual(mix["n_30d"], 5)
        self.assertEqual(mix["auth_30d"], 2)
        self.assertEqual(mix["rate_30d"], 0.6)
        self.assertEqual(mix["ok_7d"], 3)
        self.assertEqual(mix["n_7d"], 4)
        self.assertEqual(mix["display"], "rate")
        self.assertEqual(mrr.badge_text(mix), "Responded 3/5 checks in last 30 days")
        self.assertEqual(summary["servers"]["auth"]["display"], "needs_auth")
        self.assertEqual(mrr.badge_text(summary["servers"]["auth"]), "Needs auth")
        self.assertEqual(summary["servers"]["thin"]["display"], "insufficient")
        self.assertEqual(mrr.badge_text(summary["servers"]["thin"]), "Not yet checked")
        self.assertEqual(mrr.badge_text({"display": "local_only"}), "Local only")
        self.assertEqual(mrr.badge_text(None), "Not yet checked")

    def test_malformed_history_lines_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "2026-11.jsonl").write_text('{"slug":"ok","outcome":"responded","ts":"2026-11-11T00:00:00Z"}\nnot-json\n\n', encoding="utf-8")
            rows = mrr.load_history(directory)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["slug"], "ok")

    def test_partial_registry_keeps_a_previous_local_only_row(self):
        previous = {"servers": {"disk": {"disposition": "local_only", "display": "local_only", "probes": 0}}}
        summary = mrr.build_summary([], {}, NOW, previous=previous, registry_complete=False)
        self.assertEqual(summary["servers"]["disk"]["display"], "local_only")
        wiped = mrr.build_summary([], {}, NOW, previous=previous, registry_complete=True)
        self.assertNotIn("disk", wiped["servers"])


class SelectTests(unittest.TestCase):
    def _cls(self, slug, host):
        item = mrr.Classification(slug, "remote", f"https://{host}/mcp", "streamable-http")
        return item

    def test_rotation_and_per_host_cap(self):
        candidates = [self._cls("a1", "a.example"), self._cls("a2", "a.example"), self._cls("b1", "b.example"), self._cls("c1", "c.example")]
        picked, nxt, deferred = mrr.select_batch(candidates, None, [], 2, 1)
        self.assertEqual([item.slug for item in picked], ["a1", "b1"])
        self.assertEqual(deferred, ["a2"])
        self.assertEqual(nxt, "c1")
        picked2, _nxt2, deferred2 = mrr.select_batch(candidates, nxt, deferred, 2, 1)
        self.assertEqual(picked2[0].slug, "a2")
        self.assertIn("c1", [item.slug for item in picked2])
        self.assertNotIn("a1", [item.slug for item in picked2])
        self.assertNotIn("a2", deferred2)


class LimiterTests(unittest.TestCase):
    def test_global_rate_and_per_host_gap(self):
        clock = Clock()
        limiter = mrr.Limiter(rps=5, per_host_interval=1, now=clock.now, sleep=clock.sleep)
        limiter.wait("a")
        limiter.wait("a")
        self.assertEqual(clock.t, 1.0)
        limiter.wait("b", per_host=False)
        self.assertEqual(clock.t, 1.2)


class ReasonTests(unittest.TestCase):
    def test_exception_categories(self):
        import socket
        import ssl
        import urllib.error

        self.assertEqual(mrr.reason_for_exception(socket.timeout("timed out")), "timeout")
        self.assertEqual(mrr.reason_for_exception(urllib.error.URLError(socket.gaierror(8, "nodename"))), "dns")
        self.assertEqual(mrr.reason_for_exception(ssl.SSLError("CERTIFICATE_VERIFY_FAILED")), "tls")
        self.assertEqual(mrr.reason_for_exception(urllib.error.URLError("redirect to non-public address skipped")), "non_public")
        self.assertEqual(mrr.reason_for_exception(ConnectionResetError("reset")), "connection")


class ExecuteTests(unittest.TestCase):
    def test_dry_run_does_not_write_and_a_real_run_rotates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tools = [
                {"slug": "remote-a", "category": "MCP servers", "url": "https://a.example/docs", "website": "https://a.example/docs", "github": ""},
                {"slug": "remote-b", "category": "MCP servers", "url": "https://b.example", "website": "https://b.example", "github": ""},
                {"slug": "local-c", "category": "MCP servers", "url": "https://c.example", "website": "https://c.example", "github": "https://github.com/c/c"},
                {"slug": "plain", "category": "MCP servers", "url": "https://d.example", "website": "https://d.example", "github": ""},
            ]
            registry = [
                {"server": {"websiteUrl": "https://a.example/docs", "remotes": [{"type": "streamable-http", "url": "https://a.example/mcp"}]}},
                {"server": {"websiteUrl": "https://b.example", "remotes": [{"type": "streamable-http", "url": "https://b.example/mcp"}]}},
                {"server": {"repository": {"url": "https://github.com/c/c"}, "packages": [{"transport": {"type": "stdio"}}]}},
            ]
            (root / "tools.json").write_text(json.dumps(tools), encoding="utf-8")
            (root / "tool_rich.json").write_text("{}", encoding="utf-8")
            seen = []

            def fake(url, transport, timeout, limiter):
                seen.append(url)
                return {
                    "outcome": "responded",
                    "http_status": 200,
                    "latency_ms": 4,
                    "protocol_version": "2025-06-18",
                    "tool_count": 1,
                    "reason": None,
                    "endpoint": url,
                    "transport": transport,
                }

            dry = mrr.execute(root, limit=5, dry_run=True, registry=registry, probe=fake, now=NOW, per_host=8)
            self.assertFalse((root / "data" / "mcp-health").exists())
            self.assertEqual(dry["local_only"], 1)
            self.assertEqual(dry["remote_candidates"], 2)
            self.assertEqual(dry["unknown"], 1)
            self.assertEqual(sorted(seen), ["https://a.example/mcp", "https://b.example/mcp"])
            seen.clear()
            first = mrr.execute(root, limit=1, dry_run=False, registry=registry, probe=fake, now=NOW, per_host=8)
            self.assertEqual(first["probed"], 1)
            month = root / "data" / "mcp-health" / "2026-11.jsonl"
            self.assertEqual(len(month.read_text(encoding="utf-8").splitlines()), 1)
            second = mrr.execute(root, limit=1, dry_run=False, registry=registry, probe=fake, now=NOW + timedelta(days=1), per_host=8)
            self.assertEqual(second["probed"], 1)
            lines = month.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            slugs = {json.loads(line)["slug"] for line in lines}
            self.assertEqual(slugs, {"remote-a", "remote-b"})
            summary = json.loads((root / "data" / "mcp-health" / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["servers"]["local-c"]["display"], "local_only")
            self.assertEqual(summary["servers"]["remote-a"]["display"], "insufficient")
            self.assertNotIn("plain", summary["servers"])


class WorkflowTests(unittest.TestCase):
    def test_schedule_commits_only_health_data_and_pins_actions(self):
        text = (ROOT / ".github" / "workflows" / "mcp-response-rate.yml").read_text(encoding="utf-8")
        self.assertIn("cron:", text)
        self.assertIn("data/mcp-health", text)
        self.assertIn("contents: write", text)
        self.assertNotIn("pull_request_target", text)
        self.assertNotIn("secrets.", text)
        self.assertNotIn("wrangler", text.lower())
        actions = re.findall(r"uses:\s+(\S+)", text)
        self.assertGreaterEqual(len(actions), 2)
        for action in actions:
            self.assertRegex(action, r"@[0-9a-f]{40}$")
        source = (ROOT / "scripts" / "mcp_response_rate.py").read_text(encoding="utf-8")
        self.assertNotIn("tools/call", source)
        self.assertEqual(mrr.USER_AGENT, "AgentScoutBot/1.0 (+https://agentscouthq.com)")


if __name__ == "__main__":
    unittest.main()
