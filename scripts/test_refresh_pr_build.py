#!/usr/bin/env python3
"""Generated-file refresh: classify conflicts, merge, and do not force-push.

The dry run builds a throwaway branch inside a temporary repository, merges
main, checks the result, and deletes that branch.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import refresh_pr_build


ROOT = Path(__file__).resolve().parents[1]
REPO = "Clampdown-web/agentscout"
DRY_BRANCH = "cursor/refresh-dry-run-5dfb"


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout or f"git {args}")
    return result


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True, text=True)
    git(path, "config", "user.email", "refresh-test@example.com")
    git(path, "config", "user.name", "refresh test")
    git(path, "config", "commit.gpgsign", "false")


def commit(repo: Path, name: str, text: str, message: str) -> None:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    git(repo, "add", "--", name)
    git(repo, "commit", "-m", message)


class GeneratedFilesTest(unittest.TestCase):
    def test_published_html_and_build_outputs_are_generated(self):
        generated = [
            "sitemap.xml",
            "sitemap-core.xml",
            "sitemap-news.xml",
            "tools/macswarm.html",
            "best/example.html",
            "compare/example.html",
            "api/tools.json",
            "api/metrics.json",
            "pagefind/pagefind.js",
            "search/names.json",
            "search/words.json",
            "data/lastmod.json",
            "og/tools/macswarm.png",
            "og.png",
            "llms.txt",
            "cloudflare-mcp-worker/catalog_snapshot.json",
            "cloudflare-mcp-worker/products_snapshot.json",
            "mcp-server/src/products_snapshot.json",
            ".well-known/acp.json",
            ".well-known/openapi.yaml",
        ]
        for path in generated:
            self.assertTrue(refresh_pr_build.is_generated(path), path)

    def test_source_and_data_are_not_generated(self):
        source = [
            "tools.json",
            "tool_rich.json",
            "data/index_hold.json",
            "build_site.py",
            "scripts/morning_pipeline.py",
            "cloudflare-mcp-worker/test/catalog.test.mjs",
            ".well-known/brave-rewards-verification.txt",
            "notes/plan.md",
        ]
        for path in source:
            self.assertFalse(refresh_pr_build.is_generated(path), path)

    def test_split_conflicts_stops_on_any_source_file(self):
        generated, source = refresh_pr_build.split_conflicts(
            ["sitemap.xml", "tools/macswarm.html", "tools.json"]
        )
        self.assertEqual(source, ["tools.json"])
        self.assertEqual(generated, ["sitemap.xml", "tools/macswarm.html"])


class SelectTargetsTest(unittest.TestCase):
    def test_push_selects_labeled_same_repo_prs_only(self):
        prs = [
            {
                "number": 180,
                "isDraft": False,
                "headRefName": "indexable-macswarm-solari-2026-11-19",
                "headRepository": {"nameWithOwner": REPO},
                "labels": [],
                "state": "OPEN",
            },
            {
                "number": 201,
                "isDraft": False,
                "headRefName": "morning-build-2026-11-20",
                "headRepository": {"nameWithOwner": REPO},
                "labels": [{"name": "auto-rebuild"}],
                "state": "OPEN",
            },
            {
                "number": 202,
                "isDraft": True,
                "headRefName": "morning-build-draft",
                "headRepository": {"nameWithOwner": REPO},
                "labels": [{"name": "auto-rebuild"}],
                "state": "OPEN",
            },
            {
                "number": 203,
                "isDraft": False,
                "headRefName": "fork-page",
                "headRepository": {"nameWithOwner": "other/agentscout"},
                "labels": [{"name": "auto-rebuild"}],
                "state": "OPEN",
            },
        ]
        selected = refresh_pr_build.select_targets(prs, event="push", repo=REPO)
        self.assertEqual(selected, [{"number": 201, "branch": "morning-build-2026-11-20"}])

    def test_dispatch_and_label_events_stay_narrow(self):
        prs = [
            {
                "number": 180,
                "draft": False,
                "branch": "indexable-macswarm-solari-2026-11-19",
                "head_repo": REPO,
                "labels": [],
                "state": "open",
            },
            {
                "number": 204,
                "draft": False,
                "branch": "indexable-example-2026-11-20",
                "head_repo": REPO,
                "labels": ["auto-rebuild"],
                "state": "open",
            },
        ]
        self.assertEqual(
            refresh_pr_build.select_targets(prs, event="workflow_dispatch", repo=REPO, input_pr=180),
            [],
        )
        self.assertEqual(
            refresh_pr_build.select_targets(prs, event="workflow_dispatch", repo=REPO, input_pr=204),
            [{"number": 204, "branch": "indexable-example-2026-11-20"}],
        )
        self.assertEqual(
            refresh_pr_build.select_targets(
                prs, event="pull_request", repo=REPO, label="bug", event_pr=204
            ),
            [],
        )
        self.assertEqual(
            refresh_pr_build.select_targets(
                prs, event="pull_request", repo=REPO, label="auto-rebuild", event_pr=204
            ),
            [{"number": 204, "branch": "indexable-example-2026-11-20"}],
        )


class MergeDryRunTest(unittest.TestCase):
    def test_dry_run_resolves_generated_conflicts_and_deletes_the_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            commit(repo, "sitemap.xml", "<urlset>base</urlset>\n", "base sitemap")
            commit(repo, "tools.json", '{"tools":[]}\n', "base tools")
            git(repo, "checkout", "-b", DRY_BRANCH)
            commit(repo, "sitemap.xml", "<urlset>pr</urlset>\n", "pr sitemap")
            commit(repo, "tools.json", '{"tools":["pr"]}\n', "pr tools")
            git(repo, "checkout", "main")
            commit(repo, "sitemap.xml", "<urlset>main</urlset>\n", "main sitemap")
            git(repo, "checkout", DRY_BRANCH)
            result = refresh_pr_build.perform_merge(repo, "main")
            self.assertEqual(result["status"], "merged")
            self.assertEqual((repo / "sitemap.xml").read_text(encoding="utf-8"), "<urlset>main</urlset>\n")
            self.assertEqual((repo / "tools.json").read_text(encoding="utf-8"), '{"tools":["pr"]}\n')
            parents = git(repo, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
            self.assertEqual(len(parents), 3)
            git(repo, "checkout", "main")
            git(repo, "branch", "-D", DRY_BRANCH)
            names = git(repo, "branch", "--list", DRY_BRANCH).stdout.strip()
            self.assertEqual(names, "")

    def test_a_source_conflict_aborts_and_comments_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            commit(repo, "tools.json", "base\n", "base")
            commit(repo, "sitemap.xml", "base\n", "sitemap")
            git(repo, "checkout", "-b", "page-update")
            commit(repo, "tools.json", "pr\n", "pr tools")
            before = git(repo, "rev-parse", "HEAD").stdout.strip()
            git(repo, "checkout", "main")
            commit(repo, "tools.json", "main\n", "main tools")
            git(repo, "checkout", "page-update")
            comments = []
            result = refresh_pr_build.perform_merge(repo, "main", commenter=comments.append)
            self.assertEqual(result["status"], "source_conflict")
            self.assertEqual(result["files"], ["tools.json"])
            self.assertEqual((repo / "tools.json").read_text(encoding="utf-8"), "pr\n")
            self.assertEqual(git(repo, "rev-parse", "HEAD").stdout.strip(), before)
            self.assertFalse(refresh_pr_build._merge_in_progress(repo))
            self.assertEqual(len(comments), 1)
            self.assertIn("tools.json", comments[0])
            self.assertIn("left this branch unchanged", comments[0])

    def test_an_up_to_date_branch_is_not_rewritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            commit(repo, "sitemap.xml", "same\n", "sitemap")
            head = git(repo, "rev-parse", "HEAD").stdout.strip()
            result = refresh_pr_build.perform_merge(repo, "main")
            self.assertEqual(result["status"], "up_to_date")
            self.assertEqual(git(repo, "rev-parse", "HEAD").stdout.strip(), head)

    def test_a_clean_merge_is_a_merge_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            commit(repo, "readme.txt", "base\n", "base")
            git(repo, "checkout", "-b", "page")
            commit(repo, "tools.json", "pr\n", "pr source")
            git(repo, "checkout", "main")
            commit(repo, "readme.txt", "main\n", "main readme")
            git(repo, "checkout", "page")
            result = refresh_pr_build.perform_merge(repo, "main")
            self.assertEqual(result["status"], "merged")
            self.assertEqual((repo / "tools.json").read_text(encoding="utf-8"), "pr\n")
            self.assertEqual((repo / "readme.txt").read_text(encoding="utf-8"), "main\n")
            parents = git(repo, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
            self.assertEqual(len(parents), 3)


class CommentAndDispatchTest(unittest.TestCase):
    def test_rebuild_message_and_push_are_not_a_force_push(self):
        self.assertEqual(
            refresh_pr_build.rebuild_message("abcdef1234567890"),
            "chore: rebuild generated files on main abcdef1",
        )
        argv = refresh_pr_build.push_argv("morning-build-2026-11-20")
        self.assertNotIn("--force", argv)
        self.assertNotIn("--force-with-lease", argv)
        self.assertEqual(argv, ["git", "push", "origin", "HEAD:morning-build-2026-11-20"])

    def test_comments_post_once_and_name_the_failed_check(self):
        step, reason = refresh_pr_build.parse_failure("noise\nPIPELINE FAILED: tests: scripts/test_publish_gate.py: failed\n")
        body = refresh_pr_build.checks_comment("abc1234def", step, reason)
        self.assertIn("tests failed:", body)
        self.assertTrue(refresh_pr_build.should_post([], body))
        self.assertFalse(refresh_pr_build.should_post([body], body))
        calls = {"comments": 0}

        def run(argv, **_kwargs):
            class Result:
                returncode = 0
                stderr = ""
                stdout = ""

            result = Result()
            if "view" in argv:
                if calls["comments"]:
                    result.stdout = json.dumps({"comments": [{"body": body}]})
                else:
                    result.stdout = json.dumps({"comments": []})
            else:
                calls["comments"] += 1
            return result

        self.assertEqual(refresh_pr_build.post_if_new(REPO, 9, body, run), "posted")
        self.assertEqual(refresh_pr_build.post_if_new(REPO, 9, body, run), "skipped")
        self.assertEqual(calls["comments"], 1)

    def test_newest_dispatch_run_ignores_pull_request_events(self):
        rows = [
            {"databaseId": 1, "headSha": "aaa", "createdAt": "2026-11-20T10:00:00Z", "event": "pull_request"},
            {"databaseId": 2, "headSha": "aaa", "createdAt": "2026-11-20T11:00:00Z", "event": "workflow_dispatch"},
        ]
        self.assertEqual(refresh_pr_build.newest_run_id(rows, "aaa"), 2)
        fields = refresh_pr_build.dispatch_fields("guardrails.yml", 12, "head", "base")
        argv = refresh_pr_build.dispatch_argv("guardrails.yml", "feature", fields)
        self.assertIn("guardrails.yml", argv)
        self.assertIn("-f", argv)
        self.assertNotIn("--force", argv)

    def test_dispatch_can_start_checks_without_waiting(self):
        calls = []

        def run(argv, **_kwargs):
            calls.append(list(argv))

            class Result:
                returncode = 0
                stdout = ""
                stderr = ""

            result = Result()
            if argv[:3] == ["gh", "run", "list"]:
                result.stdout = json.dumps([{
                    "databaseId": 9,
                    "headSha": "abc",
                    "createdAt": "2026-11-21T00:00:00Z",
                    "event": "workflow_dispatch",
                    "status": "completed",
                }])
            return result

        waited = refresh_pr_build.dispatch_ci(
            REPO, "feature", 7, "abc", "def", run=run, sleep=lambda _seconds: None
        )
        self.assertEqual(waited, [])
        self.assertTrue(any(argv[:3] == ["gh", "run", "watch"] for argv in calls))

        calls.clear()

        def boom(_seconds):
            raise AssertionError("should not sleep")

        started = refresh_pr_build.dispatch_ci(
            REPO, "bot/mcp-health-2026-11-21-1", 7, "abc", "def", run=run, sleep=boom, wait=False
        )
        self.assertEqual(started, [])
        workflows = [argv[3] for argv in calls if argv[:3] == ["gh", "workflow", "run"]]
        self.assertEqual(workflows, ["guardrails.yml", "security.yml", "gitleaks.yml", "codeql.yml"])
        guard = next(argv for argv in calls if argv[:4] == ["gh", "workflow", "run", "guardrails.yml"])
        self.assertIn("--ref", guard)
        self.assertIn("bot/mcp-health-2026-11-21-1", guard)
        self.assertIn("pr_number=7", guard)
        self.assertIn("head_sha=abc", guard)
        self.assertIn("base_sha=def", guard)
        self.assertFalse(any("watch" in argv for argv in calls))

    def test_workflow_serializes_pushes_and_reruns_ci(self):
        text = (ROOT / ".github" / "workflows" / "refresh-pr-builds.yml").read_text(encoding="utf-8")
        self.assertIn("auto-rebuild", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("labeled", text)
        self.assertIn("branches: [main]", text)
        self.assertIn("refresh_pr_build.py", text)
        plan = text.split("- name: Choose pull requests", 1)[1].split("- name:", 1)[0]
        self.assertIn("GH_TOKEN: ${{ github.token }}", plan)
        self.assertIn("git fetch --no-tags origin main", text)
        self.assertIn("build_site.py", text)
        self.assertIn("build_lastmod.py", text)
        self.assertIn("daily_update.py", text)
        self.assertIn("PIPELINE_SKIP: live", text)
        self.assertIn("morning_pipeline.py", text)
        self.assertIn("dispatch-ci", text)
        self.assertIn("group: refresh-pr-builds", text)
        self.assertIn("group: refresh-pr-${{ matrix.pr.number }}", text)
        self.assertIn("max-parallel: 1", text)
        self.assertIn("cancel-in-progress: false", text)
        self.assertIn("timeout-minutes: 120", text)
        self.assertIn("cache: pip", text)
        self.assertIn("actions: write", text)
        self.assertNotIn("--force", text)
        self.assertNotIn("force-with-lease", text)
        self.assertNotIn("pull_request_target", text)


if __name__ == "__main__":
    unittest.main()
