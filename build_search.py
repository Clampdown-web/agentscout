"""Site-wide search (Oct 21 2026, owner-requested): Pagefind static index over every indexable page.
- page(): writes search/index.html (UI on the Pagefind JS API; index loads only on this page).
- run(): runs at the very end of every build that imports build_extras (atexit, registered first so it runs last):
  1) annotates every sitemap page (except the homepage, whose <main> is the whole directory) with data-pagefind-body,
     a type filter, tool filters (pricing, open source, category) and a date sort key;
  2) runs `python3 -m pagefind` into ./pagefind/. Pages not in sitemap.xml (sponsor, redirects, noindex) are never annotated,
     and Pagefind only indexes annotated pages, so they stay out. Set NO_PAGEFIND=1 to skip (e.g. quick local tests)."""
import os,re,json,html,subprocess,sys
B="https://agentscouthq.com/"
MK_RE=re.compile(r'<span id="pfm".*?</span></span>|<span id="pfm"[^>]*></span>')
def ptype(p):
    if p.startswith("tools/"): return "Tools"
    if p.startswith("categories/"): return "Categories"
    if p.startswith(("news/",)) or p=="news.html": return "News"
    if p.startswith("free-tools/") or p in ("free-tools.html","generate.html"): return "Free tools"
    if p.startswith(("best/","s/","mcp/","tasks/","for/","compare/","bot-templates/","alternatives/")): return "Guides & best-of"
    return "Pages"
def _price(p):
    import build_extras as X
    return {"free":"Free","freemium":"Freemium","paid":"Paid"}.get(X.ptag(p),"Not listed")
_rvc=None
def _RV():
    global _rvc
    if _rvc is None:
        try: _rvc=json.load(open("reviews.json")).get("tools",{})
        except Exception: _rvc={}
    return _rvc
