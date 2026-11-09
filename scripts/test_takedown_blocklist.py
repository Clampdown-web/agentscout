#!/usr/bin/env python3
"""Hindsight stays blocked after the Oct 26 removal request."""
import unittest

from takedown_blocklist import blocked


class TakedownBlocklistTest(unittest.TestCase):
    def test_hindsight_is_blocked_by_slug_name_domain_and_repo(self):
        self.assertTrue(blocked(slug="hindsight"))
        self.assertTrue(blocked(name="Hindsight"))
        self.assertTrue(blocked(url="https://hindsight.vectorize.io/"))
        self.assertTrue(blocked(website="https://www.hindsight.vectorize.io/docs"))
        self.assertTrue(blocked(repo="vectorize-io/hindsight"))
        self.assertTrue(blocked(repo="https://github.com/vectorize-io/hindsight"))
        self.assertFalse(blocked(name="Hindsight AI Notes"))
        self.assertFalse(blocked(slug="hindsight-notes"))
        self.assertFalse(blocked(repo="someone/not-hindsight"))

    def test_hedra_still_blocked(self):
        self.assertTrue(blocked(slug="hedra"))
        self.assertTrue(blocked(url="https://hedra.com/"))


if __name__ == "__main__":
    unittest.main()
