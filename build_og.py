"""Per-page share images (Oct 18 2026). Static 1200x630 PNGs in og/<page path>.png for tool, news, category, best-of, /s/, /for/ and
free-tool pages, in the og.png style (white, soft lavender glow, AgentScout wordmark, big title, one key stat, tool logo when we have one).
Sets og:image / twitter:image (+ og:image:width/height/alt) per page; every other page keeps og.png as the fallback.
Images only use stable facts (name, category, pricing, tool counts, story date), are written only when their bytes change, and
images for pages that no longer exist are deleted, so rebuilds don't churn the repo. Run at the end of build_site.py."""
import glob,re,os,json,html,io,hashlib,build_og_neon
from PIL import Image,ImageDraw,ImageFont
B="https://agentscouthq.com/"; W,H=1200,630; OUT="og"
FONT="data/fonts/Inter-Variable.ttf"; CACHE="data/og_cache.json"; TPL="v3"  # bump TPL when the design changes
INK=(17,17,17); MUTED=(94,101,115); ACC=(91,91,247); LINE=(230,232,236); SOFT=(239,239,254)
_fc={}
def F(size,wght):
    k=(size,wght)
    if k not in _fc:
        f=ImageFont.truetype(FONT,size); f.set_variation_by_axes([min(32,max(14,size)),wght]); _fc[k]=f
    return _fc[k]
_base=None
def base():
    global _base
    if _base is None:
        im=Image.new("RGB",(W,H),(255,255,255)); g=Image.new("L",(W,H),0); d=ImageDraw.Draw(g)
        for i in range(60,0,-1):  # soft radial glow at top centre, like og.png
            r=i/60; d.ellipse([W/2-840*r,-560*r,W/2+840*r,560*r],fill=int(255*(1-r)**1.6))
        im.paste(Image.new("RGB",(W,H),SOFT),(0,0),g)
        d=ImageDraw.Draw(im); x,y,s=72,56,1.55  # wordmark (logo-wordmark.svg, drawn natively)
        d.ellipse([x+4.5*s,y+4.5*s,x+22.5*s,y+22.5*s],outline=INK,width=round(3*s))
        d.line([x+20.3*s,y+20.3*s,x+28*s,y+28*s],fill=INK,width=round(3.2*s))
        cx,cy,a,b=x+13.5*s,y+13.5*s,5.3*s,1.2*s
        d.polygon([(cx,cy-a),(cx+b,cy-b),(cx+a,cy),(cx+b,cy+b),(cx,cy+a),(cx-b,cy+b),(cx-a,cy),(cx-b,cy-b)],fill=ACC)
        f=F(33,600); d.text((x+40*s,y+23.5*s),"Agent",font=f,fill=INK,anchor="ls"); d.text((x+40*s+d.textlength("Agent",font=f),y+23.5*s),"Scout",font=f,fill=ACC,anchor="ls")
        d.text((72,H-58),"agentscouthq.com",font=F(26,600),fill=ACC,anchor="ls")
        _base=im
    return _base.copy()
def wrap(d,text,font,maxw,maxl):
    words=text.split(); lines=[]; cur=""
    for w in words:
        t=(cur+" "+w).strip()
        if d.textlength(t,font=font)<=maxw: cur=t
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    if len(lines)>maxl:
        lines=lines[:maxl]; l=lines[-1]
        while d.textlength(l+"…",font=font)>maxw and " " in l: l=l.rsplit(" ",1)[0]
        lines[-1]=l.rstrip(",:;·-")+"…"
    return lines
