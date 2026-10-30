"""Build Quick-Start Guides, Walkthroughs & Pro Tips hub (/videos/index.html)."""
import os, re, json, datetime
from build_extras import B, e, shell, clip_text, clip_title

def pages(t):
    os.makedirs("videos", exist_ok=True)
    n_tools = len(t)
    n_bt = __import__("build_bot_templates").live_bot_template_count()
    n_mcp = sum(1 for x in t if x.get("category") == "MCP servers")
    n_cats = len({x.get("category") for x in t if x.get("category")})
    today_iso = datetime.date.today().strftime("%Y-%m-%dT08:00:00-07:00")

    guides = [
        {
            "id": "guide-mcp-setup",
            "cat": "mcp",
            "cat_label": "MCP Setup",
            "badge": "60s Quickstart · Zero API Keys",
            "color": "#14b8a6",
            "title": f"Connect AgentScout's Free MCP Server to Claude, Cursor & VS Code ({n_mcp}+ MCPs)",
            "summary": f"Query all {n_tools:,}+ verified AI agent tools and {n_mcp}+ MCP servers directly inside Claude Desktop, Claude Code, Cursor, Windsurf, or Codex over Streamable HTTP or SSE — 100% free and read-only.",
            "video": "../assets/animations/agentscout-mcp-terminal.mp4",
            "poster": "../assets/animations/agentscout-mcp-terminal-poster.png",
            "video_url": f"{B}assets/animations/agentscout-mcp-terminal.mp4",
            "poster_url": f"{B}assets/animations/agentscout-mcp-terminal-poster.png",
            "w": 1200,
            "h": 540,
            "duration": "PT20S",
            "steps": [
                "Copy the one-line CLI command or JSON config block below (no API key or account needed).",
                "Run it in your terminal for Claude Code, or paste into ~/.cursor/mcp.json or claude_desktop_config.json.",
                "Ask your coding agent: 'Use AgentScout MCP to find the best open-source browser automation MCP server.'"
            ],
            "snippet": 'claude mcp add --transport http agentscout https://mcp.agentscouthq.com/mcp',
            "links": [
                ("../mcp/connect.html", "Open MCP Server Setup Guide →"),
                ("../free-tools/mcp-config-builder.html", "Interactive MCP Config Builder →"),
                ("../mcp/index.html", f"Browse All {n_mcp} MCP Servers →"),
            ],
        },
        {
            "id": "guide-trained-bots",
            "cat": "bots",
            "cat_label": "Pre-Trained Bots",
            "badge": "Pro Bots ($39–$149) & 25 AI Agent Packs ($35–$349)",
            "color": "#f59e0b",
            "title": "Deploy AgentScout's Pre-Trained Pro Bots ($39 / $59 / $59 / $69 / $149) & 25 AI Agent Packs ($35 / $119 / $199 / $299 / $349)",
            "summary": "See how 1. AgentScout Operations / Monitoring Bot ($39), 2. AgentScout SEO & AEO Growth Auditor Bot ($59), 3. AgentScout Market & Launch Intel Bot ($59), and 4. AgentScout CEO Coordinator Bot ($69) coordinate via shared workspace handoffs ($149 4-Bot Team Bundle, Save $77) — plus 25 role-specific AI Agent Packs ($35 for 1, $119 for 5, $199 for 10, $299 for 20, or $349 for all 25). Built for Grok Bot and compatible with Claude Code, Cursor, OpenAI Codex, and Lovable.",
            "video": "../assets/animations/agentscout-trained-bots-ad.mp4",
            "poster": "../assets/animations/agentscout-trained-bots-ad-poster.png",
            "video_url": f"{B}assets/animations/agentscout-trained-bots-ad.mp4",
            "poster_url": f"{B}assets/animations/agentscout-trained-bots-ad-poster.png",
            "w": 1200,
            "h": 560,
            "duration": "PT20S",
            "steps": [
                "Choose any of the 4 downloadable Pro Bots ($39 / $59 / $59 / $69 or $149 4-Bot Bundle) or mix-and-match from 25 Pre-Trained AI Agent Packs ($35 single, $119 5-Bot Pack, $199 10-Bot Pack, $299 20-Bot Pack, or $349 All-25 Mega Pack).",
                "Unzip your instant download to get README-QUICKSTART.md, setup_workspace.py, SYSTEM.md, cron routines, custom AgentScout skills, and zero-key mcp.json.",
                "Run python3 setup_workspace.py --domain yoursite.com and drop the native config into Grok Bot (SYSTEM.md), Claude Code (CLAUDE.md), Cursor (.cursorrules), OpenAI Codex (AGENTS.md), Lovable (LOVABLE.md), Copilot, Windsurf, Cline, or Cron in under 3 minutes."
            ],
            "snippet": '{"mcpServers":{"agentscout":{"url":"https://mcp.agentscouthq.com/mcp"}}}',
            "links": [
                ("../bot-store/", "Shop Pre-Trained Pro Bots ($39 / $59 / $59 / $69 / $149) →"),
                ("../bot-templates/index.html#bt-featured", f"Browse {n_bt} Community Bot Templates →"),
            ],
        },
        {
            "id": "guide-vs-compare",
            "cat": "compare",
            "cat_label": "Compare & Pick",
            "badge": "Side-by-Side Benchmarks",
            "color": "#0ea5e9",
            "title": "How to Compare Coding Agents, Browser Agents & Frameworks Side-by-Side",
            "summary": "Use AgentScout's 87 head-to-head VS matrices and interactive comparison picker to evaluate pricing, open-source licenses, GitHub star velocity, local execution support, and MCP compatibility.",
            "video": "../assets/animations/agentscout-vs-arena.mp4",
            "poster": "../assets/animations/agentscout-vs-arena-poster.png",
            "video_url": f"{B}assets/animations/agentscout-vs-arena.mp4",
            "poster_url": f"{B}assets/animations/agentscout-vs-arena-poster.png",
            "w": 1200,
            "h": 520,
            "duration": "PT20S",
            "steps": [
                "Open /compare/ to pick any two AI agents (e.g., Cursor vs Windsurf, Claude Code vs OpenCode, Browser Use vs Stagehand).",
                "Check the verified pricing model, GitHub star growth, license type, and local/offline capability row by row.",
                "Use the Agent Run Cost Estimator to project monthly token and API spend before committing to a stack."
            ],
            "snippet": "curl -s https://agentscouthq.com/api/tools.json | jq '.tools[] | select(.category==\"coding\") | {name, pricing, github_stars}'",
            "links": [
                ("../compare/index.html", "Open Head-to-Head VS Comparisons →"),
                ("../best/index.html", "Browse Ranked Best-Of Guides →"),
                ("../free-tools/agent-run-cost-estimator.html", "Run Agent Cost Calculator →"),
            ],
        },
        {
            "id": "guide-home-terminal",
            "cat": "protips",
            "cat_label": "Pro Tips",
            "badge": "6-Agent Daily Verification",
            "color": "#6366f1",
            "title": f"Inside AgentScout's 6-Agent Live Verification Terminal ({n_tools:,}+ Tools Checked Daily)",
            "summary": f"Watch how our 6 autonomous verification agents scan GitHub repositories, test live HTTP/JSON-RPC endpoints, filter dead wrappers, and update {n_tools:,}+ listings across {n_cats} categories every morning.",
            "video": "../assets/animations/agentscout-home-terminal.mp4",
            "poster": "../assets/animations/agentscout-home-terminal-poster.png",
            "video_url": f"{B}assets/animations/agentscout-home-terminal.mp4",
            "poster_url": f"{B}assets/animations/agentscout-home-terminal-poster.png",
            "w": 1200,
            "h": 620,
            "duration": "PT20S",
            "steps": [
                "Filter the directory by price tag (Free, Freemium, Paid), open-source license, or task on the homepage.",
                "Check the 'Links checked' badge on any tool page to see its latest HTTP 200 verification date and GitHub star count.",
                "Fetch /llms-full.txt or /api/tools.json in any AI workflow for zero-hallucination grounding."
            ],
            "snippet": "curl -s https://agentscouthq.com/llms.txt | head -n 35",
            "links": [
                ("../index.html#directory", f"Search All {n_tools:,} Verified Tools →"),
                ("../mcp/link-status.html", "Live MCP Link-Status Table →"),
                ("../llms.txt", "Read llms.txt Machine Catalog →"),
            ],
        },
        {
            "id": "guide-bot-constellation",
            "cat": "bots",
            "cat_label": "Bot Templates",
            "badge": "19 Free Browser Calculators",
            "color": "#10b981",
            "title": "How to Combine Free Browser Calculators with Ready-Made Agent Skills",
            "summary": "Pair AgentScout's 19 zero-signup browser calculators (Token Counter, Context Window Sizer, Cron Builder, JSON Schema Validator, AEO Checker) with installable skills for Grok Bot, Claude Code, Cursor, OpenAI Codex, and Windsurf.",
            "video": "../assets/animations/agentscout-bot-constellation.mp4",
            "poster": "../assets/animations/agentscout-bot-constellation-poster.png",
            "video_url": f"{B}assets/animations/agentscout-bot-constellation.mp4",
            "poster_url": f"{B}assets/animations/agentscout-bot-constellation-poster.png",
            "w": 1200,
            "h": 540,
            "duration": "PT20S",
            "steps": [
                "Open /free-tools.html and pick a calculator (all 19 run 100% client-side in your browser with zero signup).",
                "Generate your mcp.json, system prompt cost estimate, or cron schedule expression and copy with 1 click.",
                "Attach the matching skill from /skills/ or /bot-templates/ to automate the workflow recurringly."
            ],
            "snippet": "npx skills add agentscout/mcp-discovery",
            "links": [
                ("../free-tools.html", "Launch 19 Free Browser Calculators →"),
                ("../skills/index.html", "Browse Agent Skills with Install Commands →"),
                ("../quiz.html", "Take the 30-Second Agent Finder Quiz →"),
            ],
        },
        {
            "id": "guide-sponsor-submit",
            "cat": "submit",
            "cat_label": "Directory Listings",
            "badge": "For AI Tool Makers & Founders",
            "color": "#ec4899",
            "title": "For Tool Makers: How to List Your AI Tool or MCP Server in the Directory ($0 / $15 / $49 / $99)",
            "summary": "Walkthrough of AgentScout's 4 Directory Listing packages for tool makers: from the $0 Free Forever Community Listing to same-day $15 Fast-Track, $49 30-Day Category Pin + Permanent SEO/AEO Placement, and $99/wk Sitewide Sponsor.",
            "video": "../assets/animations/agentscout-sponsor-placements.mp4",
            "poster": "../assets/animations/agentscout-sponsor-placements-poster.png",
            "video_url": f"{B}assets/animations/agentscout-sponsor-placements.mp4",
            "poster_url": f"{B}assets/animations/agentscout-sponsor-placements-poster.png",
            "w": 1200,
            "h": 560,
            "duration": "PT20S",
            "steps": [
                "Submit your tool free at /submit.html#free-form ($0 forever, standard review queue, permanent /tools/<slug>.html page + MCP indexing).",
                "Need same-day review + 7-day /new.html pin? Choose the $15 Fast-Track Launch Boost via Stripe or X Money (@clampdown19).",
                "Want 30-day category top pin + permanent /best/ & /compare/ placement + X spotlight? Pick the $49 Most Popular tier or $99/wk Sitewide Sponsor."
            ],
            "snippet": "curl -s https://agentscouthq.com/api/products.json | jq '.packages[] | {name, price_usd, checkout_url}'",
            "links": [
                ("../submit.html#free-form", "Submit Your Tool Free ($0) →"),
                ("../sponsor.html#packages", "Compare Directory Listing Tiers ($0 / $15 / $49 / $99) →"),
                ("../badges.html", "Get Your Free Verified README Badge →"),
            ],
        },
        {
            "id": "guide-workflow-stack",
            "cat": "protips",
            "cat_label": "Pro Tips",
            "badge": "Production Stack Blueprint",
            "color": "#10b981",
            "title": "How to Wire a 5-Layer Production AI Agent Stack (Coding + Browser + Memory + Sandbox + MCP)",
            "summary": "Step-by-step blueprint for combining a coding agent (OpenCode / Claude Code), browser runtime (Browser Use / Crawl4AI), live docs MCP (Context7), isolated microVM sandbox, and persistent memory.",
            "video": "../assets/animations/agentscout-workflow-infographic.mp4",
            "poster": "../assets/animations/agentscout-workflow-infographic-poster.png",
            "video_url": f"{B}assets/animations/agentscout-workflow-infographic.mp4",
            "poster_url": f"{B}assets/animations/agentscout-workflow-infographic-poster.png",
            "w": 1200,
            "h": 480,
            "duration": "PT20S",
            "steps": [
                "Layer 1 & 2 (Code + Docs): Pair your terminal coding agent with Context7 MCP so it never hallucinates deprecated SDK methods.",
                "Layer 3 & 4 (Browser + Sandbox): Run headless browser tasks and untrusted code inside an isolated sandbox runtime.",
                "Layer 5 (Discovery): Connect AgentScout MCP (https://mcp.agentscouthq.com/mcp) so your agent can discover new tools on demand."
            ],
            "snippet": 'claude mcp add --transport sse agentscout-sse https://agentscouthq.com/mcp/sse',
            "links": [
                ("../tasks/index.html", "Browse AI Agents by Task (86 Guides) →"),
                ("../best/mcp-servers-for-claude-code.html", "Best MCP Servers for Claude Code →"),
                ("../best/open-source-browser-automation-agents.html", "Best Open-Source Browser Agents →"),
            ],
        },
        {
            "id": "guide-radar-benchmarks",
            "cat": "compare",
            "cat_label": "Compare & Pick",
            "badge": "2026 Category Leaders",
            "color": "#38bdf8",
            "title": "2026 AI Agent Category Radar: How We Score Speed, Open-Source Stars & Local Execution",
            "summary": "See how AgentScout benchmarks category leaders across Coding, Browser Automation, MCP Infrastructure, Crawling/RAG, and Multi-Agent Frameworks using live GitHub telemetry and daily link checks.",
            "video": "../assets/animations/agentscout-radar-infographic.mp4",
            "poster": "../assets/animations/agentscout-radar-infographic-poster.png",
            "video_url": f"{B}assets/animations/agentscout-radar-infographic.mp4",
            "poster_url": f"{B}assets/animations/agentscout-radar-infographic-poster.png",
            "w": 1200,
            "h": 540,
            "duration": "PT20S",
            "steps": [
                "Check /leaderboard/ to see top-rated and fastest-growing open-source AI agent repositories updated daily.",
                "Use the 'Runs locally' filter in AgentScout MCP (runs_locally: 'offline' or 'self_hosted_or_offline') for strict privacy stacks.",
                "Subscribe to AgentScout Weekly for Tuesday's 6-block visual radar digest and free 50 AI Agents + 50 MCP Cheat Sheets."
            ],
            "snippet": "https://agentscouthq.com/leaderboard/",
            "links": [
                ("../leaderboard/index.html", "Open Live GitHub Star Leaderboard →"),
                ("../best/local-offline-ai-agents.html", "Best Local & Offline AI Agents →"),
                ("../newsletter.html", "Read AgentScout Weekly Archive →"),
            ],
        },
    ]

    pro_tips = [
        ("⚡ Zero-Key MCP Discovery", "Point Claude Code, Cursor, or Grok Bot to https://mcp.agentscouthq.com/mcp (Streamable HTTP) or https://agentscouthq.com/mcp/sse to search all 1,800+ tools live without an API key.", "../mcp/connect.html", "Setup MCP →"),
        ("🧮 Size Context & Cost Before You Build", "Run the Token Counter, Context Window Sizer, and Agent Run Cost Estimator in your browser before picking a model tier.", "../free-tools.html", "Open 19 Free Calculators →"),
        ("🤖 Buy Pre-Trained Pro Bots ($39–$149) & 25 AI Agent Packs ($35–$349)", "Buy our 4 Flagship Pro Bots ($39 / $59 / $59 / $69 or $149 4-Bot Bundle) or 25 role-specific AI Agent Packs ($35 single, $119 for 5, $199 for 10, $299 for 20, $349 for all 25) — compatible with Grok Bot, Claude Code, Cursor, Codex & Lovable.", "../bot-store/", "Open Bot Store →"),
        ("📄 Ground LLMs with llms-full.txt", "Pass https://agentscouthq.com/llms-full.txt into Cursor @Docs, NotebookLM, or Claude Projects for full category tables and verified MCP endpoints.", "../llms-full.txt", "Open llms-full.txt →"),
        ("🔒 Filter for Local-First & MIT/Apache", "Need zero data egress? Filter by Open Source + Local execution on /best/local-offline-ai-agents.html or query runs_locally='offline' via MCP.", "../best/local-offline-ai-agents.html", "Local AI Agents →"),
        ("🚀 List Your AI Tool in the Directory", "Building an AI agent or MCP server? Community directory listings are $0 forever, or choose a Maker Directory Boost ($15 Fast-Track, $49 30-Day Pin, or $99/wk Sponsor).", "../sponsor.html#packages", "Directory Listing Tiers →"),
    ]

    faq = [
        ("Are all video guides and walkthroughs on this page free?", "Yes. Every walkthrough video, copy-paste MCP snippet, and browser calculator on AgentScout is 100% free with no sign-up required."),
        ("How do I connect AgentScout to Claude Code, Cursor, or VS Code?", "Run claude mcp add --transport http agentscout https://mcp.agentscouthq.com/mcp in your terminal, or add https://mcp.agentscouthq.com/mcp (or https://agentscouthq.com/mcp/sse) to your mcp.json file. No API key is needed."),
        ("What is the difference between Pre-Trained Pro Bots ($39–$149) / 25 AI Agent Packs ($35–$349) and Directory Listing Packages ($0 / $15 / $49 / $99)?", "Pre-Trained Pro Bots and 25 AI Agent Packs (on /bot-store/ and /bot-templates/) are downloadable agent configurations (with README-QUICKSTART.md, setup_workspace.py, SYSTEM.md, cron routines, Python CLI scripts, and native files for Grok Bot, Claude Code, Cursor, OpenAI Codex & Lovable) that you buy to run your own business: 4 Flagship Pro Bots ($39 / $59 / $59 / $69 or $149 4-Bot Bundle) and 25 role-specific AI Agent Packs ($35 single, $119 for 5, $199 for 10, $299 for 20, or $349 for all 25). Directory Listing Packages (on /submit.html and /sponsor.html) are for AI tool makers who want to list and promote their own software product inside the AgentScout directory ($0 Free, $15 Fast-Track, $49 30-Day Category Pin, or $99/wk Sitewide Sponsor)."),
        ("How often are the tools and metrics in these guides updated?", f"Every day at 7:00 AM PT. All {n_tools:,} tools and {n_mcp} MCP servers are link-checked and synced with live GitHub star counts daily."),
    ]

    css = '''<style id="vid-hub-css">
.vh-hero img.aswm{filter:invert(1) hue-rotate(180deg)}
.vh-hero{margin:12px 0 22px;padding:22px;border-radius:16px;border:1px solid rgba(56,189,248,.32);background:linear-gradient(145deg,#070b14 0%,#0f172a 60%,#131129 100%);color:#f8fafc;box-shadow:0 12px 32px rgba(2,6,23,.25)}
.vh-eyebrow{display:inline-flex;align-items:center;gap:6px;padding:4px 11px;border-radius:999px;background:rgba(20,184,166,.16);border:1px solid rgba(20,184,166,.45);color:#2dd4bf;font-size:12px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;margin-bottom:10px}
.vh-hero h1{margin:0 0 8px;font-size:clamp(22px,3.2vw,32px);line-height:1.2;color:#fff}
.vh-hero p{margin:0 0 14px;color:#cbd5e1;font-size:15px;line-height:1.55;max-width:820px}
.vh-pills{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 6px}
.vh-pill{appearance:none;border:1px solid var(--line);background:var(--card);color:var(--text);padding:8px 14px;border-radius:999px;font:inherit;font-size:13px;font-weight:600;cursor:pointer;min-height:40px;display:inline-flex;align-items:center;gap:6px;transition:all .15s ease}
.vh-pill:hover{border-color:#0ea5e9}
.vh-pill.on{background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff;border-color:transparent;box-shadow:0 4px 14px rgba(14,165,233,.3)}
.vh-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin:18px 0 28px}
.vh-card{display:flex;flex-direction:column;border-radius:14px;border:1px solid var(--line);background:var(--card);overflow:hidden;min-width:0;box-shadow:0 4px 16px rgba(0,0,0,.06)}
.vh-vidwrap{position:relative;width:100%;background:#060810;border-bottom:1px solid var(--line);overflow:hidden;line-height:0}
.vh-vidwrap video{display:block;width:100%;height:auto;max-width:100%;object-fit:contain;background:#060810}
.vh-body{padding:16px;display:flex;flex-direction:column;gap:10px;flex:1;min-width:0}
.vh-meta{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px}
.vh-badge{display:inline-flex;align-items:center;padding:3px 10px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:.02em}
.vh-title{margin:0;font-size:17px;line-height:1.35;color:var(--text)}
.vh-sum{margin:0;font-size:13.5px;line-height:1.5;color:var(--muted)}
.vh-steps{margin:2px 0;padding-left:18px;font-size:13px;line-height:1.5;color:var(--text)}
.vh-steps li{margin-bottom:4px}
.vh-code{display:flex;align-items:center;justify-content:space-between;gap:8px;background:#090d16;border:1px solid rgba(56,189,248,.28);border-radius:10px;padding:8px 10px;min-width:0}
.vh-code code{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:12px;color:#38bdf8;overflow-x:auto;white-space:nowrap;flex:1;min-width:0}
.vh-copy{flex:0 0 auto;background:rgba(56,189,248,.16);border:1px solid rgba(56,189,248,.4);color:#7dd3fc;border-radius:7px;padding:5px 10px;font-size:11.5px;font-weight:700;cursor:pointer;min-height:32px}
.vh-copy:hover{background:rgba(56,189,248,.28);color:#fff}
.vh-links{display:flex;flex-wrap:wrap;gap:8px;margin-top:auto;padding-top:6px}
.vh-links a{font-size:12.5px;font-weight:600;text-decoration:none;padding:6px 11px;border-radius:8px;background:var(--soft);border:1px solid var(--line);color:var(--text);display:inline-flex;align-items:center;min-height:36px}
.vh-links a:hover{border-color:#0ea5e9;color:#0ea5e9}
.vh-tips{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:14px 0 28px}
.vh-tip{padding:15px;border-radius:12px;border:1px solid var(--line);background:var(--card);display:flex;flex-direction:column;gap:6px;min-width:0}
.vh-tip h3{margin:0;font-size:15px;color:var(--text)}
.vh-tip p{margin:0;font-size:13px;line-height:1.5;color:var(--muted);flex:1}
.vh-tip a{font-size:13px;font-weight:700;color:#0ea5e9;text-decoration:none;margin-top:4px;display:inline-flex;align-items:center;min-height:34px}
@media(max-width:920px){.vh-grid{grid-template-columns:1fr}.vh-tips{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:560px){.vh-hero img.aswm{filter:invert(1) hue-rotate(180deg)}
.vh-hero{padding:16px}.vh-hero .btn{width:100%;max-width:100%;box-sizing:border-box;white-space:normal;text-align:center;justify-content:center;height:auto;min-height:44px;line-height:1.35;padding:10px 12px}.vh-tips{grid-template-columns:1fr}.vh-links a{width:100%;box-sizing:border-box;justify-content:center}}
</style>'''

    cards_html = []
    for idx, g in enumerate(guides, 1):
        steps_li = "".join(f"<li>{e(st)}</li>" for st in g["steps"])
        links_a = "".join(
            f'<a href="{e(u)}"' + (' target="_blank" rel="noopener noreferrer"' if u.startswith("http") else "") + f">{e(lbl)}</a>"
            for u, lbl in g["links"]
        )
        vw, vh = 1200, 640
        cards_html.append(
            f'<article class="vh-card" id="{e(g["id"])}" data-vh-cat="{e(g["cat"])}">'
            f'<div class="vh-vidwrap"><video controls autoplay loop muted playsinline preload="metadata" poster="{e(g["poster"])}" width="{vw}" height="{vh}" style="aspect-ratio:{vw}/{vh}">'
            f'<source src="{e(g["video"])}" type="video/mp4">'
            f'</video></div>'
            f'<div class="vh-body">'
            f'<div class="vh-meta">'
            f'<span class="vh-badge" style="background:{g["color"]}22;border:1px solid {g["color"]}77;color:{g["color"]}">{e(g["cat_label"])} · {e(g["badge"])}</span>'
            f'<span class="muted" style="font-size:12px">Guide #{idx} · 20s Step-by-Step Walkthrough</span>'
            f'</div>'
            f'<h2 class="vh-title">{e(g["title"])}</h2>'
            f'<p class="vh-sum">{e(g["summary"])}</p>'
            f'<ol class="vh-steps">{steps_li}</ol>'
            f'<div class="vh-code"><code id="code-{e(g["id"])}">{e(g["snippet"])}</code>'
            f'<button type="button" class="vh-copy" data-copy-target="code-{e(g["id"])}">Copy</button></div>'
            f'<div class="vh-links">{links_a}</div>'
            f'</div></article>'
        )

    tips_html = "".join(
        f'<div class="vh-tip"><h3>{e(tt)}</h3><p>{e(td)}</p><a href="{e(tu)}">{e(tl)}</a></div>'
        for tt, td, tu, tl in pro_tips
    )

    faq_html = "".join(
        f'<details style="border-bottom:1px solid var(--line);padding:10px 0"><summary style="font-weight:600;cursor:pointer">{e(q)}</summary><p style="margin:8px 0 0;color:var(--muted);font-size:14px;line-height:1.55">{e(a)}</p></details>'
        for q, a in faq
    )

    js = '''<script id="vid-hub-js">(function(){
var pills=[].slice.call(document.querySelectorAll('.vh-pill')),cards=[].slice.call(document.querySelectorAll('.vh-card')),st=document.getElementById('vh-status');
pills.forEach(function(btn){
  btn.addEventListener('click',function(){
    var f=btn.getAttribute('data-vh-filter');
    pills.forEach(function(p){var on=p===btn;p.classList.toggle('on',on);p.setAttribute('aria-pressed',on?'true':'false')});
    var n=0;
    cards.forEach(function(c){
      var ok=(f==='all'||c.getAttribute('data-vh-cat')===f);
      c.style.display=ok?'flex':'none';
      if(ok)n++;
    });
    if(st)st.textContent='Showing '+n+' of '+cards.length+' video guides';
  });
});
[].slice.call(document.querySelectorAll('.vh-copy')).forEach(function(b){
  b.addEventListener('click',function(){
    var id=b.getAttribute('data-copy-target'),el=document.getElementById(id);
    if(!el)return;
    navigator.clipboard.writeText(el.textContent).then(function(){
      var old=b.textContent;b.textContent='Copied!';setTimeout(function(){b.textContent=old},1600);
    });
  });
});
})();</script>'''

    body = (
        '<div class="crumb"><a href="../index.html">AgentScout</a> / Quick-Start Guides, Walkthroughs &amp; Pro Tips</div>'
        '<section class="vh-hero">'
        '<span class="vh-eyebrow">20s Step-by-Step · Pause &amp; Scrub Steps 1–3 · Zero Signup</span>'
        f'<h1 data-pagefind-weight="10">Quick-Start Guides, Walkthroughs &amp; Pro Tips ({len(guides)})</h1>'
        f'<p>Twenty-second walkthroughs with three steps each: connect AgentScout\'s free MCP server (<code>com.agentscouthq/directory</code>) to Claude Code, Cursor &amp; VS Code, compare {n_tools:,}+ AI agents side-by-side, deploy our downloadable Pro Bots built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"> (<code>$39</code> / <code>$59</code> / <code>$59</code> / <code>$69</code> or all 4 for <code>$149</code>), and use 19 free browser calculators. Pause or scrub to Step 1, Step 2, or Step 3.</p>'
        '<div style="display:flex;flex-wrap:wrap;gap:8px">'
        '<a class="btn primary" href="../mcp/connect.html" style="background:#14b8a6;border-color:#14b8a6;color:#042f2e;font-weight:700">Connect Free MCP Server →</a>'
        '<a class="btn primary" href="../bot-store/" style="background:linear-gradient(135deg,#f59e0b,#f97316);border-color:#f59e0b;color:#0a0906;font-weight:800">🤖 Shop Pre-Trained Pro Bots ($39 / $59 / $59 / $69 / $149) →</a>'
        '<a class="btn" href="../free-tools.html" style="background:rgba(255,255,255,.08);color:#fff;border-color:rgba(255,255,255,.2)">19 Free Browser Calculators →</a>'
        '</div></section>'
        '<div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px;margin:10px 0">'
        '<div class="vh-pills" role="group" aria-label="Filter video guides by topic">'
        f'<button type="button" class="vh-pill on" data-vh-filter="all" aria-pressed="true">All Guides ({len(guides)})</button>'
        '<button type="button" class="vh-pill" data-vh-filter="mcp" aria-pressed="false">MCP Setup (1)</button>'
        '<button type="button" class="vh-pill" data-vh-filter="bots" aria-pressed="false">Pre-Trained Bots &amp; Templates (2)</button>'
        '<button type="button" class="vh-pill" data-vh-filter="compare" aria-pressed="false">Compare &amp; Benchmarks (2)</button>'
        '<button type="button" class="vh-pill" data-vh-filter="protips" aria-pressed="false">Architecture &amp; Pro Tips (2)</button>'
        '<button type="button" class="vh-pill" data-vh-filter="submit" aria-pressed="false">Directory Listing Guide (1)</button>'
        '</div>'
        f'<p id="vh-status" class="muted" style="margin:0;font-size:13px" role="status" aria-live="polite">Showing {len(guides)} of {len(guides)} video guides</p>'
        '</div>'
        '<div class="vh-grid">' + "".join(cards_html) + '</div>'
        '<section style="margin:28px 0">'
        '<h2 style="font-size:20px;margin:0 0 6px">6 Builder Pro Tips for Production AI Agent Stacks</h2>'
        f'<p class="muted" style="margin:0 0 14px;font-size:14px">Battle-tested shortcuts from running AgentScout\'s daily verification pipeline across <span data-live-tools>{n_tools:,}+</span> tools and <span data-live-mcp>{n_mcp:,}+</span> MCP servers.</p>'
        f'<div class="vh-tips">{tips_html}</div>'
        '</section>'
        '<section style="max-width:860px;margin:28px 0">'
        '<h2 style="font-size:19px;margin:0 0 10px">Video Guides &amp; Pro Tips FAQ</h2>'
        f'{faq_html}</section>'
        + js
    )

    canon = B + "videos/"
    title = clip_title("AI Agent & MCP Quick-Start Guides & Walkthroughs · AgentScout")
    desc = clip_text("Step-by-step AI agent & MCP setup guides, 20s walkthroughs, copyable CLI snippets, and Pro Bot playbooks ($39/$59/$59/$69/$149).", 160)

    video_objects = [
        {
            "@type": "VideoObject",
            "position": idx,
            "name": g["title"],
            "description": g["summary"],
            "thumbnailUrl": g["poster_url"],
            "contentUrl": g["video_url"],
            "embedUrl": canon + "#" + g["id"],
            "uploadDate": today_iso,
            "duration": g["duration"],
        }
        for idx, g in enumerate(guides, 1)
    ]

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "name": title,
                "description": desc,
                "url": canon,
                "isPartOf": {"@type": "WebSite", "name": "AgentScout", "url": B},
            },
            {
                "@type": "ItemList",
                "name": "AgentScout Quick-Start Guides, Walkthroughs & Pro Tips",
                "numberOfItems": len(guides),
                "itemListElement": video_objects,
            },
            *[
                {
                    "@type": "HowTo",
                    "name": g["title"],
                    "description": g["summary"],
                    "totalTime": "PT20S",
                    "step": [
                        {
                            "@type": "HowToStep",
                            "position": i,
                            "name": f"Step {i} of 3",
                            "text": st,
                            "url": canon + "#" + g["id"],
                        }
                        for i, st in enumerate(g["steps"], 1)
                    ],
                }
                for g in guides
            ],
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in faq
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "AgentScout", "item": B},
                    {"@type": "ListItem", "position": 2, "name": "Quick-Start Guides, Walkthroughs & Pro Tips", "item": canon},
                ],
            },
        ],
    }

    html_out = shell("../", title, desc, canon, body, ld)
    html_out = html_out.replace("</head>", css + "</head>", 1)
    html_out = html_out.replace('<main class="wrap">', '<main class="wrap" data-pagefind-body>', 1)
    open("videos/index.html", "w", encoding="utf-8").write(html_out)
    print(f"video guides hub: {len(guides)} guides written to videos/index.html")
    return [canon]

if __name__ == "__main__":
    pages(json.load(open("tools.json", encoding="utf-8")))
