"""Sponsor / Featured Packages page (sponsor.html) + shared live metrics (`api/metrics.json`) + reusable 4-tier package cards.
Public, indexed, in sitemap.xml & llms.txt (Oct 26, 2026 — owner-approved 4-Tier Neon Lineup)."""
import json, html, os, glob, re
from datetime import datetime, timezone, timedelta

STRIPE_FAST_URL = "https://buy.stripe.com/3cIaEY6T15hlfJr135e7m0e"
STRIPE_FAST = STRIPE_FAST_URL
STRIPE_49 = "https://buy.stripe.com/bJefZi4KT6lp9l3dPRe7m00"
STRIPE_99 = "https://buy.stripe.com/6oU4gA2CL9xB2WFcLNe7m01"
# Directory Launch Pack ($49 add-on). This is the only definition of the Payment Link.
LAUNCH_PACK_URL = "https://buy.stripe.com/28EfZidhp6lp9l3aDFe7m0f"
FAST_TRACK_INDEX_LINE = "Same-day indexing ping to Bing and IndexNow search engines (does not include Google)."
LAUNCH_PACK_PROMISE = "Submitted to ~25 hand-picked AI directories within 7 days, with a report of live and pending links, plus a follow-up report at 30 days (some directories take weeks to approve)."
LAUNCH_PACK_ACCOUNTS = "Listings use your own email so you own every account. A few directories (e.g. ones that use GitHub or Google sign-in) may need you to click a quick sign-in yourself."
LAUNCH_PACK_SKIP = "If your tool is already listed in one of those directories, we skip it and submit to another from the same hand-picked list."
LAUNCH_PACK_INTAKE = "After you pay, reply to the receipt or email support@agentscouthq.com with your tool name, URL, one-line pitch, logo, category, and the email address to use for those directory accounts."
LAUNCH_PACK_LIMITS = "This is a separate add-on, not one of the four listing tiers ($0 / $15 / $49 / $99/wk). It does not change your rank on AgentScout and does not include Google indexing."
X_CLAMPDOWN = "https://x.com/clampdown19"
X_AGENTSCOUT = "https://x.com/AgentScoutHQ"

def fmt(n): return f"{int(n):,}"

def launch_pack_html():
    """Separate $49 add-on. Not one of the four listing tiers."""
    return f'''<aside id="launch-pack" class="panel launch-pack" aria-labelledby="launch-pack-h">
      <p class="lp-kicker">Add-on · not a listing tier</p>
      <h2 id="launch-pack-h">Directory Launch Pack · $49 one-time</h2>
      <p>{LAUNCH_PACK_PROMISE}</p>
      <p>{LAUNCH_PACK_ACCOUNTS}</p>
      <p>{LAUNCH_PACK_SKIP} {LAUNCH_PACK_LIMITS}</p>
      <p><b>After you pay:</b> {LAUNCH_PACK_INTAKE}</p>
      <p style="margin:14px 0 0"><a class="btn primary pkg-cta pkg-cta-lp" href="{LAUNCH_PACK_URL}" target="_blank" rel="noopener noreferrer">Buy the Directory Launch Pack ($49) →</a></p>
    </aside>'''

