"""Answer-engine format for best-of, /mcp/ and /s/ list pages (owner-approved SEO audit, Oct 22 2026 PT). Idempotent; runs after build_fresh.
Adds under the intro: a one-line Quick answer (top 3 in page order + generated count), a Ranked table (#, tool, pricing, best for,
open source, GitHub stars) that replaces build_fresh's Quick comparison table on those pages, and a 'Verified on <date>' line where
the date is api/tools.json last_checked (the daily link check). Rank = the order the page lists its tools (each page's own
method note says how it sorts). Every number comes from tools.json or the page itself; nothing is hand-typed."""
import glob,re,json,html,datetime
import build_fresh as F
e=lambda s:html.escape(str(s or ""))
TOP=10
def _fmt(d): return datetime.date.fromisoformat(d).strftime("%B %-d, %Y")
def _anchor(s):
    m=re.search(r'<p class="updated">.*?</p>',s,re.S)
    if m: return m.end()
    h=s.find("</h1>",s.find("<main"))
    if h<0: return -1
    m=re.compile(r'<p class="lede"[^>]*>.*?</p>',re.S).search(s,h)
    return m.end() if m else -1
def _stars(x):
    g=x.get("github_stars")
    return f"{g:,}" if isinstance(g,int) else ""
def block(rows,total,date,how):
    names=[f'<a href="../tools/{x["slug"]}.html">{e(x["name"])}</a>' for x in rows[:3]]
    lst=names[0] if len(names)==1 else ", ".join(names[:-1])+" and "+names[-1]
    qa=f'<p class="qa"><b>Quick answer:</b> the top picks on this list, {how}, are {lst}, out of {total:,} tools ranked below.</p>'
    trs="".join(f'<tr><td>{i+1}</td><th scope="row"><a href="../tools/{x["slug"]}.html">{e(x["name"])}</a></th><td>{e(x["pricing"])}</td><td>{e(F._bestfor(x))}</td><td>{e(F._os(x["pricing"]))}</td><td>{_stars(x)}</td></tr>' for i,x in enumerate(rows[:TOP]))
    cap=f"Top {min(TOP,len(rows))} of {total:,}" if total>TOP else f"All {total:,}"
    tb=(f'<div class="cmpwrap"><h2 class="cmph">Ranked list <span>{cap}, {how}. Pricing as the maker states it; GitHub stars as recorded on each listing; blank means we don\'t have it.</span></h2>'
        f'<div class="cmpscroll"><table class="cmptbl"><thead><tr><th scope="col">#</th><th scope="col">Tool</th><th scope="col">Pricing</th><th scope="col">Best for</th><th scope="col">Open source</th><th scope="col">GitHub stars</th></tr></thead><tbody>{trs}</tbody></table></div></div>')
    vf=f'<p class="muted" style="font-size:13px;margin:0 0 14px">Verified on <time datetime="{date}">{_fmt(date)}</time>: every tool link on this page was checked by our daily link check. No paid placements.</p>' if date else ""
    return f"<!--ci:aeo-->{qa}{tb}{vf}<!--/ci:aeo-->"
def run(t):
    bys={x["slug"]:x for x in t}
    try: date=json.load(open("api/tools.json")).get("last_checked") or ""
    except Exception: date=""
    n=0
    for f in sorted(glob.glob("best/*.html")+glob.glob("mcp/*.html")+glob.glob("s/*.html")):
        if f.endswith("/index.html"): continue
        s0=s=open(f).read()
        if 'http-equiv="refresh"' in s[:4000]: continue
        s=re.sub(r"<!--ci:aeo-->.*?<!--/ci:aeo-->","",s,flags=re.S)
        a=_anchor(s)
        if a<0: continue
        _,b=F._main(s); body=re.sub(r"<!--xl:cmp-->.*?<!--/xl:cmp-->","",s[a:b],flags=re.S)
        sl=[]
        for x in re.findall(r'href="\.\./tools/([a-z0-9-]+)\.html"',body):
            if x in bys and x not in sl: sl.append(x)
        if len(sl)<3:
            if s!=s0: open(f,"w").write(s)
            continue
        s=re.sub(r"<!--xl:cmp-->.*?<!--/xl:cmp-->","",s,flags=re.S)  # the ranked table replaces the unranked quick comparison here
        rows=[bys[x] for x in sl]; how="in this page's order"
        if re.search(r"(sorted|ranked) by GitHub stars",s):  # pages that say they sort by stars (the grid may show this week's new tools first)
            rows=sorted(rows,key=lambda x:-(x.get("github_stars") if isinstance(x.get("github_stars"),int) else -1)); how="by GitHub stars"
        a=_anchor(s); s=s[:a]+block(rows,len(sl),date,how)+s[a:]
        if s!=s0: open(f,"w").write(s)
        n+=1
    print("aeo: quick answer + ranked table + verified line on",n,"pages")
if __name__=="__main__":
    run(json.load(open("tools.json")))
