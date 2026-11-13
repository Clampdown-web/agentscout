#!/usr/bin/env python3
"""Category chips must size to one line of label, including homepage tool rows."""
from __future__ import annotations

import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CategoryChipCssTest(unittest.TestCase):
    def test_homepage_and_shared_chip_rules(self):
        styles = open(os.path.join(ROOT, "styles.css"), encoding="utf-8").read()
        home = open(os.path.join(ROOT, "home-mobile.css"), encoding="utf-8").read()
        for name, text in (("styles.css", styles), ("home-mobile.css", home)):
            self.assertIn(
                "body.home #mcp-rows .mtool .b,body.home .hsec .mtool .b{grid-column:2",
                text,
                f"{name} must place homepage category chips in the text column",
            )
            self.assertIn(
                "width:max-content;max-width:100%;white-space:nowrap",
                text,
                f"{name} must size homepage category chips to one line",
            )
        self.assertIn(".b.cat,.b.has-cico{display:inline-flex", styles)
        self.assertIn(
            "#list .badges .b.cat,#list .badges .b.has-cico{white-space:nowrap",
            styles,
        )


if __name__ == "__main__":
    unittest.main()
