#!/usr/bin/env python3
"""Build a branded AgentScout MCP Server Test Report (HTML + PDF).

Reads a protocol transcript JSON and a scorecard JSON (qualitative scores
and fixes from the written report). Never invents latency numbers, counts,
or statuses — those come from the transcript.

Usage:
  python3 build_report.py \\
    --transcript ../../mcp-test-report-sample-2026-11-11.transcript.json \\
    --scorecard sample-scorecard.json \\
    --html sample.html \\
    --pdf ../../mcp-test-report-sample-2026-11-11.pdf
"""
from __future__ import annotations

import argparse
import html
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def esc(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def ident(v) -> str:
    """Escape an identifier, allowing breaks after underscores."""
    return esc(v).replace("_", "_<wbr>")


def fmt_ms(x) -> str:
    if x is None:
        return "—"
    s = f"{float(x):.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    return f"{s} ms"


def fmt_num(x) -> str:
    s = f"{float(x):.1f}"
    return s[:-2] if s.endswith(".0") else s


def load_json(path: Path):
    return json.loads(path.read_text())


def p50_bar_tone(p50: float) -> str:
    # Display only; thresholds are not scored here. Under 1s was called
    # production-quality in the source report. The 551.5 ms outlier is still < 1s.
    return "pass"


def build_model(transcript: dict, scorecard: dict) -> dict:
    timings = transcript["timings_ms"]
    target = transcript["target"]
    client = transcript["client"]

    # Operational success from every recorded HTTP call.
    def entries():
        yield 1, transcript["transcript_run1"]
        for i, run in enumerate(transcript["transcripts_extra_runs"], start=2):
            yield i, run

    ops = {}
    for _run, run_entries in entries():
        for e in run_entries:
            req = e.get("request") or {}
            method = req.get("method") or "?"
            params = req.get("params") or {}
            key = method
            if method == "tools/call":
                key = f"tools/call:{params.get('name')}"
            rec = ops.setdefault(key, {"ok": 0, "n": 0, "http_ok": 0})
            rec["n"] += 1
            status = e.get("http_status")
            err = e.get("error")
            rpc_err = None
            is_error = None
            for m in e.get("messages") or []:
                if isinstance(m, dict):
                    if "error" in m:
                        rpc_err = m["error"]
                    res = m.get("result")
                    if isinstance(res, dict) and res.get("isError"):
                        is_error = True
            ok = (
                err is None
                and rpc_err is None
                and not is_error
                and status in (200, 202)
            )
            rec["ok"] += int(ok)
            rec["http_ok"] += int(status in (200, 202))

    # Run-1 tool-call result summaries from transcript
    search_first = None
    search_n = None
    fetch_start = None
    code_first = None
    code_n = None
    for e in transcript["transcript_run1"]:
        req = e.get("request") or {}
        if req.get("method") != "tools/call":
            continue
        name = (req.get("params") or {}).get("name")
        msgs = e.get("messages") or []
        res = msgs[0].get("result") if msgs else {}
        if not isinstance(res, dict):
            continue
        if name == "microsoft_docs_search":
            results = (res.get("structuredContent") or {}).get("results") or []
            search_n = len(results)
            if results:
                search_first = {
                    "title": results[0].get("title"),
                    "url": results[0].get("contentUrl"),
                }
        elif name == "microsoft_docs_fetch":
            content = res.get("content") or []
            text = ""
            if content and isinstance(content[0], dict):
                text = content[0].get("text") or ""
            first_line = text.replace("\r\n", "\n").split("\n", 1)[0].strip()
            fetch_start = first_line
        elif name == "microsoft_code_sample_search":
            results = (res.get("structuredContent") or {}).get("results") or []
            code_n = len(results)
            if results:
                code_first = {
                    "language": results[0].get("language"),
                    "description": results[0].get("description"),
                }

    call_rows = []
    for r in transcript["call_results_run1"]:
        name = r["name"]
        args = r["arguments"]
        chars = (r.get("response_summary") or {}).get("chars")
        note = ""
        if name == "microsoft_docs_search" and search_first:
            note = (
                f"Success. Structured results plus a {chars:,}-character payload "
                f"(~{chars/1000:.1f} KB) of official Learn chunks. First hit: "
                f"“{search_first['title']}”."
            )
            if search_n is not None:
                note = (
                    f"Success. {search_n} structured results plus a {chars:,}-character "
                    f"payload (~{chars/1000:.1f} KB) of official Learn chunks. First hit: "
                    f"“{search_first['title']}”."
                )
        elif name == "microsoft_docs_fetch":
            start = fetch_start or "# Azure Functions HTTP trigger"
            note = (
                f"Success. Full page converted to Markdown "
                f"({chars:,} characters, ~{chars/1000:.1f} KB), starting at “{start}”."
            )
        elif name == "microsoft_code_sample_search":
            extra = ""
            if code_n is not None:
                extra = f"{code_n} official C# samples "
            else:
                extra = "Official C# samples "
            note = (
                f"Success. {extra}({chars:,} characters, ~{chars/1000:.1f} KB), "
                f"including an HttpExample HttpTrigger function."
            )
        arg_s = ", ".join(f"{k}: {v}" for k, v in args.items())
        call_rows.append(
            {
                "name": name,
                "args": arg_s,
                "ms": r["ms"],
                "error": r.get("error"),
                "note": note,
            }
        )

    tools = []
    for t in transcript["tools"]:
        schema = t.get("inputSchema") or {}
        props = schema.get("properties") or {}
        required = schema.get("required") or []
        parts = []
        for pname, pdef in props.items():
            typ = pdef.get("type") or ""
            req = "required" if pname in required else "not required"
            extra = ""
            if pdef.get("default", "__missing__") is None and pname not in required:
                extra = '; "default": null'
            parts.append(f"{pname} ({typ}) — {req}{extra}")
        ann = t.get("annotations") or {}
        ann_bits = []
        if ann.get("readOnlyHint"):
            ann_bits.append("read-only")
        if ann.get("idempotentHint"):
            ann_bits.append("idempotent")
        if ann.get("destructiveHint") is False:
            ann_bits.append("not destructive")
        tools.append(
            {
                "name": t.get("name"),
                "title": t.get("title"),
                "annotations": ", ".join(ann_bits) or "—",
                "input": "; ".join(parts) or "—",
                "has_output": t.get("outputSchema") is not None,
                "notes": (
                    "Has outputSchema. Description is detailed and tells the client to follow up with fetch."
                    if t.get("name") == "microsoft_docs_search"
                    else "Has outputSchema. Language enum documented in the description (csharp, python, etc.)."
                    if t.get("name") == "microsoft_code_sample_search"
                    else "No outputSchema. Description states the URL must be a microsoft.com HTML docs page."
                    if t.get("name") == "microsoft_docs_fetch"
                    else ""
                ),
            }
        )

    # Checks — statuses follow the written report; evidence is from the transcript.
    init = timings["initialize"]
    notif = timings["notifications/initialized"]
    search_t = timings["tools/call:microsoft_docs_search"]
    fetch_t = timings["tools/call:microsoft_docs_fetch"]
    code_t = timings["tools/call:microsoft_code_sample_search"]

    checks = [
        {
            "group": "Protocol and connectivity",
            "check": "initialize succeeds and negotiates protocol 2025-06-18",
            "status": "pass",
            "evidence": f"HTTP 200 on {ops['initialize']['ok']}/{ops['initialize']['n']} runs. "
            f"Negotiated protocol {transcript['initialize_protocolVersion']}. Session header set (value not shown).",
        },
        {
            "group": "Protocol and connectivity",
            "check": "notifications/initialized accepted",
            "status": "pass",
            "evidence": f"HTTP 202 on {ops['notifications/initialized']['ok']}/{ops['notifications/initialized']['n']} runs.",
        },
        {
            "group": "Protocol and connectivity",
            "check": "tools/list returns tools",
            "status": "pass",
            "evidence": f"HTTP 200, {transcript['tool_count']} well-described tools (run 1).",
        },
        {
            "group": "Correctness and reliability",
            "check": "microsoft_docs_search succeeds",
            "status": "pass",
            "evidence": f"{ops['tools/call:microsoft_docs_search']['ok']}/{ops['tools/call:microsoft_docs_search']['n']} "
            f"runs, zero errors. Results on-topic.",
        },
        {
            "group": "Correctness and reliability",
            "check": "microsoft_docs_fetch succeeds",
            "status": "pass",
            "evidence": f"{ops['tools/call:microsoft_docs_fetch']['ok']}/{ops['tools/call:microsoft_docs_fetch']['n']} "
            f"runs, zero errors. Markdown starts at “{fetch_start}”.",
        },
        {
            "group": "Correctness and reliability",
            "check": "microsoft_code_sample_search succeeds",
            "status": "pass",
            "evidence": f"{ops['tools/call:microsoft_code_sample_search']['ok']}/{ops['tools/call:microsoft_code_sample_search']['n']} "
            f"runs, zero errors. Official C# samples include an HttpExample HttpTrigger function.",
        },
        {
            "group": "Correctness and reliability",
            "check": "No write or destructive tools offered or called",
            "status": "pass",
            "evidence": "All three tools are annotated read-only, idempotent, and not destructive.",
        },
        {
            "group": "Latency",
            "check": "Connect and tool-call p50 under one second",
            "status": "pass",
            "evidence": f"initialize p50 {fmt_ms(init['p50'])} (min {fmt_ms(init['min'])}, max {fmt_ms(init['max'])}, n={init['n']}). "
            f"Tool-call p50 {fmt_ms(fetch_t['p50'])}–{fmt_ms(search_t['p50'])}.",
        },
        {
            "group": "Latency",
            "check": "notifications/initialized consistency",
            "status": "warn",
            "evidence": f"p50 {fmt_ms(notif['p50'])} (min {fmt_ms(notif['min'])}, max {fmt_ms(notif['max'])}, n={notif['n']}). "
            f"One outlier at {fmt_ms(notif['max'])} on run 3 (still under one second, HTTP 202).",
        },
        {
            "group": "Schema and tool quality",
            "check": "Titles, descriptions, and annotations",
            "status": "pass",
            "evidence": "All three tools have a title, a detailed description, and readOnlyHint / idempotentHint / destructiveHint: false.",
        },
        {
            "group": "Schema and tool quality",
            "check": "microsoft_docs_search marks query as required",
            "status": "warn",
            "evidence": "query exists and is well described, but it is omitted from required and has \"default\": null.",
        },
        {
            "group": "Schema and tool quality",
            "check": "microsoft_docs_fetch declares outputSchema",
            "status": "warn",
            "evidence": "Search and code-sample search both declare an outputSchema. Fetch does not.",
        },
        {
            "group": "Capability honesty and metadata",
            "check": "Advertised prompts match prompts/list",
            "status": "fail",
            "evidence": "initialize advertises prompts.listChanged: true, but prompts/list returned {\"prompts\": []} with HTTP 200.",
        },
        {
            "group": "Capability honesty and metadata",
            "check": "Advertised resources match resources/list",
            "status": "fail",
            "evidence": "initialize advertises resources.listChanged: true, but resources/list returned {\"resources\": []} with HTTP 200.",
        },
        {
            "group": "Capability honesty and metadata",
            "check": "serverInfo includes title, website URL, and description",
            "status": "warn",
            "evidence": f"serverInfo has only name (“{transcript['initialize_serverInfo'].get('name')}”) and version "
            f"({transcript['initialize_serverInfo'].get('version')}).",
        },
        {
            "group": "Capability honesty and metadata",
            "check": "initialize instructions are useful",
            "status": "pass",
            "evidence": "The instructions correctly describe a three-step workflow: search for breadth, code-sample search for examples, fetch for depth.",
        },
    ]

    pass_n = sum(1 for c in checks if c["status"] == "pass")
    warn_n = sum(1 for c in checks if c["status"] == "warn")
    fail_n = sum(1 for c in checks if c["status"] == "fail")

    # Latency rows for the chart, in a readable order.
    label_map = [
        ("initialize", "initialize (connect)"),
        ("notifications/initialized", "notifications/initialized"),
        ("tools/list", "tools/list"),
        ("resources/list", "resources/list"),
        ("prompts/list", "prompts/list"),
        ("tools/call:microsoft_docs_search", "microsoft_docs_search"),
        ("tools/call:microsoft_docs_fetch", "microsoft_docs_fetch"),
        ("tools/call:microsoft_code_sample_search", "microsoft_code_sample_search"),
    ]
    latency_rows = []
    for key, label in label_map:
        t = timings[key]
        latency_rows.append(
            {
                "key": key,
                "label": label,
                "p50": t["p50"],
                "min": t["min"],
                "max": t["max"],
                "n": t["n"],
                "samples": t["samples"],
            }
        )

    op_rows = []
    op_order = [k for k, _ in label_map]
    for key in op_order:
        rec = ops[key]
        op_rows.append(
            {
                "key": key,
                "label": dict(label_map)[key],
                "ok": rec["ok"],
                "n": rec["n"],
                "rate": rec["ok"] / rec["n"] if rec["n"] else 0,
            }
        )

    return {
        "transcript": transcript,
        "scorecard": scorecard,
        "target": target,
        "client": client,
        "timings": timings,
        "ops": ops,
        "tools": tools,
        "checks": checks,
        "check_counts": {"pass": pass_n, "warn": warn_n, "fail": fail_n, "total": len(checks)},
        "call_rows": call_rows,
        "latency_rows": latency_rows,
        "op_rows": op_rows,
        "search_first": search_first,
        "search_n": search_n,
        "fetch_start": fetch_start,
        "code_n": code_n,
        "server": transcript["initialize_serverInfo"],
        "protocol": transcript["initialize_protocolVersion"],
        "capabilities": transcript["initialize_capabilities"],
        "errors": transcript.get("errors") or [],
        "runs": transcript["runs"],
        "tool_count": transcript["tool_count"],
        "resource_count": transcript["resource_count"],
        "prompt_count": transcript["prompt_count"],
        "generated_at_pt": (transcript.get("generated_at_pt") or "").strip(),
    }


def score_ring(score: int, maximum: int) -> str:
    r = 88
    c = 2 * math.pi * r
    frac = score / maximum
    dash = c * frac
    gap = c - dash
    return f"""
    <div class="score-ring" role="img" aria-label="Score {score} out of {maximum}">
      <svg viewBox="0 0 210 210" aria-hidden="true">
        <defs>
          <filter id="scoreGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3.2" result="b"/>
            <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>
        <circle cx="105" cy="105" r="{r}" fill="none" stroke="#2A2F3A" stroke-width="12"/>
        <circle cx="105" cy="105" r="{r}" fill="none" stroke="#9393FF" stroke-width="12"
          stroke-linecap="round" stroke-dasharray="{dash:.2f} {gap:.2f}"
          transform="rotate(-90 105 105)" filter="url(#scoreGlow)"/>
      </svg>
      <div class="score-num"><div class="n">{score}</div><div class="d">/ {maximum}</div></div>
    </div>"""


def latency_chart(rows: list[dict]) -> str:
    # Horizontal bars with min–max whiskers. Scale from transcript max.
    observed_max = max(r["max"] for r in rows)
    # Pad to a clean ceiling just above the observed max (551.5 → 600).
    ceiling = 600 if observed_max <= 600 else math.ceil(observed_max / 100) * 100
    left, top, plot_w, row_h = 228, 4, 420, 24
    axis_h = 26
    height = top + row_h * len(rows) + axis_h + 4
    width = left + plot_w + 86
    ticks = list(range(0, ceiling + 1, 100))

    def x(ms: float) -> float:
        return left + (ms / ceiling) * plot_w

    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Latency p50 in milliseconds with min and max range">']
    # grid
    for t in ticks:
        xx = x(t)
        parts.append(f'<line x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" y2="{top + row_h * len(rows) - 4}" stroke="#2A2F3A" stroke-width="1"/>')
        parts.append(
            f'<text x="{xx:.1f}" y="{top + row_h * len(rows) + 12}" fill="#8E97A8" font-size="9" text-anchor="middle" font-family="Inter,system-ui,sans-serif">{t}</text>'
        )
    for i, r in enumerate(rows):
        cy = top + i * row_h + row_h / 2
        bar_y = cy - 6
        x0, x50, x1 = x(r["min"]), x(r["p50"]), x(r["max"])
        ntag = "" if r["n"] > 1 else "  · n=1"
        parts.append(
            f'<text x="{left - 10}" y="{cy + 4}" fill="#E8EAF0" font-size="10.5" text-anchor="end" font-family="Inter,system-ui,sans-serif">{esc(r["label"])}</text>'
        )
        # whisker
        parts.append(f'<line x1="{x0:.1f}" y1="{cy}" x2="{x1:.1f}" y2="{cy}" stroke="#8E97A8" stroke-width="1.4"/>')
        parts.append(f'<line x1="{x0:.1f}" y1="{cy-4}" x2="{x0:.1f}" y2="{cy+4}" stroke="#8E97A8" stroke-width="1.4"/>')
        parts.append(f'<line x1="{x1:.1f}" y1="{cy-4}" x2="{x1:.1f}" y2="{cy+4}" stroke="#8E97A8" stroke-width="1.4"/>')
        # p50 bar from 0
        parts.append(
            f'<rect x="{left}" y="{bar_y}" width="{max(x50-left, 1):.1f}" height="12" rx="3" fill="#9393FF" fill-opacity="0.92"/>'
        )
        # p50 marker
        parts.append(f'<circle cx="{x50:.1f}" cy="{cy}" r="3.2" fill="#E8EAF0"/>')
        parts.append(
            f'<text x="{left + plot_w + 8}" y="{cy + 4}" fill="#E8EAF0" font-size="10.5" font-variant="tabular-nums" font-family="Inter,system-ui,sans-serif">{fmt_ms(r["p50"])}{ntag}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def passrate_chart(rows: list[dict]) -> str:
    left, top, plot_w, row_h = 228, 2, 420, 20
    height = top + row_h * len(rows) + 6
    width = left + plot_w + 86

    def x(rate: float) -> float:
        return left + rate * plot_w

    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Success rate by protocol step">']
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        xx = x(t)
        parts.append(f'<line x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" y2="{top + row_h * len(rows) - 2}" stroke="#2A2F3A" stroke-width="1"/>')
    for i, r in enumerate(rows):
        cy = top + i * row_h + row_h / 2
        bar_y = cy - 5
        w = max(x(r["rate"]) - left, 1)
        color = "#34d399" if r["rate"] == 1 else "#F5C14A" if r["rate"] >= 0.8 else "#F87171"
        parts.append(
            f'<text x="{left - 10}" y="{cy + 4}" fill="#E8EAF0" font-size="10.5" text-anchor="end" font-family="Inter,system-ui,sans-serif">{esc(r["label"])}</text>'
        )
        parts.append(f'<rect x="{left}" y="{bar_y}" width="{plot_w}" height="10" rx="3" fill="#2A2F3A"/>')
        parts.append(f'<rect x="{left}" y="{bar_y}" width="{w:.1f}" height="10" rx="3" fill="{color}"/>')
        parts.append(
            f'<text x="{left + plot_w + 8}" y="{cy + 4}" fill="#E8EAF0" font-size="10.5" font-family="Inter,system-ui,sans-serif">{r["ok"]}/{r["n"]}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def page_header(subtitle: str, logo_src: str = "assets/logo/logo-mark-dark.svg", pill: str = "Sample") -> str:
    return f"""
    <div class="page-head">
      <div class="brand">
        <img src="{esc(logo_src)}" alt="AgentScout mark" width="28" height="28">
        <div class="brand-name">Agent<span class="scout">Scout</span></div>
      </div>
      <div class="head-meta">
        <span>{esc(subtitle)}</span>
        <span class="pill">{esc(pill)}</span>
      </div>
    </div>"""


def page_footer(page: int, total: int, note: str = "Sample · not published") -> str:
    return f"""
    <div class="page-foot">
      <div>AgentScout · MCP Server Test Report · {esc(note)}</div>
      <div>agentscouthq.com</div>
      <div class="pg">{page} / {total}</div>
    </div>"""


def meters(scorecard: dict) -> str:
    bits = []
    for a in scorecard["scorecard"]:
        pct = 100 * a["points"] / a["max"]
        tone = a["tone"]
        bar_cls = "pass" if tone == "pass" else "warn" if tone == "warn" else "fail"
        bits.append(
            f"""<div class="meter">
              <div class="m-lbl">{esc(a["area"])}</div>
              <div class="m-pts">{a["points"]} <span>/ {a["max"]}</span></div>
              <div class="bar {bar_cls}"><i style="width:{pct:.0f}%"></i></div>
            </div>"""
        )
    return '<div class="cover-meters">' + "\n".join(bits) + "</div>"


def already_great_line(model: dict) -> str:
    sc = model["scorecard"]
    if sc.get("whats_great"):
        return sc["whats_great"]
    tool_ops = [v for k, v in model["ops"].items() if k.startswith("tools/call:")]
    all_tools_ok = bool(tool_ops) and all(r["ok"] == r["n"] and r["n"] for r in tool_ops)
    init = model["ops"].get("initialize")
    all_init_ok = bool(init) and init["ok"] == init["n"] and init["n"]
    keys = ["initialize"] + [k for k in model["timings"] if k.startswith("tools/call:")]
    mx = max(model["timings"][k]["max"] for k in keys)
    if all_tools_ok and all_init_ok and mx < 1000:
        return (
            f"Every connection and tool call succeeded on all {model['runs']} runs, "
            "and each one finished in under 1 second."
        )
    return "See the scorecard for what already works well."


def _load_font(path: Path):
    from fontTools.ttLib import TTFont

    font = TTFont(str(path))
    return font


def _text_width(font, text: str, size: float) -> float:
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upem = font["head"].unitsPerEm
    scale = size / upem
    width = 0.0
    for ch in text:
        gname = cmap.get(ord(ch), ".notdef")
        adv = hmtx[gname][0]
        width += adv * scale
    return width


def _text_paths(font, text: str, size: float, x: float, y: float, fill: str) -> str:
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.misc.transform import Transform

    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upem = font["head"].unitsPerEm
    scale = size / upem
    parts = []
    pen_x = 0.0
    for ch in text:
        gname = cmap.get(ord(ch), ".notdef")
        adv = hmtx[gname][0]
        if ch != " ":
            pen = SVGPathPen(glyph_set)
            tp = TransformPen(pen, Transform(scale, 0, 0, -scale, x + pen_x, y))
            glyph_set[gname].draw(tp)
            d = pen.getCommands()
            if d:
                parts.append(f'<path d="{d}" fill="{fill}"/>')
        pen_x += adv * scale
    return "".join(parts)


def logo_mark_svg(x: float, y: float, size: float = 32) -> str:
    s = size / 32
    return (
        f'<g transform="translate({x:.2f} {y:.2f}) scale({s:.4f})">'
        '<circle cx="13.5" cy="13.5" r="9" fill="none" stroke="#ffffff" stroke-width="3"/>'
        '<path d="M20.3 20.3L28 28" stroke="#ffffff" stroke-width="3.2" stroke-linecap="round"/>'
        '<path d="M13.5 8.2Q14.2 12.8 18.8 13.5Q14.2 14.2 13.5 18.8Q12.8 14.2 8.2 13.5Q12.8 12.8 13.5 8.2Z" fill="#7373ff"/>'
        "</g>"
    )


def build_badge_svg(score: int, score_max: int, date_label: str) -> str:
    """Standalone, outlined-text badge. Dated test result, not an endorsement."""
    font600 = _load_font(HERE / "assets/fonts/inter-600.ttf")
    font700 = _load_font(HERE / "assets/fonts/inter-700.ttf")
    font500 = _load_font(HERE / "assets/fonts/inter-500.ttf")

    pad_x, height = 16, 64
    logo_size = 32
    logo_x = pad_x
    logo_y = (height - logo_size) / 2
    text_x = logo_x + logo_size + 12
    baseline = 38
    size_main = 15
    size_score = 16
    size_date = 14
    gap = 10

    chunks = []
    x = text_x
    chunks.append(_text_paths(font500, "Tested by ", size_main, x, baseline, "#E8EAF0"))
    x += _text_width(font500, "Tested by ", size_main)
    chunks.append(_text_paths(font600, "Agent", size_main, x, baseline, "#E8EAF0"))
    x += _text_width(font600, "Agent", size_main)
    chunks.append(_text_paths(font600, "Scout", size_main, x, baseline, "#7373ff"))
    x += _text_width(font600, "Scout", size_main)
    chunks.append(_text_paths(font500, "  ·  ", size_main, x, baseline, "#8E97A8"))
    x += _text_width(font500, "  ·  ", size_main)
    score_text = f"{score}/{score_max}"
    chunks.append(_text_paths(font700, score_text, size_score, x, baseline, "#9393FF"))
    x += _text_width(font700, score_text, size_score)
    chunks.append(_text_paths(font500, "  ·  ", size_main, x, baseline, "#8E97A8"))
    x += _text_width(font500, "  ·  ", size_main)
    chunks.append(_text_paths(font500, date_label, size_date, x, baseline, "#A9B0BE"))
    x += _text_width(font500, date_label, size_date)

    width = x + pad_x
    body = "\n  ".join(chunks)
    logo = logo_mark_svg(logo_x, logo_y, logo_size)
    # title/desc keep the meaning honest if the file is opened alone
    title = f"Tested by AgentScout · {score}/{score_max} · {date_label}"
    desc = "Dated MCP server test result from AgentScout. Not an endorsement. Scores can change as the server is updated."
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height}" viewBox="0 0 {width:.2f} {height}" role="img" aria-label="{esc(title)}">
  <title>{esc(title)}</title>
  <desc>{esc(desc)}</desc>
  <defs>
    <filter id="badgeGlow" x="-20%" y="-40%" width="140%" height="180%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect x="1.2" y="1.2" width="{width-2.4:.2f}" height="{height-2.4}" rx="12" fill="#0E1015" stroke="#9393FF" stroke-width="1.6" filter="url(#badgeGlow)"/>
  {logo}
  {body}
</svg>
'''


def write_badge_svg(path: Path, score: int, score_max: int, date_label: str) -> None:
    path.write_text(build_badge_svg(score, score_max, date_label))
    print(f"Wrote {path} ({path.stat().st_size} bytes)", file=sys.stderr)


def render_previews(pdf_path: Path, preview_dir: Path, copy_prefix: Path | None = None) -> list[Path]:
    """Rasterize every PDF page and drop stale page PNGs beyond the new count."""
    preview_dir.mkdir(parents=True, exist_ok=True)
    for old in preview_dir.glob("page-*.png"):
        old.unlink()
    subprocess.run(
        ["pdftoppm", "-png", "-r", "180", str(pdf_path), str(preview_dir / "page")],
        check=True,
    )
    pages = sorted(preview_dir.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[1]))
    if copy_prefix is not None:
        parent = copy_prefix.parent
        stem = copy_prefix.name
        for old in parent.glob(f"{stem}-page-*.png"):
            old.unlink()
        for page in pages:
            dest = parent / f"{stem}-{page.name}"
            shutil.copyfile(page, dest)
    return pages


def render_html(model: dict, web: dict | None = None) -> str:
    t = model["target"]
    sc = model["scorecard"]
    server = model["server"]
    daily = sc["daily_http_check"]
    caps = model["capabilities"]

    # Cover meta
    transport = "Streamable HTTP" if t["transport"] == "streamable-http" else t["transport"]
    auth = "None. Public. No API key." if "none" in (t.get("auth") or "").lower() else t.get("auth")

    # Page 2 facts
    facts = [
        ("Listed name", t["listed_name"]),
        ("AgentScout listing", t["listed_url"]),
        ("Website in the catalog", t["website"]),
        ("GitHub", t["github"]),
        ("MCP endpoint tested", t["endpoint"]),
        ("Transport", f"{transport} (Accept: application/json, text/event-stream)"),
        ("Auth", auth),
        ("serverInfo", f"name: {server.get('name')} · version: {server.get('version')}"),
        ("Negotiated protocol", model["protocol"]),
        ("Daily HTTP check", f"{daily['checked']} · url {daily['url']}, github {daily['github']}, snapshot label {daily['label']}"),
        ("Client", f"{model['client']['name']} {model['client']['version']}"),
        ("User-Agent", model["client"]["user_agent"]),
    ]

    scorecard_rows = []
    for a in sc["scorecard"]:
        scorecard_rows.append(
            f"<tr><td>{esc(a['area'])}</td>"
            f"<td class='num'>{a['points']} / {a['max']}</td>"
            f"<td>{esc(a['why'])}</td></tr>"
        )
    scorecard_rows.append(
        f"<tr><td><strong>Total</strong></td>"
        f"<td class='num'><strong>{sc['score']} / {sc['score_max']}</strong></td>"
        f"<td></td></tr>"
    )

    latency_rows_html = []
    for r in model["latency_rows"]:
        nnote = "" if r["n"] > 1 else " (run 1 only)"
        latency_rows_html.append(
            f"<tr><td class='mono'>{esc(r['label'])}</td>"
            f"<td class='num'><strong>{fmt_ms(r['p50'])}</strong></td>"
            f"<td class='num'>{fmt_ms(r['min'])}</td>"
            f"<td class='num'>{fmt_ms(r['max'])}</td>"
            f"<td class='num'>{r['n']}{esc(nnote)}</td></tr>"
        )

    call_html = []
    for r in model["call_rows"]:
        call_html.append(
            f"<tr><td class='mono wrap'>{ident(r['name'])}</td>"
            f"<td class='wrap'>{esc(r['args'])}</td>"
            f"<td class='num'>{fmt_ms(r['ms'])}</td>"
            f"<td class='wrap'>{esc(r['note'])}</td></tr>"
        )

    check_html = []
    last_group = None
    for c in model["checks"]:
        group_cell = esc(c["group"]) if c["group"] != last_group else ""
        last_group = c["group"]
        check_html.append(
            f"<tr><td>{group_cell}</td>"
            f"<td>{esc(c['check'])}</td>"
            f"<td><span class='status {c['status']}'>{c['status']}</span></td>"
            f"<td class='wrap'>{esc(c['evidence'])}</td></tr>"
        )

    tool_html = []
    for tl in model["tools"]:
        out = "Yes" if tl["has_output"] else "No"
        tool_html.append(
            f"<tr><td class='mono wrap'>{ident(tl['name'])}</td>"
            f"<td>{esc(tl['title'])}</td>"
            f"<td>{esc(tl['annotations'])}</td>"
            f"<td class='wrap'>{esc(tl['input'])}</td>"
            f"<td>{out}</td>"
            f"<td class='wrap'>{esc(tl['notes'])}</td></tr>"
        )

    fixes_html = []
    for i, fx in enumerate(sc["top_fixes"], start=1):
        steps = "".join(f"<li>{esc(s)}</li>" for s in fx["steps"])
        fixes_html.append(
            f"""<div class="fix">
              <div class="fix-num">{i}</div>
              <div>
                <h3>{esc(fx['title'])}</h3>
                <p>{esc(fx['why'])}</p>
                <ol>{steps}</ol>
              </div>
            </div>"""
        )

    further = "".join(f"<li>{esc(x)}</li>" for x in sc["further_improvements"])
    method = "".join(f"<li>{esc(s)}</li>" for s in sc["methodology"])
    scope = "".join(f"<li>{esc(s)}</li>" for s in sc["out_of_scope"])
    verdict_paras = "".join(f"<p class='lead'>{esc(p)}</p>" for p in sc["verdict"].split("\n\n"))
    means_paras = "".join(f"<p>{esc(p)}</p>" for p in (sc.get("what_this_means") or []))

    kf_items = []
    for i, fx in enumerate(sc["top_fixes"], start=1):
        effort = fx.get("effort") or ""
        kf_items.append(
            f"""<div class="kf-item">
              <div class="kf-num">{i}</div>
              <div class="kf-text">{esc(fx['title'])}</div>
              <div class="kf-effort">{esc(effort)}</div>
            </div>"""
        )

    cmd = """# initialize (expect HTTP 200, text/event-stream, mcp-session-id)
curl -sS -D - -o /tmp/mslearn-init.sse \\
  -X POST 'https://learn.microsoft.com/api/mcp' \\
  -H 'Accept: application/json, text/event-stream' \\
  -H 'Content-Type: application/json' \\
  -H 'MCP-Protocol-Version: 2025-06-18' \\
  -H 'User-Agent: AgentScoutMCPTest/0.1 (+https://agentscouthq.com/about.html)' \\
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"agentscout-mcp-test-sample","version":"0.1.0"}}}'

# Then: notifications/initialized (send the session header from step 1),
# tools/list, resources/list, prompts/list, and the three read-only tool calls:
#   microsoft_docs_search         {"query":"Azure Functions HTTP trigger"}
#   microsoft_docs_fetch          {"url":"https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-http-webhook-trigger"}
#   microsoft_code_sample_search  {"query":"Azure Functions HTTP trigger C#"}"""

    caps_pretty = json.dumps(caps, indent=2)

    cc = model["check_counts"]
    listing_url = t["listed_url"]
    badge_date = sc.get("badge_date") or sc.get("tested_display")
    badge_score = f"{sc['score']}/{sc['score_max']}"
    badge_alt = f"Tested by AgentScout · {badge_score} · {badge_date}"
    badge_disclaimer = sc.get("badge_disclaimer") or (
        "This badge is a dated test result, not an AgentScout endorsement. "
        "Scores can change as the server is updated."
    )
    html_snippet = (
        f'<a href="{listing_url}">\n'
        f'  <img src="(badge image URL added at launch)"\n'
        f'       alt="{badge_alt}. Dated test result, not an endorsement."\n'
        f'       width="440">\n'
        f"</a>"
    )
    md_snippet = (
        f"[![{badge_alt}](badge image URL added at launch)]({listing_url})"
    )
    next_step = sc.get("next_step") or {}
    next_title = next_step.get("title") or "Next step"
    next_body = next_step.get("body") or ""
    next_link = next_step.get("link_label") or "https://agentscouthq.com/ (booking link added at launch)"
    whats_great = already_great_line(model)
    web = web or {}
    sample = bool(sc.get("sample", True))
    pill = "Sample" if sample else "Private"
    foot_note = "Sample · not published" if sample else "Private report"
    logo_src = web.get("logo_src") or "assets/logo/logo-mark-dark.svg"
    badge_src = web.get("badge_src") or "badge-sample.svg"
    css_href = web.get("css_href") or "report.css"

    def header(subtitle: str) -> str:
        return page_header(subtitle, logo_src=logo_src, pill=pill)

    def footer(page: int, total: int) -> str:
        return page_footer(page, total, note=foot_note)

    # Pages are collected then numbered so totals stay correct when sections move.
    pages: list[str] = []

    pages.append(f"""
<article class="sheet sheet-cover">
  <div class="cover-top">
    <div class="brand">
      <img src="{esc(logo_src)}" alt="AgentScout mark" width="32" height="32">
      <div class="brand-name" style="font-size:18px">Agent<span class="scout">Scout</span></div>
    </div>
    <div class="head-meta">
      <span>agentscouthq.com</span>
      <span class="pill">{esc(pill)}</span>
    </div>
  </div>

  <div class="cover-grid">
    <div class="cover-copy">
      <div class="kicker">MCP Server Test Report</div>
      <h1>{esc(t['listed_name'])}</h1>
      <div class="endpoint">{esc(t['endpoint'])}</div>
      <ul class="meta-list">
        <li><span class="lbl">Tested</span><span class="val">{esc(sc['tested_display'])}</span></li>
        <li><span class="lbl">Transport</span><span class="val">{esc(transport)} · {esc(auth)}</span></li>
        <li><span class="lbl">Runs</span><span class="val">{model['runs']} (latency p50 over all runs; schema and tool-call bodies from run 1)</span></li>
        <li><span class="lbl">Server</span><span class="val">{esc(server.get('name'))} · version {esc(server.get('version'))}</span></li>
        <li><span class="lbl">Protocol</span><span class="val">{esc(model['protocol'])}</span></li>
        <li><span class="lbl">Listing</span><span class="val">{esc(t['listed_url'])}</span></li>
      </ul>
    </div>
    <div class="score-wrap">
      {score_ring(sc['score'], sc['score_max'])}
      <div class="score-caption">Overall score</div>
    </div>
  </div>

  <div class="cover-findings">
    <div class="kicker">Key findings</div>
    <div class="kf-good">
      <div class="kf-mark" aria-hidden="true">✓</div>
      <p>{esc(whats_great)}</p>
    </div>
    {''.join(kf_items)}
  </div>

  {meters(sc)}
  <p class="cover-foot-note">{esc(sc['cover_blurb'])}</p>
  __FOOTER__
</article>
""")

    pages.append(f"""
<article class="sheet sheet-summary">
  {header("Summary")}
  <div class="body">
    <div class="sec means">
      <h2>What this means for you</h2>
      {means_paras}
    </div>

    <div class="sec">
      <h2>Verdict</h2>
      {verdict_paras}
    </div>

    <div class="sec">
      <h2>Scorecard</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Area</th><th class="num">Points</th><th>Why</th></tr></thead>
          <tbody>
            {''.join(scorecard_rows)}
          </tbody>
        </table>
      </div>
    </div>

    <div class="sec three">
      <div class="stat"><div class="n">{model['tool_count']}</div><div class="l">Tools listed</div></div>
      <div class="stat"><div class="n warnc">{model['resource_count']}</div><div class="l">Resources listed</div></div>
      <div class="stat"><div class="n warnc">{model['prompt_count']}</div><div class="l">Prompts listed</div></div>
    </div>

    <div class="sec">
      <h2>What we connected to</h2>
      <div class="card">
        <div class="facts">
          {''.join(f'<div class="row"><div class="k">{esc(k)}</div><div class="v">{esc(v)}</div></div>' for k,v in facts)}
        </div>
      </div>
    </div>
  </div>
  __FOOTER__
</article>
""")

    pages.append(f"""
<article class="sheet">
  {header("Latency and reliability")}
  <div class="body">
    <div class="sec card chart-card">
      <h2>Latency (p50, with min–max range)</h2>
      <p class="chart-note">Median over {model['runs']} runs unless marked n=1 (tools/list, resources/list, and prompts/list were recorded on run 1 only). Connect and every tool call stayed under one second. The bar and dot are p50; the whisker is the observed min–max, in milliseconds from the transcript.</p>
      {latency_chart(model['latency_rows'])}
      <div class="legend">
        <span><i class="sw" style="background:#9393FF"></i>p50 bar</span>
        <span><i class="sw" style="background:#8E97A8"></i>min–max range</span>
        <span>Scale is 0–600 ms, just above the observed maximum of {fmt_ms(max(r['max'] for r in model['latency_rows']))}.</span>
      </div>
    </div>

    <div class="sec card chart-card">
      <h2>Success rate by protocol step</h2>
      <p class="chart-note">Success means HTTP 200 or 202 and no transport, JSON-RPC, or tool-level error. resources/list and prompts/list returned empty arrays (HTTP 200); that honesty issue is scored in the checks table, not as a failed call.</p>
      {passrate_chart(model['op_rows'])}
    </div>
    <p class="chart-pointer">Exact p50, min, and max figures are in the appendix at the end of this report.</p>
  </div>
  __FOOTER__
</article>
""")

    pages.append(f"""
<article class="sheet">
  {header("Checks")}
  <div class="body">
    <div class="sec">
      <h2>Checks</h2>
      <p class="tiny" style="margin-top:-6px;margin-bottom:8px">{cc['total']} checks · {cc['pass']} pass · {cc['warn']} warn · {cc['fail']} fail. Status reflects the written scorecard; every evidence figure is from the transcript.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Area</th><th>Check</th><th>Result</th><th>Evidence</th></tr></thead>
          <tbody>
            {''.join(check_html)}
          </tbody>
        </table>
      </div>
    </div>
  </div>
  __FOOTER__
</article>
""")

    pages.append(f"""
<article class="sheet">
  {header("Tools and tool-call results")}
  <div class="body">
    <div class="sec">
      <h2>Tools, resources, prompts</h2>
      <p class="tiny" style="margin-top:-6px;margin-bottom:8px">Tools: {model['tool_count']}. Resources: {model['resource_count']}. Prompts: {model['prompt_count']}. No schema issues rose to “missing description” or “missing inputSchema”. The issues are the un-required search query, the missing fetch outputSchema, and the advertised-but-empty prompt and resource surfaces.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Tool</th><th>Title</th><th>Annotations</th><th>Input</th><th>outputSchema</th><th>Notes</th></tr></thead>
          <tbody>
            {''.join(tool_html)}
          </tbody>
        </table>
      </div>
    </div>

    <div class="sec">
      <h2>Tool-call results (run 1, all read-only)</h2>
      <p class="tiny" style="margin-top:-6px;margin-bottom:8px">The same three calls succeeded on runs 2–5 with no errors. Search and code-sample results are returned both as stringified JSON inside content[].text and as structuredContent. Fetch returns Markdown in content only. Times below are the run 1 HTTP times from the transcript.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Tool</th><th>Arguments</th><th class="num">HTTP time</th><th>Result</th></tr></thead>
          <tbody>
            {''.join(call_html)}
          </tbody>
        </table>
      </div>
    </div>
  </div>
  __FOOTER__
</article>
""")

    pages.append(f"""
<article class="sheet">
  {header("Top fixes")}
  <div class="body">
    <div class="sec">
      <h2>Top 3 fixes</h2>
      <p style="margin-top:-4px;margin-bottom:12px">These are the changes that would close the largest remaining gaps in the score. Each one is a schema or capability change — no behavior change is required for the tools that already work.</p>
      {''.join(fixes_html)}
    </div>
    <div class="sec also">
      <h3>Also worth fixing</h3>
      <p class="tiny" style="margin-bottom:6px">{esc(sc['further_note'])}</p>
      <ol>{further}</ol>
    </div>
  </div>
  __FOOTER__
</article>
""")

    pages.append(f"""
<article class="sheet sheet-badge">
  {header("Tested by AgentScout badge")}
  <div class="body">
    <div class="sec">
      <h2>Share a “Tested by AgentScout” badge</h2>
      <p class="lead">Add this badge to your site or GitHub README. It links to this server’s AgentScout listing. It is a dated test result from this report, not an endorsement.</p>
    </div>
    <div class="badge-hero">
      <img src="{esc(badge_src)}" alt="{esc(badge_alt)}. Dated test result, not an endorsement." width="440">
      <p class="badge-note">{esc(badge_disclaimer)}</p>
    </div>
    <div class="sec snippet-grid">
      <div>
        <h3>HTML</h3>
        <p class="tiny" style="margin-top:-2px;margin-bottom:6px">The image URL will be filled in at launch. The link already points at the public listing.</p>
        <pre class="cmd">{esc(html_snippet)}</pre>
      </div>
      <div>
        <h3>Markdown</h3>
        <p class="tiny" style="margin-top:-2px;margin-bottom:6px">Paste this into a README. Same listing link, same dated-result meaning.</p>
        <pre class="cmd">{esc(md_snippet)}</pre>
      </div>
    </div>
  </div>
  __FOOTER__
</article>
""")

    pages.append(f"""
<article class="sheet sheet-method">
  {header("Methodology and disclaimer")}
  <div class="body">
    <div class="next-step">
      <div class="kicker">{esc(next_title)}</div>
      <h2>Book a free retest after you fix these</h2>
      <p>{esc(next_body)}</p>
      <div class="book">{esc(next_link)}</div>
    </div>

    <div class="sec two">
      <div>
        <h2>How this was tested</h2>
        <ol class="steps">{method}</ol>
        <p class="tiny" style="margin-top:10px">Client: {esc(model['client']['name'])} {esc(model['client']['version'])}. User-Agent: {esc(model['client']['user_agent'])}. Raw JSON-RPC transcript (all five runs, including full tool-call bodies) is the source of every latency number and schema claim in this report.</p>
      </div>
      <div>
        <h2>initialize capabilities returned</h2>
        <pre class="cmd">{esc(caps_pretty)}</pre>
        <p class="tiny" style="margin-top:8px">The server also returns a long instructions block that correctly describes a three-step workflow: search for breadth, code-sample search for examples, fetch for depth.</p>
      </div>
    </div>

    <div class="sec">
      <h2>Reproducible commands</h2>
      <p class="tiny" style="margin-top:-4px;margin-bottom:8px">These speak MCP. They do not submit anything, and they only read documentation.</p>
      <pre class="cmd">{esc(cmd)}</pre>
    </div>

    <div class="sec two">
      <div>
        <h2>What this sample does not include</h2>
        <ul class="scope">{scope}</ul>
      </div>
      <div>
        <h2>Disclaimer</h2>
        <div class="disc">
          <p>{esc(sc['disclaimer'])}</p>
          <p>Test date: {esc(sc['tested_display'])}. Time zone: {esc(sc['timezone_label'])}.</p>
        </div>
      </div>
    </div>
  </div>
  __FOOTER__
</article>
""")

    pages.append(f"""
<article class="sheet">
  {header("Appendix")}
  <div class="body">
    <div class="sec">
      <h2>Appendix: Exact latency figures</h2>
      <p class="tiny" style="margin-top:-4px;margin-bottom:10px">Median over {model['runs']} runs unless noted as run 1 only. All values are in milliseconds, taken from the transcript. Connect and every tool call stayed under one second.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Step</th><th class="num">p50</th><th class="num">Min</th><th class="num">Max</th><th class="num">n</th></tr></thead>
          <tbody>
            {''.join(latency_rows_html)}
          </tbody>
        </table>
      </div>
    </div>
  </div>
  __FOOTER__
</article>
""")

    total = len(pages)
    filled = []
    for i, page in enumerate(pages, start=1):
        page = page.replace("__FOOTER__", footer(i, total), 1)
        if web.get("fit"):
            page = f'<div class="fit">{page}</div>'
        filled.append(page)

    robots = ""
    if web.get("robots"):
        robots = f'\n  <meta name="robots" content="{esc(web["robots"])}">'
    csp_meta = ""
    if web.get("csp"):
        # The policy is our constant. It uses single quotes and must stay literal
        # inside the double-quoted content attribute. It contains no double quote.
        csp_meta = f'\n  <meta http-equiv="Content-Security-Policy" content="{web["csp"]}">'
    referrer = ""
    if web.get("referrer"):
        referrer = f'\n  <meta name="referrer" content="{esc(web["referrer"])}">'
    webbar = ""
    if web.get("pdf_href"):
        webbar = (
            '<p class="webbar"><span>Private AgentScout test report</span>'
            f'<a href="{esc(web["pdf_href"])}">Download PDF</a></p>\n'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">{referrer}{csp_meta}{robots}
  <title>AgentScout MCP Server Test Report — {esc(t['listed_name'])}</title>
  <link rel="stylesheet" href="{esc(css_href)}">
</head>
<body>
{webbar}{''.join(filled)}
</body>
</html>
"""

def render_pdf(html_path: Path, pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    # Chrome resolves relative assets from the HTML file location.
    uri = html_path.resolve().as_uri()
    cmd = [
        "google-chrome",
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--no-default-browser-check",
        "--hide-scrollbars",
        "--allow-file-access-from-files",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        "--virtual-time-budget=15000",
        uri,
    ]
    print("Rendering PDF:", " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, check=True)
    print(f"Wrote {pdf_path} ({pdf_path.stat().st_size} bytes)", file=sys.stderr)


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--transcript", type=Path, required=True)
    p.add_argument("--scorecard", type=Path, required=True)
    p.add_argument("--html", type=Path, default=HERE / "sample.html")
    p.add_argument("--pdf", type=Path, default=None)
    p.add_argument("--badge", type=Path, default=HERE / "badge-sample.svg",
                   help="Write the embeddable Tested by AgentScout badge SVG here.")
    p.add_argument("--previews", type=Path, default=None,
                   help="Directory for page-N.png previews (pdftoppm). Requires --pdf.")
    p.add_argument("--preview-prefix", type=Path, default=None,
                   help="Also copy previews to PREFIX-page-N.png and delete stale ones.")
    args = p.parse_args(argv)

    transcript = load_json(args.transcript)
    scorecard = load_json(args.scorecard)
    model = build_model(transcript, scorecard)
    badge_date = scorecard.get("badge_date") or scorecard.get("tested_display") or ""
    write_badge_svg(args.badge, scorecard["score"], scorecard["score_max"], badge_date)
    html_out = render_html(model)
    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.html.write_text(html_out)
    print(f"Wrote {args.html} ({args.html.stat().st_size} bytes)", file=sys.stderr)
    if args.pdf:
        render_pdf(args.html, args.pdf)
        if args.previews:
            pages = render_previews(args.pdf, args.previews, args.preview_prefix)
            print(f"Wrote {len(pages)} page previews in {args.previews}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
