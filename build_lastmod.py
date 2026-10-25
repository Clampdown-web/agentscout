"""Accurate per-URL <lastmod> in sitemap.xml (Oct 18 2026). Runs at exit of every generator that imports build_extras (after featured).
Each URL's file is hashed with volatile bits stripped (asset ?v= strings, ISO timestamps, "Links checked" dates). The stored date only
moves when the hash changes. First sighting is seeded from the file's last git commit date (PT), else today. State: data/lastmod.json."""
import re,os,json,hashlib,subprocess,datetime
from zoneinfo import ZoneInfo
B="https://agentscouthq.com/"
def _today(): return datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
def _file(u):
    p=u[len(B):] or "index.html"
    if p.endswith("/"): p+="index.html"
    return p
_V=[(re.compile(r"\?v=\d+"),""),(re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(\.\d+)?Z?"),""),
    (re.compile(r"Links checked [A-Z][a-z]{2} \d{1,2}, \d{4}"),""),(re.compile(r'"dateModified": ?"[^"]*"'),""),
    (re.compile(r'<section id="nlblock".*?</section>',re.S),""),
    (re.compile(r'<!-- ga4 -->.*?<!-- /ga4 -->',re.S),""),(re.compile(r' https://\*\.google-analytics\.com https://\*\.analytics\.google\.com https://www\.googletagmanager\.com| https://www\.googletagmanager\.com'),"")]  # GA4 tag + CSP are page chrome (Oct 19 2026)  # sitewide signup box is page chrome, not content (Oct 18 2026)
_V+=[(re.compile(r'<span id="pfm".*?</span></span>|<span id="pfm"[^>]*></span>'),""),(re.compile(r' data-pagefind-body| data-pagefind-weight="10"'),""),(re.compile(r'<a data-navsearch [^>]*>[^<]*</a>'),"")]  # site-search markers are not content (Oct 21 2026)
def _hash(p):
    s=open(p,encoding="utf-8",errors="replace").read()
    for r,v in _V: s=r.sub(v,s)
    return hashlib.sha1(s.encode()).hexdigest()[:16]
def _gitdate(p):
    try:
        d=subprocess.run(["git","log","-1","--format=%cI","--",p],capture_output=True,text=True,timeout=20).stdout.strip()
        return datetime.datetime.fromisoformat(d).astimezone(ZoneInfo("America/Los_Angeles")).date().isoformat() if d else None
    except Exception: return None
_TL=re.compile(r'tools/([a-z0-9][a-z0-9-]*)\.html')
def _tooldates(st,today):
    """Real per-tool content dates (Oct 22 2026, SEO audit): a tool's date moves only when its tools.json record or rich data changes.
    First sighting is seeded from the tool's own dates (rich 'updated', else 'added'), else its page's git date."""
    try: t=json.load(open("tools.json"))
    except Exception: return {}
    try: R=json.load(open("tool_rich.json"))
    except Exception: R={}
    if isinstance(R,list): R={r.get("slug"):r for r in R if isinstance(r,dict)}
    V={"verified","github_stars","stars","stars_checked","new","featured","last_checked","link_ok","status_code"}  # daily-refreshed fields are not content changes
    TS=st.setdefault("__tools__",{}); out={}
    for x in t:
        sl=x.get("slug"); 
        if not sl: continue
        r=R.get(sl) if isinstance(R,dict) else None
        rec={k:v for k,v in x.items() if k not in V}
        h=hashlib.sha1(json.dumps([rec,r],sort_keys=True,default=str).encode()).hexdigest()[:16]
        old=TS.get(sl)
        if not old:
            seed=max([d for d in ((r or {}).get("updated") if isinstance(r,dict) else None,x.get("added")) if isinstance(d,str) and re.match(r"\d{4}-\d{2}-\d{2}$",d) and d<=today] or [""]) or _gitdate(f"tools/{sl}.html") or today
            TS[sl]=[h,seed]
        elif old[0]!=h: TS[sl]=[h,today]
        out[sl]=TS[sl][1]
    st["__tools__"]={k:v for k,v in TS.items() if k in out}
    return out
def run():
    if not os.path.exists("sitemap.xml"): return
    os.makedirs("data",exist_ok=True)
    st=json.load(open("data/lastmod.json")) if os.path.exists("data/lastmod.json") else {}
    if st.get("__v__")!=2: st={"__v__":2}  # v2 (Oct 22 2026): reseed once from real dates instead of the old blanket build dates
    sm=open("sitemap.xml").read(); today=_today(); ch=0
    T=_tooldates(st,today)
    def rep(m):
        nonlocal ch
        u=m.group(1); p=_file(u)
        if not os.path.exists(p): return m.group(0)
        if u.startswith(B+"tools/") and p[6:-5] in T: return f"<url><loc>{u}</loc><lastmod>{T[p[6:-5]]}</lastmod></url>"
        body=open(p,encoding="utf-8",errors="replace").read()
        sl=sorted(set(_TL.findall(body))&set(T))
        if len(sl)>=3:  # list pages: date of the newest change among the tools they list, or of the list itself changing
            h=hashlib.sha1(" ".join(sl).encode()).hexdigest()[:16]; old=st.get(u)
            if not old or old[0]!="L"+h: st[u]=["L"+h,(today if old else (_gitdate(p) or today))]; ch+=bool(old)
            d=max([st[u][1]]+[T[s] for s in sl]); d=min(d,today)
            return f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>"
        h=_hash(p); old=st.get(u)
        if not old: st[u]=[h,_gitdate(p) or today]
        elif old[0]!=h: st[u]=[h,today]; ch+=1
        return f"<url><loc>{u}</loc><lastmod>{st[u][1]}</lastmod></url>"
    sm2=re.sub(r"<url><loc>([^<]+)</loc><lastmod>[^<]*</lastmod></url>",rep,sm)
    if sm2!=sm: open("sitemap.xml","w").write(sm2)
    live=set(re.findall(r"<loc>([^<]+)</loc>",sm2))
    st={k:v for k,v in st.items() if k in live or k.startswith("__")}
    json.dump(dict(sorted(st.items())),open("data/lastmod.json","w"),indent=0)
    ds=re.findall(r"<lastmod>([^<]+)</lastmod>",sm2)
    print(f"lastmod: {len(live)} urls, {ch} changed today, {len(set(ds))} distinct dates, {sum(d==today for d in ds)} dated today")
if __name__=="__main__": run()
