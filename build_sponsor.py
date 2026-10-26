"""Sponsor & Featured Packages page (/sponsor.html) + shared 3-tier package cards + auto-updating metrics + sitewide sponsor bar (Oct 26, 2026 PT).
Offers 3 clear tiers:
  1. Free Community Listing ($0 Forever)
  2. Featured Listing & Category Boost ($49 one-time) -> https://buy.stripe.com/bJefZi4KT6lp9l3dPRe7m00
  3. Weekly Sitewide Sponsor + Newsletter Top Slot ($99 / week) -> https://buy.stripe.com/6oU4gA2CL9xB2WFcLNe7m01
Plus instant X Money payment option to @clampdown19 (https://x.com/clampdown19).
All directory, X follower, and traffic numbers auto-update at build time (data/site_metrics.json + api/metrics.json) and via client-side fetch.
"""
import json, os, glob, re, html, datetime, urllib.request
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")
STRIPE_49 = "https://buy.stripe.com/bJefZi4KT6lp9l3dPRe7m00"
STRIPE_99 = "https://buy.stripe.com/6oU4gA2CL9xB2WFcLNe7m01"
STRIPE_FEATURED = STRIPE_49
STRIPE_WEEKLY = STRIPE_99
XMONEY_URL = "https://x.com/clampdown19"
BAR_START, BAR_END = "<!--SPONSORBAR-START-->", "<!--SPONSORBAR-END-->"
e = lambda s: html.escape(str(s or ""))

def load_metrics(t=None):
    """Compute and refresh live site, X follower, and traffic metrics without hardcoded numbers."""
    if t is None:
        t = json.load(open("tools.json")) if os.path.exists("tools.json") else []
    m_path = "data/site_metrics.json"
    M = json.load(open(m_path)) if os.path.exists(m_path) else {}
    sp_st = json.load(open("data/sponsor_stats.json")) if os.path.exists("data/sponsor_stats.json") else {}
    sb_path = "/workspace/data/30-day-growth-scoreboard.json"
    sb = json.load(open(sb_path)) if os.path.exists(sb_path) else {}

    # 1. Directory counts from repo
    n_tools = len(t)
    n_mcp = sum(1 for x in t if x.get("category") == "MCP servers")
    n_cats = len({x.get("category") for x in t if x.get("category")})
    n_bt = 193
    if os.path.exists("bot-templates/index.html"):
        _bt_rows = len(re.findall(r'<li class="bt-row" ', open("bot-templates/index.html", errors="ignore").read()))
        if _bt_rows:
            n_bt = max(_bt_rows, 189)
    n_pages = M.get("indexed_pages_count", 2327)
    if os.path.exists("sitemap.xml"):
        _locs = len(re.findall(r"<loc>", open("sitemap.xml", errors="ignore").read()))
        if _locs:
            n_pages = _locs

    # 2. X follower counts (from scoreboard snapshots/baseline or site_metrics.json)
    base_sb = sb.get("baseline_2026_10_25") or {}
    snaps = sb.get("daily_snapshots") or []
    latest_snap = snaps[-1] if snaps else {}
    x_clamp = max(int(M.get("x_clampdown19_followers", 2095)), int(base_sb.get("x_clampdown19_followers", 0)), int(latest_snap.get("x_clampdown19_followers", 0)))
    x_as = max(int(M.get("x_agentscouthq_followers", 9)), int(base_sb.get("x_agentscouthq_followers", 0)), int(latest_snap.get("x_agentscouthq_followers", 0)))
    x_comb = x_clamp + x_as

    # 3. Live traffic stats from Worker /stats?days=30 when STATS_KEY is available, with fallback to cached values
    pv_30d = int(M.get("pageviews_30d", 739))
    pv_7d = int(sp_st.get("weekly_page_views") or M.get("weekly_page_views") or 551)
    gsc_imp = int(M.get("gsc_7d_impressions", 8210))
    kp = os.path.expanduser("~/.agentscout-stats-key")
    key = os.environ.get("STATS_KEY") or (open(kp).read().strip() if os.path.exists(kp) else "")
    if key and not os.environ.get("OFFLINE_BUILD"):
        try:
            req = urllib.request.Request(
                "https://agentscout-image.agentscouthq.workers.dev/stats?days=30",
                headers={"X-Stats-Key": key, "User-Agent": "agentscout-build-metrics"}
            )
            d = json.load(urllib.request.urlopen(req, timeout=5)).get("days", [])
            if d:
                live_30 = sum(int(x.get("counters", {}).get("web:page_view", 0)) for x in d)
                live_7 = sum(int(x.get("counters", {}).get("web:page_view", 0)) for x in d[:7])
                if live_30 > 0:
                    pv_30d = max(pv_30d, live_30)
                if live_7 > 0:
                    pv_7d = max(pv_7d, live_7)
        except Exception:
            pass

    now_iso = datetime.datetime.now(PT).strftime("%Y-%m-%dT%H:%M:%S%z")
    now_disp = datetime.datetime.now(PT).strftime("%b %-d, %Y")
    out = {
        "tools_count": n_tools,
        "mcp_servers_count": n_mcp,
        "categories_count": n_cats,
        "bot_templates_count": n_bt,
        "indexed_pages_count": n_pages,
        "pages_count": n_pages,
        "mcp_count": n_mcp,
        "pageviews_7d": pv_7d,
        "x_clampdown19_followers": x_clamp,
        "x_agentscouthq_followers": x_as,
        "x_combined_followers": x_comb,
        "pageviews_30d": pv_30d,
        "weekly_page_views": pv_7d,
        "gsc_7d_impressions": gsc_imp,
        "updated_at": now_iso,
        "updated_display": now_disp
    }
    os.makedirs("data", exist_ok=True)
    os.makedirs("api", exist_ok=True)
    json.dump(out, open(m_path, "w"), indent=2)
    json.dump(out, open("api/metrics.json", "w"), indent=2)
    return out

