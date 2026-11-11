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
def listed(rows):
    """Full listings. catalog_only rows stay in the directory and out of new counts."""
    return [x for x in rows if not x.get("catalog_only")]
def is_week(x):
    mat=(x.get("maturity") or "")
    return (not x.get("catalog_only")) and (not x.get("seed")) and "discontinued" not in mat.lower() and (x.get("added") or "")>=(pt_today()-datetime.timedelta(days=6)).isoformat()
def fmt(d): return datetime.date.fromisoformat(d).strftime("%b %-d, %Y")
def short(s,n=110): return s if len(s)<=n else s[:n].rsplit(" ",1)[0]+"…"
def card(x,d):
    return (f'<a class="card rcard" href="{d}tools/{x["slug"]}.html"><div class="ct">{build_extras.ico(x,d,"sm")}<h3>{e(x["name"])}</h3></div>'
            f'<p>{e(short(x["description"]))}</p><div class="rmeta">{"<span class=\"b new\">New</span>" if is_week(x) else ""}<span class="muted">Added <time class="ago" datetime="{e(x["added"])}">{e(fmt(x["added"]))}</time></span></div></a>')
MAKER_PAGE=12  # first screen of /new.html#makers (3 rows at 4 columns, one column on a phone)
MAKER_STEP=24
NEW_CAP=80  # full listings rendered on /new.html; catalog-only additions are a count, not rows
def maker_rows(t):
    """Newest added date first (the date printed on the card), then higher id."""
    return sorted([x for x in t if x.get("maker_submitted")],key=lambda x:((x.get("added") or x.get("submitted") or ""),x.get("id",0)),reverse=True)
def makers_strip(t,n=6):
    """Homepage 'Submitted by makers' strip (Oct 18, 2026 PT): newest maker submissions, static HTML (no layout shift); empty when there are none."""
    mk=maker_rows(t)[:n]
    if not mk: return ""
    cards="".join(f'<a class="mkcard" href="tools/{e(x["slug"])}.html">{build_extras.ico24(x)}<span class="mkname">{e(x["name"])}</span><span class="b maker">✓ Submitted by maker</span></a>' for x in mk)
    return ('<section id="makers-strip" class="mkstrip" aria-labelledby="mk-h"><div class="wrap"><div class="rhead"><h2 id="mk-h">Submitted by makers</h2>'
            '<a href="new.html#makers">See all →</a></div><div class="mkrow">'+cards+'</div></div></section>')
def makers_section(t):
    """new.html 'Submitted by makers', newest added first. The count is len() of the flagged rows. Past the first page, cards stay in the HTML and open with Show more."""
    mk=maker_rows(t)
    if not mk: return ""
    n=len(mk)
    cards=[]
    for i,x in enumerate(mk):
        c=card(x,"")
        if i>=MAKER_PAGE: c=c.replace('<a class="card rcard"','<a class="card rcard mk-rest"',1)
        cards.append(c)
    more=""
    hide=""
    if n>MAKER_PAGE:
        step=min(MAKER_STEP, n-MAKER_PAGE)
        # Hide rule comes before the cards so the extra rows never paint as a pile.
        hide='<style>#makers-grid .mk-rest{display:none}</style>'
        more=(f'<p id="makers-morep" style="text-align:center;margin:4px 0 22px"><button type="button" class="btn" id="makers-more" style="min-height:44px" aria-controls="makers-grid">Show {step} more</button></p>'
              '<script>(function(){var g=document.getElementById("makers-grid"),b=document.getElementById("makers-more"),p=document.getElementById("makers-morep");if(!g||!b)return;var step=24,hid=[].slice.call(g.querySelectorAll("a.mk-rest"));'
              'function label(){var n=hid.length;b.textContent="Show "+Math.min(step,n)+" more"}'
              'b.addEventListener("click",function(){hid.splice(0,step).forEach(function(el){el.classList.remove("mk-rest")});if(!hid.length)p.remove();else label()});label()})();</script>'
              '<noscript><style>#makers-grid .mk-rest{display:flex}</style></noscript>')
    word="tool" if n==1 else "tools"
    return (f'<h2 class="rgroup" id="makers" style="scroll-margin-top:90px">Submitted by makers <span class="muted">· {n} {word}</span></h2>'
            '<p class="muted" style="margin:0 0 12px;font-size:14px">Tools their makers sent us through the <a href="submit.html">submit form</a>. We review each one and write the listing ourselves.</p>'
            f'{hide}<div class="grid rgrid" id="makers-grid">{"".join(cards)}</div>{more}')
