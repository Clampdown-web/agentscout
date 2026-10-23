"""MCP link check (Oct 22 2026): requests every MCP server's listed link (and GitHub repo when set) and writes
data/mcp_link_status.json. Read by build_aicite.py for /mcp/link-status.html. Run before a build; network only here."""
import json,os,sys,datetime as d,zoneinfo as z,urllib.request,urllib.error,concurrent.futures as cf
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UA={"User-Agent":"Mozilla/5.0 (compatible; AgentScoutLinkCheck/1.0; +https://agentscouthq.com/about.html)"}
def probe(u):
    for m in ("HEAD","GET"):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers=UA,method=m),timeout=20); return r.status
        except urllib.error.HTTPError as ex:
            if m=="GET" or ex.code not in (403,405,400,404,429,501): return ex.code
            last=ex.code
        except Exception: 
            if m=="GET": return 0
    return 0
def main():
    t=[x for x in json.load(open("tools.json")) if x.get("category")=="MCP servers"]
    jobs={}
    for x in t:
        jobs[(x["slug"],"url")]=x["url"]
        if x.get("github") and x["github"]!=x["url"]: jobs[(x["slug"],"github")]=x["github"]
    out={}
    with cf.ThreadPoolExecutor(24) as ex:
        fs={ex.submit(probe,u):k for k,u in jobs.items()}
        for f in cf.as_completed(fs): out.setdefault(fs[f][0],{})[fs[f][1]]=f.result()
    now=d.datetime.now(z.ZoneInfo("America/Los_Angeles"))
    json.dump({"checked":now.strftime("%Y-%m-%d %H:%M"),"tz":"America/Los_Angeles","results":dict(sorted(out.items()))},open("data/mcp_link_status.json","w"),indent=1)
    bad=sum(1 for v in out.values() if not all(200<=c<400 for c in v.values()))
    print(f"checked {len(jobs)} links for {len(out)} MCP servers; {bad} with a non-OK link")
if __name__=="__main__": main()