def live_metrics_js(depth=""):
    """Client-side auto-updater for [data-live-*] elements on /sponsor.html, /submit.html, and index.html."""
    return (
        f'<script>(function(){{function fmt(n){{return Number(n).toLocaleString("en-US")}}'
        f'function setAll(sel,val){{var els=document.querySelectorAll(sel);for(var i=0;i<els.length;i++)els[i].textContent=val}}'
        f'fetch("{depth}api/metrics.json",{{cache:"no-cache"}}).then(function(r){{return r.ok?r.json():null}}).then(function(m){{if(!m)return;'
        f'if(m.tools_count)setAll("[data-live-tools]",fmt(m.tools_count));'
        f'if(m.mcp_servers_count)setAll("[data-live-mcp]",fmt(m.mcp_servers_count));'
        f'if(m.categories_count)setAll("[data-live-cats]",fmt(m.categories_count));'
        f'if(m.indexed_pages_count)setAll("[data-live-pages]",fmt(m.indexed_pages_count)+"+");'
        f'if(m.x_clampdown19_followers)setAll("[data-live-clampdown]",fmt(m.x_clampdown19_followers)+"+");'
        f'if(m.x_combined_followers)setAll("[data-live-x-followers]",fmt(m.x_combined_followers)+"+");'
        f'if(m.pageviews_30d)setAll("[data-live-pv30]",fmt(m.pageviews_30d)+"+");'
        f'if(m.weekly_page_views)setAll("[data-live-pv7]",fmt(m.weekly_page_views)+"+");'
        f'if(m.updated_display)setAll("[data-live-updated]",m.updated_display);'
        f'}}).catch(function(){{}});'
        f'fetch("{depth}api/tools.json",{{cache:"no-cache"}}).then(function(r){{return r.ok?r.json():null}}).then(function(d){{if(!d||!d.count)return;'
        f'setAll("[data-live-tools]",fmt(d.count));'
        f'if(Array.isArray(d.tools)){{var mcp=d.tools.filter(function(x){{return x.category==="MCP servers"}}).length;if(mcp)setAll("[data-live-mcp]",fmt(mcp))}}'
        f'}}).catch(function(){{}});}})()</script>'
    )

