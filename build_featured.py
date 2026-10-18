"""Featured listings -> pinned 'Featured' block on the homepage and category pages.
Data: featured.json (list). Each entry:
  {"slug":"tool-slug", "scope":["homepage","crypto"], "expires":"2026-12-31", "paid":false, "note":"optional"}
scope: "homepage" and/or category slugs (as in categories/<slug>.html). Omit scope = homepage + the tool's own category.
expires: optional ISO date (Pacific); the entry stops showing after that day.
paid: true makes outbound links rel="sponsored noopener" and the label reads "Sponsored".
reason: why it's featured: "badge_backlink" (maker shows our AgentScout badge or a link; check with scripts/check_badge.py),
"editorial" or "paid". Add/remove entries with scripts/feature_tool.py. Not shown on the page; kept for our records.
With no active entries for a page, the block (and its markers) is removed entirely: no empty box.
Run after the other generators (idempotent)."""
import json,os,re,glob,html,datetime
from zoneinfo import ZoneInfo
import build_extras
e=html.escape; S,E="<!--FEAT-START-->","<!--FEAT-END-->"
def today(): return datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
def load():
    try: f=json.load(open("featured.json"))
    except Exception: return []
    T={x["slug"]:x for x in json.load(open("tools.json"))}; out=[]
    for f_ in f if isinstance(f,list) else []:
        x=T.get(f_.get("slug"))
        if not x or (f_.get("expires") and f_["expires"]<today()): continue
        sc=f_.get("scope") or ["homepage",build_extras.catslug(x["category"])]
        out.append((x,f_,set(sc)))
    return out
def card(x,f,d):
    paid=bool(f.get("paid")); lab="Sponsored" if paid else "Featured"
    rel="sponsored noopener" if paid else "noopener"; url=x.get("website") or x.get("url") or ""
    out=f'<a class="fvisit" href="{e(url)}" target="_blank" rel="{rel}">Visit site<span class="sr-only"> for {e(x["name"])} (opens in new tab)</span> ↗</a>' if url else ""
    return (f'<li class="card fcard"><span class="flabel">{lab}</span><div class="ct">{build_extras.ico(x,d)}<div class="tn"><h3><a href="{d}tools/{x["slug"]}.html">{e(x["name"])}</a></h3>'
            f'<div class="badges"><span class="b cat">{e(x["category"])}</span><span class="b">{e(x["pricing"])}</span></div></div></div><p class="hook">{e(x["description"])}</p>{out}</li>')
def block(items,d):
    paid=any(f.get("paid") for _,f,_ in items)
    note="Sponsored and featured placements are labeled. They don't affect our listings or ratings." if paid else "Featured placements are labeled and don't affect our listings or ratings."
    return (f'{S}<section id="featlist" aria-labelledby="feat-h"><div class="wrap"><h2 id="feat-h" class="feat-h">Featured</h2>'
            f'<ul class="fgrid">{"".join(card(x,f,d) for x,f,_ in items)}</ul><p class="fnote">{note}</p></div></section>{E}')
def put(path,html_,anchor,before=True):
    s=open(path).read(); s0=s
    s=re.sub(re.escape(S)+".*?"+re.escape(E),"",s,flags=re.S)
    if html_:
        i=s.find(anchor)
        if i<0: print("anchor missing",path); return
        if not before: i+=len(anchor)
        s=s[:i]+html_+s[i:]
    if s!=s0: open(path,"w").write(s)
def run():
    A=load()
    home=[a for a in A if "homepage" in a[2]]
    put("index.html",block(home,"") if home else "",'<div class="wrap"><section class="homegen"')
    for p in glob.glob("categories/*.html"):
        slug=os.path.basename(p)[:-5]
        if slug=="index": continue
        it=[a for a in A if slug in a[2]]
        # inside the category section, right above the tool grid
        put(p,block(it,"../").replace('<div class="wrap">','<div>',1) if it else "",'<div class="grid">')
    print("featured active:",len(A))
if __name__=="__main__": run()
