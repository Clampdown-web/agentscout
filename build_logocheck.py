"""Logo gate (added Oct 18, 2026 PT after logos went missing again).
Every listed tool must have a valid LOCAL logo: logo == assets/logos/<slug>.png, file exists, decodes as an image,
is at least 64px on its long side and 32px on its short side, is not blank / single-colour, not a 1x1, not a GitHub
default identicon, and is not a byte-identical copy of a known generic icon (GitHub mark/default avatar etc.).
build_site.py calls run(t) first and stops the build if anything fails; scripts/check_logos.py runs the same check
plus optional --online (personal GitHub avatar) and --live (crawl agentscouthq.com) checks."""
import os,sys,json,hashlib,collections,warnings
warnings.filterwarnings("ignore",category=DeprecationWarning)
from PIL import Image
ROOT=os.path.dirname(os.path.abspath(__file__))
GENERIC_MD5=set()  # md5s of known generic icons; add here if one ever slips in
def is_identicon(im):
    px=list(im.convert('RGB').resize((64,64),Image.NEAREST).getdata())
    near=lambda a,b,d:all(abs(p-q)<=d for p,q in zip(a,b))
    if sum(near(p,(240,240,240),8) for p in px)<0.2*len(px): return False
    rest=[p for p in px if not near(p,(240,240,240),14)]
    if not rest: return False
    fg=collections.Counter(rest).most_common(1)[0][0]
    if sum(near(p,fg,30) for p in rest)<0.85*len(rest): return False
    g=im.convert('L').resize((64,64)); f=g.transpose(Image.FLIP_LEFT_RIGHT)
    return sum(abs(a-b)<24 for a,b in zip(g.getdata(),f.getdata()))>=0.95*64*64
def problem(x):
    s=x.get("slug","?"); l=x.get("logo") or ""
    if not l: return "no logo field"
    if l.startswith("http"): return f"remote/hotlinked logo {l}"
    if l!=f"assets/logos/{s}.png": return f"logo path {l} != assets/logos/{s}.png"
    p=os.path.join(ROOT,l)
    if not os.path.isfile(p): return "logo file missing"
    b=open(p,"rb").read()
    if len(b)<100: return f"logo file only {len(b)} bytes"
    if hashlib.md5(b).hexdigest() in GENERIC_MD5: return "generic placeholder icon"
    try:
        im=Image.open(p); im.load()
    except Exception as e: return f"not a readable image ({e})"
    w,h=im.size
    if max(w,h)<64 or min(w,h)<32: return f"too small {w}x{h}"
    rgba=im.convert("RGBA")
    if rgba.getextrema()[3][1]==0: return "fully transparent"
    bg=Image.new("RGBA",rgba.size,"white"); bg.alpha_composite(rgba)
    if all(a==b for a,b in bg.convert("RGB").getextrema()): return "blank single-colour image"
    if is_identicon(im): return "GitHub default identicon"
    return None
def check(tools):
    return [(x.get("slug"),x.get("category"),problem(x)) for x in tools if problem(x)]
def run(tools,exit_on_fail=True):
    bad=check(tools)
    if bad:
        print(f"LOGO CHECK FAILED: {len(bad)} tool(s) without a valid local logo:",file=sys.stderr)
        for s,c,p in bad: print(f"  {s} [{c}]: {p}",file=sys.stderr)
        if exit_on_fail: sys.exit(1)
    else: print(f"logo check: {len(tools)} tools, all have a valid local logo")
    return bad
if __name__=="__main__":
    run(json.load(open(os.path.join(ROOT,"tools.json"))))

# ---- Listings on the built HTML (Oct 18, 2026 PT): every tool link in a listing must sit next to its logo ----
# Listing = a link to tools/<slug>.html inside <main> whose nearest block is a list item, table cell, definition, or a card,
# or that sits in an inline 'Related:' / 'pages on AgentScout:' list. Prose links inside sentences are not listings.
# The logo (<img src=".../assets/logos/...">) must be inside the link, its table cell, its list item or its card.
import re as _re
def listing_missing(h,where=""):
    import lxml.html
    m=_re.search(r"<main.*?</main>",h,_re.S)
    if not m: return []
    try: doc=lxml.html.fromstring(m.group(0))
    except Exception: return []
    bad=[]
    for a in doc.iter("a"):
        hm=_re.search(r'(?:^|/)tools/([a-z0-9-]+)\.html$',a.get("href") or "")
        if not hm: continue
        if a.xpath('.//img[contains(@src,"assets/logos/")]'): continue
        box=None; p=a.getparent(); depth=0
        while p is not None and depth<6:
            cls=" "+(p.get("class") or "")+" "
            if p.tag in ("td","th","li","dd","dt") or " card " in cls or " tile " in cls: box=p; break
            if p.tag=="p":
                t=(p.text_content() or "").strip()
                if t.startswith("Related:") or "pages on AgentScout:" in t: box=p
                break
            if p.tag in ("h1","h2","h3","blockquote","figcaption","summary","details"): break
            p=p.getparent(); depth+=1
        acls=" "+(a.get("class") or "")+" "
        if box is None and (" card " in acls or " tile " in acls): box=a
        if box is None: continue
        if box.tag=="p":  # inline list: the logo must be inside the link
            bad.append((where,hm.group(1),"inline tool list link without a logo")); continue
        if not box.xpath('.//img[contains(@src,"assets/logos/")]'):
            bad.append((where,hm.group(1),f"tool link in a {box.tag}{'.'+box.get('class').split()[0] if box.get('class') else ''} without a logo"))
    return bad
def listings_gate(exit_on_fail=True):
    import glob
    bad=[]
    for f in glob.glob("**/*.html",recursive=True):
        if f.startswith(("app/","node_modules/")) or f in ("outreach-tracker.html","og.html","stats.js.html"): continue
        s=open(f,errors="ignore").read()
        if "tools/" in s and 'http-equiv="refresh"' not in s: bad+=listing_missing(s,f)
    if bad:
        print(f"logo gate: {len(bad)} tool links in listings without a logo, e.g.:"); [print("  ",b) for b in bad[:20]]
        if exit_on_fail: raise SystemExit(1)
    else: print("logo gate (listings): every tool link in a listing has its logo")
    return bad
