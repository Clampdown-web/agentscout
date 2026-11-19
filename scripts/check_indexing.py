#!/usr/bin/env python3
"""Verify indexing hygiene on the built tree (TASK-15, A1/A2/A3/A4/A8).

Run from the repo root after a build: python3 scripts/check_indexing.py
Exits 1 with a summary when any check fails; prints ok lines otherwise.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = "https://agentscouthq.com/"
FAIL = []


def note(ok, msg):
    print(("ok  " if ok else "FAIL") + " " + msg)
    if not ok:
        FAIL.append(msg)


def _host_of(u):
    h = re.sub(r"^https?://", "", str(u or "")).split("/")[0].split("?")[0].lower()
    return h[4:] if h.startswith("www.") else h


def _locs(path):
    return re.findall(r"<loc>([^<]+)</loc>", Path(path).read_text(encoding="utf-8"))


def check_a1():
    locs = _locs(ROOT / "sitemap.xml")
    bad = [u for u in locs if not (u.endswith(".html") or u.endswith("/"))]
    note(not bad, f"A1 sitemap.xml: {len(locs)} locs, all .html or /" + ("" if not bad else f"; bad: {bad[:5]}"))
    return locs


def check_a2():
    pages = sorted((ROOT / "tools").glob("*.html"))
    bad = []
    n = 0
    for p in pages:
        s = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r'<a class="b uc"[^>]*>', s):
            tag = m.group(0)
            if "?uc=" in tag:
                n += 1
                if "nofollow" not in tag or "index.html" in tag:
                    bad.append(f"{p.name}: {tag[:120]}")
    note(not bad, f"A2 use-case chips: {n} ?uc= chips with rel=nofollow, ../?uc= form" + ("" if not bad else f"; bad: {bad[:3]}"))


def check_a3():
    data = json.loads((ROOT / "data" / "sponsored_links.json").read_text())
    tools = {x["slug"]: x for x in json.loads((ROOT / "tools.json").read_text())}
    for slug in data["slugs"]:
        x = tools[slug]
        host = _host_of(x.get("website") or x["url"])
        page = ROOT / "tools" / f"{slug}.html"
        if not page.exists():
            note(False, f"A3 {slug}: tools/{slug}.html missing")
            continue
        s = page.read_text(encoding="utf-8", errors="ignore")
        found = bad = 0
        for m in re.finditer(r'<a\b[^>]*>', s):
            tag = m.group(0)
            hm = re.search(r'href="([^"]+)"', tag)
            if not hm or _host_of(hm.group(1)) != host:
                continue
            found += 1
            if "sponsored" not in tag:
                bad += 1
        note(found > 0 and bad == 0,
             f"A3 {slug}: {found} outbound links to {host}, all rel=sponsored" + ("" if bad == 0 else f"; {bad} missing sponsored"))


def check_a4():
    skip_dirs = {".git", "node_modules", "data", "scripts", "assets", "preview", "app", "pagefind"}
    bad = []
    n = 0
    for dirpath, dirs, fnames in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
        for fn in fnames:
            if not fn.endswith(".html"):
                continue
            p = Path(dirpath) / fn
            s = p.read_text(encoding="utf-8", errors="ignore")
            # Case-insensitive, and the closing tag may carry whitespace. A case-sensitive
            # <script> filter misses <SCRIPT> and is the CodeQL bad-tag-filter alert.
            s = re.sub(r"(?is)<script\b[^>]*>.*?</script\b[^>]*>", "", s)
            s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
            s = re.sub(r'<link[^>]*rel="canonical"[^>]*>', "", s)  # canonicals unchanged by design (A4 is hrefs)
            n += 1
            for m in re.finditer(r'href="([^"]*)"', s):
                u = m.group(1)
                # External absolute URLs (a tool's own site ending in /index.html) are not ours
                if u.startswith(("http://", "https://")) and "agentscouthq.com/" not in u:
                    continue
                path = u.split("?", 1)[0].split("#", 1)[0]
                # index.html must be a whole final segment: tools/pageindex.html is a tool page
                if path == "index.html" or path.endswith("/index.html"):
                    bad.append(f"{p.relative_to(ROOT)}: href=\"{u}\"")
    note(not bad, f"A4 internal hrefs: 0 ending in index.html across {n} pages" + ("" if not bad else f"; {len(bad)} bad, e.g. {bad[:5]}"))


def _file_for(url):
    rel = url[len(B):]
    if not rel:
        return ROOT / "index.html"
    if rel.endswith("/"):
        return ROOT / rel / "index.html"
    return ROOT / rel


def check_a8(sitemap_locs):
    core = _locs(ROOT / "sitemap-core.xml")
    note(150 <= len(core) <= 300, f"A8 sitemap-core.xml: {len(core)} URLs (want 150-300)")
    missing = [u for u in core if u not in set(sitemap_locs)]
    note(not missing, f"A8 core URLs all in sitemap.xml" + ("" if not missing else f"; missing: {missing[:5]}"))
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    note("sitemap-core.xml" in robots, "A8 robots.txt references sitemap-core.xml")
    bad = []
    for u in core:
        f = _file_for(u)
        if not f.exists():
            bad.append(f"{u}: file missing")
            continue
        s = f.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'<link rel="canonical" href="([^"]+)"', s)
        if not m or m.group(1) != u:
            bad.append(f"{u}: canonical is {m.group(1) if m else 'absent'}")
        elif re.search(r'<meta name="robots" content="[^"]*noindex', s):
            bad.append(f"{u}: noindex")
    note(not bad, f"A8 core URLs: 200/self-canonical/indexable spot check ({len(core)} pages)" + ("" if not bad else f"; bad: {bad[:5]}"))


def main():
    locs = check_a1()
    check_a2()
    check_a3()
    check_a4()
    check_a8(locs)
    if FAIL:
        print(f"\n{len(FAIL)} check(s) failed")
        return 1
    print("\nall indexing checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
