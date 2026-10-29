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
HOSTS = ("Grok Bot", "Claude Code", "Cursor", "Codex", "Lovable")


def _words(text: str) -> int:
    return len(text.split())


def _lead(agent: dict) -> str:
    brand = agent["product_name"]
    first = agent["promise"].strip().split(". ")[0].rstrip(".")
    clause = first.split()
    if clause:
        clause[0] = clause[0][:1].lower() + clause[0][1:]
    tail = (
        f"It ships one skill, {len(agent['routines'])} routines, and a local Python script. "
        "Setup is one command with your company name and domain. "
        "Drafts wait for approval. There is no telemetry and no network call."
    )
    prefix = f"The {brand}"
    while clause:
        text = prefix + " " + " ".join(clause).rstrip(".") + ". " + tail
        count = _words(text)
        if count <= 60 and count >= 40:
            return text
        if count < 40:
            break
        clause.pop()
    text = prefix + " " + " ".join(first.split()).rstrip(".") + ". " + tail
    count = _words(text)
    if count > 60:
        text = (
            f"The {brand} prepares this work for your company and waits for approval. "
            + tail
        )
        count = _words(text)
    if not 40 <= count <= 60:
        raise SystemExit(f"lead for {agent['slug']} is {count} words: {text}")
    return text


