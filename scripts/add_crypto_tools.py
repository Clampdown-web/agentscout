"""Add user-approved crypto tools from the field audit into tools.json (category "crypto"), with logos.

Usage (from the repo root, on the crypto-category branch):
  python3 scripts/add_crypto_tools.py [AUDIT_JSON] --approve=all|approved.txt|"slug-a,slug-b" [--dry] [--fetch-missing-logos]
  python3 build_site.py              # regenerates tool pages, categories/crypto.html, sitemap, llms.txt, api/*.json
  python3 scripts/dedupe_check.py    # must print no duplicates

AUDIT_JSON defaults to /workspace/notes/crypto-tools-audit-2026-10-17.json. The script is tolerant of its shape:
a list, or a dict holding the list under "tools"/"new_tools"/"results". Per tool it reads
  name, slug, description, website|url|listing_url, github|gh|repo, logo|logo_path|logo_file, pricing, audience, subcategory, sources
Logo lookup order: the audit's logo path, then /workspace/notes/crypto-logos/<slug>.{png,jpg,jpeg,webp,ico,svg}.
Tools with no logo are skipped unless --fetch-missing-logos (then it reuses add_tools.getimg on the site's icons / GitHub avatar).
Only tools whose name or slug is approved are added; duplicates of existing listings (name/domain/repo) are skipped.
Nothing is pushed or deployed by this script.
"""
import sys,os,re,io,json,glob,datetime
sys.path.insert(0,'scripts'); from dedupe_check import keys
from takedown_blocklist import blocked as _takedown_blocked
from PIL import Image
AUDIT="/workspace/notes/crypto-tools-audit-2026-10-17.json"; LOGODIR="/workspace/notes/crypto-logos"
PRICES={"Open source","Freemium","Open source + cloud","Paid","Usage-based","Enterprise","See site","Open weights","Open standard"}
BUILDER_SUB={"frameworks","wallets and payments","wallets","payments","blockchain mcp servers","mcp","security and audit","security"}
def slugify(s): return re.sub(r"[^a-z0-9]+","-",(s or "").lower()).strip("-")
def first(d,*ks):
    for k in ks:
        v=d.get(k)
        if isinstance(v,list): v=v[0] if v else None
        if v: return v
    return ""
def load_audit(p):
    d=json.load(open(p))
    if isinstance(d,dict): d=d.get("tools") or d.get("new_tools") or d.get("results") or []
    return d
def load_logo(x,slug):
    c=[first(x,"logo_path","logo_file","logo")] + sorted(glob.glob(f"{LOGODIR}/{slug}.*"))
    for p in c:
        if not p or p.startswith("http") or not os.path.exists(p): continue
        try:
            if p.endswith(".svg"):
                import cairosvg; im=Image.open(io.BytesIO(cairosvg.svg2png(url=p,output_width=128,output_height=128)))
            else:
                im=Image.open(p)
                if im.format=="ICO": im.size=max(im.ico.sizes())
            im.load(); return im
        except Exception as ex: print("bad logo",p,ex)
    return None
def fetch_logo(site,gh):
    import add_tools
    from urllib.parse import urljoin
    import requests
    cands=[]
    if site:
        try:
            h=requests.get(site,headers=add_tools.UA,timeout=15).text
            for m in re.finditer(r'<link[^>]+rel=["\'][^"\']*(apple-touch-icon|icon)[^>]*>',h,re.I):
                hr=re.search(r'href=["\']([^"\']+)',m.group(0))
                if hr: cands.append(urljoin(site,hr.group(1)))
        except Exception: pass
        cands+=[urljoin(site,"/apple-touch-icon.png"),urljoin(site,"/favicon.ico")]
    if gh: cands.append(f"https://github.com/{gh.replace('https://github.com/','').split('/')[0]}.png?size=200")
    for u in cands:
        im=add_tools.getimg(u)
        if im: return im
    return None
