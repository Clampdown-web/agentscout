#!/usr/bin/env python3
"""Logo checks (Oct 18, 2026 PT).
  python3 scripts/check_logos.py            local gate: every tool in tools.json has a valid local logo (same as build), and in the
                                              built HTML every tool link in a listing (table cell, list item, card, inline
                                              'Related:' list) shows the tool's logo (build_logocheck.listing_missing)
  python3 scripts/check_logos.py --online   + flag logos that are a maintainer's personal GitHub avatar (User-owned repo,
                                              logo ~ owner avatar) unless listed in data/logo_review.json
  python3 scripts/check_logos.py --placeholders   re-search official sources (site icons, logo/icon files in the repo, custom
                                              social preview) for tools on the AgentScout-made placeholder list and print candidates
  python3 scripts/check_logos.py --live     + crawl https://agentscouthq.com (sitemap + api/tools.json): every logo <img>
                                              must return 200 with a real image, and every tool card / tool list item must
                                              carry a logo <img> (no letter-only fallbacks)
Exit code 1 on any failure. Report lines go to stdout."""
import os,sys,re,json,io,subprocess,urllib.request,urllib.parse,concurrent.futures as cf,warnings
warnings.filterwarnings("ignore")
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT); os.chdir(ROOT)
import build_logocheck as L
from PIL import Image
BASE="https://agentscouthq.com/"
def get(u,t=30,tries=3):
    for k in range(tries):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"AgentScout-logocheck"}),timeout=t)
            return r.status,r.headers.get("Content-Type",""),r.read()
        except urllib.error.HTTPError as e:
            if e.code<500 or k==tries-1: return e.code,"",b""
        except Exception as e:
            if k==tries-1: return 0,str(e),b""
        __import__("time").sleep(2*(k+1))
def vec(im):
    im=im.convert("RGBA"); bg=Image.new("RGBA",im.size,"white"); bg.alpha_composite(im)
    return list(bg.convert("L").resize((16,16)).getdata())
def online(tools):
    R=json.load(open("data/logo_review.json")) if os.path.exists("data/logo_review.json") else {}
    allow={**R.get("ok",{}),**R.get("pending",{}),**R.get("agentscout_placeholder",{})}
    if R.get("pending"): print(f"online: {len(R['pending'])} tools still on the pending list (personal avatar, no official logo): "+", ".join(R["pending"]))
    bad=[]; seen={}
    for x in tools:
        m=re.match(r"https?://github\.com/([^/]+)",x.get("github") or "")
        if not m or x["slug"] in allow: continue
        o=m.group(1).lower()
        if o not in seen:
            r=subprocess.run(["gh","api","users/"+o,"--jq","[.type,.avatar_url]"],capture_output=True,text=True)
            try: seen[o]=json.loads(r.stdout)
            except Exception: seen[o]=None
        if not seen[o] or seen[o][0]!="User": continue
        s,ct,b=get(seen[o][1]+("&" if "?" in seen[o][1] else "?")+"s=64")
        if s!=200: continue
        a=vec(Image.open(io.BytesIO(b))); l=vec(Image.open(x["logo"]))
        if sum(abs(p-q) for p,q in zip(a,l))/256<20: bad.append((x["slug"],x["category"],f"logo is the personal GitHub avatar of {o}"))
    return bad
