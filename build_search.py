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
        a=[f'data-pagefind-filter="type:{ptype(p)}"']; date=lm
        if p.startswith("tools/"):
            x=tools.get(p[6:-5])
            if x:
                a+=[f'data-pagefind-filter="pricing:{_price(x.get("pricing"))}"',f'data-pagefind-filter="category:{html.escape(x["category"])}"']
                if (x.get("pricing") or "").lower().startswith("open"): a.append('data-pagefind-filter="open source:Yes"')
                date=x.get("added") or lm
                a.append(f'data-pagefind-meta="title:{html.escape(x["name"],quote=True)}"')
                if x.get("logo"): a.append(f'data-pagefind-meta="image:/{x["logo"]}"')
        elif ptype(p)=="News":
            m=re.search(r'"datePublished": ?"(\d{4}-\d\d-\d\d)',s); date=m.group(1) if m else lm
        a.append(f'data-pagefind-sort="date:{date}"'); a.append(f'data-pagefind-meta="type:{ptype(p)}"')
        mk='<span id="pfm" hidden>'+"".join(f'<span {z}></span>' for z in a)+'</span>'
        s2=MK_RE.sub("",s)
        s2=re.sub(r'<main(?![^>]*data-pagefind-body)([^>]*)>',r'<main\1 data-pagefind-body>',s2,1)
        if "data-pagefind-body" not in s2: continue
        s2=re.sub(r'<h1(?![^>]*data-pagefind-weight)([^>]*)>',r'<h1\1 data-pagefind-weight="10">',s2,1)  # titles outrank body mentions
        s2=s2.replace("</main>",mk+"</main>",1)
        if s2!=s: open(p,"w",encoding="utf-8").write(s2)
        n+=1
    print("search: annotated",n,"pages")
def navlink():
    import glob
    n=0
    for f in glob.glob("**/*.html",recursive=True):
        if f.startswith(("sponsor","preview/","pagefind/")): continue
        s=open(f,encoding="utf-8").read()
        if 'data-navsearch' in s or '<div class="links">' not in s: continue
        open(f,"w",encoding="utf-8").write(s.replace('<div class="links">','<div class="links"><a data-navsearch href="/search/" aria-label="Search the site">🔍 Search</a>',1)); n+=1
    print("search: nav link added to",n,"pages")
def run():
    if os.environ.get("NO_PAGEFIND"): print("search: skipped (NO_PAGEFIND)"); return
    if not os.path.exists("sitemap.xml"): return
    navlink(); annotate()
    if os.path.exists("search/index.html"):  # Pagefind runs WebAssembly: allow it on the search page only
        z=open("search/index.html",encoding="utf-8").read()
        if "'wasm-unsafe-eval'" not in z: open("search/index.html","w",encoding="utf-8").write(z.replace("script-src 'self'","script-src 'self' 'wasm-unsafe-eval'",1))
    r=subprocess.run([sys.executable,"-m","pagefind","--site",".","--output-subdir","pagefind","--glob","**/*.html","--exclude-selectors","nav,footer,.crumb,.shareacts,[data-pagefind-ignore]"],capture_output=True,text=True)
    out=(r.stdout+r.stderr).strip().splitlines()
    print("search: pagefind",("ok" if r.returncode==0 else "FAILED")," | ".join(l for l in out if "Indexed" in l or "rror" in l)[:300])
    if r.returncode: sys.exit(1)
def page():
    import build_extras as X
    os.makedirs("search",exist_ok=True)
    canon=B+"search/"; title="Search AgentScout: tools, guides, news and free tools"; desc="Search the whole AgentScout site: AI agent tools, MCP servers, categories, best-of guides, news and free tools, with filters for type, pricing and open source."
    body=open("data/search.inc",encoding="utf-8").read()
    ld={"@context":"https://schema.org","@type":"SearchResultsPage","name":title,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}}
    open("search/index.html","w",encoding="utf-8").write(X.shell("../",title,desc,canon,body,ld))
    return [canon]
