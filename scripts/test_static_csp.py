#!/usr/bin/env python3
"""CSP and maker-text escaping for generated pages.

Fails when a key page loses the Content-Security-Policy meta tag, when the
policy drops a host the site actually loads, or when maker-supplied text is
written into HTML unescaped. No network calls and no POST to /submit.
"""
from __future__ import annotations

import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_rich  # noqa: E402
import csp  # noqa: E402

# Pages a reader actually opens. Each must keep the enforcing meta policy.
PAGES = (
    "index.html",
    "mcp/index.html",
    "mcp/connect.html",
    "tools/zed.html",
    "submit.html",
    "sponsor.html",
    "best/index.html",
    "best/mcp-servers.html",
    "newsletter.html",
    "bot-store/index.html",
)

REQUIRED = (
    "default-src 'self'",
    "script-src 'self'",
    "'unsafe-inline'",
    "https://challenges.cloudflare.com",
    "https://www.googletagmanager.com",
    "https://static.cloudflareinsights.com",
    "https://api.agentscouthq.com",
    "https://votes.agentscouthq.com",
    "https://agentscout-image.agentscouthq.workers.dev",
    "https://agentscout.beehiiv.com",
    "https://*.google-analytics.com",
    "https://*.analytics.google.com",
    "frame-src https://challenges.cloudflare.com",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self' https://agentscout.beehiiv.com",
)

PAYLOAD = '<script>alert("xss")</script><img src=x onerror=alert(1)>'


def _policy(html):
    match = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)">', html)
    if not match:
        raise AssertionError("missing Content-Security-Policy")
    return match.group(1)