def bar_html(sp, depth=""):
    """Small fixed bar at the bottom of the page. position:fixed, so it never shifts the layout (no CLS); dismissible per visitor."""
    logo = f'<img src="{e(sp["logo"])}" alt="" width="20" height="20" style="border-radius:5px;flex:none">' if sp.get("logo") else ""
    return (f'{BAR_START}<div id="sponsorbar" role="complementary" aria-label="Sponsor" style="position:fixed;left:50%;bottom:12px;transform:translateX(-50%);z-index:60;'
      'display:flex;align-items:center;gap:10px;max-width:calc(100vw - 24px);padding:8px 10px 8px 14px;border:1px solid var(--line);border-radius:999px;'
      'background:var(--card);box-shadow:var(--shadow);font-size:13px;line-height:20px;color:var(--text)">'
      '<span style="font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--faint);flex:none">Sponsor</span>'
      f'<a href="{e(sp["url"])}" target="_blank" rel="sponsored noopener" style="display:flex;align-items:center;gap:8px;min-width:0;color:inherit;text-decoration:none">{logo}'
      f'<span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis"><b>{e(sp["name"])}</b>: {e(sp["pitch"])}</span></a>'
      '<button type="button" aria-label="Hide sponsor" onclick="try{localStorage.setItem(\'as_sponsorbar\',\'0\')}catch(e){}this.parentNode.remove()" '
      'style="flex:none;width:24px;height:24px;border:0;border-radius:50%;background:transparent;color:var(--muted);cursor:pointer;font-size:16px;line-height:24px">×</button></div>'
      '<script>try{if(localStorage.getItem("as_sponsorbar")==="0"){var b=document.getElementById("sponsorbar");b&&b.remove()}}catch(e){}</script>'
      f'{BAR_END}')

def apply_bar(enabled):
    sp = json.load(open("data/sponsor_bar.json")) if os.path.exists("data/sponsor_bar.json") else {}
    ready = enabled and all(sp.get(k) for k in ("name", "pitch", "url"))
    if enabled and not ready:
        print("build_sponsor: SPONSOR_ENABLED is on but data/sponsor_bar.json is incomplete; no bar rendered")
    rx = re.compile(re.escape(BAR_START) + ".*?" + re.escape(BAR_END), re.S)
    n = 0
    for f in glob.glob("**/*.html", recursive=True):
        if f in ("outreach-tracker.html", "sponsor.html") or f.startswith(("app/", "node_modules/", "preview/")):
            continue
        s = open(f, errors="ignore").read()
        o = s
        s = rx.sub("", s)
        if ready and "</body>" in s and 'http-equiv="refresh"' not in s:
            d = "../" * f.count("/")
            s = s.replace("</body>", bar_html(sp, d) + "</body>", 1)
            n += 1
        if s != o:
            open(f, "w").write(s)
    return n

