"""Trending pages (competitor-research item 6, Oct 18 2026). Called from build_extras.build(); returns sitemap URLs.
1) trending.html: tools ranked by the Worker's public /trending endpoint (7-day tool-page views + tool clicks + saves from Analytics
   Engine, rank only, min 3 events per tool). Published only when >= MIN_TOOLS tools qualify; otherwise the page is not built.
2) best/trending-open-source-ai-agents.html: GitHub star growth from data/stars/ daily snapshots. Held until there are snapshots
   at least 7 days apart. Last good /trending result is kept in data/trending.json if a fetch fails."""
import json,os,glob,datetime,urllib.request
import build_extras as X
B=X.B; e=X.e
URL="https://agentscout-image.agentscouthq.workers.dev/trending"
MIN_TOOLS=10; MIN_STAR_DAYS=7; MIN_STAR_TOOLS=10
def _fetch():
    try:
        with urllib.request.urlopen(urllib.request.Request(URL,headers={"User-Agent":"AgentScout-build"}),timeout=20) as r: d=json.load(r)
        if isinstance(d.get("tools"),list): json.dump(d,open("data/trending.json","w"),indent=0); return d
    except Exception as ex: print("trending fetch failed:",ex)
    return json.load(open("data/trending.json")) if os.path.exists("data/trending.json") else {"tools":[]}
def _li(i,x,d="../",note=""):
    return (f'<li class="card tile" style="list-style:none"><a class="stretch" href="{d}tools/{x["slug"]}.html" aria-label="{e(x["name"])}"></a><div class="ct">{X.ico(x,d)}<div class="tn"><h3>#{i} {e(x["name"])}</h3><div class="badges">'
            f'<a class="b cat has-cico" href="{d}categories/{X.catslug(x["category"])}.html">{X.cico(x["category"])}{e(x["category"])}</a><span class="b">{e(x["pricing"])}</span>{note}</div></div></div><p class="hook">{e(x["description"])}</p></li>')
def trending(t):
    os.makedirs("data",exist_ok=True)
    d=_fetch(); bs={x["slug"]:x for x in t}
    items=[bs[s] for s in d.get("tools",[]) if s in bs]
    path="trending.html"
    if len(items)<MIN_TOOLS:
        if os.path.exists(path): os.remove(path)
        print(f"trending: {len(items)} tools qualify (<{MIN_TOOLS}), page held"); return []
    upd=(d.get("updated") or "")[:10]; canon=B+path; title="Trending AI agent tools this week · AgentScout"
    desc=f"The AI agent tools AgentScout visitors looked at, clicked and saved most in the last 7 days, including {', '.join(x['name'] for x in items[:3])}."[:158]
    body=(f'<div class="crumb"><a href="index.html">AgentScout</a> / Trending</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">Trending AI agent tools this week</h1>'
          f'<p class="lede" style="margin-left:0;text-align:left">The {len(items)} tools AgentScout visitors viewed, clicked and saved most over the last 7 days, in rank order. We show rank only, not counts. Updated {e(upd)}.</p>'
          f'<ol class="grid" style="padding:0;margin:0">{"".join(_li(i+1,x,"") for i,x in enumerate(items))}</ol>'
          f'<p style="margin-top:20px">See also: <a href="new.html">New tools</a> · <a href="best/most-starred-open-source-ai-agents.html">Most-starred open-source agents</a> · <a href="best/index.html">All best lists</a></p>'
          '<p class="disclose">Ranking uses anonymous, aggregate page views, tool clicks and saves on agentscouthq.com (no personal data). A tool needs at least 3 events in the window to be listed, and each visitor\'s activity is rate-limited.</p></section>')
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon},{"@type":"ItemList","itemListOrder":"https://schema.org/ItemListOrderDescending","numberOfItems":len(items),"itemListElement":[{"@type":"ListItem","position":i+1,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate(items)]}]}
    open(path,"w").write(X.shell("",title,desc,canon,body,ld)); print("trending:",len(items),"tools"); return [canon]
def star_growth(t):
    snaps=sorted(glob.glob("data/stars/*.json")); path="best/trending-open-source-ai-agents.html"
    def held(why):
        if os.path.exists(path): os.remove(path)
        print("star growth page held:",why); return []
    if len(snaps)<2: return held(f"{len(snaps)} snapshot(s)")
    last=snaps[-1]; ld_=datetime.date.fromisoformat(os.path.basename(last)[:10])
    base=[s for s in snaps if (ld_-datetime.date.fromisoformat(os.path.basename(s)[:10])).days>=MIN_STAR_DAYS]
    if not base: return held(f"snapshots span {(ld_-datetime.date.fromisoformat(os.path.basename(snaps[0])[:10])).days} days (<{MIN_STAR_DAYS})")
    b0=base[-1]; d0=datetime.date.fromisoformat(os.path.basename(b0)[:10]); A=json.load(open(b0)); Z=json.load(open(last))
    bs={x["slug"]:x for x in t}
    gr=sorted([(Z[s]-A[s],s) for s in Z if s in A and s in bs and Z[s]>A[s]],reverse=True)[:25]
    if len(gr)<MIN_STAR_TOOLS: return held(f"only {len(gr)} repos grew")
    items=[(bs[s],g) for g,s in gr]; days=(ld_-d0).days; canon=B+path
    title=f"Trending open-source AI agents (GitHub stars, last {days} days) · AgentScout"[:70]
    desc=f"Open-source AI agent projects gaining the most GitHub stars over the last {days} days, from AgentScout's daily snapshots."
    body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">Best lists</a> / Trending open source</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">Trending open-source AI agents</h1>'
          f'<p class="lede" style="margin-left:0;text-align:left">The {len(items)} listed open-source projects that gained the most GitHub stars between {e(d0.strftime("%b %-d"))} and {e(ld_.strftime("%b %-d, %Y"))}, from our daily snapshots of each repo.</p>'
          f'<ol class="grid" style="padding:0;margin:0">{"".join(_li(i+1,x,"../",f"<span class=\"b\">+{g:,} stars</span>") for i,(x,g) in enumerate(items))}</ol>'
          '<p style="margin-top:20px">See also: <a href="most-starred-open-source-ai-agents.html">Most-starred open-source agents (all time)</a> · <a href="index.html">All best lists</a></p></section>')
    ld={"@context":"https://schema.org","@type":"CollectionPage","name":title,"description":desc,"url":canon}
    open(path,"w").write(X.shell("../",title,desc,canon,body,ld)); print("star growth:",len(items)); return [canon]
def _link(path,html_,marker):
    if not os.path.exists(path): return
    s=open(path).read()
    if marker in s: return
    s=s.replace("</h1>","</h1>"+html_,1); open(path,"w").write(s)
def pages(t):
    u=trending(t)+star_growth(t)
    if os.path.exists("trending.html"): _link("new.html",'<p style="margin:6px 0 0"><a href="trending.html">See what\'s trending this week →</a></p>','href="trending.html"')
    if os.path.exists("best/trending-open-source-ai-agents.html"): _link("best/index.html",'<p style="margin:6px 0 0"><a href="trending-open-source-ai-agents.html">Trending open-source AI agents (star growth) →</a></p>','href="trending-open-source-ai-agents.html"')
    return u
