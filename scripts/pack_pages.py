#!/usr/bin/env python3
"""Crawlable /bot-store/<slug>/ pages for the 25 AgentScout role agents."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_extras as X
from agent_pack_catalog import AGENTS, PACK_TIERS

ORG = {"@type": "Organization", "name": "AgentScout", "url": "https://agentscouthq.com"}
POSTER = "https://agentscouthq.com/assets/animations/agentscout-trained-bots-ad-poster.png"


def _words(text: str) -> int:
    return len(text.split())


def _lead(agent: dict) -> str:
    text = (
        f"The {agent['brand_title']} drafts {agent['tagline'].lower()} for your company. "
        f"A domain skill, 3 cron routines, and one Python script prepare the work and wait for approval. "
        f"Setup is one command with your company name and domain. There is no telemetry and no network call."
    )
    count = _words(text)
    if not 40 <= count <= 62:
        raise SystemExit(f"lead for {agent['slug']} is {count} words")
    return text


def _faqs(agent: dict) -> list[tuple[str, str]]:
    return [
        (
            "Is my data private?",
            "Yes. The scripts use the Python standard library only. They do not phone home, and the package has no telemetry. Your files stay on the computer where you run them.",
        ),
        (
            "How fast is setup?",
            "About 5 minutes. Run python3 scripts/setup_workspace.py, enter your company name, domain, support email, and owner name, then run the helper with --self-test or --dry-run.",
        ),
        (
            "Does it work in Cursor / Claude Code / Codex / Grok Bot / Lovable?",
            "Yes. The ZIP includes README.md, system-prompt.md (SYSTEM.md), profile.json, SKILL.md, AGENTS.md, CLAUDE.md, LOVABLE.md, and .cursorrules, so the same package loads in Grok Bot, Claude Code, Cursor, Codex, and Lovable.",
        ),
        (
            "Does it send or post anything on its own?",
            f"No. The {agent['brand_title']} drafts and asks first. Sending, posting, spending, deleting, and filing stay with you.",
        ),
        (
            "What's the license and refund policy?",
            "The ZIP includes a single-organization LICENSE.txt for internal use by the buying company. Refund questions go to support@agentscouthq.com.",
        ),
    ]


def _inventory(agent: dict) -> tuple[list[str], int, int]:
    dest = ROOT / "bot-packages" / "25-agent-packs" / agent["slug"]
    files = []
    if dest.is_dir():
        for path in sorted(dest.rglob("*")):
            if path.is_file():
                files.append(str(path.relative_to(dest)))
    zpath = ROOT / "bot-packages" / "25-agent-packs" / "zips" / f"{agent['slug']}.zip"
    size = zpath.stat().st_size if zpath.is_file() else 0
    return files, len(files), size


def _related(index: int) -> list[dict]:
    picks = []
    for step in (1, 2, 3):
        picks.append(AGENTS[(index + step) % len(AGENTS)])
    return picks


def _desc(agent: dict) -> str:
    text = (
        f"{agent['brand_title']}: {agent['tagline_rich']}. "
        "Ready-to-run SKILL.md, 3 cron routines & Python CLI for Grok Bot, Claude Code, Cursor & Lovable."
    )
    return X.clip_text(text, 156)


def write_pack_pages() -> list[str]:
    urls = []
    for index, agent in enumerate(AGENTS):
        files, count, size = _inventory(agent)
        brand_title = agent["brand_title"]
        title = X.clip_title(f"{brand_title} | AI Agent Pack ($35)", 60)
        desc = _desc(agent)
        canon = f"{X.B}bot-store/{agent['slug']}/"
        faqs = _faqs(agent)
        lead = _lead(agent)
        skill = f"skills/{agent['skill_slug']}/SKILL.md"
        script = f"scripts/{agent['script']}"
        file_items = "".join(f"<li><code>{X.e(name)}</code></li>" for name in files)
        routine_items = "".join(
            f"<li><code>{X.e(r[1])}</code> — <strong>{X.e(r[2])}</strong> (<code>routines/{X.e(r[0])}.md</code>): {X.e(r[3])}</li>"
            for r in agent["routines"]
        )
        heuristic_items = "".join(
            f"<li>{X.e(h)}</li>" for h in agent["heuristics"]
        )
        tier_items = "".join(
            f'<li><a href="{X.e(t["url"])}"><strong>{X.e(t["label"])}</strong></a> (${t["per_bot"]:.2f}/bot)</li>'
            for t in PACK_TIERS
        )
        faq_html = "".join(
            f"<details open><summary>{X.e(q)}</summary><p>{X.e(a)}</p></details>"
            for q, a in faqs
        )
        related = _related(index)
        rel_html = "".join(
            f'<li><a href="../{other["slug"]}/">{X.e(other["brand_title"])}</a> — {X.e(other["tagline_rich"])}</li>'
            for other in related
        )
        kb = f"{size / 1024:.1f} KB" if size else "see the ZIP after build"
        body = f'''
<div class="crumb"><a href="../../index.html">AgentScout</a> / <a href="../">Bot Store</a> / {X.e(agent["title"])}</div>
<article class="pack-page">
<p class="pack-by">built by <span class="sr-only">AgentScout</span><img class="aswm" src="../../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"></p>
<h1>{X.e(brand_title)}</h1>
<p class="lede">{X.e(lead)}</p>
<p>{X.e(agent["description"])}</p>
<p><a href="../">Back to the AgentScout Bot Store</a></p>
<table class="pack-spec">
<tbody>
<tr><th scope="row">Department</th><td>{X.e(agent["dept_label"])}</td></tr>
<tr><th scope="row">Skills</th><td>1 — <code>{X.e(skill)}</code> (<code>{X.e(agent["skill_slug"])}</code>)</td></tr>
<tr><th scope="row">Scripts</th><td>1 — <code>{X.e(script)}</code> + <code>scripts/setup_workspace.py</code></td></tr>
<tr><th scope="row">Routines</th><td>{len(agent["routines"])} scheduled cron routines (JSON + Markdown)</td></tr>
<tr><th scope="row">Hosts</th><td>Grok Bot, Claude Code, Cursor, Codex, Windsurf, Cline, GitHub Copilot, Lovable</td></tr>
<tr><th scope="row">Price</th><td>${agent["price"]} one-time (or 5 for $119 · 10 for $199 · 20 for $299 · All 25 for $349)</td></tr>
<tr><th scope="row">Setup</th><td>About 5 minutes · Zero telemetry · 100% offline stdlib Python</td></tr>
</tbody>
</table>
<p>{X.e(agent["promise"])} Pay ${agent["price"]} by <a href="{X.e(agent["checkout_url"])}">Stripe Checkout</a> or X Money to <a href="https://x.com/clampdown19">@clampdown19</a>.</p>
<h2>3 Scheduled Cron Routines Included</h2>
<ul>{routine_items}</ul>
<h2>6 Trained Domain Heuristics &amp; Safety Guardrails</h2>
<ul>{heuristic_items}</ul>
<h2>Volume-Discount AI Agent Pack Tiers</h2>
<ul>{tier_items}</ul>
<details class="pack-zip" open>
<summary>What's Inside the ZIP ({count} files, {kb})</summary>
<p>Sample output is the JSON printed by <code>python3 {X.e(script)} --self-test</code> (or <code>--dry-run</code>). Skill file: <code>{X.e(skill)}</code>.</p>
<ul>
{file_items}
</ul>
</details>
<h2>FAQ</h2>
{faq_html}
<h2>Related packs</h2>
<ul>{rel_html}</ul>
<p>Or take the <a href="https://buy.stripe.com/28E9AUdhpfVZ0OxbHJe7m0d">$349 All 25 AI Agent Packs Mega Pack (Save $526)</a> or the <a href="../#bundle-package">$149 Full 4-Bot Company-in-a-Box Flagship Bundle</a>.</p>
</article>
<style>
.pack-page{{max-width:760px}}
.pack-page img.aswm{{height:1.3em;width:auto;filter:invert(1) hue-rotate(180deg);vertical-align:-.28em}}
.pack-by{{margin:12px 0 0;font-weight:700}}
.pack-spec{{width:100%;border-collapse:collapse;margin:16px 0}}
.pack-spec th,.pack-spec td{{text-align:left;padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.12);vertical-align:top}}
.pack-zip,details{{margin:12px 0;max-width:100%}}
.pack-page li,.pack-page p{{overflow-wrap:anywhere}}
.pack-page code{{overflow-wrap:anywhere}}
</style>
'''
        graph = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "WebPage",
                    "name": title,
                    "description": desc,
                    "url": canon,
                    "isPartOf": {"@type": "WebSite", "name": "AgentScout", "url": X.B},
                },
                {
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {"@type": "ListItem", "position": 1, "name": "AgentScout", "item": X.B},
                        {"@type": "ListItem", "position": 2, "name": "Bot Store", "item": X.B + "bot-store/"},
                        {"@type": "ListItem", "position": 3, "name": agent["title"], "item": canon},
                    ],
                },
                {
                    "@type": "Product",
                    "name": brand_title,
                    "description": desc,
                    "image": POSTER,
                    "sku": agent["slug"],
                    "brand": ORG,
                    "offers": {
                        "@type": "Offer",
                        "price": f"{agent['price']:.2f}",
                        "priceCurrency": "USD",
                        "availability": "https://schema.org/InStock",
                        "url": agent["checkout_url"],
                    },
                },
                {
                    "@type": "SoftwareApplication",
                    "name": brand_title,
                    "applicationCategory": "BusinessApplication",
                    "operatingSystem": "Grok Bot, Claude Code, Cursor, Codex, Lovable",
                    "softwareVersion": "1.0.0",
                    "fileSize": f"{size} B" if size else None,
                    "featureList": [agent["skill_slug"], agent["script"], "3 Scheduled Cron Routines"],
                    "author": ORG,
                    "brand": ORG,
                    "offers": {
                        "@type": "Offer",
                        "price": f"{agent['price']:.2f}",
                        "priceCurrency": "USD",
                        "availability": "https://schema.org/InStock",
                        "url": agent["checkout_url"],
                    },
                },
                {
                    "@type": "FAQPage",
                    "mainEntity": [
                        {
                            "@type": "Question",
                            "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a},
                        }
                        for q, a in faqs
                    ],
                },
            ],
        }
        app = graph["@graph"][3]
        if not app["fileSize"]:
            del app["fileSize"]
        out = ROOT / "bot-store" / agent["slug"]
        out.mkdir(parents=True, exist_ok=True)
        html = X.shell("../../", title, desc, canon, body, graph)
        (out / "index.html").write_text(html, encoding="utf-8")
        urls.append(canon)
    return urls


if __name__ == "__main__":
    os.chdir(ROOT)
    print(len(write_pack_pages()), "pack pages")