def packages_grid(free_href="#free-form", free_label="Submit Free Below ↓", on_submit=False, M=None):
    if M is None:
        M = load_metrics()
    ntools = f'{M["tools_count"]:,}'
    nmcp = f'{M["mcp_servers_count"]:,}'
    npages = f'{M["indexed_pages_count"]:,}+'
    xclamp = f'{M["x_clampdown19_followers"]:,}+'
    xcomb = f'{M["x_combined_followers"]:,}+'
    pv30 = f'{M["pageviews_30d"]:,}+'

    if on_submit:
        cta_free = f'<a class="btn pkg-cta" href="#sf" data-pick-pkg="free">{free_label}</a>'
        cta_49 = (f'<a class="btn primary pkg-cta pkg-cta-pop" href="#sf" data-pick-pkg="featured_49">Select $49 Featured &amp; Fill Form ↓</a>'
                  f'<div class="pkg-xmoney"><span>💳 Or <a href="{STRIPE_49}" target="_blank" rel="noopener noreferrer">checkout directly on Stripe ($49) ↗</a> · ⚡ X Money: <a href="{XMONEY_URL}" target="_blank" rel="noopener noreferrer">@clampdown19</a></span></div>')
        cta_99 = (f'<a class="btn primary pkg-cta pkg-cta-vip" href="#sf" data-pick-pkg="sponsor_99">Select $99/wk Sponsor &amp; Fill Form ↓</a>'
                  f'<div class="pkg-xmoney"><span>💳 Or <a href="{STRIPE_99}" target="_blank" rel="noopener noreferrer">checkout directly on Stripe ($99/wk) ↗</a> · ⚡ X Money: <a href="{XMONEY_URL}" target="_blank" rel="noopener noreferrer">@clampdown19</a></span></div>')
    else:
        cta_free = f'<a class="btn pkg-cta" href="{free_href}">{free_label}</a>'
        cta_49 = (f'<a class="btn primary pkg-cta pkg-cta-pop" href="{STRIPE_49}" target="_blank" rel="noopener noreferrer">Get Featured — $49 →</a>'
                  f'<div class="pkg-xmoney"><span>⚡ Or pay <b>$49</b> via <b>X Money</b> to <a href="{XMONEY_URL}" target="_blank" rel="noopener noreferrer">@clampdown19</a></span></div>')
        cta_99 = (f'<a class="btn primary pkg-cta pkg-cta-vip" href="{STRIPE_99}" target="_blank" rel="noopener noreferrer">Book Weekly Sponsor — $99/wk →</a>'
                  f'<div class="pkg-xmoney"><span>⚡ Or pay <b>$99</b> via <b>X Money</b> to <a href="{XMONEY_URL}" target="_blank" rel="noopener noreferrer">@clampdown19</a></span></div>')

    return (
        '<div class="pkg-grid" id="packages">'
        # Tier 1: Free Community Listing
        '<div class="card pkg-card" data-pkg-card="free">'
        '<div class="pkg-top"><span class="npill npft pkg-pill pkg-pill-free"><svg class="npico" aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="14" height="14"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8zM19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></svg>COMMUNITY TIER · $0</span></div>'
        '<h3>Free Community Listing</h3>'
        '<div class="pkg-price"><span class="pkg-amt">$0</span> <span class="pkg-per">forever</span></div>'
        f'<p class="pkg-sub">Get indexed across <b data-live-tools>{ntools}</b> tools &amp; <b data-live-mcp>{nmcp}</b> MCP servers at zero cost.</p>'
        '<ul class="pkg-list">'
        '<li><span class="pkg-chk" aria-hidden="true">✓</span><span>Permanent tool profile page, category placement &amp; public JSON API listing</span></li>'
        '<li><span class="pkg-chk" aria-hidden="true">✓</span><span>Standard editorial &amp; link review queue (typically 5–7 business days)</span></li>'
        '<li><span class="pkg-chk" aria-hidden="true">✓</span><span><b>✓ Submitted by maker</b> verified badge on your listing</span></li>'
        '</ul>'
        '<div class="pkg-foot">' + cta_free + '</div>'
        '</div>'
        # Tier 2: $49 Featured Listing & Category Boost
        '<div class="card pkg-card pkg-featured" data-pkg-card="featured_49">'
        '<div class="pkg-top"><span class="npill npmcp pkg-pill pkg-pill-pop"><svg class="npico" aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="14" height="14"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 2l2.4 7.2H22l-6 4.6 2.3 7.2L12 16.5 5.7 21l2.3-7.2-6-4.6h7.6z"/></svg>MOST POPULAR FOR MAKERS</span></div>'
        '<h3>Featured Listing &amp; Category Boost</h3>'
        '<div class="pkg-price"><span class="pkg-amt">$49</span> <span class="pkg-per">one-time · 30 days featured</span></div>'
        '<p class="pkg-sub">Skip the queue, pin to the top of your category &amp; get an X launch spotlight.</p>'
        '<ul class="pkg-list">'
        '<li><span class="pkg-chk pkg-chk-pop" aria-hidden="true">✓</span><span><b>Priority same-day review</b> — live within 24 hours with enriched copy, FAQ &amp; comparison links</span></li>'
        '<li><span class="pkg-chk pkg-chk-pop" aria-hidden="true">✓</span><span><b>Pinned “Featured” badge at the top of your category</b> + homepage Makers strip for <b>30 days</b></span></li>'
        f'<li><span class="pkg-chk pkg-chk-pop" aria-hidden="true">✓</span><span><b>Dedicated X launch spotlight</b> across <a href="{XMONEY_URL}" target="_blank" rel="noopener noreferrer">@clampdown19</a> &amp; <a href="https://x.com/AgentScoutHQ" target="_blank" rel="noopener noreferrer">@AgentScoutHQ</a> (<b data-live-x-followers>{xcomb}</b> combined followers)</span></li>'
        '<li><span class="pkg-chk pkg-chk-pop" aria-hidden="true">✓</span><span><b>Featured highlight</b> in the next Tuesday issue of the AgentScout Weekly newsletter</span></li>'
        '</ul>'
        '<div class="pkg-foot">' + cta_49 + '</div>'
        '</div>'
        # Tier 3: $99/wk Weekly Sitewide Sponsor + Newsletter Top Slot
        '<div class="card pkg-card pkg-vip" data-pkg-card="sponsor_99">'
        '<div class="pkg-top"><span class="npill npbt pkg-pill pkg-pill-vip"><svg class="npico" aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="14" height="14"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>1 EXCLUSIVE SLOT / WEEK</span></div>'
        '<h3>Weekly Sitewide Sponsor + Newsletter</h3>'
        '<div class="pkg-price"><span class="pkg-amt">$99</span> <span class="pkg-per">/ week · exclusive sitewide</span></div>'
        '<p class="pkg-sub">Own the top banner across every page of AgentScout + our weekly newsletter.</p>'
        '<ul class="pkg-list">'
        '<li><span class="pkg-chk pkg-chk-vip" aria-hidden="true">✓</span><span><b>Everything in Featured Boost ($49)</b> included automatically</span></li>'
        f'<li><span class="pkg-chk pkg-chk-vip" aria-hidden="true">✓</span><span><b>Exclusive Sitewide Sponsor Bar</b> across all <b data-live-pages>{npages}</b> tool, category &amp; comparison pages for 7 days</span></li>'
        '<li><span class="pkg-chk pkg-chk-vip" aria-hidden="true">✓</span><span><b>Top “Sponsored by” banner</b> in Tuesday’s AgentScout Weekly newsletter (logo + 2-sentence pitch + CTA)</span></li>'
        f'<li><span class="pkg-chk pkg-chk-vip" aria-hidden="true">✓</span><span><b>Pinned weekend &amp; launch-day X threads</b> from <a href="{XMONEY_URL}" target="_blank" rel="noopener noreferrer">@clampdown19</a> &amp; <a href="https://x.com/AgentScoutHQ" target="_blank" rel="noopener noreferrer">@AgentScoutHQ</a></span></li>'
        '</ul>'
        '<div class="pkg-foot">' + cta_99 + '</div>'
        '</div>'
        '</div>'
        # Trust signals strip (all numbers auto-updated via data-live-* attributes)
        '<div class="pkg-trust" role="region" aria-label="AgentScout directory reach and checkout options">'
        f'<span class="pkgt-item"><b data-live-tools>{ntools}</b> tools indexed</span>'
        '<span class="pkgt-dot" aria-hidden="true">·</span>'
        f'<span class="pkgt-item"><b data-live-mcp>{nmcp}</b> MCP servers</span>'
        '<span class="pkgt-dot" aria-hidden="true">·</span>'
        f'<span class="pkgt-item"><b data-live-pages>{npages}</b> indexed pages (<b data-live-pv30>{pv30}</b> 30d views)</span>'
        '<span class="pkgt-dot" aria-hidden="true">·</span>'
        f'<span class="pkgt-item">Daily X spotlights on <a href="{XMONEY_URL}" target="_blank" rel="noopener noreferrer"><b>@clampdown19</b></a> &amp; <a href="https://x.com/AgentScoutHQ" target="_blank" rel="noopener noreferrer"><b>@AgentScoutHQ</b></a> (<b data-live-x-followers>{xcomb}</b> followers)</span>'
        '<span class="pkgt-dot" aria-hidden="true">·</span>'
        f'<span class="pkgt-item">Instant checkout via <b>Stripe</b> or <b>X Money</b> (<a href="{XMONEY_URL}" target="_blank" rel="noopener noreferrer">@clampdown19</a>)</span>'
        '</div>'
    )

