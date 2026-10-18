"""Mark or unmark a tool as featured (featured.json), then re-apply the Featured blocks.
  python3 scripts/feature_tool.py add <slug> --reason=badge_backlink [--expires=YYYY-MM-DD] [--scope=homepage,coding] [--note=...]
  python3 scripts/feature_tool.py remove <slug>
  python3 scripts/feature_tool.py list
Reasons: badge_backlink (maker shows our badge/link; verify with scripts/check_badge.py first), editorial, paid (sets "paid": true -> "Sponsored").
Nothing shows publicly until featured.json has an active entry."""
import json,sys,os,subprocess,datetime
from zoneinfo import ZoneInfo
REASONS={"badge_backlink","editorial","paid"}
def main(a):
    F=json.load(open("featured.json")) if os.path.exists("featured.json") else []
    T={x["slug"] for x in json.load(open("tools.json"))}
    if not a or a[0]=="list":
        for f in F: print(f); return
    op,slug=a[0],a[1]; kw=dict(p[2:].split("=",1) for p in a[2:] if p.startswith("--") and "=" in p)
    F=[f for f in F if f.get("slug")!=slug]
    if op=="add":
        assert slug in T,f"unknown slug {slug}"
        r=kw.get("reason","editorial"); assert r in REASONS,f"reason must be one of {sorted(REASONS)}"
        e={"slug":slug,"reason":r,"since":datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat(),"paid":r=="paid"}
        if kw.get("expires"): e["expires"]=kw["expires"]
        if kw.get("scope"): e["scope"]=kw["scope"].split(",")
        if kw.get("note"): e["note"]=kw["note"]
        F.append(e)
    json.dump(F,open("featured.json","w"),indent=1,ensure_ascii=False)
    subprocess.run([sys.executable,"build_featured.py"],check=False)
    print(op,slug,"->",len(F),"featured entries")
if __name__=="__main__": main(sys.argv[1:])
