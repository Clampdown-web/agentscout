#!/usr/bin/env python3
"""Streamable-HTTP MCP client for a reproducible AgentScout test report.
Never calls tools whose names suggest write/send/pay/delete.
"""
from __future__ import annotations

import json, re, ssl, time, urllib.request, urllib.error, statistics, datetime
from pathlib import Path

ENDPOINT = "https://learn.microsoft.com/api/mcp"
UA = "AgentScoutMCPTest/0.1 (+https://agentscouthq.com/about.html)"
PROTO = "2025-06-18"
CTX = ssl.create_default_context()

WRITEISH = re.compile(
    r"(write|create|update|delete|remove|send|email|post|pay|purchase|charge|"
    r"transfer|deploy|destroy|drop|insert|mutate|publish|upload|commit|push|"
    r"execute_sql|run_command|shell|exec)",
    re.I,
)

def parse_sse_or_json(raw: bytes):
    text = raw.decode("utf-8", "replace")
    messages = []
    if "event:" in text[:40] or text.startswith("event:") or "\ndata:" in text:
        data_parts = []
        for line in text.splitlines():
            if line.startswith("data:"):
                data_parts.append(line[5:].lstrip())
            elif line.strip() == "" and data_parts:
                blob = "\n".join(data_parts)
                data_parts = []
                if blob.strip():
                    try:
                        messages.append(json.loads(blob))
                    except json.JSONDecodeError:
                        messages.append({"_unparsed": blob})
        if data_parts:
            blob = "\n".join(data_parts)
            if blob.strip():
                try:
                    messages.append(json.loads(blob))
                except json.JSONDecodeError:
                    messages.append({"_unparsed": blob})
        return messages, text
    text_s = text.strip()
    if not text_s:
        return [], text
    try:
        return [json.loads(text_s)], text
    except json.JSONDecodeError:
        return [{"_unparsed": text_s}], text


class Client:
    def __init__(self, endpoint=ENDPOINT):
        self.endpoint = endpoint
        self.session = None
        self.transcript = []
        self.protocol_id = 0

    def _next_id(self):
        self.protocol_id += 1
        return self.protocol_id

    def request(self, body, timeout=30, notification=False):
        data = json.dumps(body).encode()
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": PROTO,
            "User-Agent": UA,
        }
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        req = urllib.request.Request(self.endpoint, data=data, method="POST")
        for k, v in headers.items():
            req.add_header(k, v)
        t0 = time.perf_counter()
        status, hdrs, raw, err = 0, {}, b"", None
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
                status = r.status
                hdrs = dict(r.headers)
                raw = r.read()
        except urllib.error.HTTPError as e:
            status = e.code
            hdrs = dict(e.headers)
            raw = e.read()
            err = f"HTTP {e.code}"
        except Exception as e:
            err = repr(e)
        ms = (time.perf_counter() - t0) * 1000
        sid = hdrs.get("Mcp-Session-Id") or hdrs.get("mcp-session-id")
        if sid:
            self.session = sid
        messages, raw_text = parse_sse_or_json(raw) if raw else ([], "")
        entry = {
            "t": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "request": body,
            "http_status": status,
            "http_ms": round(ms, 1),
            "response_headers": {
                k: ("[redacted]" if k.lower() == "mcp-session-id" else v)
                for k, v in hdrs.items()
                if k.lower() in (
                    "content-type", "mcp-session-id", "mcp-protocol-version",
                    "cache-control", "www-authenticate",
                )
            },
            "messages": messages,
            "error": err,
            "raw_preview": raw_text[:2000],
        }
        self.transcript.append(entry)
        return entry

    def call(self, method, params=None, timeout=30):
        body = {"jsonrpc": "2.0", "id": self._next_id(), "method": method}
        if params is not None:
            body["params"] = params
        return self.request(body, timeout=timeout)

    def notify(self, method, params=None):
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        return self.request(body, timeout=20, notification=True)

    def initialize(self):
        return self.call(
            "initialize",
            {
                "protocolVersion": PROTO,
                "capabilities": {},
                "clientInfo": {
                    "name": "agentscout-mcp-test-sample",
                    "version": "0.1.0",
                },
            },
            timeout=20,
        )


