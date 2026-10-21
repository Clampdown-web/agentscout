"""Leaderboard page /leaderboard/ (Oct 21 2026, owner-approved in Work Chat: "Yes to all the suggestions").
Real data only: visitor star ratings and approved written reviews from reviews.json (refreshed from the Worker by build_reviews
on every build), and GitHub stars from tools.json. Nothing is seeded or estimated.
Tabs: Top rated (min MIN_RATED rating(s); no review requirement; Oct 21 owner-approved: Most loved is the default tab), Most reviewed (approved written reviews), Most loved (same weighting as the directory's
"Most loved" sort: rated tools first, then open-source tools by GitHub stars as the fallback)."""
import json,html,datetime
import build_extras as X
B="https://agentscouthq.com/"; MIN_RATED=1; TOPN=50; DEF="loved"
e=lambda s:html.escape(str(s if s is not None else ""))
bay=lambda r:(r["avg"]*r["count"]+12)/(r["count"]+3) if r and r.get("count") else 0  # same as catfilter.js
def row(i,x,stat):
    medal={1:"lb1",2:"lb2",3:"lb3"}.get(i,"")
    return (f'<li class="lbr {medal}"><span class="lbn">{i}</span><a class="lbt" href="../tools/{e(x["slug"])}.html">{X.ico(x,"../","sm")}'
            f'<span class="lbx"><b>{e(x["name"])}</b><span class="muted">{e(x["category"])}</span></span></a><span class="lbs">{stat}</span></li>')
