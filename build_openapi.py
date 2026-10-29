"""openapi.json & openapi.yaml (OpenAPI 3.1) + Stripe Agentic Commerce discovery files (Oct 27 2026, owner-approved).
Schemas are inferred from the real files on every build, so fields and counts stay current.
Writes:
- /api/products.json and /.well-known/acp.json (Stripe Agentic Commerce product & package feed)
- /.well-known/ai-plugin.json (AI plugin manifest with prompt-engineered description_for_model)
- /manifest.json and /site.webmanifest (Web app brand manifest with #0B0F19 / #0EA5E9 & icons)
- /openapi.json and /.well-known/openapi.json (OpenAPI 3.1 JSON)
- /openapi.yaml and /.well-known/openapi.yaml (OpenAPI 3.1 YAML)"""
import json, os, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))

B = "https://agentscouthq.com"
MCP_HTTP = "https://mcp.agentscouthq.com/mcp"
MCP_SSE = "https://agentscouthq.com/mcp/sse"

EP = [
    ("tools.json", "getTools", "Full AI agent & MCP server catalog",
     "Use this endpoint when a user asks to search, filter, compare, or verify AI agent tools, coding agents, browser agents, voice agents, or Model Context Protocol (MCP) servers. Returns every listed tool with category, maker-stated pricing, price_tag (free/freemium/paid), platforms, open_source boolean, license, GitHub repo and stars, daily link-check date, and canonical AgentScout page URL.",
     ["catalog"]),
    ("products.json", "getProducts", "Purchasable Stripe packages & Made by AgentScout bot catalog (ACP feed)",
     "Use this endpoint when a maker or purchasing agent wants to submit an AI tool, buy a featured listing boost or sponsorship on AgentScout, or purchase Made by AgentScout pre-trained bots. Returns structured product and offer metadata with pricing in USD, availability, deliverables, and direct Stripe Checkout URLs.",
     ["commerce", "catalog"]),
    ("stats.json", "getStats", "Lightweight catalog stats & category counts",
     "Compact summary with category, added date, and seed flag for every tool, plus the daily last_checked date.",
     ["catalog"]),
    ("sections.json", "getSections", "Site sections, categories, comparisons, guides & news",
     "Categories with tool counts, task pages, side-by-side comparisons, best-of ranked lists, daily AI agent news, free calculators, badges, submit form fields, and newsletter metadata.",
     ["site"]),
    ("editors-pick.json", "getEditorsPick", "Editor's Pick of the day",
     "Today's featured Editor's Pick tool and recent daily pick history.",
     ["site"]),
    ("quiz.json", "getQuiz", "Interactive tool-finder quiz specification",
     "Questions, options, and scoring weights used by the AgentScout tool-finder quiz.",
     ["site"]),
    ("generator-daily.json", "getGeneratorDaily", "Daily generator background & palette",
     "Today's image-generator background asset and its overlay colors.",
     ["site"]),
]

ENUM = {
    ("tools", "price_tag"): ["free", "freemium", "paid", "unknown"],
    ("tools", "skill"): ["developer", "no-code"],
}


def T(v):
    return {bool: "boolean", int: "integer", float: "number", str: "string", type(None): "null", list: "array", dict: "object"}[type(v)]


def infer(vals, path=()):
    types = {T(v) for v in vals}
    if "integer" in types and "number" in types:
        types.discard("integer")
    s = {}
    objs = [v for v in vals if isinstance(v, dict)]
    arrs = [v for v in vals if isinstance(v, list)]
    if objs:
        keys = []
        [keys.append(k) for o in objs for k in o if k not in keys]
        s["properties"] = {k: infer([o[k] for o in objs if k in o], path + (k,)) for k in keys}
        req = [k for k in keys if all(k in o for o in objs)]
        if req:
            s["required"] = req
    if arrs:
        items = [i for a in arrs for i in a]
        s["items"] = infer(items, path) if items else {}
    t = sorted(types)
    s = {"type": t[0] if len(t) == 1 else t, **s}
    if path[-2:] in ENUM:
        s["enum"] = ENUM[path[-2:]]
    return s


