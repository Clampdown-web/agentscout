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
    _write(tmp, "data/cwv-seo-benchmark.json", json.dumps({
        "pages": [{"grade": "PASS", "lcp_ms": 100, "cls": 0.01} for _ in range(6)],
    }))
    _write(tmp, "data/seo-vitals-latest.json", json.dumps({
        "pagespeed_and_vitals": {
            f"https://example.test/{i}": {
                "mobile": {"scores": {"seo": 100, "best_practices": 100}},
                "desktop": {"scores": {"seo": 100, "best_practices": 100}},
            }
            for i in range(5)
        },
    }))
    return tmp


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
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("synthetic inner check", proc.stdout)
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
        self.assertEqual(result.problems, [], result.problems)
        self.assertEqual(result.synthetic_accepted, 2)
        self.assertIs(result.category_acceptance_claimed, False)

    def test_a_full_catalog_without_packages_fails_closed(self):
        root = _fixture(tools=2000, mcp=10)
        result = morning_audit.predeploy(root)
        self.assertTrue(any("bot packages are missing" in item for item in result.problems), result.problems)
        self.assertTrue(any("pack pages" in item for item in result.problems))

    def test_email_wordmark_and_missing_measurement_are_visible(self):
        problems = morning_audit.listed_email_problems("4+\n3+", "<img src=logo-wordmark.svg>", "4+", "3+")
        self.assertTrue(any("logo-wordmark-dark.png" in item for item in problems))
        self.assertTrue(any("logo-wordmark.svg" in item for item in problems))
        root = _fixture()
        (root / "bot-store" / "index.html").write_text(
            (root / "bot-store" / "index.html").read_text(encoding="utf-8") + "{tier_btns}",
            encoding="utf-8",
        )
        # A two-tool fixture is not a full catalog, so pack UX stays quiet.
        self.assertEqual(morning_audit.pack_ux_problems(root), [])
        state = json.loads((root / "data" / "anim_state.json").read_text(encoding="utf-8"))
        state["tools"] = 2000
        (root / "data" / "anim_state.json").write_text(json.dumps(state), encoding="utf-8")
        tools = json.loads((root / "tools.json").read_text(encoding="utf-8"))
        tools.extend({"category": "coding"} for _ in range(1998))
        (root / "tools.json").write_text(json.dumps(tools), encoding="utf-8")
        self.assertTrue(any("{tier_btns}" in item for item in morning_audit.pack_ux_problems(root)))
        root = _fixture()
        (root / "data" / "cwv-seo-benchmark.json").unlink()
        result = morning_audit.live(root, lambda *args: (500, {}, ""))
        self.assertTrue(any("cwv-seo-benchmark.json" in item for item in result.unverified), result.unverified)
        pre = morning_audit.predeploy(root)
        self.assertTrue(any("Core Web Vitals" in item for item in pre.deferred), pre.deferred)
        self.assertTrue(all("cwv-seo-benchmark" not in item for item in pre.problems))

    def test_nav_mismatch_fails_the_predeploy_path(self):
        root = _fixture()
        page = (root / "videos" / "index.html").read_text(encoding="utf-8")
        (root / "videos" / "index.html").write_text(page.replace(">Home<", ">Elsewhere<", 1), encoding="utf-8")
        result = morning_audit.predeploy(root)
        self.assertTrue(any("nav/footer mismatch" in item for item in result.problems), result.problems)


if __name__ == "__main__":
    unittest.main()
