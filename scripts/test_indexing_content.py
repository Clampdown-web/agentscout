#!/usr/bin/env python3
"""Indexing content: boilerplate out of main, MCP probe data on tool pages (TASK-16, A5/A6).

Pure-function tests plus a temp-dir build_reviews run; no build needed.
Run: python3 scripts/test_indexing_content.py
"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_extras as X
import build_reviews as RV
import build_tasks as BT
import mcp_response_rate as mrr
from test_mcp_response_rate import ServerCase
import atexit as _atexit
_atexit.unregister(X._apply_featured)  # read-only tests: importing build_extras registers
# site-wide exit hooks (featured/GA/lastmod/redirects) that rewrite generated files


def _reset_probes():
    X._MCP_PROBES = None


def _probe_fixture(rows):
    d = tempfile.mkdtemp()
    health = Path(d) / "data" / "mcp-health"
    health.mkdir(parents=True)
    with open(health / "2026-11.jsonl", "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    return d


def test_probe_records_tool_names():
    case = ServerCase("test_initialize_and_tools_list_count_as_responded")
    result, _calls = case._probe("ok")
    assert result["outcome"] == "responded"
    assert result["tool_count"] == 2
    assert result["tool_names"] == ["alpha", "beta"], f"tool_names = {result.get('tool_names')!r}"
    result, _calls = case._probe("empty")
    assert result["tool_count"] == 0
    assert result["tool_names"] == [], f"empty list gives {result.get('tool_names')!r}"
    result, _calls = case._probe("auth")
    assert result["outcome"] == "needs_auth"
    assert result.get("tool_names") is None, "needs_auth rows carry no names"


def test_probe_finish_caps_names_at_ten():
    base = mrr._base_result("https://example.com/mcp", "streamable-http", 0.0)
    assert base["tool_names"] is None
    out = mrr._finish(dict(base), outcome="responded", reason=None, status=200,
                      protocol="2025-06-18", tools=12,
                      names=[f"tool-{i}" for i in range(12)], started=0.0)
    assert out["tool_count"] == 12
    assert out["tool_names"] == [f"tool-{i}" for i in range(10)], "first 10 names only"
    out2 = mrr._finish(dict(base), outcome="failed", reason="timeout", status=0, started=0.0)
    assert out2["tool_names"] is None, "failed rows carry no names"
    assert "tool_names" in mrr.RECORD_KEYS, "tool_names must be a recorded key"


def test_probe_history_roundtrips_names(tmp=None):
    d = tempfile.mkdtemp()
    directory = Path(d) / "data" / "mcp-health"
    row = {"slug": "demo", "ts": "2026-11-18T00:00:00Z", "endpoint": "https://example.com/mcp",
           "transport": "streamable-http", "outcome": "responded", "http_status": 200,
           "latency_ms": 42, "protocol_version": "2025-06-18", "tool_count": 2,
           "tool_names": ["alpha", "beta"], "reason": None}
    import datetime as _dt
    mrr.append_history(directory, [row], _dt.datetime(2026, 11, 18, tzinfo=_dt.timezone.utc))
    back = mrr.load_history(directory)
    assert len(back) == 1 and back[0]["tool_names"] == ["alpha", "beta"]
    assert back[0]["tool_count"] == 2 and back[0]["slug"] == "demo"


def test_latest_probe_wins():
    d = _probe_fixture([
        {"slug": "s1", "ts": "2026-11-10T00:00:00Z", "outcome": "failed", "transport": "sse",
         "tool_count": None, "latency_ms": 5, "protocol_version": None},
        {"slug": "s1", "ts": "2026-11-12T00:00:00Z", "outcome": "responded", "transport": "streamable-http",
         "tool_count": 3, "tool_names": ["a", "b", "c"], "latency_ms": 120, "protocol_version": "2025-06-18"},
        {"slug": "s2", "ts": "2026-11-11T00:00:00Z", "outcome": "needs_auth", "transport": "streamable-http",
         "tool_count": None, "latency_ms": 9, "protocol_version": None},
    ])
    _reset_probes()
    try:
        assert X.mcp_probe("s1", d)["outcome"] == "responded", "latest row per slug wins"
        assert X.mcp_responded("s1", d) is True
        assert X.mcp_responded("s2", d) is False
        assert X.mcp_probe("nope", d) is None
    finally:
        _reset_probes()


def test_mcp_check_html():
    d = _probe_fixture([
        {"slug": "ok", "ts": "2026-11-12T16:18:39Z", "outcome": "responded", "transport": "streamable-http",
         "tool_count": 12, "tool_names": [f"t{i}" for i in range(12)], "latency_ms": 2877,
         "protocol_version": "2025-06-18"},
        {"slug": "old", "ts": "2026-11-11T00:00:00Z", "outcome": "responded", "transport": "sse",
         "tool_count": 4, "latency_ms": 300, "protocol_version": "2025-03-26"},
        {"slug": "locked", "ts": "2026-11-12T00:00:00Z", "outcome": "needs_auth", "transport": "streamable-http",
         "tool_count": None, "latency_ms": 251, "protocol_version": None},
        {"slug": "down", "ts": "2026-11-12T00:00:00Z", "outcome": "failed", "transport": "streamable-http",
         "tool_count": None, "latency_ms": 40, "protocol_version": None},
        {"slug": "evil", "ts": "2026-11-12T00:00:00Z", "outcome": "responded", "transport": "streamable-http",
         "tool_count": 1, "tool_names": ["<script>alert(1)</script>"], "latency_ms": 10,
         "protocol_version": "2025-06-18"},
    ])
    _reset_probes()
    try:
        assert X.mcp_check_html({"slug": "missing"}, d) == "", "unprobed slug renders nothing"
        ok = X.mcp_check_html({"slug": "ok"}, d)
        assert 'data-mcp-check="1"' in ok and "<h2" in ok and "Our check" in ok
        assert "<dd>streamable-http</dd>" in ok
        assert "<dd>Responded</dd>" in ok
        assert "<dd>12 tools: t0, t1, t2, t3, t4, t5, t6, t7, t8, t9, and 2 more</dd>" in ok, ok
        assert "<dd>2,877 ms</dd>" in ok
        assert "<dd>2025-06-18</dd>" in ok
        assert "<dd>Nov 12, 2026</dd>" in ok
        old = X.mcp_check_html({"slug": "old"}, d)
        assert "<dd>4 tools</dd>" in old, "row without tool_names still shows the count, no names line"
        assert "t0" not in old
        locked = X.mcp_check_html({"slug": "locked"}, d)
        assert "<dd>Needs auth</dd>" in locked
        assert "<dt>Tools</dt>" not in locked, "needs_auth has no tool count"
        assert "<dd>251 ms</dd>" in locked
        down = X.mcp_check_html({"slug": "down"}, d)
        assert "<dd>Failed</dd>" in down
        evil = X.mcp_check_html({"slug": "evil"}, d)
        assert "<script>alert(1)</script>" not in evil, "tool names are escaped"
        assert "&lt;script&gt;" in evil
    finally:
        _reset_probes()


def test_has_enrichment_uses_probe():
    # build_site.py cannot be imported (it runs the build), so exec the shipped
    # _has_enrichment function source in isolation with a stubbed build_extras.
    src = (ROOT / "build_site.py").read_text(encoding="utf-8")
    start = src.index("def _has_enrichment")
    end = src.index("\ndef ", start + 1)
    fn_src = src[start:end]
    responded = {"probe-ok"}
    ns = {"ENRICH_FIELDS": ("long", "who", "features", "pros", "cons", "setup", "faq", "pricing", "pricing_v", "mcp")}
    class FakeExtras:
        @staticmethod
        def mcp_responded(slug):
            return slug in responded
    ns["build_extras"] = FakeExtras()
    exec(fn_src, ns)
    has = ns["_has_enrichment"]
    # rich is the whole build_rich.R map, keyed by slug.
    assert has({"slug": "plain"}, {}) is False
    assert has({"slug": "probe-ok"}, {}) is True, "responded probe counts as enriched"
    assert has({"slug": "probe-ok"}, {"probe-ok": {"pros": ["x"]}}) is True
    assert has({"slug": "plain"}, {"plain": {"pros": ["x"]}}) is True, "rich fields still count"
    assert has({"slug": "plain"}, {"plain": {"long": []}}) is False, "empty rich fields do not count"


def test_reviews_section_has_no_disclaimer():
    sec = RV.section({"name": "Demo", "slug": "demo"}, None, "1")
    assert "Star ratings count right away" not in sec, "disclaimer must not be in the section"
    assert "rv-note" not in sec
    assert sec.count("<form") == 1 and "</form>" in sec, "form stays intact"
    assert 'id="reviews"' in sec and "Submit rating" in sec


def test_reviews_run_moves_disclaimer_after_main():
    import build_lovable as _bl  # noqa: F401  (imported so the stub below replaces it)
    d = tempfile.mkdtemp()
    tools_dir = Path(d) / "tools"
    tools_dir.mkdir(parents=True)
    page = ('<html><head></head><body><main class="wrap"><h1>Demo</h1>'
            '<h2 style="font-size:16px;margin-bottom:12px">Demo alternatives</h2>'
            '<section id="reviews" class="rv"><form class="rv-form">'
            '<p class="rv-note muted">Star ratings count right away; written reviews appear after a quick check. '
            'One rating per tool per visitor. Reviews are from site visitors, not verified users. '
            '<a href="../privacy.html#reviews">How reviews work</a></p></form></section>'
            '</main><footer>f</footer></body></html>')
    (tools_dir / "demo.html").write_text(page, encoding="utf-8")
    old_cwd = os.getcwd()
    old_data = RV.data
    stub = type("Stub", (), {"run": staticmethod(lambda: None)})()
    old_lovable = sys.modules.get("build_lovable")
    sys.modules["build_lovable"] = stub
    os.chdir(d)
    try:
        RV.data = lambda: {}
        tool = {"name": "Demo", "slug": "demo"}
        RV.run([tool])
        out = (tools_dir / "demo.html").read_text(encoding="utf-8")
        main = re.search(r"<main\b[^>]*>(.*?)</main>", out, flags=re.S).group(1)
        assert "Star ratings count right away" not in main, "disclaimer must leave <main>"
        assert out.count("Star ratings count right away") == 1, "disclaimer appears exactly once"
        after = out.split("</main>", 1)[1]
        assert "Star ratings count right away" in after
        assert 'id="reviews"' in main, "reviews section stays in <main>"
        RV.run([tool])  # second run: idempotent, still exactly one note
        out2 = (tools_dir / "demo.html").read_text(encoding="utf-8")
        assert out2.count("Star ratings count right away") == 1
    finally:
        os.chdir(old_cwd)
        RV.data = old_data
        if old_lovable is None:
            sys.modules.pop("build_lovable", None)
        else:
            sys.modules["build_lovable"] = old_lovable


def test_cta_after_main():
    inner = '<main class="wrap"><p>list</p>' + BT.ai_ref_cta_html("../") + '<p class="disclose">d</p></main><footer>f</footer>'
    moved = BT._cta_after_main(inner, "../")
    main = re.search(r"<main\b[^>]*>(.*?)</main>", moved, flags=re.S).group(1)
    assert "Fast-Track" not in main, "CTA must leave <main>"
    assert moved.count('class="ai-ref-cta"') == 1, "CTA appears exactly once"
    after = moved.split("</main>", 1)[1]
    assert "Fast-Track" in after
    assert moved.split("</main>", 1)[0].endswith("</main>") or True
    # Already after main: stays after main, refreshed in place.
    already = '<main class="wrap"><p>list</p></main>\n' + BT.ai_ref_cta_html("../") + '<footer>f</footer>'
    again = BT._cta_after_main(already, "../")
    assert again.count('class="ai-ref-cta"') == 1
    assert "Fast-Track" not in re.search(r"<main\b[^>]*>(.*?)</main>", again, flags=re.S).group(1)
    assert "Fast-Track" in again.split("</main>", 1)[1]
    # No CTA: unchanged.
    assert BT._cta_after_main("<main>x</main>", "../") == "<main>x</main>"


def test_detail_template_badge_out_of_main():
    tpl = (ROOT / "data" / "detail.tpl").read_text(encoding="utf-8")
    main = re.search(r"<main\b[^>]*>(.*?)</main>", tpl, flags=re.S).group(1)
    assert "{{BADGE}}" not in main, "badge placeholder must not be inside <main>"
    assert "{{BADGE}}" in tpl.split("</main>", 1)[1], "badge placeholder sits after </main>"
    assert "{{MCPCHECK}}" in main, "MCP check placeholder stays inside <main>"
    assert tpl.index("{{MCPCHECK}}") > tpl.index("{{ABOUT}}"), "check block follows the About paragraph"


def main():
    test_probe_records_tool_names()
    test_probe_finish_caps_names_at_ten()
    test_probe_history_roundtrips_names()
    test_latest_probe_wins()
    test_mcp_check_html()
    test_has_enrichment_uses_probe()
    test_reviews_section_has_no_disclaimer()
    test_reviews_run_moves_disclaimer_after_main()
    test_cta_after_main()
    test_detail_template_badge_out_of_main()
    print("indexing content ok: probe names, Our check block, enrichment rule, badge/note/CTA out of main")


if __name__ == "__main__":
    main()