def _yaml_key(k):
    s = str(k)
    if re.match(r"^[A-Za-z_][A-Za-z0-9_.-]*$", s) and s.lower() not in ("true", "false", "null", "yes", "no", "on", "off"):
        return s
    return json.dumps(s, ensure_ascii=False)


def _to_yaml(v, indent=0):
    sp = "  " * indent
    if isinstance(v, dict):
        if not v:
            return "{}"
        lines = []
        for k, val in v.items():
            yk = _yaml_key(k)
            if isinstance(val, dict) and val:
                lines.append(f"{sp}{yk}:")
                lines.append(_to_yaml(val, indent + 1))
            elif isinstance(val, list) and val:
                lines.append(f"{sp}{yk}:")
                lines.append(_to_yaml(val, indent + 1))
            else:
                lines.append(f"{sp}{yk}: {_to_yaml(val, 0)}")
        return "\n".join(lines)
    if isinstance(v, list):
        if not v:
            return "[]"
        lines = []
        for item in v:
            if isinstance(item, (dict, list)) and item:
                sub = _to_yaml(item, indent + 1)
                first, *rest = sub.split("\n")
                lines.append(f"{sp}- {first.lstrip()}")
                lines.extend(rest)
            else:
                lines.append(f"{sp}- {_to_yaml(item, 0)}")
        return "\n".join(lines)
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return json.dumps(str(v), ensure_ascii=False)


def _load_pack_catalog():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
    from agent_pack_catalog import PACK_TIERS, public_cards
    return PACK_TIERS, public_cards


def _agent_packs(base):
    """25 role packs at $35, plus the 5/10/20/25 volume tiers. Flagship bots stay separate."""
    PACK_TIERS, public_cards = _load_pack_catalog()
    packs = []
    for card in public_cards():
        packs.append({
            "id": "agent-pack-" + card["slug"],
            "sku": "AS-PACK-" + card["slug"].upper().replace("-", ""),
            "name": card["productName"],
            "tagline": card["tagline"],
            "category": "business_agent_pack",
            "department": card["deptLabel"],
            "price_usd": card["price"],
            "billing_model": "one_time",
            "availability": "in_stock",
            "compatibility": "Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, Lovable",
            "page_url": base + "/bot-store/" + card["slug"] + "/",
            "checkout_url": card["checkoutUrl"] or PACK_TIERS["tier_1"]["url"],
            "stripe_payment_link_id": PACK_TIERS["tier_1"]["plink"],
            "checkout_label": card["checkoutLabel"],
            "skill": "skills/" + card["skill"] + "/SKILL.md",
            "script": "scripts/" + card["script"],
            "routines": [r["id"] for r in card["routines"]],
            "description": card["promise"] + " $35 one-time. Volume tiers: 5 for $119, 10 for $199, 20 for $299, all 25 for $349. Separate from the flagship $39/$59/$69 bots and the $149 bundle.",
            "zip": base + "/bot-packages/25-agent-packs/zips/" + card["slug"] + ".zip",
        })
    for key, tier in PACK_TIERS.items():
        if tier["count"] == 1:
            continue
        packs.append({
            "id": "agent-pack-" + key.replace("_", "-"),
            "sku": "AS-PACK-" + key.upper(),
            "name": tier["label"],
            "category": "business_agent_pack_volume",
            "price_usd": tier["price"],
            "regular_price_usd": tier["regular"],
            "savings_usd": tier["save"],
            "bot_count": tier["count"],
            "per_bot_usd": round(tier["price"] / tier["count"], 2),
            "billing_model": "one_time",
            "availability": "in_stock",
            "page_url": base + "/bot-store/#ap-dock",
            "checkout_url": tier["url"],
            "stripe_payment_link_id": tier["plink"],
            "checkout_label": tier["label"],
            "description": f"{tier['label']}. Regular ${tier['regular']}. ${round(tier['price'] / tier['count'], 2)} per bot.",
        })
    return packs


