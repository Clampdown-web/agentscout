"""Per-story news pages (Oct 18 2026).
Every agent news item gets a permanent page at /news/YYYY/MM/<slug>.html, plus monthly archives
(/news/YYYY/MM/index.html) and a hub (/news/index.html).
- news-history.json is the permanent store. Each build merges in news-archive.json (the routine's
  rolling 30-day file) and news.json. Items are never removed, so a page stays live after its item
  leaves the 30-day window. The slug is fixed the first time an item is seen, so later title edits
  never change a URL.
- The "page" field (site-relative path) is written back into news.json and news-archive.json, so the
  homepage box, news.html and api/sections.json link to the story pages.
Called from build_extras.build() on every build_site.py run, before news.html is generated."""
import json,os,re,html,datetime
B="https://agentscouthq.com/"
e=lambda s:html.escape(str(s or ""))
HIST="news-history.json"
GENERIC={"agent","agents","claude","openai","google","cursor","replit"}  # names too generic to auto-link from a headline (tool field still links)
def _slug(t):
    s=re.sub(r"[^a-z0-9]+","-",t.lower().replace("'","")).strip("-")
    if len(s)>70: s=s[:70].rsplit("-",1)[0]
    return s or "story"
def history():
    h=json.load(open(HIST)) if os.path.exists(HIST) else {"items":[]}
    byu={x["url"]:x for x in h["items"]}; used={x["page"] for x in h["items"]}; changed=False
    src=[]
    for f in ("news-archive.json","news.json"):
        if os.path.exists(f): src+=json.load(open(f)).get("items",[])
    for x in src:
        if not x.get("url") or not x.get("title") or not x.get("date"): continue
        o=byu.get(x["url"])
        if o is None:
            base=f'news/{x["date"][:4]}/{x["date"][5:7]}/{_slug(x["title"])}'; p=base+".html"; i=2
            while p in used: p=f"{base}-{i}.html"; i+=1
            used.add(p); o=byu[x["url"]]={"url":x["url"],"page":p,"first_seen":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}; changed=True
        for k in ("title","source","date","tool","summary"):
            if x.get(k) is not None and o.get(k)!=x[k]: o[k]=x[k]; changed=True
    items=sorted(byu.values(),key=lambda x:x["date"],reverse=True)
    if changed or not os.path.exists(HIST): json.dump({"items":items},open(HIST,"w"),indent=1,ensure_ascii=False)
    # write the page path back into the routine's files (homepage box, news.html, app API read these)
    pg={x["url"]:x["page"] for x in items}
    for f in ("news-archive.json","news.json"):
        if not os.path.exists(f): continue
        d=json.load(open(f)); ch=False
        for x in d.get("items",[]):
            if x.get("url") in pg and x.get("page")!=pg[x["url"]]: x["page"]=pg[x["url"]]; ch=True
        if ch: json.dump(d,open(f,"w"),indent=1,ensure_ascii=False)
    return items
def related(x,t):
    bs={y["slug"]:y for y in t}; out=[]
    if x.get("tool") in bs: out.append(bs[x["tool"]])
    txt=x.get("title","")+" "+x.get("summary","")
    for y in sorted(t,key=lambda y:-len(y["name"])):
        n=y["name"]
        if len(n)<4 or n.lower() in GENERIC or y in out: continue
        if re.search(r"(?<![\w-])"+re.escape(n)+r"(?![\w-])",txt): out.append(y)
        # an official "<Product> MCP Server" listing matches a story that names the product and MCP
        elif re.search(r"\bMCP\b",txt) and (m:=re.match(r"^(.{4,}?) MCP(?: Server)?$",n)) and m.group(1).lower() not in GENERIC and re.search(r"(?<![\w-])"+re.escape(m.group(1))+r"(?![\w-])",txt): out.append(y)
    return out[:6]
def _ptd(d):
    import build_extras; return build_extras.pt_date(d)
