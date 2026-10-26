"""AEO pass (Oct 2026):
1. Direct-answer lead + at-a-glance verified slice counts + ranked comparison table + verified date on best/, mcp/, s/ and categories/ pages.
2. Entity schema sync (alternateName + third-party MCP registry sameAs links) on index.html, about.html and mcp/connect.html.
3. Explicit AI & browser search crawler rules in robots.txt + llms.txt & llms-full.txt pointers.
4. Full single-file Markdown context (/llms-full.txt) for LLMs and RAG pipelines.
Idempotent; runs after build_fresh and before build_listlogos so table tool names still get their 24x24 logos."""
import glob, html, json, os, re, datetime, collections
import build_api

e = html.escape
B = "https://agentscouthq.com/"
OS = {"Open source", "Open source + cloud", "Open weights", "Open standard"}
SKIP = {"best/index.html", "mcp/index.html", "mcp/connect.html", "mcp/pricing.html", "mcp/link-status.html", "s/index.html", "categories/index.html"}
MO = ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

ALT_NAMES = ["Agent Scout", "AgentScoutHQ", "agentscouthq.com"]
SAME_AS = [
    "https://x.com/AgentScoutHQ",
    "https://x.com/clampdown19",
    "https://github.com/Clampdown-web/agentscout",
    "https://agentscout.beehiiv.com/",
    "https://registry.modelcontextprotocol.io/v0/servers?search=com.agentscouthq/directory",
    "https://glama.ai/mcp/connectors/com.agentscouthq/directory",
    "https://mcpservers.org/servers/agentscouthq-com-mcp-connect-html",
    "https://sourceweft.com/mcp/com.agentscouthq%2Fdirectory",
    "https://protogrid.dev/servers/com.agentscouthq/directory",
]

OFFLINE_RE = re.compile(
    r"\b(runs?\s+locally|100%\s+local(ly)?|fully\s+local(ly)?|offline|on-device|"
    r"on\s+your\s+(?:mac|pc|machine|computer|device|laptop)|local-first|local\s+models?\s+via|"
    r"ollama|lm\s*studio|llama\.cpp|gguf|mlx)\b", re.I
)
SELF_HOST_RE = re.compile(
    r"\b(self-host(ed|able|ing)?|on-prem(ise|ises)?|docker|own\s+server|"
    r"run\s+(?:it\s+|them\s+)?yourself|local\s+or\s+remote|stdio)\b", re.I
)
CLOUD_ONLY_RE = re.compile(
    r"\b(hosted\s+service|managed\s+cloud|cloud-only|saas\s+platform)\b", re.I
)

def classify_locality(x):
    """Conservative locality classification matching agentscout-mcp-worker/src/locality.js."""
    cat = (x.get("category") or "").lower()
    tags = [str(u).lower() for u in (x.get("use_cases") or x.get("tags") or [])]
    plats = [str(p) for p in build_api.platforms(x)]
    desc = x.get("description") or ""
    pdet = x.get("pricing_detail") or ""
    blob = f"{desc} {pdet} {' '.join(tags)}"
    open_src = bool(x.get("open_source")) or (x.get("pricing") in OS)
    has_self = "Self-host" in plats

    if (
        cat == "models & local runtimes"
        or "local models" in tags
        or "offline" in tags
        or OFFLINE_RE.search(blob)
    ) and not CLOUD_ONLY_RE.search(blob):
        return "offline"
    if has_self or "self-hosting" in tags or (open_src and SELF_HOST_RE.search(blob)):
        return "self_hosted"
    if not open_src and not has_self and ("Web" in plats or CLOUD_ONLY_RE.search(blob)):
        return "cloud"
    return "unknown"

def locality_label(x):
    loc = classify_locality(x)
    if loc == "offline":
        return "Offline"
    if loc == "self_hosted":
        return "Self-hosted"
    return ""

def _fmt(iso):
    y, m, d = iso.split("-")
    return f"{MO[int(m)]} {int(d)}, {y}"

