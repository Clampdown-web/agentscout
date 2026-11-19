#!/usr/bin/env python3
"""Verify indexing content on the built tree (TASK-16, A5/A6).

Run from the repo root after a build: python3 scripts/check_indexing_content.py
Exits 1 with a summary when any check fails; prints ok lines otherwise.

A5 metric (shared main-content text): for every indexed tool page (<loc> under /tools/ in
sitemap.xml), take the visible text inside <main> (scripts and textareas stripped), split
it into word trigrams, and count the share of each page's trigrams that appear in >=50%
of the pages. The reported number is the median share. Baseline on the pre-change tree:
37.4% on a 200-page sample (the brief's "about 41%" was measured by the delegator under
an unspecified method; this trigram definition is the closest reproducible one).
Target: <= 30%.
"""
import html as _html
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = "https://agentscouthq.com/"
FAIL = []
sys.path.insert(0, str(ROOT))


def note(ok, msg):
    print(("ok  " if ok else "FAIL") + " " + msg)
    if not ok:
        FAIL.append(msg)


def _main_html(s):
    m = re.search(r"<main\b[^>]*>(.*?)</main>", s, flags=re.S)
    return m.group(1) if m else ""


def _main_text(s):
    t = _main_html(s)
    t = re.sub(r"<script\b.*?</script>", " ", t, flags=re.S)
    t = re.sub(r"<textarea\b.*?</textarea>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return _html.unescape(t)


def _toks(t):
    return re.findall(r"[a-z0-9']+", t.lower())


def _sample_tool_pages():
    locs = re.findall(r"<loc>([^<]+)</loc>", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))
    tools = [u for u in locs if "/tools/" in u]
    pages = []
    for u in tools:
        p = ROOT / u[len(B):]
        if p.exists():
            pages.append(p)
    return pages