def _fmt(d): return datetime.date.fromisoformat(_ptd(d)).strftime("%b %-d, %Y")  # Pacific date
def _month(ym): return datetime.date(int(ym[:4]),int(ym[5:7]),1).strftime("%B %Y")
def pages(t):
    import build_extras as X
    items=[x for x in history() if x.get("summary")]
    urls=[]; months={}
    for x in items: months.setdefault(x["date"][:7],[]).append(x)
    for i,x in enumerate(items):
        d="../../../"; canon=B+x["page"]; ym=x["date"][:7]
        rel=related(x,t)
        sameday=[y for y in items if y is not x and _ptd(y["date"])==_ptd(x["date"])][:6]
        newer=items[i-1] if i>0 else None; older=items[i+1] if i+1<len(items) else None
        src=X.su(x["url"])
        relh=("<h2 style=\"font-size:18px;margin:32px 0 12px\">Related on AgentScout</h2><div class=\"grid\" style=\"grid-template-columns:repeat(auto-fill,minmax(240px,1fr))\">"+"".join(f'<a class="card" href="{d}tools/{y["slug"]}.html"><div class="ct">{X.ico(y,d,"sm")}<h3 style="flex:1">{e(y["name"])}</h3></div><p>{e(y["description"])}</p></a>' for y in rel)+"</div>") if rel else ""
        sd=("<h2 style=\"font-size:18px;margin:32px 0 8px\">More agent news from "+_fmt(x["date"])+"</h2><ul>"+"".join(f'<li><a href="{d}{y["page"]}">{e(y["title"])}</a> <span class="muted">({e(y["source"])})</span></li>' for y in sameday)+"</ul>") if sameday else ""
        nav=" · ".join(z for z in [f'<a href="{d}{newer["page"]}" rel="next">Newer: {e(newer["title"])}</a>' if newer else "",f'<a href="{d}{older["page"]}" rel="prev">Older: {e(older["title"])}</a>' if older else ""] if z)
        body=(f'<div class="crumb"><a href="{d}index.html">AgentScout</a> / <a href="{d}news.html">Agent news</a> / <a href="index.html">{_month(ym)}</a></div>'
              f'<article style="padding-top:20px;text-align:left;max-width:760px"><h1 style="text-align:left">{e(x["title"])}</h1>'
              f'<p class="muted" style="margin:0 0 18px"><time datetime="{e(x["date"])}">{_fmt(x["date"])}</time> · Source: {e(x["source"])}</p>'
              f'<p class="lede" style="margin-left:0;text-align:left">{e(x["summary"])}</p>'
              f'<p><a class="btn" href="{e(src)}" target="_blank" rel="noopener noreferrer">Read the original on {e(x["source"])} ↗</a></p>'
              f'{relh}{sd}'+(f'<p style="margin-top:28px">{nav}</p>' if nav else "")+
              f'<p style="margin-top:20px"><a href="{d}news.html">Latest agent news</a> · <a href="index.html">All {_month(ym)} stories</a> · <a href="../../index.html">News archive</a></p>'
              '<p class="disclose">Summary written by AgentScout from the original report; follow the source link for the full story.</p></article>')
        title=f'{x["title"]} · AgentScout'
        desc=x["summary"] if len(x["summary"])<=158 else x["summary"][:155].rsplit(" ",1)[0]+"…"
        ld={"@context":"https://schema.org","@graph":[
            {"@type":"NewsArticle","@id":canon+"#article","headline":x["title"][:110],"description":x["summary"],"datePublished":x["date"],"dateModified":x["date"],"url":canon,"mainEntityOfPage":canon,
             "image":[B+"og.png"],"author":{"@type":"Organization","name":"AgentScout","url":B},"publisher":{"@type":"Organization","name":"AgentScout","url":B,"logo":{"@type":"ImageObject","url":B+"logo-square.png"}},
             "isBasedOn":x["url"],"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B},**({"about":[{"@type":"SoftwareApplication","name":y["name"],"url":f'{B}tools/{y["slug"]}.html'} for y in rel]} if rel else {})},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Agent news","item":B+"news.html"},
             {"@type":"ListItem","position":3,"name":_month(ym),"item":f"{B}news/{ym[:4]}/{ym[5:]}/"},{"@type":"ListItem","position":4,"name":x["title"][:110],"item":canon}]}]}
        s=X.shell(d,title,desc,canon,body,ld).replace('<meta property="og:type" content="article">',f'<meta property="og:type" content="article"><meta property="article:published_time" content="{e(x["date"])}"><meta property="article:section" content="AI agents">',1)
        os.makedirs(os.path.dirname(x["page"]),exist_ok=True); open(x["page"],"w").write(s); urls.append(canon)
    # monthly archives
    for ym,its in sorted(months.items(),reverse=True):
        d="../../../"; canon=f"{B}news/{ym[:4]}/{ym[5:]}/"; days={}
        for x in its: days.setdefault(_ptd(x["date"]),[]).append(x)
        lis="".join(f'<h2 class="nday">{datetime.date.fromisoformat(dd).strftime("%A, %B %-d, %Y")}</h2><ol class="nlist">'+"".join(f'<li class="nitem"><h3><a href="{d}{x["page"]}">{e(x["title"])}</a></h3><p class="nsum">{e(x["summary"])}</p><span class="nm">{e(x["source"])}</span></li>' for x in days[dd])+"</ol>" for dd in sorted(days,reverse=True))
        title=f"AI agent news, {_month(ym)} · AgentScout"; desc=f"All {len(its)} AI agent news stories AgentScout covered in {_month(ym)}, each with a short summary in our own words and a link to the source."
        nl = ""
        if ym == "2026-10":
            import build_tasks
            nl = build_tasks.INLINE_NL
        body=(f'<div class="crumb"><a href="{d}index.html">AgentScout</a> / <a href="{d}news.html">Agent news</a> / {_month(ym)}</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">AI agent news: {_month(ym)}</h1>'
              f'<p class="lede" style="margin-left:0;text-align:left">{len(its)} stories about AI agents, coding agents and MCP. Open a story for its summary, related tools and the source link.</p>{nl}{lis}'
              f'<p style="margin-top:24px"><a href="../../index.html">All months</a> · <a href="{d}news.html">Latest agent news</a></p></section>')
        ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon},{"@type":"ItemList","itemListElement":[{"@type":"ListItem","position":k+1,"url":B+x["page"],"name":x["title"]} for k,x in enumerate(its)]},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Agent news","item":B+"news.html"},{"@type":"ListItem","position":3,"name":_month(ym),"item":canon}]}]}
        os.makedirs(f"news/{ym[:4]}/{ym[5:]}",exist_ok=True); open(f"news/{ym[:4]}/{ym[5:]}/index.html","w").write(X.shell(d,title,desc,canon,body,ld)); urls.append(canon)
    # hub
    d="../"; canon=B+"news/"
    rows="".join(f'<li><a href="{ym[:4]}/{ym[5:]}/index.html">{_month(ym)}</a> <span class="muted">({len(its)} stories)</span></li>' for ym,its in sorted(months.items(),reverse=True))
    latest="".join(f'<li><a href="{d}{x["page"]}">{e(x["title"])}</a> <span class="muted">({_fmt(x["date"])}, {e(x["source"])})</span></li>' for x in items[:10])
    title="AI agent news archive · AgentScout"; desc=f"Every AI agent news story AgentScout has covered ({len(items)} so far), by month, with summaries in our own words and links to the sources."
    body=(f'<div class="crumb"><a href="{d}index.html">AgentScout</a> / <a href="{d}news.html">Agent news</a> / Archive</div><section style="padding-top:20px;text-align:left;max-width:760px"><h1 style="text-align:left">AI agent news archive</h1>'
          f'<p class="lede" style="margin-left:0;text-align:left">{len(items)} stories so far. Each one has its own page with a summary, related tools and the source link. For today\'s stories, see <a href="{d}news.html">Agent news</a>.</p>'
          f'<h2 style="font-size:18px;margin:24px 0 8px">By month</h2><ul>{rows}</ul><h2 style="font-size:18px;margin:24px 0 8px">Latest stories</h2><ul>{latest}</ul></section>')
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Agent news","item":B+"news.html"},{"@type":"ListItem","position":3,"name":"Archive","item":canon}]}]}
    os.makedirs("news",exist_ok=True); open("news/index.html","w").write(X.shell(d,title,desc,canon,body,ld)); urls.insert(0,canon)
    print("news pages:",len(items),"stories,",len(months),"months")
    write_feed(t)
    return urls