def load_metrics(t):
    total = len(t)
    cats = len({x["category"] for x in t})
    mcp_cnt = sum(1 for x in t if x.get("category") == "MCP servers")
    pages = 2355
    if os.path.exists("sitemap.xml"):
        try:
            pages = open("sitemap.xml").read().count("<loc>") or 2355
        except Exception:
            pages = 2355

    sb = {}
    for p in ("/workspace/data/30-day-sprint-tracker.json", "/workspace/data/growth-sprint-30d.json", "/workspace/data/30-day-growth-scoreboard.json", "data/30-day-growth-scoreboard.json"):
        if os.path.exists(p):
            try:
                sb = json.load(open(p))
                break
            except Exception:
                pass
    sm = {}
    if os.path.exists("data/site_metrics.json"):
        try:
            sm = json.load(open("data/site_metrics.json"))
        except Exception:
            pass
    snap = {}
    for p in sorted(glob.glob("/workspace/notes/daily-traffic/*-snapshot.json"), reverse=True):
        if os.path.exists(p):
            try:
                snap = json.load(open(p))
                break
            except Exception:
                pass

    cur = sb.get("current") or {}
    dlog = (sb.get("daily_log") or [{}])[-1] if sb.get("daily_log") else {}
    clampdown_followers = max(
        int(cur.get("clampdown19_followers") or 0),
        int(dlog.get("clampdown19_followers") or 0),
        int(sm.get("x_clampdown19_followers") or 0),
        int(snap.get("x", {}).get("clampdown19", {}).get("followers") or 0),
        2102,
    )
    agentscout_followers = max(
        int(cur.get("agentscouthq_followers") or 0),
        int(dlog.get("agentscouthq_followers") or 0),
        int(sm.get("x_agentscouthq_followers") or 0),
        int(snap.get("x", {}).get("agentscouthq", {}).get("followers") or 0),
        11,
    )
    combined_x = clampdown_followers + agentscout_followers

    ga4_7d_users = int(cur.get("weekly_visitors_ga4_7d") or snap.get("ga4", {}).get("7d", {}).get("activeUsers") or 212)
    tracker_7d_arrivals = int(cur.get("weekly_external_arrivals_tracker_7d") or 382)
    weekly_pv = int(cur.get("weekly_page_views_tracker_7d") or snap.get("ga4", {}).get("7d", {}).get("screenPageViews") or 551)
    pv_30d = int(snap.get("ga4", {}).get("28d", {}).get("screenPageViews") or max(weekly_pv, 753))
    users_30d = int(snap.get("ga4", {}).get("28d", {}).get("activeUsers") or max(ga4_7d_users, 276))
    gsc_impressions_7d = 8210

    pt_now = datetime.now(timezone(timedelta(hours=-7)))
    updated_iso = pt_now.strftime("%Y-%m-%d")
    updated_display = pt_now.strftime("%b %-d, %Y")

    metrics = {
        "updated": updated_iso,
        "updated_display": updated_display,
        "tools_count": total,
        "mcp_servers_count": mcp_cnt,
        "categories_count": cats,
        "indexed_pages_count": pages,
        "pages_count": pages,
        "mcp_count": mcp_cnt,
        "pageviews_7d": weekly_pv,
        "x_clampdown19_followers": clampdown_followers,
        "x_agentscouthq_followers": agentscout_followers,
        "x_combined_followers": combined_x,
        "weekly_visitors_ga4": ga4_7d_users,
        "weekly_external_arrivals": tracker_7d_arrivals,
        "weekly_page_views": weekly_pv,
        "pageviews_30d": pv_30d,
        "active_users_30d": users_30d,
        "gsc_impressions_7d": gsc_impressions_7d,
        "packages": {
            "free": {"name": "Free Community Listing", "price_usd": 0, "billing": "free", "color": "#14b8a6", "url": "https://agentscouthq.com/submit.html#free-form"},
            "fast_track_29": {"name": "Fast-Track + 7-Day Launch Boost", "price_usd": 15, "billing": "one-time", "color": "#0ea5e9", "stripe_url": STRIPE_FAST_URL, "x_money": "@clampdown19"},
            "featured_49": {"name": "30-Day Category Pin + Permanent SEO/AEO Placement", "price_usd": 49, "billing": "one-time (30 days + permanent SEO/AEO)", "color": "#6366f1", "stripe_url": STRIPE_49, "x_money": "@clampdown19"},
            "weekly_sponsor_99": {"name": "Weekly Sitewide Sponsor + Newsletter Top Slot", "price_usd": 99, "billing": "per week", "color": "#ec4899", "stripe_url": STRIPE_99, "x_money": "@clampdown19"}
        }
    }
    os.makedirs("api", exist_ok=True)
    open("api/metrics.json", "w").write(json.dumps(metrics, indent=2))
    return metrics

