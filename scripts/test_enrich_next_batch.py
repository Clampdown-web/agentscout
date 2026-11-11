#!/usr/bin/env python3
"""Next enrichment batch: 20 thin tool pages, 5 of them indexable.

Ranking used GitHub stars on the listing (checked against data/github.json
where that snapshot has the repo). Leaderboard loved-rank was a tie-break.
No per-page Search Console export is in the repo. Pages already enriched,
including the PR #52 guides and the four clicked pages from PR #69, are not
in this batch.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import index_hold
INDEXABLE = (
    "ponytail",
    "ui-ux-pro-max",
    "caveman",
    "agent-skills-addy-osmani",
    "taste-skill",
)
HELD = (
    "impeccable",
    "archify",
    "oh-my-openagent-omo",
    "claude-code-templates",
    "chat2db",
    "hypit",
    "cube",
    "kortix-companyos",
    "toonflow-app",
    "img2threejs",
    "iii",
    "windmill",
    "a2ui",
    "dagger",
    "zvec",
)
FIELDS = ("long", "who", "features", "pros", "cons", "setup", "sources")


class EnrichNextBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rich = json.loads((ROOT / "tool_rich.json").read_text(encoding="utf-8"))
        cls.hold = json.loads((ROOT / "data" / "index_hold.json").read_text(encoding="utf-8"))
        cls.rule = (ROOT / "build_site.py").read_text(encoding="utf-8")
        cls.tools = {x["slug"]: x for x in json.loads((ROOT / "tools.json").read_text(encoding="utf-8"))}
        cls.sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")

    def test_cap_and_threshold_stay(self):
        self.assertIn("NEW_TOOL_CAP=15", self.rule)
        self.assertIn("THIN_WORDS=80", self.rule)
        self.assertIn("if enr or (not thin and (grandfather or slug in slots)):", self.rule)
        self.assertLess(
            self.rule.index('if x.get("catalog_only"):'),
            self.rule.index("if enr or (not thin and (grandfather or slug in slots)):"),
        )
        self.assertIn('not by[s].get("catalog_only")', self.rule)
        self.assertIn("data/index_hold.json", self.rule)

    def test_hold_list_is_the_fifteen_on_dated_batches(self):
        self.assertEqual(list(self.hold["indexable_now"]), list(INDEXABLE))
        releases = self.hold["releases"]
        self.assertEqual([b["date"] for b in releases[:3]], ["2026-11-10", "2026-11-11", "2026-11-12"])
        flat = [s for b in releases[:3] for s in b["slugs"]]
        self.assertEqual(flat, list(HELD))
        for batch in releases:
            self.assertLessEqual(len(batch["slugs"]), 15)
        for slug in INDEXABLE:
            self.assertNotIn(slug, flat)

    def test_every_record_cites_a_source_and_does_not_reuse_the_dropped_hypit_prices(self):
        for slug in INDEXABLE + HELD:
            record = self.rich[slug]
            self.assertEqual(record.get("kind"), "lite", slug)
            self.assertTrue(record.get("show_alts"), slug)
            for field in FIELDS:
                self.assertTrue(record.get(field), slug + " " + field)
            self.assertTrue(record.get("sources"), slug)
            blob = json.dumps(record)
            self.assertNotIn("9.90", blob, slug)
            self.assertNotIn("39.90", blob, slug)
            self.assertNotIn("99.90", blob, slug)

    def test_hypit_catalog_no_longer_states_the_unverified_tiers(self):
        detail = self.tools["hypit"].get("pricing_detail") or ""
        self.assertNotIn("9.90", detail)
        self.assertNotIn("Starter", detail)

    def test_indexable_five_are_in_the_sitemap_and_the_hold_stays_out(self):
        for slug in INDEXABLE:
            page = (ROOT / "tools" / f"{slug}.html").read_text(encoding="utf-8")
            head = page[:2500]
            self.assertNotIn('name="robots" content="noindex', head, slug)
            self.assertIn(f'rel="canonical" href="https://agentscouthq.com/tools/{slug}.html"', page)
            self.assertIn("FAQPage", page, slug)
            self.assertIn("alternatives</h2>", page, slug)
            self.assertIn(f"https://agentscouthq.com/tools/{slug}.html", self.sitemap)
            self.assertIn('if(typeof AS!=="undefined"&&AS.saveBtn)', page, slug)
        released = set(json.loads((ROOT / "data" / "index_admit.json").read_text(encoding="utf-8")).get("hold_released_slugs") or [])
        for slug in HELD:
            page = (ROOT / "tools" / f"{slug}.html").read_text(encoding="utf-8")
            self.assertIn(f'rel="canonical" href="https://agentscouthq.com/tools/{slug}.html"', page)
            self.assertIn("FAQPage", page, slug)
            loc = f"https://agentscouthq.com/tools/{slug}.html"
            if slug in released:
                self.assertNotIn('name="robots" content="noindex', page[:2500], slug)
                self.assertIn(loc, self.sitemap, slug)
            else:
                self.assertIn('name="robots" content="noindex,follow"', page[:2500], slug)
                self.assertNotIn(loc, self.sitemap, slug)


class HoldReleaseTests(unittest.TestCase):
    def schedule(self):
        return json.loads((ROOT / "data" / "index_hold.json").read_text(encoding="utf-8"))

    def _slugs(self):
        return [s for b in self.schedule()["releases"] for s in b["slugs"]]

    def test_nothing_releases_before_nov_10(self):
        state = {}
        held = index_hold.held_slugs("2026-11-09", self.schedule(), state, 5)
        self.assertEqual(held, set(self._slugs()))
        self.assertNotIn("hold_release_day", state)

    def test_nov_10_releases_only_the_first_batch(self):
        state = {}
        slugs = self._slugs()
        held = index_hold.held_slugs("2026-11-10", self.schedule(), state, 5)
        self.assertEqual(state["hold_release_day"], "2026-11-10")
        self.assertEqual(state["hold_released"], ["2026-11-10"])
        released = set(state["hold_released_slugs"])
        self.assertEqual(released, set(slugs[:5]))
        self.assertEqual(held, set(slugs[5:]))
        again = index_hold.held_slugs("2026-11-10", self.schedule(), state, 5)
        self.assertEqual(again, held)
        self.assertEqual(state["hold_released"], ["2026-11-10"])

    def test_a_later_build_releases_one_overdue_batch_per_day(self):
        state = {}
        slugs = self._slugs()
        held = index_hold.held_slugs("2026-11-12", self.schedule(), state, 5)
        self.assertEqual(set(state["hold_released_slugs"]), set(slugs[:5]))
        self.assertEqual(held, set(slugs[5:]))
        held = index_hold.held_slugs("2026-11-13", self.schedule(), state, 5)
        self.assertEqual(set(state["hold_released_slugs"]), set(slugs[:10]))
        self.assertEqual(held, set(slugs[10:]))
        released = 10
        day = 14
        while released < len(slugs):
            held = index_hold.held_slugs(f"2026-11-{day:02d}", self.schedule(), state, 5)
            released = min(released + 5, len(slugs))
            self.assertEqual(set(state["hold_released_slugs"]), set(slugs[:released]))
            self.assertEqual(held, set(slugs[released:]))
            day += 1
        held = index_hold.held_slugs(f"2026-11-{day:02d}", self.schedule(), state, 5)
        self.assertEqual(held, set())

    def test_the_rule_uses_the_dated_hold_and_keeps_the_cap(self):
        rule = (ROOT / "build_site.py").read_text(encoding="utf-8")
        self.assertIn("held=_ih.held_slugs(today, _hold, state, NEW_TOOL_CAP)", rule)
        self.assertIn("NEW_TOOL_CAP=15", rule)


if __name__ == "__main__":
    unittest.main()
