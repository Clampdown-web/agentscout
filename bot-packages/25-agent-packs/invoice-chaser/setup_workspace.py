#!/usr/bin/env python3
"""Replace {{YOUR_*}} placeholders in a purchased agent package.

Stdlib only. --dry-run prints the files that still contain placeholders and
exits 0. Pass --apply with values to write the replacements.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

KEYS = (
    "YOUR_COMPANY",
    "YOUR_DOMAIN",
    "YOUR_SUPPORT_EMAIL",
    "YOUR_OWNER_NAME",
    "YOUR_MCP_SERVER_URL",
    "YOUR_TIMEZONE",
)

SKIP = {".git", "__pycache__"}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".", help="Package root to scan")
    p.add_argument("--dry-run", action="store_true", help="Report placeholders and exit 0")
    p.add_argument("--sample", action="store_true", help="Same as --dry-run")
    p.add_argument("--apply", action="store_true", help="Write replacements")
    p.add_argument("--company", default="")
    p.add_argument("--domain", default="")
    p.add_argument("--support-email", default="")
    p.add_argument("--owner-name", default="")
    p.add_argument("--mcp-url", default="")
    p.add_argument("--timezone", default="America/Los_Angeles")
    return p


def files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP for part in path.parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".zip", ".woff", ".woff2"}:
            continue
        yield path


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    root = Path(args.root)
    values = {
        "YOUR_COMPANY": args.company,
        "YOUR_DOMAIN": args.domain,
        "YOUR_SUPPORT_EMAIL": args.support_email,
        "YOUR_OWNER_NAME": args.owner_name,
        "YOUR_MCP_SERVER_URL": args.mcp_url,
        "YOUR_TIMEZONE": args.timezone,
    }
    hits = []
    for path in files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        found = [key for key in KEYS if "{{" + key + "}}" in text]
        if found:
            hits.append((path, found))
            if args.apply:
                for key, value in values.items():
                    if value:
                        text = text.replace("{{" + key + "}}", value)
                path.write_text(text, encoding="utf-8")
    print(f"placeholder files: {len(hits)}")
    for path, found in hits:
        print(f"- {path}: {', '.join(found)}")
    if args.apply:
        missing = [key for key, value in values.items() if not value]
        if missing:
            print("left untouched because no value was passed: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
