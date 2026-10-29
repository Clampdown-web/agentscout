#!/usr/bin/env python3
"""Fail when any page's sitewide <nav> or <footer> differs from index.html.

Relative link depth (../ and root-absolute /) is ignored. Meta-refresh stubs,
drafts, and pages without a chrome pair are skipped the same way as
build_seo_new.unify_all_nav_and_footer.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import build_seo_new

if __name__ == "__main__":
    sys.exit(1 if build_seo_new.verify_nav_footer_unified() else 0)
