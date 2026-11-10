#!/usr/bin/env python3
"""Maker-submission flag shared by the catalog importer and the site build.

A tool whose source is the submit form ("Submission" or "Maker submission",
any case) is a maker submission. The importer stamps maker_submitted and
submitted (YYYY-MM-DD, Pacific) on those rows. The build refuses to continue
when a submit-form source is missing either field.

Other sources are not guessed. "Owner request" is a person asking for a
listing, not the submit form, and stays unflagged unless --maker-submitted
is passed explicitly.
"""
from __future__ import annotations

import datetime
import html
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

# Exact submit-form labels used in tools.json. Compared case-insensitively.
SUBMISSION_SOURCES = frozenset({"submission", "maker submission"})
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ROOT = Path(__file__).resolve().parents[1]
BADGE_RE = re.compile(
    r'(<div class="badges">)(.*?)(</div>\s*<h1 class="icoh")',
    re.S,
)


def is_submission_source(source) -> bool:
    return str(source or "").strip().lower() in SUBMISSION_SOURCES


def pacific_today() -> str:
    return datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()


def stamp_new(entry, today=None):
    """Tag a row the importer is adding. Keeps an existing YYYY-MM-DD submitted date."""
    entry["maker_submitted"] = True
    if not DATE_RE.fullmatch(entry.get("submitted") or ""):
        entry["submitted"] = today or pacific_today()
    return entry


def backfill_row(entry) -> bool:
    """Set maker_submitted and submitted on an existing submit-form row.

    submitted keeps a date already stored, otherwise the row's added date.
    Returns True when a field was written. No other field is touched.
    """
    if not is_submission_source(entry.get("source")):
        return False
    changed = False
    if entry.get("maker_submitted") is not True:
        entry["maker_submitted"] = True
        changed = True
    if not DATE_RE.fullmatch(entry.get("submitted") or ""):
        added = entry.get("added") or ""
        if not DATE_RE.fullmatch(added):
            raise ValueError(f"{entry.get('slug') or entry.get('name')}: submit-form row has no added date")
        entry["submitted"] = added
        changed = True
    return changed


def problems(tools) -> list[str]:
    """Submit-form sources must carry the flag and a Pacific YYYY-MM-DD submitted date."""
    bad = []
    for row in tools:
        slug = row.get("slug") or row.get("name") or "?"
        if row.get("catalog_only") and row.get("maker_submitted"):
            bad.append(f"{slug}: catalog_only and maker_submitted")
        if row.get("maker_submitted") and not DATE_RE.fullmatch(row.get("submitted") or ""):
            bad.append(f"{slug}: maker_submitted without submitted YYYY-MM-DD")
        if is_submission_source(row.get("source")) and not row.get("maker_submitted"):
            bad.append(f"{slug}: source {row.get('source')!r} lacks maker_submitted")
        if is_submission_source(row.get("source")) and row.get("catalog_only"):
            bad.append(f"{slug}: catalog_only submit-form source")
    return bad


def check(tools=None, path=None):
    """Fail the build when a submit-form listing is missing the maker flag. Prints every miss."""
    if tools is None:
        tools = json.loads(Path(path or ROOT / "tools.json").read_text(encoding="utf-8"))
    bad = problems(tools)
    if bad:
        print("MAKER FLAG CHECK FAILED", file=sys.stderr)
        print(
            f"{len(bad)} listing(s): a submit-form source needs maker_submitted and submitted (YYYY-MM-DD).",
            file=sys.stderr,
        )
        for line in bad[:50]:
            print(" -", line, file=sys.stderr)
        if len(bad) > 50:
            print(f" - ... {len(bad) - 50} more", file=sys.stderr)
        raise SystemExit(1)
    return tools


def badge_html(row) -> str:
    """The 'Submitted by maker' badge build_site inserts next to the tool name."""
    sd = row.get("submitted") or row.get("added") or ""
    sdt = datetime.date.fromisoformat(sd).strftime("%b %-d, %Y") if DATE_RE.fullmatch(sd) else ""
    when = f" on {sdt}" if sdt else ""
    title = f"The maker submitted this tool through our submit form{when}. We reviewed and wrote the listing."
    return f'<span class="b maker" title="{html.escape(title, quote=True)}">✓ Submitted by maker</span>'


def apply_badge(page: str, row) -> str | None:
    """Insert the maker badge into a built tool page. None when the page has no badge slot."""
    if not row.get("maker_submitted"):
        return page
    match = BADGE_RE.search(page)
    if not match:
        return None
    if 'class="b maker"' in match.group(2):
        return page
    badge = badge_html(row)
    return page[: match.start(3)] + badge + page[match.start(3) :]


def apply_badges(tools, tools_dir=None) -> dict:
    """Write the maker badge onto tool pages that are flagged and do not have it yet."""
    folder = Path(tools_dir or ROOT / "tools")
    wrote = skipped = missing = 0
    missed = []
    for row in tools:
        if not row.get("maker_submitted"):
            continue
        path = folder / f"{row['slug']}.html"
        if not path.is_file():
            missing += 1
            missed.append(row["slug"])
            continue
        old = path.read_text(encoding="utf-8")
        new = apply_badge(old, row)
        if new is None:
            missing += 1
            missed.append(row["slug"])
            continue
        if new == old:
            skipped += 1
            continue
        path.write_text(new, encoding="utf-8")
        wrote += 1
    return {"wrote": wrote, "already": skipped, "missing": missing, "missed": missed}


if __name__ == "__main__":
    check()
    print("maker flag check ok")
