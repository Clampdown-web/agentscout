#!/usr/bin/env python3
"""MCP and directory verification copy is once daily, around 7 AM PT.

The link check runs once each morning Pacific and may finish later. Public
cards, status copy, and the templates that regenerate them must not claim a
second 7 PM pass.
"""
from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import build_seo_trim
import build_status

APPROVED = "Updated daily, around 7 AM PT"
# Split so this file can list the stale claims without matching its own scan.
STALE_PARTS = (
    ("twice", " daily"),
    ("twice-", "daily"),
    ("7 AM and ", "7 PM"),
    ("7 AM & ", "7 PM"),
    ("7 AM &amp; ", "7 PM"),
    ("7 PM ", "Pacific"),
    ("07:00 and ", "19:00"),
    ("07:00 & ", "19:00"),
    ("07:00 &amp; ", "19:00"),
)
STALE = tuple(a + b for a, b in STALE_PARTS)
GENERATORS = (
    "build_status.py",
    "build_growth.py",
    "build_extras.py",
    "build_aeo.py",
)
SKIP_DIRS = {".git", "node_modules", "og", "assets"}
CARD_RE = re.compile(r'<span class="vc-upd">(.*?)</span>')


def _card_line(html):
    found = CARD_RE.findall(html)
    if not found:
        raise AssertionError("verification card has no update line")
    return found


class VerificationCadenceTest(unittest.TestCase):
    def test_rendered_verification_card_uses_approved_copy(self):
        servers = []
        doc = {"catalog": {}, "servers": servers}
        rendered = [
            build_status._card_head("Verification", 1, 1),
            build_status._card_head("Verification for this list", 95, 100),
            build_status.tool_rows({"status": "live", "check_label": "OK"}),
            build_status.panel(doc, servers, "", "Verification"),
            build_seo_trim.dir_rows({}, ""),
        ]
        for html in rendered:
            lines = _card_line(html)
            self.assertTrue(lines)
            for line in lines:
                self.assertEqual(line, APPROVED)
                lowered = line.lower()
                self.assertNotIn("twice", lowered)
                self.assertNotIn("7 pm", lowered)
                self.assertNotIn("19:00", lowered)

    def test_generators_keep_approved_copy(self):
        self.assertEqual(build_status.VERIFY_CADENCE, APPROVED)
        for name in GENERATORS:
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn(APPROVED.lower(), text.lower(), name)
            for stale in STALE:
                self.assertNotIn(stale, text, f"{name} still has {stale!r}")

    def test_public_pages_drop_stale_cadence(self):
        stale_hits = []
        card_pages = 0
        for dirpath, dirnames, filenames in os.walk(ROOT):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                path = Path(dirpath) / name
                if path.resolve() == Path(__file__).resolve():
                    continue
                if path.suffix.lower() not in {".html", ".txt", ".py", ".md", ".js", ".mjs"}:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                for stale in STALE:
                    if stale in text:
                        stale_hits.append(f"{path.relative_to(ROOT)}: {stale}")
                if path.suffix.lower() == ".html":
                    lines = CARD_RE.findall(text)
                    if lines:
                        card_pages += 1
                        for line in lines:
                            self.assertEqual(line, APPROVED, path)
        self.assertEqual(stale_hits, [])
        self.assertGreater(card_pages, 1000)


if __name__ == "__main__":
    unittest.main()
