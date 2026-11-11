#!/usr/bin/env python3
"""Quick initialize probe for candidate MCP HTTP endpoints."""
import json, ssl, sys, time, urllib.request, urllib.error

ENDPOINTS = [
    ("microsoft-learn-mcp", "https://learn.microsoft.com/api/mcp"),
    ("microsoft-learn-mcp-alt", "https://learn.microsoft.com/mcp"),
    ("context7", "https://mcp.context7.com/mcp"),
    ("gitmcp", "https://gitmcp.io/docs"),
    ("gitmcp-mcp", "https://gitmcp.io/mcp"),
    ("cf-docs", "https://docs.mcp.cloudflare.com/mcp"),
    ("cf-docs-sse", "https://docs.mcp.cloudflare.com/sse"),
    ("hf-mcp", "https://huggingface.co/mcp"),
    ("agentscout", "https://mcp.agentscouthq.com/mcp"),
    ("toolspad", "https://toolspad.com/mcp"),
    ("crakseo", "https://crakseo.com/mcp"),
    ("anonli", "https://anon.li/mcp"),
    ("tiktokapi", "https://tiktokapi.io/mcp"),
]

INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "agentscout-mcp-test-sample", "version": "0.1.0"},
    },
}

CTX = ssl.create_default_context()

def post(url, body, headers, timeout=15):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            raw = r.read()
            ms = (time.perf_counter() - t0) * 1000
            return r.status, dict(r.headers), raw, ms, None
    except urllib.error.HTTPError as e:
        raw = e.read()
        ms = (time.perf_counter() - t0) * 1000
        return e.code, dict(e.headers), raw, ms, str(e)
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000
        return 0, {}, b"", ms, repr(e)

def peek(raw, n=400):
    try:
        return raw.decode("utf-8", "replace")[:n]
    except Exception:
        return repr(raw[:n])

for name, url in ENDPOINTS:
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": "2025-06-18",
        "User-Agent": "AgentScoutMCPTest/0.1 (+https://agentscouthq.com/about.html)",
    }
    status, hdrs, raw, ms, err = post(url, INIT, headers)
    ctype = hdrs.get("Content-Type") or hdrs.get("content-type") or ""
    session = hdrs.get("Mcp-Session-Id") or hdrs.get("mcp-session-id") or ""
    print(f"\n=== {name}  {url}")
    print(f"  status={status}  {ms:.0f}ms  ctype={ctype!r}  session_set={bool(session)}  err={err}")
    print(f"  body: {peek(raw)}")
