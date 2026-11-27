#!/usr/bin/env python3
"""Tests for scripts/lint_seo_terms.py and scripts/apply_seo_overrides.py.

Run from anywhere: python3 scripts/test_seo_terms.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import apply_seo_overrides as apply  # noqa: E402
import lint_seo_terms as lint  # noqa: E402

TODAY_STAMP = "2026-11-27T13:30:00-08:00"


def page(title: str, meta: str, lede: str, technical: str = "") -> str:
    tech = technical or lede
    return (
        "<!doctype html><html><head>"
        f"<title>{title}</title>"
        f'<meta name="description" content="{meta}">'
        f'<meta property="og:title" content="{title}">'
        f'<meta property="og:description" content="{meta}">'
        "</head><body><main>"
        f'<p class="lede">{lede}</p>'
        f"<h2>At a glance</h2><p>{tech}</p>"
        "</main></body></html>"
    )


class TermHelpers(unittest.TestCase):
    def test_protected_terms_and_urls(self) -> None:
        text = (
            "Sandscale runs Firecracker sandboxes for Claude Code, with an MCP server "
            "at mcp.sandscale.dev and a streamable HTTP option."
        )
        found = lint.protected_in(text)
        for term in ("Firecracker", "Claude Code", "MCP server", "streamable HTTP", "mcp.sandscale.dev"):
            self.assertIn(term, found, found)

    def test_claude_code_kept_still_counts_as_claude(self) -> None:
        old = "The docs tell Claude Code how to connect."
        new = "The docs tell Claude Code how to connect to the MCP server."
        self.assertEqual(lint.missing_terms(old, new), [])

    def test_dropping_claude_code_to_claude_fails(self) -> None:
        old = "Firecracker sandboxes for Claude Code"
        new = "Firecracker sandboxes for Claude"
        self.assertIn("Claude Code", lint.missing_terms(old, new))

    def test_official_url_drop_is_detected(self) -> None:
        old = "Docs are at docs.superagent.sh."
        new = "Docs are linked from the project."
        self.assertIn("docs.superagent.sh", lint.missing_terms(old, new))

    def test_github_urls_are_not_protected(self) -> None:
        old = "See the repo at github.com/ankurmans/pepys-mcp."
        new = "See the package you can run locally."
        self.assertEqual(lint.missing_terms(old, new), [])


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

    def write_json(self, rel: str, data: object) -> None:
        self.write(rel, json.dumps(data, indent=2) + "\n")

    def commit(self, message: str, when: str = TODAY_STAMP) -> str:
        self.git("add", "-A")
        self.git(
            "commit",
            "--allow-empty",
            "-m",
            message,
            env={"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when},
        )
        return self.git("rev-parse", "HEAD")

    def close(self) -> None:
        self._tmp.cleanup()


class DiffAwareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo()
        self.repo.write_json(
            "tools.json",
            [{"slug": "sandscale", "name": "Sandscale", "description": "Plain body."}],
        )
        self.repo.write(
            "tools/sandscale.html",
            page(
                "Sandscale: Firecracker sandboxes for Claude Code",
                "Sandscale runs Firecracker microVM sandboxes for Claude Code, with an MCP server at mcp.sandscale.dev.",
                "Sandscale runs Firecracker microVM sandboxes for AI agents. The MCP server asks you to sign in.",
                "The docs tell Claude Code how to connect. MCP server at mcp.sandscale.dev.",
            ),
        )
        self.base = self.repo.commit("listing with protected title and meta")

    def tearDown(self) -> None:
        self.repo.close()

    def test_unchanged_page_passes(self) -> None:
        self.repo.write("README.md", "docs only\n")
        head = self.repo.commit("docs")
        self.assertEqual(lint.failures(self.repo.path, self.base, head), [])
        self.assertEqual(lint.flags(self.repo.path, self.base, head), [])

    def test_dropping_claude_code_from_title_fails(self) -> None:
        self.repo.write(
            "tools/sandscale.html",
            page(
                "Sandscale: Firecracker sandboxes for agents",
                "Sandscale runs Firecracker microVM sandboxes, with an MCP server at mcp.sandscale.dev.",
                "Sandscale runs Firecracker microVM sandboxes for AI agents. The MCP server asks you to sign in.",
                "The docs tell Claude Code how to connect. MCP server at mcp.sandscale.dev.",
            ),
        )
        head = self.repo.commit("strip Claude Code from title and meta")
        messages = lint.failures(self.repo.path, self.base, head)
        self.assertTrue(messages, messages)
        self.assertTrue(any("Claude Code" in item and "sandscale" in item for item in messages), messages)

    def test_keeping_terms_in_new_wording_passes(self) -> None:
        self.repo.write(
            "tools/sandscale.html",
            page(
                "Sandscale: Claude Code Firecracker microVM sandboxes",
                "Firecracker sandboxes for Claude Code, plus an MCP server at mcp.sandscale.dev. Sign-in required.",
                "Sandscale runs Firecracker microVM sandboxes for AI agents. The MCP server asks you to sign in.",
                "The docs tell Claude Code how to connect. MCP server at mcp.sandscale.dev.",
            ),
        )
        head = self.repo.commit("reword title and meta, keep terms")
        self.assertEqual(lint.failures(self.repo.path, self.base, head), [])

    def test_dropping_product_name_from_title_fails(self) -> None:
        self.repo.write(
            "tools/sandscale.html",
            page(
                "Firecracker sandboxes for Claude Code",
                "Sandscale runs Firecracker microVM sandboxes for Claude Code, with an MCP server at mcp.sandscale.dev.",
                "Sandscale runs Firecracker microVM sandboxes for AI agents.",
                "The docs tell Claude Code how to connect. MCP server at mcp.sandscale.dev.",
            ),
        )
        head = self.repo.commit("drop product name from title")
        messages = lint.failures(self.repo.path, self.base, head)
        self.assertTrue(any("Sandscale" in item for item in messages), messages)

    def test_technical_section_drop_is_flagged_not_failed(self) -> None:
        self.repo.write(
            "tools/sandscale.html",
            page(
                "Sandscale: Firecracker sandboxes for Claude Code",
                "Sandscale runs Firecracker microVM sandboxes for Claude Code, with an MCP server at mcp.sandscale.dev.",
                "Sandscale runs Firecracker microVM sandboxes for AI agents. The MCP server asks you to sign in.",
                "The MCP server asks you to sign in before it will connect.",
            ),
        )
        head = self.repo.commit("strip Claude Code from technical section only")
        self.assertEqual(lint.failures(self.repo.path, self.base, head), [])
        flagged = lint.flags(self.repo.path, self.base, head)
        self.assertTrue(flagged, flagged)
        self.assertTrue(any("Claude Code" in item and "FLAG" in item for item in flagged), flagged)

    def test_unrelated_tool_page_is_ignored(self) -> None:
        self.repo.write("best/mcp-servers.html", "<title>Best MCP servers</title>")
        head = self.repo.commit("edit a hub page")
        self.assertEqual(lint.failures(self.repo.path, self.base, head), [])


class ApplyOverridesTests(unittest.TestCase):
    def test_apply_writes_title_and_meta_only(self) -> None:
        original = page(
            "Sandscale: what it does, pricing and alternatives",
            "Sandscale: Sandscale runs Firecracker microVM sandboxes…",
            "Sandscale runs Firecracker microVM sandboxes for AI agents. The MCP server asks you to sign in.",
        )
        updated = apply.apply_one(
            original,
            "Sandscale: Firecracker sandboxes for Claude Code",
            "Sandscale runs Firecracker microVM sandboxes for Claude Code, with an MCP server at mcp.sandscale.dev.",
        )
        self.assertIn("<title>Sandscale: Firecracker sandboxes for Claude Code</title>", updated)
        self.assertIn(
            'content="Sandscale runs Firecracker microVM sandboxes for Claude Code, with an MCP server at mcp.sandscale.dev."',
            updated,
        )
        self.assertIn(
            "Sandscale runs Firecracker microVM sandboxes for AI agents. The MCP server asks you to sign in.",
            updated,
        )
        # Visible lede unchanged
        self.assertIn(
            '<p class="lede">Sandscale runs Firecracker microVM sandboxes for AI agents. The MCP server asks you to sign in.</p>',
            updated,
        )


if __name__ == "__main__":
    unittest.main()
