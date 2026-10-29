#!/usr/bin/env python3
"""Keep the 25 AI Agent Packs section on tools/lovable.html.

build_site.py regenerates every tools/<slug>.html from the detail template.
This pass runs after that rewrite (and after later enrichment passes) and
inserts the packs section once. A second run replaces the same marked block,
so the section is never duplicated.

Nav, footer, neon pills, and JSON-LD already on the page are left in place.
Stripe Payment Links for the $35 / $119 / $199 / $299 / $349 packs are the
same Payment Links as the Bot Store.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Same Payment Links as scripts/agent_pack_catalog.py PACK_TIER_URLS.
STRIPE = {
    35: "https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
    119: "https://buy.stripe.com/9B600kfpx4dhbtb8vxe7m0a",
    199: "https://buy.stripe.com/6oU8wQ4KT4dh0OxeTVe7m0b",
    299: "https://buy.stripe.com/5kQ28s1yH5hl8gZ8vxe7m0c",
    349: "https://buy.stripe.com/28E9AUdhpfVZ0OxbHJe7m0d",
}

MARK_START = "<!--lovable-agent-packs-->"
MARK_END = "<!--/lovable-agent-packs-->"
SECTION_ID = "lovable-agent-packs"

def _pay(price: int, label: str) -> str:
    return (
        f'<a href="{STRIPE[price]}" target="_blank" rel="noopener noreferrer">{label}</a>'
    )

SECTION_INNER = f'''<section id="{SECTION_ID}">
<h2 style="font-size:16px;margin:28px 0 10px">25 AI Agent Packs</h2>
<p>Every one of the <a href="../bot-store/#ai-agent-packs">25 AI Agent Packs ($35–$349) on the AgentScout Bot Store</a> includes a ready-to-import <code>LOVABLE.md</code> project knowledge file and skill ZIP compatible with Lovable alongside Grok Bot, Claude Code, Cursor, and Codex.</p>
<h2 style="font-size:16px;margin:28px 0 10px">Pre-Trained Lovable AI Agent Packs &amp; MCP Registry</h2>
<p>All <a href="../bot-store/#ai-agent-packs">25 Pre-Trained AI Agent Packs</a> ({_pay(35, "$35")} single, {_pay(119, "$119")} for 5, {_pay(199, "$199")} for 10, {_pay(299, "$299")} for 20, or {_pay(349, "$349")} for all 25) and our <a href="../bot-store/">4 Flagship Pro Bots ($39–$149)</a> include a ready-to-paste <code>LOVABLE.md</code> Custom Knowledge file plus an importable <code>SKILL.md</code> playbook (Workspace Settings → Skills → Add → Upload ZIP). You can also connect AgentScout's MCP Registry directly in Lovable at <code>https://mcp.agentscouthq.com/v0/servers</code>.</p>
</section>'''

BLOCK = f"{MARK_START}{SECTION_INNER}{MARK_END}"

_MARKED = re.compile(re.escape(MARK_START) + r".*?" + re.escape(MARK_END), re.S)
_LEGACY_INTRO = re.compile(
    r"\s*<p>Every one of the <a href=\"[^\"]*bot-store/#ai-agent-packs\">25 AI Agent Packs \(\$35[–-]\$349\) on the AgentScout Bot Store</a> includes a ready-to-import <code>LOVABLE\.md</code>.*?</p>",
    re.S,
)
_LEGACY_H2 = re.compile(
    r"\s*<h2[^>]*>Pre-Trained Lovable AI Agent Packs(?: &amp;| &) MCP Registry</h2>\s*<p>All <a href=\"[^\"]*bot-store/#ai-agent-packs\">25 Pre-Trained AI Agent Packs</a>.*?</p>",
    re.S,
)
_ANCHORS = (
    re.compile(r'<h2 style="font-size:16px;margin-bottom:12px">[^<]*alternatives</h2>'),
    re.compile(r"<!--xl:tool-->"),
    re.compile(r'<h2 style="font-size:16px;margin:36px 0 6px">Badge for makers</h2>'),
    re.compile(r'<aside class="panel">'),
    re.compile(r"</main>"),
)


def apply(html: str) -> str:
    """Return html with exactly one packs section. Idempotent."""
    html = _MARKED.sub("", html)
    html = _LEGACY_INTRO.sub("", html)
    html = _LEGACY_H2.sub("", html)
    for pat in _ANCHORS:
        m = pat.search(html)
        if m:
            return html[: m.start()] + BLOCK + html[m.start() :]
    return html + BLOCK


def _sitemap() -> None:
    path = Path("sitemap.xml")
    if not path.exists():
        return
    sm = path.read_text(encoding="utf-8")
    loc = "https://agentscouthq.com/tools/lovable.html"
    if loc in sm:
        return
    line = f"  <url><loc>{loc}</loc><lastmod>2026-10-28</lastmod></url>\n"
    needle = "  <url><loc>https://agentscouthq.com/tools/v0.html</loc>"
    if needle in sm:
        sm = sm.replace(needle, line + needle, 1)
    else:
        sm = sm.replace("</urlset>", line + "</urlset>", 1)
    path.write_text(sm, encoding="utf-8")


def _shell_page() -> str:
    """Fallback when the build has not written tools/lovable.html yet."""
    import json

    sys.path.insert(0, str(ROOT))
    import build_extras as X

    tool = next(x for x in json.load(open("tools.json")) if x["slug"] == "lovable")
    body = f'''
<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="../categories/app-builders.html">app builders</a> / Lovable</div>
<section style="padding-top:20px"><div class="detail"><div>
<div class="badges"><span class="b cat">app builders</span><span class="b">Freemium</span><span class="b new">New</span></div>
<h1 class="icoh"><span class="ico lg"><img src="../assets/logos/lovable.png" alt="Lovable logo" width="56" height="56"></span><span>Lovable</span></h1>
<p class="lede">{X.e(tool["description"])}</p>
<div class="acts"><a class="btn primary" href="https://lovable.dev" target="_blank" rel="noopener noreferrer">Visit lovable.dev ↗</a></div>
<h2 style="font-size:16px;margin:28px 0 10px">About Lovable</h2>
<p>Lovable is the AI app builder at lovable.dev. It is listed next to <a href="lovable-mcp.html">Lovable MCP</a>, the official MCP server for working with Lovable projects from another agent. Lovable workspaces can import a skill ZIP under Workspace settings, Skills, Add, Upload ZIP, and they can connect a registry that serves <code>GET /v0/servers</code>.</p>
<p>Pricing, as the maker states it: free tier and paid plans on the official site. This page is the product. The MCP server listing stays on its own page.</p>
</div>
<aside class="panel"><h3>At a glance</h3><dl><dt>Category</dt><dd>app builders</dd><dt>Website</dt><dd><a href="https://lovable.dev" target="_blank" rel="noopener noreferrer">lovable.dev</a></dd><dt>Pricing</dt><dd>Freemium</dd><dt>Related</dt><dd><a href="lovable-mcp.html">Lovable MCP</a></dd></dl></aside>
</div></section>
'''
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "name": "Lovable: what it does, pricing and alternatives",
                "url": "https://agentscouthq.com/tools/lovable.html",
                "isPartOf": {"@type": "WebSite", "name": "AgentScout", "url": "https://agentscouthq.com/"},
                "about": {
                    "@type": "SoftwareApplication",
                    "name": "Lovable",
                    "url": "https://lovable.dev",
                    "applicationCategory": "BusinessApplication",
                    "description": tool["description"],
                },
            }
        ],
    }
    html = X.shell(
        "../",
        "Lovable: what it does, pricing and alternatives",
        "Lovable is an AI app builder that turns a prompt into a full-stack web app. Listed on AgentScout next to Lovable MCP.",
        "https://agentscouthq.com/tools/lovable.html",
        body,
        ld,
    )
    ref_path = next(
        (Path(p) for p in ("tools/cursor.html", "tools/v0.html", "index.html") if Path(p).exists()),
        None,
    )
    if ref_path is not None:
        ref = ref_path.read_text(encoding="utf-8")
        nav = re.search(r"<nav\b[^>]*>.*?</nav>", ref, re.S)
        foot = re.search(r"<footer\b[^>]*>.*?</footer>", ref, re.S)
        depth = "" if ref_path.parent.name == "tools" else "../"
        if nav:
            block = nav.group(0)
            if depth:
                block = re.sub(r'(href|src)=(["\'])(?!https?:|mailto:|#|javascript:|\.\./|/)', rf"\1=\2{depth}", block)
            html = re.sub(r"<nav\b[^>]*>.*?</nav>", lambda _m: block, html, count=1, flags=re.S)
        if foot:
            block = foot.group(0)
            if depth:
                block = re.sub(r'(href|src)=(["\'])(?!https?:|mailto:|#|javascript:|\.\./|/)', rf"\1=\2{depth}", block)
            html = re.sub(r"<footer\b[^>]*>.*?</footer>", lambda _m: block, html, count=1, flags=re.S)
    return html


def run() -> int:
    prev = os.getcwd()
    os.chdir(ROOT)
    try:
        page = Path("tools/lovable.html")
        if page.exists():
            html = page.read_text(encoding="utf-8")
        else:
            html = _shell_page()
        new = apply(html)
        n = new.count(f'id="{SECTION_ID}"')
        if n != 1:
            print(f"FAIL tools/lovable.html packs section count {n}")
            return 1
        if new != html or not page.exists():
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(new, encoding="utf-8")
            print("wrote tools/lovable.html (1 AI Agent Packs section)")
        else:
            print("tools/lovable.html already has 1 AI Agent Packs section")
        _sitemap()
        return 0
    finally:
        os.chdir(prev)


if __name__ == "__main__":
    sys.exit(run())