class StaticCspTest(unittest.TestCase):
    def test_headers_file_enforces_the_same_allowlist(self):
        text = (ROOT / "_headers").read_text(encoding="utf-8")
        directives = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
        self.assertNotIn("Content-Security-Policy-Report-Only", directives)
        self.assertNotIn("report-uri", directives)
        self.assertNotIn("report-to", directives)
        match = re.search(r"(?m)^  Content-Security-Policy: (.+)$", directives)
        self.assertIsNotNone(match)
        header = match.group(1)
        for bit in (
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' https://challenges.cloudflare.com",
            "connect-src",
            "https://challenges.cloudflare.com",
            "https://api.agentscouthq.com",
            "https://votes.agentscouthq.com",
            "https://agentscout-image.agentscouthq.workers.dev",
            "https://mcp.agentscouthq.com",
            "https://agentscout.beehiiv.com",
            "frame-src https://challenges.cloudflare.com",
            "worker-src 'self'",
            "frame-ancestors 'none'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self' https://agentscout.beehiiv.com",
        ):
            self.assertIn(bit, header)
        self.assertNotIn("unsafe-eval", header.replace("'wasm-unsafe-eval'", ""))

    def test_key_pages_keep_the_allowlist(self):
        for rel in PAGES:
            html = (ROOT / rel).read_text(encoding="utf-8")
            policy = _policy(html)
            for bit in REQUIRED:
                self.assertIn(bit, policy, rel)
            connect = policy.split("connect-src ", 1)[1].split(";", 1)[0]
            self.assertIn("https://challenges.cloudflare.com", connect, rel)
            self.assertNotIn("data:", connect, rel)
            self.assertNotIn("unsafe-eval", policy.replace("'wasm-unsafe-eval'", ""), rel)
            self.assertIn("'wasm-unsafe-eval'" if rel == "index.html" else "script-src", policy)

    def test_template_is_the_source_of_the_policy(self):
        tpl = (ROOT / "data/detail.tpl").read_text(encoding="utf-8")
        policy = _policy(tpl)
        for bit in REQUIRED:
            self.assertIn(bit, policy)
        connect = policy.split("connect-src ", 1)[1].split(";", 1)[0]
        self.assertIn("https://challenges.cloudflare.com", connect)
        self.assertNotIn("unsafe-eval", policy.replace("'wasm-unsafe-eval'", ""))
        # Tool pages do not compile WebAssembly. The homepage keeps its own token.
        self.assertNotIn("wasm-unsafe-eval", policy)

    def test_missing_meta_is_restored_without_stripping_wasm(self):
        bare = "<!doctype html><html><head><meta charset=\"utf-8\"></head><body></body></html>"
        restored = csp.harden(bare, "tools/x.html")
        self.assertIn(csp.POLICY, restored)
        home = '<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="script-src \'self\' \'wasm-unsafe-eval\'"></head><body><a href="https://example.com" target="_blank" rel="noopener">x</a></body></html>'
        fixed = csp.harden(home, "index.html")
        self.assertIn("'wasm-unsafe-eval'", _policy(fixed))
        self.assertIn('rel="noopener noreferrer"', fixed)
        self.assertIn("https://www.googletagmanager.com", _policy(fixed))

    def test_blank_form_gets_noopener(self):
        html = '<form action="https://agentscout.beehiiv.com/subscribe" method="get" target="_blank"></form>'
        out = csp.harden_links(html)
        self.assertIn('rel="noopener noreferrer"', out)

    def test_maker_fields_are_escaped_in_a_generated_page(self):
        tool = {
            "name": PAYLOAD,
            "description": PAYLOAD,
            "pricing": "Free <b>now</b>",
            "pricing_detail": PAYLOAD,
            "category": "MCP servers",
            "status_note": PAYLOAD,
            "good_for": PAYLOAD,
            "website": 'https://example.com/?q=<script>alert(1)</script>',
            "url": 'javascript:alert(1)',
        }
        page = csp.render_tool_sample(tool)
        self.assertIn(csp.POLICY, page)
        self.assertNotRegex(page, r"<script>alert")
        self.assertNotRegex(page, r"<img\b[^>]*onerror")
        self.assertNotIn("javascript:", page)
        self.assertEqual(csp.safe_http_url("javascript:alert(1)"), "#")
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", page)
        self.assertIn("&lt;b&gt;now&lt;/b&gt;", page)
        self.assertIn("https://example.com/?q=&lt;script&gt;alert(1)&lt;/script&gt;", page)
        # The generator itself must keep using the shared escape.
        src = (ROOT / "build_site.py").read_text(encoding="utf-8")
        self.assertIn("e=_csp.escape", src)
        for field in ('e(x["name"])', 'e(x["description"])', 'e(x["status_note"])'):
            self.assertIn(field, src, field)
        tasks = (ROOT / "build_tasks.py").read_text(encoding="utf-8")
        self.assertIn('e(x["good_for"])', tasks)

    def test_rich_faq_escapes_maker_description(self):
        tool = {
            "name": "Safe",
            "slug": "safe",
            "description": PAYLOAD,
            "category": "coding",
            "pricing": "Free",
            "pricing_detail": PAYLOAD,
            "audience": "builders",
            "maturity": "Active",
            "verified": "2026-11-09",
            "added": "2026-11-01",
        }
        _out, extra = build_rich.auto(
            "<html><head></head><body></body></html>",
            tool,
            [tool],
            lambda _c: "coding",
            "https://example.com/",
            "https://agentscouthq.com/",
        )
        section = extra[0]
        self.assertNotRegex(section, r"<script>alert")
        self.assertNotRegex(section, r"<img\b[^>]*onerror")
        self.assertIn("&lt;script&gt;", section)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", section)

    def test_unpinned_vendor_scripts_are_not_given_a_fake_sri_requirement(self):
        # Rolling URLs. An integrity hash here would break the next vendor publish.
        for url in (
            "https://challenges.cloudflare.com/turnstile/v0/api.js",
            "https://www.googletagmanager.com/gtag/js?id=G-TGDXK5F13D",
        ):
            self.assertEqual(csp.missing_sri(f'<script src="{url}"></script>'), [])
        pinned = '<script src="https://cdn.example.com/lib/1.2.3/lib.js"></script>'
        self.assertEqual(csp.missing_sri(pinned), ["https://cdn.example.com/lib/1.2.3/lib.js"])
        ok = '<script src="https://cdn.example.com/lib/1.2.3/lib.js" integrity="sha384-abc" crossorigin="anonymous"></script>'
        self.assertEqual(csp.missing_sri(ok), [])
        for rel in PAGES:
            html = (ROOT / rel).read_text(encoding="utf-8")
            self.assertEqual(csp.missing_sri(html), [], rel)


if __name__ == "__main__":
    unittest.main()
