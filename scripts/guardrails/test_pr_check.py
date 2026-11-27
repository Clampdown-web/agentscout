#!/usr/bin/env python3
"""Synthetic-diff tests for the pull-request guardrail and the live page rules.

Run from anywhere: python3 scripts/guardrails/test_pr_check.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import pages  # noqa: E402
import post_deploy  # noqa: E402
import pr_check  # noqa: E402

TODAY = date(2026, 11, 18)
TODAY_STAMP = "2026-11-18T12:00:00-08:00"
YESTERDAY_STAMP = "2026-11-17T12:00:00-08:00"
REASON = "Reason this page exists: best open source MCP servers for Postgres\n"
SITE = "https://agentscouthq.com"


def document(canonical: str, body: str = "A guide to open source MCP servers for Postgres.", robots: str | None = None) -> str:
    robots_tag = f'<meta name="robots" content="{robots}">\n' if robots else ""
    return (
        "<!doctype html><html><head>\n"
        f'<link rel="canonical" href="{canonical}">\n'
        f"{robots_tag}"
        "</head><body><main><p>"
        f"{body}"
        "</p></main></body></html>\n"
    )


def sitemap(urls: list[str]) -> str:
    locs = "\n".join(f"  <url><loc>{url}</loc></url>" for url in urls)
    return f"<urlset>\n{locs}\n</urlset>\n"


class Repo:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name)
        self.git("init", "-b", "main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")

    def git(self, *args: str, env: dict | None = None) -> str:
        merged = os.environ.copy()
        merged.setdefault("GIT_AUTHOR_NAME", "Test")
        merged.setdefault("GIT_AUTHOR_EMAIL", "test@example.com")
        merged.setdefault("GIT_COMMITTER_NAME", "Test")
        merged.setdefault("GIT_COMMITTER_EMAIL", "test@example.com")
        if env:
            merged.update(env)
        result = subprocess.run(
            ["git", "-C", str(self.path), *args],
            check=True,
            capture_output=True,
            text=True,
            env=merged,
        )
        return result.stdout.strip()

    def write(self, rel: str, text: str) -> None:
        path = self.path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, message: str, when: str) -> None:
        self.git("add", "-A")
        self.git(
            "commit",
            "-m",
            message,
            env={"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when},
        )

    def close(self) -> None:
        self._tmp.cleanup()


class SourceRulesTest(unittest.TestCase):
    def test_prompts_data_is_paired_with_prompt_pages(self) -> None:
        self.assertEqual(pages.source_outputs("data/prompts.json"), ("prompts/", "sitemap.xml"))
        self.assertTrue(pages.output_satisfies("prompts/index.html", ("prompts/", "sitemap.xml")))
        self.assertTrue(pages.output_satisfies("sitemap.xml", ("prompts/", "sitemap.xml")))
        self.assertFalse(pages.output_satisfies("tools/other.html", ("prompts/", "sitemap.xml")))

    def test_snapshots_and_guardrail_scripts_are_not_page_sources(self) -> None:
        self.assertIsNone(pages.source_outputs("data/stars/2026-11-18.json"))
        self.assertEqual(pages.source_outputs("data/mcp-health/state.json"), pages.BROAD)
        self.assertEqual(pages.source_outputs("data/mcp-health/2026-11.jsonl"), pages.BROAD)
        self.assertIsNone(pages.source_outputs("scripts/guardrails/pr_check.py"))
        self.assertIsNone(pages.source_outputs(".github/workflows/guardrails.yml"))
        self.assertIsNone(pages.source_outputs("build_openapi.py"))
        self.assertIsNone(pages.source_outputs("build_og_neon.py"))

    def test_index_html_normalizes_to_the_directory_url(self) -> None:
        self.assertEqual(pages.page_public_url("prompts/index.html"), f"{SITE}/prompts/")
        self.assertEqual(pages.page_public_url("index.html"), f"{SITE}/")
        raw = f"{SITE}/prompts/index.html"
        self.assertEqual(pages.normalize_url(raw), f"{SITE}/prompts/")
        self.assertEqual(
            pages.normalize_url(f"{SITE}/prompts/"),
            pages.normalize_url(raw),
        )

    def test_main_text_drops_a_script_whose_end_tag_has_space(self) -> None:
        script = "<main><script>alert(1)</script ><p>Visible guide text</p></main>"
        style = "<main><style>body{color:red}</style ><p>Visible guide text</p></main>"
        self.assertEqual(pages.main_text(script), "Visible guide text")
        self.assertEqual(pages.main_text(style), "Visible guide text")

    def test_reason_line_rejects_placeholders(self) -> None:
        self.assertIsNone(pages.reason_problem(REASON, ["guides/a.html"]))
        self.assertIsNotNone(pages.reason_problem("", ["guides/a.html"]))
        self.assertIsNotNone(pages.reason_problem("Reason this page exists:\n", ["guides/a.html"]))
        self.assertIsNotNone(pages.reason_problem("Reason this page exists: TODO\n", ["guides/a.html"]))
        self.assertIsNone(pages.reason_problem("Reason this page exists:\n", []))


class PullRequestDiffTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo()

    def tearDown(self) -> None:
        self.repo.close()

    def _seed_main(self, urls: list[str] | None = None) -> None:
        self.repo.write("README.md", "seed\n")
        self.repo.write("sitemap.xml", sitemap(urls or []))
        self.repo.commit("seed", YESTERDAY_STAMP)

    def _start_pr(self) -> None:
        self.repo.git("checkout", "-b", "pr")

    def _failures(self, body: str = "", today: date = TODAY) -> list[str]:
        return pr_check.evaluate(self.repo.path, "main", "HEAD", body, "main", today)

    def test_generator_change_without_html_fails(self) -> None:
        self._seed_main()
        self._start_pr()
        self.repo.write("data/prompts.json", '{"prompts": []}\n')
        self.repo.commit("edit prompts data only", TODAY_STAMP)
        failures = self._failures()
        self.assertEqual(len(failures), 1)
        self.assertIn("data/prompts.json", failures[0])
        self.assertIn("prompts/*.html", failures[0])
        self.assertIn("does not rebuild", failures[0])

    def test_generator_change_with_unrelated_html_still_fails(self) -> None:
        self._seed_main()
        self.repo.write("tools/other.html", document(f"{SITE}/tools/other.html"))
        self.repo.commit("unrelated page", YESTERDAY_STAMP)
        self._start_pr()
        self.repo.write("data/prompts.json", '{"prompts": ["new"]}\n')
        self.repo.write("tools/other.html", document(f"{SITE}/tools/other.html", body="Touched the wrong page."))
        self.repo.commit("prompts data and an unrelated tool page", TODAY_STAMP)
        failures = self._failures()
        self.assertTrue(any("data/prompts.json" in item for item in failures))

    def test_mcp_health_without_html_fails(self) -> None:
        self._seed_main()
        self._start_pr()
        self.repo.write("data/mcp-health/summary.json", '{"servers": {}}\n')
        self.repo.write("data/mcp-health/2026-11.jsonl", '{"slug": "one"}\n')
        self.repo.commit("health data only", TODAY_STAMP)
        failures = self._failures()
        self.assertEqual(len(failures), 1)
        self.assertIn("data/mcp-health/summary.json", failures[0])
        self.assertIn("data/mcp-health/2026-11.jsonl", failures[0])
        self.assertIn("published *.html", failures[0])

    def test_mcp_health_with_rebuilt_html_passes(self) -> None:
        self._seed_main([f"{SITE}/tools/one.html"])
        self.repo.write("tools/one.html", document(f"{SITE}/tools/one.html"))
        self.repo.commit("tool page", YESTERDAY_STAMP)
        self._start_pr()
        self.repo.write("data/mcp-health/summary.json", '{"servers": {"one": {"display": "rate"}}}\n')
        self.repo.write("data/mcp-health/state.json", '{"next_slug": "two"}\n')
        self.repo.write(
            "tools/one.html",
            document(f"{SITE}/tools/one.html", body="Responded 3/3 checks in last 30 days."),
        )
        self.repo.commit("health data and the rebuilt page", TODAY_STAMP)
        self.assertEqual(self._failures("New indexable pages in this PR: 0\n"), [])

    def test_generator_change_with_paired_page_passes(self) -> None:
        self._seed_main([f"{SITE}/prompts/"])
        self.repo.write("prompts/index.html", document(f"{SITE}/prompts/"))
        self.repo.write("data/prompts.json", "{}\n")
        self.repo.commit("prompts exist", YESTERDAY_STAMP)
        self._start_pr()
        self.repo.write("data/prompts.json", '{"changed": true}\n')
        self.repo.write("prompts/index.html", document(f"{SITE}/prompts/", body="Regenerated prompt library page."))
        self.repo.commit("regenerate prompts", TODAY_STAMP)
        self.assertEqual(self._failures(), [])

    def test_sitemap_satisfies_a_paired_source(self) -> None:
        self._seed_main()
        self._start_pr()
        self.repo.write("data/prompts.json", "{}\n")
        self.repo.write("sitemap.xml", sitemap([f"{SITE}/prompts/"]))
        self.repo.commit("data and sitemap", TODAY_STAMP)
        self.assertEqual(self._failures(), [])

    def test_new_indexable_page_needs_a_real_reason(self) -> None:
        self._seed_main()
        self._start_pr()
        path = "guides/postgres-mcp.html"
        url = f"{SITE}/{path}"
        self.repo.write(path, document(url))
        self.repo.write("sitemap.xml", sitemap([url]))
        self.repo.commit("add a guide", TODAY_STAMP)
        failures = self._failures("Reason this page exists: TODO\n")
        self.assertTrue(any("Reason this page exists:" in item for item in failures))
        self.assertEqual(pr_check.evaluate(self.repo.path, "main", "HEAD", REASON, "main", TODAY), [])

    def test_prompts_index_canonical_matches_sitemap_index_html(self) -> None:
        self._seed_main()
        self._start_pr()
        self.repo.write("prompts/index.html", document(f"{SITE}/prompts/"))
        self.repo.write("sitemap.xml", sitemap([f"{SITE}/prompts/index.html"]))
        self.repo.commit("prompt library", TODAY_STAMP)
        self.assertEqual(self._failures(REASON), [])

    def test_noindex_page_in_the_sitemap_fails(self) -> None:
        self._seed_main()
        self._start_pr()
        path = "news/story.html"
        url = f"{SITE}/{path}"
        self.repo.write(path, document(url, robots="noindex,follow"))
        self.repo.write("sitemap.xml", sitemap([url]))
        self.repo.commit("noindex but listed", TODAY_STAMP)
        failures = self._failures()
        self.assertTrue(any("is noindex, but sitemap.xml lists it" in item for item in failures))
        self.assertFalse(any("Reason this page exists:" in item for item in failures))

    def test_indexable_page_missing_from_the_sitemap_fails(self) -> None:
        self._seed_main()
        self._start_pr()
        path = "guides/missing.html"
        self.repo.write(path, document(f"{SITE}/{path}"))
        self.repo.commit("page without sitemap", TODAY_STAMP)
        failures = self._failures(REASON)
        self.assertTrue(any("does not list" in item for item in failures))
        self.assertFalse(any("daily cap" in item for item in failures))

    def test_canonical_mismatch_fails(self) -> None:
        self._seed_main()
        self._start_pr()
        path = "guides/wrong.html"
        url = f"{SITE}/{path}"
        self.repo.write(path, document(f"{SITE}/guides/other.html"))
        self.repo.write("sitemap.xml", sitemap([url]))
        self.repo.commit("bad canonical", TODAY_STAMP)
        failures = self._failures(REASON)
        self.assertTrue(any("canonical is" in item and "expected" in item for item in failures))

    def test_daily_cap_counts_this_pr_and_main_today(self) -> None:
        self.repo.write("sitemap.xml", sitemap([f"{SITE}/old.html"]))
        self.repo.commit("yesterday", YESTERDAY_STAMP)
        self.repo.write(
            "sitemap.xml",
            sitemap([f"{SITE}/old.html", f"{SITE}/tools/one.html", f"{SITE}/tools/two.html"]),
        )
        self.repo.commit("two urls today", TODAY_STAMP)
        self.repo.git("checkout", "-b", "pr")
        for name in ("alpha", "beta"):
            path = f"guides/{name}.html"
            url = f"{SITE}/{path}"
            self.repo.write(path, document(url))
        current = sitemap(
            [
                f"{SITE}/old.html",
                f"{SITE}/tools/one.html",
                f"{SITE}/tools/two.html",
                f"{SITE}/guides/alpha.html",
                f"{SITE}/guides/beta.html",
            ]
        )
        self.repo.write("sitemap.xml", current)
        self.repo.commit("two new guides", TODAY_STAMP)
        failures = pr_check.evaluate(self.repo.path, "main", "HEAD", REASON, "main", TODAY)
        self.assertTrue(any("daily free cap of 3" in item for item in failures), failures)
        self.assertTrue(any("guides/alpha.html" in item for item in failures))
        self.assertTrue(any(f"{SITE}/tools/one.html" in item for item in failures))

    def test_three_new_urls_across_main_and_the_pr_pass(self) -> None:
        self.repo.write("sitemap.xml", sitemap([]))
        self.repo.commit("yesterday", YESTERDAY_STAMP)
        self.repo.write("sitemap.xml", sitemap([f"{SITE}/tools/one.html"]))
        self.repo.commit("one url today", TODAY_STAMP)
        self.repo.git("checkout", "-b", "pr")
        for name in ("alpha", "beta"):
            path = f"guides/{name}.html"
            self.repo.write(path, document(f"{SITE}/{path}"))
        self.repo.write(
            "sitemap.xml",
            sitemap([f"{SITE}/tools/one.html", f"{SITE}/guides/alpha.html", f"{SITE}/guides/beta.html"]),
        )
        self.repo.commit("two guides", TODAY_STAMP)
        failures = pr_check.evaluate(self.repo.path, "main", "HEAD", REASON, "main", TODAY)
        self.assertEqual(failures, [], failures)

    def test_yesterdays_sitemap_urls_do_not_count(self) -> None:
        urls = [f"{SITE}/tools/{i}.html" for i in range(5)]
        self.repo.write("sitemap.xml", sitemap(urls))
        self.repo.commit("five yesterday", YESTERDAY_STAMP)
        self.repo.git("checkout", "-b", "pr")
        path = "guides/only.html"
        url = f"{SITE}/{path}"
        self.repo.write(path, document(url))
        self.repo.write("sitemap.xml", sitemap(urls + [url]))
        self.repo.commit("one today on the branch", TODAY_STAMP)
        failures = pr_check.evaluate(self.repo.path, "main", "HEAD", REASON, "main", TODAY)
        self.assertEqual(failures, [], failures)

    def _write_tools(self, entries: list[dict]) -> None:
        import json
        self.repo.write("tools.json", json.dumps(entries))

    def test_paid_page_on_main_does_not_consume_the_free_cap(self) -> None:
        """2 free + 1 paid already today, plus 1 free in the PR, is 3 free and must pass."""
        self.repo.write("sitemap.xml", sitemap([f"{SITE}/old.html"]))
        self._write_tools([
            {"slug": "one", "name": "One"},
            {"slug": "two", "name": "Two"},
            {"slug": "kurodyne", "name": "Kurodyne", "fast_track": True},
        ])
        self.repo.commit("yesterday", YESTERDAY_STAMP)
        self.repo.write(
            "sitemap.xml",
            sitemap([
                f"{SITE}/old.html",
                f"{SITE}/tools/one.html",
                f"{SITE}/tools/two.html",
                f"{SITE}/tools/kurodyne.html",
            ]),
        )
        self.repo.commit("two free and one paid today", TODAY_STAMP)
        self.repo.git("checkout", "-b", "pr")
        path = "guides/alpha.html"
        url = f"{SITE}/{path}"
        self.repo.write(path, document(url))
        self.repo.write(
            "sitemap.xml",
            sitemap([
                f"{SITE}/old.html",
                f"{SITE}/tools/one.html",
                f"{SITE}/tools/two.html",
                f"{SITE}/tools/kurodyne.html",
                url,
            ]),
        )
        self.repo.commit("one free guide", TODAY_STAMP)
        failures = pr_check.evaluate(self.repo.path, "main", "HEAD", REASON, "main", TODAY)
        self.assertEqual(failures, [], failures)

    def test_paid_page_in_the_pr_is_read_from_head_tools_json(self) -> None:
        """3 free already on main; a Fast-Track in this PR must not trip the free cap."""
        self.repo.write("sitemap.xml", sitemap([]))
        self._write_tools([])
        self.repo.commit("yesterday", YESTERDAY_STAMP)
        self.repo.write(
            "sitemap.xml",
            sitemap([f"{SITE}/tools/one.html", f"{SITE}/tools/two.html", f"{SITE}/guides/alpha.html"]),
        )
        self.repo.write("guides/alpha.html", document(f"{SITE}/guides/alpha.html"))
        self.repo.write("tools/one.html", document(f"{SITE}/tools/one.html"))
        self.repo.write("tools/two.html", document(f"{SITE}/tools/two.html"))
        self.repo.commit("three free today", TODAY_STAMP)
        self.repo.git("checkout", "-b", "pr")
        path = "tools/kurodyne.html"
        url = f"{SITE}/{path}"
        self.repo.write(path, document(url))
        self._write_tools([{"slug": "kurodyne", "name": "Kurodyne", "fast_track": True}])
        self.repo.write(
            "sitemap.xml",
            sitemap([
                f"{SITE}/tools/one.html",
                f"{SITE}/tools/two.html",
                f"{SITE}/guides/alpha.html",
                url,
            ]),
        )
        self.repo.commit("paid fast-track", TODAY_STAMP)
        failures = pr_check.evaluate(self.repo.path, "main", "HEAD", REASON, "main", TODAY)
        self.assertEqual(failures, [], failures)

    def test_third_paid_page_fails_the_paid_cap(self) -> None:
        self.repo.write("sitemap.xml", sitemap([]))
        self._write_tools([
            {"slug": "pin-a", "listing_tier": "category_pin"},
            {"slug": "sponsor-a", "listing_tier": "weekly_sponsor"},
        ])
        self.repo.commit("yesterday", YESTERDAY_STAMP)
        self.repo.write(
            "sitemap.xml",
            sitemap([f"{SITE}/tools/pin-a.html", f"{SITE}/tools/sponsor-a.html"]),
        )
        self.repo.commit("two paid today", TODAY_STAMP)
        self.repo.git("checkout", "-b", "pr")
        path = "tools/kurodyne.html"
        url = f"{SITE}/{path}"
        self.repo.write(path, document(url))
        self._write_tools([
            {"slug": "pin-a", "listing_tier": "category_pin"},
            {"slug": "sponsor-a", "listing_tier": "weekly_sponsor"},
            {"slug": "kurodyne", "fast_track": True},
        ])
        self.repo.write(
            "sitemap.xml",
            sitemap([f"{SITE}/tools/pin-a.html", f"{SITE}/tools/sponsor-a.html", url]),
        )
        self.repo.commit("third paid", TODAY_STAMP)
        failures = pr_check.evaluate(self.repo.path, "main", "HEAD", REASON, "main", TODAY)
        self.assertTrue(any("daily paid cap of 2" in item for item in failures), failures)
        self.assertFalse(any("daily free cap" in item for item in failures), failures)

    def test_three_free_and_two_paid_pass(self) -> None:
        self.repo.write("sitemap.xml", sitemap([]))
        self._write_tools([
            {"slug": "kurodyne", "fast_track": True},
            {"slug": "pin-me", "listing_tier": "category_pin"},
        ])
        self.repo.commit("yesterday", YESTERDAY_STAMP)
        self.repo.write(
            "sitemap.xml",
            sitemap([
                f"{SITE}/tools/one.html",
                f"{SITE}/tools/two.html",
                f"{SITE}/guides/alpha.html",
                f"{SITE}/tools/kurodyne.html",
                f"{SITE}/tools/pin-me.html",
            ]),
        )
        self.repo.commit("three free and two paid", TODAY_STAMP)
        self.repo.git("checkout", "-b", "pr")
        # No new pages; a tools.json typo fix should not fail the cap.
        self.repo.write("README.md", "note\n")
        self.repo.commit("docs only", TODAY_STAMP)
        failures = pr_check.evaluate(self.repo.path, "main", "HEAD", "n/a", "main", TODAY)
        self.assertEqual(failures, [], failures)

    def test_guardrail_and_star_snapshot_changes_do_not_require_html(self) -> None:
        self._seed_main()
        self._start_pr()
        self.repo.write("scripts/guardrails/pr_check.py", "# guard\n")
        self.repo.write("data/stars/2026-11-18.json", "{}\n")
        self.repo.write(".github/workflows/guardrails.yml", "name: guardrails\n")
        self.repo.commit("tooling only", TODAY_STAMP)
        self.assertEqual(self._failures(), [])


class LiveCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo()

    def tearDown(self) -> None:
        self.repo.close()

    def _commit_pair(self, first: dict[str, str], second: dict[str, str]) -> str:
        for path, text in first.items():
            self.repo.write(path, text)
        self.repo.commit("base", YESTERDAY_STAMP)
        for path, text in second.items():
            self.repo.write(path, text)
        self.repo.commit("deploy", TODAY_STAMP)
        return self.repo.git("rev-parse", "HEAD")

    def test_failing_page_is_not_pinged_and_a_passing_page_is(self) -> None:
        ok = "guides/ok.html"
        bad = "guides/bad.html"
        ok_url = f"{SITE}/{ok}"
        sha = self._commit_pair(
            {ok: document(ok_url, body="old"), bad: document(f"{SITE}/{bad}", body="old")},
            {ok: document(ok_url, body="A live page about MCP servers."), bad: document(f"{SITE}/{bad}", body="still bad")},
        )
        pinged: list[str] = []

        def fetch(url: str):
            if url.endswith("/sitemap.xml"):
                return 200, {}, sitemap([ok_url]), url
            if url == ok_url:
                return 200, {}, document(ok_url, body="A live page about MCP servers."), url
            if url == f"{SITE}/{bad}":
                return 404, {}, "missing", url
            raise AssertionError(url)

        code = post_deploy.run(
            self.repo.path,
            sha,
            fetch=fetch,
            ping=pinged.extend,
            sleep=lambda _seconds: None,
            attempts=2,
            workers=1,
        )
        self.assertEqual(code, 1)
        self.assertEqual(pinged, [ok_url])

    def test_all_passing_pages_are_pinged_once(self) -> None:
        path = "guides/ok.html"
        url = f"{SITE}/{path}"
        sha = self._commit_pair(
            {"README.md": "x\n"},
            {path: document(url)},
        )
        pinged: list[list[str]] = []

        def fetch(target: str):
            if target.endswith("/sitemap.xml"):
                return 200, {}, sitemap([url]), target
            if target == url:
                return 200, {}, document(url), target
            raise AssertionError(target)

        code = post_deploy.run(
            self.repo.path,
            sha,
            fetch=fetch,
            ping=lambda urls: pinged.append(list(urls)),
            sleep=lambda _seconds: None,
            attempts=1,
            workers=1,
        )
        self.assertEqual(code, 0)
        self.assertEqual(pinged, [[url]])

    def test_prompts_directory_canonical_passes_against_index_html_sitemap(self) -> None:
        path = "prompts/index.html"
        public = f"{SITE}/prompts/"
        sha = self._commit_pair(
            {path: document(public, body="old library")},
            {path: document(public, body="Prompt library for coding agents.")},
        )
        pinged: list[str] = []

        def fetch(url: str):
            if url.endswith("/sitemap.xml"):
                return 200, {}, sitemap([f"{SITE}/prompts/index.html"]), url
            if url == public:
                return 200, {}, document(public, body="Prompt library for coding agents."), url
            raise AssertionError(url)

        code = post_deploy.run(
            self.repo.path,
            sha,
            fetch=fetch,
            ping=pinged.extend,
            sleep=lambda _seconds: None,
            attempts=1,
            workers=1,
        )
        self.assertEqual(code, 0, pinged)
        self.assertEqual(pinged, [public])

    def test_noindex_page_that_passes_is_not_pinged(self) -> None:
        path = "sponsor.html"
        url = f"{SITE}/{path}"
        page = document(url, robots="noindex,follow")
        sha = self._commit_pair({"README.md": "x\n"}, {path: page})
        pinged: list[str] = []

        def fetch(target: str):
            if target.endswith("/sitemap.xml"):
                return 200, {}, sitemap([]), target
            if target == url:
                return 200, {}, page, target
            raise AssertionError(target)

        code = post_deploy.run(
            self.repo.path,
            sha,
            fetch=fetch,
            ping=pinged.extend,
            sleep=lambda _seconds: None,
            attempts=1,
            workers=1,
        )
        self.assertEqual(code, 0)
        self.assertEqual(pinged, [])

    def test_empty_main_fails_and_is_not_pinged(self) -> None:
        problems, indexable = post_deploy.page_problems(
            "guides/empty.html",
            200,
            {},
            "<!doctype html><html><head><link rel=\"canonical\" href=\""
            + f"{SITE}/guides/empty.html\"></head><body><main>  </main></body></html>",
            f"{SITE}/guides/empty.html",
            {f"{SITE}/guides/empty.html": f"{SITE}/guides/empty.html"},
            None,
        )
        self.assertTrue(any("no text in <main>" in item for item in problems))
        self.assertTrue(indexable)

    def test_noindex_page_without_main_text_is_not_a_problem(self) -> None:
        html = (
            "<!doctype html><html><head><meta name=\"robots\" content=\"noindex, nofollow\">"
            + f'<link rel="canonical" href="{SITE}/sponsor.html"></head><body></body></html>'
        )
        problems, indexable = post_deploy.page_problems(
            "sponsor.html",
            200,
            {},
            html,
            f"{SITE}/sponsor.html",
            {},
            None,
        )
        self.assertEqual(problems, [])
        self.assertFalse(indexable)

    def test_report_kit_sample_without_main_is_not_a_problem(self) -> None:
        path = "tools/report-kit/sample.html"
        url = f"{SITE}/{path}"
        html = (
            "<!doctype html><html><head><meta name=\"robots\" content=\"noindex, nofollow\">"
            + f'<link rel="canonical" href="{url}"></head><body></body></html>'
        )
        problems, indexable = post_deploy.page_problems(
            path,
            200,
            {},
            html,
            url,
            {},
            None,
        )
        self.assertEqual(problems, [])
        self.assertFalse(indexable)

    def test_report_kit_sample_is_not_pinged_and_an_indexable_page_still_is(self) -> None:
        sample = "tools/report-kit/ai-visibility/sample.html"
        sample_url = f"{SITE}/{sample}"
        ok = "guides/ok.html"
        ok_url = f"{SITE}/{ok}"
        sample_html = (
            "<!doctype html><html><head><meta name=\"robots\" content=\"noindex, nofollow\">"
            + f'<link rel="canonical" href="{sample_url}"></head><body></body></html>'
        )
        sha = self._commit_pair(
            {"README.md": "x\n"},
            {sample: sample_html, ok: document(ok_url)},
        )
        pinged: list[str] = []

        def fetch(target: str):
            if target.endswith("/sitemap.xml"):
                return 200, {}, sitemap([ok_url]), target
            if target == sample_url:
                return 200, {}, sample_html, target
            if target == ok_url:
                return 200, {}, document(ok_url), target
            raise AssertionError(target)

        code = post_deploy.run(
            self.repo.path,
            sha,
            fetch=fetch,
            ping=pinged.extend,
            sleep=lambda _seconds: None,
            attempts=1,
            workers=1,
        )
        self.assertEqual(code, 0)
        self.assertEqual(pinged, [ok_url])

    def test_noindex_page_may_point_canonical_at_its_hub(self) -> None:
        problems, indexable = post_deploy.page_problems(
            "launches/page-2.html",
            200,
            {},
            "<!doctype html><html><head><meta name=\"robots\" content=\"noindex,follow\">"
            + f"<link rel=\"canonical\" href=\"{SITE}/launches/\"></head><body><main>Week list</main></body></html>",
            f"{SITE}/launches/page-2.html",
            {},
            None,
        )
        self.assertEqual(problems, [])
        self.assertFalse(indexable)

    def test_indexable_page_still_needs_self_canonical(self) -> None:
        problems, indexable = post_deploy.page_problems(
            "guides/hub.html",
            200,
            {},
            "<!doctype html><html><head>"
            + f"<link rel=\"canonical\" href=\"{SITE}/guides/\"></head><body><main>Text</main></body></html>",
            f"{SITE}/guides/hub.html",
            {f"{SITE}/guides/hub.html": f"{SITE}/guides/hub.html"},
            None,
        )
        self.assertTrue(any("canonical is" in item for item in problems))
        self.assertTrue(indexable)

    def test_retry_accepts_a_page_after_cdn_lag(self) -> None:
        path = "guides/lag.html"
        url = f"{SITE}/{path}"
        sha = self._commit_pair({"README.md": "x\n"}, {path: document(url)})
        calls = {"page": 0}
        pinged: list[str] = []

        def fetch(target: str):
            if target.endswith("/sitemap.xml"):
                return 200, {}, sitemap([url]), target
            calls["page"] += 1
            if calls["page"] == 1:
                return 404, {}, "not yet", target
            return 200, {}, document(url), target

        code = post_deploy.run(
            self.repo.path,
            sha,
            fetch=fetch,
            ping=pinged.extend,
            sleep=lambda _seconds: None,
            attempts=3,
            workers=1,
        )
        self.assertEqual(code, 0)
        self.assertGreaterEqual(calls["page"], 2)
        self.assertEqual(pinged, [url])

    def test_fragment_is_not_a_live_page(self) -> None:
        sha = self._commit_pair(
            {"free-tools-rest.html": "<li>old</li>\n"},
            {"free-tools-rest.html": "<li>new</li>\n"},
        )
        pinged: list[str] = []
        code = post_deploy.run(
            self.repo.path,
            sha,
            fetch=lambda url: (_ for _ in ()).throw(AssertionError(url)),
            ping=pinged.extend,
            sleep=lambda _seconds: None,
            attempts=1,
            workers=1,
        )
        self.assertEqual(code, 0)
        self.assertEqual(pinged, [])


class WorkflowWiringTest(unittest.TestCase):
    def test_workflows_and_template_exist(self) -> None:
        guard = (ROOT / ".github/workflows/guardrails.yml").read_text(encoding="utf-8")
        live = (ROOT / ".github/workflows/post-deploy-verify.yml").read_text(encoding="utf-8")
        template = (ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
        self.assertIn("pull_request:", guard)
        self.assertIn("branches: [main]", guard)
        self.assertIn("scripts/guardrails/pr_check.py", guard)
        self.assertIn("name: guardrails", guard)
        self.assertNotIn("pull_request_target", guard)
        self.assertIn("pages-build-deployment", live)
        self.assertIn("deployment_status:", live)
        self.assertIn("scripts/guardrails/post_deploy.py", live)
        self.assertIn("refs/heads/main", live)
        self.assertNotIn("${{ secrets", live)
        self.assertIn("Reason this page exists:", template)
        self.assertIn("Built HTML is included", template)
        self.assertIn("sitemap.xml is updated", template)
        self.assertIn("New indexable pages in this PR:", template)


if __name__ == "__main__":
    unittest.main()
