#!/usr/bin/env python3
"""Refresh the newsletter "Latest issue" data from the public Beehiiv site (read-only).

Reads https://agentscout.beehiiv.com/sitemap.xml (the /feed RSS is off and the API needs a key),
takes every published /p/ post, reads title/subtitle/date from each post page's meta tags, and writes:
  data/newsletter-issues.json  all issues, newest first (newsletter.html archive list, build_extras)
  data/latest-issue.json       newest issue (site-wide signup panel via app.js, api/sections.json)
and rewrites the fallback LATEST line in app.js. On any network error it leaves the files unchanged
and exits 0, so a build never fails because Beehiiv was unreachable.
Usage (from repo root): python3 scripts/update_latest_issue.py   then rebuild: python3 build_site.py
"""
import json,os,re,sys,html,datetime,urllib.request
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB="https://agentscout.beehiiv.com"
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25).read().decode("utf-8","replace")
def meta(s,k):
    m=re.search(r'<meta (?:property|name)="%s" content="([^"]*)"'%re.escape(k),s); return html.unescape(m.group(1)) if m else ""
def main():
    try:
        sm=get(PUB+"/sitemap.xml")
        urls=list(dict.fromkeys(re.findall(r"<loc>(%s/p/[^<]+)</loc>"%re.escape(PUB),sm)))
        issues=[]
        for u in urls:
            s=get(u); t=meta(s,"og:title"); d=meta(s,"article:published_time")
            if not t or not d: continue
            dt=datetime.datetime.fromisoformat(d.replace("Z","+00:00"))
            issues.append({"title":t,"subtitle":meta(s,"og:description"),"date":(dt-datetime.timedelta(hours=7)).date().isoformat(),"published_at":dt.strftime("%Y-%m-%dT%H:%M:%SZ"),"url":u})
    except Exception as ex:
        print("update_latest_issue: Beehiiv unreachable, keeping current data:",ex); return 0
    if not issues: print("update_latest_issue: no posts found, keeping current data"); return 0
    issues.sort(key=lambda x:x["published_at"],reverse=True); L=issues[0]
    os.makedirs(os.path.join(ROOT,"data"),exist_ok=True)
    json.dump(issues,open(os.path.join(ROOT,"data/newsletter-issues.json"),"w"),indent=1,ensure_ascii=False)
    lat=dict(L,display_date=datetime.date.fromisoformat(L["date"]).strftime("%b %-d, %Y"))
    json.dump(lat,open(os.path.join(ROOT,"data/latest-issue.json"),"w"),indent=1,ensure_ascii=False)
    ap=os.path.join(ROOT,"app.js"); a=open(ap).read()
    line="var LATEST="+json.dumps({"title":L["title"],"date":lat["display_date"],"sub":L["subtitle"],"url":L["url"]},ensure_ascii=False)+";"
    a2=re.sub(r"var LATEST=\{.*?\};",lambda m:line,a,count=1)
    if a2!=a: open(ap,"w").write(a2)
    print("update_latest_issue: latest =",L["title"],L["date"],L["url"],"(%d issues)"%len(issues)); return 0
if __name__=="__main__": sys.exit(main())