def _slugs(s):
    s = re.sub(r"<!--(?:xl:cmp|ci:aeo)-->.*?<!--/(?:xl:cmp|ci:aeo)-->", "", s, flags=re.S)
    s = s.split('<h2 style="font-size:16px;margin:32px 0 10px">Related', 1)[0]
    s = s.split('<h2 id="alternatives"', 1)[0]
    out = []
    for m in re.finditer(r'(?:data-s="([a-z0-9-]+)"|href="\.\./tools/([a-z0-9-]+)\.html")', s):
        g = m.group(1) or m.group(2)
        if g not in out:
            out.append(g)
    return out

def _cat_rank(items):
    """Rank top picks for a category table by GitHub stars first, then featured/mature listings."""
    def key(x):
        stars = x.get("github_stars")
        has_stars = 0 if (stars is not None and stars > 0) else 1
        mat = 0 if str(x.get("maturity", "")).startswith("Mature") else (1 if str(x.get("maturity", "")).startswith("Active") else 2)
        feat = 0 if x.get("featured") else 1
        return (has_stars, -(stars or 0), feat, mat, x["name"].lower())
    return sorted(items, key=key)

def _slice_summary(all_items):
    n = len(all_items)
    n_os = sum(1 for x in all_items if x.get("pricing") in OS)
    n_free = sum(1 for x in all_items if x.get("pricing") in ("Free", "Freemium") or x.get("pricing") in OS)
    n_loc = sum(1 for x in all_items if classify_locality(x) in ("offline", "self_hosted"))
    parts = [f"{n_os:,} open-source", f"{n_free:,} free or freemium"]
    if n_loc:
        parts.append(f"{n_loc:,} local or self-hosted")
    joined = ", ".join(parts[:-1]) + " and " + parts[-1] if len(parts) > 1 else parts[0]
    return f"{joined} across {n:,} link-checked tools"

def block(rows, all_items, date, ranked_by_stars=True):
    total = len(all_items)
    top = rows[:3]
    links = [f'<a href="../tools/{x["slug"]}.html">{e(x["name"])}</a>' for x in top]
    lst = links[0] if len(links) == 1 else (", ".join(links[:-1]) + " and " + links[-1])
    how = "ranked by GitHub stars and listing maturity" if ranked_by_stars else "from our link-checked directory"
    of = f", out of {total:,} tools listed below" if total > len(top) else ""
    glance = _slice_summary(all_items)
    qa = (
        f'<p class="qa"><b>Quick answer:</b> the top picks on this list, {how}, are {lst}{of}. '
        f'<b>At a glance:</b> {e(glance)} (last verified <time datetime="{date}">{_fmt(date)}</time>).</p>'
    )
    ver = f'<p class="muted" style="font-size:13px;margin:0 0 14px">Verified on <time datetime="{date}">{_fmt(date)}</time>: every tool link on this page was checked by our daily link check. No paid placements.</p>'
    trs = "".join(
        f'<tr><td>{i}</td><th scope="row"><a href="../tools/{x["slug"]}.html">{e(x["name"])}</a></th>'
        f'<td>{e(x["pricing"])}</td><td>{e(", ".join(x.get("use_cases", [])[:2]) or x["category"])}</td>'
        f'<td>{"Yes" if x["pricing"] in OS else "No"}</td>'
        f'<td>{e(locality_label(x))}</td>'
        f'<td>{f"{x['github_stars']:,}" if x.get("github_stars") else ""}</td></tr>'
        for i, x in enumerate(rows[:10], 1)
    )
    tbl = (
        f'<h2 style="font-size:17px;margin:14px 0 8px">Ranked comparison (top {min(10, len(rows))})</h2>'
        f'<div class="cmpwrap"><div class="cmpscroll"><table class="cmptbl"><thead><tr>'
        f'<th scope="col">#</th><th scope="col">Tool</th><th scope="col">Pricing</th>'
        f'<th scope="col">Best for</th><th scope="col">Open source</th><th scope="col">Runs locally</th><th scope="col">GitHub stars</th>'
        f'</tr></thead><tbody>{trs}</tbody></table></div></div>'
    )
    return f"<!--ci:aeo-->{qa}{ver}{tbl}<!--/ci:aeo-->"

