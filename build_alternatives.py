"""'<Tool> alternatives' pages in best/<slug>-alternatives.html (competitor-research item 4, Oct 18 2026). Called from build_best.pages().
Picks popular tools (featured or most GitHub stars) that have >=8 real peers: same category AND sharing at least one task or sub-task.
Each page: data-driven intro + per-alternative "why consider it" lines (>=150 unique words checked, else skipped), comparison table,
links to written /compare/ pages. The tool page gets one link to its alternatives page (no repeated list). Counts are computed each build."""
import re,os,glob,json,html
import build_extras as X, build_subtasks as S, build_tasks as BT
B=X.B; e=X.e
MAX_PAGES=93; MIN_PEERS=8; SHOW=10; MIN_WORDS=150
SKIP={"cursor","hyperframes"}  # cursor: hand-built page; hyperframes: redirected to its tool page (redirects.json), keep it that way
FORCE_ALTS={"conductor"}  # high-impression Search Console alternatives pages
def live(x): return "iscontinued" not in x.get("maturity","").lower() and "discontinued" not in x.get("description","").lower()[:40]
def peers(x,t,tm,tg):
    mine=tm.get(x["slug"],set()); ms=set(tg.get(x["slug"],[]))
    out=[]
    for y in t:
        if y is x or y["category"]!=x["category"] or not live(y): continue
        st=len(mine&tm.get(y["slug"],set())); ss=len(ms&set(tg.get(y["slug"],[])))
        if st+ss==0: continue
        out.append((st+2*ss,y))
    out.sort(key=lambda z:(-z[0],-(z[1].get("github_stars") or 0),z[1]["name"].lower()))
    return [y for _,y in out]
def lic(x):
    import build_rich
    F=(build_rich.R.get(x["slug"]) or {}).get("facts") or {}
    return re.sub(r" (License|Licence)$","",re.sub(r"^the ","",F.get("license") or ""))
OPEN=S.OPEN|S.SRC
def why(x,y,tg):
    """One data-driven line on what y offers compared with x."""
    bits=[]
    if y["pricing"] in S.OPEN and x["pricing"] not in S.OPEN: bits.append("it is open source, so you can self-host and inspect it")
    elif y["pricing"] in S.FREE and x["pricing"] in S.PAID: bits.append("it lists a free plan")
    elif y["pricing"] in S.PAID and x["pricing"] in S.OPEN: bits.append("it is a managed commercial product, if you'd rather not run it yourself")
    if y["audience"]!=x["audience"]: bits.append("it is "+("ready to use without building anything" if y["audience"]!="builders" else "aimed at developers who want to build on it"))
    extra=[S.LABEL[s] for s in tg.get(y["slug"],[]) if s not in tg.get(x["slug"],[])][:2]
    if extra: bits.append("it also covers "+" and ".join(extra))
    ys,xs=y.get("github_stars"),x.get("github_stars")
    if ys and xs and ys>xs: bits.append(f"it has more GitHub stars ({ys:,} vs {xs:,})")
    elif ys and not xs: bits.append(f"it has a public repo with {ys:,} stars")
    if not bits: bits.append(f"it does the same job with a different approach ({y['pricing'].lower()})")
    return "Consider it because "+"; ".join(bits[:3])+"."