def _faqs(agent: dict) -> list[tuple[str, str]]:
    name = agent["product_name"]
    return [
        (
            "Is my data private?",
            "Yes. The scripts use the Python standard library only. They do not phone home, and the package has no telemetry. Your files stay on the computer where you run them.",
        ),
        (
            "How fast is setup?",
            'About 5 minutes. Run python3 setup_workspace.py --apply --company "Your Company" --domain "yourdomain.com".',
        ),
        (
            "Does it work in Cursor / Claude Code / Codex / Grok Bot / Lovable?",
            "Yes. The ZIP includes README.md, system-prompt.md (SYSTEM.md), profile.json, SKILL.md, AGENTS.md, CLAUDE.md, LOVABLE.md, and .cursorrules, so the same package loads in Grok Bot, Claude Code, Cursor, Codex, and Lovable.",
        ),
        (
            "Does it send or post anything on its own?",
            f"No. The {name} drafts and asks first. Sending, posting, spending, deleting, and filing stay with you.",
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
        f"{agent['product_name']}: {agent['tagline']}. "
        "Ready-to-run skills, routines and scripts for Grok Bot, Claude Code, Cursor and Codex."
    )
    return X.clip_text(text, 156)


def write_pack_pages() -> list[str]:
    urls = []
    for index, agent in enumerate(AGENTS):
        files, count, size = _inventory(agent)
        name = agent["product_name"]
        title = X.clip_title(f"{name} | AI Agent Pack", 60)
        desc = _desc(agent)
        canon = f"{X.B}bot-store/{agent['slug']}/"
        faqs = _faqs(agent)
        lead = _lead(agent)
        if "Agent Agent" in lead or "Agent Agent" in name or "Agent Agent" in title:
            raise SystemExit(f"doubled agent in {agent['slug']}")
        skill = f"skills/{agent['skill_slug']}/SKILL.md"
        script = f"scripts/{agent['script']}"
        file_items = "".join(f"<li><code>{X.e(item)}</code></li>" for item in files)
        faq_html = "".join(
            "<details class=\"pack-faq-item\" open>"
            f"<summary>{X.e(q)}</summary><p>{X.e(a)}</p></details>"
            for q, a in faqs
        )
        hosts = "".join(f"<li>{X.e(host)}</li>" for host in HOSTS)
        chips = "".join(f"<li>{X.e(chip)}</li>" for chip in agent.get("chips") or [])
        heuristics = "".join(f"<li>{X.e(rule)}</li>" for rule in agent["heuristics"])
        routines = "".join(
            "<li><b>" + X.e(rtitle) + "</b> <code>" + X.e(cron) + "</code><p>" + X.e(prompt) + "</p></li>"
            for _rid, cron, rtitle, prompt in agent["routines"]
        )
        related = _related(index)
        rel_html = "".join(
            f'<a class="pack-rel" href="../{other["slug"]}/" style="--ap:{X.e(other["color"])}">'
            f'<strong>{X.e(other["product_name"])}</strong>'
            f'<span>{X.e(other["tagline"])}</span>'
            f'<em>${other["price"]} one-time</em></a>'
            for other in related
        )
        kb = f"{size / 1024:.1f} KB" if size else "see the ZIP after build"
        note = f'<p class="pack-note">{X.e(agent["store_note"])}</p>' if agent.get("store_note") else ""
        color = agent["color"]
        body = f'''
<div class="crumb"><a href="../../index.html">AgentScout</a> / <a href="../">Bot Store</a> / {X.e(name)}</div>
<article class="pack-page" style="--ap:{X.e(color)}">
<section class="pack-hero">
<p class="pack-by">built by <span class="sr-only">AgentScout</span><img class="aswm" src="../../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"><span class="pack-verified">✓ Verified pack</span></p>
<div class="pack-badges"><span class="pack-price">${agent["price"]} One-Time · Instant ZIP Download</span><span class="pack-dept">{X.e(agent["dept_label"])}</span></div>
<h1 data-pagefind-weight="10"><span class="pack-brand">AgentScout</span> <span class="pack-role">{X.e(agent["role"])}</span> <span class="pack-kind">Agent</span></h1>
<p class="lede">{X.e(lead)}</p>
<p class="pack-outcome">{X.e(agent["promise"])}</p>
<p class="pack-tag">{X.e(agent["tagline"])}</p>
<ul class="pack-chips">{chips}</ul>
<div class="pack-cta">
<a class="pack-btn buy" href="{X.e(agent["checkout_url"] or "../#ap-dock")}">Buy this agent — ${agent["price"]}</a>
<a class="pack-btn x" href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer">Pay via X Money (@clampdown19)</a>
<a class="pack-btn back" href="../#ai-agent-packs">← Back to All 25 Packs</a>
</div>
<p class="pack-volume">Volume packs: <b>5-Bot Pack ($119)</b>, <b>10-Bot Pack ($199)</b>, <b>20-Bot Pack ($299)</b>, <b>All 25 Bots ($349)</b>. Flagship Pro Bots stay $39 / $59 / $59 / $69, and the <a href="../#bundle-package">$149 4-Bot Bundle</a> is separate.</p>
{note}
</section>
<section class="pack-pillars" aria-label="Pack highlights">
<article><h2>Functionality &amp; Trained Judgment</h2><p>Six written heuristics, one skill, and {len(agent["routines"])} routines decide the draft before anyone sends it.</p></article>
<article><h2>Security &amp; Privacy by Design</h2><p>100% Python standard library, zero network calls, and no telemetry. Files stay on the machine that runs them.</p></article>
<article><h2>5-Minute Turnkey Setup</h2><p>Run <code>python3 setup_workspace.py</code>, add your company name and domain, then dry-run <code>{X.e(agent["script"])}</code>.</p></article>
<article><h2>Works Across All Major AI Coding &amp; Agent Hosts</h2><p>The same ZIP loads in Grok Bot, Claude Code, Cursor, Codex, and Lovable.</p></article>
</section>
<section class="pack-block">
<h2>Trained Judgment Rules &amp; Heuristics</h2>
<ul class="pack-rules">{heuristics}</ul>
<h2>Scheduled routines</h2>
<ul class="pack-routines">{routines}</ul>
</section>
<h2>What you get</h2>
<table class="pack-spec">
<tbody>
<tr><th scope="row">Skills</th><td>1 — <code>{X.e(agent["skill_slug"])}</code></td></tr>
<tr><th scope="row">Scripts</th><td>1 — <code>{X.e(agent["script"])}</code></td></tr>
<tr><th scope="row">Routines</th><td>{len(agent["routines"])}</td></tr>
<tr><th scope="row">Hosts</th><td><ul class="pack-hosts">{hosts}</ul></td></tr>
<tr><th scope="row">Price</th><td>${agent["price"]} one-time</td></tr>
<tr><th scope="row">Setup</th><td>About 5 minutes</td></tr>
</tbody>
</table>
<details class="pack-zip">
<summary>What's Inside the ZIP ({count} files, {kb})</summary>
<p>Sample output is the JSON printed by <code>python3 {X.e(script)} --dry-run</code>. Skill file: <code>{X.e(skill)}</code>.</p>
<ul class="pack-files">
{file_items}
</ul>
</details>
<h2>FAQ</h2>
<div class="pack-faq">{faq_html}</div>
<h2>Related packs</h2>
<div class="pack-related">{rel_html}</div>
<p class="pack-more">Or take the <a href="../#bundle-package">$149 Full 4-Bot Company-in-a-Box bundle</a>.</p>
</article>
<style>
.pack-page{{--ap:{X.e(color)};max-width:920px;min-width:0}}
.pack-page *{{box-sizing:border-box}}
.pack-hero{{position:relative;overflow:hidden;margin:8px 0 18px;padding:18px 16px 16px;border-radius:20px;border:1px solid color-mix(in srgb, var(--ap) 42%, rgba(255,255,255,.12));background:linear-gradient(180deg, color-mix(in srgb, var(--ap) 14%, #181c26) 0%, #12151c 100%);box-shadow:0 16px 40px -18px rgba(0,0,0,.7), 0 0 28px -10px color-mix(in srgb, var(--ap) 45%, transparent)}}
.pack-hero::before{{content:"";position:absolute;left:0;right:0;top:0;height:3px;background:linear-gradient(90deg, transparent, var(--ap), transparent)}}
.pack-page img.aswm{{height:1.25em;width:auto;max-width:100%;filter:invert(1) hue-rotate(180deg);vertical-align:-.28em}}
.pack-by{{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0 0 10px;font-weight:700;color:#e4e4e7}}
.pack-verified{{border-radius:999px;padding:2px 8px;font-size:11px;color:#bbf7d0;background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.35)}}
.pack-badges{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}}
.pack-price,.pack-dept{{display:inline-flex;align-items:center;max-width:100%;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:800;overflow-wrap:anywhere}}
.pack-price{{color:#fff;background:color-mix(in srgb, var(--ap) 24%, #12151c);border:1px solid color-mix(in srgb, var(--ap) 55%, transparent)}}
.pack-dept{{color:#e4e4e7;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.04)}}
.pack-page h1{{margin:0 0 10px;font-size:clamp(26px, 4vw, 36px);line-height:1.15;color:#fff;letter-spacing:-.03em;overflow-wrap:anywhere}}
.pack-role{{color:var(--ap)}}
.pack-kind{{color:#d4d4d8;font-weight:650}}
.pack-page .lede{{color:#e4e4e7;font-size:15.5px;line-height:1.55}}
.pack-outcome{{margin:8px 0;color:#d4d4d8;font-size:15px;line-height:1.55;overflow-wrap:anywhere}}
.pack-tag{{margin:0 0 8px;color:var(--ap);font-weight:800;overflow-wrap:anywhere}}
.pack-chips,.pack-hosts,.pack-files{{display:flex;flex-wrap:wrap;gap:6px;list-style:none;padding:0;margin:8px 0}}
.pack-chips li,.pack-hosts li,.pack-files li{{max-width:100%;overflow-wrap:anywhere;border-radius:999px;padding:4px 8px;font-size:12px;font-weight:700;color:#e4e4e7;background:#12151c;border:1px solid rgba(255,255,255,.12)}}
.pack-cta{{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}}
.pack-btn{{display:inline-flex;align-items:center;justify-content:center;flex:1 1 200px;min-width:0;min-height:44px;padding:10px 12px;border-radius:12px;font-weight:800;text-decoration:none;text-align:center;overflow-wrap:anywhere}}
.pack-btn.buy{{background:#f4f4f5;color:#18181b}}
.pack-btn.x{{background:transparent;color:#e4e4e7;border:1px solid rgba(255,255,255,.2)}}
.pack-btn.back{{background:#172033;color:#dbeafe;border:1px solid #1d4ed8}}
.pack-note{{color:#a1a1aa;font-size:13px}}
.pack-pillars{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:0 0 18px}}
.pack-pillars article,.pack-block,.pack-faq-item,.pack-rel{{min-width:0;border-radius:16px;padding:14px;background:#161922;border:1px solid rgba(255,255,255,.1)}}
.pack-pillars h2,.pack-block h2,.pack-page>h2{{margin:0 0 8px;font-size:16px;color:#fff;line-height:1.3}}
.pack-pillars p,.pack-page p,.pack-page li{{overflow-wrap:anywhere}}
.pack-block{{margin:0 0 18px;border-color:color-mix(in srgb, var(--ap) 30%, rgba(255,255,255,.1))}}
.pack-rules,.pack-routines{{list-style:none;padding:0;margin:0 0 12px;display:flex;flex-direction:column;gap:8px}}
.pack-rules li,.pack-routines li{{background:#12151c;border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:8px 10px;color:#d4d4d8;line-height:1.45}}
.pack-rules li::before{{content:"✓ ";color:#34d399;font-weight:800}}
.pack-routines p{{margin:4px 0 0}}
.pack-spec{{width:100%;border-collapse:collapse;margin:8px 0 16px;table-layout:fixed}}
.pack-spec th,.pack-spec td{{text-align:left;padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.12);vertical-align:top;overflow-wrap:anywhere}}
.pack-spec th{{width:34%;color:#fff}}
.pack-zip{{margin:12px 0;max-width:100%;border-radius:14px;padding:10px 12px;background:#161922;border:1px solid rgba(255,255,255,.1)}}
.pack-zip summary{{cursor:pointer;font-weight:800;color:#fff}}
.pack-faq{{display:flex;flex-direction:column;gap:8px;margin-bottom:16px}}
.pack-faq-item summary{{cursor:pointer;font-weight:800;color:#fff}}
.pack-related{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-bottom:12px}}
.pack-rel{{display:flex;flex-direction:column;gap:6px;text-decoration:none;color:#e4e4e7;border-color:color-mix(in srgb, var(--ap) 40%, rgba(255,255,255,.1))}}
.pack-rel strong{{color:#fff;overflow-wrap:anywhere}}
.pack-rel em{{font-style:normal;color:var(--ap);font-weight:800}}
.pack-page code{{overflow-wrap:anywhere}}
@media(max-width:720px){{
  .pack-pillars,.pack-related{{grid-template-columns:minmax(0,1fr)}}
  .pack-btn{{flex-basis:100%}}
}}
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
                        {"@type": "ListItem", "position": 3, "name": name, "item": canon},
                    ],
                },
                {
                    "@type": "Product",
                    "name": name,
                    "description": desc,
                    "image": POSTER,
                    "sku": agent["slug"],
                    "brand": ORG,
                    "offers": {
                        "@type": "Offer",
                        "price": f"{agent['price']:.2f}",
                        "priceCurrency": "USD",
                        "availability": "https://schema.org/InStock",
                        "url": agent["checkout_url"] or canon,
                    },
                },
                {
                    "@type": "SoftwareApplication",
                    "name": name,
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
                        "url": agent["checkout_url"] or canon,
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
        page = X.shell("../../", title, desc, canon, body, graph)
        (out / "index.html").write_text(page, encoding="utf-8")
        urls.append(canon)
    return urls


if __name__ == "__main__":
    os.chdir(ROOT)
    print(len(write_pack_pages()), "pack pages")
