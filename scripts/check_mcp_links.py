"""MCP link check (Oct 22 2026): requests every MCP server's listed link (and GitHub repo when set) and writes
data/mcp_link_status.json. Read by build_aicite.py for /mcp/link-status.html. Run before a build; network only here.

The population is every MCP server in tools.json, including catalog_only. A catalog-only
server with no row yet is unverified and is not part of the live percentage.

A bot status of 403, 406, 429, or 5xx (including Cloudflare 520/523), or a timeout, is retried
once with a browser GET before it can count as down. An http URL that still returns 5xx is
retried once as https. A GitHub 404 is a github_404 note, not a down row, when the site URL is OK.
"""
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
def public(u, resolve=None):
    """True only if every address the host resolves to is global (not private, shared, or reserved)."""
    try:
        p=urllib.parse.urlsplit(u); h=p.hostname
        if p.scheme not in("http","https") or not h: return False
        addrs=set(resolve(h) if resolve else {i[4][0] for i in socket.getaddrinfo(h,None)})
        if not addrs: return False
        for a in addrs:
            ip=ipaddress.ip_address(str(a).split("%")[0])
            if FAKEIP and ip in FAKE: continue
            # is_global is false for 100.64.0.0/10. is_multicast stays explicit: 224/4 is global on this interpreter.
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified or not ip.is_global: return False
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
def _pass(c):
    """Same single-link OK rule as ok_code: 200-399, 405, or 401/403/429."""
    return isinstance(c,int) and ((200<=c<400) or c==405 or c in (401,403,429))
def _hard(c):
    """Bot HTTP statuses that get one browser GET before the row can be marked down."""
    return isinstance(c,int) and (c in (403,406,429) or 500<=c<=599)
def _get(op,u,headers,timeout):
    try:
        r=op(urllib.request.Request(u,headers=headers,method="GET"),timeout=timeout); return r.status
    except urllib.error.HTTPError as ex: return ex.code
    except Exception: return 0
def probe(u, opener=None):
    """HTTP status; 0 = no response. A TLS failure, timeout or reset for our bot UA that a browser UA gets past
    (or a box-only TLS failure) is reported as 403 = "Reachable, blocks automated checks", not "Not responding".
    403, 406, 429, and 5xx (Cloudflare 520/523 included) get one browser GET first; a passing browser status is kept."""
    if not public(u): return 0  # skipped: non-public or unresolvable host
    op=opener or OPEN
    err=None
    code=None
    for m in ("HEAD","GET"):
        try:
            r=op(urllib.request.Request(u,headers=UA,method=m),timeout=20); code=r.status; break
        except urllib.error.HTTPError as ex:
            if m=="GET" or ex.code not in (403,405,406,400,404,429,501): code=ex.code; break  # 406: some hosts reject HEAD only (WordRadar, Nov 9 2026)
        except Exception as ex: err=ex
    if code is not None and _hard(code):
        b=_get(op,u,BUA,25)
        return b if _pass(b) else code
    if code is not None: return code
    if err is None: return 0
    try:
        r=op(urllib.request.Request(u,headers=BUA,method="GET"),timeout=25); return r.status if r.status>=400 else 403
    except urllib.error.HTTPError as ex: return ex.code if ex.code not in (200,) else 403
    except Exception as ex2:
        return 403 if (_tls(err) or _tls(ex2)) else 0
def check_link(u, opener=None):
    """Probe u. An http URL that still returns 5xx is retried once as https."""
    code=probe(u, opener)
    if isinstance(u,str) and u.startswith("http://") and isinstance(code,int) and 500<=code<=599:
        https="https://"+u[len("http://"):]
        if https!=u and public(https):
            c2=probe(https, opener)
            if _pass(c2): return c2,"https works"
    return code,None
def numeric_codes(row):
    return {k:c for k,c in (row or {}).items() if isinstance(c,int)}
def ok_code(c,v):
    """Unchanged live rule: 200-399 or 405, and 401/403/429 when GitHub is OK or it is the only code."""
    return (200<=c<400) or c==405 or (c in (401,403,429) and (200<=v.get("github",0)<400 or len(v)==1))
def is_down(row):
    nums=numeric_codes(row)
    return not all(ok_code(c,nums) for c in nums.values())
def link_row(url_code, github_code=None, note=None):
    """Stored row. A GitHub 404 is a note when the site URL passes, not a failing code."""
    notes=[]
    if note:
        for part in str(note).split("; "):
            if part and part not in notes: notes.append(part)
    row={"url":url_code}
    if github_code is not None:
        if github_code==404 and _pass(url_code):
            if "github_404" not in notes: notes.append("github_404")
        else:
            row["github"]=github_code
    if notes: row["note"]="; ".join(notes)
    return row
def mcp_targets(tools):
    """Every MCP server, including catalog_only. The daily run does not skip the bulk import."""
    return [x for x in tools if x.get("category")=="MCP servers"]
def _only(argv):
    only=[]
    i=0
    while i<len(argv):
        a=argv[i]
        if a=="--slug":
            if i+1>=len(argv): raise SystemExit("--slug needs a value")
            only.append(argv[i+1]); i+=2; continue
        if a.startswith("--slug="):
            only.append(a.split("=",1)[1]); i+=1; continue
        raise SystemExit(f"unknown arg {a}")
    return only
def _write(doc):
    open("data/mcp_link_status.json","w").write(json.dumps(doc,indent=1))
def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    only=_only(argv)
    t=mcp_targets(json.load(open("tools.json")))
    if only:
        want=set(only)
        t=[x for x in t if x["slug"] in want]
        missing=want-{x["slug"] for x in t}
        if missing: raise SystemExit("unknown slug: "+", ".join(sorted(missing)))
    jobs={}
    for x in t:
        jobs[(x["slug"],"url")]=x["url"]
        if x.get("github") and x["github"]!=x["url"]: jobs[(x["slug"],"github")]=x["github"]
    raw={}
    with cf.ThreadPoolExecutor(24) as ex:
        fs={ex.submit(check_link,u):k for k,u in jobs.items()}
        for f in cf.as_completed(fs): raw.setdefault(fs[f][0],{})[fs[f][1]]=f.result()
    out={}
    for slug,parts in raw.items():
        url_code,url_note=parts["url"]
        gh=parts.get("github")
        notes=[n for n in (url_note, gh[1] if gh else None) if n]
        out[slug]=link_row(url_code, gh[0] if gh else None, "; ".join(notes) if notes else None)
    if only:
        doc=json.load(open("data/mcp_link_status.json"))
        res=doc.setdefault("results",{})
        for slug,row in out.items(): res[slug]=row
        _write(doc)
    else:
        now=d.datetime.now(z.ZoneInfo("America/Los_Angeles"))
        _write({"checked":now.strftime("%Y-%m-%d %H:%M"),"tz":"America/Los_Angeles","includes_catalog_only":True,"results":dict(sorted(out.items()))})
    bad=sum(1 for v in out.values() if is_down(v))
    print(f"checked {len(jobs)} links for {len(out)} MCP servers; {bad} broken links")
if __name__=="__main__": main()
