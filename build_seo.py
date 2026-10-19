"""Technical SEO pass for the recently added page groups (tool pages, best-of, /s/, /for/, free tools, categories, homepage).
Idempotent post-processing, run at the end of build_site.py:
- shortens <title>/og:title over 65 chars on every generated page group (drops brand, then year; keeps the tool name),
- adds twitter:title / twitter:description / twitter:image mirrored from the Open Graph tags when missing,
- adds BreadcrumbList + ItemList JSON-LD to the best/, s/, for/ and categories/ hubs."""
import glob,re,json,html
B="https://agentscouthq.com/"
def _groups():
    return (sorted(glob.glob("tools/*.html"))+sorted(glob.glob("best/*.html"))+sorted(glob.glob("s/*.html"))+sorted(glob.glob("for/*.html"))
        +["free-tools.html"]+sorted(f for f in glob.glob("free-tools/*.html") if not f.endswith("index.html"))+sorted(glob.glob("categories/*.html"))+sorted(glob.glob("tasks/*.html"))+sorted(glob.glob("compare/*.html"))+sorted(glob.glob("news/**/*.html",recursive=True))+["index.html"])
def _attr(s,pat):
    m=re.search(pat,s); return m.group(1) if m else None
def _settitle(s,new):
    v=html.escape(new,quote=True)
    s=re.sub(r"<title>.*?</title>",f"<title>{v}</title>",s,1,flags=re.S)
    s=re.sub(r'(<meta property="og:title" content=")[^"]*(")',lambda m:m.group(1)+v+m.group(2),s,1)
    s=re.sub(r'(<meta name="twitter:title" content=")[^"]*(")',lambda m:m.group(1)+v+m.group(2),s,1)
    return s
MAXT=65  # Google shows ~60-65 chars; was 70 (Oct 18 2026)
def _generic(t):
    """Brand first, then the year, then both; keeps the meaning of the title."""
    a=re.sub(r" · AgentScout$| \| AgentScout$","",t); b=t.replace(" (2026)",""); c=a.replace(" (2026)","")
    return [a,b,c]
def shorten(f,s,names,c):
    t=_attr(s,r"<title>(.*?)</title>"); 
    if not t: return s
    t=html.unescape(t.strip())
    if len(t)<=MAXT: return s
    cands=[]
    if f.startswith("tools/"):
        n=names.get(f[6:-5])
        if n: cands=_generic(t)+[f"{n}: pricing and alternatives · AgentScout",f"{n}: pricing and alternatives",f"{n}: alternatives · AgentScout",f"{n}: alternatives",f"{n} · AgentScout"]
    elif f.startswith("tasks/"):
        x=re.sub(r" \(\d+ tools\)","",t); cands=_generic(t)+[x]+_generic(x)
    elif f.startswith("best/") and f.endswith("-alternatives.html"):
        x=re.sub(r" ?: \d+ similar tools","",t); cands=_generic(t)+[x]+_generic(x)
    elif f.startswith("compare/"):
        x=re.sub(r": Which [^?]*\?"," compared (2026)",t); cands=_generic(t)+[x]+_generic(x)
    else:
        cands=_generic(t)
    for cand in cands:
        if cand!=t and len(cand)<=MAXT: c["title_shortened"]+=1; return _settitle(s,cand)
    if f.startswith("news/"):  # headline is the meaning: keep it whole, just drop the brand suffix
        a=_generic(t)[0]
        if a!=t: c["title_shortened"]+=1; s=_settitle(s,a); t=a
        if len(t)>MAXT:  # search-result <title> only: cut at a clause break, else at a word with "…"; the H1 and og:title keep the full headline
            cut=[t[:i].rstrip(" :,;-–") for sep in (" (",", ",": "," — "," – "," so "," as "," without "," after "," for ") for i in [m.start() for m in re.finditer(re.escape(sep),t)]]
            cut=[x for x in cut if 45<=len(x)<=MAXT]
            if cut: short=max(cut,key=len)
            else:
                w=t[:MAXT-1].rsplit(" ",1)[0].rstrip(" :,;-–").split(" ")
                while len(w)>4 and w[-1].lower() in ("a","an","the","at","to","and","of","for","with","in","on","into","by","or","your"): w.pop()
                short=" ".join(w).rstrip(" :,;-–")+"…"
            c["title_shortened"]+=1
            return re.sub(r"<title>.*?</title>",f"<title>{html.escape(short,quote=True)}</title>",s,1,flags=re.S)
    c["title_still_long"]+=1
    return s
