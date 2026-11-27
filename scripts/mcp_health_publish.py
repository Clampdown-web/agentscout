#!/usr/bin/env python3
"""Open one mergeable pull request for the daily MCP handshake.

The probe runs on a worktree that already includes unmerged bot rows and
fresh main. This script then checks out current main again, keeps those
health files, restamps the pages that read them, and pushes a new branch.
Older open bot/mcp-health pull requests are closed so only one stays open.

A pull request created with GITHUB_TOKEN does not start pull_request
workflows. workflow_dispatch does run, and it reports the guardrails check
on the head commit. That is the check the ruleset requires. When
MCP_HEALTH_PR_TOKEN is set, the pull request is opened with that token and
DISPATCH_CI=0 so the normal pull_request workflows start instead.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "guardrails"))

import mcp_health_pages as pages_job  # noqa: E402
import mcp_response_rate as mrr  # noqa: E402
from pages import is_published_html  # noqa: E402
from refresh_pr_build import CI_WORKFLOWS, dispatch_ci, safe_branch  # noqa: E402

PT = ZoneInfo("America/Los_Angeles")
BRANCH_PREFIX = "bot/mcp-health-"
BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
# A new month file is the only untracked path this job may add.
_MONTH_LOG = re.compile(r"data/mcp-health/(\d{4})-(0[1-9]|1[0-2])\.jsonl")
# CodeQL and the other scans have to finish before auto-merge. The ruleset
# only requires guardrails, so enabling auto-merge earlier would merge first.
CHECK_TIMEOUT_SECONDS = 35 * 60
CHECK_POLL_SECONDS = 20


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "git failed").strip()
        raise RuntimeError(detail)
    return result


def run_cmd(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True)


def pacific_day(now: datetime | None = None) -> str:
    current = now or datetime.now(PT)
    return current.astimezone(PT).date().isoformat()


def make_branch(day: str, run_id: str) -> str:
    branch = f"{BRANCH_PREFIX}{day}-{run_id}"
    if (
        not branch.startswith(BRANCH_PREFIX)
        or branch == "main"
        or "/main" in branch
        or not safe_branch(branch)
        or not run_id.isdigit()
    ):
        raise RuntimeError(f"refusing branch name {branch}")
    return branch


def union_jsonl(base: str, extra: str) -> str:
    """Keep base order, then append extra lines that are not already present."""
    seen: set[str] = set()
    lines: list[str] = []
    for raw in f"{base}\n{extra}".splitlines():
        stripped = raw.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        lines.append(stripped)
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def _line_set(text: str) -> set[str]:
    return {line.strip() for line in text.splitlines() if line.strip()}


def allowed_path(path: str) -> bool:
    rel = path.replace("\\", "/").strip().lstrip("./")
    if ".." in rel.split("/"):
        return False
    if rel.startswith("data/mcp-health/"):
        return True
    if rel in {"llms.txt", "llms-full.txt"}:
        return True
    # Category and task pages spill the rest of a long list into one JSON file.
    # Those are the only generated JSON fragments this restamp rewrites.
    for directory in ("categories", "tasks"):
        prefix = directory + "/"
        if rel.startswith(prefix) and rel.endswith(".more.json") and rel.count("/") == 1:
            return True
    return is_published_html(rel)


def is_new_month_log(code: str, path: str) -> bool:
    """True for an untracked data/mcp-health/YYYY-MM.jsonl and nothing else."""
    if code.strip() != "??":
        return False
    return _MONTH_LOG.fullmatch(path.replace("\\", "/").strip()) is not None


def review_status(rows: list[tuple[str, str]]) -> str | None:
    """None when the worktree may be committed. Empty string when there is nothing to commit.

    A modification is allowed. The only addition allowed is next month's probe log.
    """
    odd: list[str] = []
    for code, path in rows:
        if set(code) <= {" ", "M"}:
            continue
        if is_new_month_log(code, path):
            continue
        odd.append(f"{code} {path}".strip())
    if odd:
        return "refusing to commit a status other than a modification: " + ", ".join(odd[:12])
    return commit_block([path for _code, path in rows])


def commit_block(paths: list[str]) -> str | None:
    """None when the paths may be committed. Empty string when there is nothing to commit."""
    if not paths:
        return ""
    bad = [path for path in paths if not allowed_path(path)]
    if bad:
        return "refusing to commit unexpected paths: " + ", ".join(bad[:12])
    health = [path for path in paths if path.startswith("data/mcp-health/")]
    html = [path for path in paths if is_published_html(path)]
    if health and not html:
        names = ", ".join(health[:8])
        return (
            f"source/builder files changed ({names}) but the rebuild produced no published *.html "
            "and no sitemap.xml changes. Run the builders and commit the output."
        )
    return None


def select_health_prs(rows: list[dict]) -> list[dict]:
    chosen = []
    for row in rows:
        if row.get("isCrossRepository") is True:
            continue
        branch = str(row.get("headRefName") or "")
        if branch.startswith(BRANCH_PREFIX) and safe_branch(branch):
            chosen.append(row)
    chosen.sort(key=lambda row: str(row.get("updatedAt") or ""))
    return chosen


def read_health(root: Path) -> dict[str, str]:
    health = root / "data" / "mcp-health"
    files: dict[str, str] = {}
    if not health.is_dir():
        return files
    for path in sorted(health.iterdir()):
        if not path.is_file():
            continue
        if path.suffix == ".jsonl" or path.name in {"state.json", "summary.json"}:
            files[path.name] = path.read_text(encoding="utf-8")
    return files


def overlay_carried(root: Path, incoming: dict[str, str]) -> bool:
    """Union jsonl onto the worktree. Take state.json only when the branch adds rows.

    A pull request whose rows are already on main must not rewind next_slug.
    Summary is left for the probe, which rebuilds it from the jsonl.
    """
    health = root / "data" / "mcp-health"
    health.mkdir(parents=True, exist_ok=True)
    added = False
    for name in sorted(incoming):
        if not name.endswith(".jsonl"):
            continue
        dest = health / name
        current = dest.read_text(encoding="utf-8") if dest.is_file() else ""
        merged = union_jsonl(current, incoming[name])
        if _line_set(merged) != _line_set(current):
            added = True
        dest.write_text(merged, encoding="utf-8")
    if added and "state.json" in incoming:
        text = incoming["state.json"]
        (health / "state.json").write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return added


def merge_probe_health(root: Path, probe: dict[str, str]) -> None:
    """Put the probe result on top of the health files now on disk (fresh main)."""
    health = root / "data" / "mcp-health"
    health.mkdir(parents=True, exist_ok=True)
    probe_lines: set[str] = set()
    for name, text in probe.items():
        if name.endswith(".jsonl"):
            probe_lines |= _line_set(text)
            current = (health / name).read_text(encoding="utf-8") if (health / name).is_file() else ""
            (health / name).write_text(union_jsonl(current, text), encoding="utf-8")
        elif name == "state.json":
            (health / name).write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    written: set[str] = set()
    for path in sorted(health.glob("*.jsonl")):
        written |= _line_set(path.read_text(encoding="utf-8"))
    summary_text = probe.get("summary.json") or ""
    if written == probe_lines and summary_text:
        (health / "summary.json").write_text(
            summary_text if summary_text.endswith("\n") else summary_text + "\n",
            encoding="utf-8",
        )
        return
    previous: dict = {}
    if summary_text.strip():
        try:
            loaded = json.loads(summary_text)
        except json.JSONDecodeError:
            loaded = {}
        if isinstance(loaded, dict):
            previous = loaded
    history = mrr.load_history(health)
    classifications = {}
    servers = previous.get("servers") if isinstance(previous.get("servers"), dict) else {}
    for slug, row in servers.items():
        if not isinstance(row, dict):
            continue
        endpoint = row.get("endpoint") if isinstance(row.get("endpoint"), str) else None
        transport = row.get("transport") if isinstance(row.get("transport"), str) else None
        classifications[slug] = mrr.Classification(
            slug,
            str(row.get("disposition") or "remote"),
            endpoint,
            transport,
        )
    summary = mrr.build_summary(
        history,
        classifications,
        mrr.utcnow(),
        previous=previous,
        registry_complete=bool(previous.get("registry_complete")),
    )
    (health / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def _status_rows(repo: Path) -> list[tuple[str, str]]:
    result = git(repo, "status", "--porcelain", "-uall")
    rows: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        code = line[:2]
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip().strip('"')
        rows.append((code, path))
    return rows


def _ensure_identity(repo: Path) -> None:
    if git(repo, "config", "--get", "user.email", check=False).returncode != 0:
        git(repo, "config", "user.email", BOT_EMAIL)
    if git(repo, "config", "--get", "user.name", check=False).returncode != 0:
        git(repo, "config", "user.name", BOT_NAME)
    git(repo, "config", "commit.gpgsign", "false")


def _health_at(repo: Path, rev: str) -> dict[str, str]:
    listed = git(repo, "ls-tree", "-r", "--name-only", rev, "data/mcp-health", check=False)
    if listed.returncode != 0:
        return {}
    files: dict[str, str] = {}
    for path in listed.stdout.splitlines():
        name = path.rsplit("/", 1)[-1]
        if not (name.endswith(".jsonl") or name in {"state.json", "summary.json"}):
            continue
        shown = git(repo, "show", f"{rev}:{path}", check=False)
        if shown.returncode == 0:
            files[name] = shown.stdout
    return files


def _gh_json(argv: list[str], run) -> list:
    result = run(argv)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "gh failed").strip()
        raise RuntimeError(detail)
    payload = json.loads(result.stdout or "[]")
    if not isinstance(payload, list):
        raise RuntimeError("unexpected gh JSON")
    return payload


def list_open_health_prs(slug: str, run=None) -> list[dict]:
    run = run or run_cmd
    rows = _gh_json(
        [
            "gh", "pr", "list", "--repo", slug, "--state", "open", "--limit", "100",
            "--json", "number,headRefName,updatedAt,isCrossRepository",
        ],
        run,
    )
    return select_health_prs(rows)


def _listed_runs(result: subprocess.CompletedProcess[str]) -> list[dict]:
    if result.returncode != 0 or not (result.stdout or "").strip():
        return []
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def wait_for_checks(
    slug: str,
    branch: str,
    head: str,
    *,
    run=None,
    sleep=None,
    clock=None,
    timeout: float = CHECK_TIMEOUT_SECONDS,
    poll: float = CHECK_POLL_SECONDS,
) -> list[str]:
    """Poll the four CI workflows on head until each has concluded success.

    Returns the workflows that failed or were still unfinished at the timeout.
    An empty list means all four succeeded.
    """
    run = run or run_cmd
    pause = sleep or time.sleep
    now = clock or time.monotonic
    started = now()
    pending = list(CI_WORKFLOWS)
    failed: list[str] = []
    while pending:
        still: list[str] = []
        for workflow in pending:
            listed = run(
                [
                    "gh", "run", "list", "--repo", slug, "--workflow", workflow,
                    "--branch", branch, "--limit", "20",
                    "--json", "databaseId,headSha,status,conclusion,createdAt",
                ]
            )
            # A pull request opened with GITHUB_TOKEN gets pull_request runs that
            # GitHub parks at action_required (waiting for maintainer approval).
            # They never run and report no check on the commit, so they are not a
            # result. The dispatched runs on the same head are what count.
            matches = [
                row for row in _listed_runs(listed)
                if row.get("headSha") == head and row.get("conclusion") != "action_required"
            ]
            matches.sort(key=lambda row: str(row.get("createdAt") or ""), reverse=True)
            if not matches or matches[0].get("status") != "completed":
                still.append(workflow)
                continue
            conclusion = matches[0].get("conclusion")
            if conclusion != "success":
                failed.append(f"{workflow} {conclusion or 'completed'}")
        pending = still
        if not pending or failed:
            return failed
        if now() - started >= timeout:
            return failed + pending
        print("waiting for " + ", ".join(pending), flush=True)
        pause(poll)
    return failed


def fetch_main(repo: Path) -> str:
    # The workflow checkout is shallow. One commit of main is enough to branch from.
    git(repo, "fetch", "--no-tags", "--depth=1", "origin", "main")
    return git(repo, "rev-parse", "origin/main").stdout.strip()


def carry(repo: Path, slug: str, run=None) -> int:
    """Reset to fresh main and copy health files from older open bot pull requests."""
    run = run or run_cmd
    dirty = git(repo, "status", "--porcelain").stdout.strip()
    if dirty:
        raise RuntimeError("carry refused: the worktree is not clean")
    fetch_main(repo)
    git(repo, "checkout", "-f", "-B", "main", "origin/main")
    for pr in list_open_health_prs(slug, run):
        branch = str(pr["headRefName"])
        git(repo, "fetch", "--no-tags", "--depth=1", "origin", branch)
        overlay_carried(repo, _health_at(repo, f"origin/{branch}"))
        print(f"carried health rows from #{pr['number']} {branch}", flush=True)
    return 0


def _pr_body(day: str) -> str:
    return (
        f"Daily MCP handshake results for {day} (America/Los_Angeles).\n\n"
        "The probe appends data/mcp-health and this job restamps the pages that read it: "
        "badges, Responds attributes, the Our check block, and the handshake count. "
        "No new indexable URL is included.\n\n"
        "New indexable pages in this PR: 0\n\n"
        "Reason this page exists: daily MCP handshake results, no new indexable pages\n"
    )


def publish(repo: Path, slug: str, run_id: str, day: str | None = None, run=None, dry_run: bool = False) -> int:
    run = run or run_cmd
    day = day or pacific_day()
    branch = make_branch(day, run_id)
    if dry_run:
        # The caller already probed and restamped. Do not fetch, reset, or push.
        rows = _status_rows(repo)
    else:
        probe = read_health(repo)
        fetch_main(repo)
        git(repo, "checkout", "-f", "-B", branch, "origin/main")
        merge_probe_health(repo, probe)
        pages_job.rebuild_pages(repo)
        rows = _status_rows(repo)
    block = review_status(rows)
    if block == "":
        print("no health changes", flush=True)
        return 0
    if block:
        raise RuntimeError(block)
    paths = [path for _code, path in rows]
    if dry_run:
        print(f"dry-run: {len(paths)} path(s) would be committed", flush=True)
        for path in paths:
            print(path, flush=True)
        return 0
    _ensure_identity(repo)
    git(repo, "add", "--", *paths)
    if git(repo, "diff", "--cached", "--quiet", check=False).returncode == 0:
        print("no health changes", flush=True)
        return 0
    git(repo, "commit", "-m", "Record daily MCP response probes")
    git(repo, "push", "origin", f"HEAD:{branch}")
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    base = git(repo, "rev-parse", "origin/main").stdout.strip()
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(_pr_body(day))
        body_path = handle.name
    created = run(
        [
            "gh", "pr", "create", "--repo", slug, "--base", "main", "--head", branch,
            "--title", f"Record daily MCP response probes ({day})", "--body-file", body_path,
        ]
    )
    os.unlink(body_path)
    if created.returncode != 0:
        detail = (created.stderr or created.stdout or "could not open the pull request").strip()
        raise RuntimeError(detail)
    url = (created.stdout or "").strip().splitlines()[-1].strip()
    number = url.rsplit("/", 1)[-1]
    if not number.isdigit():
        raise RuntimeError(f"could not read the pull request number from {url}")
    pr_number = int(number)
    for old in list_open_health_prs(slug, run):
        if int(old["number"]) == pr_number:
            continue
        note = (
            f"Superseded by #{pr_number}. The daily handshake job keeps a single open pull request "
            f"based on current main, and this one is closed. Probe rows from this branch were carried forward."
        )
        closed = run(
            ["gh", "pr", "close", str(old["number"]), "--repo", slug, "--comment", note]
        )
        if closed.returncode != 0:
            detail = (closed.stderr or closed.stdout or "could not close the older pull request").strip()
            raise RuntimeError(detail)
        print(f"closed #{old['number']}", flush=True)
    if os.environ.get("DISPATCH_CI", "1") != "0":
        failed = dispatch_ci(slug, branch, pr_number, head, base, wait=False)
        if failed:
            print(f"leaving {url} open. CI dispatch failed: {' '.join(failed)}", file=sys.stderr)
            return 1
    unfinished = wait_for_checks(slug, branch, head, run=run)
    if unfinished:
        print(
            f"leaving {url} open. checks did not succeed: {', '.join(unfinished)}",
            file=sys.stderr,
        )
        return 1
    merged = run(["gh", "pr", "merge", number, "--repo", slug, "--auto", "--squash"])
    if merged.returncode != 0:
        print(f"squash auto-merge was not enabled for {url}.", file=sys.stderr)
        print(
            "Allow auto-merge has to be on (Settings, General, Pull Requests). Squash merges are already allowed.",
            file=sys.stderr,
        )
        print(
            "This job does not push to main, does not bypass repository rules, and does not admin-merge.",
            file=sys.stderr,
        )
        return 1
    print(f"opened {url}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish the daily MCP handshake pull request.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    carry_cmd = sub.add_parser("carry")
    carry_cmd.add_argument("--repo", type=Path, default=ROOT)
    carry_cmd.add_argument("--slug", default=os.environ.get("GITHUB_REPOSITORY", ""))
    publish_cmd = sub.add_parser("publish")
    publish_cmd.add_argument("--repo", type=Path, default=ROOT)
    publish_cmd.add_argument("--slug", default=os.environ.get("GITHUB_REPOSITORY", ""))
    publish_cmd.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", ""))
    publish_cmd.add_argument("--day", default="")
    publish_cmd.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "carry":
            if not args.slug:
                raise RuntimeError("slug is required")
            return carry(args.repo, args.slug)
        if not args.slug or not args.run_id:
            raise RuntimeError("slug and run id are required")
        return publish(
            args.repo,
            args.slug,
            args.run_id,
            day=args.day or None,
            dry_run=args.dry_run,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