def annotate():
    sm=open("sitemap.xml").read()
    locs=re.findall(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>",sm)
    tools={x["slug"]:x for x in json.load(open("tools.json"))}
    keep=set(); n=0
    for u,lm in locs:
        p=u.replace(B,"")
        if not p or p.endswith("/"): p+="index.html"
        if not p.endswith(".html") or p=="index.html" or p.startswith("search/") or not os.path.exists(p): continue
        s=open(p,encoding="utf-8").read()
        if 'name="robots" content="noindex' in s or 'http-equiv="refresh"' in s[:4000]: continue
        a=[f'data-pagefind-filter="type:{ptype(p)}"']; date=lm; kw=""
        if p.startswith("tools/"):
            x=tools.get(p[6:-5])
            if x:
                a+=[f'data-pagefind-filter="pricing:{_price(x.get("pricing"))}"',f'data-pagefind-filter="category:{html.escape(x["category"])}"']
                if (x.get("pricing") or "").lower().startswith("open"): a.append('data-pagefind-filter="open source:Yes"')
                date=x.get("added") or lm
                a.append(f'data-pagefind-meta="title:{html.escape(x["name"],quote=True)}"')
                if x.get("logo"): a.append(f'data-pagefind-meta="logo:/{x["logo"]}"')
                kw=_joined(x["name"])
                # extra sort keys so /search/ offers the same 4 sorts as the homepage (Oct 22 2026)
                gs=x.get("github_stars") if x.get("github_stars") is not None else 0
                r=_RV().get(x["slug"]) or {}; bay=(r["avg"]*r["count"]+12)/(r["count"]+3) if r.get("count") else 0
                a+=[f'data-pagefind-sort="stars:{int(gs)}"',f'data-pagefind-sort="loved:{int(round(bay*1000))*10**9+int(gs)}"',f'data-pagefind-sort="name:{html.escape(x["name"].lower(),quote=True)}"']
        elif p.startswith("bot-templates/") and p!="bot-templates/index.html":
            m=re.search(r'<div class="bd-top"><img[^>]*?src="([^"]+)"',s)
            if m and not m.group(1).startswith(("http","/","data:")): a.append(f'data-pagefind-meta="logo:/bot-templates/{html.escape(m.group(1),quote=True)}"')
        elif ptype(p)=="News":
            m=re.search(r'"datePublished": ?"(\d{4}-\d\d-\d\d)',s); date=m.group(1) if m else lm
        a.append(f'data-pagefind-sort="date:{date}"'); a.append(f'data-pagefind-meta="type:{ptype(p)}"')
        mk='<span id="pfm" hidden>'+"".join(f'<span {z}></span>' for z in a)+(f'<span data-pagefind-weight="7">{html.escape(kw)}</span>' if kw else "")+'</span>'
        s2=MK_RE.sub("",s)
        s2=re.sub(r'<main(?![^>]*data-pagefind-body)([^>]*)>',r'<main\1 data-pagefind-body>',s2,1)
        if "data-pagefind-body" not in s2: continue
        s2=re.sub(r'<h1(?![^>]*data-pagefind-weight)([^>]*)>',r'<h1\1 data-pagefind-weight="10">',s2,1)  # titles outrank body mentions
        s2=s2.replace("</main>",mk+"</main>",1)
        if s2!=s: open(p,"w",encoding="utf-8").write(s2)
        n+=1
    print("search: annotated",n,"pages")
NAVFORM='<form data-navsearch class="nsrch" role="search" action="/search/" method="get"><input name="q" type="search" placeholder="Search tools…" aria-label="Search the site" autocomplete="off" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="nsl"><ul id="nsl" role="listbox" aria-label="Suggestions" hidden></ul></form>'
NAVJS='<script src="/navsearch.js?v=20261021d" defer></script>'
OLD_LINK='<a data-navsearch href="/search/" aria-label="Search the site">🔍 Search</a>'
def navlink():
    """Oct 23 2026 (owner): back to ONE search per page. The menu search box (Oct 21) is removed from every page;
    the homepage panel and /search/ have their own box with filters attached, and the menu keeps its "Search & filters" link to /search/."""
    import glob
    n=0
    for f in glob.glob("**/*.html",recursive=True):
        if f.startswith(("sponsor","preview/","pagefind/")): continue
        s=open(f,encoding="utf-8").read(); s0=s
        s=s.replace(OLD_LINK,"")
        s=re.sub(r'<form data-navsearch.*?</form>','',s,1,flags=re.S)
        s=re.sub(r'<script src="/navsearch\.js[^"]*" defer></script>','',s)
        if s!=s0: open(f,"w",encoding="utf-8").write(s); n+=1
    print("search: menu search box removed on",n,"pages")
def _joined(name):
    """Joined-up lowercase forms of a tool name so Pagefind finds 'gmapsscraper' / 'gmapsscraper.ai' (Oct 21 2026).
    Only added when the name has more than one part; e.g. 'GMapsScraper.AI' -> 'gmapsscraperai gmapsscraper'."""
    n=name.lower(); parts=[w for w in re.split(r"[^a-z0-9]+",n) if w]
    if len(parts)<2: return ""
    out=["".join(parts)]
    m=re.match(r"^(.*?)\.(ai|io|app|dev|so|sh|co|com|xyz|run|chat|tech|net|org|me|gg)$",n.strip())
    if m:
        b="".join(w for w in re.split(r"[^a-z0-9]+",m.group(1)) if w)
        if b and b not in out: out.append(b)
    return " ".join(out)
def run():
    if os.environ.get("NO_PAGEFIND"): print("search: skipped (NO_PAGEFIND)"); return
    if not os.path.exists("sitemap.xml"): return
    navlink(); annotate()
    if os.path.exists("search/index.html"):  # Pagefind runs WebAssembly: allow it on the search page only
        z=open("search/index.html",encoding="utf-8").read()
        if "'wasm-unsafe-eval'" not in z: open("search/index.html","w",encoding="utf-8").write(z.replace("script-src 'self'","script-src 'self' 'wasm-unsafe-eval'",1))
    # Build into a temp dir, then swap it in, so stale index/fragment files from old builds never pile up (Oct 21 2026: 85 stale builds, ~16.8k files)
    import shutil; tmp=".pagefind_new"; shutil.rmtree(tmp,ignore_errors=True)
    r=subprocess.run([sys.executable,"-m","pagefind","--site",".","--output-path",tmp,"--glob","**/*.html","--exclude-selectors","nav,footer,.crumb,.shareacts,[data-pagefind-ignore],.badges,.rv-top,.updated,.gencall,.acts,.bd-back,.bd-meta,.bd-cta,.ico,.bt-ic,.rv,.embeds,.bd-src,.bd-rel,.addedago"],capture_output=True,text=True)
    out=(r.stdout+r.stderr).strip().splitlines()
    print("search: pagefind",("ok" if r.returncode==0 else "FAILED")," | ".join(l for l in out if "Indexed" in l or "rror" in l)[:300])
    if r.returncode or not os.path.exists(os.path.join(tmp,"pagefind-entry.json")): shutil.rmtree(tmp,ignore_errors=True); sys.exit(1)
    shutil.rmtree("pagefind",ignore_errors=True); os.rename(tmp,"pagefind")
def page():
    import build_extras as X
    os.makedirs("search",exist_ok=True)
    canon=B+"search/"; title="Search AgentScout: tools, guides, news and free tools"; desc="Search the whole AgentScout site: AI agent tools, MCP servers, categories, best-of guides, news and free tools, with filters for type, pricing and open source."
    body=open("data/search.inc",encoding="utf-8").read()
    ld={"@context":"https://schema.org","@type":"SearchResultsPage","name":title,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}}
    open("search/index.html","w",encoding="utf-8").write(X.shell("../",title,desc,canon,body,ld))
    # small tool-name index for best-match pinning and "Did you mean" (loaded lazily with the Pagefind index)
    t=json.load(open("tools.json"))
    # popularity score (owner-approved Oct 21 2026) used to order nav suggestions WITHIN each name-match group:
    # log10 GitHub stars; tools without a repo get the median (neutral) so closed tools aren't buried; ratings add in only from 3+ ratings.
    # Paid/sponsored/featured status is never used.
    import math,statistics
    try: RV=json.load(open("reviews.json")).get("tools",{})
    except Exception: RV={}
    lg=[math.log10(x["github_stars"]+1) for x in t if x.get("github") and x.get("github_stars")]
    mid=statistics.median(lg) if lg else 0
    def pop(x):
        sc=math.log10(x["github_stars"]+1) if x.get("github") and x.get("github_stars") else mid
        r=RV.get(x["slug"]) or {}
        if r.get("count",0)>=3: sc+=((r["avg"]*r["count"]+12)/(r["count"]+3)-3)*0.5
        return round(sc,2)
    json.dump([[x["name"],x["slug"],x.get("logo") or "",x["category"],x.get("pricing") or "",pop(x)] for x in t],open("search/names.json","w",encoding="utf-8"),ensure_ascii=False,separators=(",",":"))
    # typo-fallback vocabulary (Oct 21 2026): common words from tool names, categories, use cases and descriptions, with counts
    import collections; W=collections.Counter()
    for x in t:
        for fld in (x["name"],x["category"],x.get("description",""),x.get("pricing","")," ".join(x.get("use_cases") or [])):
            for w in re.findall(r"[a-z][a-z0-9]{2,}",fld.lower()): W[w]+=1
    json.dump([[w,c] for w,c in W.most_common(6000) if c>=2],open("search/words.json","w",encoding="utf-8"),separators=(",",":"))
    return [canon]
