"""Builds news.json: recent AI-agent news from free RSS/Atom feeds (+ optional X items).
Usage: python3 scripts/update_news.py [--x scripts/x_items.json] [--hours 72] [--n 8] [--offline] [--dry-run]
Stdlib only. Titles are shortened/cleaned; no summaries are copied.
The 7 AM run refreshes scripts/x_items.json with same-day items, then runs this
script. That cache is read before ranking. Candidates sort by score descending,
then newest date. At least half of --n slots (rounded up) are kept for the last
24 hours when that many items exist; the --hours window fills only the slots
left over. --offline skips the feeds. --dry-run prints the selection and does
not write. This script does not submit listings.
After this script, run `python3 build_site.py`: build_news.py then gives every item a permanent page under news/YYYY/MM/ (tracked in news-history.json). Commit news/ and news-history.json with the other files."""
import json,re,sys,datetime as dt,urllib.request,xml.etree.ElementTree as ET,email.utils,html,argparse,os
FEEDS=[("TechCrunch","https://techcrunch.com/category/artificial-intelligence/feed/"),
("The Verge","https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
("VentureBeat","https://venturebeat.com/category/ai/feed/"),
("Hacker News","https://hnrss.org/newest?q=agent&points=10"),
("Google News","https://news.google.com/rss/search?q=%22AI+agent%22+OR+%22coding+agent%22+OR+MCP+when:3d&hl=en-US&gl=US&ceid=US:en"),
("Hugging Face","https://huggingface.co/blog/feed.xml")]
KW=re.compile(r"\b(ai agents?|agentic|agents?\b.*\b(launch|framework|sdk|platform)|mcp|model context protocol|computer[- ]use|coding agents?|agent frameworks?|autonomous agents?|multi-agent)\b",re.I)
def fetch(u):
    r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 AgentScoutNews/1.0"})
    return urllib.request.urlopen(r,timeout=20).read()
def pdate(s):
    s=(s or "").strip()
    try: return email.utils.parsedate_to_datetime(s).astimezone(dt.timezone.utc)
    except Exception: pass
    try: return dt.datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(dt.timezone.utc)
    except Exception: return None
def items(src,raw):
    root=ET.fromstring(raw); ns={"a":"http://www.w3.org/2005/Atom"}
    for it in root.iter("item"):
        yield src,it.findtext("title"),it.findtext("link"),pdate(it.findtext("pubDate"))
    for it in root.iter("{http://www.w3.org/2005/Atom}entry"):
        l=it.find("a:link",ns); yield src,it.findtext("a:title",namespaces=ns),(l.get("href") if l is not None else ""),pdate(it.findtext("a:updated",namespaces=ns) or it.findtext("a:published",namespaces=ns))
def short(t,src):
    t=html.unescape(re.sub(r"\s+"," ",t or "")).strip()
    t=re.sub(r"\s+[-–|]\s+[^-–|]{2,40}$","",t) if src=="Google News" else t  # drop " - Publisher"
    t=re.sub(r"^(Show|Launch|Ask) HN:\s*","",t)
    return t if len(t)<=90 else t[:87].rsplit(" ",1)[0]+"…"
FRESH_HOURS=24  # same-day window; how many slots that window gets is derived from --n

def rank_candidates(items):
    """Higher score first. On a tie, the newer date comes first."""
    return sorted(items,key=lambda x:(x.get("score",0),x.get("date") or ""),reverse=True)

def fresh_slots(n):
    """At least half of the requested slots, rounded up."""
    return (n+1)//2 if n>0 else 0

def fresh_span(hours,fresh_hours=FRESH_HOURS):
    return min(fresh_hours,hours) if hours and hours>0 else fresh_hours

def select_slots(ranked,n,now,hours=72,fresh_hours=FRESH_HOURS):
    """Keep a share of slots for the last day, then fill what is left from `ranked`.

    `ranked` is already score-then-newest. The reserve takes the best items
    inside the fresh window. Remaining slots walk that same order, so an older
    item is used only when it still outranks whatever fresh items are left.
    """
    if n<=0: return []
    cutoff=(now-dt.timedelta(hours=fresh_span(hours,fresh_hours))).strftime("%Y-%m-%dT%H:%M:%SZ")
    fresh=[x for x in ranked if (x.get("date") or "")>=cutoff]
    chosen=list(fresh[:min(len(fresh),fresh_slots(n),n)])
    seen={x.get("url") for x in chosen}
    for x in ranked:
        if len(chosen)>=n: break
        if x.get("url") in seen: continue
        chosen.append(x); seen.add(x.get("url"))
    return chosen

def dedupe(items):
    seen=set(); res=[]
    for x in rank_candidates(items):
        k=re.sub(r"[^a-z0-9]","",(x.get("title") or "").lower())[:40]
        url=x.get("url")
        if k in seen or url in seen: continue
        seen|={k,url}; res.append(x)
    return res

def newest_first(items):
    return sorted(items,key=lambda x:x.get("date") or "",reverse=True)

def load_x_cache(path,cut):
    """Read the morning cache. Ranking must happen after this, not before."""
    if not path or not os.path.exists(path): return []
    rows=[]
    with open(path) as fh: raw=json.load(fh)
    for x in raw:
        d=pdate(x.get("date"))
        if not d or d<cut: continue
        row=dict(x); row["date"]=d.strftime("%Y-%m-%dT%H:%M:%SZ"); row.setdefault("tool",None); rows.append(row)
    return rows

def main(argv=None,now=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--x",default=None)
    ap.add_argument("--hours",type=int,default=72)
    ap.add_argument("--n",type=int,default=8)
    ap.add_argument("--summaries",default="scripts/news_summaries.json")
    ap.add_argument("--days",type=int,default=30)
    ap.add_argument("--offline",action="store_true",help="Skip RSS fetches and rank only the local cache")
    ap.add_argument("--dry-run",action="store_true",help="Print the selection and do not write news.json")
    a=ap.parse_args(argv)
    root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    now=now or dt.datetime.now(dt.timezone.utc); cut=now-dt.timedelta(hours=a.hours); out=[]; used=[]
    if not a.offline:
        tools=json.load(open(os.path.join(root,"tools.json")))
        names=sorted(((x["name"],x["slug"]) for x in tools if len(x["name"])>3),key=lambda z:-len(z[0]))
        for src,u in FEEDS:
            try: raw=fetch(u)
            except Exception as e: print("skip",src,e,file=sys.stderr); continue
            for s,t,l,d in items(src,raw):
                if not t or not l or not d or d<cut: continue
                hit=[sl for nm,sl in names if re.search(r"\b"+re.escape(nm)+r"\b",t,re.I)]
                if not (KW.search(t) or hit): continue
                out.append({"title":short(t,s),"source":s if s!="Google News" else (re.findall(r"[-–]\s+([^-–]{2,40})$",t) or ["Google News"])[0].strip(),"url":l.strip(),"date":d.strftime("%Y-%m-%dT%H:%M:%SZ"),"tool":hit[0] if hit else None,"score":(2 if KW.search(t) else 0)+(2 if hit else 0)+(1 if s in("TechCrunch","The Verge","VentureBeat") else 0)})
            used.append(src)
    # Cache is loaded here, before rank/select. The morning run must refresh it first.
    if a.x and os.path.exists(a.x):
        cached=load_x_cache(a.x,cut)
        out.extend(cached); used.append("X")
        fresh_cut=(now-dt.timedelta(hours=fresh_span(a.hours))).strftime("%Y-%m-%dT%H:%M:%SZ")
        if not any(x["date"]>=fresh_cut for x in cached):
            print("warning: x cache has no item from the last %sh; refresh scripts/x_items.json before this rank"%fresh_span(a.hours),file=sys.stderr)
    chosen=select_slots(dedupe(out),a.n,now,a.hours)
    if a.dry_run:
        fresh_cut=(now-dt.timedelta(hours=fresh_span(a.hours))).strftime("%Y-%m-%dT%H:%M:%SZ")
        show=newest_first(chosen)
        fresh_n=sum(1 for x in show if (x.get("date") or "")>=fresh_cut)
        print("%s items from %s; %s in the last %sh (dry-run)"%(len(show),used,fresh_n,fresh_span(a.hours)))
        for x in show: print("%s  score=%s  %s  %s"%(x.get("date"),x.get("score",0),x.get("source",""),x.get("title")))
        return
    sm=json.load(open(os.path.join(root,a.summaries))) if os.path.exists(os.path.join(root,a.summaries)) else {}
    for x in chosen:
        o=sm.get(x["url"],{}); x.pop("score",None)
        if o.get("title"): x["title"]=o["title"]
        if o.get("summary"): x["summary"]=o["summary"]
    # rolling archive (picked rows, deduped by url, last N days)
    ap_=os.path.join(root,"news-archive.json")
    arc=json.load(open(ap_))["items"] if os.path.exists(ap_) else []
    byu={x["url"]:x for x in arc}
    for x in chosen: byu[x["url"]]={**byu.get(x["url"],{}),**x}
    for u,x in byu.items():
        o=sm.get(u,{})
        if o.get("summary"): x["summary"]=o["summary"]
        if o.get("title"): x["title"]=o["title"]
    acut=(now-dt.timedelta(days=a.days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    arc=sorted([x for x in byu.values() if x["date"]>=acut],key=lambda x:x["date"],reverse=True)
    json.dump({"updated":now.strftime("%Y-%m-%dT%H:%M:%SZ"),"days":a.days,"items":arc},open(ap_,"w"),indent=1,ensure_ascii=False)
    res=newest_first(chosen)
    json.dump({"updated":now.strftime("%Y-%m-%dT%H:%M:%SZ"),"sources":used,"items":res},open(os.path.join(root,"news.json"),"w"),indent=1,ensure_ascii=False)
    print(len(res),"items from",used)
if __name__=="__main__": main()
