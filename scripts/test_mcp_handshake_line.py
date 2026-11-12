#!/usr/bin/env python3
"""The handshake line sits beside the link-check sentence and is counted from summary.json.

The daily probe commits data/mcp-health without regenerating HTML, so published
pages are checked for the builder's wording, not pinned to whatever summary.json
says at test time. The builder itself is checked against the live summary.
"""
import json
import os
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import atexit

import build_aicite as bac

atexit._clear()

_HS = re.compile(
    r"Handshake check: (?P<probed>[\d,]+) of (?P<remote>[\d,]+) remote servers? checked(?P<so_far> so far)?\."
    r"(?P<once> The catalog of remote endpoints has been checked once\.)?"
    r"(?: Of those, (?P<responded>[\d,]+) answered with a tools list"
    r"(?: \((?P<pct>[0-9.]+)% of remote servers handshake-checked\))?"
    r", (?P<auth>[\d,]+) asked for auth, (?P<failed>[\d,]+) failed\.)?"
    r" This is the initialize \+ tools/list probe, updated daily around 7:15 AM Pacific, "
    r"separate from the link check around 7 AM PT\."
)


def _n(text):
    return int(text.replace(",", ""))


def _independent(servers):
    remote = local_only = probed = responded = needs_auth = failed = 0
    for row in servers.values():
        if not isinstance(row, dict):
            continue
        if row.get("disposition") == "local_only":
            local_only += 1
            continue
        if row.get("disposition") != "remote":
            continue
        remote += 1
        probes = row.get("probes")
        try:
            n = int(probes)
        except (TypeError, ValueError):
            n = 0
        if isinstance(probes, bool) or n < 1:
            continue
        probed += 1
        outcome = row.get("last_outcome")
        if outcome == "responded":
            responded += 1
        elif outcome == "needs_auth":
            needs_auth += 1
        else:
            failed += 1
    return {
        "remote": remote,
        "local_only": local_only,
        "probed": probed,
        "responded": responded,
        "needs_auth": needs_auth,
        "failed": failed,
        "complete": remote > 0 and probed >= remote,
    }


def _graphs(html):
    out = []
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, flags=re.S):
        data = json.loads(raw)
        if isinstance(data, dict) and isinstance(data.get("@graph"), list):
            out.extend(x for x in data["@graph"] if isinstance(x, dict))
        elif isinstance(data, dict) and data.get("@type"):
            out.append(data)
    return out


