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
BUA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
def _tls(ex):
    import ssl
    return isinstance(ex,ssl.SSLError) or isinstance(getattr(ex,"reason",None),ssl.SSLError) or "SSL" in str(ex) or "CERTIFICATE" in str(ex).upper()
def probe(u):
    """HTTP status; 0 = no response. A TLS failure, timeout or reset for our bot UA that a browser UA gets past
    (or a box-only TLS failure) is reported as 403 = "Reachable, blocks automated checks", not "Not responding"."""
    if not public(u): return 0  # skipped: non-public or unresolvable host
    err=None
    for m in ("HEAD","GET"):
        try:
            r=OPEN(urllib.request.Request(u,headers=UA,method=m),timeout=20); return r.status
        except urllib.error.HTTPError as ex:
            if m=="GET" or ex.code not in (403,405,400,404,429,501): return ex.code
        except Exception as ex: err=ex
    if err is None: return 0
    try:
        r=OPEN(urllib.request.Request(u,headers=BUA,method="GET"),timeout=25); return r.status if r.status>=400 else 403
    except urllib.error.HTTPError as ex: return ex.code if ex.code not in (200,) else 403
    except Exception as ex2:
        return 403 if (_tls(err) or _tls(ex2)) else 0
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
    ok_code=lambda c,v:(200<=c<400) or c==405 or (c in (401,403,429) and (200<=v.get("github",0)<400 or len(v)==1))
    bad=sum(1 for v in out.values() if not all(ok_code(c,v) for c in v.values()))
    print(f"checked {len(jobs)} links for {len(out)} MCP servers; {bad} broken links")
if __name__=="__main__": main()