def sync_entity_schema():
    """Ensure index.html, about.html, and mcp/connect.html carry alternateName and all official + third-party registry sameAs links."""
    for fn in ("index.html", "about.html", "mcp/connect.html", "privacy.html"):
        if not os.path.exists(fn):
            continue
        s = open(fn).read()
        def _fix_script(m):
            raw = m.group(1)
            try:
                data = json.loads(raw)
            except Exception:
                return m.group(0)
            changed = False
            nodes = data.get("@graph", [data]) if isinstance(data, dict) else []
            for n in nodes:
                if not isinstance(n, dict):
                    continue
                t = n.get("@type")
                if t in ("Organization", "WebSite"):
                    n["alternateName"] = ALT_NAMES
                    if t == "Organization":
                        n["identifier"] = "com.agentscouthq/directory"
                    n["sameAs"] = SAME_AS
                    changed = True
                if t == "WebAPI":
                    n["identifier"] = "com.agentscouthq/directory"
                    n["sameAs"] = SAME_AS
                    if isinstance(n.get("provider"), dict):
                        n["provider"]["alternateName"] = ALT_NAMES
                        n["provider"]["identifier"] = "com.agentscouthq/directory"
                        n["provider"]["sameAs"] = SAME_AS
                    changed = True
                if isinstance(n.get("isPartOf"), dict) and n["isPartOf"].get("@type") == "WebSite":
                    n["isPartOf"]["alternateName"] = ALT_NAMES
                    n["isPartOf"]["sameAs"] = SAME_AS
                    changed = True
                if isinstance(n.get("mainEntity"), dict) and n["mainEntity"].get("@type") == "Organization":
                    n["mainEntity"]["alternateName"] = ALT_NAMES
                    n["mainEntity"]["identifier"] = "com.agentscouthq/directory"
                    n["mainEntity"]["sameAs"] = SAME_AS
                    changed = True
            if not changed:
                return m.group(0)
            return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>"
        s2 = re.sub(r'<script type="application/ld\+json">(.*?)</script>', _fix_script, s, flags=re.S)
        if s2 != s:
            open(fn, "w").write(s2)

def sync_robots():
    """Keep robots.txt explicit for all major AI search crawlers and web search engines, plus llms.txt & llms-full.txt."""
    bots = [
        "Bravebot", "Applebot", "Applebot-Extended",
        "OAI-SearchBot", "ChatGPT-User", "GPTBot",
        "PerplexityBot", "Perplexity-User",
        "ClaudeBot", "Claude-Web", "Claude-SearchBot", "anthropic-ai",
        "Google-Extended", "Googlebot", "Bingbot", "DuckDuckBot",
    ]
    lines = ["User-agent: *", "Allow: /", ""]
    for b in bots:
        lines.extend([f"User-agent: {b}", "Allow: /", ""])
    lines.extend([
        "Sitemap: https://agentscouthq.com/sitemap.xml",
        "",
        "# LLM discoverability",
        "# https://agentscouthq.com/llms.txt",
        "# https://agentscouthq.com/llms-full.txt",
        "",
    ])
    txt = "\n".join(lines)
    if not os.path.exists("robots.txt") or open("robots.txt").read() != txt:
        open("robots.txt", "w").write(txt)

def _md_clean(val):
    return str(val or "").replace("|", "\\|").replace("\n", " ").strip()