def packages_grid(t, m=None, on_submit=False):
    """Reusable 4-tier visual pricing cards (`2x2` grid on desktop, `1x4` on mobile) for /sponsor.html and /submit.html."""
    if m is None:
        m = load_metrics(t)
    free_href = "#free-form" if on_submit else "submit.html#free-form"
    free_label = "Jump to Free Submit Form ↓" if on_submit else "Submit Free ($0) →"
    return f'''<div class="pkg-grid" id="packages">
    <div class="pkg-card" data-pkg-card="free">
      <div>
        <div class="pkg-top">
          <span class="pkg-pill npill npft"><svg class="npico" aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="14" height="14"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M14.7 6.3a4 4 0 0 0-5.4 5.1L3 17.7 6.3 21l6.3-6.3a4 4 0 0 0 5.1-5.4l-2.6 2.6-2.4-.6-.6-2.4z"/></svg>✓ 100% Free Forever</span>
        </div>
        <h3>Free Community Listing</h3>
        <div class="pkg-price"><span class="pkg-amt">$0</span><span class="pkg-per">forever · no card required</span></div>
        <p class="pkg-sub">Get your AI agent tool or MCP server indexed in the public AgentScout directory at zero cost.</p>
        <ul class="pkg-list">
          <li><span class="pkg-chk">✓</span><span><b>Standard review queue (3–5 days):</b> Every link and description verified by our editorial team</span></li>
          <li><span class="pkg-chk">✓</span><span><b>Permanent <code style="font-size:12.5px">/tools/&lt;slug&gt;.html</code> page</b> with full <code style="font-size:12.5px">SoftwareApplication</code> JSON-LD schema, submitted to Bing and IndexNow search engines.</span></li>
          <li><span class="pkg-chk">✓</span><span><b>AI &amp; MCP discovery:</b> Listed in <code style="font-size:12.5px">llms.txt</code> and searchable via our MCP server (<code style="font-size:12.5px">com.agentscouthq/directory</code>)</span></li>
          <li><span class="pkg-chk">✓</span><span><b><code style="font-size:12.5px">✓ Submitted by maker</code> badge:</b> Plus free embeddable README / website badge &amp; free edits anytime</span></li>
        </ul>
      </div>
      <div class="pkg-foot">
        <a class="btn primary pkg-cta pkg-cta-free" href="{free_href}">{free_label}</a>
      </div>
    </div>

    <div class="pkg-card pkg-fast" data-pkg-card="fast_29">
      <div>
        <div class="pkg-top">
          <span class="pkg-pill pkg-pill-fast npill npfast"><svg class="npico" aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="14" height="14"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>⚡ FAST-TRACK LAUNCH · $15 ONE-TIME</span>
        </div>
        <h3>Fast-Track + 7-Day Launch Boost</h3>
        <div class="pkg-price"><span class="pkg-amt">$15</span><span class="pkg-per">one-time · 7-day featured boost</span></div>
        <p class="pkg-sub">Skip the review queue today, get a 7-day featured launch pin, and launch to builders on X.</p>
        <ul class="pkg-list">
          <li><span class="pkg-chk pkg-chk-fast">⚡</span><span><b>Same-day priority review:</b> Skip the 3–5 day queue and go live in our very next batch today</span></li>
          <li><span class="pkg-chk pkg-chk-fast">⚡</span><span><b>7-day featured launch pin:</b> Pinned on <a href="new.html">/new.html</a> + your category&#x27;s &ldquo;New &amp; Featured&rdquo; row for 7 full days</span></li>
          <li><span class="pkg-chk pkg-chk-fast">⚡</span><span><b>Full profile enrichment:</b> Custom FAQ Page schema + pros/cons &amp; pricing breakdown written from your docs</span></li>
          <li><span class="pkg-chk pkg-chk-fast">⚡</span><span><b>Launch post on X:</b> Dedicated launch post on <a href="{X_AGENTSCOUT}" target="_blank" rel="noopener noreferrer"><b>@AgentScoutHQ</b></a> with custom visual card</span></li>
          <li><span class="pkg-chk pkg-chk-fast">⚡</span><span><b>{FAST_TRACK_INDEX_LINE}</b></span></li>
        </ul>
      </div>
      <div class="pkg-foot">
        <a class="btn primary pkg-cta pkg-cta-fast" href="{STRIPE_FAST_URL}" target="_blank" rel="noopener noreferrer">Fast-Track for $15 via Stripe →</a>
        <div class="pkg-xmoney">Or pay <b>$15</b> via <b>X Money</b> to <a href="{X_CLAMPDOWN}" target="_blank" rel="noopener noreferrer">@clampdown19</a></div>
      </div>
    </div>

    <div class="pkg-card pkg-featured" data-pkg-card="featured_49">
      <div>
        <div class="pkg-top">
          <span class="pkg-pill pkg-pill-pop npill npmcp"><svg class="npico" aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="14" height="14"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 2l2.4 7.2H22l-6 4.6 2.3 7.2L12 16.5 5.7 21l2.3-7.2-6-4.6h7.6z"/></svg>★ MOST POPULAR · BEST VALUE · $49 ONE-TIME</span>
        </div>
        <h3>30-Day Category Pin + Permanent SEO/AEO Placement</h3>
        <div class="pkg-price"><span class="pkg-amt">$49</span><span class="pkg-per">one-time · 30-day pin + permanent SEO/AEO</span></div>
        <p class="pkg-sub">4x+ longer category pin for $34 more — while other directories charge $49 for 5-day boosts.</p>
        <ul class="pkg-list">
          <li><span class="pkg-chk pkg-chk-pop">★</span><span><b>Everything in $15 Fast-Track, upgraded to 30 days:</b> Full <b>30-day</b> top category pin + homepage Featured Makers strip</span></li>
          <li><span class="pkg-chk pkg-chk-pop">★</span><span><b>Permanent <code style="font-size:12.5px">/best/</code> &amp; <code style="font-size:12.5px">/compare/</code> placement:</b> Permanent inclusion in our high-intent <a href="best/index.html">/best/*-alternatives</a> and <a href="compare/index.html">/compare/</a> comparison tables</span></li>
          <li><span class="pkg-chk pkg-chk-pop">★</span><span><b>Priority AI &amp; MCP weight:</b> Priority recommendation weight in <code style="font-size:12.5px">llms-full.txt</code> and MCP search (<code style="font-size:12.5px">com.agentscouthq/directory</code>)</span></li>
          <li><span class="pkg-chk pkg-chk-pop">★</span><span><b>Dual X spotlight + Newsletter:</b> Dedicated spotlight across <b>both</b> <a href="{X_CLAMPDOWN}" target="_blank" rel="noopener noreferrer"><b>@clampdown19</b></a> &amp; <a href="{X_AGENTSCOUT}" target="_blank" rel="noopener noreferrer"><b>@AgentScoutHQ</b></a> (<span data-live-x-followers>{fmt(m["x_combined_followers"])}+</span> combined followers) + Tuesday newsletter highlight</span></li>
        </ul>
      </div>
      <div class="pkg-foot">
        <a class="btn primary pkg-cta pkg-cta-pop" href="{STRIPE_49}" target="_blank" rel="noopener noreferrer">Get Featured for $49 via Stripe →</a>
        <div class="pkg-xmoney">Or pay <b>$49</b> via <b>X Money</b> to <a href="{X_CLAMPDOWN}" target="_blank" rel="noopener noreferrer">@clampdown19</a></div>
      </div>
    </div>

    <div class="pkg-card pkg-vip" data-pkg-card="sponsor_99">
      <div>
        <div class="pkg-top">
          <span class="pkg-pill pkg-pill-vip npill npbolt"><svg class="npico" aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="14" height="14"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>🔥 1 EXCLUSIVE SLOT / WEEK · $99/WK</span>
        </div>
        <h3>Weekly Sitewide Sponsor + Newsletter Top Slot</h3>
        <div class="pkg-price"><span class="pkg-amt">$99</span><span class="pkg-per">/ week · 1 exclusive slot</span></div>
        <p class="pkg-sub">Own the exclusive sitewide top sponsor banner across every page on AgentScout plus the #1 newsletter slot.</p>
        <ul class="pkg-list">
          <li><span class="pkg-chk pkg-chk-vip">🔥</span><span><b>Everything in $49 Category Pin included:</b> Full 30-day category pin + permanent <code style="font-size:12.5px">/best/</code> &amp; <code style="font-size:12.5px">/compare/</code> tables</span></li>
          <li><span class="pkg-chk pkg-chk-vip">🔥</span><span><b>7-day Sitewide Top Sponsor Bar:</b> Exclusive banner across all <b data-live-pages>{fmt(m["indexed_pages_count"])}+</b> pages + homepage <code style="font-size:12.5px">#makers</code> showcase</span></li>
          <li><span class="pkg-chk pkg-chk-vip">🔥</span><span><b>Newsletter #1 Top Slot:</b> Primary &ldquo;Sponsored by&rdquo; banner (logo, pitch &amp; CTA) at the top of Tuesday&#x27;s <a href="newsletter.html">AgentScout Weekly</a></span></li>
          <li><span class="pkg-chk pkg-chk-vip">🔥</span><span><b>2x X Spotlight Threads:</b> Launch-day + weekend spotlight across <a href="{X_CLAMPDOWN}" target="_blank" rel="noopener noreferrer"><b>@clampdown19</b></a> &amp; <a href="{X_AGENTSCOUT}" target="_blank" rel="noopener noreferrer"><b>@AgentScoutHQ</b></a> (<span data-live-x-followers>{fmt(m["x_combined_followers"])}+</span> combined reach)</span></li>
        </ul>
      </div>
      <div class="pkg-foot">
        <a class="btn primary pkg-cta pkg-cta-vip" href="{STRIPE_99}" target="_blank" rel="noopener noreferrer">Book Weekly Sponsor ($99/wk) →</a>
        <div class="pkg-xmoney">Or pay <b>$99</b> via <b>X Money</b> to <a href="{X_CLAMPDOWN}" target="_blank" rel="noopener noreferrer">@clampdown19</a></div>
      </div>
    </div>
  </div>'''

