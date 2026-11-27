#!/usr/bin/env python3
"""Fail a pull request that publishes pages without the matching build output.

Reads the diff of BASE_SHA...HEAD_SHA and the pull-request body in PR_BODY.
MAIN_REF is the branch already on main (origin/main in CI). The daily free cap
(DAILY_CAP) and paid sub-cap (PAID_DAILY_CAP) use that history, tools.json on
main and the PR head, and the America/Los_Angeles committer date. Paid listings
are excluded from the free cap.

Exit 1 prints every failure. Exit 0 means the pull request passed.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pages import (
    DAILY_CAP,
    HEURISTIC,
    PAID_DAILY_CAP,
    canonical_problem,
    classify_indexable,
    describe_outputs,
    is_noindex,
    is_published_html,
    looks_like_document,
    normalize_url,
    output_satisfies,
    page_public_url,
    paid_slugs_from_tools_json,
    reason_problem,
    sitemap_locs,
    source_outputs,
)

PT = ZoneInfo("America/Los_Angeles")
HISTORY_LIMIT = 400


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "diff.renames=false", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _blob(repo: Path, sha: str | None, path: str) -> str | None:
    if not sha:
        return None
    result = _git(repo, "cat-file", "-p", f"{sha}:{path}", check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def _parent(repo: Path, sha: str) -> str | None:
    result = _git(repo, "rev-parse", "--verify", "--quiet", f"{sha}^", check=False)
    if result.returncode != 0:
        return None
    parent = result.stdout.strip()
    return parent or None


def _committer_date(repo: Path, sha: str) -> date:
    result = _git(repo, "show", "-s", "--format=%cI", sha)
    return datetime.fromisoformat(result.stdout.strip()).astimezone(PT).date()


def _name_status(repo: Path, base: str, head: str) -> tuple[list[tuple[str, str]], str | None]:
    result = _git(repo, "diff", "--name-status", "--no-renames", f"{base}...{head}", check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "git diff failed").strip()
        return [], (
            f"Could not diff {base}...{head}. {detail} "
            "The checkout may not contain enough history to find the merge base."
        )
    rows: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2 or not parts[0]:
            continue
        # Renames are disabled, so a move is a delete plus an add.
        rows.append((parts[0][0], parts[-1]))
    return rows, None


def additions_today(repo: Path, main_ref: str, today: date) -> tuple[list[str], str | None]:
    """Sitemap URLs added by commits on main whose committer date is today, Pacific time.

    Returns the raw <loc> values, one per normalized URL, and an error when the
    fetched history stops before yesterday while today's commits are still going.
    """
    listed = _git(repo, "rev-list", f"--max-count={HISTORY_LIMIT + 1}", main_ref, check=False)
    if listed.returncode != 0:
        return [], f"Could not read main history at {main_ref}: {(listed.stderr or '').strip()}"
    shas = [line for line in listed.stdout.split() if line]
    truncated = len(shas) > HISTORY_LIMIT
    shas = shas[:HISTORY_LIMIT]
    added: list[str] = []
    seen: set[str] = set()
    saw_older = False
    for sha in shas:
        committed = _committer_date(repo, sha)
        if committed > today:
            continue
        if committed < today:
            saw_older = True
            break
        parent = _parent(repo, sha)
        old = sitemap_locs(_blob(repo, parent, "sitemap.xml") or "")
        new = sitemap_locs(_blob(repo, sha, "sitemap.xml") or "")
        for norm, raw in new.items():
            if norm in old or norm in seen:
                continue
            seen.add(norm)
            added.append(raw)
    if saw_older or not shas or _parent(repo, shas[-1]) is None:
        return added, None
    if truncated or _parent(repo, shas[-1]):
        return added, (
            f"Main history at {main_ref} does not reach a commit before {today.isoformat()} "
            "(America/Los_Angeles). The daily new-URL count would be incomplete."
        )
    return added, None


def _format_list(items: list[str], limit: int = 12) -> str:
    if len(items) <= limit:
        return ", ".join(items) if items else "(none)"
    rest = len(items) - limit
    return ", ".join(items[:limit]) + f", and {rest} more"


def evaluate(repo: Path, base: str, head: str, body: str, main_ref: str, today: date) -> list[str]:
    rows, diff_error = _name_status(repo, base, head)
    if diff_error:
        return [diff_error]
    changed = [path for _status, path in rows]
    failures: list[str] = []

    grouped: dict[tuple[str, ...], list[str]] = {}
    for path in changed:
        outputs = source_outputs(path)
        if outputs is None:
            continue
        if any(output_satisfies(other, outputs) for other in changed):
            continue
        grouped.setdefault(outputs, []).append(path)
    for outputs, sources in grouped.items():
        names = ", ".join(sources)
        noun = "file" if len(sources) == 1 else "those files"
        failures.append(
            f"{names} changed, but this pull request does not update the pages that {noun} "
            f"generate. Expected a change to one of: {describe_outputs(outputs)}. {HEURISTIC}"
        )

    merge_base = _git(repo, "merge-base", base, head, check=False)
    sitemap_base = merge_base.stdout.strip() if merge_base.returncode == 0 and merge_base.stdout.strip() else base
    old_locs = sitemap_locs(_blob(repo, sitemap_base, "sitemap.xml") or "")
    head_locs = sitemap_locs(_blob(repo, head, "sitemap.xml") or "")
    added_norms = set(head_locs) - set(old_locs)

    new_pages: list[tuple[str, str, bool]] = []
    for status, path in rows:
        if status != "A" or not is_published_html(path):
            continue
        document = _blob(repo, head, path)
        if document is None or not looks_like_document(document[:8000]):
            continue
        url = page_public_url(path)
        norm = normalize_url(url)
        noindex = is_noindex(document)
        listed = norm in head_locs
        new_pages.append((path, url, noindex))
        if noindex and listed:
            raw = head_locs.get(norm, url)
            failures.append(
                f"{path} is noindex, but sitemap.xml lists it ({raw}). "
                "A noindex page must stay out of the sitemap."
            )
        if (not noindex) and not listed:
            failures.append(
                f"{path} is indexable (it has no noindex) but sitemap.xml does not list {url}."
            )
        if (not noindex) or listed:
            problem = canonical_problem(document, path)
            if problem:
                failures.append(problem)

    indexable_paths = [path for path, _url, noindex in new_pages if not noindex]
    reason = reason_problem(body or "", indexable_paths)
    if reason:
        failures.append(reason)

    capped_labels: list[str] = []
    pr_norms: set[str] = set()
    for path, url, noindex in new_pages:
        norm = normalize_url(url)
        if noindex or norm not in added_norms:
            continue
        pr_norms.add(norm)
        capped_labels.append(f"{path} ({url})")

    already, history_error = additions_today(repo, main_ref, today)
    if capped_labels and history_error:
        failures.append(history_error)
    elif capped_labels:
        already_norms = {normalize_url(url) for url in already}
        paid_slugs = paid_slugs_from_tools_json(_blob(repo, head, "tools.json") or "")
        paid_slugs |= paid_slugs_from_tools_json(_blob(repo, main_ref, "tools.json") or "")
        paid_slugs |= paid_slugs_from_tools_json(_blob(repo, sitemap_base, "tools.json") or "")
        already_list = list(already_norms)
        pr_list = list(pr_norms)
        already_free, already_paid = classify_indexable(already_list, paid_slugs)
        pr_free, pr_paid = classify_indexable(pr_list, paid_slugs)
        # URLs in both the PR and main today should not be double-counted.
        already_free = [u for u in already_free if u not in pr_norms]
        already_paid = [u for u in already_paid if u not in pr_norms]
        free_combined = set(pr_free) | set(already_free)
        paid_combined = set(pr_paid) | set(already_paid)
        if len(free_combined) > DAILY_CAP:
            failures.append(
                f"This PR adds {len(pr_free)} new free indexable "
                f"{'page' if len(pr_free) == 1 else 'pages'} that sitemap.xml newly lists, "
                f"and main already added {len(already_free)} free sitemap "
                f"{'URL' if len(already_free) == 1 else 'URLs'} on {today.isoformat()} "
                f"(America/Los_Angeles). Together that is {len(free_combined)} distinct free "
                f"{'URL' if len(free_combined) == 1 else 'URLs'}, which is over the daily free cap of {DAILY_CAP}. "
                f"Paid listings are excluded from this count. "
                f"This PR: {_format_list(capped_labels)}. "
                f"Already merged to main today: {_format_list(already)}."
            )
        if len(paid_combined) > PAID_DAILY_CAP:
            failures.append(
                f"This PR adds {len(pr_paid)} new paid indexable "
                f"{'page' if len(pr_paid) == 1 else 'pages'} that sitemap.xml newly lists, "
                f"and main already added {len(already_paid)} paid sitemap "
                f"{'URL' if len(already_paid) == 1 else 'URLs'} on {today.isoformat()} "
                f"(America/Los_Angeles). Together that is {len(paid_combined)} distinct paid "
                f"{'URL' if len(paid_combined) == 1 else 'URLs'}, which is over the daily paid cap of {PAID_DAILY_CAP}. "
                f"Ship extra paid pages as noindex/out of the sitemap; the next morning build "
                f"will promote them first, ahead of free listings. "
                f"This PR: {_format_list(capped_labels)}. "
                f"Already merged to main today: {_format_list(already)}."
            )
    return failures


def pacific_today() -> date:
    override = os.environ.get("GUARDRAIL_TODAY", "").strip()
    if override:
        return date.fromisoformat(override)
    return datetime.now(PT).date()


def main() -> int:
    repo = Path(os.environ.get("REPO", ".")).resolve()
    base = os.environ.get("BASE_SHA", "").strip()
    head = os.environ.get("HEAD_SHA", "HEAD").strip() or "HEAD"
    main_ref = os.environ.get("MAIN_REF", base).strip()
    body = os.environ.get("PR_BODY")
    if body is None:
        body_file = os.environ.get("PR_BODY_FILE", "").strip()
        body = Path(body_file).read_text(encoding="utf-8") if body_file else ""
    if not base:
        print("BASE_SHA is not set. The guardrails workflow must pass the pull request base commit.")
        return 1
    if not main_ref:
        print("MAIN_REF is not set, so the daily sitemap count on main cannot be read.")
        return 1
    failures = evaluate(repo, base, head, body or "", main_ref, pacific_today())
    if failures:
        print("Guardrail check failed.\n")
        for number, message in enumerate(failures, 1):
            print(f"{number}. {message}\n")
        return 1
    print("Guardrail check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
