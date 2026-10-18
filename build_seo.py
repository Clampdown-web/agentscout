"""Technical SEO pass for the recently added page groups (tool pages, best-of, /s/, /for/, free tools, categories, homepage).
Idempotent post-processing, run at the end of build_site.py:
- shortens tool and /s/ <title>/og:title over 70 chars (keeps the tool name),
- adds twitter:title / twitter:description / twitter:image mirrored from the Open Graph tags when missing,
- adds BreadcrumbList + ItemList JSON-LD to the best/, s/, for/ and categories/ hubs."""
import glob,re,json,html
B="https://agentscouthq.com/"
def _groups():
    return (sorted(glob.glob("tools/*.html"))+sorted(glob.glob("best/*.html"))+sorted(glob.glob("s/*.html"))+sorted(glob.glob("for/*.html"))
        +["free-tools.html"]+sorted(f for f in glob.glob("free-tools/*.html") if not f.endswith("index.html"))+sorted(glob.glob("categories/*.html"))+["index.html"])
def _attr(s,pat):
    m=re.search(pat,s); return m.group(1) if m else None
def _settitle(s,new):
    v=html.escape(new,quote=True)
    s=re.sub(r"<title>.*?</title>",f"<title>{v}</title>",s,1,flags=re.S)
    s=re.sub(r'(<meta property="og:title" content=")[^"]*(")',lambda m:m.group(1)+v+m.group(2),s,1)
    s=re.sub(r'(<meta name="twitter:title" content=")[^"]*(")',lambda m:m.group(1)+v+m.group(2),s,1)
    return s
def shorten(f,s,names,c):
    t=_attr(s,r"<title>(.*?)</title>"); 
    if not t: return s
    t=html.unescape(t.strip())
    if len(t)<=70: return s
    if f.startswith("tools/"):
        n=names.get(f[6:-5])
        if not n: return s
        for cand in (f"{n}: pricing and alternatives · AgentScout",f"{n}: alternatives · AgentScout",f"{n} · AgentScout"):
            if len(cand)<=70: c["title_shortened"]+=1; return _settitle(s,cand)
    elif f.startswith("s/"):
        cand=t.replace(" (2026)","")
        if cand!=t and len(cand)<=70: c["title_shortened"]+=1; return _settitle(s,cand)
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
    print("seo pass:",dict(c))