FEED=B+"feed.xml"
def _xml(s):
    from xml.sax.saxutils import escape
    s="".join(ch for ch in str(s or "") if ch in "\t\n\r" or ord(ch)>=32)
    return escape(s)
def _when(iso):
    s=str(iso or "").strip().replace("Z","+00:00")
    if not s: return None
    if "T" not in s: s+="T12:00:00+00:00"
    try: d=datetime.datetime.fromisoformat(s)
    except ValueError: return None
    if d.tzinfo is None: d=d.replace(tzinfo=datetime.timezone.utc)
    return d.astimezone(datetime.timezone.utc)
def write_feed(tools=None):
    """RSS 2.0 at /feed.xml: newest agent-news pages plus newest non-seed tools. Absolute site URLs only."""
    import email.utils,xml.etree.ElementTree as ET
    if tools is None: tools=json.load(open("tools.json"))
    rows=[]; seen=set()
    hist=json.load(open(HIST)) if os.path.exists(HIST) else {"items":[]}
    news=[]
    for x in hist.get("items",[]):
        page=x.get("page"); when=_when(x.get("date"))
        if not page or not x.get("title") or when is None: continue
        url=B+page.lstrip("/")
        if not url.startswith(B) or url in seen: continue
        seen.add(url); news.append((when,x["title"],url,x.get("summary") or x["title"]))
    news.sort(key=lambda z:z[0],reverse=True)
    rows.extend(news[:25])
    pool=sorted((x for x in tools if not x.get("seed") and x.get("slug") and x.get("name")),key=lambda x:(x.get("added") or "",x.get("id") or 0),reverse=True)
    for x in pool[:20]:
        url=f"{B}tools/{x['slug']}.html"
        when=_when(x.get("added"))
        if when is None or url in seen: continue
        seen.add(url); rows.append((when,x["name"],url,x.get("description") or x["name"]))
    rows.sort(key=lambda z:z[0],reverse=True)
    if not rows: raise SystemExit("feed.xml: no items")
    built=max(z[0] for z in rows)
    items="\n".join(
        "<item>"
        f"<title>{_xml(title)}</title>"
        f"<link>{_xml(url)}</link>"
        f"<guid isPermaLink=\"true\">{_xml(url)}</guid>"
        f"<pubDate>{email.utils.format_datetime(when,usegmt=True)}</pubDate>"
        f"<description>{_xml(desc)}</description>"
        "</item>"
        for when,title,url,desc in rows)
    doc=(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "<channel>\n"
        "<title>AgentScout</title>\n"
        f"<link>{B}</link>\n"
        "<description>Latest AI agent tools and agent news from AgentScout.</description>\n"
        "<language>en-us</language>\n"
        f"<lastBuildDate>{email.utils.format_datetime(built,usegmt=True)}</lastBuildDate>\n"
        f'<atom:link href="{FEED}" rel="self" type="application/rss+xml"/>\n'
        f"{items}\n</channel>\n</rss>\n")
    root=ET.fromstring(doc)
    if root.tag!="rss" or root.get("version")!="2.0": raise SystemExit("feed.xml: not RSS 2.0")
    got=list(root.iter("item"))
    if len(got)!=len(rows): raise SystemExit("feed.xml: item count mismatch")
    for it in got:
        link=it.findtext("link") or ""
        if not link.startswith("https://agentscouthq.com/") or it.findtext("guid")!=link or not it.findtext("title") or not it.findtext("pubDate"):
            raise SystemExit("feed.xml: item missing an absolute AgentScout link")
    open("feed.xml","w",encoding="utf-8").write(doc)
    print("feed.xml:",len(rows),"items")
    return FEED
if __name__=="__main__":
    write_feed()
