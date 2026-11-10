#!/usr/bin/env python3
"""Submit-form listings always carry maker_submitted and a Pacific submitted date.

"Submission" and "Maker submission" (any case) are the submit form. The importer
stamps both fields for those sources without a separate flag. A catalog_only
import cannot be a maker submission. The build check fails when a submit-form
source is missing the flag.
"""
from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import add_tools  # noqa: E402
import build_recent  # noqa: E402
import maker_flag  # noqa: E402

import atexit
import build_extras

# Importing the page builder registers exit hooks that rewrite sitemap and lastmod.
atexit.unregister(build_extras._apply_featured)
atexit.unregister(build_extras._pf_last)


class MakerFlagTest(unittest.TestCase):
    def test_importer_stamps_a_submission_source_without_the_cli_flag(self):
        src = (ROOT / "scripts" / "add_tools.py").read_text(encoding="utf-8")
        self.assertIn("--maker-submitted", src)
        self.assertIn("listing_flags(e)", src)
        self.assertIn("guard_import_flags()", src)
        self.assertIn("elif MAKER or is_submission_source(SOURCE):", src)
        self.assertIn("stamp_new(e)", src)
        self.assertIn("catalog-only imports are not submit-form listings", src)
        self.assertLess(src.index("if CATALOG_ONLY:"), src.index("elif MAKER or is_submission_source(SOURCE):"))
        site = (ROOT / "build_site.py").read_text(encoding="utf-8")
        self.assertIn("from maker_flag import check as _maker_check", site)
        self.assertIn("_maker_check(t)", site)
        recent = (ROOT / "build_recent.py").read_text(encoding="utf-8")
        self.assertIn("_maker_check(t)", recent)
        self.assertIn("makers_section(t)", recent)

    def test_stamp_uses_the_source_for_every_submit_form_label(self):
        saved = (add_tools.SOURCE, add_tools.MAKER, add_tools.CATALOG_ONLY)
        try:
            add_tools.MAKER = False
            add_tools.CATALOG_ONLY = False
            for source in ("Submission", "Maker submission", "maker submission", "  SUBMISSION  "):
                add_tools.SOURCE = source
                entry = {"name": "Example"}
                add_tools.listing_flags(entry)
                self.assertTrue(entry["maker_submitted"], source)
                self.assertRegex(entry["submitted"], r"^\d{4}-\d{2}-\d{2}$")
            for source in ("GitHub", "Owner request", "Newsletter", "Research (art, design, 3D & photo sweep)"):
                add_tools.SOURCE = source
                add_tools.MAKER = False
                entry = {"name": "Example"}
                add_tools.listing_flags(entry)
                self.assertNotIn("maker_submitted", entry, source)
            add_tools.SOURCE = "GitHub"
            add_tools.MAKER = True
            entry = {}
            add_tools.listing_flags(entry)
            self.assertTrue(entry["maker_submitted"])
            self.assertRegex(entry["submitted"], r"^\d{4}-\d{2}-\d{2}$")
            kept = {"submitted": "2026-10-18"}
            maker_flag.stamp_new(kept, today="2026-11-10")
            self.assertEqual(kept["submitted"], "2026-10-18")
        finally:
            add_tools.SOURCE, add_tools.MAKER, add_tools.CATALOG_ONLY = saved

    def test_catalog_only_cannot_be_a_submit_form_import(self):
        saved = (add_tools.SOURCE, add_tools.MAKER, add_tools.CATALOG_ONLY)
        try:
            add_tools.CATALOG_ONLY = True
            add_tools.MAKER = False
            add_tools.SOURCE = "Submission"
            with self.assertRaises(SystemExit):
                add_tools.guard_import_flags()
            entry = {}
            add_tools.listing_flags(entry)
            self.assertTrue(entry.get("catalog_only"))
            self.assertNotIn("maker_submitted", entry)
            add_tools.SOURCE = "GitHub"
            add_tools.MAKER = True
            with self.assertRaises(SystemExit):
                add_tools.guard_import_flags()
        finally:
            add_tools.SOURCE, add_tools.MAKER, add_tools.CATALOG_ONLY = saved

    def test_backfill_sets_only_the_two_fields(self):
        row = {"slug": "example", "name": "Example", "source": "Maker submission", "added": "2026-10-23", "pricing": "Free"}
        self.assertTrue(maker_flag.backfill_row(row))
        self.assertEqual(row["maker_submitted"], True)
        self.assertEqual(row["submitted"], "2026-10-23")
        self.assertEqual(row["pricing"], "Free")
        self.assertFalse(maker_flag.backfill_row(row))
        dated = {"slug": "kept", "source": "Submission", "added": "2026-10-20", "maker_submitted": True, "submitted": "2026-10-19"}
        self.assertFalse(maker_flag.backfill_row(dated))
        self.assertEqual(dated["submitted"], "2026-10-19")
        self.assertFalse(maker_flag.backfill_row({"source": "Owner request", "added": "2026-10-20"}))

    def test_check_fails_loud_when_a_submission_source_lacks_the_flag(self):
        good = [{"slug": "ok", "source": "Submission", "maker_submitted": True, "submitted": "2026-11-01"}]
        self.assertEqual(maker_flag.problems(good), [])
        missing = [{"slug": "bare", "source": "maker submission", "added": "2026-11-04"}]
        self.assertTrue(any("bare" in line and "maker_submitted" in line for line in maker_flag.problems(missing)))
        err = io.StringIO()
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(err):
                maker_flag.check(missing)
        self.assertIn("MAKER FLAG CHECK FAILED", err.getvalue())
        self.assertIn("bare", err.getvalue())
        both = [{"slug": "nope", "source": "Submission", "catalog_only": True, "maker_submitted": True, "submitted": "2026-11-01"}]
        text = " ".join(maker_flag.problems(both))
        self.assertIn("catalog_only", text)

    def test_live_rows_keep_catalog_only_and_maker_flags_apart(self):
        tools = json.loads((ROOT / "tools.json").read_text(encoding="utf-8"))
        self.assertEqual(maker_flag.problems(tools), [])
        flagged = [row for row in tools if row.get("maker_submitted")]
        submit = [row for row in tools if maker_flag.is_submission_source(row.get("source"))]
        self.assertTrue(flagged)
        self.assertEqual(len(submit), len(flagged))
        self.assertGreater(len(flagged), 99)
        by = {row["slug"]: row for row in tools}
        for slug in ("diri-ai", "fileaify", "talynce", "botsee", "xmcp", "inkroom", "aifetchly"):
            self.assertTrue(by[slug].get("maker_submitted"), slug)
            self.assertEqual(by[slug]["submitted"], by[slug]["added"], slug)
        # An earlier listing kept its original submitted day when that differed from added.
        self.assertEqual(by["robylon"]["submitted"], "2026-10-19")
        self.assertEqual(by["robylon"]["added"], "2026-10-20")
        self.assertFalse(any(row.get("maker_submitted") for row in tools if row.get("source") == "Owner request"))

    def test_new_page_count_comes_from_the_rows_and_pages_the_rest(self):
        rows = []
        for i in range(30):
            day = f"2026-10-{(i % 27) + 1:02d}"
            rows.append({
                "slug": f"m{i}",
                "name": f"Maker {i}",
                "description": "A tool sent through the submit form.",
                "added": day,
                "submitted": day,
                "id": i,
                "maker_submitted": True,
                "logo": "assets/logos/orke.png",
            })
        html = build_recent.makers_section(rows)
        self.assertIn('>Submitted by makers <span class="muted">· 30 tools</span>', html)
        self.assertNotIn("99 tools", html)
        self.assertEqual(html.count('class="card rcard mk-rest"'), 30 - build_recent.MAKER_PAGE)
        self.assertEqual(html.count('class="card rcard"'), build_recent.MAKER_PAGE)
        self.assertIn('id="makers-more"', html)
        self.assertIn("Show 18 more", html)
        one = build_recent.makers_section(rows[:1])
        self.assertIn("· 1 tool</span>", one)
        self.assertNotIn("makers-more", one)


if __name__ == "__main__":
    unittest.main()
