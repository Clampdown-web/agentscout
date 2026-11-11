"""Per-page share images. Static 1200x630 PNGs for tool, news, category, best-of, /s/, /for/,
free-tool, MCP, and the static pages that used to fall back to the white og.png.
Every card is the dark neon style: #0b0d12 background, purple/cyan accents, AgentScout wordmark, white text.
Sets og:image / twitter:image (+ width/height/alt) and a ?v= cache-buster so X refetches.
Images only use stable facts (name, category, pricing, story date). Catalog counts on a card are the
generic pitch from build_counts (5,000+ / 3,000+) or the live tools.json figures on MCP cards.
Written only when bytes change; images for pages that no longer exist are deleted.
These PNGs are produced by this build script. The Cloudflare image worker is not involved and is not deployed from here.
Run at the end of build_site.py. stamp_share_tags() runs again after later passes rewrite submit/sponsor."""
import glob,re,os,json,html,io,hashlib,build_og_neon
from PIL import Image,ImageDraw,ImageFont,ImageFilter
B="https://agentscouthq.com/"; W,H=1200,630; OUT="og"
FONT="data/fonts/Inter-Variable.ttf"; CACHE="data/og_cache.json"; TPL="v4"  # bump TPL when the design changes
TPL_FILE="data/detail.tpl"
BG=(11,13,18); INK=(244,246,252); MUTED=(186,194,208); PUR=(147,147,255); CYAN=(45,226,230)
CHIP=(23,26,34); LINE=(70,84,120)
_fc={}
def F(size,wght):
    k=(size,wght)
    if k not in _fc:
        f=ImageFont.truetype(FONT,size); f.set_variation_by_axes([min(32,max(14,size)),wght]); _fc[k]=f
    return _fc[k]
def _px(im):
    return im.get_flattened_data() if hasattr(im,"get_flattened_data") else im.getdata()
