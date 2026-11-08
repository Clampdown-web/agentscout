#!/usr/bin/env python3
"""Submit widget and leaderboard contrast. No live POST and no CSP edit."""
from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _contrast(rgb, bg):
    def lin(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    def lum(color):
        r, g, b = color
        return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)

    hi, lo = max(lum(rgb), lum(bg)), min(lum(rgb), lum(bg))
    return (hi + 0.05) / (lo + 0.05)


class SubmitWidgetTest(unittest.TestCase):
    def test_css_and_js_share_the_asset_stamp(self):
        tasks = (ROOT / "build_tasks.py").read_text(encoding="utf-8")
        stamp = re.search(r'ASSET_V = "(\d+)"', tasks).group(1)
        self.assertNotEqual(stamp, "202611042330")
        html = (ROOT / "submit.html").read_text(encoding="utf-8")
        self.assertIn(f"styles.css?v={stamp}", html)
        self.assertIn(f"app.js?v={stamp}", html)
        self.assertNotIn("styles.css?v=202611042330", html)
        css = (ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertIn("@media(max-width:640px){.pkg-grid{margin-right:calc(56px + env(safe-area-inset-right))}}", css)
        self.assertIn('data-sitekey="0x4AAAAAAFfaxf14aQF-sky1"', html)
    def test_error_callback_keeps_the_token_gate_and_the_csp(self):
        html = (ROOT / "submit.html").read_text(encoding="utf-8")
        self.assertIn('data-sitekey="0x4AAAAAAFfaxf14aQF-sky1"', html)
        self.assertIn('data-error-callback="asTsErr"', html)
        self.assertIn('data-callback="asTsOk"', html)
        self.assertIn("https://challenges.cloudflare.com/turnstile/v0/api.js", html)
        self.assertIn("window.asTsErr=function(code)", html)
        err_fn = html.split("window.asTsErr=")[1].split("window.asTsOk=")[0]
        ok_fn = html.split("window.asTsOk=")[1].split(";(function()")[0]
        self.assertIn("return true", err_fn)
        self.assertIn('getElementById("sfts")', err_fn)
        self.assertNotIn('getElementById("serr")', err_fn)
        self.assertIn('getElementById("sfts")', ok_fn)
        self.assertNotIn('getElementById("serr")', ok_fn)
        self.assertIn('id="sfts"', html)
        self.assertNotIn('id="serr" role="alert" style="color:#e5484d"', html)
        gate = html.split("var ts=sfTs()", 1)[1][:180]
        self.assertIn("!ts", gate)
        self.assertIn("Please complete the quick check", gate)
        csp = re.search(r'Content-Security-Policy" content="([^"]+)"', html).group(1)
        connect = csp.split("connect-src ", 1)[1].split(";", 1)[0]
        self.assertNotIn("data:", connect)
        self.assertNotIn("challenges.cloudflare.com", connect)
        self.assertIn("https://challenges.cloudflare.com", csp.split("script-src ", 1)[1].split(";", 1)[0])
        self.assertIn("https://challenges.cloudflare.com", csp.split("frame-src ", 1)[1].split(";", 1)[0])

    def test_phone_package_gutter_does_not_hide_scroll_buttons(self):
        css = (ROOT / "styles.css").read_text(encoding="utf-8")
        block = re.search(r"@media \(max-width:640px\)\{(.*?)\n\}", css, re.S).group(1)
        self.assertIn(".pkg-grid{margin-right:calc(56px + env(safe-area-inset-right))}", css)
        self.assertNotIn(".pkg-grid", block)
        self.assertNotIn("display:none", block)
        js = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("#sf-turnstile", js)
        self.assertIn('role="tab"', js)

    def test_leaderboard_arrow_contrast_clears_4_5(self):
        css = (ROOT / "leaderboard/index.html").read_text(encoding="utf-8")
        white = (255, 255, 255)
        dark = (14, 16, 21)
        self.assertGreaterEqual(_contrast((0x0D, 0x6B, 0x34), white), 4.5)
        self.assertGreaterEqual(_contrast((0x3D, 0xD6, 0x78), dark), 4.5)
        self.assertGreaterEqual(_contrast((0xC1, 0x40, 0x36), white), 4.5)
        self.assertGreaterEqual(_contrast((0xDA, 0x6B, 0x62), dark), 4.5)
        self.assertIn(".lbm.up{color:#0d6b34}", css)
        self.assertIn("html[data-theme=dark] .lbm.up{color:#3dd678}", css)
        self.assertIn(".lbm.dn{color:#c14036}", css)
        self.assertIn("html[data-theme=dark] .lbm.dn{color:#da6b62}", css)
        self.assertNotIn("#1a9a4b", css)
        self.assertGreaterEqual(_contrast((0x9F, 0x12, 0x39), white), 4.5)
        self.assertGreaterEqual(_contrast((0xFD, 0xA4, 0xAF), dark), 4.5)
        self.assertLess(_contrast((0xE5, 0x48, 0x4D), white), 4.5)
        css_site = (ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertIn("#serr,#sfts,.reqmark{color:#9f1239}", css_site)
        self.assertIn("html[data-theme=dark] #serr,html[data-theme=dark] #sfts,html[data-theme=dark] .reqmark{color:#fda4af}", css_site)


if __name__ == "__main__":
    unittest.main()
