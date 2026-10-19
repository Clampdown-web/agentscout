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
def _hash(p):
    s=open(p,encoding="utf-8",errors="replace").read()
    for r,v in _V: s=r.sub(v,s)
    return hashlib.sha1(s.encode()).hexdigest()[:16]
def _gitdate(p):
    try:
        d=subprocess.run(["git","log","-1","--format=%cI","--",p],capture_output=True,text=True,timeout=20).stdout.strip()
        return datetime.datetime.fromisoformat(d).astimezone(ZoneInfo("America/Los_Angeles")).date().isoformat() if d else None
    except Exception: return None
def run():
    if not os.path.exists("sitemap.xml"): return
    os.makedirs("data",exist_ok=True)
    st=json.load(open("data/lastmod.json")) if os.path.exists("data/lastmod.json") else {}
    sm=open("sitemap.xml").read(); today=_today(); ch=0
    def rep(m):
        nonlocal ch
        u=m.group(1); p=_file(u)
        if not os.path.exists(p): return m.group(0)
        h=_hash(p); old=st.get(u)
        if not old: st[u]=[h,_gitdate(p) or today]
        elif old[0]!=h: st[u]=[h,today]; ch+=1
        return f"<url><loc>{u}</loc><lastmod>{st[u][1]}</lastmod></url>"
    sm2=re.sub(r"<url><loc>([^<]+)</loc><lastmod>[^<]*</lastmod></url>",rep,sm)
    if sm2!=sm: open("sitemap.xml","w").write(sm2)
    live=set(re.findall(r"<loc>([^<]+)</loc>",sm2))
    st={k:v for k,v in st.items() if k in live}
    json.dump(dict(sorted(st.items())),open("data/lastmod.json","w"),indent=0)
    print(f"lastmod: {len(live)} urls, {ch} changed today, {len({v[1] for v in st.values()})} distinct dates")
if __name__=="__main__": run()
