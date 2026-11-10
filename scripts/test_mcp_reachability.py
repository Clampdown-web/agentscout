#!/usr/bin/env python3
"""Reachability copy and JSON-LD come from the check file, not from hardcoded counts."""
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
import build_status as bst

atexit._clear()  # importing the builders registers site-wide exit hooks; tests must not run them


def _visible(html):
    html = re.sub(r"(?is)<script\b.*?</script\b[^>]*>", " ", html)
    html = re.sub(r"(?is)<style\b.*?</style\b[^>]*>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html))


def _graphs(html):
    out = []
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, flags=re.S):
        data = json.loads(raw)
        if isinstance(data, dict) and isinstance(data.get("@graph"), list):
            out.extend(x for x in data["@graph"] if isinstance(x, dict))
        elif isinstance(data, dict) and data.get("@type"):
            out.append(data)
    return out


class ReachabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools = json.load(open("tools.json"))
        cls.st = bac.mcp_reachability(cls.tools)
        cls.sentence = bac.reach_sentence(cls.st)
        raw = json.load(open("data/mcp_link_status.json"))
        cls.checked = raw["checked"]

    def test_counts_match_the_check_file_and_are_not_invented(self):
        listed = [x for x in self.tools if x.get("category") == "MCP servers"]
        doc = bst.build_document(self.tools)
        self.assertEqual(self.st["total"], len(listed))
        self.assertEqual(self.st["reachable"], doc["catalog"]["live"])
        self.assertEqual(self.st["down"], doc["catalog"]["down"])
        self.assertEqual(self.st["not_yet_checked"], doc["catalog"]["not_yet_checked"])
        self.assertEqual(self.st["day"], self.checked[:10])
        self.assertEqual(self.st["reachable"] + self.st["down"] + self.st["not_yet_checked"], self.st["total"])
        self.assertEqual(self.st["checked_count"], self.st["reachable"] + self.st["down"])
        self.assertLessEqual(self.st["reachable"], self.st["checked_count"])
        self.assertIn(f"{self.st['reachable']} of {self.st['checked_count']} checked servers live", self.sentence)
        self.assertNotIn(f"of {self.st['total']} reachable", self.sentence)
        if self.st["not_yet_checked"]:
            self.assertIn(f"+{self.st['not_yet_checked']} listed, not yet checked", self.sentence)
        self.assertIn(f"last checked {self.st['day']}", self.sentence)
        home = Path("index.html").read_text(encoding="utf-8")
        card = re.search(r'<b>(\d+) of (\d+)</b> checked servers live', home)
        self.assertIsNotNone(card, "homepage card is missing the checked-server denominator")
        self.assertEqual(int(card.group(1)), self.st["reachable"])
        self.assertEqual(int(card.group(2)), self.st["checked_count"])
        self.assertNotIn(str(self.st["reachable"]), Path("build_aicite.py").read_text().split("def reach_sentence")[1].split("def ")[0])

    def test_daily_check_includes_catalog_only_servers(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_mcp_links", ROOT / "scripts" / "check_mcp_links.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        targets = mod.mcp_targets(self.tools)
        only = [row for row in self.tools if row.get("catalog_only") and row.get("category") == "MCP servers"]
        self.assertTrue(only)
        slugs = {row["slug"] for row in targets}
        self.assertTrue(all(row["slug"] in slugs for row in only))

    def test_missing_check_file_does_not_invent_today(self):
        missing = bac.mcp_reachability([])
        self.assertEqual(missing["total"], 0)
        self.assertIn("no timestamp", bac.reach_sentence({"reachable": 0, "total": 0, "checked_count": 0, "day": ""}))

    def test_mcp_pages_lead_with_the_check_and_valid_schema(self):
        pages = list(Path("mcp").glob("*.html")) + [Path("mcp/status/index.html"), Path("categories/mcp-servers.html")]
        seen = 0
        for path in pages:
            text = path.read_text(encoding="utf-8")
            if 'http-equiv="refresh"' in text[:4000]:
                continue
            seen += 1
            block = re.search(r"<!--mcp:reach-->(.*)<!--/mcp:reach-->", text, flags=re.S)
            self.assertIsNotNone(block, path)
            visible = _visible(block.group(1))
            self.assertIn(self.sentence, visible, path)
            self.assertIn(bac._Q_HOW, visible, path)
            self.assertIn("HEAD, then GET", visible, path)
            lede_at = text.find('class="lede"')
            reach_at = text.find('id="mcp-reach"')
            if path.name == "connect.html":
                self.assertLess(lede_at, reach_at, path)
            elif lede_at != -1:
                self.assertLess(reach_at, lede_at, path)
            nodes = _graphs(text)
            types = [n.get("@type") for n in nodes]
            self.assertIn("Dataset", types, path)
            ds = next(n for n in nodes if n.get("@id", "").endswith("#reachability") or n.get("name") == "AgentScout MCP server reachability")
            self.assertEqual(ds.get("dateModified"), self.st["day"], path)
            self.assertIn(self.sentence, ds.get("description", ""), path)
            self.assertEqual(ds["distribution"]["contentUrl"], "https://agentscouthq.com/status.json")
            self.assertTrue(any(n.get("@type") == "WebSite" or (isinstance(n.get("isPartOf"), dict) and n["isPartOf"].get("potentialAction", {}).get("@type") == "SearchAction") for n in nodes), path)
            faq = next((n for n in nodes if n.get("@type") == "FAQPage"), None)
            self.assertIsNotNone(faq, path)
            by_q = {q["name"]: q["acceptedAnswer"]["text"] for q in faq["mainEntity"]}
            self.assertEqual(by_q[bac._Q_COUNT], self.sentence, path)
            self.assertEqual(by_q[bac._Q_HOW], bac.methodology_plain(), path)
            self.assertIn(by_q[bac._Q_HOW], visible, path)
            for n in nodes:
                if n.get("@type") != "ItemList":
                    continue
                items = n.get("itemListElement") or []
                self.assertEqual(n.get("numberOfItems"), len(items), path)
                positions = [i.get("position") for i in items]
                self.assertEqual(positions, list(range(1, len(items) + 1)), path)
        self.assertGreaterEqual(seen, 10)

    def test_llms_files_quote_the_same_sentence(self):
        for name in ("llms.txt", "llms-full.txt"):
            text = Path(name).read_text(encoding="utf-8")
            self.assertIn("## MCP server reachability", text, name)
            self.assertIn(self.sentence, text, name)
            self.assertIn("HEAD, then GET", text, name)
            self.assertNotIn("responded today", text, name)
        self.assertNotIn("responded today", Path("categories/mcp-servers.html").read_text(encoding="utf-8")[:8000])


if __name__ == "__main__":
    unittest.main()
