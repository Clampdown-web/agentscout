"""Public Sponsor & Get Featured page (sponsor.html) + the sitewide sponsor bar component.
sponsor.html is a public, indexed page included in sitemap.xml, llms.txt, and the site footer + submit.html.
Offers 3 tiers:
1) Free Community Listing ($0) -> submit.html
2) Featured Listing & Category Boost ($49 one-time) -> Stripe Payment Link + X Money (@clampdown19)
3) Weekly Sitewide Sponsor + Newsletter Top Slot ($99/week) -> Stripe Payment Link + X Money (@clampdown19)

Sponsor bar: off until booked. To turn it on, set SPONSOR_ENABLED = True in build_site.py and fill data/sponsor_bar.json, then rebuild."""
import json,os,glob,re,html,datetime
from zoneinfo import ZoneInfo
import build_extras
B=build_extras.B; e=lambda s:html.escape(str(s))
PT=ZoneInfo("America/Los_Angeles")
MAIL="mailto:support@agentscouthq.com?subject=AgentScout%20Sponsorship"
STRIPE_FEATURED="https://buy.stripe.com/bJefZi4KT6lp9l3dPRe7m00"
STRIPE_WEEKLY="https://buy.stripe.com/6oU4gA2CL9xB2WFcLNe7m01"
BAR_START,BAR_END="<!--SPONSORBAR-START-->","<!--SPONSORBAR-END-->"
def _pt(ts):
    try: return datetime.datetime.strptime(ts,"%Y-%m-%dT%H:%M:%S%z").astimezone(PT).strftime("%b %-d, %Y, %-I:%M %p PT")
    except Exception: return ""
def _win(w):
    try:
        a,b=[datetime.date.fromisoformat(x) for x in w.split(" to ")]
        return (f"{a:%b} {a.day}–{b.day}, {b.year}" if a.month==b.month else f"{a:%b} {a.day} – {b:%b} {b.day}, {b.year}")
    except Exception: return e(w)
def _n(v): return f"{v:,}" if isinstance(v,int) else "Not available"
def bar_html(sp,depth=""):
    """Small fixed bar at the bottom of the page. position:fixed, so it never shifts the layout (no CLS); dismissible per visitor."""
    logo=f'<img src="{e(sp["logo"])}" alt="" width="20" height="20" style="border-radius:5px;flex:none">' if sp.get("logo") else ""
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
    sp=json.load(open("data/sponsor_bar.json")) if os.path.exists("data/sponsor_bar.json") else {}
    ready=enabled and all(sp.get(k) for k in ("name","pitch","url"))
    if enabled and not ready: print("build_sponsor: SPONSOR_ENABLED is on but data/sponsor_bar.json is incomplete; no bar rendered")
    rx=re.compile(re.escape(BAR_START)+".*?"+re.escape(BAR_END),re.S); n=0
    for f in glob.glob("**/*.html",recursive=True):
        if f in ("outreach-tracker.html","sponsor.html") or f.startswith(("app/","node_modules/","preview/")): continue
        s=open(f,errors="ignore").read(); o=s; s=rx.sub("",s)
        if ready and "</body>" in s and 'http-equiv="refresh"' not in s:
            d="../"*f.count("/"); s=s.replace("</body>",bar_html(sp,d)+"</body>",1); n+=1
        if s!=o: open(f,"w").write(s)
    return n
