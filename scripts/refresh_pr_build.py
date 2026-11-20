#!/usr/bin/env python3
"""Refresh generated files on an open pull request after main moves.

The generated-file list lives in scripts/guardrails/pages.py (is_refresh_generated).
This script merges origin/main with a merge commit, keeps main's copy of generated
conflicts, and leaves the branch untouched when a source file conflicts. It does
not force-push and it does not rewrite history.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "guardrails"))
from pages import is_refresh_generated  # noqa: E402

LABEL = "auto-rebuild"
CI_WORKFLOWS = ("guardrails.yml", "security.yml", "gitleaks.yml", "codeql.yml")
_BRANCH = re.compile(r"[A-Za-z0-9._/-]+")
_FAILURE = re.compile(r"^PIPELINE FAILED: ([^:]+): (.+)$")


def is_generated(path: str) -> bool:
    return is_refresh_generated(path)


def split_conflicts(paths: list[str]) -> tuple[list[str], list[str]]:
    generated: list[str] = []
    source: list[str] = []
    for path in paths:
        rel = path.replace("\\", "/").strip().strip('"')
        if rel.startswith("./"):
            rel = rel[2:]
        if not rel:
            continue
        if is_generated(rel):
            generated.append(rel)
        else:
            source.append(rel)
    return generated, source


def rebuild_message(main_sha: str) -> str:
    return f"chore: rebuild generated files on main {main_sha.strip()[:7]}"


def push_argv(branch: str) -> list[str]:
    return ["git", "push", "origin", f"HEAD:{branch}"]


def safe_branch(branch: str) -> bool:
    return bool(_BRANCH.fullmatch(branch or "")) and not branch.startswith(("-", "/")) and ".." not in branch.split("/")


def conflict_comment(main_sha: str, files: list[str]) -> str:
    shown = files[:20]
    names = ", ".join(shown)
    extra = len(files) - len(shown)
    if extra:
        names += f", and {extra} more"
    return (
        f"Refresh left this branch unchanged. main {main_sha[:7]} conflicts in source files: {names}. "
        f"A human needs to merge main.\n"
        f"<!-- refresh-pr-builds conflict {main_sha} -->"
    )


def checks_comment(main_sha: str, step: str, reason: str) -> str:
    text = " ".join((reason or "").split()) or "failed"
    if len(text) > 240:
        text = text[:237] + "..."
    return (
        f"Refresh did not push. {step} failed: {text}. The branch was left unchanged.\n"
        f"<!-- refresh-pr-builds checks {main_sha} {step} -->"
    )


def push_comment(main_sha: str) -> str:
    return (
        f"Refresh did not push. origin rejected the update for main {main_sha[:7]}, "
        f"and this run did not force-push. The branch was left unchanged.\n"
        f"<!-- refresh-pr-builds push {main_sha} -->"
    )


def ci_comment(head_sha: str, failed: list[str]) -> str:
    return (
        f"Refresh pushed, then CI failed: {', '.join(failed)}.\n"
        f"<!-- refresh-pr-builds ci {head_sha} -->"
    )


def marker_of(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("<!-- refresh-pr-builds ") and stripped.endswith("-->"):
            return stripped
    return ""


def should_post(existing: list[str], body: str) -> bool:
    marker = marker_of(body)
    if not marker:
        return True
    return all(marker not in item for item in existing)


def parse_failure(log: str) -> tuple[str, str]:
    for line in reversed((log or "").splitlines()):
        match = _FAILURE.match(line.strip())
        if match:
            return match.group(1).strip(), match.group(2).strip()
    return "checks", "the morning pipeline failed"


def normalize_pr(pr: dict) -> dict:
    labels = []
    for label in pr.get("labels") or []:
        if isinstance(label, dict):
            labels.append(label.get("name") or "")
        else:
            labels.append(str(label))
    repo = pr.get("headRepository") or pr.get("head_repo") or ""
    if isinstance(repo, dict):
        repo = repo.get("nameWithOwner") or ""
    return {
        "number": int(pr["number"]),
        "draft": bool(pr.get("isDraft") if "isDraft" in pr else pr.get("draft")),
        "branch": pr.get("headRefName") or pr.get("branch") or "",
        "head_repo": repo,
        "labels": labels,
        "state": str(pr.get("state") or "open").lower(),
    }


def eligible(pr: dict, repo: str) -> bool:
    return (
        pr["state"] == "open"
        and not pr["draft"]
        and pr["head_repo"] == repo
        and LABEL in pr["labels"]
        and safe_branch(pr["branch"])
    )


def select_targets(
    prs: list[dict],
    *,
    event: str,
    repo: str,
    label: str = "",
    event_pr: int | None = None,
    input_pr: int | None = None,
) -> list[dict]:
    """Open, non-draft, same-repo pull requests that carry auto-rebuild."""
    if event == "pull_request" and label != LABEL:
        return []
    chosen = []
    for raw in prs:
        pr = normalize_pr(raw)
        if not eligible(pr, repo):
            continue
        if event == "workflow_dispatch" and pr["number"] != input_pr:
            continue
        if event == "pull_request" and pr["number"] != event_pr:
            continue
        chosen.append({"number": pr["number"], "branch": pr["branch"]})
    return chosen


def dispatch_fields(workflow: str, pr: int, head: str, base: str) -> dict[str, str]:
    if workflow == "guardrails.yml":
        return {"pr_number": str(pr), "head_sha": head, "base_sha": base}
    return {"head_sha": head}


def dispatch_argv(workflow: str, ref: str, fields: dict[str, str]) -> list[str]:
    argv = ["gh", "workflow", "run", workflow, "--ref", ref]
    for key, value in fields.items():
        argv.extend(["-f", f"{key}={value}"])
    return argv


def newest_run_id(rows: list[dict], head_sha: str) -> int | None:
    matches = [
        row for row in rows
        if row.get("headSha") == head_sha and row.get("event") in (None, "", "workflow_dispatch")
    ]
    if not matches:
        return None
    matches.sort(key=lambda row: row.get("createdAt") or "", reverse=True)
    return int(matches[0]["databaseId"])


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "git failed").strip()
        raise RuntimeError(detail)
    return result


def ensure_identity(repo: Path) -> None:
    if _git(repo, "config", "--get", "user.email", check=False).returncode != 0:
        _git(repo, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    if _git(repo, "config", "--get", "user.name", check=False).returncode != 0:
        _git(repo, "config", "user.name", "github-actions[bot]")
    _git(repo, "config", "commit.gpgsign", "false")


def _merge_in_progress(repo: Path) -> bool:
    path = Path(_git(repo, "rev-parse", "--git-path", "MERGE_HEAD").stdout.strip())
    if not path.is_absolute():
        path = repo / path
    return path.exists()


def _unmerged(repo: Path) -> list[str]:
    result = _git(repo, "diff", "--name-only", "-z", "--diff-filter=U", check=False)
    return [path for path in result.stdout.split("\0") if path]


def _stages(repo: Path, path: str) -> set[str]:
    result = _git(repo, "ls-files", "-u", "-z", "--", path, check=False)
    stages: set[str] = set()
    for record in result.stdout.split("\0"):
        if not record:
            continue
        meta = record.split("\t", 1)[0]
        parts = meta.split()
        if parts:
            stages.add(parts[-1])
    return stages


def take_main_version(repo: Path, path: str) -> None:
    """During a merge, --theirs is the branch being merged in (main)."""
    stages = _stages(repo, path)
    if stages and "3" not in stages:
        _git(repo, "rm", "-f", "--", path)
        return
    _git(repo, "checkout", "--theirs", "--", path)
    _git(repo, "add", "--", path)


def _result(status: str, main_sha: str = "", branch: str = "", files: list[str] | None = None) -> dict:
    return {
        "status": status,
        "main_sha": main_sha,
        "short_sha": main_sha[:7],
        "branch": branch,
        "files": files or [],
    }


def perform_merge(repo: Path, main_ref: str = "origin/main", *, commenter=None) -> dict:
    """git merge --no-ff --no-commit <main>, then a merge commit. Never rebases."""
    ensure_identity(repo)
    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    main_sha = _git(repo, "rev-parse", main_ref).stdout.strip()
    base = _git(repo, "merge-base", "HEAD", main_ref).stdout.strip()
    if base == main_sha:
        print(f"already contains {main_ref} {main_sha[:7]}", flush=True)
        return _result("up_to_date", main_sha, branch)
    print(f"git merge --no-ff --no-commit {main_ref}", flush=True)
    merged = _git(repo, "merge", "--no-ff", "--no-commit", main_ref, check=False)
    if merged.stdout:
        print(merged.stdout, end="" if merged.stdout.endswith("\n") else "\n", flush=True)
    if merged.stderr:
        print(merged.stderr, end="" if merged.stderr.endswith("\n") else "\n", flush=True)
    if merged.returncode not in (0, 1) or not _merge_in_progress(repo):
        if "Already up to date" in (merged.stdout + merged.stderr):
            return _result("up_to_date", main_sha, branch)
        print("git merge failed", file=sys.stderr)
        return _result("error", main_sha, branch)
    conflicts = _unmerged(repo)
    _generated, source = split_conflicts(conflicts)
    if source:
        _git(repo, "merge", "--abort")
        body = conflict_comment(main_sha, source)
        print(body, flush=True)
        if commenter:
            commenter(body)
        return _result("source_conflict", main_sha, branch, source)
    for path in conflicts:
        take_main_version(repo, path)
    if _unmerged(repo):
        _git(repo, "merge", "--abort", check=False)
        print("generated conflicts could not be resolved", file=sys.stderr)
        return _result("error", main_sha, branch, conflicts)
    _git(repo, "commit", "-m", f"Merge {main_ref} into {branch}")
    print(f"merge commit {_git(repo, 'rev-parse', '--short', 'HEAD').stdout.strip()}", flush=True)
    return _result("merged", main_sha, branch)


def commit_rebuild(repo: Path, main_sha: str) -> str:
    ensure_identity(repo)
    _git(repo, "add", "-A")
    staged = _git(repo, "diff", "--cached", "--quiet", check=False)
    if staged.returncode == 0:
        print("no generated changes to commit", flush=True)
        return "clean"
    message = rebuild_message(main_sha)
    _git(repo, "commit", "-m", message)
    print(message, flush=True)
    return "committed"


def push_head(repo: Path, branch: str) -> int:
    if not safe_branch(branch):
        print("refusing to push this branch name", file=sys.stderr)
        return 1
    argv = ["git", "-C", str(repo), *push_argv(branch)]
    print(" ".join(push_argv(branch)), flush=True)
    if "--force" in argv or "--force-with-lease" in argv:
        print("refusing to force-push", file=sys.stderr)
        return 1
    result = subprocess.run(argv, text=True)
    return result.returncode


def post_if_new(slug: str, pr: int, body: str, run=None) -> str:
    run = run or subprocess.run
    viewed = run(
        ["gh", "pr", "view", str(pr), "--repo", slug, "--json", "comments"],
        capture_output=True,
        text=True,
    )
    if viewed.returncode != 0:
        print(viewed.stderr or viewed.stdout or "could not read comments", file=sys.stderr)
        return "error"
    payload = json.loads(viewed.stdout or "{}")
    bodies = [item.get("body") or "" for item in payload.get("comments") or []]
    if not should_post(bodies, body):
        print("comment already posted", flush=True)
        return "skipped"
    posted = run(["gh", "pr", "comment", str(pr), "--repo", slug, "--body", body], capture_output=True, text=True)
    if posted.returncode != 0:
        print(posted.stderr or posted.stdout or "could not comment", file=sys.stderr)
        return "error"
    return "posted"


def find_run(slug: str, workflow: str, branch: str, head: str, run, sleep) -> int | None:
    argv = [
        "gh", "run", "list", "--repo", slug, "--workflow", workflow, "--branch", branch,
        "--limit", "20", "--json", "databaseId,headSha,createdAt,event,status",
    ]
    for _attempt in range(12):
        listed = run(argv, capture_output=True, text=True)
        if listed.returncode == 0 and (listed.stdout or "").strip():
            found = newest_run_id(json.loads(listed.stdout), head)
            if found is not None:
                return found
        sleep(5)
    return None


def dispatch_ci(slug: str, branch: str, pr: int, head: str, base: str, run=None, sleep=None) -> list[str]:
    """Start the pull-request workflows on head. GITHUB_TOKEN may dispatch workflow_dispatch."""
    run = run or subprocess.run
    pause = sleep or time.sleep
    failed: list[str] = []
    for workflow in CI_WORKFLOWS:
        fields = dispatch_fields(workflow, pr, head, base)
        started = run(dispatch_argv(workflow, branch, fields) + ["--repo", slug], capture_output=True, text=True)
        if started.returncode != 0:
            print(started.stderr or started.stdout or f"could not dispatch {workflow}", file=sys.stderr)
            failed.append(workflow)
    for workflow in CI_WORKFLOWS:
        if workflow in failed:
            continue
        run_id = find_run(slug, workflow, branch, head, run, pause)
        if run_id is None:
            print(f"{workflow} did not start on {head[:7]}", file=sys.stderr)
            failed.append(workflow)
            continue
        watched = run(["gh", "run", "watch", str(run_id), "--repo", slug, "--exit-status"], capture_output=True, text=True)
        if watched.returncode != 0:
            failed.append(workflow)
    return failed


def export_env(values: dict[str, str]) -> None:
    for key, value in values.items():
        print(f"{key}={value}", flush=True)
    path = os.environ.get("GITHUB_ENV")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            if "\n" in str(value):
                continue
            handle.write(f"{key}={value}\n")


def write_github_output(prs: list[dict]) -> None:
    payload = json.dumps(prs, separators=(",", ":"))
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        print(payload)
        print(len(prs))
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"prs<<ENDPRS\n{payload}\nENDPRS\n")
        handle.write(f"count={len(prs)}\n")


def _optional_int(value: str | None) -> int | None:
    text = (value or "").strip()
    if not text:
        return None
    return int(text)


def _load_open_prs(slug: str) -> list[dict]:
    raw = subprocess.check_output(
        [
            "gh", "pr", "list", "--repo", slug, "--state", "open", "--limit", "200",
            "--json", "number,isDraft,headRefName,headRepository,labels,state",
        ],
        text=True,
    )
    return [normalize_pr(item) for item in json.loads(raw)]


def _run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh generated files on labeled pull requests.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("plan")

    merge = sub.add_parser("merge")
    merge.add_argument("--repo", type=Path, default=Path("."))
    merge.add_argument("--main", default="origin/main")
    merge.add_argument("--pr", type=int)
    merge.add_argument("--slug", default=os.environ.get("GITHUB_REPOSITORY", ""))

    comment = sub.add_parser("comment")
    comment.add_argument("--pr", type=int, required=True)
    comment.add_argument("--slug", default=os.environ.get("GITHUB_REPOSITORY", ""))
    comment.add_argument("--kind", choices=("checks", "push"), required=True)
    comment.add_argument("--main-sha", default=os.environ.get("MAIN_SHA", ""))
    comment.add_argument("--log", type=Path)

    rebuild = sub.add_parser("commit-rebuild")
    rebuild.add_argument("--repo", type=Path, default=Path("."))
    rebuild.add_argument("--main-sha", default=os.environ.get("MAIN_SHA", ""))

    push = sub.add_parser("push")
    push.add_argument("--repo", type=Path, default=Path("."))
    push.add_argument("--branch", default=os.environ.get("BRANCH", ""))
    push.add_argument("--pr", type=int)
    push.add_argument("--slug", default=os.environ.get("GITHUB_REPOSITORY", ""))
    push.add_argument("--main-sha", default=os.environ.get("MAIN_SHA", ""))

    dispatch = sub.add_parser("dispatch-ci")
    dispatch.add_argument("--slug", default=os.environ.get("GITHUB_REPOSITORY", ""))
    dispatch.add_argument("--branch", default=os.environ.get("BRANCH", ""))
    dispatch.add_argument("--pr", type=int, required=True)
    dispatch.add_argument("--head", default="")
    dispatch.add_argument("--base", default=os.environ.get("MAIN_SHA", ""))
    dispatch.add_argument("--repo", type=Path, default=Path("."))

    args = parser.parse_args(argv)
    if args.cmd == "plan":
        slug = os.environ.get("GITHUB_REPOSITORY", "")
        event = os.environ.get("GITHUB_EVENT_NAME", "push")
        selected = select_targets(
            _load_open_prs(slug),
            event=event,
            repo=slug,
            label=os.environ.get("EVENT_LABEL", ""),
            event_pr=_optional_int(os.environ.get("EVENT_PR")),
            input_pr=_optional_int(os.environ.get("INPUT_PR")),
        )
        write_github_output(selected)
        print(f"selected {len(selected)} pull request(s)")
        for item in selected:
            print(f"  #{item['number']} {item['branch']}")
        if event == "workflow_dispatch" and not selected:
            print("No matching open same-repo non-draft pull request with the auto-rebuild label.", file=sys.stderr)
            return 1
        return 0

    if args.cmd == "merge":
        def commenter(body: str) -> None:
            if args.pr and args.slug and post_if_new(args.slug, args.pr, body) == "error":
                raise RuntimeError("could not comment on the pull request")

        try:
            result = perform_merge(args.repo, args.main, commenter=commenter if args.pr else None)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        export_env({
            "STATUS": result["status"],
            "MAIN_SHA": result["main_sha"],
            "SHORT_SHA": result["short_sha"],
            "BRANCH": result["branch"],
        })
        return 1 if result["status"] == "error" else 0

    if args.cmd == "comment":
        if args.kind == "checks":
            log = args.log.read_text(encoding="utf-8") if args.log else ""
            step, reason = parse_failure(log)
            body = checks_comment(args.main_sha or "unknown", step, reason)
        else:
            body = push_comment(args.main_sha or "unknown")
        status = post_if_new(args.slug, args.pr, body)
        return 0 if status in ("posted", "skipped") else 1

    if args.cmd == "commit-rebuild":
        try:
            status = commit_rebuild(args.repo, args.main_sha)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        head = _git(args.repo, "rev-parse", "HEAD").stdout.strip()
        export_env({"REBUILD": status, "HEAD_SHA": head})
        return 0

    if args.cmd == "push":
        code = push_head(args.repo, args.branch)
        if code != 0 and args.pr and args.slug:
            post_if_new(args.slug, args.pr, push_comment(args.main_sha or "unknown"))
        return code

    if args.cmd == "dispatch-ci":
        head = args.head or _git(args.repo, "rev-parse", "HEAD").stdout.strip()
        failed = dispatch_ci(args.slug, args.branch, args.pr, head, args.base)
        if failed:
            post_if_new(args.slug, args.pr, ci_comment(head, failed))
            print("CI_FAILED " + " ".join(failed), flush=True)
            return 1
        print("CI passed", flush=True)
        return 0
    return 2


def main(argv: list[str] | None = None) -> int:
    return _run(argv)


if __name__ == "__main__":
    sys.exit(main())
