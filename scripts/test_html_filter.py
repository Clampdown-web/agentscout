#!/usr/bin/env python3
"""Hidden markup is dropped even when the end tag is spaced or split."""
from __future__ import annotations

import unittest

import content_check
import morning_audit


class HtmlFilterTest(unittest.TestCase):
    def test_script_end_tags_with_space_and_newline(self):
        page = (
            "<p>visible tools</p>"
            "<script>SECRET</script >"
            "<p>still visible</p>"
            "<SCRIPT>HIDDEN</SCRIPT\n>"
            "<p>tail</p>"
            "<style>233</style >"
            "<textarea>&lt;img secret</textarea >"
        )
        text = content_check._visible(page)
        self.assertIn("visible tools", text)
        self.assertIn("still visible", text)
        self.assertIn("tail", text)
        self.assertNotIn("SECRET", text)
        self.assertNotIn("HIDDEN", text)
        self.assertNotIn("233", text)
        self.assertNotIn("&lt;img", text)
        self.assertNotIn("<script", text.lower())

    def test_inline_script_check_stops_at_spaced_end_tags(self):
        page = (
            "<script>var a=1;</script ><p>after</p><SCRIPT>var b=2;</SCRIPT\n>"
            "<script src=\"app.js\"></script>"
            "<script type=\"application/ld+json\">{\"a\":1}</script>"
        )
        found = morning_audit.inline_scripts(page)
        self.assertEqual(found, ["var a=1;", "var b=2;"])
        self.assertNotIn("after", "".join(found))
        self.assertNotIn('{"a":1}', "".join(found))


if __name__ == "__main__":
    unittest.main()