def check_a5_shared():
    pages = _sample_tool_pages()
    toks = []
    for p in pages:
        toks.append(_toks(_main_text(p.read_text(encoding="utf-8", errors="ignore"))))
    n = len(toks)
    df = Counter()
    page_tri = []
    for tk in toks:
        tri = {" ".join(tk[i:i + 3]) for i in range(max(0, len(tk) - 2))}
        page_tri.append(tri)
        for t in tri:
            df[t] += 1
    shared = {t for t, c in df.items() if c >= n // 2}
    fracs = [len(tri & shared) / len(tri) if tri else 0 for tri in page_tri]
    med = statistics.median(fracs) * 100 if fracs else 0
    note(med <= 30.0, f"A5 shared main-content: median {med:.1f}% over {n} tool pages (want <= 30%)")
    return med


def check_a5_badge_note():
    pages = _sample_tool_pages()
    bad_badge = bad_note = missing_badge = missing_note = 0
    for p in pages:
        s = p.read_text(encoding="utf-8", errors="ignore")
        main = _main_html(s)
        if "Get your badge" not in s:
            missing_badge += 1
        elif "Get your badge" in main:
            bad_badge += 1
        if "Star ratings count right away" not in s:
            missing_note += 1
        elif "Star ratings count right away" in main:
            bad_note += 1
    note(not bad_badge and not missing_badge,
         f"A5 badge block: {len(pages)} indexed tool pages, {bad_badge} with 'Get your badge' inside <main>, "
         f"{missing_badge} missing it" + ("" if not bad_badge and not missing_badge else ""))
    note(not bad_note and not missing_note,
         f"A5 review disclaimer: {bad_note} with the rv-note inside <main>, {missing_note} missing it")


def _list_pages():
    dirs = ("best", "tasks", "compare", "for", "s", "free-tools")
    pages = []
    for d in dirs:
        pages += sorted((ROOT / d).glob("*.html"))
    pages += [ROOT / "free-tools.html", ROOT / "new.html"]
    return [p for p in pages if p.exists()]


def check_a5_list_cta():
    # The check targets the shared CTA itself (the ai-ref-cta aside / Fast-Track button),
    # not the bare string: one free-tools page mentions Fast-Track in its own checklist
    # copy ("Submit the tool free on AgentScout, or buy Fast-Track ($15) for same-day
    # review"), which is page content, not the CTA boilerplate, and A5 allows no copy
    # changes. That mention is reported as a note, not a failure.
    bad = []
    mentions = []
    n = 0
    for p in _list_pages():
        s = p.read_text(encoding="utf-8", errors="ignore")
        n += 1
        main = _main_html(s)
        if 'ai-ref-cta' in main or 'pkg-cta-fast' in main:
            bad.append(str(p.relative_to(ROOT)))
        elif "Fast-Track" in main:
            mentions.append(str(p.relative_to(ROOT)))
    note(not bad, f"A5 list CTA: {len(bad)} list pages with the Submit/Fast-Track CTA inside <main> ({n} pages scanned)"
         + ("" if not bad else f"; bad: {bad[:5]}"))
    if mentions:
        print(f"note  A5 list CTA: {len(mentions)} page(s) mention Fast-Track in their own content (not the CTA): {mentions[:5]}")


def _latest_probes():
    rows = []
    for path in sorted((ROOT / "data" / "mcp-health").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict) and isinstance(row.get("slug"), str):
                rows.append(row)
    rows.sort(key=lambda r: str(r.get("ts") or ""), reverse=True)
    out = {}
    for row in rows:
        out.setdefault(row["slug"], row)
    return out


def _block_fields(s):
    m = re.search(r'<section class="mcp-check" data-mcp-check="1".*?</section>', s, flags=re.S)
    if not m:
        return None
    pairs = re.findall(r"<dt>([^<]*)</dt><dd>([^<]*)</dd>", m.group(0))
    return dict(pairs)


def check_a6_block():
    probes = _latest_probes()
    import datetime as _dt
    label = {"responded": "Responded", "needs_auth": "Needs auth", "failed": "Failed"}
    missing = []
    n = 0
    for slug in sorted(probes):
        p = ROOT / "tools" / f"{slug}.html"
        if not p.exists():
            continue
        n += 1
        s = p.read_text(encoding="utf-8", errors="ignore")
        if 'data-mcp-check="1"' not in s:
            missing.append(slug)
    note(not missing, f"A6 'Our check' block present on {n} probed tool pages"
         + ("" if not missing else f"; missing: {missing[:5]}"))
    # Sampled value check: block numbers match the latest jsonl row.
    responded = sorted(s for s, r in probes.items() if r.get("outcome") == "responded")
    auth = sorted(s for s, r in probes.items() if r.get("outcome") == "needs_auth")
    failed = sorted(s for s, r in probes.items() if r.get("outcome") == "failed")
    sample = responded[::max(1, len(responded) // 25)][:25] + auth[::max(1, len(auth) // 10)][:10] + failed[:5]
    bad = []
    for slug in sample:
        p = ROOT / "tools" / f"{slug}.html"
        if not p.exists():
            continue
        row = probes[slug]
        fields = _block_fields(p.read_text(encoding="utf-8", errors="ignore"))
        if fields is None:
            bad.append(f"{slug}: no block")
            continue
        want = {"Transport": str(row.get("transport") or ""),
                "Last handshake": label.get(str(row.get("outcome") or ""), "")}
        lat = row.get("latency_ms")
        if isinstance(lat, int):
            want["Latency"] = f"{lat:,} ms"
        if row.get("protocol_version"):
            want["Protocol version"] = str(row["protocol_version"])
        want["Checked"] = _dt.date.fromisoformat(str(row.get("ts") or "")[:10]).strftime("%b %-d, %Y")
        for k, v in want.items():
            if fields.get(k) != v:
                bad.append(f"{slug}: {k} is {fields.get(k)!r}, jsonl says {v!r}")
        tc = row.get("tool_count")
        if row.get("outcome") == "responded" and isinstance(tc, int):
            tools = fields.get("Tools") or ""
            if not tools.startswith(f"{tc} tool"):
                bad.append(f"{slug}: Tools is {tools!r}, jsonl count is {tc}")
            names = [x for x in (row.get("tool_names") or []) if isinstance(x, str)][:10]
            for nm in names:
                if nm not in tools:
                    bad.append(f"{slug}: tool name {nm!r} missing from block")
    note(not bad, f"A6 block numbers match the jsonl for {len(sample)} sampled slugs"
         + ("" if not bad else f"; bad: {bad[:5]}"))


def main():
    check_a5_shared()
    check_a5_badge_note()
    check_a5_list_cta()
    check_a6_block()
    if FAIL:
        print(f"\n{len(FAIL)} check(s) failed")
        return 1
    print("\nall indexing-content checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
