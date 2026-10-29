#!/usr/bin/env python3
"""Check translation key parity and placeholder tokens for {{YOUR_COMPANY}}.

Compares a source locale with one or more targets. Flags missing keys,
empty strings, and placeholders that do not match. It can also list hreflang
codes that are missing from a provided set.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SAMPLE = {
    "source_locale": "en",
    "targets": {
        "es": {
            "hero.title": "Reserve una visita",
            "hero.cta": "Elegir hora",
            "mail.hello": "Hola {name}",
        }
    },
    "source": {
        "hero.title": "Book a visit",
        "hero.cta": "Pick a time",
        "mail.hello": "Hello {name}",
        "faq.hours": "We answer within one business day.",
    },
    "glossary": {"visit": "visita", "slot": "horario"},
    "do_not_translate": ["{{YOUR_COMPANY}}", "{{YOUR_DOMAIN}}"],
    "hreflang_present": ["en", "es"],
    "hreflang_expected": ["en", "es", "fr"],
}

TOKEN = re.compile(r"(\{\{[^}]+\}\}|\{[A-Za-z0-9_]+\}|%[sd]|%\([^)]+\)[sd])")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--self-test", action="store_true", help="Run built-in self-test sample and exit 0")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Locale bundle JSON")
    p.add_argument("--output", help="JSON report path")
    return p


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text or "")


def analyze(doc: dict) -> dict:
    source = doc["source"]
    report_targets = []
    for locale, strings in doc.get("targets", {}).items():
        missing = sorted(set(source) - set(strings))
        extra = sorted(set(strings) - set(source))
        empty = sorted(k for k, v in strings.items() if not str(v).strip())
        token_mismatch = []
        for key, value in source.items():
            if key not in strings:
                continue
            if tokens(value) != tokens(strings[key]):
                token_mismatch.append({"key": key, "source": tokens(value), "target": tokens(strings[key])})
        report_targets.append({
            "locale": locale,
            "missing_keys": missing,
            "extra_keys": extra,
            "empty_values": empty,
            "placeholder_mismatches": token_mismatch,
        })
    expected = set(doc.get("hreflang_expected") or [])
    present = set(doc.get("hreflang_present") or [])
    return {
        "company": "{{YOUR_COMPANY}}",
        "source_locale": doc.get("source_locale", "en"),
        "targets": report_targets,
        "glossary": doc.get("glossary", {}),
        "do_not_translate": doc.get("do_not_translate", []),
        "hreflang_missing": sorted(expected - present),
        "rules": [
            "Keep the glossary term even when a synonym sounds smoother.",
            "Do not translate brand, domain, or placeholder tokens.",
            "Send legal and medical lines to a person before they ship.",
            "Match hreflang codes to locales you actually serve.",
        ],
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or getattr(args, 'self_test', False) or not args.input
    doc = SAMPLE if dry else json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = analyze(doc)
    report["dry_run"] = dry
    payload = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