def render(kind,title,sub,stat,logo=None):
    im=base(); d=ImageDraw.Draw(im)
    pf=F(22,600); pw=d.textlength(kind.upper(),font=pf)+36  # page-type pill, top right
    d.rounded_rectangle([W-72-pw,58,W-72,102],radius=22,fill=(255,255,255),outline=LINE,width=2)
    d.text((W-72-pw/2,81),kind.upper(),font=pf,fill=ACC,anchor="mm")
    x=72; maxw=W-144
    if logo:
        try:
            L=Image.open(logo).convert("RGBA"); L.thumbnail((104,104),Image.LANCZOS)
            tile=Image.new("RGBA",(128,128),(0,0,0,0)); m=Image.new("L",(128,128),0); ImageDraw.Draw(m).rounded_rectangle([0,0,127,127],radius=26,fill=255)
            bg=Image.new("RGBA",(128,128),(255,255,255,255)); bg.alpha_composite(L,((128-L.width)//2,(128-L.height)//2))
            tile.paste(bg,(0,0),m); im.paste(tile,(72,170),tile); ImageDraw.Draw(im).rounded_rectangle([72,170,199,297],radius=26,outline=LINE,width=2)
            d=ImageDraw.Draw(im); x=72+128+32; maxw=W-72-x
        except Exception: pass
    for size,ml in ((68,2),(60,2),(54,3),(48,3)):
        tf=F(size,700); lines=wrap(d,title,tf,maxw,ml)
        if not lines[-1].endswith("…") or size==48: break
    y=168 if not logo else 176; lh=int(size*1.14)
    for l in lines: d.text((x,y),l,font=tf,fill=INK,anchor="la"); y+=lh
    y+=14
    if sub:
        sf=F(28,400)
        for l in wrap(d,sub,sf,W-72-x,2 if len(lines)<3 else 1): d.text((x,y),l,font=sf,fill=MUTED,anchor="la"); y+=38
    if stat:
        stf=F(26,600); sw=d.textlength(stat,font=stf)+40; sy=max(y+18,430)
        sy=min(sy,H-140)
        d.rounded_rectangle([72,sy,72+sw,sy+50],radius=25,fill=SOFT); d.text((72+sw/2,sy+25),stat,font=stf,fill=ACC,anchor="mm")
    im=im.quantize(colors=128,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    b=io.BytesIO(); im.save(b,"PNG",optimize=True); return b.getvalue()
def _h1(s):
    m=re.search(r"<h1[^>]*>(.*?)</h1>",s,re.S)
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>","",m.group(1)))).strip() if m else ""
def _desc(s):
    m=re.search(r'<meta name="description" content="([^"]*)"',s); return html.unescape(m.group(1)) if m else ""
def _n(s):
    m=re.search(r'"numberOfItems": ?(\d+)',s); return int(m.group(1)) if m else None
def _num(d):
    m=re.search(r"\b(\d[\d,]*) (?:link-checked |similar |free |open-source )?(?:[A-Za-z&/-]+ ){0,4}?(?:tools|agents|picks|servers|frameworks|apps|models)\b",d); return m.group(1) if m else None
def run(t):
    import build_extras
    bys={x["slug"]:x for x in t}; cnt={}
    for x in t: k=build_extras.catslug(x["category"]); cnt[k]=cnt.get(k,0)+1
    jobs=[]
    for f in sorted(glob.glob("tools/*.html")): jobs.append(("tool",f))
    for f in sorted(glob.glob("categories/*.html")): jobs.append(("category",f))
    for f in sorted(glob.glob("best/*.html")): jobs.append(("best",f))
    for f in sorted(glob.glob("s/*.html")): jobs.append(("search",f))
    for f in sorted(glob.glob("mcp/*.html")): jobs.append(("best",f))
    for f in sorted(glob.glob("for/*.html")): jobs.append(("role",f))
    for f in ["free-tools.html"]+sorted(glob.glob("free-tools/*.html")): jobs.append(("free",f))
    for f in sorted(glob.glob("news/**/*.html",recursive=True)): jobs.append(("news",f))
    keep=set(); c={"pages":0,"written":0,"same":0,"skipped":0}
    cache=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    for kind,f in jobs:
        if not os.path.exists(f): continue
        s=open(f).read()
        if 'name="robots" content="noindex' in s or 'property="og:image"' not in s: c["skipped"]+=1; continue
        h1=_h1(s); d=_desc(s); n=_n(s); logo=None; sub=None; stat=None; label=kind
        if kind=="tool":
            x=bys.get(f[6:-5])
            if not x: c["skipped"]+=1; continue
            title=x["name"]; sub=x["description"]; label="AI agent tool"; logo=x.get("logo") if x.get("logo") and os.path.exists(x["logo"]) else None
            stat=f'{x["category"][0].upper()+x["category"][1:]} · {x["pricing"]}'
            if len(stat)>60: stat=x["category"][0].upper()+x["category"][1:]+" · link-checked"
        elif kind=="category":
            if f.endswith("index.html"): title=h1 or "AI agent tool categories"; stat=f"{len(t):,} link-checked tools · {len(cnt)} categories"; label="Categories"
            else:
                k=f[11:-5]; title=h1; stat=f"{cnt[k]:,} link-checked tools" if cnt.get(k) else None; label="Category"
        elif kind=="news":
            title=h1 or "AI agent news"; label="AI agent news"
            m=re.search(r'"datePublished": ?"([0-9T:.+-]+Z?)"',s)
            if m and not f.endswith("index.html"):  # story date in Pacific time
                import datetime; from zoneinfo import ZoneInfo
                try: stat=datetime.datetime.fromisoformat(m.group(1).replace("Z","+00:00")).astimezone(ZoneInfo("America/Los_Angeles")).strftime("%b %-d, %Y")
                except ValueError: stat=None
            sub=None if f.endswith("index.html") else (d if len(d)<150 else None)
        elif kind=="free":
            title=h1; label="Free tool"; stat="Free · runs in your browser · no sign-up"
        else:
            title=h1; label={"best":"Best-of list","search":"Search","role":"By role"}[kind]
            if f.endswith("-alternatives.html"): label="Alternatives"
            k=n or _num(d); stat=(f"{int(str(k).replace(',','')):,} tools" if k else None)
            if stat and kind=="best" and not f.endswith("-alternatives.html") and not f.endswith("index.html"): stat=f"Top {k} · ranking method stated"
            if f.endswith("index.html"): stat=f"{n} {dict(best='pages',search='searches',role='roles')[kind]}" if n else None
        if not title: c["skipped"]+=1; continue
        neon=None
        if f.startswith("mcp/"):  # neon share cards for MCP pages (Oct 23 2026); counts from tools.json
            nm=sum(1 for x in t if x["category"]=="MCP servers"); foot=f"· {len(t):,} AI agent tools · {nm} MCP servers"
            sl=[m for m in dict.fromkeys(re.findall(r'tools/([a-z0-9-]+)\.html',s)) if m in bys][:3]
            if f=="mcp/connect.html":
                label="MCP server"; title=title; sub="Search AgentScout from Claude, Cursor, VS Code or any MCP client"
                cards=[dict(name=f"{len(t):,}",tag="AI agent tools",size=44),dict(name=f"{nm}",tag="MCP servers",size=44),dict(name="Free",tag="read-only · no sign-up",size=44)]
            elif f in ("mcp/link-status.html","mcp/status/index.html","mcp/pricing.html") or len(sl)<3:
                label="MCP servers"; sub=None
                cards=[dict(name=f"{nm}",tag="MCP servers",size=44),dict(name=f"{len(t):,}",tag="AI agent tools",size=44),dict(name=("Pricing" if "pricing" in f else "Link check"),tag=("free, freemium, paid" if "pricing" in f else "listing + GitHub links"),size=40)]
            else:
                label="MCP servers"; k=n or _num(d); sub=(f"{k} MCP servers, ranked by GitHub stars and activity" if k and not f.endswith("index.html") else "Ranked by GitHub stars and activity, sorted by task")
                cards=[dict(name=bys[x]["name"],tag=("Top pick" if f.endswith("index.html") else f"#{i+1} by GitHub stars"),logo=bys[x].get("logo")) for i,x in enumerate(sl)]
            title=re.sub(r"\s*\(2026\)$","",title); neon=(label,title,sub,cards,foot)
        if kind in ("category","best","search","role","free") and not sub and d:  # one line of real context from the page description
            m=re.search(r"including ([^.]+?)(?:\.|$)",d)
            sub=("Including "+m.group(1).strip()) if m and not f.endswith("index.html") else re.split(r"(?<=[.!?])\s",d)[0]
        if kind in ("best","search","role") and not stat:
            m=re.match(r"(\d[\d,]*) ",d)
            if m: stat=f"{m.group(1)} tools"
        title=re.sub(r"\s*\(2026\)$","",title)
        out=f"{OUT}/{f[:-5]}.png"; keep.add(out); c["pages"]+=1
        key=hashlib.sha1(json.dumps([TPL,"neon1",neon] if neon else [TPL,label,title,sub,stat,logo,hashlib.sha1(open(logo,"rb").read()).hexdigest() if logo else ""]).encode()).hexdigest()[:16]
        if cache.get(out)==key and os.path.exists(out): c["same"]+=1  # inputs unchanged: skip rendering
        else:
            png=build_og_neon.render(F,wrap,*neon,accent="MCP") if neon else render(label,title,sub,stat,logo); os.makedirs(os.path.dirname(out),exist_ok=True)
            if os.path.exists(out) and open(out,"rb").read()==png: c["same"]+=1
            else: open(out,"wb").write(png); c["written"]+=1
            cache[out]=key
        url=B+out+(f"?v={key[:10]}" if neon else ""); alt=html.escape(f"{title}, on AgentScout",quote=True)
        s2=re.sub(r'<meta property="og:image" content="[^"]*">(?:<meta property="og:image:(?:width|height|alt)" content="[^"]*">)*',
                  f'<meta property="og:image" content="{url}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{alt}">',s,1)
        s2=re.sub(r'<meta name="twitter:image" content="[^"]*">',f'<meta name="twitter:image" content="{url}">',s2,1)
        if s2!=s: open(f,"w").write(s2)
    for p in glob.glob(f"{OUT}/**/*.png",recursive=True):  # images whose page is gone or redirected
        if p not in keep: os.remove(p); c["removed"]=c.get("removed",0)+1
    json.dump({k:v for k,v in sorted(cache.items()) if k in keep},open(CACHE,"w"),indent=0)
    sz=sum(os.path.getsize(p) for p in keep)
    print("og images:",c,f"total {sz/1e6:.1f} MB")
if __name__=="__main__":
    run(json.load(open("tools.json")))
