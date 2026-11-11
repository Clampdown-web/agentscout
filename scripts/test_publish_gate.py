#!/usr/bin/env python3
"""The Nov 8 deep-audit failures are mixed checks, not a weaker security contract."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT / "scripts"))
import publish_gate

LOG_CATEGORIES = [
    "3D & concept art",
    "DevOps & cloud",
    "HR & recruiting",
    "MCP servers",
    "QA & testing",
    "agent infra",
    "app builders",
    "browser/computer use",
    "business agents",
    "coding",
    "crypto",
    "customer support",
    "data & analytics",
    "e-commerce & retail",
    "education & tutoring",
    "evals & observability",
    "film & TV audio",
    "film & TV production",
    "finance & accounting",
    "frameworks",
    "games",
    "graphic design & branding",
    "healthcare & biotech",
    "image generation",
    "legal & compliance",
    "memory & RAG",
    "models & local runtimes",
    "music production",
    "no-code builders",
    "personal agents",
    "photography & photo editing",
    "productivity",
    "research",
    "robotics & physical AI",
    "sales & marketing",
    "sandboxes & code execution",
    "security & governance",
    "video generation",
    "vision",
    "voice",
    "other",
]

PREPARED_STATE = {
    "tools": 2366,
    "mcp": 320,
    "pages": 2992,
    "bot_templates": 190,
    "free_tools": 21,
    "date": "2026-11-08",
    "script_mtime": 1794149813,
}


class PreflightTest(unittest.TestCase):
    def test_missing_origin_403_is_the_contract(self):
        self.assertEqual(publish_gate.preflight_problems(403, origin_present=False), [])

    def test_allowed_origin_204_is_the_contract(self):
        self.assertEqual(publish_gate.preflight_problems(204, origin_present=True), [])

    def test_a_success_without_origin_is_a_failure(self):
        problems = publish_gate.preflight_problems(204, origin_present=False)
        self.assertEqual(problems, ["OPTIONS without Origin returned 204, expected 403"])

    def test_a_forbidden_allowed_origin_is_a_failure(self):
        problems = publish_gate.preflight_problems(403, origin_present=True)
        self.assertEqual(len(problems), 1)


class CategoryTest(unittest.TestCase):
    def test_uniform_turnstile_rejections_are_not_category_defects(self):
        responses = [(name, "Bot check failed.") for name in LOG_CATEGORIES]
        self.assertEqual(publish_gate.category_probe_problems(responses), [])

    def test_a_different_category_body_is_still_reported(self):
        responses = [("coding", "Bot check failed."), ("other", "Unknown category.")]
        self.assertEqual(publish_gate.category_probe_problems(responses), ["other: Unknown category."])

    def test_local_acceptance_uses_the_catalog_and_does_not_include_a_bypass(self):
        catalog = json.loads((ROOT / "categories.json").read_text(encoding="utf-8"))
        self.assertEqual(catalog, LOG_CATEGORIES)
        self.assertEqual(publish_gate.category_names_problems(catalog, catalog), [])
        self.assertIs(publish_gate.category_accepted("coding", catalog), True)
        self.assertIs(publish_gate.category_accepted("not-a-category", catalog), False)
        source = (ROOT / "scripts" / "publish_gate.py").read_text(encoding="utf-8")
        self.assertNotIn("TURNSTILE_ENABLED", source)
        self.assertNotIn("urllib", source)


class PackagesTest(unittest.TestCase):
    def test_live_shape_without_a_pages_string_matches_the_product_file(self):
        document = json.loads((ROOT / "api" / "products.json").read_text(encoding="utf-8"))
        rows = []
        for key in publish_gate.PRODUCT_GROUPS:
            rows.extend(document[key])
        # 39 after retiring the 10-bot pack, the 20-bot pack, and the standalone Directory Launch Pack.
        self.assertEqual(len(rows), 39)
        live = {"total_products": 39, "products": rows}
        self.assertIsNone(live.get("pages"))
        self.assertEqual(publish_gate.list_packages_problems(200, live, stale=[]), [])
        self.assertEqual(publish_gate.product_snapshot_problems(ROOT), [])

    def test_a_short_product_or_a_stale_token_fails(self):
        short = {"total_products": 1, "products": [{"id": "x", "name": "X"}]}
        self.assertIn("x is missing price_usd", publish_gate.product_catalog_problems(short))
        stale = publish_gate.list_packages_problems(200, {"products": [{"id": "x", "name": "X", "price_usd": 0}]}, ["old-count"])
        self.assertIn("list_packages stale tokens: old-count", stale)

    def test_a_non_200_fails_closed(self):
        self.assertEqual(publish_gate.list_packages_problems(500, {"products": []}), ["list_packages HTTP 500"])

    def test_duplicate_id_and_total_mismatch_fail(self):
        row = {"id": "same", "name": "One", "price_usd": 0}
        duplicate = {"total_products": 2, "products": [row, dict(row)]}
        problems = publish_gate.product_catalog_problems(duplicate)
        self.assertIn("duplicate product id same", problems)
        mismatch = {"total_products": 9, "products": [row]}
        self.assertIn("total_products is 9, product rows are 1", publish_gate.product_catalog_problems(mismatch))

    def test_invalid_product_json_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "api").mkdir()
            (root / "cloudflare-mcp-worker").mkdir()
            (root / "api" / "products.json").write_text("{", encoding="utf-8")
            (root / "cloudflare-mcp-worker" / "products_snapshot.json").write_text("{", encoding="utf-8")
            problems = publish_gate.product_snapshot_problems(root)
            self.assertTrue(any("not valid JSON" in item for item in problems))

    def test_inner_submit_accepts_a_known_category_without_storing_it(self):
        catalog = ["coding", "other"]
        pricing = ["Free", "Paid"]
        self.assertEqual(
            publish_gate.inner_submit_decision("coding", "__audit_invalid__", catalog, pricing),
            publish_gate.PRICING_REJECTION,
        )
        self.assertEqual(
            publish_gate.inner_submit_decision("nope", "__audit_invalid__", catalog, pricing),
            publish_gate.CATEGORY_REJECTION,
        )
        self.assertIsNone(publish_gate.inner_submit_decision("coding", "Free", catalog, pricing))


class AnimationTest(unittest.TestCase):
    def test_the_morning_live_token_is_not_a_defect_in_the_newer_artifact(self):
        local = publish_gate.animation_token(PREPARED_STATE)
        self.assertEqual(local, "20261108-2366")
        self.assertNotEqual(local, "20261108-2325")
        defect = publish_gate.animation_live_token_is_artifact_defect(PREPARED_STATE, 2325, pages_contain_live_token=False)
        self.assertIs(defect, False)
        pages = {name: f'<source src="assets/animations/clip.mp4?v={local}">' for name in ("index.html", "bot-store/index.html", "videos/index.html")}
        self.assertEqual(publish_gate.animation_predeploy_problems(PREPARED_STATE, pages, 2366, 320), [])

    def test_a_stamp_that_disagrees_with_the_artifact_fails(self):
        pages = {"index.html": '<source src="assets/animations/clip.mp4?v=20261108-2325">'}
        problems = publish_gate.animation_predeploy_problems(PREPARED_STATE, pages, 2366, 320)
        self.assertIn("index.html is missing the artifact cache buster ?v=20261108-2366", problems)

    def test_same_count_missing_from_the_page_is_a_defect(self):
        state = {"tools": 2325, "mcp": 311, "date": "2026-11-08"}
        self.assertIs(publish_gate.animation_live_token_is_artifact_defect(state, 2325, False), True)

    def test_committed_tree_matches_its_own_stamp(self):
        self.assertEqual(publish_gate.artifact_animation_problems(ROOT), [])


if __name__ == "__main__":
    unittest.main()
