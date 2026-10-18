"""Daily GitHub snapshot for listed tools (no token, no API: public repo page + Atom feeds, ~1 req/s).
Writes data/stars/YYYY-MM-DD.json ({slug: stars}) and data/github.json ({slug: {repo, stars, release_tag, release_date, release_url,
releases:[[tag,date,url]..3], pushed, archived, fetched}}). Previous values are kept when a fetch fails.
Usage (from repo root): python3 github_snapshot.py [--limit N]"""
import json,re,os,sys,time,urllib.request,datetime,html
from zoneinfo import ZoneInfo
UA={"User-Agent":"AgentScout-snapshot/1.0 (+https://agentscouthq.com)"}
def get(u,tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25) as r: return r.read().decode("utf-8","replace")
        except urllib.error.HTTPError as ex:
            if ex.code==404: return None
            if ex.code in (429,403): time.sleep(60*(i+1)); continue
            time.sleep(5)
        except Exception: time.sleep(5)
    return None
def entries(atom,n=3):
    out=[]
    for m in re.finditer(r"<entry>(.*?)</entry>",atom or "",re.S):
        b=m.group(1); t=re.search(r"<title>(.*?)</title>",b,re.S); d=re.search(r"<updated>(.*?)</updated>",b); l=re.search(r'<link[^>]*href="([^"]+)"',b)
        if t and d: out.append([html.unescape(t.group(1)).strip()[:80],d.group(1)[:10],l.group(1) if l else ""])
        if len(out)>=n: break
    return out
def save(G,snap,today):
    json.dump(dict(sorted(G.items())),open("data/github.json","w"),indent=1,ensure_ascii=False)
    if snap:
        p=f"data/stars/{today}.json"; old=json.load(open(p)) if os.path.exists(p) else {}
        old.update(snap); json.dump(dict(sorted(old.items())),open(p,"w"),indent=0)
def main():
    lim=int(sys.argv[sys.argv.index("--limit")+1]) if "--limit" in sys.argv else 10**9
    t=json.load(open("tools.json")); today=datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    os.makedirs("data/stars",exist_ok=True)
    G=json.load(open("data/github.json")) if os.path.exists("data/github.json") else {}
    snap={}; ok=fail=0
    repos=[(x["slug"],m.group(1).rstrip("/")) for x in t for m in [re.search(r"github\.com/([^/\s]+/[^/\s#?]+)",x.get("github") or "")] if m][:lim]
    for slug,repo in repos:
        repo=re.sub(r"\.git$","",repo); g=G.get(slug,{}); g["repo"]=repo
        if "--resume" in sys.argv and g.get("fetched")==today and "stars" in g: snap[slug]=g["stars"]; continue
        page=get(f"https://github.com/{repo}"); time.sleep(1)
        m=re.search(r'"stargazerCount":(\d+)',page or "")
        if m:
            g["stars"]=int(m.group(1)); snap[slug]=g["stars"]; ok+=1
            a=re.search(r'"isArchived":(true|false)',page); g["archived"]=bool(a and a.group(1)=="true")
        else: fail+=1
        rel=get(f"https://github.com/{repo}/releases.atom"); time.sleep(1)
        if rel is not None:
            r=entries(rel)
            g["releases"]=r
            if r: g["release_tag"],g["release_date"],g["release_url"]=r[0]
            else: [g.pop(k,None) for k in ("release_tag","release_date","release_url")]
        com=get(f"https://github.com/{repo}/commits.atom"); time.sleep(1)
        c=entries(com,1)
        if c: g["pushed"]=c[0][1]
        g["fetched"]=today; G[slug]=g; n_done=len(G)
        if (ok+fail)%25==0:
            save(G,snap,today); print(f"progress {ok+fail}/{len(repos)}",flush=True)
    save(G,snap,today)
    print(f"github snapshot {today}: {ok} repos with stars, {fail} failed, {sum(1 for v in G.values() if v.get('release_tag'))} with releases")
if __name__=="__main__": main()