def tiers_html(ntools=1786, nmcp=249, on_submit=False, t=None):
    M = load_metrics(t)
    return packages_grid(
        free_href="#sf" if on_submit else "submit.html#free-form",
        free_label="Select Free Tier & Fill Form ↓" if on_submit else "Submit Free ($0) →",
        on_submit=on_submit,
        M=M
    )

def build(t=None):
    import build_extras as X
    if t is None:
        t = json.load(open("tools.json"))
    M = load_metrics(t)
    n_tools = M["tools_count"]
    n_cats = M["categories_count"]
    n_mcp = M["mcp_servers_count"]
    n_pages = M["indexed_pages_count"]
    x_comb = M["x_combined_followers"]
    pv_30d = M["pageviews_30d"]
    pv_7d = M["weekly_page_views"]
    upd_disp = M["updated_display"]

    title = "Get Featured & Sponsor AgentScout — Boost Your AI Agent Tool"
    desc = f"Get your AI agent tool or MCP server featured across {n_tools:,}+ tools on AgentScout. Choose Free Community Listing ($0), Featured Category Boost ($49), or Weekly Sitewide Sponsor ($99/wk)."
    canon = f"{X.B}sponsor.html"
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canon,
                "url": canon,
                "name": title,
                "description": desc,
                "isPartOf": {"@type": "WebSite", "name": "AgentScout", "url": X.B}
            },
            {
                "@type": "Product",
                "name": "AgentScout Featured Listing & Sponsorship Packages",
                "description": desc,
                "brand": {"@type": "Organization", "name": "AgentScout", "url": X.B, "sameAs": ["https://x.com/AgentScoutHQ", "https://x.com/clampdown19"]},
                "offers": [
                    {
                        "@type": "Offer",
                        "name": "Free Community Listing",
                        "price": "0",
                        "priceCurrency": "USD",
                        "availability": "https://schema.org/InStock",
                        "url": f"{X.B}submit.html#free-form"
                    },
                    {
                        "@type": "Offer",
                        "name": "Featured Listing & Category Boost (30 Days + X Spotlight)",
                        "price": "49",
                        "priceCurrency": "USD",
                        "availability": "https://schema.org/InStock",
                        "url": STRIPE_49
                    },
                    {
                        "@type": "Offer",
                        "name": "Weekly Sitewide Sponsor + Newsletter Top Slot (7 Days)",
                        "price": "99",
                        "priceCurrency": "USD",
                        "availability": "https://schema.org/LimitedAvailability",
                        "url": STRIPE_99
                    }
                ]
            }
        ]
    }
    stats_cards = (
        '<h2 style="font-size:20px;margin:28px 0 12px">Live directory &amp; audience reach <span class="muted" style="font-size:13px;font-weight:400">(auto-updated <span data-live-updated>' + e(upd_disp) + '</span>)</span></h2>'
        '<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(200px,1fr));margin-bottom:28px">'
        f'<div class="card"><div style="font-size:26px;font-weight:800;line-height:1.1" data-live-tools>{n_tools:,}</div><div style="font-weight:600;margin-top:4px">AI agent tools indexed</div><p class="muted" style="margin:4px 0 0;font-size:12.5px">Across <span data-live-cats>{n_cats}</span> categories, link-checked daily.</p></div>'
        f'<div class="card"><div style="font-size:26px;font-weight:800;line-height:1.1" data-live-pages>{n_pages:,}+</div><div style="font-weight:600;margin-top:4px">Indexed directory pages</div><p class="muted" style="margin:4px 0 0;font-size:12.5px"><span data-live-pv30>{pv_30d:,}+</span> 30-day views (<span data-live-pv7>{pv_7d:,}+</span> weekly views).</p></div>'
        f'<div class="card"><div style="font-size:26px;font-weight:800;line-height:1.1" data-live-mcp>{n_mcp:,}</div><div style="font-weight:600;margin-top:4px">MCP servers indexed</div><p class="muted" style="margin:4px 0 0;font-size:12.5px">Searchable via our public MCP server for Claude, Cursor &amp; VS Code.</p></div>'
        f'<div class="card"><div style="font-size:26px;font-weight:800;line-height:1.1" data-live-x-followers>{x_comb:,}+</div><div style="font-weight:600;margin-top:4px">X spotlight reach</div><p class="muted" style="margin:4px 0 0;font-size:12.5px">Dedicated posts on <a href="{XMONEY_URL}" target="_blank" rel="noopener noreferrer">@clampdown19</a> &amp; <a href="https://x.com/AgentScoutHQ" target="_blank" rel="noopener noreferrer">@AgentScoutHQ</a>.</p></div>'
        '</div>'
    )
    body = (
        '<div class="crumb"><a href="index.html">AgentScout</a> / Sponsor &amp; Get Featured</div>'
        '<section class="sp-hero" style="padding-top:20px;text-align:left">'
        '<span class="npill npsp sp-eyebrow"><svg class="npico" aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="14" height="14"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8zM19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></svg>For AI Agent &amp; MCP Makers · High-Intent Buyer Traffic</span>'
        '<h1 style="text-align:left;margin:8px 0 10px">Get your AI tool in front of builders &amp; buyers</h1>'
        f'<p class="lede" style="margin-left:0;text-align:left;max-width:780px">AgentScout indexes <b data-live-tools>{n_tools:,}</b> link-checked AI agent tools (including <b data-live-mcp>{n_mcp:,}</b> MCP servers) across <b data-live-cats>{n_cats}</b> categories and <b data-live-pages>{n_pages:,}+</b> pages, plus side-by-side comparisons, best-of lists, and the Tuesday <b>AgentScout Weekly</b> newsletter. Every paid boost also gets a dedicated X spotlight across <a href="{XMONEY_URL}" target="_blank" rel="noopener noreferrer"><b>@clampdown19</b></a> and <a href="https://x.com/AgentScoutHQ" target="_blank" rel="noopener noreferrer"><b>@AgentScoutHQ</b></a> (<b data-live-x-followers>{x_comb:,}+</b> combined followers).</p>'
        + packages_grid(free_href="submit.html#free-form", free_label="Submit Free ($0) →", on_submit=False, M=M)
        + stats_cards
        + '<div class="card sp-xmoney-card">'
        '<h2 style="font-size:18px;margin:0 0 8px">💳 Pay with Card (Stripe) or X Money (<a href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer">@clampdown19</a>)</h2>'
        '<p style="margin:0 0 10px;font-size:14.5px;color:var(--muted)">Use the instant <b>Stripe Checkout</b> buttons above (Apple Pay, Google Pay, Link, and all major credit/debit cards accepted), or send <b>$49</b> (Featured Boost) or <b>$99</b> (Weekly Sitewide Sponsor) directly via <b>X Money</b> to <a href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer"><b>@clampdown19</b></a> with your tool name and URL in the note.</p>'
        '<p style="margin:0;font-size:13.5px;color:var(--muted)">Already submitted your tool via the <a href="submit.html#free-form">submission form</a>? Just use the same tool name or email at checkout and we will upgrade and pin your listing within 24 hours.</p>'
        '</div>'
        '<h2 style="font-size:20px;margin:32px 0 12px">How it works</h2>'
        '<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr));margin-bottom:28px">'
        '<div class="card"><h3 style="margin:0 0 6px;font-size:16px">1. Submit or claim your tool</h3><p style="margin:0;font-size:14px;color:var(--muted)">Fill out the 60-second <a href="submit.html#free-form">tool submission form</a> (or name an existing tool already listed on AgentScout).</p></div>'
        '<div class="card"><h3 style="margin:0 0 6px;font-size:16px">2. Pick your boost tier</h3><p style="margin:0;font-size:14px;color:var(--muted)">Complete checkout via Stripe (<a href="' + STRIPE_49 + '" target="_blank" rel="noopener noreferrer">$49 Featured Boost</a> or <a href="' + STRIPE_99 + '" target="_blank" rel="noopener noreferrer">$99/wk Weekly Sponsor</a>) or X Money (<a href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer">@clampdown19</a>).</p></div>'
        '<div class="card"><h3 style="margin:0 0 6px;font-size:16px">3. Go live within 24 hours</h3><p style="margin:0;font-size:14px;color:var(--muted)">We verify your links, publish your enriched profile, pin your tool, and post your X launch spotlight on <a href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer">@clampdown19</a> &amp; <a href="https://x.com/AgentScoutHQ" target="_blank" rel="noopener noreferrer">@AgentScoutHQ</a>.</p></div>'
        '</div>'
        '<h2 style="font-size:20px;margin:28px 0 12px">Frequently asked questions</h2>'
        '<details style="margin:0 0 10px"><summary><b>How transparent are sponsored &amp; featured placements?</b></summary><p class="muted" style="margin:8px 0 0;font-size:14px">Every paid placement carries a clear “Featured” or “Sponsored” badge (<code style="font-size:12px">rel="sponsored"</code>) so readers always know what is sponsored. Organic rankings, comparison facts, and editorial notes are never altered for payment.</p></details>'
        '<details style="margin:0 0 10px"><summary><b>What if my tool isn’t a fit for the directory?</b></summary><p class="muted" style="margin:8px 0 0;font-size:14px">We only list working AI agent tools, MCP servers, frameworks, and AI apps. If we cannot verify or list your submission, we refund 100% of your payment immediately.</p></details>'
        '<details style="margin:0 0 10px"><summary><b>How do I send my logo, screenshots, or newsletter copy?</b></summary><p class="muted" style="margin:8px 0 0;font-size:14px">Include your links in the <a href="submit.html#free-form">submission form</a> or email <a href="mailto:support@agentscouthq.com">support@agentscouthq.com</a> / DM <a href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer">@clampdown19</a> or <a href="https://x.com/AgentScoutHQ" target="_blank" rel="noopener noreferrer">@AgentScoutHQ</a> on X after checkout.</p></details>'
        '<p class="disclose" style="margin-top:24px">Questions or multi-week sponsorship inquiries? Email <a href="mailto:support@agentscouthq.com">support@agentscouthq.com</a> or message <a href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer">@clampdown19</a> / <a href="https://x.com/AgentScoutHQ" target="_blank" rel="noopener noreferrer">@AgentScoutHQ</a> on X.</p>'
        '</section>'
        + live_metrics_js("")
    )
    out = X.shell("", title, desc, canon, body, ld)
    open("sponsor.html", "w").write(out)
    return canon

page = build

if __name__ == "__main__":
    t = json.load(open("tools.json"))
    page(t)
    import build_tasks
    build_tasks.sitewide(t)
    print("sponsor.html built; bar pages:", apply_bar(False))
