#!/usr/bin/env python3
"""Tests for scripts/lint_listing_copy.py (diff-aware listing-copy lint).

Run from anywhere: python3 scripts/test_listing_copy.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
GUARDRAILS = SCRIPTS / "guardrails"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(GUARDRAILS))

import lint_listing_copy as lint  # noqa: E402
import pr_check  # noqa: E402

TODAY_STAMP = "2026-11-27T12:00:00-08:00"
CLEAN_DESC = (
    "Kurodyne is a marketplace of skills, prompts, automation workflows, software "
    "tools, spreadsheets and templates that AI agents can search. Its Catalog MCP "
    "server is free to use with no account, so agents can search products, read "
    "reviews and pull each product's README. Sellers use a separate Seller Console "
    "MCP to have their own agent publish products and answer buyers. Prices run "
    "from $5 to $500, with a 20% fee per sale and no listing or monthly fees. A "
    "person reviews every listing, and packages are malware-scanned and fingerprinted."
)
CLEAN_DETAIL = (
    "Free to browse and to search through the Catalog MCP. Products are priced by "
    "sellers from $5 to $500 in whole US dollars. Sellers pay no listing or monthly "
    "fee and a 20% platform fee per sale, plus Stripe processing; the first sellers "
    "to publish pay no platform fee for 3 months, according to its selling page, "
    "checked 27 Nov 2026."
)
LOG_DESC = (
    "Its Catalog MCP at https://mcp.kurodyne.com/mcp needs no account; a POST "
    "initialize on 27 Nov 2026 returned com.kurodyne/catalog v1.0.0 with read-only "
    "tools such as search_products and get_product."
)
TEMPLATE_OSS = (
    "Openclaude is an open-source agent project that helps builders handle runs anywhere."
)
TEMPLATE_MCP = (
    "Netdata is an MCP server that gives agents a way to handle infrastructure monitoring."
)


class ScanTests(unittest.TestCase):
    def test_clean_kurodyne_rewrite_passes(self) -> None:
        self.assertEqual(lint.scan_text(CLEAN_DESC), [])
        self.assertEqual(lint.scan_text(CLEAN_DETAIL), [])

    def test_log_line_and_url_fail(self) -> None:
        types = lint.unique_types(lint.scan_text(LOG_DESC))
        for expected in (
            "raw_url",
            "http_method",
            "version_string",
            "snake_case_identifier",
            "log_line",
            "initialize",
            "returned_log",
        ):
            self.assertIn(expected, types, types)

    def test_stock_templates_fail(self) -> None:
        self.assertIn("ai_template", lint.unique_types(lint.scan_text(TEMPLATE_OSS)))
        self.assertIn("ai_template", lint.unique_types(lint.scan_text(TEMPLATE_MCP)))

    def test_http_status_returned_fails(self) -> None:
        types = lint.unique_types(lint.scan_text("A GET to the server returned HTTP 200."))
        self.assertIn("http_method", types)
        self.assertIn("returned_log", types)

    def test_json_ish_fails(self) -> None:
        types = lint.unique_types(lint.scan_text('The payload was {"name": "hookr"} and tools/list ran.'))
        self.assertIn("json_ish", types)

    def test_architecture_snake_case_is_allowed(self) -> None:
        self.assertEqual(lint.scan_text("The package ships a Linux x86_64 binary."), [])

    def test_get_started_is_not_an_http_method(self) -> None:
        self.assertEqual(lint.scan_text("Get started in a few minutes."), [])

    def test_dates_and_long_sentences_are_not_hard_fails(self) -> None:
        text = (
            "On 27 Nov 2026 the maker's site described a free plan. "
            "That is an as-of date, not a handshake log."
        )
        self.assertEqual(lint.scan_text(text), [])


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


def _tool(slug: str, description: str, pricing_detail: str = "") -> dict:
    return {
        "id": 1,
        "slug": slug,
        "name": slug.replace("-", " ").title(),
        "description": description,
        "pricing_detail": pricing_detail,
        "category": "MCP servers",
        "pricing": "Free",
    }


class DiffAwareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo()
        self.repo.write_json(
            "tools.json",
            [_tool("legacy-log", LOG_DESC, "See kurodyne.com/sell, 27 Nov 2026.")],
        )
        self.repo.write_json(
            "tool_rich.json",
            {
                "legacy-log": {
                    "kind": "lite",
                    "long": [LOG_DESC],
                    "features": ["Catalog MCP at https://mcp.example.com/mcp"],
                    "faq": [["Does it need an account?", "On 27 Nov 2026 it answered initialize as com.x/y v1.0.0."]],
                }
            },
        )
        self.base = self.repo.commit("main catalog with backlog")

    def tearDown(self) -> None:
        self.repo.close()

    def test_unchanged_backlog_does_not_fail(self) -> None:
        self.repo.write("README.md", "no listing change\n")
        head = self.repo.commit("docs only")
        self.assertEqual(lint.failures(self.repo.path, self.base, head), [])

    def test_logo_only_edit_does_not_lint_old_description(self) -> None:
        tools = [_tool("legacy-log", LOG_DESC, "See kurodyne.com/sell, 27 Nov 2026.")]
        tools[0]["logo"] = "assets/logos/legacy-log.png"
        self.repo.write_json("tools.json", tools)
        head = self.repo.commit("logo only")
        self.assertEqual(lint.failures(self.repo.path, self.base, head), [])

    def test_new_listing_with_log_copy_fails(self) -> None:
        tools = json.loads((self.repo.path / "tools.json").read_text(encoding="utf-8"))
        tools.append(_tool("new-log", LOG_DESC))
        self.repo.write_json("tools.json", tools)
        head = self.repo.commit("add messy listing")
        messages = lint.failures(self.repo.path, self.base, head)
        self.assertTrue(messages, messages)
        self.assertTrue(any("new-log" in item and "description" in item for item in messages), messages)
        self.assertFalse(any("legacy-log" in item for item in messages), messages)

    def test_new_listing_with_template_fails(self) -> None:
        tools = json.loads((self.repo.path / "tools.json").read_text(encoding="utf-8"))
        tools.append(_tool("openclaude", TEMPLATE_OSS))
        self.repo.write_json("tools.json", tools)
        head = self.repo.commit("add template listing")
        messages = lint.failures(self.repo.path, self.base, head)
        self.assertTrue(any("openclaude" in item and "template" in item for item in messages), messages)

    def test_clean_new_listing_passes(self) -> None:
        tools = json.loads((self.repo.path / "tools.json").read_text(encoding="utf-8"))
        tools.append(_tool("kurodyne", CLEAN_DESC, CLEAN_DETAIL))
        self.repo.write_json("tools.json", tools)
        self.repo.write_json(
            "tool_rich.json",
            {
                **json.loads((self.repo.path / "tool_rich.json").read_text(encoding="utf-8")),
                "kurodyne": {
                    "kind": "lite",
                    "long": [
                        "Kurodyne is a marketplace for digital products that agents can search.",
                        "The Catalog MCP server is free to use with no account.",
                    ],
                    "features": ["Catalog MCP that needs no account, so agents can search for free"],
                    "faq": [["Does Kurodyne's MCP need an account?", "No. The Catalog MCP needs no sign-in and is free to use."]],
                    "mcp": {
                        "endpoint": "https://mcp.kurodyne.com/mcp",
                        "transport": "Streamable HTTP",
                        "auth": "none",
                    },
                },
            },
        )
        head = self.repo.commit("add clean Kurodyne rewrite")
        self.assertEqual(lint.failures(self.repo.path, self.base, head), [])

    def test_changed_pricing_detail_url_fails(self) -> None:
        tools = [_tool("legacy-log", LOG_DESC, "See the selling page (example.com/sell).")]
        self.repo.write_json("tools.json", tools)
        head = self.repo.commit("edit pricing_detail")
        messages = lint.failures(self.repo.path, self.base, head)
        self.assertTrue(any("pricing_detail" in item and "legacy-log" in item for item in messages), messages)

    def test_changed_faq_answer_fails(self) -> None:
        rich = json.loads((self.repo.path / "tool_rich.json").read_text(encoding="utf-8"))
        rich["legacy-log"]["faq"] = [[
            "Does it need an account?",
            "A POST initialize returned com.x/catalog v1.0.0.",
        ]]
        self.repo.write_json("tool_rich.json", rich)
        head = self.repo.commit("edit faq")
        messages = lint.failures(self.repo.path, self.base, head)
        self.assertTrue(any("faq" in item and "legacy-log" in item for item in messages), messages)

    def test_mcp_technical_section_is_not_scanned(self) -> None:
        tools = json.loads((self.repo.path / "tools.json").read_text(encoding="utf-8"))
        tools.append(_tool("probed", "A hosted catalog server that agents can search without an account."))
        self.repo.write_json("tools.json", tools)
        rich = json.loads((self.repo.path / "tool_rich.json").read_text(encoding="utf-8"))
        rich["probed"] = {
            "kind": "lite",
            "long": ["A hosted catalog server that agents can search without an account."],
            "mcp": {
                "endpoint": "https://mcp.example.com/mcp",
                "transport": "Streamable HTTP",
                "tools": [["get_product", "Read one product"]],
            },
        }
        self.repo.write_json("tool_rich.json", rich)
        head = self.repo.commit("probe details in mcp field only")
        self.assertEqual(lint.failures(self.repo.path, self.base, head), [])

    def test_quality_extras_override_is_scanned(self) -> None:
        self.repo.write_json(
            "data/quality_tool_extras.json",
            {"legacy-log": {"features": ["Talk to it over https://mcp.example.com/mcp"]}},
        )
        head = self.repo.commit("override features")
        messages = lint.failures(self.repo.path, self.base, head)
        self.assertTrue(any("features" in item for item in messages), messages)

    def test_pr_check_evaluate_includes_copy_failures(self) -> None:
        tools = json.loads((self.repo.path / "tools.json").read_text(encoding="utf-8"))
        tools.append(_tool("hookr-mcp", "A bare GET to https://hookr.fun/api/mcp returned HTTP 405."))
        self.repo.write_json("tools.json", tools)
        head = self.repo.commit("add hookr")
        messages = pr_check.evaluate(
            self.repo.path,
            self.base,
            head,
            "Reason this page exists: not adding a public page\n",
            self.base,
            date(2026, 11, 27),
        )
        self.assertTrue(any("hookr-mcp" in item and "bot-like" in item for item in messages), messages)


if __name__ == "__main__":
    unittest.main()