def result_of(entry):
    for m in entry.get("messages") or []:
        if isinstance(m, dict) and "result" in m:
            return m["result"]
        if isinstance(m, dict) and "error" in m:
            return {"_rpc_error": m["error"]}
    return None


def schema_issues(tools):
    issues = []
    for t in tools:
        name = t.get("name") or "(unnamed)"
        desc = (t.get("description") or "").strip()
        title = (t.get("title") or "").strip()
        if not desc:
            issues.append({"tool": name, "issue": "missing description", "severity": "high"})
        elif len(desc) < 40:
            issues.append({"tool": name, "issue": f"very short description ({len(desc)} chars)", "severity": "medium"})
        schema = t.get("inputSchema") or t.get("input_schema") or {}
        if not schema:
            issues.append({"tool": name, "issue": "missing inputSchema", "severity": "high"})
            continue
        if schema.get("type") and schema.get("type") != "object":
            issues.append({"tool": name, "issue": f"inputSchema type is {schema.get('type')!r}, expected object", "severity": "medium"})
        props = schema.get("properties") or {}
        required = schema.get("required") or []
        if schema.get("type") == "object" and not props and not schema.get("additionalProperties"):
            # empty object may be ok if no args
            pass
        for pname, pschema in props.items():
            if not isinstance(pschema, dict):
                issues.append({"tool": name, "issue": f"property {pname} is not a schema object", "severity": "high"})
                continue
            if not pschema.get("description") and not pschema.get("title"):
                issues.append({"tool": name, "issue": f"property '{pname}' has no description", "severity": "low"})
            if not pschema.get("type") and not pschema.get("anyOf") and not pschema.get("$ref") and not pschema.get("oneOf"):
                issues.append({"tool": name, "issue": f"property '{pname}' has no type", "severity": "medium"})
        for r in required:
            if r not in props:
                issues.append({"tool": name, "issue": f"required '{r}' not in properties", "severity": "high"})
        # annotate annotations
        ann = t.get("annotations") or {}
        if t.get("name") and not ann and "readOnlyHint" not in t:
            issues.append({"tool": name, "issue": "no annotations (readOnlyHint/destructiveHint missing)", "severity": "low"})
    return issues


SAFE_CALLS = [
    # Harmless read-only documentation lookups
    ("microsoft_docs_search", {"query": "Azure Functions HTTP trigger"}),
    ("microsoft_docs_fetch", {"url": "https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-http-webhook-trigger"}),
    ("microsoft_code_sample_search", {"query": "Azure Functions HTTP trigger C#"}),
]


def pick_safe_calls(tools):
    names = {t.get("name") for t in tools}
    # Prefer known Microsoft Learn tools; fall back to first 2-3 clearly read-only tools
    planned = [c for c in SAFE_CALLS if c[0] in names]
    if len(planned) >= 2:
        return planned[:3]
    # fallback: tools with readOnlyHint or search/get/list/fetch/read in name
    extra = []
    by = {t.get("name"): t for t in tools}
    for t in tools:
        n = t.get("name") or ""
        if WRITEISH.search(n):
            continue
        ann = t.get("annotations") or {}
        readonly = ann.get("readOnlyHint") is True or ann.get("destructiveHint") is False
        looks_read = re.search(r"(search|get|list|fetch|read|lookup|find|query|docs)", n, re.I)
        if not (readonly or looks_read):
            continue
        schema = t.get("inputSchema") or {}
        props = schema.get("properties") or {}
        required = schema.get("required") or []
        args = {}
        # only auto-fill simple string query-like fields with harmless text
        ok = True
        for r in required:
            p = props.get(r) or {}
            typ = p.get("type")
            if typ in (None, "string") and re.search(r"(query|q|search|url|term|name|id|text)", r, re.I):
                if "url" in r.lower():
                    args[r] = "https://learn.microsoft.com/en-us/azure/azure-functions/functions-overview"
                else:
                    args[r] = "Azure Functions HTTP trigger"
            else:
                ok = False
                break
        if ok and n not in {c[0] for c in planned}:
            extra.append((n, args))
        if len(planned) + len(extra) >= 3:
            break
    return (planned + extra)[:3]