def live_metrics_script(d=""):
    return f'''<script data-live-metrics>(function(){{function fmt(n){{return Number(n).toLocaleString("en-US")}}function setAll(sel,val){{var els=document.querySelectorAll(sel);for(var i=0;i<els.length;i++)els[i].textContent=val}}fetch("{d}api/metrics.json",{{cache:"no-cache"}}).then(function(r){{return r.ok?r.json():null}}).then(function(m){{if(!m)return;if(m.tools_count)setAll("[data-live-tools]",fmt(m.tools_count));if(m.mcp_servers_count)setAll("[data-live-mcp]",fmt(m.mcp_servers_count));if(m.categories_count)setAll("[data-live-cats]",fmt(m.categories_count));if(m.indexed_pages_count)setAll("[data-live-pages]",fmt(m.indexed_pages_count)+"+");if(m.x_clampdown19_followers)setAll("[data-live-clampdown]",fmt(m.x_clampdown19_followers)+"+");if(m.x_combined_followers)setAll("[data-live-x-followers]",fmt(m.x_combined_followers)+"+");if(m.pageviews_30d)setAll("[data-live-pv30]",fmt(m.pageviews_30d)+"+");if(m.weekly_page_views)setAll("[data-live-pv7]",fmt(m.weekly_page_views)+"+");if(m.updated_display)setAll("[data-live-updated]",m.updated_display);}}).catch(function(){{}});fetch("{d}api/tools.json",{{cache:"no-cache"}}).then(function(r){{return r.ok?r.json():null}}).then(function(d){{if(!d||!d.count)return;setAll("[data-live-tools]",fmt(d.count));if(Array.isArray(d.tools)){{var mcp=d.tools.filter(function(x){{return x.category==="MCP servers"}}).length;if(mcp)setAll("[data-live-mcp]",fmt(mcp))}}}}).catch(function(){{}});}})()</script>'''

