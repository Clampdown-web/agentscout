#!/usr/bin/env python3
"""The newsletter is Wednesday. A built page must not still say Tuesday.

News dates such as 'Tuesday, November 18, 2026' are fine. This fails on the
maker-brief and 'every Tuesday' signup lines.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "node_modules", "pagefind", "preview", "bot-packages", "scripts", "data"}
# Newsletter wording. A weekday heading in the news list does not match.
TUESDAY_NEWS = re.compile(
    r"Tuesday maker brief|every Tuesday|Newsletter, every Tuesday|want the Tuesday",
    re.I,
)


class NewsletterWednesdayTest(unittest.TestCase):
    def test_built_pages_do_not_say_tuesday_newsletter(self):
        hits = []
        for path in ROOT.rglob("*.html"):
            rel = path.relative_to(ROOT)
            if rel.parts and rel.parts[0] in SKIP:
                continue
            if rel.parts[:1] == ("news",) or (len(rel.parts) > 1 and rel.parts[0] == "news"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if TUESDAY_NEWS.search(text):
                hits.append(rel.as_posix())
        self.assertEqual(hits, [], "Tuesday newsletter wording:\n" + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
