"""Hidden sponsor page (sponsor.html) + the sponsor bar component (added Oct 18, 2026 PT).
sponsor.html: prepared, NOT published as a public page. It is noindex,nofollow, never added to sitemap.xml or llms.txt,
and nothing on the site links to it (recheck treats it like outreach-tracker.html). Share the URL by hand when needed.
It is not listed in robots.txt on purpose: robots.txt is public, so a Disallow line would advertise the URL, and a
crawler blocked by robots.txt can't see the noindex tag. noindex + no links is the stronger way to keep it hidden.
Stats are real and come from data/sponsor_stats.json (scripts/sponsor_stats.py) plus the tools.json count at build time.
A missing number shows as "Not available"; nothing is estimated.

Sponsor bar: off. To turn it on, set SPONSOR_ENABLED = True in build_site.py and fill data/sponsor_bar.json, then rebuild.
apply_bar(enabled) adds the bar to every page when on, and removes any bar when off, so the flag is the only switch."""
import json,os,glob,re,html,datetime
from zoneinfo import ZoneInfo
import build_extras
B=build_extras.B; e=lambda s:html.escape(str(s))
PT=ZoneInfo("America/Los_Angeles")
MAIL="mailto:support@agentscouthq.com?subject=Sponsor%20AgentScout"
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
def page(t):
    st=json.load(open("data/sponsor_stats.json")) if os.path.exists("data/sponsor_stats.json") else {}
    n=len(t); nc=len({x["category"] for x in t})
    now=datetime.datetime.now(PT).strftime("%b %-d, %Y, %-I:%M %p PT")
    card='style="border:1px solid var(--line);border-radius:12px;background:var(--card);padding:16px 18px;box-shadow:var(--shadow)"'
    H2='style="font-size:19px;margin:34px 0 10px"'
    stat=lambda v,label,note:(f'<div {card}><div style="font-size:28px;font-weight:700;line-height:1.15">{v}</div>'
                              f'<div style="font-weight:600;margin-top:2px">{label}</div><div class="muted" style="font-size:12.5px;margin-top:4px">{note}</div></div>')
    wk=st.get("weekly_page_views"); sub=st.get("newsletter_subscribers")
    stats=(f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px">'
      +stat(_n(wk),"page views in the last 7 days",f'Real visitors only: our own and automated traffic is excluded. Cloudflare Analytics Engine, {_win(st.get("weekly_window",""))}{", as of "+_pt(st["weekly_as_of"]) if st.get("weekly_as_of") else ""}.')
      +stat(f"{n:,}","tools listed",f"In {nc} categories, counted from the live directory at build time ({now}).")
      +stat(_n(sub),"newsletter subscribers",f'Active subscribers on beehiiv{", as of "+_pt(st["subscribers_as_of"]) if st.get("subscribers_as_of") else ""}.')
      +'</div><p class="muted" style="font-size:13px;margin:10px 0 0">These numbers are pulled from our own analytics and beehiiv when the site is built. They are not rounded up or estimated.</p>')
    demo={"name":"Your brand","pitch":"your pitch, about 40 characters","url":"#","logo":""}
    barprev=bar_html(demo).replace(BAR_START,"").replace(BAR_END,"")
    barprev=re.sub(r'<script>.*?</script>','',barprev).replace('position:fixed;left:50%;bottom:12px;transform:translateX(-50%);z-index:60;','position:relative;margin:0 auto;width:max-content;')
    barprev=re.sub(r'<a href="#"[^>]*>','<span style="display:flex;align-items:center;gap:8px;min-width:0">',barprev).replace('</span></a><button','</span></span><button')
    barprev=re.sub(r'<button type="button" aria-label="Hide sponsor".*?</button>','<span aria-hidden="true" style="flex:none;width:24px;height:24px;color:var(--muted);font-size:16px;line-height:24px;text-align:center">×</span>',barprev,flags=re.S)
    barprev=barprev.replace('id="sponsorbar" role="complementary"','role="img" aria-label="Preview of the sponsor bar: Your brand, your pitch"').replace(' onclick="try{localStorage.setItem(\'as_sponsorbar\',\'0\')}catch(e){}this.parentNode.remove()"',' tabindex="-1"').replace('href="#" target="_blank" rel="sponsored noopener"','href="#how" tabindex="-1"')
    nlprev=(f'<div {card}><div class="muted" style="font-size:12px;margin-bottom:8px">AgentScout newsletter · New this week</div>'
      '<div style="border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:12px 0;margin-bottom:10px">'
      '<div style="font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--faint)">Sponsored by</div>'
      '<div style="margin-top:4px"><b>Your brand</b>: your pitch, about 40 characters</div></div>'
      '<div class="muted" style="font-size:13px">…then the week\'s new agent tools, launches and news.</div></div>')
    body=(f'<div class="crumb"><a href="index.html">AgentScout</a> / Sponsor</div><section style="padding-top:20px;text-align:left;max-width:820px">'
      f'<h1 style="text-align:left">Sponsor AgentScout</h1><p class="lede" style="margin-left:0;text-align:left">One sponsor at a time, in front of people who come to AgentScout to find an AI agent or agent tool to actually use.</p>'
      f'<h2 {H2}>Who visits</h2><p>Builders and everyday users comparing AI agents: coding agents, MCP servers, browser and computer use, voice, research, and business agents. They arrive with a job to do and leave through a tool\'s official link. AgentScout is a curated, link-checked directory of {n:,} tools, updated daily.</p>'
      f'<h2 {H2}>The numbers</h2>{stats}'
      f'<h2 {H2} id="how">What you get</h2><p>One slot type, two placements, for one week:</p><ul>'
      '<li><b>The sponsor bar</b>, a small bar at the bottom of every page on agentscouthq.com: your name, a short pitch and a link. Visitors can hide it.</li>'
      '<li><b>A spot in the weekly newsletter</b>, a "Sponsored by" line at the top of that week\'s issue.</li></ul>'
      f'<p class="muted" style="margin:16px 0 8px;font-size:13px">The sponsor bar, at the bottom of every page</p>'
      f'<div style="border:1px dashed var(--line);border-radius:12px;padding:22px 12px;overflow:hidden">{barprev}</div>'
      f'<p class="muted" style="margin:18px 0 8px;font-size:13px">The newsletter, once a week</p>{nlprev}'
      '<p style="margin-top:16px">Sponsored placements are always labeled "Sponsor" or "Sponsored by" and links carry rel="sponsored". Sponsorship never changes a listing, its description, ranking or reviews.</p>'
      f'<h2 {H2}>Price</h2><div {card}><div style="font-size:22px;font-weight:700">Price: TBD</div><p class="muted" style="margin:6px 0 0">Email us and we\'ll share dates and pricing.</p></div>'
      f'<p style="margin:22px 0 0"><a class="btn primary" href="{MAIL}">Email us about sponsoring</a></p>'
      '<p class="muted" style="font-size:13px;margin-top:10px">Opens your email app to <a href="'+MAIL+'">support@agentscouthq.com</a> with the subject "Sponsor AgentScout".</p></section>')
    title="Sponsor AgentScout · AgentScout"; desc="Sponsor AgentScout: a small bar on every page plus a spot in the weekly newsletter. Live traffic and subscriber numbers."
    canon=B+"sponsor.html"
    ld={"@context":"https://schema.org","@type":"WebPage","name":title,"description":desc,"url":canon}
    s=build_extras.shell("",title,desc,canon,body,ld)
    s=s.replace("<title>",'<meta name="robots" content="noindex,nofollow"><meta name="googlebot" content="noindex,nofollow">\n<title>',1)
    open("sponsor.html","w").write(s)
    return "sponsor.html"
if __name__=="__main__":
    t=json.load(open("tools.json")); page(t)
    import build_tasks; build_tasks.sitewide(t)
    print("sponsor.html built; bar pages:",apply_bar(False))
