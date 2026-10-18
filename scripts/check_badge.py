"""Cheap check: does a maker's homepage link to AgentScout or show our badge?
Usage: python3 scripts/check_badge.py [slug ...]   (no slugs = every tool with "maker_submitted": true)
Fetches the tool's website (and the GitHub README when the tool has a repo) and looks for an agentscouthq.com link
or one of our badge images (badges/listed-*.svg, badges/featured-*.svg). Read-only; prints one line per tool and
exits 0 if at least one tool qualifies for a featured spot (reason "badge_backlink"), else 1."""
import json,re,sys,urllib.request
UA={"User-Agent":"Mozilla/5.0 (compatible; AgentScoutBadgeCheck/1.0; +https://agentscouthq.com/badges.html)"}
PAT=re.compile(r'agentscouthq\.com|agentscout-image\.agentscouthq\.workers\.dev',re.I)
def get(u):
    try: return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=15).read(2_000_000).decode("utf-8","ignore")
    except Exception as ex: return ""
def check(x):
    urls=[x.get("website") or x["url"]]
    if x.get("repo"): urls.append(f'https://raw.githubusercontent.com/{x["repo"]}/HEAD/README.md')
    for u in urls:
        h=get(u); m=PAT.search(h)
        if m:
            badge=bool(re.search(r'agentscouthq\.com/badges/(listed|featured)-(light|dark)\.(svg|png)',h,re.I))
            return True,u,("badge image" if badge else "link")
    return False,urls[0],""
if __name__=="__main__":
    T=json.load(open("tools.json")); by={x["slug"]:x for x in T}
    sl=sys.argv[1:] or [x["slug"] for x in T if x.get("maker_submitted")]
    ok=False
    for s in sl:
        x=by.get(s)
        if not x: print(s,"unknown slug"); continue
        q,u,what=check(x); ok|=q
        print(f"{s}: {'HAS ' + what if q else 'no AgentScout link or badge'} ({u})")
    sys.exit(0 if ok else 1)