def run_once(call_plan=None, do_lists=True):
    c = Client()
    timings = {}
    errors = []

    init = c.initialize()
    timings["initialize"] = init["http_ms"]
    init_res = result_of(init)
    if not init_res or "_rpc_error" in (init_res or {}):
        errors.append({"step": "initialize", "detail": init_res or init.get("error")})
        return c, timings, errors, {}, init_res

    n = c.notify("notifications/initialized")
    timings["notifications/initialized"] = n["http_ms"]

    lists = {}
    if do_lists:
        for method in ("tools/list", "resources/list", "prompts/list"):
            e = c.call(method, {})
            timings[method] = e["http_ms"]
            res = result_of(e)
            if e.get("error") and not res:
                errors.append({"step": method, "detail": e["error"], "http": e["http_status"]})
                lists[method] = None
            elif isinstance(res, dict) and res.get("_rpc_error"):
                errors.append({"step": method, "detail": res["_rpc_error"]})
                lists[method] = res
            else:
                lists[method] = res

    tools = (lists.get("tools/list") or {}).get("tools") or []
    plan = call_plan or pick_safe_calls(tools)
    call_results = []
    for name, args in plan:
        if WRITEISH.search(name):
            errors.append({"step": "tools/call", "detail": f"refused unsafe tool {name}"})
            continue
        e = c.call("tools/call", {"name": name, "arguments": args}, timeout=45)
        timings[f"tools/call:{name}"] = e["http_ms"]
        res = result_of(e)
        is_err = False
        if e.get("error") and not res:
            errors.append({"step": f"tools/call:{name}", "detail": e["error"]})
            is_err = True
        elif isinstance(res, dict) and (res.get("_rpc_error") or res.get("isError")):
            errors.append({"step": f"tools/call:{name}", "detail": res.get("_rpc_error") or res})
            is_err = True
        call_results.append({"name": name, "arguments": args, "entry_index": len(c.transcript) - 1, "error": is_err, "ms": e["http_ms"]})

    meta = {
        "init": init_res,
        "lists": lists,
        "call_plan": plan,
        "call_results": call_results,
        "session": "[redacted]" if c.session else None,
    }
    return c, timings, errors, meta, init_res


def p50(vals):
    if not vals:
        return None
    return statistics.median(vals)


