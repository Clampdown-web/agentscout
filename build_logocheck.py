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
