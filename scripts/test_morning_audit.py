#!/usr/bin/env python3
"""The 7AM entrypoint, not the helper module, is what these checks execute."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import morning_audit
import publish_gate

APP = "/* Scroll buttons */\n(function(){var up=document.createElement('button');up.className='scrollbtn up';var down=document.createElement('button');down.className='scrollbtn down';})();\n"
CSS = ".scrollbtns{}\n.scrollbtn.show{}\n"


def _chrome(rel: str) -> str:
    prefix = "../" * rel.count("/")
    return (
        f'<nav><a href="{prefix}index.html">Home</a><a href="{prefix}submit.html">Submit a tool</a></nav>'
        f'<footer><a href="{prefix}index.html">Home</a><a href="{prefix}submit.html">Submit a tool</a></footer>'
    )


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture(tools: int = 2, mcp: int = 1) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="morning-audit-"))
    token = f"20261108-{tools}"
    for rel in ("index.html", "bot-store/index.html", "videos/index.html", "submit.html"):
        extra = ""
        if rel == "submit.html":
            ids = "".join(f'<input id="{item}">' for item in (
                "sf", "spkg-field", "name", "website", "category", "pricing", "desc", "email",
                "found", "sbtn", "sdone", "sdone-msg", "sdone-pay", "sdone-pay-btn",
            ))
            extra = (
                ids
                + '<p>https://api.agentscouthq.com/submit</p>'
                + '<select id="category"><option value="coding">coding</option><option>other</option></select>'
                + '<select id="pricing"><option>Free</option><option>Paid</option></select>'
                + "".join(morning_audit.DIRECTORY_STRIPE.values())
            )
        page = (
            "<!doctype html><html><body>"
            + _chrome(rel)
            + f'<video><source src="assets/animations/clip.mp4?v={token}"></video>'
            + extra
            + "</body></html>"
        )
        _write(tmp, rel, page)
    _write(tmp, "styles.css", CSS)
    _write(tmp, "app.js", APP)
    _write(tmp, "categories.json", json.dumps(["coding", "other"]))
    catalog = [{"category": "MCP servers"} for _ in range(mcp)]
    catalog.extend({"category": "coding"} for _ in range(tools - mcp))
    _write(tmp, "tools.json", json.dumps(catalog))
    _write(tmp, "data/anim_state.json", json.dumps({
        "tools": tools, "mcp": mcp, "pages": 4, "bot_templates": 0,
        "free_tools": 1, "date": "2026-11-08", "script_mtime": 1,
    }))
    products = {"packages": [{"id": "free", "name": "Free", "price_usd": 0}], "addons": [], "bot_templates": [], "agent_packs": []}
    text = json.dumps(products)
    _write(tmp, "api/products.json", text)
    _write(tmp, "cloudflare-mcp-worker/products_snapshot.json", text)
    _write(tmp, "api/metrics.json", json.dumps({
        "tools_count": tools, "pages_count": 4, "indexed_pages_count": 4, "x_combined_followers": 3,
    }))
    links = "".join(morning_audit.DIRECTORY_STRIPE.values()) + "".join(morning_audit.BOT_STRIPE.values())
    _write(tmp, "sponsor.html", _chrome("sponsor.html") + links)
    _write(tmp, ".well-known/acp.json", links)
    _write(tmp, "bot-templates/index.html", _chrome("bot-templates/index.html") + links + "logo-wordmark.svg")
    store = (tmp / "bot-store" / "index.html").read_text(encoding="utf-8")
    (tmp / "bot-store" / "index.html").write_text(store + links + "logo-wordmark.svg", encoding="utf-8")
    submit = (tmp / "submit.html").read_text(encoding="utf-8")
    (tmp / "submit.html").write_text(submit + "".join(morning_audit.BOT_STRIPE.values()), encoding="utf-8")
    key = "abcdef0123456789abcdef0123456789"
    _write(tmp, f"{key}.txt", key)
    _write(tmp, "data/cwv-seo-benchmark.json", json.dumps(_benchmark(tools)))
    _write(tmp, "data/seo-vitals-latest.json", json.dumps(_vitals()))
    _pack_surface(tmp)
    return tmp


def _benchmark(tools: int) -> dict:
    pages = []
    for i, path in enumerate(("/", "/bot-store/", "/videos/", "/bot-templates/", "/mcp/", "/tools/noteboxd.html")):
        pages.append({
            "url": f"http://127.0.0.1:8766{path}",
            "lcp_ms": 100 + i,
            "cls": 0,
            "ttfb_ms": 50,
            "grade": "PASS",
        })
    return {
        "generated_at": "2026-11-08",
        "source": "lab-unthrottled-benchmark",
        "method": "cwv_seo_benchmark.measure_url",
        "throttle": "none",
        "field_cwv": False,
        "thresholds": {"lcp_ms": 2500, "cls": 0.1, "ttfb_ms": 800},
        "scope": {"artifact_date": "2026-11-08", "artifact_tools": tools},
        "targets": [page["url"] for page in pages],
        "not_measured": [],
        "pages": pages,
    }


def _vitals() -> dict:
    urls = [f"https://agentscouthq.com/hub/{i}" for i in range(5)]
    return {
        "generated_at": "2026-11-08",
        "source": "lab-pagespeed",
        "throttle": "none",
        "field_cwv": False,
        "scope": {"artifact_date": "2026-11-08", "artifact_tools": 2},
        "targets": urls,
        "pagespeed_and_vitals": {
            url: {
                "mobile": {"scores": {"seo": 100, "best_practices": 100}},
                "desktop": {"scores": {"seo": 100, "best_practices": 100}},
            }
            for url in urls
        },
    }


def _pack_surface(tmp: Path) -> None:
    hosts = "Claude Code Cursor Codex Grok Bot Lovable"
    cards = "".join(f'<div class="ap-compat" data-pack="p{i}"></div>' for i in range(25))
    section = f'<section id="ai-agent-packs">{hosts}{cards}</section>'
    dock = 'id="ap-dock" hidden #ap-dock[hidden]{display:none'
    prices = "$39 $59 $69 $149 clampdown19 built by logo-wordmark.svg neon-lime neon-gold neon-orange neon-red #10b981"
    for rel in ("bot-store/index.html", "bot-templates/index.html"):
        path = tmp / rel
        path.write_text(path.read_text(encoding="utf-8") + section + dock + prices, encoding="utf-8")
    templates = tmp / "bot-templates" / "index.html"
    templates.write_text(templates.read_text(encoding="utf-8") + "agentscout-bot-constellation.mp4?v=1", encoding="utf-8")
    videos = tmp / "videos" / "index.html"
    videos.write_text(videos.read_text(encoding="utf-8") + "$35 25 AI Agent Packs Lovable", encoding="utf-8")
    _write(tmp, "tools/lovable.html", "#ai-agent-packs $35")
    _write(tmp, "data/outreach/25-agent-packs-email.html", "https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09 Claude")
    for i in range(25):
        _write(tmp, f"bot-store/p{i}/index.html", 'class="pack-compat"')


class EntrypointTest(unittest.TestCase):
    def test_predeploy_cli_passes_a_small_tree_and_does_not_post(self):
        root = _fixture()
        env = os.environ.copy()
        env["AGENTSCOUT_ROOT"] = str(root)
        env.pop("AGENTSCOUT_ALLOW_STALE_ROOT", None)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "daily_deep_audit.py"), "--predeploy"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("[PASS] categories:", proc.stdout)
        self.assertIn("[PASS] animation:", proc.stdout)
        self.assertIn("[PASS] form-fields:", proc.stdout)
        self.assertIn("[FAIL] zip-packages:", proc.stdout)
        self.assertNotIn("API accepts", proc.stdout)
        self.assertNotIn("https://api.agentscouthq.com/submit", proc.stdout.split("SUMMARY")[0].replace("submit endpoint", ""))

    def test_missing_root_and_stale_root_are_refused(self):
        env = os.environ.copy()
        env.pop("AGENTSCOUT_ROOT", None)
        missing = subprocess.run(
            [sys.executable, str(ROOT / "daily_deep_audit.py"), "--predeploy"],
            cwd=ROOT, env=env, capture_output=True, text=True,
        )
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("agent-tool-finder", missing.stderr + missing.stdout)
        env["AGENTSCOUT_ROOT"] = "/workspace/agent-tool-finder"
        stale = subprocess.run(
            [sys.executable, str(ROOT / "daily_deep_audit.py"), "--predeploy"],
            cwd=ROOT, env=env, capture_output=True, text=True,
        )
        self.assertNotEqual(stale.returncode, 0)
        self.assertIn("stale checkout", stale.stderr + stale.stdout)

    def test_live_mode_checks_both_origins_and_mcp_shape_without_a_category_post(self):
        root = _fixture()
        calls = []

        def fetch(url, method="GET", data=None, headers=None):
            calls.append((url, method, headers, data))
            agent = (headers or {}).get("User-Agent", "")
            if method == "OPTIONS" and not (headers or {}).get("Origin"):
                return 403, {"vary": "Origin"}, ""
            if method == "OPTIONS":
                return 204, {"Access-Control-Allow-Origin": "https://agentscouthq.com"}, ""
            if "HTTrack" in agent:
                return 403, {}, ""
            if method == "POST" and url.endswith("/mcp"):
                body = json.dumps({"result": {"structuredContent": {
                    "total_products": 1,
                    "products": [{"id": "free", "name": "Free", "price_usd": 0}],
                }}})
                return 200, {}, body
            if url.endswith("/api/metrics.json"):
                return 200, {}, json.dumps({
                    "tools_count": 2, "pages_count": 4, "indexed_pages_count": 4, "x_combined_followers": 3,
                })
            if url.endswith(".txt"):
                return 200, {}, "abcdef0123456789abcdef0123456789"
            headers_out = {
                "server": "cloudflare",
                "strict-transport-security": "max-age=31536000; includeSubDomains; preload",
                "x-frame-options": "SAMEORIGIN",
                "x-content-type-options": "nosniff",
                "referrer-policy": "strict-origin-when-cross-origin",
            }
            return 200, headers_out, "pages 4+ active checkout"

        result = morning_audit.live(root, fetch)
        self.assertEqual(result.problems, [], result.problems)
        self.assertIs(result.category_acceptance_claimed, False)
        self.assertFalse(any(url.endswith("/submit") and method == "POST" for url, method, _headers, _data in calls))
        self.assertFalse(any("indexnow.org" in url for url, _method, _headers, _data in calls))
        self.assertEqual(sum(1 for url, method, _h, _d in calls if method == "OPTIONS"), 2)
        self.assertTrue(any(method == "POST" and url.endswith("/mcp") for url, method, _h, _d in calls))
        self.assertNotIn("accepts all", " ".join(result.passes))

    def test_a_no_origin_204_and_a_pages_string_gap_are_not_confused(self):
        opened = publish_gate.preflight_problems(204, origin_present=False)
        self.assertEqual(opened, ["OPTIONS without Origin returned 204, expected 403"])
        body = json.dumps({"result": {"structuredContent": {
            "total_products": 2,
            "products": [
                {"id": "same", "name": "A", "price_usd": 0},
                {"id": "same", "name": "B", "price_usd": 1},
            ],
        }}})
        problems = morning_audit.mcp_body_problems(200, body)
        self.assertTrue(any("duplicate product id same" in item for item in problems))
        self.assertEqual(morning_audit.mcp_body_problems(200, "{"), ["list_packages response is not JSON"])
        mismatch = json.dumps({"result": {"structuredContent": {
            "total_products": 9,
            "products": [{"id": "only", "name": "Only", "price_usd": 0}],
        }}})
        self.assertTrue(any("total_products is 9" in item for item in morning_audit.mcp_body_problems(200, mismatch)))

    def test_turnstile_text_does_not_become_an_acceptance_claim(self):
        responses = [(name, "Bot check failed.") for name in ("coding", "other")]
        self.assertEqual(publish_gate.category_probe_problems(responses), [])
        root = _fixture()
        result = morning_audit.predeploy(root)
        self.assertTrue(any(item.startswith("zip-packages:") for item in result.problems), result.problems)
        self.assertFalse(any(item.startswith("categories:") for item in result.problems))
        self.assertEqual(result.synthetic_accepted, 2)
        self.assertIs(result.category_acceptance_claimed, False)

    def test_a_full_catalog_without_packages_fails_closed(self):
        root = _fixture(tools=2000, mcp=10)
        result = morning_audit.predeploy(root)
        self.assertTrue(any("25-agent-packs is missing" in item for item in result.problems), result.problems)

    def test_email_wordmark_and_missing_measurement_are_visible(self):
        problems = morning_audit.listed_email_problems("4+\n3+", "<img src=logo-wordmark.svg>", "4+", "3+")
        self.assertTrue(any("logo-wordmark-dark.png" in item for item in problems))
        self.assertTrue(any("logo-wordmark.svg" in item for item in problems))
        root = _fixture()
        self.assertEqual(morning_audit.pack_ux_problems(root), [])
        (root / "bot-store" / "index.html").write_text(
            (root / "bot-store" / "index.html").read_text(encoding="utf-8") + "{tier_btns}",
            encoding="utf-8",
        )
        self.assertTrue(any("{tier_btns}" in item for item in morning_audit.pack_ux_problems(root)))
        stale = _benchmark(2)
        stale["generated_at"] = "2026-11-04"
        problems, _note = morning_audit.measurement_evidence(stale, "cwv", "2026-11-08", 2)
        self.assertTrue(any("older than the artifact date" in item for item in problems), problems)
        throttled = _benchmark(2)
        throttled["source"] = "lab-lighthouse"
        throttled["method"] = "lighthouse-mobile-throttled"
        throttled["throttle"] = "mobile-simulated"
        throttled["pages"][1]["lcp_ms"] = 3376
        throttled["pages"][1]["grade"] = "PASS"
        problems, _note = morning_audit.measurement_evidence(throttled, "cwv", "2026-11-08", 2)
        self.assertTrue(any("Throttled Lighthouse" in item for item in problems), problems)
        fresh_problems, fresh_note = morning_audit.measurement_evidence(_benchmark(2), "cwv", "2026-11-08", 2)
        self.assertEqual(fresh_problems, [], fresh_problems)
        stalled = _benchmark(2)
        stalled["not_measured"] = [{"url": "http://127.0.0.1:8766/submit.html", "reason": "networkidle timeout"}]
        stalled_problems, _stalled_note = morning_audit.measurement_evidence(stalled, "cwv", "2026-11-08", 2)
        self.assertTrue(any("networkidle" in item for item in stalled_problems), stalled_problems)
        self.assertIn("not field CWV", fresh_note)
        seo69 = _vitals()
        seo69["pagespeed_and_vitals"][seo69["targets"][0]]["mobile"]["scores"]["seo"] = 69
        self.assertTrue(any("SEO 100" in item or "not SEO 100" in item for item in morning_audit.measurement_evidence(seo69, "vitals", "2026-11-08", 2)[0]))
        root = _fixture()
        (root / "data" / "cwv-seo-benchmark.json").unlink()
        result = morning_audit.live(root, lambda *args: (500, {}, ""))
        self.assertTrue(any("cwv-seo-benchmark.json" in item for item in result.unverified), result.unverified)
        pre = morning_audit.predeploy(root)
        self.assertTrue(any(item.startswith("postdeploy-vitals:") for item in pre.deferred), pre.deferred)
        self.assertTrue(all("cwv-seo-benchmark" not in item for item in pre.problems))

    def test_nav_mismatch_fails_the_predeploy_path(self):
        root = _fixture()
        page = (root / "videos" / "index.html").read_text(encoding="utf-8")
        (root / "videos" / "index.html").write_text(page.replace(">Home<", ">Elsewhere<", 1), encoding="utf-8")
        result = morning_audit.predeploy(root)
        self.assertTrue(any("nav/footer mismatch" in item or "nav-footer:" in item for item in result.problems), result.problems)

    def test_a_broken_zip_is_reported_by_the_start_here_comparison(self):
        import verify_bot_zip_packages
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            guide = root / "START-HERE.md"
            guide.write_text("package copy\n", encoding="utf-8")
            broken = root / "pack.zip"
            broken.write_bytes(b"not a zip")
            problems = verify_bot_zip_packages.compare_start_here("pack", guide, broken)
            self.assertEqual(problems, ["pack START-HERE comparison could not read a broken zip"])


if __name__ == "__main__":
    unittest.main()