def tiers_html(n, nmcp, on_submit=False):
    """Reusable 3-tier package cards for sponsor.html and submit.html."""
    c_base='style="border:1px solid var(--line);border-radius:14px;background:var(--card);padding:20px 18px;box-shadow:var(--shadow);display:flex;flex-direction:column;justify-content:space-between;min-width:0;overflow-wrap:anywhere"'
    c_feat='style="border:2px solid var(--accent,#2563eb);border-radius:14px;background:var(--card);padding:20px 18px;box-shadow:var(--shadow);display:flex;flex-direction:column;justify-content:space-between;min-width:0;overflow-wrap:anywhere;position:relative"'
    ul_s='style="margin:12px 0 18px;padding-left:18px;font-size:14px;line-height:1.55"'
    t1_cta = ('<a class="btn" href="#sf" style="width:100%;justify-content:center;text-align:center">Use free form below ↓</a>'
              if on_submit else
              '<a class="btn" href="submit.html" style="width:100%;justify-content:center;text-align:center">Submit free →</a>')
    return (
      '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:16px;margin:18px 0 22px">'
      # Tier 1: Free Community Listing
      f'<div {c_base}><div>'
      '<div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)">Tier 1 · Community</div>'
      '<h3 style="font-size:18px;margin:6px 0 4px">Free Community Listing</h3>'
      '<div style="font-size:28px;font-weight:800;line-height:1.15;margin:6px 0">$0 <span style="font-size:13px;font-weight:500;color:var(--muted)">forever</span></div>'
      '<p class="muted" style="font-size:13.5px;margin:6px 0 0">Our default community tier for every real AI agent, MCP server, or AI tool.</p>'
      f'<ul {ul_s}>'
      '<li>Full directory listing on <b>agentscouthq.com</b>, reviewed in our daily maker batches and link-checked daily</li>'
      f'<li>Included in our public read-only MCP server (<b>{nmcp:,}</b> servers / <b>{n:,}</b> tools) and JSON API</li>'
      '<li>Eligible for the Tuesday <b>AgentScout Weekly</b> newsletter Maker Spotlight queue</li>'
      '</ul></div>'
      f'<div>{t1_cta}<p class="muted" style="font-size:12px;margin:8px 0 0;text-align:center">No card needed · Reviewed daily</p></div></div>'
      # Tier 2: Featured Listing & Category Boost
      f'<div {c_feat}><div>'
      '<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap">'
      '<span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--accent,#2563eb)">Tier 2 · Most Popular</span>'
      '<span class="b" style="font-size:11px;padding:2px 8px">One-time boost</span></div>'
      '<h3 style="font-size:18px;margin:6px 0 4px">Featured Listing &amp; Category Boost</h3>'
      '<div style="font-size:28px;font-weight:800;line-height:1.15;margin:6px 0">$49 <span style="font-size:13px;font-weight:500;color:var(--muted)">one-time</span></div>'
      '<p class="muted" style="font-size:13.5px;margin:6px 0 0">Priority same-day launch, 30-day category pin, and X spotlight post.</p>'
      f'<ul {ul_s}>'
      '<li><b>Priority same-day review &amp; enriched profile</b> (pricing breakdown, use cases, comparison &amp; alternatives placement)</li>'
      '<li><b>Pinned Featured badge</b> at the top of your category on <b>agentscouthq.com</b> for 30 days (<code style="font-size:12px">rel="sponsored"</code> disclosure; never alters editorial reviews)</li>'
      '<li><b>Dedicated spotlight post on X</b> across <b>@clampdown19</b> (2,095+ followers) and <b>@AgentScoutHQ</b></li>'
      '</ul></div>'
      f'<div><a class="btn primary" href="{STRIPE_FEATURED}" target="_blank" rel="noopener" style="width:100%;justify-content:center;text-align:center">Get Featured ($49) →</a>'
      '<p class="muted" style="font-size:12px;margin:8px 0 0;text-align:center">Or pay via <b>X Money</b> to <b>@clampdown19</b> — email <a href="mailto:support@agentscouthq.com">support@agentscouthq.com</a></p></div></div>'
      # Tier 3: Weekly Sitewide Sponsor + Newsletter Top Slot
      f'<div {c_base}><div>'
      '<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap">'
      '<span style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)">Tier 3 · Exclusive</span>'
      '<span class="b" style="font-size:11px;padding:2px 8px">1 sponsor at a time</span></div>'
      '<h3 style="font-size:18px;margin:6px 0 4px">Weekly Sitewide Sponsor + Newsletter Top Slot</h3>'
      '<div style="font-size:28px;font-weight:800;line-height:1.15;margin:6px 0">$99 <span style="font-size:13px;font-weight:500;color:var(--muted)">/ week</span></div>'
      '<p class="muted" style="font-size:13.5px;margin:6px 0 0">Maximum visibility across every page on AgentScout plus our Tuesday newsletter.</p>'
      f'<ul {ul_s}>'
      '<li><b>Everything in the Featured Listing &amp; Category Boost tier</b> (30-day category pin, enriched profile &amp; X spotlight)</li>'
      '<li><b>Exclusive Sitewide Sponsor Bar</b> at the bottom of all <b>2,320+ pages</b> on <b>agentscouthq.com</b> for 7 days (brand logo, 40-character pitch, and link)</li>'
      '<li><b>"Sponsored by" top banner</b> at the top of Tuesday\'s <b>AgentScout Weekly</b> Beehiiv newsletter issue</li>'
      '</ul></div>'
      f'<div><a class="btn primary" href="{STRIPE_WEEKLY}" target="_blank" rel="noopener" style="width:100%;justify-content:center;text-align:center">Book Weekly Sponsor ($99) →</a>'
      '<p class="muted" style="font-size:12px;margin:8px 0 0;text-align:center">Or pay via <b>X Money</b> to <b>@clampdown19</b> — email <a href="mailto:support@agentscouthq.com">support@agentscouthq.com</a></p></div></div>'
      '</div>'
    )
