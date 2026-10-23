"""MCP link check (Oct 22 2026): requests every MCP server's listed link (and GitHub repo when set) and writes
data/mcp_link_status.json. Read by build_aicite.py for /mcp/link-status.html. Run before a build; network only here."""
import json,os,sys,socket,ipaddress,urllib.parse,datetime as d,zoneinfo as z,urllib.request,urllib.error,concurrent.futures as cf
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UA={"User-Agent":"Mozilla/5.0 (compatible; AgentScoutLinkCheck/1.0; +https://agentscouthq.com/about.html)"}
FAKE=ipaddress.ip_network("198.18.0.0/15")
def _fakeip():
    # Sandboxed networks with a fake-IP DNS proxy resolve every host into 198.18.0.0/15; the proxy, not this script,
    # then picks the real destination. Detected by a known public host resolving there; only that range is then allowed.
    try: return all(ipaddress.ip_address(i[4][0]) in FAKE for i in socket.getaddrinfo("example.com",None))
    except Exception: return False
FAKEIP=_fakeip()
def public(u):
    """True only if every address the host resolves to is public (no private/loopback/link-local/reserved)."""
    try:
        p=urllib.parse.urlsplit(u); h=p.hostname
        if p.scheme not in("http","https") or not h: return False
        for a in {i[4][0] for i in socket.getaddrinfo(h,None)}:
            ip=ipaddress.ip_address(a.split("%")[0])
            if FAKEIP and ip in FAKE: continue
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified: return False
        return True
    except Exception: return False
class Guard(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,hdrs,newurl):
        if not public(newurl): raise urllib.error.URLError("redirect to non-public address skipped")
        return super().redirect_request(req,fp,code,msg,hdrs,newurl)
OPEN=urllib.request.build_opener(Guard).open
def probe(u):
    if not public(u): return 0  # skipped: non-public or unresolvable host
    for m in ("HEAD","GET"):
        try:
            r=OPEN(urllib.request.Request(u,headers=UA,method=m),timeout=20); return r.status
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