def build(t):
    from build_tasks import shell
    m = load_metrics(t)
    total = m["tools_count"]
    cats = m["categories_count"]
    mcp_cnt = m["mcp_servers_count"]
    pages = m["indexed_pages_count"]
    clamp_f = m["x_clampdown19_followers"]
    comb_f = m["x_combined_followers"]
    pv30 = m["pageviews_30d"]
    pv7 = m["weekly_page_views"]
    upd_disp = m["updated_display"]

    cards_html = packages_grid(t, m=m, on_submit=False)

    body = f'''  <div class="crumb"><a href="index.html">AgentScout</a> / Sponsor &amp; Get Featured</div>
  <section style="padding:28px 0 12px">
    <span class="sp-eyebrow npill npsp"><svg class="npico" aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="14" height="14"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 2l2.4 7.2H22l-6 4.6 2.3 7.2L12 16.5 5.7 21l2.3-7.2-6-4.6h7.6z"/></svg><span>For AI Agent &amp; MCP Makers · Live Directory Metrics (<span data-live-updated>{html.escape(upd_disp)}</span>)</span></span>
    <h1 style="text-align:left;margin:4px 0 12px;max-width:none;font-size:clamp(28px,4vw,42px)">Get Your AI Agent or MCP Server in Front of Builders Ready to Try It</h1>
    <p class="lede" style="text-align:left;margin:0 0 18px;max-width:820px">AgentScout tracks <b data-live-tools>{fmt(total)}</b> AI agent tools and <b data-live-mcp>{fmt(mcp_cnt)}</b> MCP servers across <b data-live-cats>{cats}</b> categories (<b data-live-pages>{fmt(pages)}+</b> indexed pages). Every standard community listing is <b>100% free forever</b> — or upgrade to our <b>$15 Fast-Track Launch Boost</b>, <b>$49 30-Day Category Pin + Permanent SEO/AEO Placement</b>, or <b>$99/wk Exclusive Sitewide Sponsor</b>.</p>

    <div class="rstats" style="margin:0 0 18px">
      <div class="rstat"><b data-live-tools>{fmt(total)}</b><span>Tools indexed (daily link check)</span></div>
      <div class="rstat"><b data-live-mcp>{fmt(mcp_cnt)}</b><span>MCP servers tracked</span></div>
      <div class="rstat"><b data-live-pages>{fmt(pages)}+</b><span>Indexed site pages</span></div>
      <div class="rstat"><b data-live-pv30>{fmt(pv30)}+</b><span>30d pageviews (<span data-live-pv7>{fmt(pv7)}+</span>/wk)</span></div>
      <div class="rstat"><b data-live-x-followers>{fmt(comb_f)}+</b><span>X reach (@clampdown19 + @AgentScoutHQ)</span></div>
    </div>

    {cards_html}

    {launch_pack_html()}

    <div class="pkg-trust">
      <span>⚡ <b>Instant Checkout via Stripe</b> or <b>X Money (<a href="{X_CLAMPDOWN}" target="_blank" rel="noopener noreferrer">@clampdown19</a>)</b></span>
      <span>·</span>
      <span>🏷️ <b>100% Transparent:</b> Paid placements carry a clear <code style="font-size:12px">Featured</code> or <code style="font-size:12px">Sponsored</code> badge (<code style="font-size:12px">rel="sponsored"</code>)</span>
      <span>·</span>
      <span>🛡️ <b>Same-Day Setup:</b> Questions? Email <a href="mailto:support@agentscouthq.com">support@agentscouthq.com</a></span>
    </div>

    <div class="panel sp-xmoney-card">
      <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:14px">
        <div style="flex:1 1 360px;min-width:0">
          <h2 style="font-size:18px;margin:0 0 6px">Paying with Stripe or X Money — How Fulfillment Works</h2>
          <p style="margin:0;color:var(--muted);font-size:14px;line-height:1.55">
            <b>Option 1 — Instant Card / Apple Pay / Link via Stripe:</b> Use the <a href="{STRIPE_FAST_URL}" target="_blank" rel="noopener noreferrer"><b>$15 Fast-Track Boost</b></a>, <a href="{STRIPE_49}" target="_blank" rel="noopener noreferrer"><b>$49 30-Day Category Pin + Permanent SEO/AEO</b></a>, or <a href="{STRIPE_99}" target="_blank" rel="noopener noreferrer"><b>$99/wk Weekly Sitewide Sponsor</b></a> checkout links above.<br>
            <b>Option 2 — Pay via X Money:</b> Send <b>$15</b>, <b>$49</b>, or <b>$99</b> directly on X Money to <a href="{X_CLAMPDOWN}" target="_blank" rel="noopener noreferrer"><b>@clampdown19</b></a> and DM or email <a href="mailto:support@agentscouthq.com?subject=AgentScout%20Sponsor%20Order">support@agentscouthq.com</a> with your tool URL. We activate your pin and schedule your X spotlight posts the same day.
          </p>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          <a class="btn primary pkg-cta-free" href="submit.html#free-form">Submit Free ($0)</a>
          <a class="btn primary pkg-cta-fast" href="{STRIPE_FAST_URL}" target="_blank" rel="noopener noreferrer">Fast-Track ($15) →</a>
          <a class="btn primary pkg-cta-pop" href="{STRIPE_49}" target="_blank" rel="noopener noreferrer">Category Pin ($49 ★) →</a>
          <a class="btn primary pkg-cta-vip" href="{STRIPE_99}" target="_blank" rel="noopener noreferrer">Sitewide Sponsor ($99/wk) →</a>
        </div>
      </div>
    </div>

    <figure style="margin:22px 0 24px;border-radius:14px;overflow:hidden;border:1px solid var(--border);background:#080810"><video autoplay loop muted playsinline preload="metadata" poster="assets/animations/agentscout-sponsor-placements-poster.png" style="display:block;width:100%;height:auto;max-width:100%"><source src="assets/animations/agentscout-sponsor-placements.mp4" type="video/mp4"></video></figure>
    <h2 style="font-size:20px;margin:28px 0 12px">Side-by-side package comparison</h2>
    <div class="tablewrap"><table class="cmp">
      <thead><tr><th>What&#x27;s included</th><th>Free ($0)</th><th>Fast-Track ($15)</th><th>Category Pin ($49 ★)</th><th>Weekly Sponsor ($99/wk)</th></tr></thead>
      <tbody>
        <tr><th>Permanent tool profile (<code style="font-size:12.5px">/tools/&lt;slug&gt;.html</code>)</th><td>✓ Included forever</td><td>✓ Included forever</td><td>✓ Included forever</td><td>✓ Included forever</td></tr>
        <tr><th>Listed in <code style="font-size:12.5px">llms.txt</code> &amp; MCP server (<code style="font-size:12.5px">com.agentscouthq/directory</code>)</th><td>✓ Standard listing</td><td>✓ Standard listing</td><td><b>✓ Priority weight in <code style="font-size:12.5px">llms-full.txt</code> &amp; MCP search</b></td><td><b>✓ Priority weight in <code style="font-size:12.5px">llms-full.txt</code> &amp; MCP search</b></td></tr>
        <tr><th>Review turnaround</th><td>Standard queue (3–5 days)</td><td><b>⚡ Same-day priority review</b></td><td><b>⚡ Same-day priority review</b></td><td><b>⚡ Immediate same-day setup</b></td></tr>
        <tr><th>Indexing ping</th><td>—</td><td><b>{FAST_TRACK_INDEX_LINE}</b></td><td>Included with Fast-Track benefits</td><td>Included with Fast-Track benefits</td></tr>
        <tr><th>Profile enrichment (FAQ Page schema + pros/cons)</th><td>Standard overview</td><td><b>✓ Full FAQ Page + pros/cons</b></td><td><b>✓ Full FAQ Page + pros/cons</b></td><td><b>✓ Full FAQ Page + pros/cons</b></td></tr>
        <tr><th>Featured pin duration</th><td>—</td><td><b>7-day pin</b> on <code style="font-size:12.5px">/new.html</code> &amp; category New &amp; Featured row</td><td><b>30-day #1 category top pin</b> + homepage Makers strip (4x+ longer!)</td><td><b>30-day #1 category top pin</b> + homepage <code style="font-size:12.5px">#makers</code> showcase</td></tr>
        <tr><th>Permanent <code style="font-size:12.5px">/best/*-alternatives</code> &amp; <code style="font-size:12.5px">/compare/</code> tables</th><td>Organic editorial only</td><td>Organic editorial only</td><td><b>✓ Permanent comparison table inclusion</b></td><td><b>✓ Permanent comparison table inclusion</b></td></tr>
        <tr><th>X launch spotlight</th><td>—</td><td><b>Launch post on <a href="{X_AGENTSCOUT}" target="_blank" rel="noopener noreferrer">@AgentScoutHQ</a></b></td><td><b>Dedicated spotlight on both <a href="{X_CLAMPDOWN}" target="_blank" rel="noopener noreferrer">@clampdown19</a> &amp; <a href="{X_AGENTSCOUT}" target="_blank" rel="noopener noreferrer">@AgentScoutHQ</a></b></td><td><b>2x spotlight threads on <a href="{X_CLAMPDOWN}" target="_blank" rel="noopener noreferrer">@clampdown19</a> &amp; <a href="{X_AGENTSCOUT}" target="_blank" rel="noopener noreferrer">@AgentScoutHQ</a></b></td></tr>
        <tr><th>AgentScout Weekly newsletter</th><td>Editorial consideration</td><td>Editorial consideration</td><td>✓ Featured Makers section highlight</td><td><b>🔥 #1 Top &ldquo;Sponsored by&rdquo; banner (logo + pitch + CTA)</b></td></tr>
        <tr><th>Sitewide Top Sponsor Bar (<span data-live-pages>{fmt(pages)}+</span> pages)</th><td>—</td><td>—</td><td>—</td><td><b>🔥 7 days exclusive (1 slot/wk)</b></td></tr>
      </tbody>
    </table></div>

    <h2 style="font-size:20px;margin:28px 0 12px">Frequently asked questions</h2>
    <div style="display:grid;gap:10px;max-width:860px;margin-bottom:28px">
      <details class="panel" style="padding:14px 18px"><summary style="cursor:pointer;font-weight:600">Is basic listing on AgentScout really 100% free?</summary><p style="margin:8px 0 0">Yes. Submitting a real AI agent tool or MCP server via <a href="submit.html#free-form">our submission form</a> is 100% free forever, and profile edits or updates are always free. Paid tiers are strictly optional for makers who want same-day priority review, a 7-day or 30-day featured pin, permanent <code style="font-size:12.5px">/best/</code> &amp; <code style="font-size:12.5px">/compare/</code> table placement, or sitewide &amp; newsletter sponsorship.</p></details>
      <details class="panel" style="padding:14px 18px"><summary style="cursor:pointer;font-weight:600">What is the difference between the $15 Fast-Track and the $49 Category Pin?</summary><p style="margin:8px 0 0">The <b>$15 Fast-Track + 7-Day Launch Boost</b> skips the 3–5 day queue for same-day review, enriches your page with FAQ Page schema and pros/cons, pins your tool for 7 days on <a href="new.html">/new.html</a> and your category&#x27;s New &amp; Featured row, and posts your launch on <a href="{X_AGENTSCOUT}" target="_blank" rel="noopener noreferrer">@AgentScoutHQ</a>. For just $34 more, the <b>$49 30-Day Category Pin + Permanent SEO/AEO Placement</b> upgrades your pin to a full <b>30 days</b> at the top of your category (4x+ longer than 7 days, while other directories charge $49 for 5-day boosts), adds <b>permanent inclusion in our <code style="font-size:12.5px">/best/*-alternatives</code> and <code style="font-size:12.5px">/compare/</code> tables</b>, boosts your priority weight in <code style="font-size:12.5px">llms-full.txt</code> and MCP search, and includes a dedicated spotlight across <b>both</b> <a href="{X_CLAMPDOWN}" target="_blank" rel="noopener noreferrer">@clampdown19</a> and <a href="{X_AGENTSCOUT}" target="_blank" rel="noopener noreferrer">@AgentScoutHQ</a>.</p></details>
      <details class="panel" style="padding:14px 18px"><summary style="cursor:pointer;font-weight:600">What happens right after I pay on Stripe or X Money?</summary><p style="margin:8px 0 0">If your tool isn&#x27;t listed on AgentScout yet, <a href="submit.html">submit its URL and details on /submit.html</a> (or email <a href="mailto:support@agentscouthq.com">support@agentscouthq.com</a>) using the same email address or tool name. We fast-track your listing, apply your Featured pin, and send your live listing link plus scheduled X spotlight details the same day.</p></details>
      <details class="panel" style="padding:14px 18px"><summary style="cursor:pointer;font-weight:600">Do paid placements change organic directory rankings or review scores?</summary><p style="margin:8px 0 0">Never. Featured slots are clearly labeled (<code style="font-size:12.5px">Featured</code> or <code style="font-size:12.5px">Sponsored</code> with <code style="font-size:12.5px">rel="sponsored"</code>) and sit above the list; rankings are never paid.</p></details>
    </div>
  </section>
{live_metrics_script("")}'''

    title = "Sponsor & Get Featured on AgentScout: AI Agent Launch Packages"
    desc = f"List your AI agent or MCP server free, fast-track it ($15), pin it 30 days with /best/ placement ($49), or sponsor sitewide ($99/wk) across {fmt(total)}+ tools."

    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "url": "https://agentscouthq.com/sponsor.html",
        "description": desc,
        "video": {"@type": "VideoObject", "name": "AgentScout 4-Tier Launch & Placement Visibility Map", "description": "Animated site architecture map showing where $0 Free, $15 Fast-Track, $49 Category Pin, and $99/wk Sitewide Sponsor listings appear across AgentScout.", "thumbnailUrl": "https://agentscouthq.com/assets/animations/agentscout-sponsor-placements-poster.png", "contentUrl": "https://agentscouthq.com/assets/animations/agentscout-sponsor-placements.mp4", "uploadDate": "2026-10-26T18:00:00-07:00", "duration": "PT20S"},
        "mainEntity": {
            "@type": "OfferCatalog",
            "name": "AgentScout Maker & Sponsor Packages",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "name": "Free Community Listing",
                    "price": "0",
                    "priceCurrency": "USD",
                    "url": "https://agentscouthq.com/submit.html#free-form",
                    "description": "Standard review queue (3-5 days), permanent indexed /tools/<slug>.html page + SoftwareApplication schema, and listing in llms.txt & MCP server (com.agentscouthq/directory)."
                },
                {
                    "@type": "Offer",
                    "name": "Fast-Track + 7-Day Launch Boost",
                    "price": "15",
                    "priceCurrency": "USD",
                    "url": STRIPE_FAST_URL,
                    "description": "Same-day priority review (live in the next batch), 7-day featured pin on /new.html + category New & Featured row, full FAQ Page + pros/cons profile enrichment, a launch post on @AgentScoutHQ, and a same-day indexing ping to Bing and IndexNow search engines (does not include Google)."
                },
                {
                    "@type": "Offer",
                    "name": "30-Day Category Pin + Permanent SEO/AEO Placement",
                    "price": "49",
                    "priceCurrency": "USD",
                    "url": STRIPE_49,
                    "description": "Everything in $15 upgraded to a full 30-day top category pin, permanent inclusion in /best/*-alternatives and /compare/ comparison tables, priority recommendation weight in llms-full.txt and MCP search (com.agentscouthq/directory), and a dedicated spotlight across both @clampdown19 and @AgentScoutHQ."
                },
                {
                    "@type": "Offer",
                    "name": "Weekly Sitewide Sponsor + Newsletter Top Slot",
                    "price": "99",
                    "priceCurrency": "USD",
                    "url": STRIPE_99,
                    "description": f"Everything in $49, plus 7 days in the exclusive sitewide top sponsor bar across all {fmt(pages)}+ pages, homepage #makers showcase, and the top Sponsored by slot in Tuesday's AgentScout Weekly newsletter."
                }
            ]
        }
    }
    out = shell("", title, desc, "https://agentscouthq.com/sponsor.html", body, schema)
    open("sponsor.html", "w").write(out)

