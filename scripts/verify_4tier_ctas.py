#!/usr/bin/env python3
"""Confirm the five flagship bot cards, Stripe links, neon colors, and wordmark stay intact."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINKS = (
    "https://buy.stripe.com/cNidRa0uDdNRgNvaDFe7m03",
    "https://buy.stripe.com/14A7sMfpx6lp9l3aDFe7m05",
    "https://buy.stripe.com/4gM8wQelt11568RaDFe7m06",
    "https://buy.stripe.com/9B69AU2CLh031SB8vxe7m07",
    "https://buy.stripe.com/fZueVe5OX7pt1SB6npe7m08",
)
PRICES = ("$39", "$59", "$69", "$149")
PAGES = ("bot-store/index.html", "bot-templates/index.html")


def main() -> int:
    bad = []
    for rel in PAGES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for link in LINKS:
            if text.count(link) < 1:
                bad.append(f"{rel} missing {link}")
        for price in PRICES:
            if price not in text:
                bad.append(f"{rel} missing {price}")
        if "clampdown19" not in text:
            bad.append(f"{rel} missing X Money @clampdown19")
        if "logo-wordmark.svg" not in text or "built by" not in text.lower() and "Built by" not in text and "built by" not in text:
            # The visible phrase is "built by" plus the wordmark image.
            if "built by" not in text:
                bad.append(f"{rel} missing built-by wordmark copy")
        if 'id="ai-agent-packs"' not in text:
            bad.append(f"{rel} missing AI Agent Packs section")
        if text.count('data-pack="') < 25:
            bad.append(f"{rel} has fewer than 25 agent cards")
    store = (ROOT / "bot-store/index.html").read_text(encoding="utf-8")
    for klass in ("neon-lime", "neon-gold", "neon-orange", "neon-red"):
        if klass not in store:
            bad.append(f"bot-store missing {klass}")
    if "#10b981" not in store:
        bad.append("bot-store missing mint bundle color")
    print(f"4-tier CTAs: {len(bad)} problems")
    for line in bad:
        print("FAIL", line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
