#!/usr/bin/env python3
"""Replace {{YOUR_*}} placeholders in a purchased agent package.

Stdlib only. --dry-run / --self-test / --check prints the files that still
contain placeholders and exits 0. Pass --apply (or pass --company / --domain)
with values to write the replacements.
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
    p.add_argument("--root", default="", help="Package root to scan")
    p.add_argument("--dry-run", action="store_true", help="Report placeholders and exit 0")
    p.add_argument("--self-test", action="store_true", help="Run self-test placeholder scan and exit 0")
    p.add_argument("--check", action="store_true", help="Same as --dry-run")
    p.add_argument("--sample", action="store_true", help="Same as --dry-run")
    p.add_argument("--apply", action="store_true", help="Write replacements")
    p.add_argument("--company", default="")
    p.add_argument("--domain", default="")
    p.add_argument("--support-email", default="")
    p.add_argument("--email", default="", help="Alias for --support-email")
    p.add_argument("--owner-name", default="")
    p.add_argument("--owner", default="", help="Alias for --owner-name")
    p.add_argument("--mcp-url", default="")
    p.add_argument("--timezone", default="America/Los_Angeles")
    return p


def resolve_root(raw_root: str) -> Path:
    if raw_root:
        return Path(raw_root).resolve()
    here = Path(__file__).resolve().parent
    if here.name == "scripts" and (here.parent / "manifest.json").exists():
        return here.parent
    cwd = Path.cwd().resolve()
    if cwd.name == "scripts" and (cwd.parent / "manifest.json").exists():
        return cwd.parent
    return cwd


def files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP for part in path.parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".zip", ".woff", ".woff2"}:
            continue
        if path.name == "setup_workspace.py":
            continue
        yield path


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    root = resolve_root(args.root)
    support_email = args.support_email or args.email
    owner_name = args.owner_name or args.owner
    has_Explicit_vals = any([args.company, args.domain, support_email, owner_name, args.mcp_url])
    do_apply = args.apply or (has_Explicit_vals and not (args.dry_run or args.self_test or args.check or args.sample))
    values = {
        "YOUR_COMPANY": args.company,
        "YOUR_DOMAIN": args.domain,
        "YOUR_SUPPORT_EMAIL": support_email,
        "YOUR_OWNER_NAME": owner_name,
        "YOUR_MCP_SERVER_URL": args.mcp_url,
        "YOUR_TIMEZONE": args.timezone if do_apply else "",
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
            if do_apply:
                for key, value in values.items():
                    if value:
                        text = text.replace("{{" + key + "}}", value)
                path.write_text(text, encoding="utf-8")
    print(f"placeholder files: {len(hits)}")
    for path, found in hits:
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        print(f"- {rel}: {', '.join(found)}")
    if do_apply:
        missing = [key for key, value in values.items() if not value]
        if missing:
            print("left untouched because no value was passed: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
