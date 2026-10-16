"""Builds news.json: recent AI-agent news from free RSS/Atom feeds (+ optional X items).
Usage: python3 scripts/update_news.py [--x scripts/x_items.json] [--hours 72] [--n 8]
Stdlib only. Titles are shortened/cleaned; no summaries are copied."""
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
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--x",default=None); ap.add_argument("--hours",type=int,default=72); ap.add_argument("--n",type=int,default=8); a=ap.parse_args()
    root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tools=json.load(open(os.path.join(root,"tools.json")))
    names=sorted(((x["name"],x["slug"]) for x in tools if len(x["name"])>3),key=lambda z:-len(z[0]))
    now=dt.datetime.now(dt.timezone.utc); cut=now-dt.timedelta(hours=a.hours); out=[]; used=[]
    for src,u in FEEDS:
        try: raw=fetch(u); n0=len(out)
        except Exception as e: print("skip",src,e,file=sys.stderr); continue
        for s,t,l,d in items(src,raw):
            if not t or not l or not d or d<cut: continue
            hit=[sl for nm,sl in names if re.search(r"\b"+re.escape(nm)+r"\b",t,re.I)]
            if not (KW.search(t) or hit): continue
            out.append({"title":short(t,s),"source":s if s!="Google News" else (re.findall(r"[-–]\s+([^-–]{2,40})$",t) or ["Google News"])[0].strip(),"url":l.strip(),"date":d.strftime("%Y-%m-%dT%H:%M:%SZ"),"tool":hit[0] if hit else None,"score":(2 if KW.search(t) else 0)+(2 if hit else 0)+(1 if s in("TechCrunch","The Verge","VentureBeat") else 0)})
        used.append(src)
    if a.x and os.path.exists(a.x):
        for x in json.load(open(a.x)):
            d=pdate(x.get("date"))
            if d and d>=cut: x.setdefault("tool",None); out.append(x)
        used.append("X")
    seen=set(); res=[]
    for x in sorted(out,key=lambda x:(-x.get("score",0),x["date"]),reverse=False):
        k=re.sub(r"[^a-z0-9]","",x["title"].lower())[:40]
        if k in seen or x["url"] in seen: continue
        seen|={k,x["url"]}; res.append(x)
    res=sorted(res[:a.n],key=lambda x:x["date"],reverse=True)
    for x in res: x.pop("score",None)
    json.dump({"updated":now.strftime("%Y-%m-%dT%H:%M:%SZ"),"sources":used,"items":res},open(os.path.join(root,"news.json"),"w"),indent=1,ensure_ascii=False)
    print(len(res),"items from",used)
if __name__=="__main__": main()