def logo_tile(path,inner,tile,radius):
    """Rounded chip for a tool mark. Dark marks sit on a light chip so they stay visible; others sit on the card color."""
    L=Image.open(path).convert("RGBA"); L.thumbnail((inner,inner),Image.LANCZOS)
    lum=[0.2126*r+0.7152*g+0.0722*b for r,g,b,a in _px(L) if a>200]
    light=bool(lum) and (sum(lum)/len(lum))<96
    bg=(244,246,251,255) if light else (CHIP[0],CHIP[1],CHIP[2],255)
    plate=Image.new("RGBA",(tile,tile),bg); plate.alpha_composite(L,((tile-L.width)//2,(tile-L.height)//2))
    m=Image.new("L",(tile,tile),0); ImageDraw.Draw(m).rounded_rectangle([0,0,tile-1,tile-1],radius=radius,fill=255)
    out=Image.new("RGBA",(tile,tile),(0,0,0,0)); out.paste(plate,(0,0),m)
    return out
def _wordmark(d,x,y,s):
    d.ellipse([x+4.5*s,y+4.5*s,x+22.5*s,y+22.5*s],outline=INK,width=round(3*s))
    d.line([x+20.3*s,y+20.3*s,x+28*s,y+28*s],fill=INK,width=round(3.2*s))
    cx,cy,a,b=x+13.5*s,y+13.5*s,5.3*s,1.2*s
    d.polygon([(cx,cy-a),(cx+b,cy-b),(cx+a,cy),(cx+b,cy+b),(cx,cy+a),(cx-b,cy+b),(cx-a,cy),(cx-b,cy-b)],fill=CYAN)
    f=F(33,600); d.text((x+40*s,y+23.5*s),"Agent",font=f,fill=INK,anchor="ls")
    d.text((x+40*s+d.textlength("Agent",font=f),y+23.5*s),"Scout",font=f,fill=PUR,anchor="ls")
_base=None
def base():
    global _base
    if _base is None:
        im=Image.new("RGB",(W,H),BG); g=Image.new("RGB",(W,H),(0,0,0)); d=ImageDraw.Draw(g)
        d.ellipse([W-560,-280,W+180,420],fill=(78,48,190))
        d.ellipse([-220,H-340,560,H+220],fill=(8,120,150))
        g=g.filter(ImageFilter.GaussianBlur(110)); im=Image.blend(im,g,0.42)
        d=ImageDraw.Draw(im); _wordmark(d,72,56,1.55)
        d.text((72,H-58),"agentscouthq.com",font=F(26,600),fill=CYAN,anchor="ls")
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
    pf=F(22,600); label=kind.upper(); pw=d.textlength(label,font=pf)+36
    d.rounded_rectangle([W-72-pw,58,W-72,102],radius=22,fill=(16,22,36),outline=CYAN,width=2)
    d.text((W-72-pw/2,81),label,font=pf,fill=INK,anchor="mm")
    x=72; maxw=W-144
    if logo:
        try:
            tile=logo_tile(logo,104,128,26); im.paste(tile,(72,170),tile)
            ImageDraw.Draw(im).rounded_rectangle([72,170,199,297],radius=26,outline=LINE,width=2)
            d=ImageDraw.Draw(im); x=72+128+32; maxw=W-72-x
        except Exception: pass
    for size,ml in ((68,2),(60,2),(54,3),(48,3)):
        tf=F(size,700); lines=wrap(d,title,tf,maxw,ml)
        if not lines[-1].endswith("…") or size==48: break
    y=168 if not logo else 176; lh=int(size*1.14)
    for l in lines: d.text((x,y),l,font=tf,fill=INK,anchor="la"); y+=lh
    y+=14
    if sub:
        sf=F(28,500)
        for l in wrap(d,sub,sf,W-72-x,2 if len(lines)<3 else 1): d.text((x,y),l,font=sf,fill=MUTED,anchor="la"); y+=38
    if stat:
        stf=F(26,600); sw=d.textlength(stat,font=stf)+40; sy=max(y+18,430)
        sy=min(sy,H-140)
        if 72+sw>W-72: sw=W-144
        d.rounded_rectangle([72,sy,72+sw,sy+50],radius=25,fill=(14,36,44),outline=CYAN,width=2)
        d.text((72+sw/2,sy+25),stat,font=stf,fill=INK,anchor="mm")
    im=im.quantize(colors=128,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert("RGB")
    d=ImageDraw.Draw(im); d.rectangle([0,0,W//2,5],fill=PUR); d.rectangle([W//2,0,W,5],fill=CYAN)
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
def pitches():
    """Generic catalog lines. Floored to the thousand so a card stays true as the directory grows."""
    import build_counts
    c=build_counts.load() or {}
    return build_counts.pitch_tools_label(c.get("tools") or 0), build_counts.pitch_mcp_label(c.get("mcp_servers") or 0)
def static_specs():
    tools_pitch,mcp_pitch=pitches()
    return [
        ("index.html","og.png","AgentScout","The AI agent tools actually worth trying.","Curated, link-checked, updated daily.",None),
        ("submit.html","og/submit.png","Submit","Submit your AI agent tool","Free community listing. We review every submission and check the links.",tools_pitch),
        ("sponsor.html","og/sponsor.png","Sponsor","Get Your AI Agent or MCP Server in Front of Builders Ready to Try It","Free listing, fast-track, category pin, or a sitewide sponsor.",tools_pitch),
        ("newsletter.html","og/newsletter.png","Newsletter","AgentScout Weekly","One short email a week with the best new AI agents, launches and what's worth trying.",None),
        ("mcp-test-report.html","og/mcp-test-report.png","MCP","MCP server test report","Protocol test of a public MCP server, with a private report and PDF. Bundle with an AI visibility check.",mcp_pitch),
        ("ai-visibility-check.html","og/ai-visibility-check.png","Check","AI visibility check","How a public site shows up in AI answers, with rivals and cited sources. Bundle with the MCP server test.",None),
        ("refunds.html","og/refunds.png","Refunds","Refund policy","When a paid listing, sponsorship, Bot Store download, or paid report can be refunded.",None),
        ("new.html","og/new.png","New","New AI agent tools","The newest AI agent tools added in the last 30 days.",tools_pitch),
        ("bot-store/index.html","og/bot-store.png","Bot Store","Bot Store","Flagship bots, role packs, and the 4-bot bundle.","$39–$149"),
    ]
def apply_meta(s,url,alt):
    """Absolute image URL, 1200x630, alt, summary_large_image, and a matching twitter:image."""
    block=(f'<meta property="og:image" content="{url}">'
           f'<meta property="og:image:width" content="1200">'
           f'<meta property="og:image:height" content="630">'
           f'<meta property="og:image:alt" content="{alt}">')
    if 'property="og:image"' in s:
        s=re.sub(r'<meta property="og:image" content="[^"]*">(?:<meta property="og:image:(?:width|height|alt)" content="[^"]*">)*',block,s,1)
    elif 'property="og:site_name"' in s:
        s=s.replace('<meta property="og:site_name" content="AgentScout">','<meta property="og:site_name" content="AgentScout">'+block,1)
    if 'name="twitter:image"' in s:
        s=re.sub(r'<meta name="twitter:image" content="[^"]*">',f'<meta name="twitter:image" content="{url}">',s,1)
    elif 'name="twitter:card"' in s:
        s=s.replace('<meta name="twitter:card"',f'<meta name="twitter:image" content="{url}"><meta name="twitter:card"',1)
    s=re.sub(r'<meta name="twitter:card" content="(?!summary_large_image")[^"]*">','<meta name="twitter:card" content="summary_large_image">',s,1)
    if 'name="twitter:card"' not in s and 'name="twitter:image"' in s:
        s=s.replace(f'<meta name="twitter:image" content="{url}">',f'<meta name="twitter:image" content="{url}"><meta name="twitter:card" content="summary_large_image">',1)
    return s
def _ck(v):
    return v.get("k") if isinstance(v,dict) else v
def _ca(v):
    return v.get("alt") if isinstance(v,dict) else None
def _page_for(image):
    if image=="og.png": return "index.html"
    if image.startswith("og/") and image.endswith(".png"): return image[3:-4]+".html"
    return None
def sync_template(version,alt):
    if not os.path.exists(TPL_FILE): return
    s=open(TPL_FILE).read(); s2=apply_meta(s,f"{B}og.png?v={version}",alt)
    if s2!=s: open(TPL_FILE,"w").write(s2)
def stamp_share_tags():
    """Put cache-busted absolute image URLs back after a later pass rewrites a page from the template."""
    cache=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    home=cache.get("og.png"); home_key=_ck(home)
    if not home_key: return
    home_url=f"{B}og.png?v={home_key[:10]}"
    home_alt=_ca(home) or html.escape("The AI agent tools actually worth trying, on AgentScout",quote=True)
    for image,entry in cache.items():
        page=_page_for(image)
        if not page or not os.path.exists(page): continue
        key=_ck(entry)
        if not key: continue
        s=open(page).read(); s2=apply_meta(s,f"{B}{image}?v={key[:10]}",_ca(entry) or home_alt)
        if s2!=s: open(page,"w").write(s2)
    bare=re.compile(r'https://agentscouthq\.com/og\.png(?!\?v='+re.escape(home_key[:10])+r')(?:\?v=[^"\s]*)?')
    for root,dirs,files in os.walk("."):
        dirs[:]=[d for d in dirs if d not in (".git","node_modules","preview","bot-packages")]
        for fn in files:
            if not fn.endswith(".html"): continue
            page=os.path.normpath(os.path.join(root,fn))
            if page.startswith("./"): page=page[2:]
            try: s=open(page,encoding="utf-8").read()
            except UnicodeError: continue
            if "og.png" not in s: continue
            s2=bare.sub(home_url,s)
            m=re.search(r'<meta property="og:image" content="([^"]*)"',s2)
            if m and "/og.png" in m.group(1): s2=apply_meta(s2,home_url,home_alt)
            if s2!=s: open(page,"w").write(s2)
    sync_template(home_key[:10],home_alt)
def run(t):
    import build_extras
    bys={x["slug"]:x for x in t}; cnt={}
    for x in t: k=build_extras.catslug(x["category"]); cnt[k]=cnt.get(k,0)+1
    jobs=[]; extra={}
    for page,out,label,title,sub,stat in static_specs():
        jobs.append(("card",page)); extra[page]=(out,label,title,sub,stat)
    for f in sorted(glob.glob("bot-store/*/index.html")): jobs.append(("store",f))
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
        if 'property="og:image"' not in s: c["skipped"]+=1; continue
        if 'name="robots" content="noindex' in s and not f.startswith("tools/"): c["skipped"]+=1; continue
        h1=_h1(s); d=_desc(s); n=_n(s); logo=None; sub=None; stat=None; label=kind; fixed=None
        if kind=="card":
            fixed,label,title,sub,stat=extra[f]
        elif kind=="store":
            title=h1 or "Bot Store"; sub=d; label="Bot Store"; stat="AI agent pack"
        elif kind=="tool":
            x=bys.get(f[6:-5])
            if not x: c["skipped"]+=1; continue
            title=x["name"]; sub=x["description"]; label="MCP server" if x.get("category")=="MCP servers" else "AI agent tool"
            logo=x.get("logo") if x.get("logo") and os.path.exists(x["logo"]) else None
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
        out=fixed or f"{OUT}/{f[:-5]}.png"; keep.add(out); c["pages"]+=1
        if c["pages"]%500==0: print("og progress",c,flush=True)
        import build_counts
        sig=build_counts.signature()
        logo_hash=hashlib.sha1(open(logo,"rb").read()).hexdigest() if logo else ""
        body=[TPL,"neon2",neon] if neon else [TPL,label,title,sub,stat,logo,logo_hash]
        visual=" ".join(str(x) for x in (label,title,sub,stat,neon))
        depends=any(isinstance(n,int) and n and (str(n) in visual or f"{n:,}" in visual) for n in sig)
        if depends: body.append(sig)  # count-only changes skip cards that do not print a count
        key=hashlib.sha1(json.dumps(body).encode()).hexdigest()[:16]
        alt=html.escape(f"{title.rstrip('.')}, on AgentScout",quote=True)
        if _ck(cache.get(out))==key and os.path.exists(out): c["same"]+=1
        else:
            png=build_og_neon.render(F,wrap,*neon,accent="MCP") if neon else render(label,title,sub,stat,logo)
            parent=os.path.dirname(out)
            if parent: os.makedirs(parent,exist_ok=True)
            if os.path.exists(out) and open(out,"rb").read()==png: c["same"]+=1
            else: open(out,"wb").write(png); c["written"]+=1
        cache[out]={"k":key,"alt":alt}
        url=f"{B}{out}?v={key[:10]}"
        s2=apply_meta(s,url,alt)
        if s2!=s: open(f,"w").write(s2)
    for p in glob.glob(f"{OUT}/**/*.png",recursive=True):  # images whose page is gone or redirected
        if p not in keep: os.remove(p); c["removed"]=c.get("removed",0)+1
    json.dump({k:v for k,v in sorted(cache.items()) if k in keep},open(CACHE,"w"),indent=0)
    stamp_share_tags()
    sz=sum(os.path.getsize(p) for p in keep if os.path.exists(p))
    print("og images:",c,f"total {sz/1e6:.1f} MB")
if __name__=="__main__":
    run(json.load(open("tools.json")))