def build(t):
    import sys
    sys.path.insert(0,"scripts")
    from maker_flag import check as _maker_check
    _maker_check(t)
    top=(newest(fresh(listed(t)))+[x for x in newest(listed(t)) if x.get("seed")])[:12]
    nw=sum(1 for x in t if is_week(x))
    sec=('<!--RECENT-START--><section id="recent" aria-labelledby="recent-h"><div class="wrap"><div class="rhead"><h2 id="recent-h">Recently added</h2>'
         f'<a href="new.html">See all new tools →</a></div><div class="rstats" id="rstats" aria-live="polite"></div><p class="muted rsub"><span id="rsum">{len(t):,} tools · {nw:,} new this week · every link checked</span><br><span id="rchecked"></span></p><div class="grid rgrid">'+"".join(card(x,"") for x in top)+'</div></div></section>'+STATS_JS+'<!--RECENT-END-->')
    s=open("index.html").read()
    if "<!--RECENT-START-->" in s: s=re.sub(r"<!--RECENT-START-->.*?<!--RECENT-END-->",lambda m:sec,s,flags=re.S)
    else: s=s.replace('<section id="feed">',sec+'\n<section id="feed">',1)
    # makers strip sits near the top: right after the Free AI tools band, above the editor's pick and Recently added (Oct 19, 2026 PT)
    s=re.sub(r"<!--MAKERS-START-->.*?<!--MAKERS-END-->","",s,flags=re.S)
    mk="<!--MAKERS-START-->"+makers_strip(t)+"<!--MAKERS-END-->"
    s=s.replace("<!--PICK-START-->",mk+"<!--PICK-START-->",1) if "<!--PICK-START-->" in s else s.replace("<!--RECENT-START-->",mk+"<!--RECENT-START-->",1)
    open("index.html","w").write(s)
    body,ld=_new_body(t)
    _publish_new(body,ld)
    write_home(t)
    return B+"new.html"
def _new_body(t):
    cut=(pt_today()-datetime.timedelta(days=29)).isoformat()
    rows=newest(fresh(t))
    full=[x for x in rows if (x.get("added") or "")>=cut and not x.get("catalog_only")]
    catalog=[x for x in rows if (x.get("added") or "")>=cut and x.get("catalog_only")]
    shown=full[:NEW_CAP]
    seed=[x for x in t if x.get("seed")]; sd=sorted({x["added"] for x in seed if x.get("added")})
    seednote=(f' The starting catalog of {len(seed):,} tools ({e(datetime.date.fromisoformat(sd[0]).strftime("%b %-d"))}–{e(fmt(sd[-1]))}) is not counted as new. <a href="index.html#feed">Browse all {len(t):,} tools</a>.' if seed and sd else "")
    word="tool" if len(full)==1 else "tools"
    lede=f'{len(full):,} full {word} added in the last 30 days, newest first.'
    if len(full)>len(shown): lede+=f' Showing the latest {len(shown):,}.'
    lede+=" Every link is checked when it is added."
    if catalog:
        cw="listing" if len(catalog)==1 else "listings"
        verb="is" if len(catalog)==1 else "are"
        lede+=f' {len(catalog):,} catalog-only {cw} added in the same window {verb} not listed here. <a href="index.html#spanel">Search the directory</a>.'
    days={}
    for x in shown: days.setdefault(x["added"],[]).append(x)
    body=('<div class="crumb"><a href="index.html">AgentScout</a> / New tools</div><section class="calm">'
          f'<h1 style="text-align:left">New AI agent tools</h1><p class="lede" style="margin-left:0;text-align:left">{lede}{seednote}</p>')
    wk=(pt_today()-datetime.timedelta(days=6)).isoformat()
    body+=makers_section(t)  # newest added first; count comes from the flagged rows
    for label,cond in (("This week",lambda d:d>=wk),("Earlier this month",lambda d:d<wk)):
      ds=[d for d in days if cond(d)]
      if not ds: continue
      n=sum(len(days[d]) for d in ds)
      body+=f'<h2 class="rgroup">{label} <span class="muted">· {n} tool{"s" if n!=1 else ""}</span></h2>'
      for d in ds:
        xs=days[d]; body+=f'<h2 class="rday">{e(fmt(d))} <span class="muted">· {len(xs)} tool{"s" if len(xs)!=1 else ""}</span></h2><div class="grid rgrid">'+"".join(card(x,"") for x in xs)+'</div>'
    body+='</section>'
    ld={"@context":"https://schema.org","@type":"CollectionPage","name":"New AI agent tools","url":B+"new.html","mainEntity":{"@type":"ItemList","itemListElement":[{"@type":"ListItem","position":i+1,"url":f"{B}tools/{x['slug']}.html","name":x["name"]} for i,x in enumerate(shown[:50])]}}
    return body,ld
