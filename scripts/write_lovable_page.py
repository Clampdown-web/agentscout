#!/usr/bin/env python3
"""Write tools/lovable.html from the shared site shell and list it in the sitemap."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import os
os.chdir(ROOT)
import build_extras as X

tool = next(x for x in json.load(open("tools.json")) if x["slug"] == "lovable")
body = f'''
<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="../categories/app-builders.html">app builders</a> / Lovable</div>
<section style="padding-top:20px"><div class="detail"><div>
<div class="badges"><span class="b cat">app builders</span><span class="b">Freemium</span><span class="b new">New</span></div>
<h1 class="icoh"><span class="ico lg"><img src="../assets/logos/lovable.png" alt="Lovable logo" width="56" height="56"></span><span>Lovable</span></h1>
<p class="lede">{X.e(tool["description"])}</p>
<p class="updated">Updated <time datetime="2026-10-28">October 28, 2026</time></p>
<div class="acts"><a class="btn primary" href="https://lovable.dev" target="_blank" rel="noopener noreferrer">Visit lovable.dev ↗</a></div>
<h2 style="font-size:16px;margin:28px 0 10px">About Lovable</h2>
<p>Lovable is the AI app builder at lovable.dev. It is listed next to <a href="lovable-mcp.html">Lovable MCP</a>, the official MCP server for working with Lovable projects from another agent. Lovable workspaces can import a skill ZIP under Workspace settings, Skills, Add, Upload ZIP, and they can connect a registry that serves <code>GET /v0/servers</code>.</p>
<p>Every one of the <a href="../bot-store/#ai-agent-packs">25 AI Agent Packs ($35–$349) on the AgentScout Bot Store</a> includes a ready-to-import <code>LOVABLE.md</code> project knowledge file and skill ZIP compatible with Lovable alongside Grok Bot, Claude Code, Cursor, and Codex.</p>
<p>Pricing, as the maker states it: free tier and paid plans on the official site. This page is the product. The MCP server listing stays on its own page.</p><h2 style="font-size:16px;margin:28px 0 10px">Pre-Trained Lovable AI Agent Packs &amp; MCP Registry</h2><p>All <a href="../bot-store/#ai-agent-packs">25 Pre-Trained AI Agent Packs</a> ($35 single, $119 for 5, $199 for 10, $299 for 20, or $349 for all 25) and our <a href="../bot-store/">4 Flagship Pro Bots ($39–$149)</a> include a ready-to-paste <code>LOVABLE.md</code> Custom Knowledge file plus an importable <code>SKILL.md</code> playbook (Workspace Settings → Skills → Add → Upload ZIP). You can also connect AgentScout's MCP Registry directly in Lovable at <code>https://mcp.agentscouthq.com/v0/servers</code>.</p>
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
v0_html = Path("tools/v0.html").read_text(encoding="utf-8")
import re as _re
html = _re.sub(r"<nav\b[^>]*>.*?</nav>", lambda _m: _re.search(r"<nav\b[^>]*>.*?</nav>", v0_html, _re.S).group(0), html, count=1, flags=_re.S)
html = _re.sub(r"<footer\b[^>]*>.*?</footer>", lambda _m: _re.search(r"<footer\b[^>]*>.*?</footer>", v0_html, _re.S).group(0), html, count=1, flags=_re.S)
Path("tools/lovable.html").write_text(html, encoding="utf-8")
sm = Path("sitemap.xml").read_text(encoding="utf-8")
loc = "https://agentscouthq.com/tools/lovable.html"
if loc not in sm:
    line = f"  <url><loc>{loc}</loc><lastmod>2026-10-28</lastmod></url>\n"
    sm = sm.replace("  <url><loc>https://agentscouthq.com/tools/v0.html</loc>", line + "  <url><loc>https://agentscouthq.com/tools/v0.html</loc>", 1)
    Path("sitemap.xml").write_text(sm, encoding="utf-8")
print("wrote tools/lovable.html")

import re
ref = Path("tools/cursor.html").read_text(encoding="utf-8")
nav = re.search(r'<nav\b[^>]*>.*?</nav>', ref, re.S).group(0)
ft = re.search(r'<footer\b[^>]*>.*?</footer>', ref, re.S).group(0)
lov = Path("tools/lovable.html").read_text(encoding="utf-8")
lov = re.sub(r'<nav\b[^>]*>.*?</nav>', lambda _: nav, lov, count=1, flags=re.S)
lov = re.sub(r'<footer\b[^>]*>.*?</footer>', lambda _: ft, lov, count=1, flags=re.S)
Path("tools/lovable.html").write_text(lov, encoding="utf-8")