def stars(v): return f'<span class="rv-stars" style="--r:{v}" aria-hidden="true">★★★★★</span>'
def rt(d): c=d["count"]; return f'{stars(d["avg"])}<span><b>{d["avg"]:.1f}</b> <span class="muted">({c} rating{"s" if c!=1 else ""})</span></span>'
def gh(x): return f'<span>★ <b>{x["github_stars"]:,}</b> <span class="muted">GitHub</span></span>'
def pages(t):
    try: J=json.load(open("reviews.json")); D=J.get("tools",{}); upd=J.get("updated","")
    except Exception: D={}; upd=""
    bs={x["slug"]:x for x in t}; R={k:v for k,v in D.items() if k in bs and v.get("count")}
    nrated=len(R); nrev=sum(len(v.get("reviews") or []) for v in R.values())
    top=sorted([k for k,v in R.items() if v["count"]>=MIN_RATED],key=lambda k:(-R[k]["avg"],-R[k]["count"],bs[k]["name"].lower()))[:TOPN]
    rev=sorted([k for k,v in R.items() if v.get("reviews")],key=lambda k:(-len(R[k]["reviews"]),-R[k]["count"],bs[k]["name"].lower()))[:TOPN]
    loved=sorted(R,key=lambda k:(-bay(R[k]),-R[k]["count"],bs[k]["name"].lower()))
    osrc=sorted([x for x in t if x.get("github") and x.get("github_stars") and x["slug"] not in R],key=lambda x:-x["github_stars"])
    lv=[(bs[k],rt(R[k])) for k in loved]+[(x,gh(x)) for x in osrc]
    lv=lv[:max(TOPN,len(loved))]
    ol=lambda L:f'<ol class="lbl">{"".join(row(i+1,x,s) for i,(x,s) in enumerate(L))}</ol>'
    empty=lambda msg:f'<div class="lbe"><p>{msg}</p><p><a class="btn primary" href="../index.html#directory">Find a tool you use and rate it</a></p></div>'
    p1=(ol([(bs[k],rt(R[k])) for k in top]) if top else "")+(empty("No tools have been rated yet. Be the first to rate one.") if not top else "")
    p2=(ol([(bs[k],f'<span><b>{len(R[k]["reviews"])}</b> <span class="muted">review{"s" if len(R[k]["reviews"])!=1 else ""}</span></span>') for k in rev]) if rev else "")+(empty("Very few written reviews so far. Approved reviews show up here.") if len(rev)<10 else "")
    p3=ol(lv)
    try: when=datetime.datetime.fromisoformat(upd.replace("Z","+00:00")).astimezone(datetime.timezone(datetime.timedelta(hours=-7))).strftime("%b %-d, %Y")
    except Exception: when=""
    tabs=[("top","Top rated",p1,f"Average visitor star rating. Tools need at least {MIN_RATED} rating{"s" if MIN_RATED!=1 else ""} to be ranked. Ties go to the tool with more ratings."),
          ("reviewed","Most reviewed",p2,"Number of approved written reviews (each one is checked before it goes live)."),
          ("loved","Most loved",p3,"Rated tools first, weighted toward 4★ until a tool has more ratings (same as the directory's Most loved sort). Tools with no ratings yet follow, ranked by GitHub stars (open-source tools only).")]
    tb="".join(f'<button type="button" role="tab" id="lbt-{k}" aria-controls="lb-{k}" aria-selected="{"true" if k==DEF else "false"}">{n}</button>' for i,(k,n,_,_) in enumerate(tabs))
    pn="".join(f'<section role="tabpanel" id="lb-{k}" aria-labelledby="lbt-{k}"{" hidden" if k!=DEF else ""}><h2>{n}</h2><p class="muted lbh">{h}</p>{p}</section>' for i,(k,n,p,h) in enumerate(tabs))
    css=("<style>.lbtabs{display:flex;gap:6px;flex-wrap:wrap;margin:16px 0 8px}.lbtabs button{font:inherit;font-size:14px;padding:8px 14px;min-height:40px;border-radius:999px;border:1px solid var(--line,rgba(127,127,127,.35));background:transparent;color:inherit;cursor:pointer}"
         ".lbtabs button[aria-selected=true]{background:#6b8afd;border-color:#6b8afd;color:#fff}.lb h2{font-size:18px;margin:16px 0 4px}.lbh{font-size:13px;margin:0 0 10px}"
         ".lbl{list-style:none;padding:0;margin:0}.lbr{display:flex;align-items:center;gap:10px;padding:10px 8px;border-top:1px solid var(--line,rgba(127,127,127,.2));border-radius:8px;min-width:0}"
         ".lb1{background:rgba(245,179,1,.12)}.lb2{background:rgba(160,170,185,.14)}.lb3{background:rgba(205,127,50,.13)}.lbn{flex:0 0 28px;text-align:center;font-weight:700;font-variant-numeric:tabular-nums}"
         ".lb1 .lbn::before{content:'🥇'}.lb2 .lbn::before{content:'🥈'}.lb3 .lbn::before{content:'🥉'}.lb1 .lbn,.lb2 .lbn,.lb3 .lbn{font-size:0}.lb1 .lbn::before,.lb2 .lbn::before,.lb3 .lbn::before{font-size:20px}"
         ".lbt{display:flex;align-items:center;gap:10px;flex:1 1 auto;min-width:0;color:inherit;text-decoration:none}.lbx{display:flex;flex-direction:column;min-width:0}.lbx b,.lbx span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.lbx span{font-size:12px}"
         ".lbs{flex:0 0 auto;display:flex;flex-direction:column;align-items:flex-end;gap:2px;font-size:13px;text-align:right}.lbs .rv-stars{font-size:13px}"
         ".lbe{padding:14px;border:1px dashed var(--line,rgba(127,127,127,.4));border-radius:12px;margin:12px 0}.lbe p{margin:0 0 10px}.lbe p:last-child{margin:0}"
         "@media(max-width:420px){.lbr{gap:8px;padding:10px 4px}.lbs{font-size:12px}}</style>")
    js=('<script>(function(){var b=document.querySelectorAll(".lbtabs button");function go(k,push){b.forEach(function(x){var on=x.id==="lbt-"+k;x.setAttribute("aria-selected",on);document.getElementById(x.getAttribute("aria-controls")).hidden=!on});if(push)history.replaceState(null,"","#"+k)}'
        'b.forEach(function(x){x.addEventListener("click",function(){go(x.id.slice(4),1)})});var h=location.hash.slice(1);if(document.getElementById("lbt-"+h))go(h)})();</script>')
    title="AI Agent Tools Leaderboard: top rated, most reviewed and most loved · AgentScout"
    desc=f"The AgentScout leaderboard ranks AI agent tools by real visitor star ratings, approved reviews and GitHub stars. {nrated} tools rated so far; rate the tools you use."[:160]
    body=(f'<p class="crumb"><a href="../index.html">AgentScout</a> › Leaderboard</p><div class="lb"><h1>AI agent tools leaderboard</h1>'
          f'<p>Rankings from real visitor ratings and reviews on AgentScout, plus GitHub stars for open-source tools. No paid placements. {nrated} tool{"s" if nrated!=1 else ""} rated and {nrev} written review{"s" if nrev!=1 else ""} so far{f" (updated {when})" if when else ""}. '
          f'Used a tool? Open its page and tap <b>Rate this tool</b>.</p>'
          f'<div class="lbtabs" role="tablist" aria-label="Leaderboard rankings" data-pagefind-ignore>{tb}</div><div data-pagefind-ignore>{pn}</div>'
          f'<p class="muted" style="font-size:13px;margin-top:20px">Ratings come from site visitors and are not verified purchases. One rating per tool per visitor; written reviews are checked before they appear. <a href="../privacy.html#reviews">How reviews work</a></p></div>{css}{js}')
    canon=B+"leaderboard/"
    items=[{"@type":"ListItem","position":i+1,"url":f'{B}tools/{x["slug"]}.html',"name":x["name"]} for i,(x,_) in enumerate(lv[:20])]
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
        {"@type":"ItemList","name":"Most loved AI agent tools","itemListElement":items},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Leaderboard","item":canon}]}]}
    import os; os.makedirs("leaderboard",exist_ok=True)
    open("leaderboard/index.html","w",encoding="utf-8").write(X.shell("../",title,desc,canon,body,ld))
    print(f"leaderboard: {len(top)} top rated, {len(rev)} most reviewed, {len(lv)} most loved ({nrated} rated)")
    return [canon]
