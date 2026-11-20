#!/usr/bin/env python3
"""Indexing hygiene: rel=sponsored for paid placements (TASK-15, A3).

For every slug in data/sponsored_links.json, outbound links to the tool's own
host must carry rel="sponsored". Pure-function tests; no build needed.
Run: python3 scripts/test_sponsored_links.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_extras as X


def _page(slug, url, host):
    return (
        f'<a class="btn primary" href="{url}" target="_blank" rel="noopener noreferrer">Visit {host} \u2197</a>'
        f'<p>Official site: <a href="https://{host}/" target="_blank" rel="noopener noreferrer">{host}</a>.</p>'
        f'<p>Pricing: <a href="https://{host}/pricing" target="_blank" rel="noopener noreferrer">official pricing page</a>.</p>'
        f'<p>Code: <a href="https://github.com/example/{slug}" target="_blank" rel="noopener noreferrer">GitHub</a>.</p>'
        f'<p>Video: <a href="https://{host}/demo.mp4" target="_blank" rel="nofollow noopener noreferrer">Watch the demo</a>.</p>'
    )


def main():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "data" / "sponsored_links.json").read_text())
    slugs = data.get("slugs") or []
    assert slugs, "data/sponsored_links.json has no slugs"
    assert len(slugs) == len(set(slugs)), "duplicate slugs in data/sponsored_links.json"
    tools = {x["slug"]: x for x in json.loads((root / "tools.json").read_text())}
    for slug in slugs:
        assert slug in tools, f"sponsored slug {slug} is not in tools.json"
        host = re.sub(r"^https?://(www\.)?", "", tools[slug]["url"]).split("/")[0]
        html = _page(slug, tools[slug]["url"], host)
        out = X.sponsored_rel(html, slug, host)
        sponsored = re.findall(r'rel="sponsored nofollow noopener noreferrer"', out)
        assert len(sponsored) == 3, (
            f"{slug}: expected 3 sponsored links (Visit, Official site, pricing), got {len(sponsored)}"
        )
        assert 'href="https://github.com/example/' in out and 'rel="noopener noreferrer">GitHub' in out, (
            f"{slug}: non-tool-host link was rewritten"
        )
        assert 'rel="nofollow noopener noreferrer">Watch the demo' in out, (
            f"{slug}: non-Visit rel was rewritten"
        )
        assert X.visit_rel(slug) == "sponsored nofollow noopener noreferrer", f"{slug}: visit_rel wrong"
        # www-insensitive host match: pricing on the bare host still counts
        bare = host[4:] if host.startswith("www.") else "www." + host
        out2 = X.sponsored_rel(
            f'<a href="https://{bare}/pricing" target="_blank" rel="noopener noreferrer">pricing</a>',
            slug, host,
        )
        assert "sponsored" in out2, f"{slug}: www-insensitive host match failed"
    # Unlisted slugs are untouched, and a missing/empty host is a no-op.
    sample = _page("cursor", "https://cursor.com/", "cursor.com")
    assert X.sponsored_rel(sample, "cursor", "cursor.com") == sample
    assert X.sponsored_rel(sample, "botpress", "") == sample
    assert X.visit_rel("cursor") == "noopener noreferrer"
    print(f"sponsored links ok: {len(slugs)} slugs ({', '.join(slugs)})")


if __name__ == "__main__":
    main()