def twitter(s,c):
    if 'name="twitter:card"' not in s: return s
    add=""
    for tw,og in (("title","og:title"),("description","og:description"),("image","og:image")):
        if f'name="twitter:{tw}"' in s: continue
        v=_attr(s,rf'<meta property="{og}" content="([^"]*)"')
        if v is None and tw=="description": v=_attr(s,r'<meta name="description" content="([^"]*)"')
        if v is None: continue
        add+=f'<meta name="twitter:{tw}" content="{v}">'; c["twitter_"+tw]+=1
    if add: s=s.replace('<meta name="twitter:card"',add+'<meta name="twitter:card"',1)
    return s
HUBS={"best/index.html":("Best-of lists","best/"),"s/index.html":("Popular searches","s/"),"for/index.html":("AI agents by role","for/"),"categories/index.html":("Categories","categories/")}
def hubld(f,s,c):
    s=re.sub(r"<!--xl:ldhub-->.*?<!--/xl:ldhub-->","",s,flags=re.S)
    name,path=HUBS[f]; d=path
    links=[];seen=set()
    main=s.split("<main",1)[-1].split('<section id="nlblock"')[0]
    for h,txt in re.findall(r'<a [^>]*href="([a-z0-9-]+\.html)"[^>]*>(.*?)</a>',main,re.S):
        if h=="index.html" or h in seen: continue
        import os
        if not os.path.exists(d+h): continue
        nm=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",txt))).strip()
        if not nm: continue
        seen.add(h); links.append((B+d+h,nm))
    ld=[{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":name,"item":B+path}]}]
    if links: ld.append({"@context":"https://schema.org","@type":"ItemList","name":name,"numberOfItems":len(links),"itemListElement":[{"@type":"ListItem","position":i+1,"url":u,"name":n} for i,(u,n) in enumerate(links)]})
    blk="<!--xl:ldhub-->"+"".join('<script type="application/ld+json">'+json.dumps(x,ensure_ascii=False).replace("</","<\\/")+"</script>" for x in ld)+"<!--/xl:ldhub-->"
    c["hub_ld"]+=1; c["hub_items"]+=len(links)
    return s.replace("</head>",blk+"</head>",1)
def run(t):
    import collections; c=collections.Counter(); names={x["slug"]:x["name"] for x in t}
    for f in _groups():
        s0=s=open(f).read()
        s=shorten(f,s,names,c); s=twitter(s,c)
        if f in HUBS: s=hubld(f,s,c)
        if s!=s0: open(f,"w").write(s)
    llms_extra(c)
    print("seo pass:",dict(c))
def _h1(f):
    s=open(f,errors="ignore").read()
    if 'name="robots" content="noindex' in s: return None
    m=re.search(r"<h1[^>]*>(.*?)</h1>",s,re.S)
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>","",m.group(1)))).strip() if m else None
def llms_extra(c=None):
    """llms.txt sections for every indexable best-of, alternatives, search, role, task and free-tool page (idempotent, between markers)."""
    import os
    if not os.path.exists("llms.txt"): return
    L=open("llms.txt").read(); L=re.sub(r"\n?<!-- pages:start -->.*?<!-- pages:end -->\n?","\n",L,flags=re.S).rstrip()+"\n"
    def sec(name,files,strip=""):
        out=[]
        for f in files:
            if f.endswith("index.html"): continue
            h=_h1(f)
            if h: out.append(f"- [{h.replace(strip,'').strip()}]({B}{f})")
        return [f"## {name}",""]+out+[""] if out else []
    best=sorted(glob.glob("best/*.html")); alt=[f for f in best if f.endswith("-alternatives.html")]
    S=["<!-- pages:start -->",""]+sec("Best-of lists",[f for f in best if f not in alt]," (2026)")+sec("Alternatives pages",alt," (2026)")+sec("Popular searches",sorted(glob.glob("s/*.html"))," (2026)")+sec("AI agents by role",sorted(glob.glob("for/*.html"))," (2026)")+sec("AI agents by task",sorted(glob.glob("tasks/*.html")))+sec("Free tools",sorted(glob.glob("free-tools/*.html")))+["<!-- pages:end -->"]
    open("llms.txt","w").write(L+"\n"+"\n".join(S)+"\n")
    if c is not None: c["llms_pages"]=sum(1 for z in S if z.startswith("- ["))