def _publish_new(body,ld):
    """Refresh new.html in place when the daily build has already added share, search, and footer chrome."""
    import os
    title="New AI agent tools (last 30 days) · AgentScout"
    desc="The newest full AI agent tools added to AgentScout in the last 30 days, grouped by date: coding agents, MCP servers, frameworks and more."
    if os.path.exists("new.html"):
        s=open("new.html",encoding="utf-8").read()
        share=re.search(r'<div class="shareacts">.*?</div>',s,re.S)
        n,k=re.subn(r'<div class="crumb">.*?</section>',lambda m:body,s,count=1,flags=re.S)
        if k and "<main" in n:
            if 'data-pagefind-weight' in s and 'data-pagefind-weight' not in n:
                n=n.replace('<h1 style="text-align:left">','<h1 style="text-align:left" data-pagefind-weight="10">',1)
            if share and "data-share" not in n:
                n=n.replace("</h1>","</h1>"+share.group(0),1)
            raw=json.dumps(ld,ensure_ascii=False).replace("</","<\\/")
            n,k2=re.subn(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "CollectionPage", "name": "New AI agent tools".*?</script>','<script type="application/ld+json">'+raw+'</script>',n,count=1,flags=re.S)
            if not k2: raise SystemExit("new.html JSON-LD was not updated")
            open("new.html","w",encoding="utf-8").write(n)
            return
    open("new.html","w").write(build_extras.shell("",title,desc,B+"new.html",body,ld))
def compact_tool(x):
    return {"id":x.get("id") or 0,"slug":x.get("slug") or "","name":x.get("name") or "","category":x.get("category") or "","description":x.get("description") or "","pricing":x.get("pricing") or "","pricing_detail":x.get("pricing_detail") or "","logo":x.get("logo") or "","url":x.get("url") or "","audience":x.get("audience") or "","github_stars":x.get("github_stars"),"added":x.get("added") or "","new":bool(x.get("new")),"seed":bool(x.get("seed")),"use_cases":x.get("use_cases") or [],"verified":x.get("verified") or "","catalog_only":bool(x.get("catalog_only"))}
def write_home(t):
    """Small homepage payload: counts, category totals, and the new/star rows the first screen renders."""
    import os
    from collections import Counter
    os.makedirs("api",exist_ok=True)
    today=pt_today().isoformat(); month=(pt_today()-datetime.timedelta(days=29)).isoformat()
    fresh_full=[x for x in t if not x.get("catalog_only") and not x.get("seed") and x.get("added")]
    cats=Counter((x.get("category") or "") for x in t)
    categories=[{"name":n,"count":c} for n,c in sorted(cats.items(),key=lambda kv:(-kv[1],kv[0].lower())) if n]
    new_rows=sorted([x for x in t if is_week(x)],key=lambda x:((x.get("added") or ""),x.get("id") or 0),reverse=True)[:8]
    stars=sorted([x for x in t if x.get("github_stars") is not None],key=lambda x:(-(x.get("github_stars") or 0),(x.get("name") or "").lower()))[:8]
    last=max((x["added"] for x in fresh_full),default="")
    lc=max((x.get("verified") or "") for x in t) if t else ""
    doc={"tools_count":len(t),"mcp_servers_count":sum(1 for x in t if x.get("category")=="MCP servers"),"categories_count":len(categories),"catalog_only":sum(1 for x in t if x.get("catalog_only")),"last_checked":lc,"categories":categories,"new":[compact_tool(x) for x in new_rows],"stars":[compact_tool(x) for x in stars],
         "stats":{"total":len(t),"today":sum(1 for x in fresh_full if x["added"]==today),"week":sum(1 for x in t if is_week(x)),"month":sum(1 for x in fresh_full if x["added"]>=month),"last":last,"lastN":sum(1 for x in fresh_full if x["added"]==last),"cats":len(categories)}}
    json.dump(doc,open("api/home.json","w"),separators=(",",":"),ensure_ascii=False)
    return doc
def refresh_published_maker_sections(t=None):
    """Rewrite the homepage strip and the new.html makers block from tools.json. Leaves the rest of each page in place."""
    import sys
    sys.path.insert(0,"scripts")
    from maker_flag import check as _maker_check
    if t is None: t=json.load(open("tools.json"))
    _maker_check(t)
    s=open("index.html",encoding="utf-8").read()
    mk="<!--MAKERS-START-->"+makers_strip(t)+"<!--MAKERS-END-->"
    n,k=re.subn(r"<!--MAKERS-START-->.*?<!--MAKERS-END-->",lambda m:mk,s,count=1,flags=re.S)
    if not k: raise SystemExit("index.html has no makers strip")
    open("index.html","w",encoding="utf-8").write(n)
    s=open("new.html",encoding="utf-8").read()
    mark=s.find('id="makers"')
    start=s.rfind("<h2", 0, mark+1) if mark>=0 else -1
    if start<0: raise SystemExit("new.html has no makers section")
    end=s.find('<h2 class="rgroup"', mark+1)
    if end<0: raise SystemExit("new.html makers section has no following group")
    open("new.html","w",encoding="utf-8").write(s[:start]+makers_section(t)+s[end:])
    return len(maker_rows(t))
