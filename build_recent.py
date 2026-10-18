"""'Recently added' homepage section + new.html, driven by each tool's 'added' date."""
import json,re,html,datetime,build_extras
from zoneinfo import ZoneInfo
def pt_today(): return datetime.datetime.now(ZoneInfo('America/Los_Angeles')).date()
e=lambda s:html.escape(str(s or ""))
B="https://agentscouthq.com/"
STATS_JS=re.sub(r'<meta name="robots"[^>]*>\s*',"",open("stats.js.html").read())  # shared PT stats logic (mirrored in the app: src/api/tools.js stats())
def newest(t): return sorted(t,key=lambda x:(x.get("added",""),x.get("id",0)),reverse=True)
# "seed" = starting catalog (launch Oct 14 + bulk import Oct 16). Never counted as new; daily-discovery additions are.
def fresh(t): return [x for x in t if not x.get("seed")]
def is_week(x): return (not x.get("seed")) and x.get("added","")>=(pt_today()-datetime.timedelta(days=6)).isoformat()
def fmt(d): return datetime.date.fromisoformat(d).strftime("%b %-d, %Y")
def short(s,n=110): return s if len(s)<=n else s[:n].rsplit(" ",1)[0]+"…"
def card(x,d):
    return (f'<a class="card rcard" href="{d}tools/{x["slug"]}.html"><div class="ct">{build_extras.ico(x,d,"sm")}<h3>{e(x["name"])}</h3></div>'
            f'<p>{e(short(x["description"]))}</p><div class="rmeta">{"<span class=\"b new\">New</span>" if is_week(x) else ""}<span class="muted">Added <time class="ago" datetime="{e(x["added"])}">{e(fmt(x["added"]))}</time></span></div></a>')
def build(t):
    top=(newest(fresh(t))+[x for x in newest(t) if x.get("seed")])[:12]
    nw=sum(1 for x in t if is_week(x))
    sec=('<!--RECENT-START--><section id="recent" aria-labelledby="recent-h"><div class="wrap"><div class="rhead"><h2 id="recent-h">Recently added</h2>'
         f'<a href="new.html">See all new tools →</a></div><div class="rstats" id="rstats" aria-live="polite"></div><p class="muted rsub"><span id="rsum">{len(t)} tools · {nw} new this week · every link checked</span><br><span id="rchecked"></span></p><div class="grid rgrid">'+"".join(card(x,"") for x in top)+'</div></div></section>'+STATS_JS+'<!--RECENT-END-->')
    s=open("index.html").read()
    if "<!--RECENT-START-->" in s: s=re.sub(r"<!--RECENT-START-->.*?<!--RECENT-END-->",lambda m:sec,s,flags=re.S)
    else: s=s.replace('<section id="feed">',sec+'\n<section id="feed">',1)
    open("index.html","w").write(s)
    cut=(pt_today()-datetime.timedelta(days=29)).isoformat()
    recent=[x for x in newest(fresh(t)) if x.get("added","")>=cut]
    seed=[x for x in t if x.get("seed")]; sd=sorted({x["added"] for x in seed if x.get("added")})
    seednote=(f' The starting catalog of {len(seed)} tools ({e(datetime.date.fromisoformat(sd[0]).strftime("%b %-d"))}–{e(fmt(sd[-1]))}) is not counted as new. <a href="index.html#feed">Browse all {len(t)} tools</a>.' if seed and sd else "")
    days={}
    for x in recent: days.setdefault(x["added"],[]).append(x)
    body=('<div class="crumb"><a href="index.html">AgentScout</a> / New tools</div><section style="padding-top:20px;text-align:left">'
          f'<h1 style="text-align:left">New AI agent tools</h1><p class="lede" style="margin-left:0;text-align:left">{len(recent)} tool{"s" if len(recent)!=1 else ""} added in the last 30 days, newest first. Every link is checked when it is added.{seednote}</p>')
    wk=(pt_today()-datetime.timedelta(days=6)).isoformat()
    mk=sorted([x for x in t if x.get("maker_submitted")],key=lambda x:(x.get("submitted") or x.get("added",""),x.get("id",0)))  # first submissions first (orke)
    if mk:
        body+=(f'<h2 class="rgroup" id="makers">Submitted by makers <span class="muted">· {len(mk)} tool{"s" if len(mk)!=1 else ""}</span></h2>'
               '<p class="muted" style="margin:0 0 12px;font-size:14px">Tools their makers sent us through the <a href="submit.html">submit form</a>. We review each one and write the listing ourselves.</p>'
               '<div class="grid rgrid">'+"".join(card(x,"") for x in mk)+'</div>')
    for label,cond in (("This week",lambda d:d>=wk),("Earlier this month",lambda d:d<wk)):
      ds=[d for d in days if cond(d)]
      if not ds: continue
      body+=f'<h2 class="rgroup">{label} <span class="muted">· {sum(len(days[d]) for d in ds)} tools</span></h2>'
      for d in ds:
        xs=days[d]; body+=f'<h2 class="rday">{e(fmt(d))} <span class="muted">· {len(xs)} tool{"s" if len(xs)!=1 else ""}</span></h2><div class="grid rgrid">'+"".join(card(x,"") for x in xs)+'</div>'
    body+='</section>'
    ld={"@context":"https://schema.org","@type":"CollectionPage","name":"New AI agent tools","url":B+"new.html","mainEntity":{"@type":"ItemList","itemListElement":[{"@type":"ListItem","position":i+1,"url":f"{B}tools/{x['slug']}.html","name":x["name"]} for i,x in enumerate(recent[:50])]}}
    open("new.html","w").write(build_extras.shell("","New AI agent tools (last 30 days) · AgentScout","The newest AI agent tools added to AgentScout in the last 30 days, grouped by date: coding agents, MCP servers, frameworks and more.",B+"new.html",body,ld))
    return B+"new.html"