def page(t):
    st=json.load(open("data/sponsor_stats.json")) if os.path.exists("data/sponsor_stats.json") else {}
    n=len(t); nc=len({x["category"] for x in t}); nmcp=sum(1 for x in t if x.get("category")=="MCP servers")
    now=datetime.datetime.now(PT).strftime("%b %-d, %Y, %-I:%M %p PT")
    card='style="border:1px solid var(--line);border-radius:12px;background:var(--card);padding:16px 18px;box-shadow:var(--shadow);min-width:0;overflow-wrap:anywhere"'
    H2='style="font-size:19px;margin:34px 0 10px"'
    stat=lambda v,label,note:(f'<div {card}><div style="font-size:26px;font-weight:700;line-height:1.15">{v}</div>'
                              f'<div style="font-weight:600;margin-top:2px">{label}</div><div class="muted" style="font-size:12.5px;margin-top:4px">{note}</div></div>')
    wk=st.get("weekly_page_views")
    stats=(f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,190px),1fr));gap:12px">'
      +stat(f"{n:,}","tools & agents listed",f"Across {nc} categories, link-checked daily ({now}).")
      +stat("2,320+","indexed directory pages","Tool profiles, head-to-head comparisons, task guides, and role pages.")
      +stat(f"{nmcp:,}","MCP servers indexed","Searchable via our free public MCP server for Claude, Cursor & VS Code.")
      +stat("2,095+","X audience reach",f'Spotlight posts shared across @clampdown19 & @AgentScoutHQ'+(f' · {_n(wk)} 7-day site views' if isinstance(wk,int) else '')+'.')
      +'</div>')
    demo={"name":"Your brand","pitch":"your pitch, about 40 characters","url":"#","logo":""}
    barprev=bar_html(demo).replace(BAR_START,"").replace(BAR_END,"")
    barprev=re.sub(r'<script>.*?</script>','',barprev).replace('position:fixed;left:50%;bottom:12px;transform:translateX(-50%);z-index:60;','position:relative;margin:0 auto;width:max-content;max-width:100%;')
    barprev=re.sub(r'<a href="#"[^>]*>','<span style="display:flex;align-items:center;gap:8px;min-width:0">',barprev).replace('</span></a><button','</span></span><button')
    barprev=re.sub(r'<button type="button" aria-label="Hide sponsor".*?</button>','<span aria-hidden="true" style="flex:none;width:24px;height:24px;color:var(--muted);font-size:16px;line-height:24px;text-align:center">×</span>',barprev,flags=re.S)
    barprev=barprev.replace('id="sponsorbar" role="complementary"','role="img" aria-label="Preview of the sponsor bar: Your brand, your pitch"').replace(' onclick="try{localStorage.setItem(\'as_sponsorbar\',\'0\')}catch(e){}this.parentNode.remove()"',' tabindex="-1"').replace('href="#" target="_blank" rel="sponsored noopener"','href="#how" tabindex="-1"')
    nlprev=(f'<div {card}><div class="muted" style="font-size:12px;margin-bottom:8px">AgentScout Weekly newsletter · Tuesday issue</div>'
      '<div style="border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:12px 0;margin-bottom:10px">'
      '<div style="font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--faint)">Sponsored by</div>'
      '<div style="margin-top:4px"><b>Your brand</b>: your pitch, about 40 characters</div></div>'
      '<div class="muted" style="font-size:13px">…followed by the week\'s new AI agents, MCP servers, and maker launches.</div></div>')
    faq=[
      ("Is the basic listing on AgentScout really free?",
       f"Yes. Our Free Community Listing ($0) is and always will be free for real AI agents, MCP servers, and AI tools. Every free listing gets a dedicated profile page on agentscouthq.com, daily link checking, and inclusion in our public MCP server ({nmcp:,} servers / {n:,} tools)."),
      ("How fast do Featured Listings ($49) and Weekly Sponsorships ($99) go live?",
       "As soon as you complete checkout via Stripe (or send payment via X Money to @clampdown19), we review and enrich your tool profile the same day, activate your 30-day Featured category pin, and schedule your X spotlight post and weekly sitewide sponsor bar."),
      ("Can I pay with X Money instead of Stripe?",
       "Yes. You can pay $49 (Featured Listing & Category Boost) or $99 (Weekly Sitewide Sponsor + Newsletter Top Slot) via X Money directly to @clampdown19, then email support@agentscouthq.com with your tool URL and 40-character sponsor pitch."),
      ("Does sponsoring change editorial descriptions or rankings?",
       "Never. Sponsored placements carry a clear 'Featured' or 'Sponsor' badge and rel=\"sponsored\" on outbound links. Editorial descriptions, pricing verification, and comparison tables remain independent.")
    ]
    faq_html="".join(f'<details style="margin:0 0 10px;border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:var(--card)"><summary style="cursor:pointer;font-weight:600">{e(q)}</summary><p style="margin:8px 0 0;font-size:14px">{e(a)}</p></details>' for q,a in faq)
    body=(f'<div class="crumb"><a href="index.html">AgentScout</a> / Sponsor &amp; Get Featured</div>'
      f'<section style="padding-top:20px;text-align:left;max-width:980px;margin:0 auto">'
      f'<h1 style="text-align:left">Sponsor &amp; Get Featured on AgentScout</h1>'
      f'<p class="lede" style="margin-left:0;text-align:left">Get your AI agent, MCP server, or AI tool in front of developers, founders, and buyers comparing tools across <b>{n:,}</b> listings and <b>2,320+</b> pages. Basic community listings are always free.</p>'
      f'<h2 {H2} id="packages">Choose your package</h2>'
      +tiers_html(n, nmcp, on_submit=False)
      +f'<h2 {H2}>Directory reach at a glance</h2>{stats}'
      f'<h2 {H2} id="how">Placement previews</h2>'
      '<p>See how the <b>Weekly Sitewide Sponsor ($99/week)</b> placements look across the directory and newsletter:</p>'
      f'<p class="muted" style="margin:16px 0 8px;font-size:13px">1. Exclusive sitewide sponsor bar at the bottom of all 2,320+ pages (7 days)</p>'
      f'<div style="border:1px dashed var(--line);border-radius:12px;padding:22px 12px;overflow:hidden">{barprev}</div>'
      f'<p class="muted" style="margin:18px 0 8px;font-size:13px">2. "Sponsored by" top banner in Tuesday\'s AgentScout Weekly newsletter</p>{nlprev}'
      '<p style="margin-top:16px;font-size:14px">Sponsored placements are always labeled <b>Featured</b>, <b>Sponsor</b>, or <b>Sponsored by</b> and outbound links carry <code>rel="sponsored"</code>. Sponsorship never changes an editorial description, pricing check, or review.</p>'
      f'<h2 {H2} id="faq">Frequently asked questions</h2>{faq_html}'
      f'<div {card} style="border:1px solid var(--line);border-radius:12px;background:var(--card);padding:18px 20px;margin-top:28px;display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap">'
      '<div><div style="font-weight:700;font-size:16px">Questions or custom multi-week bundles?</div>'
      '<div class="muted" style="font-size:13.5px;margin-top:2px">Email <a href="'+MAIL+'">support@agentscouthq.com</a> or pay directly via Stripe or X Money (<b>@clampdown19</b>).</div></div>'
      f'<div style="display:flex;gap:10px;flex-wrap:wrap"><a class="btn primary" href="{STRIPE_FEATURED}" target="_blank" rel="noopener">Get Featured ($49) →</a>'
      f'<a class="btn" href="{STRIPE_WEEKLY}" target="_blank" rel="noopener">Book Weekly Sponsor ($99) →</a></div></div>'
      '</section>')
    title="Sponsor & Get Featured on AgentScout · Pricing & Packages"
    desc=f"List your AI tool free ($0), boost with a Featured Listing ($49), or book the exclusive Weekly Sitewide Sponsor Bar + Newsletter Top Slot ($99/wk) across {n:,} tools."[:158]
    canon=B+"sponsor.html"
    ld={"@context":"https://schema.org","@graph":[
        {"@type":"WebPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
        {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}
    ]}
    s=build_extras.shell("",title,desc,canon,body,ld)
    open("sponsor.html","w").write(s)
    return "sponsor.html"
if __name__=="__main__":
    t=json.load(open("tools.json")); page(t)
    import build_tasks; build_tasks.sitewide(t)
    print("sponsor.html built; bar pages:",apply_bar(False))