def main():
    outdir = Path("/workspace/notes/offers/samples")
    outdir.mkdir(parents=True, exist_ok=True)

    # First full run captures lists + schema + one set of tool calls
    c1, t1, e1, meta1, init1 = run_once(do_lists=True)
    tools = (meta1.get("lists") or {}).get("tools/list") or {}
    tool_list = tools.get("tools") if isinstance(tools, dict) else []
    plan = meta1.get("call_plan") or pick_safe_calls(tool_list or [])

    # Additional runs for latency p50 (initialize + same tool calls)
    all_timings = {k: [v] for k, v in t1.items() if isinstance(v, (int, float))}
    extra_errors = []
    extra_transcripts = []
    RUNS = 5
    for i in range(2, RUNS + 1):
        c, t, e, meta, _ = run_once(call_plan=plan, do_lists=False)
        extra_transcripts.append(c.transcript)
        extra_errors.extend([{"run": i, **x} for x in e])
        for k, v in t.items():
            all_timings.setdefault(k, []).append(v)

    # Build summary
    schema = schema_issues(tool_list or [])
    resources = ((meta1.get("lists") or {}).get("resources/list") or {})
    prompts = ((meta1.get("lists") or {}).get("prompts/list") or {})

    def summarize_content(entry_idx):
        if entry_idx is None or entry_idx >= len(c1.transcript):
            return None
        res = result_of(c1.transcript[entry_idx])
        if not res:
            return None
        # truncate structured content
        blob = json.dumps(res, default=str)
        return {"keys": list(res.keys()) if isinstance(res, dict) else type(res).__name__, "chars": len(blob), "preview": blob[:1500], "isError": isinstance(res, dict) and res.get("isError")}

    payload = {
        "product": "AgentScout MCP Server Test Report — sample",
        "generated_at_pt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M %Z"),
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "timezone_note": "Box clock is America/Los_Angeles (Pacific). UTC timestamps are labeled.",
        "target": {
            "listed_name": "Microsoft Learn MCP",
            "listed_slug": "microsoft-learn-mcp",
            "listed_url": "https://agentscouthq.com/tools/microsoft-learn-mcp.html",
            "website": "https://learn.microsoft.com/en-us/",
            "github": "https://github.com/MicrosoftDocs/mcp",
            "endpoint": ENDPOINT,
            "transport": "streamable-http",
            "auth": "none (public)",
        },
        "client": {
            "name": "agentscout-mcp-test-sample",
            "version": "0.1.0",
            "protocolVersion_requested": PROTO,
            "user_agent": UA,
        },
        "runs": RUNS,
        "initialize_serverInfo": (init1 or {}).get("serverInfo") if isinstance(init1, dict) else None,
        "initialize_protocolVersion": (init1 or {}).get("protocolVersion") if isinstance(init1, dict) else None,
        "initialize_capabilities": (init1 or {}).get("capabilities") if isinstance(init1, dict) else None,
        "initialize_instructions_preview": ((init1 or {}).get("instructions") or "")[:1500] if isinstance(init1, dict) else None,
        "timings_ms": {k: {"samples": vs, "p50": p50(vs), "min": min(vs), "max": max(vs), "n": len(vs)} for k, vs in all_timings.items()},
        "errors": e1 + extra_errors,
        "tools": tool_list,
        "tool_count": len(tool_list or []),
        "resources": resources,
        "resource_count": len((resources or {}).get("resources") or []) if isinstance(resources, dict) else None,
        "prompts": prompts,
        "prompt_count": len((prompts or {}).get("prompts") or []) if isinstance(prompts, dict) else None,
        "schema_issues": schema,
        "call_plan": plan,
        "call_results_run1": [
            {**r, "response_summary": summarize_content(r.get("entry_index"))}
            for r in (meta1.get("call_results") or [])
        ],
        "transcript_run1": c1.transcript,
        "transcripts_extra_runs": extra_transcripts,
    }

    raw_path = outdir / "mcp-test-report-sample-2026-11-11.transcript.json"
    raw_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print("WROTE", raw_path)
    print("serverInfo", payload["initialize_serverInfo"])
    print("protocol", payload["initialize_protocolVersion"])
    print("tool_count", payload["tool_count"], "resource_count", payload["resource_count"], "prompt_count", payload["prompt_count"])
    print("schema_issues", len(schema))
    print("errors", json.dumps(payload["errors"], default=str)[:2000])
    print("timings p50:")
    for k, v in payload["timings_ms"].items():
        print(f"  {k}: p50={v['p50']:.0f}ms min={v['min']:.0f} max={v['max']:.0f} n={v['n']}")
    print("calls:")
    for r in payload["call_results_run1"]:
        print(" ", r["name"], "err=", r["error"], "ms=", r["ms"], "chars=", (r.get("response_summary") or {}).get("chars"))
    print("plan", plan)

if __name__ == "__main__":
    main()
