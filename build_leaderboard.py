"""Leaderboard page /leaderboard/ (Oct 21 2026, owner-approved in Work Chat).
Real data only: visitor star ratings and approved written reviews from reviews.json (refreshed from the Worker by build_reviews
on every build), GitHub stars from tools.json and the daily snapshots in data/stars/. Nothing is seeded or estimated.
Tabs: Most loved (default), Top rated (min MIN_RATED rating), Most reviewed, Trending this week.
Oct 21 2026 additions (owner-approved): category / Free / Open-source filters (client-side, same categories and rules as the
homepage directory), rank-movement arrows vs the rank snapshot from ~7 days earlier (data/lb-ranks/), Rate buttons, Trending tab
(new GitHub stars from data/stars/, new ratings from data/ratings/ count snapshots, new reviews by timestamp), and
"Ranked #N on AgentScout" badges (badges/rank/<slug>.svg + /leaderboard/badges.html).
Every build (build_site.py -> build_extras.build) rewrites today's data/ratings and data/lb-ranks snapshot files; commit them."""
import json,html,datetime,os,glob,re
import build_extras as X
B="https://agentscouthq.com/"; MIN_RATED=1; TOPN=100; DEF="loved"; XTRA=10
PT=datetime.timezone(datetime.timedelta(hours=-7))
e=lambda s:html.escape(str(s if s is not None else ""))
bay=lambda r:(r["avg"]*r["count"]+12)/(r["count"]+3) if r and r.get("count") else 0  # same as catfilter.js
def pc(x):  # same buckets as the homepage directory's pricing filter (index.html pc())
    p=(x.get("pricing") or "").lower()
    if re.match(r"(open|free$)",p): return "freemium" if "cloud" in p else "free"
    if re.search(r"freemium|\+ cloud",p): return "freemium"
    return "paid" if re.match(r"(paid|usage|enterprise)",p) else "unknown"
isfree=lambda x:pc(x) in ("free","freemium")   # directory "Free or free plan"
isos=lambda x:bool(re.match(r"open",x.get("pricing") or "",re.I))  # directory "Open source only"
def load(p,d):
    try: return json.load(open(p))
    except Exception: return d
def snap_before(dirn,today,days):
    """Newest snapshot dated <= today-days, else the oldest one within the window (returns (date,data) or (None,None))."""
    fs=sorted(glob.glob(f"{dirn}/*.json")); ds=[os.path.basename(f)[:-5] for f in fs]
    cut=(today-datetime.timedelta(days=days)).isoformat()
    old=[d for d in ds if d<=cut]
    if old: d=old[-1]
    else:
        win=[d for d in ds if d<today.isoformat()]
        if not win: return None,None
        d=win[0]
    return d,load(f"{dirn}/{d}.json",None)
def arrow(k,slug,rank,prev):
    if not prev or k not in prev or slug not in prev[k]: return ""
    p=prev[k][slug]; d=p-rank
    if d>0: return f'<span class="lbm up" title="Up {d} since last week" aria-label="Up {d} since last week">▲{d}</span>'
    if d<0: return f'<span class="lbm dn" title="Down {-d} since last week" aria-label="Down {-d} since last week">▼{-d}</span>'
    return '<span class="lbm eq" title="Same rank as last week" aria-label="Same rank as last week">–</span>'
def row(i,x,stat,mv="",extra=False):
    medal={1:"lb1",2:"lb2",3:"lb3"}.get(i,"")
    return (f'<li class="lbr {medal}" data-c="{e(x["category"])}" data-f="{1 if isfree(x) else 0}" data-o="{1 if isos(x) else 0}"{" data-x hidden" if extra else ""}>'
            f'<span class="lbn">{i}</span><a class="lbt" href="../tools/{e(x["slug"])}.html">{X.ico(x,"../","sm")}'
            f'<span class="lbx"><b>{e(x["name"])}</b><span class="muted">{e(x["category"])}</span></span><span class="lbd muted">{e(short(x.get("description")))}</span></a><span class="lbs">{stat}{mv}</span>'
            f'<a class="lbrate" href="../tools/{e(x["slug"])}.html#rv-form" aria-label="Rate {e(x["name"])}">Rate</a></li>')
