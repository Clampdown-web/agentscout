#!/usr/bin/env python3
"""False-alarm cases for the MCP link checker. No network."""
import os
import sys
import unittest
import urllib.error
from email.message import Message
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)

import check_mcp_links as chk


class _Resp:
    def __init__(self, status):
        self.status = status


def _http(url, code):
    return urllib.error.HTTPError(url, code, "status", Message(), None)


class _Opener:
    def __init__(self, table):
        self.table = table
        self.calls = []

    def __call__(self, req, timeout=None):
        ua = req.get_header("User-agent") or ""
        kind = "browser" if "Chrome" in ua else "bot"
        url = req.full_url
        self.calls.append((kind, req.get_method(), url, timeout))
        code = self.table[(kind, req.get_method(), url)]
        if isinstance(code, BaseException):
            raise code
        if code >= 400:
            raise _http(url, code)
        return _Resp(code)


class CheckerFalseAlarmTests(unittest.TestCase):
    def setUp(self):
        self._public = chk.public
        chk.public = lambda u, resolve=None: True

    def tearDown(self):
        chk.public = self._public

    def test_rate_limits_stay(self):
        src = (ROOT / "scripts" / "check_mcp_links.py").read_text(encoding="utf-8")
        self.assertIn("ThreadPoolExecutor(24)", src)
        self.assertIn("timeout=20", src)
        self.assertIn("timeout=25", src)
        self.assertIn("def ok_code(c,v):", src)

    def test_bot_block_or_timeout_retries_once_with_a_browser_get(self):
        # Cloudflare 520 on HEAD, browser GET 200. No second bot request.
        op = _Opener({
            ("bot", "HEAD", "https://a1.example/"): 520,
            ("browser", "GET", "https://a1.example/"): 200,
        })
        self.assertEqual(chk.probe("https://a1.example/", op), 200)
        self.assertEqual(op.calls, [("bot", "HEAD", "https://a1.example/", 20), ("browser", "GET", "https://a1.example/", 25)])
        self.assertFalse(chk.is_down(chk.link_row(200)))
        # 406 from the bot (HEAD then GET), browser GET 200.
        op = _Opener({
            ("bot", "HEAD", "https://word.example/"): 406,
            ("bot", "GET", "https://word.example/"): 406,
            ("browser", "GET", "https://word.example/"): 200,
        })
        self.assertEqual(chk.probe("https://word.example/", op), 200)
        self.assertEqual([c[0] for c in op.calls], ["bot", "bot", "browser"])
        self.assertEqual(op.calls[-1][1], "GET")
        # Timeout on both bot methods, browser GET 200. Existing transport path reports 403, which is live.
        op = _Opener({
            ("bot", "HEAD", "https://slow.example/"): TimeoutError("timed out"),
            ("bot", "GET", "https://slow.example/"): TimeoutError("timed out"),
            ("browser", "GET", "https://slow.example/"): 200,
        })
        self.assertEqual(chk.probe("https://slow.example/", op), 403)
        self.assertEqual(sum(1 for c in op.calls if c[0] == "browser"), 1)
        self.assertFalse(chk.is_down({"url": 403}))
        # Browser still failing keeps the bot status, so the row stays down.
        op = _Opener({
            ("bot", "HEAD", "https://down.example/"): 523,
            ("browser", "GET", "https://down.example/"): 523,
        })
        self.assertEqual(chk.probe("https://down.example/", op), 523)
        self.assertTrue(chk.is_down(chk.link_row(523)))

    def test_http_5xx_retries_https_and_notes_it(self):
        op = _Opener({
            ("bot", "HEAD", "http://old.example/"): 500,
            ("browser", "GET", "http://old.example/"): 500,
            ("bot", "HEAD", "https://old.example/"): 200,
        })
        code, note = chk.check_link("http://old.example/", op)
        self.assertEqual((code, note), (200, "https works"))
        row = chk.link_row(code, note=note)
        self.assertEqual(row, {"url": 200, "note": "https works"})
        self.assertFalse(chk.is_down(row))
        self.assertIn(("browser", "GET", "http://old.example/", 25), op.calls)
        self.assertTrue(any(c[2] == "https://old.example/" for c in op.calls))
        # https that is still down does not count.
        op = _Opener({
            ("bot", "HEAD", "http://still.example/"): 502,
            ("browser", "GET", "http://still.example/"): 502,
            ("bot", "HEAD", "https://still.example/"): 502,
            ("browser", "GET", "https://still.example/"): 502,
        })
        code, note = chk.check_link("http://still.example/", op)
        self.assertEqual((code, note), (502, None))
        self.assertTrue(chk.is_down(chk.link_row(code)))

    def test_github_404_does_not_mark_a_live_site_down(self):
        row = chk.link_row(200, 404)
        self.assertEqual(row, {"url": 200, "note": "github_404"})
        self.assertFalse(chk.is_down(row))
        self.assertNotIn("github", row)
        # The same OK rule still treats a real site failure as down, with or without GitHub.
        dead = chk.link_row(404, 404)
        self.assertEqual(dead, {"url": 404, "github": 404})
        self.assertTrue(chk.is_down(dead))
        self.assertTrue(chk.is_down(chk.link_row(500, 200)))
        self.assertFalse(chk.is_down(chk.link_row(401)))
        self.assertFalse(chk.is_down(chk.link_row(405, 200)))
        both = chk.link_row(200, 404, "https works")
        self.assertEqual(both["note"], "https works; github_404")
        self.assertFalse(chk.is_down(both))


if __name__ == "__main__":
    unittest.main()
