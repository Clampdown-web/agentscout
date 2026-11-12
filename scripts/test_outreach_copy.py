#!/usr/bin/env python3
"""Maker email, outreach, and briefing copy stays on the current facts.

Bot Store packs in that copy are 1 for $35, 5 for $119, and all 25 for $349.
AgentScout videos are 30 fps, so outgoing copy does not claim 60 fps.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import agent_pack_catalog  # noqa: E402
import render_maker_listed_email  # noqa: E402

COPY_FILES = (
    "scripts/render_maker_listed_email.py",
    "data/outreach/25-agent-packs-email.html",
    "data/outreach/25-agent-packs-x-posts.md",
    "data/outreach/paid-listing-confirmation.html",
    "llms.txt",
    "llms-full.txt",
    "build_tasks.py",
    "build_seo.py",
    "build_aeo.py",
    "build_seo_new.py",
    "build_bot_store.py",
    "build_bot_templates.py",
    "bot-store/index.html",
    "bot-templates/index.html",
    "index.html",
)

STALE_FPS = ("60fps", "60 fps", "60-fps", "60FPS")
RETIRED_PACKS = ("10-bot", "20-bot", "10 bots", "20 bots", "10 Bots", "20 Bots", "$199", "$299")


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _hit(body: str, needle: str) -> str:
    idx = body.find(needle)
    if idx < 0:
        return ""
    return body[max(0, idx - 60): idx + len(needle) + 60].replace("\n", " ")


class OutreachCopyTest(unittest.TestCase):
    def test_pack_ladder_is_one_five_and_all_25(self):
        tiers = agent_pack_catalog.PACK_TIERS
        self.assertEqual(set(tiers), {"tier_1", "tier_5", "tier_25"})
        self.assertEqual((tiers["tier_1"]["count"], tiers["tier_1"]["price"]), (1, 35))
        self.assertEqual((tiers["tier_5"]["count"], tiers["tier_5"]["price"]), (5, 119))
        self.assertEqual((tiers["tier_25"]["count"], tiers["tier_25"]["price"]), (25, 349))

    def test_maker_email_offers_only_the_current_packs(self):
        html = render_maker_listed_email.email_html()
        posts = render_maker_listed_email.x_posts()
        fixture = _text("data/outreach/25-agent-packs-email.html")
        for name, body in (("email", html), ("posts", posts), ("fixture", fixture)):
            self.assertIn("$35", body)
            self.assertIn("$119", body)
            self.assertIn("$349", body)
            for stale in STALE_FPS + RETIRED_PACKS:
                snippet = _hit(body, stale)
                self.assertFalse(snippet, f"{name} still says {stale}: {snippet}")
        self.assertIn(agent_pack_catalog.PACK_TIERS["tier_1"]["url"], html)
        self.assertIn(agent_pack_catalog.PACK_TIERS["tier_5"]["url"], html)
        self.assertIn(agent_pack_catalog.PACK_TIERS["tier_25"]["url"], html)
        self.assertIn("$15 Fast-Track", _text("data/outreach/paid-listing-confirmation.html"))

    def test_briefing_and_pitch_copy_does_not_claim_60fps(self):
        for rel in COPY_FILES:
            body = _text(rel)
            for stale in STALE_FPS:
                snippet = _hit(body, stale)
                self.assertFalse(snippet, f"{rel} still says {stale}: {snippet}")
        self.assertIn("8 playable 30 fps walkthroughs", _text("llms.txt"))
        self.assertIn("daily stack demos", _text("build_tasks.py"))
        videos = _text("videos/index.html")
        self.assertIn("daily stack demos", videos)
        self.assertFalse(_hit(videos, "60fps"), _hit(videos, "60fps"))


if __name__ == "__main__":
    unittest.main()