class HandshakeWordingTests(unittest.TestCase):
    def test_live_summary_counts_drive_the_sentence(self):
        data = json.loads((ROOT / "data" / "mcp-health" / "summary.json").read_text(encoding="utf-8"))
        expect = _independent(data["servers"])
        got = bac.handshake_tally(data)
        self.assertEqual(got, expect)
        self.assertGreater(expect["local_only"], 0)
        self.assertEqual(expect["responded"] + expect["needs_auth"] + expect["failed"], expect["probed"])
        text = bac.handshake_sentence(data)
        self.assertIn(f"{expect['probed']:,} of {expect['remote']:,} remote", text)
        self.assertIn(f"{expect['responded']:,} answered with a tools list", text)
        self.assertIn(f"{expect['needs_auth']:,} asked for auth", text)
        self.assertIn(f"{expect['failed']:,} failed", text)
        self.assertNotIn(f"of {expect['remote'] + expect['local_only']:,}", text)
        self.assertIn("initialize + tools/list", text)
        self.assertIn("7:15 AM Pacific", text)
        self.assertIn("around 7 AM PT", text)
        self.assertNotIn("MCP servers", text)
        if expect["complete"]:
            self.assertNotIn("so far", text)
            self.assertIn("The catalog of remote endpoints has been checked once.", text)
            self.assertIn("% of remote servers handshake-checked", text)
        else:
            self.assertIn("checked so far", text)
            self.assertNotIn("%", text)
            self.assertNotIn("checked once", text)
            self.assertNotIn("response rate", text.lower())

    def test_thin_sample_says_checked_so_far_and_drops_local_only(self):
        servers = {
            "ok": {"disposition": "remote", "probes": 1, "last_outcome": "responded"},
            "auth": {"disposition": "remote", "probes": 4, "last_outcome": "needs_auth"},
            "down": {"disposition": "remote", "probes": 1, "last_outcome": "failed"},
            "other": {"disposition": "remote", "probes": 2, "last_outcome": "timeout"},
            "waiting": {"disposition": "remote", "probes": 0, "last_outcome": "responded"},
            "bare": {"disposition": "remote"},
            "local": {"disposition": "local_only", "probes": 9, "last_outcome": "responded", "display": "local_only"},
            "unknown": {"disposition": "unclassified", "probes": 3, "last_outcome": "responded"},
        }
        tally = bac.handshake_tally(servers)
        self.assertEqual(tally["remote"], 6)
        self.assertEqual(tally["local_only"], 1)
        self.assertEqual(tally["probed"], 4)
        self.assertEqual(tally["responded"], 1)
        self.assertEqual(tally["needs_auth"], 1)
        self.assertEqual(tally["failed"], 2)
        self.assertFalse(tally["complete"])
        text = bac.handshake_sentence(servers)
        self.assertIn("4 of 6 remote servers checked so far", text)
        self.assertIn("1 answered with a tools list, 1 asked for auth, 2 failed", text)
        self.assertNotIn("%", text)
        self.assertNotIn("checked once", text)
        self.assertNotIn("of 7", text)
        self.assertNotIn("of 8", text)
        self.assertNotIn("9 answered", text)
        self.assertNotIn("response rate", text.lower())
        self.assertNotIn("MCP servers", text)

    def test_needs_auth_is_not_a_tools_list_answer(self):
        # One remote server is still unprobed, so this is not a finished pass.
        servers = {
            "wall": {"disposition": "remote", "probes": 1, "last_outcome": "needs_auth"},
            "waiting": {"disposition": "remote", "probes": 0},
            "local": {"disposition": "local_only", "probes": 5, "last_outcome": "responded"},
        }
        text = bac.handshake_sentence(servers)
        self.assertIn("1 of 2 remote servers checked so far", text)
        self.assertIn("0 answered with a tools list, 1 asked for auth, 0 failed", text)
        self.assertNotIn("%", text)
        self.assertNotIn("1 answered", text)
        self.assertNotIn("of 3", text)

    def test_full_pass_states_the_remote_share_and_drops_so_far(self):
        servers = {
            "a": {"disposition": "remote", "probes": 1, "last_outcome": "responded"},
            "b": {"disposition": "remote", "probes": 1, "last_outcome": "responded"},
            "c": {"disposition": "remote", "probes": 1, "last_outcome": "needs_auth"},
            "local": {"disposition": "local_only", "probes": 4, "last_outcome": "responded"},
        }
        text = bac.handshake_sentence(servers)
        self.assertIn("3 of 3 remote servers checked.", text)
        self.assertNotIn("so far", text)
        self.assertIn("The catalog of remote endpoints has been checked once.", text)
        self.assertIn("2 answered with a tools list (66.7% of remote servers handshake-checked)", text)
        self.assertIn("1 asked for auth, 0 failed", text)
        self.assertNotIn("MCP servers", text)
        self.assertNotIn("of all", text)
        self.assertNotIn("of 4", text)

    def test_one_remote_server_uses_the_singular(self):
        text = bac.handshake_sentence({"only": {"disposition": "remote", "probes": 1, "last_outcome": "failed"}})
        self.assertIn("1 of 1 remote server checked.", text)
        self.assertNotIn("1 of 1 remote servers checked", text)
        self.assertIn("0 answered with a tools list (0.0% of remote servers handshake-checked), 0 asked for auth, 1 failed", text)

    def test_no_remote_rows_do_not_invent_a_rate(self):
        text = bac.handshake_sentence({"local": {"disposition": "local_only", "probes": 3, "last_outcome": "responded"}})
        self.assertIn("no remote servers are in the summary yet", text)
        self.assertIn("Local-only servers are not part of this probe", text)
        self.assertNotIn("%", text)
        self.assertNotIn("so far", text)
        self.assertNotIn("checked once", text)

    def test_script_end_tag_with_space_is_not_rewritten(self):
        sentence = "Checked daily, 1 of 1 checked servers live, last checked 2026-11-12."
        hs = "Handshake check: 1 of 1 remote server checked so far."
        script = f"<script>{sentence}</script >"
        html = f"<p>{sentence}</p>{script}<style>{sentence}</style >"
        out = bac._beside_plain_reach_sentence(html, sentence, hs)
        self.assertIn(script, out)
        self.assertIn(f"<style>{sentence}</style >", out)
        self.assertIn(f"<p>{sentence} {hs}</p>", out)
        self.assertEqual(out.count(hs), 1)

    def test_missing_summary_does_not_invent_counts(self):
        self.assertIsNone(bac.handshake_tally(path=str(ROOT / "data" / "mcp-health" / "missing-summary.json")))
        self.assertEqual(bac.handshake_sentence(path=str(ROOT / "data" / "mcp-health" / "missing-summary.json")), "")

    def test_link_check_sentence_is_unchanged_in_meaning(self):
        st = bac.mcp_reachability()
        sentence = bac.reach_sentence(st)
        self.assertRegex(
            sentence,
            r"^Checked daily, [\d,]+ of [\d,]+ checked servers live, last checked \d{4}-\d{2}-\d{2}\."
            r"( \+[\d,]+ listed, not yet checked\.)?$",
        )
        self.assertNotIn("Handshake", sentence)
        self.assertNotIn("tools/list", sentence)
        self.assertNotIn("so far", sentence)
        self.assertNotIn("Handshake", bac.methodology_plain())
        block = bac._reach_block(st, "mcp/status/index.html")
        hs = bac.handshake_sentence()
        self.assertIn(hs, block)
        self.assertIn(bac.reach_sentence_html(st), block)
        answer = re.search(r'id="mcp-reachable-a">(.*?)</p>', block, re.S).group(1)
        qa = re.search(r'id="mcp-reach">(.*?)</p>', block, re.S).group(1)
        self.assertNotIn("Handshake", answer)
        self.assertNotIn("Handshake", qa)
        self.assertIn("checked servers live", re.sub(r"<[^>]+>", "", answer))
        self.assertIn(bac._Q_ANSWER, block)
        count = bac.handshake_count_html()
        self.assertIn(hs, count)
        self.assertNotIn("checked servers live", count)


class PublishedPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st = bac.mcp_reachability()
        cls.sentence = bac.reach_sentence(cls.st)

    def _assert_handshake_copy(self, text, label):
        found = list(_HS.finditer(text))
        self.assertTrue(found, label)
        for match in found:
            probed, remote = _n(match.group("probed")), _n(match.group("remote"))
            so_far = match.group("so_far")
            responded = match.group("responded")
            if responded is None:
                self.assertEqual(probed, 0, label)
                responded_n = auth_n = failed_n = 0
            else:
                responded_n, auth_n, failed_n = _n(responded), _n(match.group("auth")), _n(match.group("failed"))
                self.assertEqual(responded_n + auth_n + failed_n, probed, label)
            line = match.group(0)
            if so_far:
                self.assertIsNone(match.group("once"), label)
                self.assertIsNone(match.group("pct"), label)
                self.assertNotIn("%", line, label)
                self.assertNotIn("checked once", line, label)
            else:
                self.assertIsNotNone(match.group("once"), label)
                if responded is not None:
                    self.assertIsNotNone(match.group("pct"), label)
                    self.assertIn("% of remote servers handshake-checked", line, label)
            self.assertNotIn("MCP servers", line, label)
            tally = {
                "remote": remote,
                "local_only": 0,
                "probed": probed,
                "responded": responded_n,
                "needs_auth": auth_n,
                "failed": failed_n,
                "complete": not so_far,
            }
            self.assertEqual(line, bac.handshake_sentence(tally), label)

    def test_status_page_keeps_the_link_check_and_adds_the_handshake_line(self):
        text = (ROOT / "mcp" / "status" / "index.html").read_text(encoding="utf-8")
        self.assertIn(self.sentence, text)
        updated = re.search(r'<p class="st-updated">(.*?)</p>', text, re.S)
        self.assertIsNotNone(updated)
        self.assertIn("checked servers live", updated.group(1))
        self.assertNotIn("Handshake", updated.group(1))
        self.assertRegex(text, r'</p>\s*<p id="mcp-handshake-count">Handshake check:')
        answer = re.search(r'id="mcp-reachable-a">(.*?)</p>', text, re.S).group(1)
        self.assertNotIn("Handshake", answer)
        self.assertIn("checked servers live", re.sub(r"<[^>]+>", "", answer))
        faq = next(n for n in _graphs(text) if n.get("@type") == "FAQPage")
        by_q = {q["name"]: q["acceptedAnswer"]["text"] for q in faq["mainEntity"]}
        self.assertEqual(by_q[bac._Q_COUNT], self.sentence)
        self.assertNotIn("Handshake", by_q[bac._Q_COUNT])
        self.assertNotIn("tools/list", by_q[bac._Q_COUNT])
        self.assertEqual(by_q[bac._Q_HOW], bac.methodology_plain())
        self.assertIn("Handshake check:", by_q[bac._Q_ANSWER])
        self.assertIn("initialize + tools/list", by_q[bac._Q_ANSWER])
        self._assert_handshake_copy(text, "mcp/status/index.html")

    def test_citation_pages_quote_both_facts(self):
        pages = [
            ROOT / "mcp" / "index.html",
            ROOT / "categories" / "mcp-servers.html",
            ROOT / "llms.txt",
            ROOT / "llms-full.txt",
        ]
        for path in pages:
            text = path.read_text(encoding="utf-8")
            self.assertIn(self.sentence, text, path)
            self.assertIn("HEAD, then GET", text, path)
            self._assert_handshake_copy(text, str(path))
            if path.suffix == ".html":
                faq = next(n for n in _graphs(text) if n.get("@type") == "FAQPage")
                by_q = {q["name"]: q["acceptedAnswer"]["text"] for q in faq["mainEntity"]}
                self.assertEqual(by_q[bac._Q_COUNT], self.sentence, path)
                self.assertNotIn("Handshake", by_q[bac._Q_COUNT], path)
                answer = re.search(r'id="mcp-reachable-a">(.*?)</p>', text, re.S).group(1)
                self.assertNotIn("Handshake", answer, path)


if __name__ == "__main__":
    unittest.main()
