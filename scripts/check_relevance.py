"""scripts/check_relevance.py: flags any tasks/, s/, for/ or best/ page where more than 10% of listed tools are off-topic.
Run after the build (build.py calls it) and in the standing recheck. Exit code 1 = at least one page over the limit (build fails
when --strict). Report: data/relevance_report.json + a printed table. Pacific time stamps."""
import json,re,glob,os,sys,io,contextlib,datetime
from zoneinfo import ZoneInfo
R=sys.argv[sys.argv.index('--root')+1] if '--root' in sys.argv else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,R)
os.chdir(R)
with contextlib.redirect_stdout(io.StringIO()):
    import build_extras as _bx, build_tasks as bt, build_landing as bl, build_best as bb
import atexit; atexit.unregister(_bx._apply_featured)  # read-only check: don't run the generators' exit hooks
from relevance import score,MIN
LIMIT=0.10
tools={x["slug"]:x for x in json.load(open(os.path.join(R,"tools.json")))}
TASK={T[0]:T for T in bt.TASKS}
ROLE={r[0]:[s for _,s in r[4]] for r in bl.R}
TG={k:task for k,_,_,task in bl.TARGETS}
BEST={p[0]:p[2] for p in bb.PAGES}
def slugs(f):
    h=open(f,encoding="utf-8").read(); body=h.split("<main",1)[-1].split('id="nlblock"')[0]
    return [s for s in dict.fromkeys(re.findall(r'tools/([a-z0-9-]+)\.html',body)) if s in tools]
def off_for(x,ts):  # off-topic only if it fails every topic task the page covers
    ts=[TASK[t] for t in ts if t in TASK]
    return bool(ts) and all(score(x,T)<MIN for T in ts)
rows=[]
def add(page,topic,s,off): rows.append({"page":page,"topic":topic,"tools":len(s),"off":len(off),"share":round(len(off)/max(1,len(s)),3),"off_tools":off})
for f in sorted(glob.glob(R+"/tasks/*.html")):
    b=os.path.basename(f)[:-5]
    if b=="index": continue
    par=max([t for t in TASK if b==t or b.startswith(t+"-")],key=len,default=None)
    if not par: continue
    s=slugs(f); add("tasks/"+b+".html",par,s,[x for x in s if off_for(tools[x],[par])])
for f in sorted(glob.glob(R+"/s/*.html")):
    b=os.path.basename(f)[:-5]
    t=next((TG[k] for k in sorted(TG,key=len,reverse=True) if b==k or b.endswith("-"+k)),None)
    if not t: continue
    s=slugs(f); add("s/"+b+".html",t,s,[x for x in s if off_for(tools[x],[t])])
for f in sorted(glob.glob(R+"/for/*.html")):
    b=os.path.basename(f)[:-5]
    ts=ROLE.get(b)
    if not ts: continue
    s=slugs(f); add("for/"+b+".html",",".join(ts),s,[x for x in s if off_for(tools[x],ts)])
for f in sorted(glob.glob(R+"/best/*.html")):
    b=os.path.basename(f)[:-5]
    if b not in BEST: continue
    s=slugs(f); add("best/"+b+".html","filter",s,[x for x in s if not BEST[b](tools[x])])
bad=[r for r in rows if r["share"]>LIMIT and r["tools"]>=3]
now=datetime.datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%b %-d, %Y %-I:%M %p PT")
json.dump({"checked":now,"limit":LIMIT,"pages":len(rows),"over_limit":bad},open(os.path.join(R,"data/relevance_report.json") if "--write" in sys.argv else os.devnull,"w"),indent=1)
print(f"Relevance check {now}: {len(rows)} pages, {len(bad)} over {int(LIMIT*100)}% off-topic")
for r in sorted(bad,key=lambda r:-r["share"]): print(f'  {r["page"]} [{r["topic"]}] {r["off"]}/{r["tools"]} ({r["share"]:.0%}) e.g. {", ".join(r["off_tools"][:5])}')
sys.exit(1 if bad and "--strict" in sys.argv else 0)