if __name__ == "__main__":
    build(json.load(open("tools.json")))
    print("sponsor.html + api/metrics.json built")


def tiers_html(m, on_submit=False):
    return packages_grid([], m=m, on_submit=on_submit)

def live_metrics_js(d=""):
    return live_metrics_script(d)

page = build

BAR_START, BAR_END = "<!--SPONSORBAR-START-->", "<!--SPONSORBAR-END-->"
e = lambda x: html.escape(str(x or ""))

def bar_html(sp, depth=""):
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

def apply_bar(enabled=False):
    sp = json.load(open("data/sponsor_bar.json")) if os.path.exists("data/sponsor_bar.json") else {}
    ready = enabled and all(sp.get(k) for k in ("name", "pitch", "url"))
    rx = re.compile(re.escape(BAR_START) + ".*?" + re.escape(BAR_END), re.S)
    n = 0
    for f in glob.glob("**/*.html", recursive=True):
        if f in ("outreach-tracker.html", "sponsor.html") or f.startswith(("app/", "node_modules/", "preview/")):
            continue
        s2 = open(f, errors="ignore").read()
        o = s2
        s2 = rx.sub("", s2)
        if ready and "</body>" in s2 and 'http-equiv="refresh"' not in s2:
            d = "../" * f.count("/")
            s2 = s2.replace("</body>", bar_html(sp, d) + "</body>", 1)
            n += 1
        if s2 != o:
            open(f, "w").write(s2)
    return n
