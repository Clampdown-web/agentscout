#!/usr/bin/env python3
"""After GitHub Pages publishes main, check every changed page on the live site.

For each HTML document added or modified in the deployed commit, fetch the
public URL with retries (the CDN can lag the deploy) and require:

- HTTP 200
- a canonical that matches the public URL (index.html is the directory URL)
- robots meta that agrees with sitemap.xml membership
- a sitemap listing when the page is indexable
- non-empty text inside <main> (skipped for noindex pages and for
  pages under tools/report-kit/, which include sample documents
  that have no <main>)

IndexNow is pinged only for indexable pages that passed, using
scripts/indexnow_ping.py and the key file already in the repo. A failing page
is never sent. The process exits 1 if any page fails, so the workflow fails
and GitHub can email the repository owner.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pages import (
    SITE,
    canonical_problem,
    is_noindex,
    is_published_html,
    looks_like_document,
    main_text,
    normalize_url,
    page_public_url,
    sitemap_locs,
)

SITEMAP_URL = SITE + "/sitemap.xml"
USER_AGENT = "AgentScout-post-deploy-verify"
RETRY_SLEEPS = (5, 10, 15, 20, 30)
ATTEMPTS = len(RETRY_SLEEPS) + 1


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "diff.renames=false", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _blob_prefix(repo: Path, sha: str, path: str) -> str:
    result = _git(repo, "cat-file", "-p", f"{sha}:{path}", check=False)
    if result.returncode != 0:
        return ""
    return result.stdout[:8000]


def changed_documents(repo: Path, sha: str) -> tuple[list[str], list[str], str | None]:
    """Return (pages to check, deleted pages, error).

    A move shows up as a delete plus an add because rename detection is off.
    Fragments such as free-tools-rest.html are not pages.
    """
    parent = _git(repo, "rev-parse", "--verify", "--quiet", f"{sha}^", check=False)
    if parent.returncode != 0 or not parent.stdout.strip():
        return [], [], f"The deployed commit {sha} has no parent, so the changed pages cannot be listed."
    diff = _git(
        repo,
        "diff",
        "--name-status",
        "--no-renames",
        parent.stdout.strip(),
        sha,
        check=False,
    )
    if diff.returncode != 0:
        return [], [], f"Could not list files changed in {sha}: {(diff.stderr or '').strip()}"
    pages: list[str] = []
    deleted: list[str] = []
    for line in diff.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2 or not parts[0]:
            continue
        status, path = parts[0][0], parts[-1]
        if not path.endswith(".html"):
            continue
        if status == "D":
            deleted.append(path)
            continue
        if status not in {"A", "M", "T"}:
            continue
        if not is_published_html(path):
            continue
        if not looks_like_document(_blob_prefix(repo, sha, path)):
            continue
        pages.append(path)
    return pages, deleted, None


def live_fetch(url: str) -> tuple[int, dict[str, str], str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Cache-Control": "no-cache",
        },
    )
    try:
        response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.HTTPError as exc:
        body = exc.read(3_000_000).decode("utf-8", "replace")
        headers = {key.lower(): value for key, value in (exc.headers.items() if exc.headers else [])}
        return exc.code, headers, body, url
    with response:
        headers = {key.lower(): value for key, value in response.headers.items()}
        body = response.read(3_000_000).decode("utf-8", "replace")
        status = getattr(response, "status", 200)
        return status, headers, body, response.geturl()


def skips_empty_main(path: str, noindex: bool) -> bool:
    """Noindex pages and report-kit samples may omit visible <main> text."""
    rel = path.replace("\\", "/").lstrip("/")
    return noindex or rel == "tools/report-kit" or rel.startswith("tools/report-kit/")


def page_problems(
    path: str,
    status: int,
    headers: dict[str, str],
    body: str,
    final_url: str,
    sitemap_norms: dict[str, str],
    fetch_error: str | None,
) -> tuple[list[str], bool]:
    """Problems for one live page, and whether the HTML is indexable."""
    expected = page_public_url(path)
    if fetch_error:
        return [f"{path} could not be fetched ({expected}): {fetch_error}"], False
    problems: list[str] = []
    if status != 200:
        problems.append(f"{path} returned HTTP {status} from {expected} after the CDN retries. Expected HTTP 200.")
    host = urllib.parse.urlsplit(final_url).hostname or ""
    if host not in {"agentscouthq.com"}:
        problems.append(f"{path} ended on {final_url}, which is outside {SITE}.")
    if status == 200:
        header = headers.get("x-robots-tag", "")
        noindex = is_noindex(body, header)
        # A noindex page (paginated archive, redirect stub) may point its canonical
        # at the hub page it folds into. Only indexable pages must be self-canonical.
        canon = None if noindex else canonical_problem(body, path)
        if canon:
            problems.append(canon)
        norm = normalize_url(expected)
        listed = norm in sitemap_norms
        if noindex and listed:
            raw = sitemap_norms.get(norm, expected)
            problems.append(
                f"{path} is noindex, but the live sitemap.xml lists it ({raw}). "
                "The robots meta does not match sitemap membership."
            )
        if (not noindex) and not listed:
            problems.append(
                f"{path} is indexable (no noindex), but the live sitemap.xml does not list {expected}."
            )
        if not main_text(body) and not skips_empty_main(path, noindex):
            problems.append(f"{path} has no text in <main>.")
        return problems, not noindex
    return problems, False


def _fetch_sitemap(fetch) -> tuple[dict[str, str], str | None]:
    try:
        status, _headers, body, _final = fetch(SITEMAP_URL)
    except Exception as exc:  # network errors, not HTTP status codes
        return {}, str(exc)
    if status != 200:
        return {}, f"HTTP {status}"
    if "<loc>" not in body.lower() and "<urlset" not in body.lower():
        return {}, "the response was not a sitemap"
    return sitemap_locs(body), None


def verify(
    repo: Path,
    sha: str,
    *,
    fetch=live_fetch,
    sleep=time.sleep,
    attempts: int = ATTEMPTS,
    workers: int = 8,
) -> tuple[list[str], list[str], list[str]]:
    """Return (failure messages, indexable URLs that passed, deleted paths)."""
    pages, deleted, error = changed_documents(repo, sha)
    if error:
        return [error], [], deleted
    if not pages:
        return [], [], deleted

    pending = list(pages)
    passed_indexable: list[str] = []
    last_problems: dict[str, list[str]] = {}
    sleeps = RETRY_SLEEPS
    for attempt in range(attempts):
        norms, sitemap_error = _fetch_sitemap(fetch)
        still: list[str] = []

        def check(path: str) -> tuple[str, list[str], bool]:
            expected = page_public_url(path)
            try:
                status, headers, body, final = fetch(expected)
                fetch_error = None
            except Exception as exc:
                status, headers, body, final, fetch_error = 0, {}, "", expected, str(exc)
            problems, indexable = page_problems(path, status, headers, body, final, norms, fetch_error)
            if sitemap_error:
                problems = [f"Live sitemap.xml could not be read ({sitemap_error})."] + problems
                indexable = False
            return path, problems, indexable

        with ThreadPoolExecutor(max_workers=max(1, min(workers, len(pending)))) as pool:
            results = list(pool.map(check, pending))
        for path, problems, indexable in results:
            if problems:
                still.append(path)
                last_problems[path] = problems
                continue
            last_problems.pop(path, None)
            if indexable:
                passed_indexable.append(page_public_url(path))
        pending = still
        if not pending or attempt == attempts - 1:
            break
        sleep(sleeps[min(attempt, len(sleeps) - 1)])

    failures = []
    for path in pages:
        problems = last_problems.get(path)
        if problems:
            failures.append(" ".join(problems))
    return failures, passed_indexable, deleted


def ping_indexnow(urls: list[str], repo: Path) -> None:
    if not urls:
        return
    subprocess.run(
        [sys.executable, str(repo / "scripts" / "indexnow_ping.py"), *urls],
        cwd=repo,
        check=True,
    )


def _summary(text: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def run(
    repo: Path,
    sha: str,
    *,
    fetch=live_fetch,
    ping=None,
    sleep=time.sleep,
    attempts: int = ATTEMPTS,
    workers: int = 8,
) -> int:
    pages, deleted, error = changed_documents(repo, sha)
    if error:
        print("POST-DEPLOY VERIFY FAILED")
        print(f"1. {error}")
        print(f"::error::{' '.join(error.split())}")
        _summary("## Post-deploy verify failed\n\n- " + error)
        return 1
    failures, passed, deleted = verify(
        repo, sha, fetch=fetch, sleep=sleep, attempts=attempts, workers=workers
    )
    if deleted:
        print("Deleted pages were not fetched: " + ", ".join(deleted))
    if not pages:
        print(f"No HTML pages changed in {sha}. Nothing to verify or ping.")
        _summary(f"No HTML pages changed in `{sha}`.")
        return 0
    if passed:
        print(f"IndexNow will be pinged for {len(passed)} indexable page(s) that passed.")
        for url in passed:
            print(f"  pass {url}")
    pinger = ping if ping is not None else (lambda urls: ping_indexnow(urls, repo))
    # Ping only the pages that passed. Do this before exiting so a later failure
    # of the ping itself is still visible, and never include a failing URL.
    if passed:
        try:
            pinger(passed)
        except Exception as exc:
            failures.append(f"IndexNow ping failed for the pages that passed: {exc}")
    if failures:
        print("POST-DEPLOY VERIFY FAILED")
        for number, message in enumerate(failures, 1):
            print(f"{number}. {message}")
            flat = " ".join(message.split())
            print(f"::error::{flat}")
        if passed:
            print(f"IndexNow was pinged for {len(passed)} passing page(s) and not for the failing pages.")
        else:
            print("IndexNow was not pinged, because no page passed.")
        _summary("## Post-deploy verify failed\n\n" + "\n".join(f"- {message}" for message in failures))
        return 1
    print(f"Post-deploy verify passed for {sha}.")
    _summary(f"Post-deploy verify passed for `{sha}`. IndexNow pinged {len(passed)} page(s).")
    return 0


def main() -> int:
    repo = Path(os.environ.get("REPO", ".")).resolve()
    sha = os.environ.get("DEPLOY_SHA", "").strip()
    if not sha:
        sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    return run(repo, sha)


if __name__ == "__main__":
    sys.exit(main())
