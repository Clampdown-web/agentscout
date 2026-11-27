#!/usr/bin/env python3
"""Apply data/seo_overrides.json to page <title> and meta tags only.

This is the surgical half of build_seo_new.run(): it writes the hand-written
titles and descriptions onto existing HTML, and it does not run the rest of
that pass (no nav, animation, or llms.txt rewrites).

Use it after a listing-copy rewrite that rebuilds a tool page from the
template, so custom title and meta terms are not wiped. The daily listing
copy cleanup batch should run this, then scripts/lint_seo_terms.py.

  python3 scripts/apply_seo_overrides.py
  python3 scripts/apply_seo_overrides.py tools/sandscale.html
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path

REPO_DEFAULT = Path(__file__).resolve().parents[1]


def _set(s: str, attr: str, name: str, value: str) -> str:
    return re.sub(
        rf'(<meta {re.escape(attr)}="{re.escape(name)}" content=")[^"]*(")',
        lambda m: m.group(1) + value + m.group(2),
        s,
        count=1,
    )


def apply_one(html_s: str, title: str | None, description: str | None) -> str:
    s = html_s
    if title:
        value = html.escape(title, quote=True)
        s = re.sub(r"<title>.*?</title>", f"<title>{value}</title>", s, count=1, flags=re.S)
        s = _set(s, "property", "og:title", value)
        s = _set(s, "name", "twitter:title", value)
    if description:
        value = html.escape(description, quote=True)
        s = _set(s, "name", "description", value)
        s = _set(s, "property", "og:description", value)
        s = _set(s, "name", "twitter:description", value)
    return s


def load_overrides(repo: Path) -> dict[str, list]:
    path = repo / "data" / "seo_overrides.json"
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        return {}
    return data


def apply_paths(repo: Path, paths: list[str] | None = None) -> list[str]:
    """Apply overrides to the given relative paths, or to every existing override path."""
    overrides = load_overrides(repo)
    wanted = set(paths) if paths else None
    changed: list[str] = []
    for rel, pair in overrides.items():
        if wanted is not None and rel not in wanted:
            continue
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            continue
        title, description = pair[0], pair[1]
        target = repo / rel
        if not target.is_file():
            continue
        original = target.read_text()
        updated = apply_one(original, title, description)
        if updated != original:
            target.write_text(updated)
            changed.append(rel)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("REPO", str(REPO_DEFAULT)))
    parser.add_argument("paths", nargs="*", help="Relative HTML paths; default is every override that exists")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    changed = apply_paths(repo, args.paths or None)
    if changed:
        print(f"Applied SEO overrides to {len(changed)} page(s):")
        for path in changed:
            print(f"  {path}")
    else:
        print("SEO overrides already applied; no HTML changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