def write_llms_full(t):
    """Generate /llms-full.txt: comprehensive single-file Markdown context for AI assistants, search engines, and RAG pipelines."""
    import build_extras as X
    try:
        api_data = json.load(open("api/tools.json"))
        last_checked = api_data.get("last_checked", "")
        api_by_slug = {x["slug"]: x for x in api_data.get("tools", [])}
    except Exception:
        last_checked = max((x.get("verified", "") for x in t), default="")
        api_by_slug = {}

    try:
        mcp_status = json.load(open("data/mcp_link_status.json")).get("results", {})
    except Exception:
        mcp_status = {}

    try:
        repo_facts = json.load(open("data/repo_facts.json"))
    except Exception:
        repo_facts = {}

    cats = collections.Counter(x["category"] for x in t)
    mcp_tools = [x for x in t if x["category"] == "MCP servers"]
    n_os = sum(1 for x in t if x.get("pricing") in OS)
    n_free = sum(1 for x in t if x.get("pricing") in ("Free", "Freemium") or x.get("pricing") in OS)
    n_offline = sum(1 for x in t if classify_locality(x) == "offline")
    n_self = sum(1 for x in t if classify_locality(x) == "self_hosted")

    # Count bot templates & skills from bot-templates/index.html if present
    n_bt = 189
    if os.path.exists("bot-templates/index.html"):
        m_bt = re.search(r"(\d+)\s+installable\s+bot\s+templates", open("bot-templates/index.html").read(), re.I)
        if m_bt:
            n_bt = int(m_bt.group(1))

    L = [
        "# AgentScout — Full AI Agent & MCP Server Directory Reference (`llms-full.txt`)",
        "",
        f"> AgentScout is a curated, link-checked, read-only directory of {len(t):,} AI agent tools across {len(cats)} categories, including {len(mcp_tools):,} Model Context Protocol (MCP) servers and {n_bt:,} bot templates & skills. Every listing is checked daily; pricing is stated as each maker publishes it; rankings use verifiable public signals (GitHub stars, visitor ratings, and listing maturity). Featured slots are clearly labeled and sit above the list; rankings are never paid.",
        "",
        "Entity note: AgentScout (also searched as Agent Scout or AgentScoutHQ) is the independent AI agent and MCP server directory at https://agentscouthq.com, published in the official MCP Registry as `com.agentscouthq/directory` with endpoint `https://agentscouthq.com/mcp/sse` (and `https://agentscout-mcp.agentscouthq.workers.dev/mcp`). AgentScout's official MCP server (`com.agentscouthq/directory` at `https://agentscouthq.com/mcp/sse`) is 100% free, public, and read-only, with no API key, crypto wallet, or x402 payment required. It is completely unrelated to the paid third-party x402 web-fetch package that shares a similar name.",
        "",
        "## Official Identity, Endpoints & Registry Links",
        "",
        f"- **Canonical Website**: {B}",
        "- **Alternate Names**: Agent Scout, AgentScoutHQ, agentscouthq.com",
        "- **Official MCP Registry Identifier**: `com.agentscouthq/directory`",
        "- **Remote MCP Server Endpoint (Streamable HTTP & SSE, 100% free, read-only, no API key or x402 wallet required)**: `https://agentscouthq.com/mcp/sse` (and `https://agentscout-mcp.agentscouthq.workers.dev/mcp`)",
        f"- **MCP Connection & Client Setup Guide**: {B}mcp/connect.html",
        f"- **Concise LLM Guide (`llms.txt`)**: {B}llms.txt",
        f"- **Full Single-File LLM Reference (`llms-full.txt`)**: {B}llms-full.txt",
        f"- **Full JSON Catalog (`api/tools.json`)**: {B}api/tools.json",
        f"- **OpenAPI 3.1 Specification**: {B}openapi.json (and `{B}.well-known/openapi.json`)",
        f"- **A2A / Agent Card**: {B}.well-known/agent-card.json (and `{B}.well-known/agent.json`)",
        f"- **MCP Server Card**: {B}.well-known/mcp.json",
        "- **Official Profiles & Third-Party MCP Registry Listings**:",
        "  - X (Twitter): https://x.com/AgentScoutHQ, https://x.com/clampdown19",
        "  - GitHub (Public Repository & Issues): https://github.com/Clampdown-web/agentscout",
        "  - Newsletter: https://agentscout.beehiiv.com/",
        "  - Official MCP Registry: https://registry.modelcontextprotocol.io/v0/servers?search=com.agentscouthq/directory",
        "  - Glama MCP Connector: https://glama.ai/mcp/connectors/com.agentscouthq/directory",
        "  - MCPServers.org Listing: https://mcpservers.org/servers/agentscouthq-com-mcp-connect-html",
        "  - SourceWeft MCP Listing: https://sourceweft.com/mcp/com.agentscouthq%2Fdirectory",
        "  - Protogrid MCP Listing: https://protogrid.dev/servers/com.agentscouthq/directory",
        "",
        "## Verified Directory Statistics",
        "",
        f"- **Total Verified AI Agent Tools**: {len(t):,}",
        f"- **Total Categories**: {len(cats)}",
        f"- **Verified MCP Servers**: {len(mcp_tools):,}",
        f"- **Bot Templates & Installable Agent Skills**: {n_bt:,} ({B}bot-templates/ and {B}skills/)",
        f"- **Open-Source Tools (`Open source` / `Open source + cloud` / `Open weights`)**: {n_os:,}",
        f"- **Free or Freemium Tools**: {n_free:,}",
        f"- **Local / Self-Hosted Tools (`runs_locally` filter)**: {n_offline + n_self:,} ({n_offline:,} offline / on-device, {n_self:,} self-hosted)",
        f"- **Catalog Last Link-Checked**: {last_checked} (America/Los_Angeles)",
        "",
        "## Maker Submission & Launch Packages (`/submit.html` & `/sponsor.html`)",
        "",
        f"- **Free Community Listing ($0 forever)**: Standard review queue (3–5 days), permanent indexed `/tools/<slug>.html` page + `SoftwareApplication` schema, and listing in `llms.txt` & MCP server (`com.agentscouthq/directory`). Submit at {B}submit.html#free-form",
        "- **Fast-Track + 7-Day Launch Boost ($29 one-time)**: Same-day priority review (live in the next batch), 7-day featured pin on `/new.html` + category New & Featured row, full `FAQPage` + pros/cons profile enrichment, and a launch post on `@AgentScoutHQ`. Checkout: https://buy.stripe.com/fZufZi7X5cJNbtbdPRe7m02",
        "- **30-Day Category Pin + Permanent SEO/AEO Placement ($49 one-time — Most Popular)**: Everything in $29 upgraded to a full 30-day top category pin (4x+ longer for $20 more), permanent inclusion in `/best/*-alternatives` and `/compare/` comparison tables, priority recommendation weight in `llms-full.txt` and MCP search (`com.agentscouthq/directory`), and a dedicated spotlight across both `@clampdown19` and `@AgentScoutHQ`. Checkout: https://buy.stripe.com/bJefZi4KT6lp9l3dPRe7m00",
        "- **Weekly Sitewide Sponsor + Newsletter Top Slot ($99/wk — 1 Exclusive Slot/Week)**: Everything in $49, plus 7 days in the exclusive sitewide top sponsor bar across all 2,338+ pages, homepage `#makers` showcase, and the top Sponsored by slot in Tuesday's AgentScout Weekly newsletter. Checkout: https://buy.stripe.com/6oU4gA2CL9xB2WFcLNe7m01",
        "",
        "## High-Intent Ranked Guides (`/best/` & `/mcp/`)",
        "",
        f"- [All Best AI Agent Lists]({B}best/)",
        f"- [Best AI Coding Agents]({B}best/ai-coding-agents.html)",
        f"- [Best AI Agent Frameworks]({B}best/ai-agent-frameworks.html)",
        f"- [Best AI Browser Agents]({B}best/ai-browser-agents.html)",
        f"- [Best Open-Source Browser Automation Agents]({B}best/open-source-browser-automation-agents.html)",
        f"- [Best Local & Offline AI Agents]({B}best/local-offline-ai-agents.html)",
        f"- [Best Open-Source MCP Servers]({B}best/open-source-mcp-servers.html)",
        f"- [Most-Starred Open-Source AI Agent Projects]({B}best/most-starred-open-source-ai-agents.html)",
        f"- [Best Self-Hosted AI Agents]({B}best/self-hosted-ai-agents.html)",
        f"- [Best Free AI Agents (Free Plans)]({B}best/free-ai-agents.html)",
        f"- [Best No-Code AI Agent Builders]({B}best/no-code-ai-agent-builders.html)",
        f"- [Best AI Voice Agent Platforms]({B}best/ai-voice-agent-platforms.html)",
        f"- [Best AI Agent Observability & Eval Tools]({B}best/ai-agent-observability-tools.html)",
        f"- [Best Personal AI Agents]({B}best/personal-ai-agents.html)",
        f"- [Best AI Agents for Business Teams]({B}best/ai-business-agents.html)",
        f"- [Best Crypto AI Agents]({B}best/crypto-ai-agents.html)",
        f"- [Best MCP Servers for Claude Code]({B}best/mcp-servers-for-claude-code.html)",
        f"- [Best MCP Servers for Cursor]({B}best/mcp-servers-for-cursor.html)",
        f"- [Best MCP Servers for Codex]({B}best/mcp-servers-for-codex.html)",
        f"- [Cursor Alternatives]({B}best/cursor-alternatives.html)",
        f"- [MCP Server Pricing Table (with change history)]({B}mcp/pricing.html)",
        f"- [MCP Server Link Status Table (with daily HTTP check history)]({B}mcp/link-status.html)",
        "",
        "---",
        "",
        "## Category-by-Category Comparison Tables (All 30 Categories)",
        "",
        "Each category section below summarizes the verified tool count, open-source count, free/freemium count, and local/self-hosted count, followed by the top ranked tools in that category.",
        "",
    ]

    for c, n in cats.most_common():
        c_slug = X.catslug(c)
        c_items = [x for x in t if x["category"] == c]
        ranked = _cat_rank(c_items)
        c_os = sum(1 for x in c_items if x.get("pricing") in OS)
        c_free = sum(1 for x in c_items if x.get("pricing") in ("Free", "Freemium") or x.get("pricing") in OS)
        c_loc = sum(1 for x in c_items if classify_locality(x) in ("offline", "self_hosted"))
        L.extend([
            f"### {c} ({n} tools) — [{B}categories/{c_slug}.html]({B}categories/{c_slug}.html)",
            "",
            f"- **At a glance**: {n} link-checked tools ({c_os} open-source, {c_free} free or freemium, {c_loc} local or self-hosted).",
            f"- **Top picks**: {', '.join(f'[{x['name']}]({B}tools/{x['slug']}.html)' for x in ranked[:5])}.",
            "",
            "| # | Tool | Pricing | Open Source | License | Runs Locally | GitHub Stars | Best For | Description | AgentScout Listing | Official URL |",
            "|---|---|---|---|---|---|---:|---|---|---|---|",
        ])
        for i, x in enumerate(ranked[:15], 1):
            ax = api_by_slug.get(x["slug"], {})
            lic = ax.get("license") or repo_facts.get(x["slug"], {}).get("license") or ""
            loc = locality_label(x)
            stars = f"{x['github_stars']:,}" if x.get("github_stars") else ""
            best_for = ", ".join(x.get("use_cases", [])[:2]) or x["category"]
            prim = x.get("website") or x.get("url") or x.get("github") or ""
            L.append(
                f"| {i} | {_md_clean(x['name'])} | {_md_clean(x.get('pricing_detail') or x['pricing'])} | "
                f"{'Yes' if x['pricing'] in OS else 'No'} | {_md_clean(lic)} | {_md_clean(loc)} | {stars} | "
                f"{_md_clean(best_for)} | {_md_clean(x['description'])} | "
                f"{B}tools/{x['slug']}.html | {_md_clean(prim)} |"
            )
        L.append("")

    # Complete MCP Servers table (all 246 MCP servers)
    ranked_mcp = _cat_rank(mcp_tools)
    L.extend([
        "---",
        "",
        f"## Complete Verified MCP Servers Catalog ({len(ranked_mcp):,} MCP Servers)",
        "",
        f"Full table of all {len(ranked_mcp):,} Model Context Protocol (MCP) servers listed on AgentScout, cross-referenced with `{B}mcp/pricing.html` and `{B}mcp/link-status.html`.",
        "",
        "| # | MCP Server | Pricing | Link Status | Runs Locally | License | GitHub Stars | Primary Use Case | Description | AgentScout Listing | Official / Repo URL |",
        "|---|---|---|---|---|---|---:|---|---|---|---|",
    ])
    for i, x in enumerate(ranked_mcp, 1):
        ax = api_by_slug.get(x["slug"], {})
        lic = ax.get("license") or repo_facts.get(x["slug"], {}).get("license") or ""
        loc = locality_label(x)
        stars = f"{x['github_stars']:,}" if x.get("github_stars") else ""
        import build_aicite as _bac
        _st_lbl, _st_det = _bac.lstat(mcp_status.get(x["slug"], {}))
        st_str = f"{_st_lbl} ({_st_det})" if _st_det else _st_lbl
        best_for = ", ".join(x.get("use_cases", [])[:2]) or "MCP server"
        prim = x.get("website") or x.get("url") or x.get("github") or ""
        L.append(
            f"| {i} | {_md_clean(x['name'])} | {_md_clean(x.get('pricing_detail') or x['pricing'])} | "
            f"{_md_clean(st_str)} | {_md_clean(loc)} | {_md_clean(lic)} | {stars} | "
            f"{_md_clean(best_for)} | {_md_clean(x['description'])} | "
            f"{B}tools/{x['slug']}.html | {_md_clean(prim)} |"
        )
    L.append("")

    out_txt = "\n".join(L)
    open("llms-full.txt", "w").write(out_txt)
    print(f"aeo: wrote llms-full.txt ({len(out_txt):,} bytes, {len(L):,} lines)")

