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

ALT_NAMES = ["Agent Scout", "AgentScoutHQ", "agentscouthq.com", "com.agentscouthq/directory"]
SAME_AS = [
    "https://x.com/clampdown19",
    "https://x.com/AgentScoutHQ",
    "https://agentscout.beehiiv.com/",
    "https://github.com/clampdown19/agentscout",
    "https://github.com/Clampdown-web/agentscout",
    "https://registry.modelcontextprotocol.io/v0/servers?search=com.agentscouthq/directory",
    "https://glama.ai/mcp/connectors/com.agentscouthq/directory",
    "https://mcpservers.org/servers/agentscouthq-com-mcp-connect-html",
    "https://sourceweft.com/mcp/com.agentscouthq%2Fdirectory",
    "https://protogrid.dev/servers/com.agentscouthq/directory",
    "https://mcpcollection.com/server/agentscout-mcp",
    # Competitor and rival-directory URLs must never be added to sameAs.
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

def _words(text):
    return len(re.findall(r"\S+", text))

def _join_names(names):
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + " and " + names[-1]

def _fit_answer(lead, bits):
    """Keep a Quick answer between 40 and 60 words. Drop optional sentences before the lead."""
    required = [lead, bits["sources"], bits["paid"]]
    optional = [bits["lead_n"], bits["price"], bits["read"]]
    text = " ".join(required[:1] + optional + required[1:])
    while _words(text) > 60 and optional:
        optional.pop()
        text = " ".join([lead] + optional + required[1:])
    if _words(text) > 60:
        text = " ".join(required)
    if _words(text) < 40:
        for extra in (bits["read"], bits["price"], bits["lead_n"]):
            if extra not in text:
                text = text + " " + extra
            if _words(text) >= 40:
                break
    return " ".join(text.split())

def catalog_check_date():
    """Directory link-check date from api/tools.json. Empty when that file has no date."""
    try:
        data = json.load(open("api/tools.json"))
    except Exception:
        return ""
    if isinstance(data, dict):
        day = str(data.get("last_checked") or "")[:10]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            return day
    return ""

def mcp_best_answer(by):
    """Install-first answer for the Best MCP servers page. Names and the live check come from catalog data.
    Playwright MCP is listed, but it is not in the MCP link-status file, so this sentence does not call it live."""
    need = ("context7", "github-mcp-server", "playwright-mcp")
    if any(s not in by for s in need):
        return ""
    import build_aicite as bac
    try:
        checked = json.load(open("data/mcp_link_status.json"))
    except Exception:
        checked = {}
    results = checked.get("results") or {}
    when = str(checked.get("checked") or "")
    day = when[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        day = catalog_check_date()
    live = []
    for slug in ("context7", "github-mcp-server"):
        label, _detail = bac.lstat(results.get(slug) or {})
        if label == "OK":
            live.append(by[slug]["name"])
    opener = (
        f"Install {by['context7']['name']}, {by['github-mcp-server']['name']} and {by['playwright-mcp']['name']} first, "
        "then add one server for your main system (database, design, tickets). Keep 3–6 active."
    )
    if live and day:
        checked_bit = f"{_join_names(live)} were link-checked live on {_fmt(day)}."
    elif day:
        checked_bit = f"Sources checked {_fmt(day)}."
    else:
        checked_bit = "Link status: not yet checked."
    text = f"{opener} AgentScout lists all three. {checked_bit} No vendor paid for a position."
    text = " ".join(text.split())
    if not 40 <= _words(text) <= 60:
        text = f"{opener} AgentScout lists all three. {checked_bit} No vendor paid for a position. Read each listing before you connect a server."
        text = " ".join(text.split())
    return text

def best_block(path, rows, all_items, date, ranked_by_stars, by):
    """Quick answer, dated ranked table, How we rank, and Updated / sources checked for /best/ pages."""
    if not date or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(date)[:10]):
        date = ""
        pretty = "not yet checked"
        dt = ""
    else:
        date = str(date)[:10]
        months = ("", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
        y, m, d = date.split("-")
        pretty = f"{months[int(m)]} {int(d)}, {y}"
        dt = date
    how = "GitHub stars on each listing" if ranked_by_stars else "listing maturity, then GitHub stars"
    names = [x["name"] for x in rows[:3]]
    if path == "s/best-mcp-servers.html":
        plain = mcp_best_answer(by)
    else:
        plain = ""
    if not plain:
        if not names:
            plain = ""
        else:
            if len(names) == 1:
                lead = f"The top pick on this list is {names[0]}."
            else:
                lead = f"The top picks on this list are {_join_names(names)}."
            n = len(all_items) or len(rows)
            src = f"Sources checked {pretty}." if dt else "Sources checked: not yet checked."
            plain = _fit_answer(lead, {
                "lead_n": f"They lead {n:,} matching tools, ranked by {how}.",
                "price": "Pricing is what each maker states.",
                "read": "Read each listing before you choose.",
                "sources": src,
                "paid": "No vendor paid for a position.",
            })
    if plain and not 40 <= _words(plain) <= 60:
        print(f"aeo: quick answer word count {_words(plain)} on {path}")
    linked = plain
    for x in sorted(rows, key=lambda z: len(z["name"]), reverse=True):
        if x["name"] and x["name"] in linked:
            linked = linked.replace(x["name"], f'<a href="../tools/{x["slug"]}.html">{e(x["name"])}</a>', 1)
    # Names in the MCP install line may sit outside this page's ranked rows (Playwright MCP is another category).
    for slug in ("context7", "github-mcp-server", "playwright-mcp"):
        tool = by.get(slug)
        if tool and tool["name"] in linked and f'tools/{slug}.html' not in linked:
            linked = linked.replace(tool["name"], f'<a href="../tools/{slug}.html">{e(tool["name"])}</a>', 1)
    qa = f'<p class="qa"><b>Quick answer:</b> {linked}</p>' if plain else ""
    time = f'<time datetime="{dt}">{e(pretty)}</time>' if dt else e(pretty)
    trs = "".join(
        f'<tr><td>{i}</td><th scope="row"><a href="../tools/{x["slug"]}.html">{e(x["name"])}</a></th>'
        f'<td>{e(x["pricing"])}</td><td>{e(", ".join(x.get("use_cases", [])[:2]) or x["category"])}</td>'
        f'<td>{"Yes" if x["pricing"] in OS else "No"}</td>'
        f'<td>{e(locality_label(x))}</td>'
        f'<td>{x["github_stars"]:,}</td></tr>' if x.get("github_stars") else
        f'<tr><td>{i}</td><th scope="row"><a href="../tools/{x["slug"]}.html">{e(x["name"])}</a></th>'
        f'<td>{e(x["pricing"])}</td><td>{e(", ".join(x.get("use_cases", [])[:2]) or x["category"])}</td>'
        f'<td>{"Yes" if x["pricing"] in OS else "No"}</td>'
        f'<td>{e(locality_label(x))}</td><td></td></tr>'
        for i, x in enumerate(rows[:10], 1)
    )
    tbl = (
        f'<h2 style="font-size:17px;margin:14px 0 8px">Ranked comparison (top {min(10, len(rows))})</h2>'
        f'<p class="muted" style="font-size:13px;margin:0 0 8px">Dated {time}.</p>'
        f'<div class="cmpwrap"><div class="cmpscroll"><table class="cmptbl"><caption class="muted" style="caption-side:bottom;text-align:left;padding:8px 10px;font-size:12.5px">Ranked {time}</caption><thead><tr>'
        f'<th scope="col">#</th><th scope="col">Tool</th><th scope="col">Pricing</th>'
        f'<th scope="col">Best for</th><th scope="col">Open source</th><th scope="col">Runs locally</th><th scope="col">GitHub stars</th>'
        f'</tr></thead><tbody>{trs}</tbody></table></div></div>'
    ) if rows else ""
    rank = (
        f'<p class="muted" style="margin:0 0 8px"><strong>How we rank:</strong> {e(how)}. '
        "Stars and maturity come from each AgentScout listing. No vendor paid for a position.</p>"
    )
    updated = f'<p class="srcchecked" style="margin:0 0 14px">Updated / sources checked {time}.</p>'
    return f"<!--ci:aeo-->{qa}{tbl}{rank}{updated}<!--/ci:aeo-->", plain

def _place_best_block(s, block):
    s = re.sub(r"<!--ci:aeo-->.*?<!--/ci:aeo-->", "", s, count=1, flags=re.S)
    s = re.sub(r"<!--xl:cmp-->.*?<!--/xl:cmp-->", "", s, flags=re.S)
    m = re.search(r"<h1\b[^>]*>.*?</h1>(\s*<div class=\"shareacts\">.*?</div>)?", s, flags=re.S)
    if not m:
        return s
    return s[:m.end()] + block + s[m.end():]

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
        if isinstance(api_data, list):
            last_checked, api_tools = "", api_data
        elif isinstance(api_data, dict):
            last_checked, api_tools = api_data.get("last_checked", ""), api_data.get("tools", [])
        else:
            last_checked, api_tools = "", []
        api_by_slug = {x["slug"]: x for x in api_tools}
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

    # Count bot templates & skills from the built /bot-templates/ rows (not a frozen total).
    import build_bot_templates
    n_bt = build_bot_templates.live_bot_template_count()

    L = [
        "# AgentScout — Full AI Agent & MCP Server Directory Reference (`llms-full.txt`)",
        "",
        f"> AgentScout is a curated, link-checked, read-only directory of {len(t):,} AI agent tools across {len(cats)} categories, including {len(mcp_tools):,} Model Context Protocol (MCP) servers and {n_bt:,} bot templates & skills. Every listing is checked daily; pricing is stated as each maker publishes it; rankings use verifiable public signals (GitHub stars, visitor ratings, and listing maturity). Featured slots are clearly labeled and sit above the list; rankings are never paid.",
        "",
        "Entity note: AgentScout (also searched as Agent Scout or AgentScoutHQ) is the independent AI agent and MCP server directory at https://agentscouthq.com, published in the official MCP Registry as `com.agentscouthq/directory` with endpoint `https://mcp.agentscouthq.com/mcp` (and `https://agentscouthq.com/mcp/sse`). AgentScout's official MCP server (`com.agentscouthq/directory` at `https://agentscouthq.com/mcp/sse`) is 100% free, public, and read-only, with no API key, crypto wallet, or x402 payment required. It is completely unrelated to the paid third-party x402 web-fetch package that shares a similar name.",
        "",
        "## Official Identity, Endpoints & Registry Links",
        "",
        f"- **Canonical Website**: {B}",
        "- **Alternate Names**: Agent Scout, AgentScoutHQ, agentscouthq.com",
        "- **Official MCP Registry Identifier**: `com.agentscouthq/directory`",
        "- **Remote MCP Server Endpoint (Streamable HTTP & SSE, 100% free, read-only, no API key or x402 wallet required)**: `https://mcp.agentscouthq.com/mcp` (and `https://agentscouthq.com/mcp/sse`)",
        f"- **MCP Connection & Client Setup Guide**: {B}mcp/connect.html",
        f"- **How-To Video Guides & Pro Tips Hub (`/videos/`)**: {B}videos/ (8 playable 60fps walkthroughs with copyable MCP & CLI snippets)",
        f"- **Made by AgentScout Pro Bots & 4-Bot Bundle (`/bot-store/` and `/bot-templates/#made-by-agentscout`)**: {B}bot-store/ and {B}bot-templates/#made-by-agentscout — $39 Operations / Monitoring Bot, $59 SEO & AEO Growth Auditor Bot, $59 Market & Launch Intel Bot, $69 CEO Coordinator Bot, $149 Full 4-Bot \"Company-in-a-Box\" Team Bundle",
        f"- **Concise LLM Guide (`llms.txt`)**: {B}llms.txt",
        f"- **Full Single-File LLM Reference (`llms-full.txt`)**: {B}llms-full.txt",
        f"- **Full JSON Catalog (`api/tools.json`)**: {B}api/tools.json",
        f"- **Stripe Agentic Commerce Product Feed (`api/products.json` & `.well-known/acp.json`)**: {B}api/products.json (and `{B}.well-known/acp.json`)",
        f"- **AI Plugin Manifest (`.well-known/ai-plugin.json`)**: {B}.well-known/ai-plugin.json",
        f"- **OpenAPI 3.1 Specification (JSON & YAML)**: {B}openapi.json, {B}openapi.yaml (and `{B}.well-known/openapi.json`, `{B}.well-known/openapi.yaml`)",
        f"- **Web App Brand Manifest (`manifest.json`)**: {B}manifest.json",
        f"- **A2A / Agent Card**: {B}.well-known/agent-card.json (and `{B}.well-known/agent.json`)",
        f"- **MCP Server Card**: {B}.well-known/mcp.json",
        "- **Official Profiles & Third-Party MCP Registry Listings**:",
        "  - X (Twitter): https://x.com/AgentScoutHQ, https://x.com/clampdown19",
        "  - GitHub (Public Repository & Issues): https://github.com/clampdown19/agentscout (and https://github.com/Clampdown-web/agentscout)",
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
        "- **Fast-Track + 7-Day Launch Boost ($29 one-time)**: Same-day priority review (live in the next batch), 7-day featured pin on `/new.html` + category New & Featured row, full FAQ Page + pros/cons profile enrichment, and a launch post on `@AgentScoutHQ`. Checkout: https://buy.stripe.com/fZufZi7X5cJNbtbdPRe7m02",
        "- **30-Day Category Pin + Permanent SEO/AEO Placement ($49 one-time — Most Popular)**: Everything in $29 upgraded to a full 30-day top category pin (4x+ longer for $20 more), permanent inclusion in `/best/*-alternatives` and `/compare/` comparison tables, priority recommendation weight in `llms-full.txt` and MCP search (`com.agentscouthq/directory`), and a dedicated spotlight across both `@clampdown19` and `@AgentScoutHQ`. Checkout: https://buy.stripe.com/bJefZi4KT6lp9l3dPRe7m00",
        f"- **Weekly Sitewide Sponsor + Newsletter Top Slot ($99/wk — 1 Exclusive Slot/Week)**: Everything in $49, plus 7 days in the exclusive sitewide top sponsor bar across all {open('sitemap.xml').read().count('<loc>'):,}+ pages, homepage `#makers` showcase, and the top Sponsored by slot in Tuesday's AgentScout Weekly newsletter. Checkout: https://buy.stripe.com/6oU4gA2CL9xB2WFcLNe7m01",
        "",
        "## Made by AgentScout — Pre-Trained Pro Bots & 4-Bot Company-in-a-Box Bundle (`/bot-store/`)",
        "",
        f"- **Bot Store**: {B}bot-store/",
        f"- **Bot templates**: {B}bot-templates/#made-by-agentscout",
        "- **Host Compatibility**: Built natively for Grok Bot and compatible with Claude Code (`CLAUDE.md`), Cursor (`.cursorrules`), OpenAI Codex (`AGENTS.md`), and Lovable (`LOVABLE.md`).",
        "- **Flagship Pro Bot Packages**: $39 Operations / Monitoring Bot, $59 SEO & AEO Growth Auditor Bot, $59 Market & Launch Intel Bot, $69 CEO Coordinator Bot, $149 Full 4-Bot \"Company-in-a-Box\" Team Bundle",
        f"- **1. AgentScout Operations / Monitoring Bot ($39 one-time, sold separately — Neon Lime)**: Pre-trained 24/7 Operations & Monitoring bot with 4-hour inbox triage, 42-point site & checkout deep audits (`daily_deep_audit.py`), and X velocity tracking. Store: {B}bot-store/ · Checkout: https://buy.stripe.com/cNidRa0uDdNRgNvaDFe7m03",
        f"- **2. AgentScout SEO & AEO Growth Auditor Bot ($59 one-time, sold separately — Neon Gold)**: Pre-trained technical SEO and AI-Answer Engine Optimization (AEO) auditor bot tracking Search Console, JSON-LD entity graphs, `llms.txt`, and ChatGPT/Perplexity/Claude citations. Store: {B}bot-store/ · Checkout: https://buy.stripe.com/14A7sMfpx6lp9l3aDFe7m05",
        f"- **3. AgentScout Market & Launch Intel Bot ($59 one-time, sold separately — Neon Sunset Orange)**: Pre-trained competitive intelligence bot monitoring rival launches, pricing shifts, 20-account X outlier hooks (`HOOKS.md`), and Product Hunt/HN traction. Store: {B}bot-store/ · Checkout: https://buy.stripe.com/4gM8wQelt11568RaDFe7m06",
        f"- **4. AgentScout CEO Coordinator Bot ($69 one-time, sold separately — Neon Crimson Red)**: Pre-trained lead builder & multi-agent coordinator bot with subagent dispatch architecture, daily 7:00 AM build pipeline, and X/newsletter growth engine. Store: {B}bot-store/ · Checkout: https://buy.stripe.com/9B69AU2CLh031SB8vxe7m07",
        f"- **Full 4-Bot \"Company-in-a-Box\" Team Bundle ($149 one-time — Save $77 vs. $226 separately — Neon Mint-Emerald)**: All 4 downloadable bots together with shared `/workspace/handoff/` multi-agent protocol and 15+ cron routines. Store: {B}bot-store/ · Checkout: https://buy.stripe.com/fZueVe5OX7pt1SB6npe7m08 (or X Money `@clampdown19`)",
        "",
        "## 25 Pre-Trained AI Agent Packs (`/bot-store/#ai-agent-packs` — Works with Grok Bot, Claude Code, Cursor, Codex & Lovable)",
        "",
        "- **5-Tier Volume Pricing Ladder (Stripe Checkout & X Money `@clampdown19`)**:",
        "  - **1-Bot AI Agent Pack ($35 one-time · $35.00/bot)**: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        "  - **5-Bot AI Agent Pack ($119 one-time · $23.80/bot · Save $56)**: https://buy.stripe.com/9B600kfpx4dhbtb8vxe7m0a",
        "  - **10-Bot AI Agent Pack ($199 one-time · $19.90/bot · Save $151)**: https://buy.stripe.com/6oU8wQ4KT4dh0OxeTVe7m0b",
        "  - **20-Bot AI Agent Pack ($299 one-time · $14.95/bot · Save $401)**: https://buy.stripe.com/5kQ28s1yH5hl8gZ8vxe7m0c",
        "  - **All 25 AI Agent Packs Mega Pack ($349 one-time · $13.96/bot · Save $526)**: https://buy.stripe.com/28E9AUdhpfVZ0OxbHJe7m0d",
        f"- **AgentScout Accountant Agent ($35 one-time · Operations & Admin)**: Automated bookkeeping, ledger reconciliation & tax-ready financials. Includes `skills/bookkeeping-tax-prep/SKILL.md`, `scripts/reconcile_ledger.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/accountant/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Graphic Designer Agent ($35 one-time · Marketing & Content)**: High-converting ad creatives, social graphics & YouTube thumbnails. Includes `skills/brand-card-system/SKILL.md`, `scripts/generate_brand_card_spec.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/graphic-designer/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Lead Gen Agent ($35 one-time · Sales & Outreach)**: Daily B2B prospect discovery, ICP scoring & verified lead lists. Includes `skills/icp-lead-scoring/SKILL.md`, `scripts/score_leads_pipeline.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/lead-gen/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Copywriter Agent ($35 one-time · Marketing & Content)**: Conversion-focused landing pages, sales emails & social hooks. Includes `skills/conversion-copy-audit/SKILL.md`, `scripts/audit_sales_copy.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/copywriter/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Video Editor Agent ($35 one-time · Operations & Admin)**: Short-form retention hooks, cut lists, captions & FFmpeg workflows. Includes `skills/shortform-cut-captions/SKILL.md`, `scripts/format_captions_and_cuts.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/video-editor/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Outreach Agent ($35 one-time · Sales & Outreach)**: Personalized cold emails, warm follow-ups & reply triage. Includes `skills/cold-email-sequence/SKILL.md`, `scripts/lint_outreach_sequence.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/outreach-agent/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Google Review Replier Agent ($35 one-time · Operations & Admin)**: Fast, on-brand replies to every 5-star and critical local review. Includes `skills/review-reply-desk/SKILL.md`, `scripts/generate_review_replies.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/google-review-replier/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout SEO Specialist Agent ($35 one-time · Marketing & Content)**: Technical SEO audits, JSON-LD schema & AI-search visibility. Includes `skills/seo-aeo-site-audit/SKILL.md`, `scripts/seo_site_audit.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/seo-specialist/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Email Marketer Agent ($35 one-time · Marketing & Content)**: High-open newsletters, onboarding flows & win-back campaigns. Includes `skills/newsletter-issue-score/SKILL.md`, `scripts/score_newsletter_issue.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/email-marketer/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Customer Support Agent ($35 one-time · Operations & Admin)**: 24/7 inbox triage, instant FAQ answers & refund/escalation routing. Includes `skills/support-ticket-triage/SKILL.md`, `scripts/triage_support_tickets.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/customer-support/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Appointment Setter Agent ($35 one-time · Sales & Outreach)**: Qualifies inbound leads, proposes times & books discovery calls. Includes `skills/call-briefing-slots/SKILL.md`, `scripts/build_call_briefing.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/appointment-setter/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Personal Assistant Agent ($35 one-time · Operations & Admin)**: Morning inbox digest, daily priorities & meeting prep briefs. Includes `skills/daily-exec-briefing/SKILL.md`, `scripts/daily_exec_briefing.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/personal-assistant/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Data Analyst Agent ($35 one-time · Product & Data)**: Weekly KPI reports, cohort retention & revenue anomaly alerts. Includes `skills/kpi-csv-analyst/SKILL.md`, `scripts/analyze_kpi_csv.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/data-analyst/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Social Media Manager Agent ($35 one-time · Marketing & Content)**: Daily X, LinkedIn & Instagram posts with outlier hook tracking. Includes `skills/social-hook-desk/SKILL.md`, `scripts/score_social_hooks.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/social-media-manager/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Recruiter Agent ($35 one-time · Sales & Outreach)**: Candidate sourcing, resume scorecarding & structured interview kits. Includes `skills/candidate-rubric/SKILL.md`, `scripts/score_candidate_rubric.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/recruiter/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Web Designer Agent ($35 one-time · Product & Data)**: Responsive landing pages, mobile UX audits & dark/light CSS polish. Includes `skills/landing-page-ux-check/SKILL.md`, `scripts/check_landing_page_ux.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/web-designer/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Meta Ads Agent ($35 one-time · Sales & Outreach)**: ROAS monitoring, creative fatigue alerts & ad-angle variations. Includes `skills/ad-roas-rules/SKILL.md`, `scripts/evaluate_ad_roas.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/meta-ads-agent/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Market Researcher Agent ($35 one-time · Product & Data)**: Competitor pricing watch, launch tracking & side-by-side battlecards. Includes `skills/competitor-diff/SKILL.md`, `scripts/competitor_diff_check.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/market-researcher/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Content Strategist Agent ($35 one-time · Marketing & Content)**: 30-day editorial calendars, topic clusters & multi-channel repurposing. Includes `skills/thirty-day-calendar/SKILL.md`, `scripts/generate_30day_calendar.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/content-strategist/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout TikTok Shop Manager Agent ($35 one-time · Marketing & Content)**: Product listing optimization, creator affiliate briefs & stock alerts. Includes `skills/shop-listing-optimizer/SKILL.md`, `scripts/optimize_shop_listing.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/tiktok-shop-manager/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Influencer Scout Agent ($35 one-time · Sales & Outreach)**: Creator discovery, engagement-rate vetting & sponsorship ROI tracking. Includes `skills/creator-roi/SKILL.md`, `scripts/calculate_creator_roi.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/influencer-scout/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Invoice Chaser Agent ($35 one-time · Sales & Outreach)**: Polite, automated overdue invoice reminders & AR aging reports. Includes `skills/ar-aging/SKILL.md`, `scripts/aging_ar_report.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/invoice-chaser/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Product Builder Agent ($35 one-time · Product & Data)**: PRDs, user stories, release checklists & feedback prioritization. Includes `skills/pricing-and-mvp-scope/SKILL.md`, `scripts/model_product_pricing.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/product-builder/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Community Manager Agent ($35 one-time · Operations & Admin)**: Discord, Slack & forum engagement, member onboarding & FAQ digests. Includes `skills/community-health/SKILL.md`, `scripts/community_health_score.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/community-manager/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        f"- **AgentScout Translator Agent ($35 one-time · Marketing & Content)**: Context-aware localization for UI strings, docs & marketing copy. Includes `skills/i18n-key-parity/SKILL.md`, `scripts/verify_i18n_keys.py`, 3 scheduled cron routines, and multi-host configs (`SYSTEM.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `LOVABLE.md`). Details: {B}bot-store/translator/ · Checkout: https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
        "",
        "## High-Intent Ranked Guides (`/best/`, `/mcp/` & `/videos/`)",
        "",

        "",
        f"- [How-To Video Guides & Builder Pro Tips Hub (8 60fps Walkthroughs)]({B}videos/)",
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
        f"- [Link-check status (JSON)]({B}status.json): last-checked time, live or down status, and check history for every MCP server",
        "",
        "---",
        "",
        "## Category-by-Category Comparison Tables (All 40 Categories)",
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
    catalog_day = catalog_check_date()
    files = sorted(
        set(glob.glob("best/*.html") + glob.glob("mcp/*.html") + glob.glob("s/*.html") + glob.glob("categories/*.html")) - SKIP
    )
    n = 0
    answers = []
    for f in files:
        s = open(f).read()
        if 'http-equiv="refresh"' in s[:2500]:
            continue
        is_best = f.startswith("best/") or f == "s/best-mcp-servers.html"
        if not is_best and os.environ.get("BEST_ONLY"):
            continue
        is_cat = f.startswith("categories/")
        if is_cat:
            all_items = bycat.get(f, [])
            rows = _cat_rank(all_items)
        else:
            sl = _slugs(s)
            all_items = [by[k] for k in sl if k in by]
            rows = all_items
        if len(rows) < (1 if is_best else 3):
            continue
        dates = [x["verified"] for x in all_items if x.get("verified")]
        d = max(dates) if dates else today
        if is_best:
            d = catalog_day or d
        ranked = is_cat or ("GitHub stars" in s or f.startswith(("best/", "mcp/", "s/")))
        if f.startswith("best/") and "rank by the maturity stated on each listing" in s:
            ranked = False  # maturity-ranked best pages (build_best "maturity"): say so in the Quick answer (Oct 29 2026)
        if is_best:
            b, plain = best_block(f, rows, all_items, d, ranked, by)
            if plain:
                answers.append((f, plain))
            s2 = _place_best_block(s, b)
        else:
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
    if answers:
        open("data/best-quick-answers.json", "w").write(json.dumps([{"page": p, "quick_answer": t} for p, t in answers], indent=1, ensure_ascii=False) + "\n")
    sync_entity_schema()
    sync_robots()
    write_llms_full(t)
    print(f"aeo: {n}/{len(files)} best/mcp/s/categories pages updated with quick answer + ranked table + verified date")

if __name__ == "__main__":
    run(json.load(open("tools.json")))
