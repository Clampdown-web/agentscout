#!/usr/bin/env python3
"""Submit-form listings get maker_submitted only when the importer says so.

The source string is not proof. A catalog_only import cannot also be a maker
submission. Rows that already carry the flag need a Pacific submitted date.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MakerFlagTest(unittest.TestCase):
    def test_importer_sets_the_flag_only_for_an_explicit_submit(self):
        src = (ROOT / "scripts" / "add_tools.py").read_text(encoding="utf-8")
        self.assertIn('--maker-submitted', src)
        self.assertIn('e["maker_submitted"]=True', src)
        self.assertIn("catalog-only imports are not submit-form listings", src)
        self.assertLess(src.index("if CATALOG_ONLY:"), src.index("elif MAKER:"))

    def test_live_rows_keep_catalog_only_and_maker_flags_apart(self):
        tools = json.loads((ROOT / "tools.json").read_text(encoding="utf-8"))
        flagged = [row for row in tools if row.get("maker_submitted")]
        self.assertTrue(flagged)
        for row in tools:
            if row.get("catalog_only"):
                self.assertFalse(row.get("maker_submitted"), row.get("slug"))
            if row.get("maker_submitted"):
                self.assertRegex(row.get("submitted") or "", r"^\d{4}-\d{2}-\d{2}$", row.get("slug"))
        # The source string alone does not decide the flag. Research batches use it too.
        source_like = [row for row in tools if re.search(r"submission", row.get("source") or "", re.I)]
        self.assertGreater(len(source_like), len(flagged))


if __name__ == "__main__":
    unittest.main()