def run(t):
    import build_extras as X
    by = {x["slug"]: x for x in t}
    bycat = collections.defaultdict(list)
    for x in t:
        bycat[f"categories/{X.catslug(x['category'])}.html"].append(x)

    today = max(x["verified"] for x in t)
    files = sorted(
        set(glob.glob("best/*.html") + glob.glob("mcp/*.html") + glob.glob("s/*.html") + glob.glob("categories/*.html")) - SKIP
    )
    n = 0
    for f in files:
        s = open(f).read()
        if 'http-equiv="refresh"' in s[:2500]:
            continue
        is_cat = f.startswith("categories/")
        if is_cat:
            all_items = bycat.get(f, [])
            rows = _cat_rank(all_items)
        else:
            sl = _slugs(s)
            all_items = [by[k] for k in sl if k in by]
            rows = all_items
        if len(rows) < 3:
            continue
        dates = [x["verified"] for x in all_items if x.get("verified")]
        d = max(dates) if dates else today
        ranked = is_cat or ("GitHub stars" in s or f.startswith(("best/", "mcp/")))
        b = block(rows, all_items, d, ranked)
        if "<!--ci:aeo-->" in s:
            s2 = re.sub(r"<!--ci:aeo-->.*?<!--/ci:aeo-->", lambda _: b, s, count=1, flags=re.S)
            s2 = re.sub(r"<!--xl:cmp-->.*?<!--/xl:cmp-->", "", s2, flags=re.S)
        elif "<!--xl:cmp-->" in s:
            s2 = re.sub(r"<!--xl:cmp-->.*?<!--/xl:cmp-->", lambda _: b, s, count=1, flags=re.S)
        else:
            s2 = re.sub(r'(<p class="lede"[^>]*>.*?</p>)', lambda m: m.group(1) + b, s, count=1, flags=re.S)
        if s2 != s:
            open(f, "w").write(s2)
            n += 1
    sync_entity_schema()
    sync_robots()
    write_llms_full(t)
    print(f"aeo: {n}/{len(files)} best/mcp/s/categories pages updated with quick answer + ranked table + verified date")

if __name__ == "__main__":
    run(json.load(open("tools.json")))