def main():
    args=[a for a in sys.argv[1:] if not a.startswith("--")]; audit=args[0] if args else AUDIT
    opt={a.split("=")[0]:(a.split("=",1)[1] if "=" in a else True) for a in sys.argv[1:] if a.startswith("--")}
    ap=opt.get("--approve")
    if not ap: sys.exit("--approve is required (all | file of names/slugs | comma list). Only add what the user approved.")
    if not os.path.exists(audit): sys.exit(f"audit file not found: {audit}")
    if ap=="all": ok=None
    elif os.path.exists(ap): ok={slugify(l) for l in open(ap) if l.strip() and not l.startswith("#")}
    else: ok={slugify(s) for s in ap.split(",")}
    t=json.load(open("tools.json")); K=keys(t); nid=max(x["id"] for x in t); today=datetime.date.today().isoformat()
    added=[]; skipped={}
    for x in load_audit(audit):
        name=x.get("name","").strip(); slug=x.get("slug") or slugify(name)
        if ok is not None and slug not in ok and slugify(name) not in ok: continue
        if x.get("include") is False or x.get("exclude"): skipped.setdefault("excluded in audit",[]).append(name); continue
        site=first(x,"website","url","listing_url"); gh=first(x,"github","gh","repo","gh_candidates")
        if gh and not re.match(r"^(https?://github\.com/)?[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)?/?$",gh): gh=""  # audit placeholders like "N/A (closed-source ...)" or "none found"
        if gh and not gh.startswith("http"): gh="https://github.com/"+gh
        if site and "github.com" in site and not gh: gh=site
        desc=(x.get("description") or "").strip()
        if not (name and desc and (site or gh)): skipped.setdefault("missing name/description/link",[]).append(name); continue
        sub=(x.get("subcategory") or "").lower()
        pr=x.get("pricing") if x.get("pricing") in PRICES else ("Open source" if gh and (not site or "github.com" in site) else "See site")
        aud=x.get("audience") if x.get("audience") in ("builders","ready to use") else ("builders" if sub in BUILDER_SUB or "mcp" in name.lower() or "sdk" in name.lower() else "ready to use")
        e={"name":name,"url":site or gh,"description":desc,"category":"crypto","pricing":pr,"maturity":x.get("maturity") or "Active","audience":aud,
           "featured":False,"new":True,"verified":today,"added":today,"source":(first(x,"sources","source") or "Web search"),"pricing_detail":x.get("pricing_detail",""),
           "use_cases":[],"website":site if site and "github.com" not in site else "","github":gh or ""}
        if gh:
            e["repo"]="/".join(gh.replace("https://github.com/","").strip("/").split("/")[:2])
            if x.get("github_stars") is not None: e["github_stars"]=x["github_stars"]
        if x.get("tags"): e["tags"]=x["tags"]
        ks=keys([e])
        if _takedown_blocked(name=e.get("name",""), url=e.get("url",""), website=e.get("website",""), slug=slug):
            skipped.setdefault("blocklist",[]).append(name); continue
        if ks["name"]&K["name"] or ks["domain"]&K["domain"] or ks["repo"]&K["repo"]: skipped.setdefault("duplicate",[]).append(name); continue
        im=load_logo(x,slug) or (fetch_logo(site,gh) if opt.get("--fetch-missing-logos") else None)
        if im is None: skipped.setdefault("no logo",[]).append(name); continue
        for k in K: K[k]|=ks[k]
        nid+=1; e["id"]=nid; e["slug"]=x.get("site_slug") or slugify(name); e["logo"]=f"assets/logos/{e['slug']}.png"
        if not opt.get("--dry"):
            im=im.convert("RGBA"); im.thumbnail((128,128)); im.save(e["logo"])
        added.append(e)
    if not opt.get("--dry"): json.dump(t+added,open("tools.json","w"),indent=2,ensure_ascii=False)
    print(json.dumps({"dry":bool(opt.get("--dry")),"added":len(added),"names":[a["name"] for a in added],"total_after":len(t)+len(added),"skipped":skipped},indent=1))
    if added and not opt.get("--dry"): print("Next: python3 build_site.py && python3 scripts/dedupe_check.py")
if __name__=="__main__": main()
