"""Daily Editor's Pick -> api/editors-pick.json + homepage section. Deterministic by Pacific date hash over quality tools
(logo file present, link checked, official website/url, real description), no repeats within 30 days (history kept in the JSON)."""
import json,os,hashlib,datetime,re,html
from zoneinfo import ZoneInfo
import build_extras
B=build_extras.B; e=html.escape
def today():
    # Pick day rolls over at 8 AM Pacific (before 8 AM it is still the previous day's pick)
    return (datetime.datetime.now(ZoneInfo("America/Los_Angeles"))-datetime.timedelta(hours=8)).date()
def quality(x):
    return bool(x.get("logo")) and os.path.exists(x["logo"]) and bool(x.get("verified")) and bool(x.get("website") or x.get("url")) and len(x.get("description",""))>=40
def why(x):
    kf=x.get("key_features") or []
    if isinstance(kf,str):
        try: kf=json.loads(kf.replace("'",'"'))
        except Exception: kf=[]
    lead=kf[0] if kf else x["description"].split(". ")[0]
    lead=lead.rstrip(".")
    aud="builders" if "build" in str(x.get("audience","")).lower() else "everyday users"
    return f"A standout {x['category']} tool for {aud}: {lead[0].lower()+lead[1:] if lead[:2]!=lead[:2].upper() else lead}."
def pick(t):
    p="api/editors-pick.json"; d=today().isoformat()
    try: old=json.load(open(p))
    except Exception: old={}
    hist=[h for h in old.get("history",[]) if h.get("date","")>=(today()-datetime.timedelta(days=60)).isoformat()]
    if old.get("date")==d and old.get("slug"): cur=old
    else:
        recent={h["slug"] for h in hist if h["date"]>=(today()-datetime.timedelta(days=30)).isoformat()}
        cand=sorted([x for x in t if quality(x) and x["slug"] not in recent],key=lambda x:x["slug"])
        if not cand: cand=sorted([x for x in t if quality(x)],key=lambda x:x["slug"])
        x=cand[int(hashlib.sha256(d.encode()).hexdigest(),16)%len(cand)]
        cur={"date":d,"slug":x["slug"],"name":x["name"],"why":why(x)}
        hist=[h for h in hist if h["date"]!=d]+[{"date":d,"slug":x["slug"]}]
    bys={x["slug"]:x for x in t}; x=bys.get(cur["slug"])
    if not x: return
    out={"date":d,"slug":x["slug"],"name":x["name"],"why":cur["why"],"category":x["category"],"description":x["description"],
         "logo":B+x["logo"],"page":f"{B}tools/{x['slug']}.html","history":sorted(hist,key=lambda h:h["date"])}
    json.dump(out,open(p,"w"),indent=1)
    # Homepage section (static, refreshed by the daily rebuild)
    dd=today(); ds=f"{dd.strftime('%b')} {dd.day}, {dd.year}"
    sec=(f'<!--PICK-START--><section id="epick" aria-labelledby="epick-h"><div class="wrap"><a class="card epick" href="tools/{x["slug"]}.html" data-pick="{x["slug"]}">'
         f'<span class="ico">{build_extras.ico(x,"")[17:-7] if False else ""}<img src="{x["logo"]}" alt="{e(x["name"])} logo" width="56" height="56" loading="lazy" decoding="async"></span>'
         f'<div class="eptext"><div class="eplabel"><span class="epbadge" aria-hidden="true">★</span><span id="epick-h">Editor\'s Pick</span><span class="muted">· {ds}</span></div>'
         f'<h3>{e(x["name"])}</h3><p class="epwhy">{e(cur["why"])}</p><div class="badges"><span class="b cat has-cico">{build_extras.cico(x["category"])}{e(x["category"])}</span><span class="b">{e(x["pricing"])}</span></div></div></a></div></section><!--PICK-END-->')
    s=open("index.html").read()
    s=re.sub(r'<!--PICK-START-->.*?<!--PICK-END-->','',s,flags=re.S)
    s=s.replace('<!--RECENT-START-->',sec+'<!--RECENT-START-->',1)
    s=s.replace('const f=d.find(t=>t.featured),cats={};','const f=null,cats={};')
    open("index.html","w").write(s)
    print("editor's pick:",x["name"])
if __name__=="__main__": pick(json.load(open("tools.json")))