def short(d,n=100):  # tool's one-line description, cut at a word boundary (Oct 21 2026, owner-approved)
    d=" ".join(str(d or "").split())
    return d if len(d)<=n else d[:n].rsplit(" ",1)[0].rstrip(",;:.-–—")+"…"
def stars(v): return f'<span class="rv-stars" style="--r:{v}" aria-hidden="true">★★★★★</span>'
def rt(d): c=d["count"]; return f'{stars(d["avg"])}<span><b>{d["avg"]:.1f}</b> <span class="muted">({c} rating{"s" if c!=1 else ""})</span></span>'
def both(x,d):  # Oct 21 2026 owner request: star rating block AND GitHub count on every row
    r=rt(d) if d and d.get("count") else '<span class="muted">No ratings yet</span>'
    g=gh(x) if x.get("github") and x.get("github_stars") else ('<span class="muted lbcs">Closed source</span>' if d and d.get("count") else "")
    return f'<span class="lbb">{r}</span>{g}'
def gh(x): return f'<span>★ <b>{x["github_stars"]:,}</b> <span class="muted">GitHub</span></span>'
def svg(n):
    txt=f"Ranked #{n} on AgentScout" if n else "Listed on AgentScout"; sub="Most loved AI agent tools" if n else "AI agent tools directory"
    w=max(200,int(len(txt)*7.4)+58)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="54" viewBox="0 0 {w} 54" role="img" aria-label="{e(txt)}">'
            f'<rect x=".5" y=".5" width="{w-1}" height="53" rx="10" fill="#ffffff" stroke="#e4e4ea"/>'
            f'<circle cx="24" cy="25" r="9" fill="none" stroke="#111111" stroke-width="3"/><path d="M31 32l7 7" stroke="#111111" stroke-width="3.2" stroke-linecap="round"/>'
            f'<text x="46" y="24" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="13" font-weight="700" fill="#111111">{e(txt)}</text>'
            f'<text x="46" y="40" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="11" fill="#5b5b66">{e(sub)}</text></svg>')
