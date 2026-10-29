#!/usr/bin/env python3
"""Verify the 25 general-purpose agent packages.

Checks required files, skill frontmatter, placeholder presence, a ban on
directory leakage, and that every helper exits 0 for --help and --dry-run.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "bot-packages" / "25-agent-packs"
BANNED = ("mcp.agentscouthq.com", "buy.stripe.com", "api/tools.json", "com.agentscouthq")
NOTICE_LINES = (
    "coreyhaines31 (MIT, (c) 2025 Corey Haines)",
    "ericosiu (MIT, (c) 2026 Single Grain)",
    "aaron-he-zhu (Apache-2.0, (c) 2024 Aaron He Zhu)",
    "kostja94 (MIT, (c) 2025 kostja94)",
)
FORBIDDEN_DIRS = {"tools", "clis", "connectors", "telemetry", "hooks"}
NET = re.compile(r"\b(?:urllib|requests|http\.client|socket|subprocess)\b|\bcurl\b|\bfetch\s*\(")
REQUIRED = (
    "SYSTEM.md",
    "README-QUICKSTART.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    "LOVABLE.md",
    "LICENSE.txt",
    "THIRD_PARTY_NOTICES.md",
    "manifest.json",
    "setup_workspace.py",
    "context/business-profile.md",
    "routines/routines.json",
)


def main() -> int:
    sys.path.insert(0, str(ROOT / "scripts"))
    from agent_pack_catalog import AGENTS
    bad = []
    if len(AGENTS) != 25:
        bad.append(f"catalog has {len(AGENTS)} agents")
    for agent in AGENTS:
        dest = PACKS / agent["slug"]
        if not dest.is_dir():
            bad.append(f"missing package {agent['slug']}")
            continue
        for rel in REQUIRED:
            if not (dest / rel).is_file():
                bad.append(f"{agent['slug']} missing {rel}")
        skill = dest / "skills" / agent["skill_slug"] / "SKILL.md"
        script = dest / "scripts" / agent["script"]
        if not skill.is_file():
            bad.append(f"{agent['slug']} missing skill")
        else:
            text = skill.read_text(encoding="utf-8")
            if not text.startswith("---\n"):
                bad.append(f"{agent['slug']} skill missing frontmatter")
            if not re.search(r"^name:\s+\S+", text, re.M):
                bad.append(f"{agent['slug']} skill missing name")
            if "description:" not in text.split("---", 2)[1]:
                bad.append(f"{agent['slug']} skill missing description")
        if not script.is_file():
            bad.append(f"{agent['slug']} missing script")
        notice = (dest / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        for line in NOTICE_LINES:
            if line not in notice:
                bad.append(f"{agent['slug']} notice missing {line}")
        if "references only" not in notice.lower() or "own words" not in notice.lower():
            bad.append(f"{agent['slug']} notice does not say references were rewritten")
        readme = (dest / "README-QUICKSTART.md").read_text(encoding="utf-8")
        if "Built by AgentScout" not in readme:
            bad.append(f"{agent['slug']} README missing Built by AgentScout")
        blob_parts = []
        for path in dest.rglob("*"):
            if path.is_dir():
                if path.name in FORBIDDEN_DIRS:
                    bad.append(f"{agent['slug']} forbidden dir {path.relative_to(dest)}")
                continue
            if path.name == "partners.json":
                bad.append(f"{agent['slug']} has partners.json")
            if path.suffix == ".py":
                src = path.read_text(encoding="utf-8", errors="ignore")
                if NET.search(src):
                    bad.append(f"{agent['slug']} network call in {path.name}")
                blob_parts.append(src)
            elif path.suffix != ".zip":
                blob_parts.append(path.read_text(encoding="utf-8", errors="ignore"))
        blob = "\n".join(blob_parts)
        for token in BANNED:
            if token in blob:
                bad.append(f"{agent['slug']} contains {token}")
        if "Agent Agent" in blob:
            bad.append(f"{agent['slug']} doubles Agent Agent")
        manifest_doc = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
        if manifest_doc.get("price_usd") != 35:
            bad.append(f"{agent['slug']} manifest price_usd {manifest_doc.get('price_usd')}")
        if manifest_doc.get("script") != f"scripts/{agent['script']}":
            bad.append(f"{agent['slug']} manifest script {manifest_doc.get('script')}")
        if manifest_doc.get("skill") != f"skills/{agent['skill_slug']}/SKILL.md":
            bad.append(f"{agent['slug']} manifest skill {manifest_doc.get('skill')}")
        for rel in ("manifest.json", "SYSTEM.md", "LOVABLE.md", "README-QUICKSTART.md", "AGENTS.md"):
            text = (dest / rel).read_text(encoding="utf-8")
            if "Agent Agent" in text or "Agent** agent" in text:
                bad.append(f"{agent['slug']} {rel} doubles Agent")
        phrases = {
            "accountant": "Monthly P&L Audit",
            "google-review-replier": "Escalation Guard",
            "social-media-manager": "Velocity Guard",
            "web-designer": "Responsive UI Audit",
            "market-researcher": "Sales Battlecards",
            "content-strategist": "1-to-5 Repurposer",
        }
        if agent["slug"] in phrases:
            skill_text = (dest / "skills" / agent["skill_slug"] / "SKILL.md").read_text(encoding="utf-8")
            if phrases[agent["slug"]] not in skill_text:
                bad.append(f"{agent['slug']} SKILL.md missing {phrases[agent['slug']]}")
        if "{{YOUR_COMPANY}}" not in blob or "{{YOUR_DOMAIN}}" not in blob:
            bad.append(f"{agent['slug']} missing company placeholders")
        for flag in ("--help", "--dry-run"):
            run = subprocess.run([sys.executable, str(script), flag], cwd=dest, capture_output=True, text=True)
            if run.returncode != 0:
                bad.append(f"{agent['slug']} {script.name} {flag} exit {run.returncode}")
        setup = subprocess.run([sys.executable, str(dest / "setup_workspace.py"), "--dry-run"], cwd=dest, capture_output=True, text=True)
        if setup.returncode != 0:
            bad.append(f"{agent['slug']} setup_workspace --dry-run exit {setup.returncode}")
        routines = json.loads((dest / "routines" / "routines.json").read_text(encoding="utf-8"))
        if not routines.get("routines"):
            bad.append(f"{agent['slug']} has no routines")
    print(f"bot zip packages: {len(AGENTS)} specs, {len(bad)} problems")
    for line in bad:
        print("FAIL", line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