def words(s): return len(re.findall(r"[A-Za-z0-9']+",re.sub(r"<[^>]+>"," ",s)))
def pages(t):
    tm={}; m=BT.mapping(t)
    for s,(T,items) in m.items():
        for y in items: tm.setdefault(y["slug"],set()).add(s)
    tg={x["slug"]:S.tags(x) for x in t}
    global ORD; ORD={k:i for i,k in enumerate(m)}
    cands=sorted([x for x in t if live(x) and x["slug"] not in SKIP],key=lambda x:(not (x.get("featured") or x["slug"] in FORCE_ALTS),-(x.get("github_stars") or 0),x["name"].lower()))
    pairs={X.cslug(a,b) for a,b in X.PAIRS}|{X.cslug(b,a) for a,b in X.PAIRS}
    made=[]; os.makedirs("best",exist_ok=True)
    for x in cands:
        if len(made)>=MAX_PAGES: break
        if not x.get("featured") and not x.get("github_stars") and x["slug"] not in FORCE_ALTS: continue
        ps=peers(x,t,tm,tg)
        if len(ps)<MIN_PEERS: continue
        alts=ps[:SHOW]; n=x["name"]; sl=f"{x['slug']}-alternatives"; path=f"best/{sl}.html"; canon=B+path
        tasks=[m[s][0][1] for s in sorted(tm.get(x["slug"],[]),key=ORD.get)][:3]
        opn=sum(y["pricing"] in S.OPEN for y in ps); fr=sum(y["pricing"] in S.FREE for y in ps)
        intro=(f"{e(n)} is a {e(x['category'])} tool: {e(x['description'])} Pricing, as the maker states it: {e(x.get('pricing_detail') or x['pricing'])}."
               +(f" Its GitHub repo has {x['github_stars']:,} stars." if x.get("github_stars") else "")
               +f" We found {len(ps)} tools in the directory that do overlapping work"+(f" ({e(', '.join(tasks))})" if tasks else "")
               +f"; {opn} of them are open source and {fr} list a free or freemium plan. Below are the {len(alts)} closest, ranked by how many tasks and sub-tasks they share with {e(n)}, then by GitHub stars.")
        lines="".join(f'<li style="margin:0 0 10px"><a href="../tools/{y["slug"]}.html" style="display:inline-flex;align-items:center;gap:8px;vertical-align:middle;max-width:100%">{X.ico(y,"../","sm").replace('width="40" height="40"','width="24" height="24"')}<b>{e(y["name"])}</b></a> ({e(y["pricing"])}): {e(y["description"])} {e(why(x,y,tg))}'
                      +(f' <a href="../compare/{X.cslug(x["slug"],y["slug"]) if X.cslug(x["slug"],y["slug"]) in {X.cslug(a,b) for a,b in X.PAIRS} else X.cslug(y["slug"],x["slug"])}.html">{e(n)} vs {e(y["name"])} →</a>' if X.cslug(x["slug"],y["slug"]) in pairs else "")+'</li>' for y in alts)
        uniq=words(intro)+sum(words(why(x,y,tg)) for y in alts)
        if uniq<MIN_WORDS: continue
        gf=lambda y:", ".join(m[s][0][1] for s in sorted(tm.get(y["slug"],[]),key=ORD.get)[:2]) or y["category"]
        rows="".join(f'<tr><td><a href="../tools/{y["slug"]}.html">{e(y["name"])}</a></td><td>{e(y["pricing"])}</td><td>{e(lic(y)) or ("Yes" if y["pricing"] in S.OPEN else "No")}</td><td>{(format(y["github_stars"],",") if y.get("github_stars") else "—")}</td><td>{e(gf(y))}</td></tr>' for y in [x]+alts)
        table=(f'<h2 style="font-size:18px;margin:28px 0 10px">{e(n)} vs alternatives at a glance</h2><div class="tablewrap"><table class="cmp"><thead><tr><th scope="col">Tool</th><th scope="col">Pricing</th><th scope="col">Open source / licence</th><th scope="col">GitHub stars</th><th scope="col">Good for</th></tr></thead><tbody>{rows}</tbody></table></div>')
        cmpl=[f'<a href="../compare/{c}.html">{e(X_n(t,c))}</a>' for c in sorted({X.cslug(a,b) for a,b in X.PAIRS if x["slug"] in (a,b)})]
        title=f"{n} alternatives (2026): {len(alts)} similar tools · AgentScout"
        if len(title)>70: title=f"{n} alternatives: {len(alts)} similar tools · AgentScout"
        desc=f"The {len(alts)} closest {n} alternatives, including {', '.join(y['name'] for y in alts[:3])}: pricing, open source, GitHub stars and why to switch."[:158]
        body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">Best lists</a> / {e(n)} alternatives</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">{e(n)} alternatives (2026)</h1>'
              f'<p class="lede" style="margin-left:0;text-align:left">{intro}</p> + (f"<p class=\"muted\" style=\"margin:-4px 0 14px;font-size:14px\">Looking for the open-source microservice workflow engine? See <a href=\"../tools/orkes.html\">Orkes Conductor →</a>.</p>" if x["slug"]=="conductor" else "") + f"<ol style="padding-left:20px">{lines}</ol>{table}'
              +(f'<p style="margin-top:20px">Written comparisons: {" · ".join(cmpl)}</p>' if cmpl else "")
              +f'<p style="margin-top:16px">More: <a href="../tools/{x["slug"]}.html">{e(n)} listing</a> · <a href="../categories/{X.catslug(x["category"])}.html">All {e(x["category"])} tools</a> · <a href="index.html#alternatives">All alternatives pages</a></p>'
              f'<p class="disclose">Alternatives are picked from directory data only: same category plus shared tasks and sub-tasks. Pricing is as each maker states it; GitHub stars as recorded on each listing.</p></section>')
        ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":f"{n} alternatives","description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
            {"@type":"ItemList","numberOfItems":len(alts),"itemListElement":[{"@type":"ListItem","position":i+1,"name":y["name"],"url":f"{B}tools/{y['slug']}.html"} for i,y in enumerate(alts)]},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Best lists","item":B+"best/"},{"@type":"ListItem","position":3,"name":f"{n} alternatives","item":canon}]}]}
        open(path,"w").write(X.shell("../",title,desc,canon,body,ld)); made.append((x,sl,len(alts)))
    keep={sl for _,sl,_ in made}
    for f in glob.glob("best/*-alternatives.html"):
        b=os.path.basename(f)[:-5]
        # Never delete a published alternatives page (Oct 20 2026): the word-count gate above flips with data changes, which used to
        # remove pages like best/cognee-alternatives.html that are indexed. Pages not rebuilt this run keep their last good version.
        if b!="cursor-alternatives" and b not in keep: print("alternatives: kept existing (not rebuilt this run):",f)
    # tool page link (one line, no repeated list)
    for x,sl,k in made:
        p=f"tools/{x['slug']}.html"
        if not os.path.exists(p): continue
        s=open(p).read(); s=re.sub(r'<p class="altlink".*?</p>','',s)
        s=re.sub(r'(<h2 style="font-size:16px;margin-bottom:12px">[^<]*alternatives</h2>)',lambda mm:mm.group(1)+f'<p class="altlink" style="margin:-4px 0 12px;font-size:14px"><a href="../best/{sl}.html">Compare {k} {e(x["name"])} alternatives side by side →</a></p>',s,count=1)
        open(p,"w").write(s)
    print("alternatives pages:",len(made))
    return made
def X_n(t,c):
    a,b=c.split("-vs-",1); bs={y["slug"]:y["name"] for y in t}
    return f"{bs.get(a,a)} vs {bs.get(b,b)}"