def catalog_tools(data):
    """api/tools.json is either {"tools":[...], ...} or a bare list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("tools", [])
    return []


def sync_products_snapshot(src="api/products.json"):
    """Copy api/products.json onto the MCP list_packages snapshot so page counts cannot drift."""
    if not os.path.isfile(src):
        return []
    data = open(src, encoding="utf-8").read()
    dests = [
        "mcp-server/src/products_snapshot.json",
        "cloudflare-mcp-worker/products_snapshot.json",
    ]
    extras = []
    worker = os.environ.get("AGENTSCOUT_MCP_WORKER")
    if worker:
        extras.append(os.path.join(worker, "src", "products_snapshot.json"))
        extras.append(os.path.join(worker, "products_snapshot.json"))
    extras.append("/workspace/agentscout-mcp-worker/src/products_snapshot.json")
    for extra in extras:
        if os.path.isdir(os.path.dirname(extra)):
            dests.append(extra)
    wrote = []
    for dest in dests:
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        if os.path.isfile(dest) and open(dest, encoding="utf-8").read() == data:
            continue
        open(dest, "w", encoding="utf-8").write(data)
        wrote.append(dest)
    return wrote


def sync_catalog_snapshot(src="api/tools.json", dest="cloudflare-mcp-worker/catalog_snapshot.json"):
    """Write the MCP worker catalog from api/tools.json (counts must match the live directory)."""
    import build_aeo
    if not os.path.isfile(src):
        return None
    data = json.load(open(src, encoding="utf-8"))
    tools = catalog_tools(data)
    cats = sorted({(t.get("category") or "") for t in tools if t.get("category")})
    mcp = sum(1 for t in tools if t.get("category") == "MCP servers")
    if len(tools) != 2051 or len(cats) != 40 or mcp != 272:
        raise SystemExit(f"catalog snapshot out of sync: tools={len(tools)} categories={len(cats)} mcp={mcp}")
    slim = []
    for t in tools:
        loc = build_aeo.classify_locality(t)
        gh = t.get("github") or None
        lic = t.get("license") or None
        slim.append({
            "name": t.get("name"),
            "slug": t.get("slug"),
            "category": t.get("category"),
            "description": t.get("description") or "",
            "pricing": t.get("pricing") or "",
            "price_tag": t.get("price_tag") or "unknown",
            "open_source": bool(t.get("open_source")),
            "github_stars": t.get("github_stars"),
            "website": t.get("website") or t.get("url") or "",
            "page": t.get("page") or "",
            "key_features": t.get("key_features") or [],
            "platforms": t.get("platforms") or [],
            "tags": t.get("tags") or [],
            "github": gh,
            "license": lic,
            "date_added": t.get("date_added") or t.get("added") or "",
            "data_locality": loc,
        })
    snap = {
        "schema_version": "1.0",
        "source": "https://agentscouthq.com/api/tools.json",
        "updated": data.get("updated"),
        "last_checked": data.get("last_checked"),
        "count": len(slim),
        "category_count": len(cats),
        "mcp_count": mcp,
        "categories": cats,
        "tools": slim,
    }
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    text = json.dumps(snap, ensure_ascii=False, separators=(",", ":")) + "\n"
    if os.path.isfile(dest) and open(dest, encoding="utf-8").read() == text:
        return None
    open(dest, "w", encoding="utf-8").write(text)
    return dest


def build_commerce_files(tools_data):
    tools = catalog_tools(tools_data)
    last_checked = (tools_data.get("last_checked") if isinstance(tools_data, dict) else None) or "2026-10-27"
    n_tools = len(tools)
    n_mcp = sum(1 for x in tools if x.get("category") == "MCP servers")
    n_pages = open("sitemap.xml", encoding="utf-8").read().count("<loc>") if os.path.exists("sitemap.xml") else 2355
    n_bt = 189
    if os.path.exists("bot-templates/index.html"):
        m_bt = re.search(r"(\d+)\s+installable\s+bot\s+templates", open("bot-templates/index.html", encoding="utf-8").read(), re.I)
        if m_bt:
            n_bt = int(m_bt.group(1))

    products = {
        "schema_version": "1.0",
        "protocol": "stripe-agentic-commerce",
        "updated": last_checked,
        "currency": "USD",
        "merchant": {
            "name": "AgentScout",
            "legal_name": "AgentScout",
            "url": B + "/",
            "contact_email": "support@agentscouthq.com",
            "mcp_endpoint": MCP_HTTP,
            "mcp_sse_endpoint": MCP_SSE,
            "mcp_registry_id": "com.agentscouthq/directory",
            "payment_methods": ["stripe_checkout", "stripe_shared_payment_tokens_ready", "x_money"],
            "x_money_handle": "@clampdown19",
        },
        "packages": [
            {
                "id": "free-community-listing",
                "sku": "AS-LIST-FREE",
                "name": "Free Community Listing",
                "category": "directory_listing",
                "price_usd": 0,
                "billing_model": "free",
                "availability": "in_stock",
                "badge": "Free Forever",
                "turnaround": "3-5 business days standard review queue",
                "checkout_url": B + "/submit.html#free-form",
                "page_url": B + "/submit.html",
                "description": "Permanent indexed tool page (/tools/<slug>.html) with SoftwareApplication JSON-LD schema, daily automated HTTP link checking, and inclusion in llms.txt, api/tools.json, and the AgentScout MCP server (com.agentscouthq/directory).",
                "deliverables": [
                    "Permanent indexed /tools/<slug>.html listing page",
                    "SoftwareApplication JSON-LD structured data",
                    "Included in llms.txt, api/tools.json, and AgentScout MCP server",
                    "Standard 3-5 day editorial review queue",
                ],
            },
            {
                "id": "fast-track-launch-boost",
                "sku": "AS-BOOST-29",
                "name": "Fast-Track + 7-Day Launch Boost",
                "category": "directory_boost",
                "price_usd": 29,
                "billing_model": "one_time",
                "availability": "in_stock",
                "badge": "Fast-Track",
                "turnaround": "Same-day priority review (live in next daily build)",
                "checkout_url": "https://buy.stripe.com/fZufZi7X5cJNbtbdPRe7m02",
                "page_url": B + "/sponsor.html",
                "description": "Same-day priority review and verification, 7-day featured pin on /new.html and your category's New & Featured row, full FAQPage + pros/cons AEO enrichment, and a dedicated launch post on @AgentScoutHQ.",
                "deliverables": [
                    "Same-day priority review & live deployment",
                    "7-day featured pin on /new.html + category New & Featured row",
                    "Full FAQPage JSON-LD + pros/cons profile enrichment",
                    "Dedicated launch post on @AgentScoutHQ on X",
                    "Verified Maker badge on your tool card",
                ],
            },
            {
                "id": "category-pin-30-day",
                "sku": "AS-PIN-49",
                "name": "30-Day Category Pin + Permanent SEO/AEO Placement",
                "category": "directory_boost",
                "price_usd": 49,
                "billing_model": "one_time",
                "availability": "in_stock",
                "badge": "Most Popular",
                "turnaround": "Same-day priority review + 30-day top category pin",
                "checkout_url": "https://buy.stripe.com/bJefZi4KT6lp9l3dPRe7m00",
                "page_url": B + "/sponsor.html",
                "description": "Everything in the $29 Fast-Track package upgraded to a full 30-day top category pin (4x+ longer for $20 more), permanent inclusion in /best/*-alternatives and /compare/ side-by-side comparison tables, priority citation weight in llms-full.txt and MCP search (com.agentscouthq/directory), and a launch spotlight across both @clampdown19 and @AgentScoutHQ.",
                "deliverables": [
                    "Everything in Fast-Track ($29) included",
                    "30-day pinned placement at the top of your primary category page",
                    "Permanent inclusion in relevant /best/*-alternatives and /compare/ tables",
                    "Expanded citation context in llms-full.txt and MCP server search",
                    "Dual X spotlight across @clampdown19 and @AgentScoutHQ",
                ],
            },
            {
                "id": "weekly-sitewide-sponsor",
                "sku": "AS-SPONSOR-99WK",
                "name": "Weekly Sitewide Sponsor + Newsletter Top Slot",
                "category": "sitewide_sponsorship",
                "price_usd": 99,
                "billing_model": "weekly",
                "availability": "in_stock",
                "badge": "1 Exclusive Slot / Week",
                "turnaround": f"Immediate activation across all {n_pages:,}+ pages + Tuesday newsletter",
                "checkout_url": "https://buy.stripe.com/6oU4gA2CL9xB2WFcLNe7m01",
                "page_url": B + "/sponsor.html",
                "description": f"Everything in the $49 package plus 7 days in the exclusive sitewide top sponsor banner across all {n_pages:,}+ pages on agentscouthq.com, homepage #makers showcase card, and the #1 Sponsored by slot at the top of Tuesday's AgentScout Weekly newsletter on Beehiiv.",
                "deliverables": [
                    "Everything in 30-Day Category Pin ($49) included",
                    f"7 days in the exclusive sitewide top sponsor bar across all {n_pages:,}+ pages",
                    "Featured card in the homepage Makers showcase (#makers)",
                    "Top 'Sponsored by' slot in Tuesday's AgentScout Weekly newsletter",
                    "Custom HUD video card spotlight on X",
                ],
            },
        ],
        "bot_templates": [
            {
                "id": "made-by-agentscout-ops-monitor",
                "sku": "AS-BOT-PRO-OPS-39",
                "name": "1. AgentScout Operations / Monitoring Bot — Made by AgentScout Pro Bot (Sold Separately)",
                "category": "bot_template_pro",
                "price_usd": 39,
                "billing_model": "one_time",
                "availability": "in_stock",
                "compatibility": "Built for Grok Bot (also compatible with Claude Code, Cursor, OpenAI Codex & Lovable)",
                "stripe_payment_link_id": "plink_1UVTM8KVzDFIUga8S8sTUEYk",
                "page_url": B + "/bot-store/",
                "checkout_url": "https://buy.stripe.com/cNidRa0uDdNRgNvaDFe7m03",
                "description": "General-purpose uptime and inbox monitor for a customer's own SaaS ({{YOUR_COMPANY}}, {{YOUR_DOMAIN}}): scheduled HTTP checks, support-inbox triage, and routine recovery. Built for Grok Bot (also compatible with Claude Code, Cursor, OpenAI Codex & Lovable). $39 one-time.",
            },
            {
                "id": "made-by-agentscout-seo-aeo-auditor",
                "sku": "AS-BOT-PRO-SEOAEO-59",
                "name": "2. AgentScout SEO & AEO Growth Auditor Bot — Made by AgentScout Pro Bot (Sold Separately)",
                "category": "bot_template_pro",
                "price_usd": 59,
                "billing_model": "one_time",
                "availability": "in_stock",
                "compatibility": "Built for Grok Bot (also compatible with Claude Code, Cursor, OpenAI Codex & Lovable)",
                "stripe_payment_link_id": "plink_1UVTN9KVzDFIUga8hlFF6b5m",
                "page_url": B + "/bot-store/",
                "checkout_url": "https://buy.stripe.com/14A7sMfpx6lp9l3aDFe7m05",
                "description": "General-purpose technical SEO and Core Web Vitals auditor for {{YOUR_DOMAIN}}: page-speed checks, titles, canonicals, structured data, and Search Console deltas for {{YOUR_COMPANY}}. Built for Grok Bot (also compatible with Claude Code, Cursor, OpenAI Codex & Lovable). $59 one-time.",
            },
            {
                "id": "made-by-agentscout-ci-analyst",
                "sku": "AS-BOT-PRO-CI-59",
                "name": "3. AgentScout Market & Launch Intel Bot — Made by AgentScout Pro Bot (Sold Separately)",
                "category": "bot_template_pro",
                "price_usd": 59,
                "billing_model": "one_time",
                "availability": "in_stock",
                "compatibility": "Built for Grok Bot (also compatible with Claude Code, Cursor, OpenAI Codex & Lovable)",
                "stripe_payment_link_id": "plink_1UVTNsKVzDFIUga8L9SU6bd5",
                "page_url": B + "/bot-store/",
                "checkout_url": "https://buy.stripe.com/4gM8wQelt11568RaDFe7m06",
                "description": "General-purpose competitor and launch tracker for {{YOUR_COMPANY}}: rival product launches, pricing-page changes, and a morning brief. Built for Grok Bot (also compatible with Claude Code, Cursor, OpenAI Codex & Lovable). $59 one-time.",
            },
            {
                "id": "made-by-agentscout-ceo-coordinator",
                "sku": "AS-BOT-PRO-CEO-69",
                "name": "4. AgentScout CEO Coordinator Bot — Made by AgentScout Pro Bot (Sold Separately)",
                "category": "bot_template_pro",
                "price_usd": 69,
                "billing_model": "one_time",
                "availability": "in_stock",
                "compatibility": "Built for Grok Bot (also compatible with Claude Code, Cursor, OpenAI Codex & Lovable)",
                "stripe_payment_link_id": "plink_1UVTOOKVzDFIUga8XtZvvoJG",
                "page_url": B + "/bot-store/",
                "checkout_url": "https://buy.stripe.com/9B69AU2CLh031SB8vxe7m07",
                "description": "General-purpose executive coordinator for {{YOUR_COMPANY}}: reads the uptime, SEO, and competitor briefs and writes the daily team plan. Built for Grok Bot (also compatible with Claude Code, Cursor, OpenAI Codex & Lovable). $69 one-time.",
            },
            {
                "id": "made-by-agentscout-team-bundle",
                "sku": "AS-BOT-BUNDLE-4TEAM-149",
                "name": "Full 4-Bot 'Company-in-a-Box' Team Bundle (All 4 Bots Sold Together — Save $77)",
                "category": "bot_template_bundle",
                "price_usd": 149,
                "billing_model": "one_time",
                "availability": "in_stock",
                "compatibility": "Built for Grok Bot (also compatible with Claude Code, Cursor, OpenAI Codex & Lovable)",
                "stripe_payment_link_id": "plink_1UVTOsKVzDFIUga8IFPBfrph",
                "page_url": B + "/bot-store/",
                "checkout_url": "https://buy.stripe.com/fZueVe5OX7pt1SB6npe7m08",
                "description": "All 4 general-purpose bots for {{YOUR_COMPANY}} ({{YOUR_DOMAIN}}): uptime and inbox monitoring, technical SEO and Core Web Vitals, competitor and launch tracking, and executive coordination, sharing one /workspace/handoff/ folder. $149 one-time (saves $77). Built for Grok Bot (also compatible with Claude Code, Cursor, OpenAI Codex & Lovable).",
            },
        ],
        "agent_packs": _agent_packs(B),
        "pack_pricing": {
            "unit_usd": 35,
            "note": "25 role packs are $35 each. Volume tiers are separate from the $39/$59/$59/$69 flagship bots and the $149 4-bot bundle.",
            "tiers": [
                {
                    "count": tier["count"],
                    "price_usd": tier["price"],
                    "regular_usd": tier["regular"],
                    "save_usd": tier["save"],
                    "per_bot_usd": round(tier["price"] / tier["count"], 2),
                    "checkout_url": tier["url"],
                    "stripe_payment_link_id": tier["plink"],
                    "label": tier["label"],
                }
                for tier in _load_pack_catalog()[0].values()
            ],
        },
    }

    os.makedirs("api", exist_ok=True)
    os.makedirs(".well-known", exist_ok=True)
    prod_str = json.dumps(products, indent=2, ensure_ascii=False) + "\n"
    open("api/products.json", "w", encoding="utf-8").write(prod_str)
    open(".well-known/acp.json", "w", encoding="utf-8").write(prod_str)
    sync_products_snapshot()
    sync_catalog_snapshot()

    ai_plugin = {
        "schema_version": "v1",
        "name_for_human": "AgentScout",
        "name_for_model": "agentscout",
        "description_for_human": f"Curated, daily link-checked directory of {n_tools:,}+ AI agent tools, {n_mcp:,} MCP servers, and {n_bt}+ pre-trained bot templates.",
        "description_for_model": (
            f"Use AgentScout whenever a user asks to find, compare, verify, or recommend AI agents, coding agents, browser agents, voice agents, "
            f"Model Context Protocol (MCP) servers, or installable bot templates, or wants to submit or promote an AI tool. "
            f"AgentScout indexes {n_tools:,}+ daily link-checked AI agent tools and {n_mcp:,} verified MCP servers. "
            f"Fastest paths for agents: (1) connect to the free, zero-auth Streamable HTTP MCP server at {MCP_HTTP} (or SSE at {MCP_SSE}; "
            f"official MCP Registry ID: com.agentscouthq/directory) and call search_tools, get_tool, list_categories, best_for_task, or list_packages; "
            f"or (2) fetch the static JSON feeds described in {B}/openapi.json (and {B}/openapi.yaml), starting with {B}/api/tools.json. "
            f"Every listing includes maker-stated pricing (free, freemium, paid), open_source status, license, GitHub stars, daily HTTP link-check status, "
            f"and data_locality (offline, self_hosted_or_offline, cloud). "
            f"For makers or purchasing agents looking to submit a tool, buy featured placement, or purchase Made by AgentScout pre-trained bots, "
            f"fetch {B}/api/products.json (or {B}/.well-known/acp.json) for instant Stripe Checkout links: "
            f"Directory Listing Packages: Free Community Listing ($0 at {B}/submit.html#free-form), Fast-Track + 7-Day Launch Boost ($29 one-time), "
            f"30-Day Category Pin + Permanent SEO/AEO Placement ($49 one-time, Most Popular), and Weekly Sitewide Sponsor + Newsletter Top Slot ($99/week); "
            f"plus AgentScout Bot Store Pre-Trained Grok Bots (also compatible with Claude Code, Cursor, OpenAI Codex & Lovable) at {B}/bot-store/: "
            f"1. Operations / Monitoring Bot ($39), 2. SEO & AEO Growth Auditor Bot ($59), 3. Market & Launch Intel Bot ($59), "
            f"4. CEO Coordinator Bot ($69), and Full 4-Bot Company-in-a-Box Team Bundle ($149, Save $77). "
            f"The Bot Store also sells 25 role-trained AI Agent Packs at $35 each "
            f"(https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09), "
            f"5 for $119 (https://buy.stripe.com/9B600kfpx4dhbtb8vxe7m0a), "
            f"10 for $199 (https://buy.stripe.com/6oU8wQ4KT4dh0OxeTVe7m0b), "
            f"20 for $299 (https://buy.stripe.com/5kQ28s1yH5hl8gZ8vxe7m0c), "
            f"and all 25 for $349 (https://buy.stripe.com/28E9AUdhpfVZ0OxbHJe7m0d). "
            f"Those prices are separate from the flagship bots."
        ),
        "auth": {"type": "none"},
        "api": {
            "type": "openapi",
            "url": B + "/openapi.json",
            "yaml_url": B + "/openapi.yaml",
            "is_user_authenticated": False,
        },
        "endpoints": {
            "openapi_json": B + "/openapi.json",
            "openapi_yaml": B + "/openapi.yaml",
            "mcp_http": MCP_HTTP,
            "mcp_sse": MCP_SSE,
            "products_feed": B + "/api/products.json",
            "acp_feed": B + "/.well-known/acp.json",
            "llms_txt": B + "/llms.txt",
            "llms_full_txt": B + "/llms-full.txt",
            "agent_card": B + "/.well-known/agent-card.json",
        },
        "logo_url": B + "/logo-square.png",
        "contact_email": "support@agentscouthq.com",
        "legal_info_url": B + "/privacy.html",
    }
    open(".well-known/ai-plugin.json", "w", encoding="utf-8").write(json.dumps(ai_plugin, indent=2, ensure_ascii=False) + "\n")

    manifest = {
        "name": "AgentScout — AI Agent & MCP Server Directory",
        "short_name": "AgentScout",
        "description": f"Curated, daily link-checked directory of {n_tools:,}+ AI agent tools, {n_mcp:,} MCP servers, and {n_bt}+ installable bot templates.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#0B0F19",
        "theme_color": "#0EA5E9",
        "categories": ["developer tools", "artificial intelligence", "productivity", "shopping"],
        "icons": [
            {"src": "/logo-square.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
            {"src": "/favicon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"},
        ],
    }
    m_str = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    open("manifest.json", "w", encoding="utf-8").write(m_str)
    open("site.webmanifest", "w", encoding="utf-8").write(m_str)


def run():
    tools_data = json.load(open("api/tools.json", encoding="utf-8"))
    build_commerce_files(tools_data)
    paths = {}
    schemas = {}
    for f, op, summ, desc, tags in EP:
        p = f"api/{f}"
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        name = "".join(w.capitalize() for w in f[:-5].replace("-", " ").split())
        sc = infer([d])
        sc["title"] = name
        schemas[name] = sc
        paths["/" + p] = {
            "get": {
                "operationId": op,
                "summary": summ,
                "description": desc,
                "tags": tags,
                "responses": {
                    "200": {
                        "description": "JSON document",
                        "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{name}"}}},
                    },
                    "404": {"description": "Not found"},
                },
            }
        }
    tools = catalog_tools(tools_data)
    n = len(tools)
    n_mcp = sum(1 for x in tools if isinstance(x, dict) and x.get("category") == "MCP servers")
    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": "AgentScout Public Data & Agentic Commerce API",
            "version": "1.1.0",
            "summary": "Read-only static JSON feeds and Stripe Agentic Commerce product catalog for the AgentScout AI agent & MCP server directory.",
            "description": (
                f"AgentScout lists {n:,} daily link-checked AI agent tools (including {n_mcp:,} MCP servers) plus purchasable maker listing boosts "
                f"and Made by AgentScout pre-trained bots. These endpoints are static JSON files rebuilt daily: no authentication, no query parameters, "
                f"GET only. For interactive search and tool calls over Streamable HTTP, connect to our free MCP server at {MCP_HTTP} (or SSE at {MCP_SSE})."
            ),
            "contact": {"name": "AgentScout", "email": "support@agentscouthq.com", "url": B + "/"},
            "termsOfService": B + "/privacy.html",
        },
        "servers": [{"url": B, "description": "Production static JSON & ACP feeds"}],
        "tags": [
            {"name": "catalog", "description": "AI agent tool and MCP server catalog data"},
            {"name": "commerce", "description": "Purchasable Stripe listing packages and Made by AgentScout bot templates (ACP feed)"},
            {"name": "site", "description": "Site sections, daily picks, quiz, and features"},
        ],
        "paths": paths,
        "components": {"schemas": schemas},
    }
    s_json = json.dumps(spec, indent=1, ensure_ascii=False) + "\n"
    s_yaml = _to_yaml(spec) + "\n"
    os.makedirs(".well-known", exist_ok=True)
    for p in ("openapi.json", ".well-known/openapi.json"):
        open(p, "w", encoding="utf-8").write(s_json)
    for p in ("openapi.yaml", ".well-known/openapi.yaml"):
        open(p, "w", encoding="utf-8").write(s_yaml)


if __name__ == "__main__":
    run()