def pages(t):
    J=load("reviews.json",{}); D=J.get("tools",{}) if isinstance(J,dict) else {}; upd=J.get("updated","") if isinstance(J,dict) else ""
    bs={x["slug"]:x for x in t}; R={k:v for k,v in D.items() if k in bs and v.get("count")}
    nrated=len(R); nrev=sum(len(v.get("reviews") or []) for v in R.values())
    now=datetime.datetime.now(PT); today=now.date()
    cats=sorted({x["category"] for x in t})  # same list and names as the homepage directory category filter (app: [...new Set(tools.map(t=>t.category))].sort())
    # --- snapshots written every build (real counts only)
    os.makedirs("data/ratings",exist_ok=True); os.makedirs("data/lb-ranks",exist_ok=True)
    json.dump({k:v["count"] for k,v in sorted(R.items())},open(f"data/ratings/{today}.json","w"),indent=0)
    prevd,prev=snap_before("data/lb-ranks",today,7)
    if prevd and prevd>(today-datetime.timedelta(days=6)).isoformat(): prev=None  # only compare against a snapshot at least ~a week old
    # --- rankings
    def topn(L,key): return L[:TOPN],[k for k in L[TOPN:] if k]  # (shown, candidates for extras)
    top=sorted([k for k,v in R.items() if v["count"]>=MIN_RATED],key=lambda k:(-R[k]["avg"],-R[k]["count"],bs[k]["name"].lower()))
    rev=sorted([k for k,v in R.items() if v.get("reviews")],key=lambda k:(-len(R[k]["reviews"]),-R[k]["count"],bs[k]["name"].lower()))
    loved=sorted(R,key=lambda k:(-bay(R[k]),-R[k]["count"],bs[k]["name"].lower()))
    osrc=sorted([x["slug"] for x in t if x.get("github") and x.get("github_stars") and x["slug"] not in R],key=lambda s:-bs[s]["github_stars"])
    lvall=loved+osrc; NL=max(TOPN,len(loved))
    # Trending: new ratings (count snapshots), new reviews (timestamps), new GitHub stars (daily snapshots), last 7 days
    sd=sorted(os.path.basename(f)[:-5] for f in glob.glob("data/stars/*.json")); trend=[]; tnote=""
    if len(sd)>=2:
        end=sd[-1]; cut=(datetime.date.fromisoformat(end)-datetime.timedelta(days=7)).isoformat()
        base=[d for d in sd if d<=cut]; base=base[-1] if base else sd[0]
        S0=load(f"data/stars/{base}.json",{}); S1=load(f"data/stars/{end}.json",{})
        rd,R0=snap_before("data/ratings",today,7)
        ms=(now-datetime.timedelta(days=7)).timestamp()*1000
        for s in bs:
            ds=(S1.get(s,0)-S0[s]) if s in S0 and s in S1 else 0
            nr=(R.get(s,{}).get("count",0)-R0.get(s,0)) if R0 is not None and s in R else 0
            nv=sum(1 for r in (R.get(s,{}).get("reviews") or []) if (r.get("ts") or 0)>=ms)
            if ds>0 or nr>0 or nv>0: trend.append((s,max(nr,0),nv,max(ds,0)))
        trend.sort(key=lambda z:(-(z[1]+z[2]),-z[3],bs[z[0]]["name"].lower()))
        fmt=lambda d:datetime.date.fromisoformat(d).strftime("%b %-d")
        days=(datetime.date.fromisoformat(end)-datetime.date.fromisoformat(base)).days
        tnote=(f"New GitHub stars from our daily snapshots ({fmt(base)} to {fmt(end)}{f', only {days} day'+('s' if days!=1 else '')+' of history so far' if days<7 else ''}), plus new visitor ratings and approved reviews in the last 7 days"
               f"{'' if R0 is not None else ' (rating counts are tracked from today, so new ratings start counting next week; new reviews count already)'}. Ranked by new ratings and reviews first, then new GitHub stars.")
    def tstat(z):
        s,nr,nv,ds=z; bits=[]
        if nr: bits.append(f'<b>+{nr}</b> <span class="muted">rating{"s" if nr!=1 else ""}</span>')
        if nv: bits.append(f'<b>+{nv}</b> <span class="muted">review{"s" if nv!=1 else ""}</span>')
        if ds: bits.append(f'<b>+{ds:,}</b> <span class="muted">GitHub ★</span>')
        return f'<span>{" · ".join(bits)}</span>'
    # extras: rows beyond the overall cut that are needed so each category / Free / Open-source filter still shows up to XTRA
    def extras(L,cap):
        keep=set(); cnt={}
        for s in L[cap:]:
            x=bs[s]; ks=[x["category"]]+(["f"] if isfree(x) else [])+(["o"] if isos(x) else [])
            if any(cnt.get(k,0)<XTRA for k in ks):
                keep.add(s)
                for k in ks: cnt[k]=cnt.get(k,0)+1
        return keep
    ranks={}
    def ol(k,L,cap,stat):
        ex=extras(L,cap); ranks[k]={s:i+1 for i,s in enumerate(L[:cap])}; out=[]
        for i,s in enumerate(L):
            if i<cap: out.append(row(i+1,bs[s],stat(s),arrow(k,s,i+1,prev)))
            elif s in ex: out.append(row(i+1,bs[s],stat(s),"",True))
        return f'<ol class="lbl">{"".join(out)}</ol>' if out else ""
    fe='<div class="lbe lbf" hidden><p>No ranked tools match these filters yet.</p><p><a class="btn primary" href="../index.html#directory">Browse the directory</a></p></div>'
    empty=lambda msg,cls="":f'<div class="lbe{cls}"><p>{msg}</p><p><a class="btn primary" href="../index.html#directory">Find a tool you use and rate it</a></p></div>'
    p1=(ol("top",top,TOPN,lambda s:both(bs[s],R[s])) if top else empty("No tools have been rated yet. Be the first to rate one."))+fe
    p2=(ol("reviewed",rev,TOPN,lambda s:f'<span><b>{len(R[s]["reviews"])}</b> <span class="muted">review{"s" if len(R[s]["reviews"])!=1 else ""}</span></span>') if rev else "")+(empty("Very few written reviews so far. Approved reviews show up here.") if len(rev)<10 else "")+fe
    p3=ol("loved",lvall,NL,lambda s:both(bs[s],R.get(s)))+fe
    tz={z[0]:z for z in trend}
    p4=(ol("trending",[z[0] for z in trend],TOPN,lambda s:tstat(tz[s])) if trend else empty("Not enough history yet to show what's trending. This fills in as our daily GitHub snapshots and new ratings build up."))+fe
    json.dump(ranks,open(f"data/lb-ranks/{today}.json","w"),indent=0,sort_keys=True)
    try: when=datetime.datetime.fromisoformat(upd.replace("Z","+00:00")).astimezone(PT).strftime("%b %-d, %Y")
    except Exception: when=""
    mvnote=" Arrows show the change since last week's rank (shown when the filters are off)." if prev else ""
    tabs=[("loved","Most loved",p3,"Rated tools first, weighted toward 4★ until a tool has more ratings (same as the directory's Most loved sort). Tools with no ratings yet follow, ranked by GitHub stars (open-source tools only)."+mvnote),
          ("top","Top rated",p1,f"Average visitor star rating. Tools need at least {MIN_RATED} rating{'s' if MIN_RATED!=1 else ''} to be ranked. Ties go to the tool with more ratings."+mvnote),
          ("reviewed","Most reviewed",p2,"Number of approved written reviews (each one is checked before it goes live)."+mvnote),
          ("trending","Trending this week",p4,(tnote or "Ranked by new ratings, reviews and GitHub stars over the last 7 days.")+mvnote)]
    tb="".join(f'<button type="button" role="tab" id="lbt-{k}" aria-controls="lb-{k}" aria-selected="{"true" if k==DEF else "false"}">{n}</button>' for (k,n,_,_) in tabs)
    pn="".join(f'<section role="tabpanel" id="lb-{k}" aria-labelledby="lbt-{k}"{" hidden" if k!=DEF else ""}><h2>{n}</h2><p class="muted lbh">{h}</p>{p}</section>' for (k,n,p,h) in tabs)
    opts='<option value="">All categories</option>'+"".join(f'<option value="{e(c)}">{e(c)}</option>' for c in cats)
    ctl=(f'<div class="lbctl" id="lbctl" role="group" aria-label="Filter the leaderboard" hidden><label for="lbcat">Category</label><select id="lbcat" class="ucsel">{opts}</select>'
         f'<label class="fchk"><input type="checkbox" id="lbfree"> Free or free plan</label><label class="fchk"><input type="checkbox" id="lbos"> Open source only</label>'
         f'<span class="lbcount muted" id="lbcount" aria-live="polite"></span></div>'
         f'<noscript><p class="muted" style="font-size:13px">Browse rankings for one area on its <a href="../categories/index.html">category page</a>.</p></noscript>')
    css=("<style>.lbtabs{display:flex;gap:6px;flex-wrap:wrap;margin:16px 0 8px}.lbtabs button{font:inherit;font-size:14px;padding:8px 14px;min-height:44px;border-radius:999px;border:1px solid var(--line,rgba(127,127,127,.35));background:transparent;color:inherit;cursor:pointer}"
         ".lbtabs button[aria-selected=true]{background:#4263eb;border-color:#4263eb;color:#fff}.lb h2{font-size:18px;margin:16px 0 4px}.lbh{font-size:13px;margin:0 0 10px}"
         ".lbctl{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;margin:8px 0 4px;font-size:14px}.lbctl select{min-height:44px;max-width:100%;font:inherit;font-size:14px}.lbctl .fchk{display:inline-flex;align-items:center;gap:6px;min-height:44px;cursor:pointer}.lbctl .fchk input{width:20px;height:20px;margin:0}.lbcount{font-size:13px}"
         ".lbctl[hidden],.lbr[hidden],.lbe[hidden]{display:none}"
         ".lbl{list-style:none;padding:0;margin:0}.lbr{display:flex;align-items:center;gap:10px;padding:10px 8px;border-top:1px solid var(--line,rgba(127,127,127,.2));border-radius:8px;min-width:0}"
         ".lb1{background:rgba(245,179,1,.12)}.lb2{background:rgba(160,170,185,.14)}.lb3{background:rgba(205,127,50,.13)}.lbn{flex:0 0 28px;text-align:center;font-weight:700;font-variant-numeric:tabular-nums}"
         ".lb1 .lbn::before{content:'🥇'}.lb2 .lbn::before{content:'🥈'}.lb3 .lbn::before{content:'🥉'}.lb1 .lbn,.lb2 .lbn,.lb3 .lbn{font-size:0}.lb1 .lbn::before,.lb2 .lbn::before,.lb3 .lbn::before{font-size:20px}"
         ".lbt{display:flex;align-items:center;gap:10px;flex:1 1 auto;min-width:0;min-height:44px;color:inherit;text-decoration:none}.lbx{display:flex;flex-direction:column;min-width:0}.lbx b,.lbx span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.lbx span{font-size:12px}.lbx{flex:0 0 clamp(150px,27%,250px)}@media(min-width:641px){.lbs{flex:0 0 auto}.lbs>span{white-space:nowrap}}.lbd{flex:1 1 0;min-width:0;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding:0 8px}@media(max-width:640px){.lbd{display:none}.lbx{max-width:none}}"
         ".lbs{flex:0 1 auto;min-width:0;display:flex;flex-direction:column;align-items:flex-end;gap:2px;font-size:13px;text-align:right}.lbs .rv-stars{font-size:13px}.lbb{display:flex;align-items:center;gap:6px}.lbcs{font-size:12px}"
         ".lbm{font-size:12px;font-weight:700;font-variant-numeric:tabular-nums}.lbm.up{color:#1a9a4b}.lbm.dn{color:#d0453a}.lbm.eq{color:var(--muted,#888)}.lbf-on .lbm{display:none}"
         ".lbrate{flex:0 0 auto;display:inline-flex;align-items:center;justify-content:center;min-height:44px;min-width:44px;padding:0 12px;border-radius:999px;border:1px solid var(--line,rgba(127,127,127,.35));color:inherit;text-decoration:none;font-size:13px;font-weight:600}.lbrate:hover{border-color:#6b8afd;color:#6b8afd}"
         ".lbe{padding:14px;border:1px dashed var(--line,rgba(127,127,127,.4));border-radius:12px;margin:12px 0}.lbe p{margin:0 0 10px}.lbe p:last-child{margin:0}"
         "@media(max-width:480px){.lbr{gap:6px;padding:10px 2px;flex-wrap:wrap}.lbt{flex:1 1 calc(100% - 40px)}.lbs{flex:1 1 auto;flex-direction:row;flex-wrap:wrap;align-items:center;justify-content:flex-start;gap:4px 8px;padding-left:34px;text-align:left;font-size:12px}.lbctl select{flex:1 1 100%}}</style>")
    js=('<script>(function(){var b=document.querySelectorAll(".lbtabs button"),c=document.getElementById("lbctl"),sel=document.getElementById("lbcat"),fr=document.getElementById("lbfree"),os=document.getElementById("lbos"),ct=document.getElementById("lbcount"),cur="'+DEF+'";'
        'function filt(){var v=sel.value,f=fr.checked,o=os.checked,on=!!(v||f||o);document.querySelectorAll(".lb [role=tabpanel]").forEach(function(p){var n=0,cap=p.id==="lb-loved"?'+str(NL)+':'+str(TOPN)+';p.classList.toggle("lbf-on",on);p.querySelectorAll(".lbr").forEach(function(r){var ok=(!v||r.dataset.c===v)&&(!f||r.dataset.f==="1")&&(!o||r.dataset.o==="1");if(!on&&r.hasAttribute("data-x"))ok=false;if(ok&&n>=cap)ok=false;r.hidden=!ok;if(ok){n++;r.querySelector(".lbn").textContent=n;r.classList.remove("lb1","lb2","lb3");if(n<4)r.classList.add("lb"+n)}});var fe=p.querySelector(".lbf");if(fe)fe.hidden=!(on&&n===0&&p.querySelector(".lbr"));p.dataset.n=n});'
        'var cp=document.getElementById("lb-"+cur);ct.textContent=on?(cp.dataset.n+" ranked tool"+(cp.dataset.n==="1"?"":"s")+" shown"):"";try{var q=new URLSearchParams(location.search);v?q.set("cat",v):q.delete("cat");f?q.set("free","1"):q.delete("free");o?q.set("os","1"):q.delete("os");var s=q.toString();history.replaceState(null,"",location.pathname+(s?"?"+s:"")+location.hash)}catch(e){}}'
        'function go(k,push){cur=k;b.forEach(function(x){var on=x.id==="lbt-"+k;x.setAttribute("aria-selected",on);document.getElementById(x.getAttribute("aria-controls")).hidden=!on});if(push)history.replaceState(null,"",location.pathname+location.search+"#"+k);filt()}'
        'b.forEach(function(x){x.addEventListener("click",function(){go(x.id.slice(4),1)})});c.hidden=false;var q=new URLSearchParams(location.search),qc=q.get("cat");if(qc&&[].some.call(sel.options,function(o){return o.value===qc}))sel.value=qc;fr.checked=q.get("free")==="1";os.checked=q.get("os")==="1";'
        '[sel,fr,os].forEach(function(x){x.addEventListener("change",filt)});var h=location.hash.slice(1);go(document.getElementById("lbt-"+h)?h:cur)})();</script>')
    title="AI Agent Tools Leaderboard: Top 100 · AgentScout"  # owner-approved Oct 21 2026
    desc=f"The top 100 AI agent tools, ranked by real visitor ratings, reviews and GitHub stars. Filter by category, free or open source, and rate the tools you use."[:160]
    body=(f'<p class="crumb"><a href="../index.html">AgentScout</a> › Leaderboard</p><div class="lb"><h1>AI Agent Tools Leaderboard: Top&nbsp;{TOPN}</h1>'
          f'<p>Rankings from real visitor ratings and reviews on AgentScout, plus GitHub stars for open-source tools. No paid placements. {nrated} tool{"s" if nrated!=1 else ""} rated and {nrev} written review{"s" if nrev!=1 else ""} so far{f" (updated {when})" if when else ""}. '
          f'Used a tool? Tap <b>Rate</b> next to it. Makers: <a href="badges.html">get your “Ranked on AgentScout” badge</a>.</p>'
          f'<div class="lbtabs" role="tablist" aria-label="Leaderboard rankings" data-pagefind-ignore>{tb}</div>{ctl}<div data-pagefind-ignore>{pn}</div>'
          f'<p class="muted" style="font-size:13px;margin-top:20px">Ratings come from site visitors and are not verified purchases. One rating per tool per visitor; written reviews are checked before they appear. <a href="../privacy.html#reviews">How reviews work</a></p></div>{css}{js}')
    canon=B+"leaderboard/"
    lv=[bs[s] for s in lvall[:NL]]
    items=[{"@type":"ListItem","position":i+1,"url":f'{B}tools/{x["slug"]}.html',"name":x["name"]} for i,x in enumerate(lv[:20])]
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
        {"@type":"ItemList","name":"Most loved AI agent tools","itemListElement":items},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Leaderboard","item":canon}]}]}
    os.makedirs("leaderboard",exist_ok=True)
    open("leaderboard/index.html","w",encoding="utf-8").write(X.shell("../",title,desc,canon,body,ld).replace('<meta property="og:url"',f'<meta name="twitter:title" content="{e(title)}"><meta property="og:url"',1))
    # --- rank badges (Most loved rank, top TOPN). Tools that drop out get a plain "Listed on AgentScout" badge so no SVG goes stale.
    os.makedirs("badges/rank",exist_ok=True); rk={x["slug"]:i+1 for i,x in enumerate(lv[:TOPN])}
    for f in glob.glob("badges/rank/*.svg"):
        s=os.path.basename(f)[:-4]
        if s not in rk: open(f,"w").write(svg(0))
    for s,n in rk.items(): open(f"badges/rank/{s}.svg","w").write(svg(n))
    cp='<button class="btn" type="button" onclick="navigator.clipboard.writeText(this.previousElementSibling.value);this.textContent=\'Copied\'">Copy HTML</button>'
    li=""
    for s,n in rk.items():
        x=bs[s]; snip=f'<a href="{B}tools/{s}.html"><img src="{B}badges/rank/{s}.svg" alt="{x["name"]} is ranked #{n} on AgentScout" height="54"></a>'
        li+=(f'<li class="bdg" id="{e(s)}"><p><b>#{n} {e(x["name"])}</b></p><img src="../badges/rank/{e(s)}.svg" alt="Ranked #{n} on AgentScout badge for {e(x["name"])}" height="54" loading="lazy">'
             f'<label class="sr-only" for="bd-{e(s)}">Badge HTML for {e(x["name"])}</label><textarea id="bd-{e(s)}" readonly rows="3" onclick="this.select()">{e(snip)}</textarea>{cp}</li>')
    bt="Ranked on AgentScout badges for the most loved AI agent tools · AgentScout"; bd="Embeddable “Ranked #N on AgentScout” badges for the top tools on the AgentScout leaderboard. Copy the HTML for your site or README."
    bcss="<style>.bdgl{list-style:none;padding:0;margin:16px 0;display:grid;gap:14px}.bdg{border:1px solid var(--line,rgba(127,127,127,.3));border-radius:12px;padding:14px;min-width:0}.bdg p{margin:0 0 8px}.bdg img{max-width:100%;height:auto;display:block;margin:0 0 8px}.bdg textarea{width:100%;box-sizing:border-box;font:12px ui-monospace,monospace;margin:0 0 8px}.bdg .btn{min-height:44px}</style>"
    bb=(f'<p class="crumb"><a href="../index.html">AgentScout</a> › <a href="./">Leaderboard</a> › Badges</p><h1>“Ranked on AgentScout” badges</h1>'
        f'<p>If your tool is in the top {TOPN} of the <a href="./">Most loved leaderboard</a>, add its badge to your site or README. The badge image updates with every daily build, so it always shows the current rank (and switches to “Listed on AgentScout” if the tool leaves the top {TOPN}). Rank comes from real visitor ratings and GitHub stars only.</p>'
        f'<ol class="bdgl">{li}</ol>{bcss}')
    open("leaderboard/badges.html","w",encoding="utf-8").write(X.shell("../",bt,bd,canon+"badges.html",bb,{"@context":"https://schema.org","@type":"CollectionPage","name":bt,"description":bd,"url":canon+"badges.html"}))
    print(f"leaderboard: {len(top)} top rated, {len(rev)} most reviewed, {len(lvall[:NL])} most loved, {len(trend)} trending ({nrated} rated), prev ranks {prevd if prev else 'none'}, {len(rk)} rank badges")
    return [canon,canon+"badges.html"]
