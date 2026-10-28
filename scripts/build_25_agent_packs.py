#!/usr/bin/env python3
"""Build the 25 downloadable agent packages and the catalog JSON the store reads."""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_pack_catalog import AGENTS, render_package, public_cards  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bot-packages" / "25-agent-packs"
ZIPS = OUT / "zips"
BANNED = (
    "mcp.agentscouthq.com",
    "buy.stripe.com",
    "api/tools.json",
    "com.agentscouthq",
)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ZIPS.mkdir(parents=True, exist_ok=True)
    for agent in AGENTS:
        dest = OUT / agent["slug"]
        render_package(agent, dest)
        blob = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in dest.rglob("*") if p.is_file())
        for token in BANNED:
            if token in blob:
                raise SystemExit(f"{agent['slug']} contains banned token {token}")
        zpath = ZIPS / f"{agent['slug']}.zip"
        if zpath.exists():
            zpath.unlink()
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in dest.rglob("*"):
                if path.is_file():
                    zf.write(path, Path(agent["slug"]) / path.relative_to(dest))
        print(f"built {agent['slug']}")
    catalog = {
        "title": "AI Agent Packs",
        "count": len(AGENTS),
        "agents": public_cards(),
    }
    (ROOT / "data" / "agent-packs-25.json").write_text(
        json.dumps(catalog, indent=2) + "\n", encoding="utf-8"
    )
    print(f"packages: {len(AGENTS)} at {OUT}")


if __name__ == "__main__":
    build()