CARD=re.compile(r'<a [^>]*href="(?:\.\./|/)?tools/([a-z0-9-]+)\.html"[^>]*>(.{0,400}?)</a>',re.S)
def live(tools):
    bad=[]
    s,ct,b=get(BASE+"sitemap.xml"); urls=re.findall(r"<loc>([^<]+)</loc>",b.decode())
    s,ct,b=get(BASE+"api/tools.json"); api=json.loads(b); api=api if isinstance(api,list) else (api.get("tools",[]) if isinstance(api,dict) else [])
    imgs={}
    for x in api:
        if not x.get("logo"): bad.append(("api/tools.json",x.get("slug"),"no logo")); continue
        imgs.setdefault(x["logo"],set()).add("api/tools.json")
    def page(u): return u,get(u)
    with cf.ThreadPoolExecutor(16) as ex:
        for u,(s,ct,b) in ex.map(page,urls):
            if s!=200: bad.append((u,"",f"page HTTP {s}")); continue
            h=b.decode("utf-8","replace"); m=re.search(r"<main.*?</main>",h,re.S); main=m.group(0) if m else h
            for src in re.findall(r'<img[^>]*src="([^"]*assets/logos/[^"]+)"',h): imgs.setdefault(urllib.parse.urljoin(u,src),set()).add(u)
            bad.extend(L.listing_missing(h,u))  # every tool link in a listing/table row/card/inline list needs its logo (Oct 18 2026)
            for mm in CARD.finditer(main):
                a_open=main[mm.start():main.find(">",mm.start())+1]; inner=mm.group(2)
                pre=main[max(0,mm.start()-80):mm.start()]; li=re.search(r"<li[^>]*>\s*$",pre)
                if 'class="stretch"' in a_open:  # card whose link overlays it: the logo is a sibling inside the same <li>
                    end=main.find("</li>",mm.end()); inner=main[mm.end():end]
                    if "assets/logos/" not in inner: bad.append((u,mm.group(1),"tool card without a logo img"))
                elif 'class="card' in a_open or li:
                    if "assets/logos/" not in inner: bad.append((u,mm.group(1),"tool card/list item without a logo img"))
    def img(u): return u,get(u)
    with cf.ThreadPoolExecutor(16) as ex:
        for u,(s,ct,b) in ex.map(img,list(imgs)):
            ok=s==200 and ct.startswith("image") and len(b)>=100
            if ok:
                try: Image.open(io.BytesIO(b)).load()
                except Exception: ok=False
            if not ok: bad.append((u,sorted(imgs[u])[0],f"logo HTTP {s} {ct} {len(b)}B"))
    print(f"live: {len(urls)} pages, {len(imgs)} logo URLs checked")
    return bad
def placeholders(tools):
    R=json.load(open("data/logo_review.json")); ph=R.get("agentscout_placeholder",{}); by={x["slug"]:x for x in tools}; found=[]
    for s in ph:
        x=by.get(s)
        if not x: continue
        m=re.match(r"https?://github\.com/([^/]+)/([^/#?]+)",x.get("github") or "")
        if m:
            o,r=m.groups()
            tr=subprocess.run(["gh","api",f"repos/{o}/{r}/git/trees/HEAD?recursive=1","--jq",".tree[].path"],capture_output=True,text=True).stdout.split("\n")
            for p in tr:
                if re.search(r"(^|/)(logo|icon|brand|favicon)[^/]*\.(png|svg|jpe?g|webp|ico)$",p,re.I) and not re.search(r"node_modules|test|vendor|templates?/icons",p,re.I): found.append((s,"repo file",p))
            g=subprocess.run(["gh","api","graphql","-f","query=query{repository(owner:\"%s\",name:\"%s\"){usesCustomOpenGraphImage openGraphImageUrl}}"%(o,r),"--jq",".data.repository|select(.usesCustomOpenGraphImage)|.openGraphImageUrl"],capture_output=True,text=True).stdout.strip()
            if g : found.append((s,"custom social preview",g))
        site=x.get("website") or ""
        if site and "github.com" not in site:
            st,ct,b=get(site)
            for h in re.findall(r'<link[^>]+rel=["\'][^"\']*icon[^"\']*["\'][^>]*>',b.decode("utf-8","replace"),re.I): found.append((s,"site icon",h[:160]))
    rej=R.get("reviewed_not_logo",{})
    found=[f for f in found if not any(k in f[2] or (k=="site icon" and f[1]=="site icon") for k in rej.get(f[0],[]))]
    for f in found: print("CANDIDATE",*f)
    print(f"placeholders: {len(ph)} AgentScout-made icons, {len(found)} candidate real logos to review by eye")
    return found
if __name__=="__main__":
    tools=json.load(open("tools.json")); fails=[(s,c,p) for s,c,p in L.check(tools)]
    print(f"local: {len(tools)} tools, {len(fails)} without a valid local logo")
    lg=L.listings_gate(exit_on_fail=False); fails+=lg  # built HTML: tool links in listings without a logo
    if "--online" in sys.argv: o=online(tools); print(f"online: {len(o)} personal-avatar logos not yet reviewed"); fails+=o
    if "--placeholders" in sys.argv: placeholders(tools)
    if "--live" in sys.argv: v=live(tools); print(f"live: {len(v)} problems"); fails+=v
    for f in fails: print("FAIL",*f)
    sys.exit(1 if fails else 0)
