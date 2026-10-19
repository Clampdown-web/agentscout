"""Internal links to /s/ (searches), /for/ (roles) and free-tools/ across the site (Oct 18 2026).
Runs last in build_site.py. Every block sits between <!--xl:NAME--> markers, so each build replaces it in place
(idempotent) and static pages (index.html, submit.html, ...) keep it too. Links come only from page membership:
a tool links to the search/role pages that actually list it."""
import re,os,glob,json,collections
import build_extras as X, build_landing as L, build_free_tools as F, build_best as BB
B=X.B; e=X.e
CAP=lambda s:s[:1].upper()+s[1:]
H2='style="font-size:16px;margin:0 0 10px"'
stats=collections.Counter(); miss=collections.Counter()
def put(s,name,html,anchor,before=True,regex=False):
    s=re.sub(r'<!--xl:%s-->.*?<!--/xl:%s-->'%(name,name),'',s,flags=re.S)
    if not html: return s
    blk=f'<!--xl:{name}-->{html}<!--/xl:{name}-->'
    if regex:
        m=re.search(anchor,s,re.S)
        if not m: miss[name]+=1; return s
        i=m.start() if before else m.end()
    else:
        i=s.find(anchor)
        if i<0: miss[name]+=1; return s
        if not before: i+=len(anchor)
    stats[name]+=1
    return s[:i]+blk+s[i:]
def edit(path,fn):
    if not os.path.exists(path): miss[path]+=1; return
    s=open(path).read(); o=s; s=fn(s)
    if s!=o: open(path,"w").write(s)
def chips(items): return '<div class="badges">'+"".join(f'<a class="b uc" href="{h}">{e(t)}</a>' for h,t in items)+'</div>'
COST_CAT={"models & local runtimes","frameworks"}
COST_RX=re.compile(r"\bLLMs?\b|\binference\b|model (API|gateway|router|provider)|\bgateway\b|\brouter\b|\btokens?\b|\bmodel APIs?\b",re.I)
def cost_tool(x): return x["category"] in COST_CAT or (x["category"] in ("MCP & infra","evals & observability") and bool(COST_RX.search(x["description"]))) or bool(re.search(r"\bLLM API|\bmodel API|inference API",x["description"],re.I))
def cost_pair(a,b):
    f=lambda x:x["category"] in {"coding","models & local runtimes","frameworks"} or bool(re.search(r"\bAPI\b",x["description"])) or cost_tool(x)
    return f(a) or f(b)
# small categories with no list overlap: hand-picked, directly relevant pages
MANUAL={"models & local runtimes":([],["ai-engineers"]),"games":([],["game-developers"])}
def run(t):
    S=L.DATA["search"]; RO=L.DATA["roles"]; bys={x["slug"]:x for x in t}
    sname={a[0]:a[1] for a in S}; rname={r[0]:r[1] for r in RO}
    spos=collections.defaultdict(list); rpos=collections.defaultdict(list)
    for a in S:
        for i,x in enumerate(a[4]): spos[x["slug"]].append((i,len(a[4]),a[0]))
    for r in RO:
        for i,sl in enumerate(r[4]): rpos[sl].append((i,r[0]))
    rtasks={r[0]:r[3] for r in RO}
    BEST={}
    for f in glob.glob("best/*.html"):
        k=os.path.basename(f)[:-5]
        if k=="index": continue
        h=open(f).read(); m=re.search(r"<h1[^>]*>(.*?)</h1>",h,re.S)
        if 'name="robots" content="noindex' in h: continue  # Moved stubs (redirects.json)
        BEST[k]=(re.sub(r"<[^>]+>","",m.group(1)).replace(" (2026)","").strip() if m else k,[y for y in re.findall(r'href="\.\./tools/([^"]+)\.html"',h.split("<main",1)[-1])])
    # alternatives pages (best/*-alternatives.html) and sub-task pages (3-level crumb) with the tools they list
    ALTP={k:v for k,v in BEST.items() if k.endswith("-alternatives")}
    SUB={}
    for f in glob.glob("tasks/*.html"):
        h=open(f).read()
        if 'name="robots" content="noindex' in h: continue
        cm=re.search(r'<div class="crumb">(.*?)</div>',h,re.S)
        if not cm or cm.group(1).count("</a>")<3: continue
        m=re.search(r"<h1[^>]*>(.*?)</h1>",h,re.S); nm=re.sub(r"<[^>]+>","",m.group(1)).replace("AI tools for ","").strip() if m else f
        SUB[os.path.basename(f)[:-5]]=(nm[:1].upper()+nm[1:],re.findall(r'href="\.\./tools/([^"]+)\.html"',h.split("<main",1)[-1]))
    altin=collections.Counter(); subin=collections.Counter()
    def best_for(slugs,n=2,mn=3):
        sl=set(slugs); sc=sorted(((len(sl&set(v[1])),k) for k,v in BEST.items()),reverse=True)
        return [k for c,k in sc if c>=mn][:n]
    def blink(k,d="../"): return f'<a href="{d}best/{k}.html">{e(BEST[k][0])}</a>'
    # (1) tool pages
    for x in t:
        p=f"tools/{x['slug']}.html"
        ss=[k for _,_,k in sorted(spos.get(x["slug"],[]))][:4]; rr=[k for _,k in sorted(rpos.get(x["slug"],[]))][:2]
        c=cost_tool(x); html=""
        inb=[k for k,v in BEST.items() if x["slug"] in v[1]][:2]
        catb=[k for k,v in BEST.items() if sum(1 for y in v[1] if bys.get(y,{}).get("category")==x["category"])*2>=max(1,len(v[1]))][:1]
        bl=("Ranked in: "+" · ".join(blink(k) for k in inb)) if inb else ("See also: "+blink(catb[0])+" · " if catb else "")+'<a href="../best/index.html">All best-of lists</a>'
        if inb: stats["tool_ranked_in"]+=1
        # alternatives pages and sub-task guides that list this tool (least-linked first, so every page gets inbound links)
        al=sorted([k for k,v in ALTP.items() if x["slug"] in v[1] and k!=x["slug"]+"-alternatives"],key=lambda k:(altin[k],k))[:3]
        for k in al: altin[k]+=1
        sb=sorted([k for k,v in SUB.items() if x["slug"] in v[1]],key=lambda k:(subin[k],k))[:3]
        for k in sb: subin[k]+=1
        extra=(f'<p style="margin:10px 0 0;font-size:14px">🔁 Listed in: '+" · ".join(blink(k) for k in al)+'</p>' if al else "")+(f'<p style="margin:10px 0 0;font-size:14px">🧭 Task guides: '+" · ".join(f'<a href="../tasks/{k}.html">{e(SUB[k][0])}</a>' for k in sb)+'</p>' if sb else "")
        if al: stats["tool_alt_links"]+=len(al)
        if sb: stats["tool_subtask_links"]+=len(sb)
        if True:
            it=[(f"../s/{k}.html",sname[k]) for k in ss]+[(f"../for/{k}.html","For "+rname[k]) for k in rr]
            html=((f'<h2 {H2}>Popular searches with this tool</h2>'+chips(it)) if it else f'<h2 {H2}>Related lists</h2>')+(
                  f'<p style="margin:10px 0 0;font-size:14px">🏆 {bl}</p>'+
                  extra+(f'<p style="margin:10px 0 0;font-size:14px">💲 <a href="../free-tools/ai-cost-calculator.html">Estimate API cost</a>: compare per-request and monthly costs for GPT, Claude, Gemini and Grok models.</p>' if c else ""))
            html=f'<div style="margin:0 0 32px">{html}</div>'
            if ss or rr: stats["tool_with_search_or_role"]+=1
            if c: stats["tool_cost_link"]+=1
        edit(p,lambda s,html=html:put(s,"tool",html,'<h2 style="font-size:16px;margin:36px 0 6px">Badge for makers</h2>'))
    # (3) category pages + hub
    cats=sorted({x["category"] for x in t})
    for c in cats:
        cs=X.catslug(c)
        n_=lambda a:sum(1 for y in a[4] if y["category"]==c)
        rs=[a for a in S if n_(a)*10>=len(a[4])*3 or n_(a)>=5]+[a for a in S if a[0] in MANUAL.get(c,([],[]))[0]]
        rs=sorted(rs,key=lambda a:-sum(1 for y in a[4] if y["category"]==c))[:6]
        ro=[(sum(1 for sl in r[4] if bys.get(sl,{}).get("category")==c),r) for r in RO]; ro=sorted(ro,key=lambda z:-z[0]/max(1,len(z[1][4]))); ro=([r for n,r in ro if n>=3 and n*100>=len(r[4])*15] or [r for n,r in ro[:1] if n>=2])[:4]
        ro+=[r for r in RO if r[0] in MANUAL.get(c,([],[]))[1] and r not in ro]
        html=""
        if rs: html+=f'<h2 style="font-size:16px;margin:28px 0 10px">Related searches</h2>'+chips([(f"../s/{a[0]}.html",a[1]) for a in rs])
        if ro: html+=f'<h2 style="font-size:16px;margin:24px 0 10px">Who uses these</h2>'+chips([(f"../for/{r[0]}.html","For "+r[1]) for r in ro])
        cb=sorted([k for k,v in BEST.items() if v[1] and sum(1 for y in v[1] if bys.get(y,{}).get("category")==c)*2>=len(v[1])],key=lambda k:-len(BEST[k][1]))[:3]
        html+=f'<h2 style="font-size:16px;margin:24px 0 10px">Best-of lists</h2>'+chips([(f"../best/{k}.html",BEST[k][0]) for k in cb]+[("../best/index.html","All best-of lists")])
        ca=sorted([k for k in ALTP if bys.get(k[:-13],{}).get("category")==c],key=lambda k:-(bys[k[:-13]].get("github_stars") or 0))[:8]
        if ca: html+=f'<h2 style="font-size:16px;margin:24px 0 10px">Alternatives pages</h2>'+chips([(f"../best/{k}.html",BEST[k][0]) for k in ca]); stats["cat_alt"]+=len(ca)
        cg=sorted([k for k,v in SUB.items() if v[1] and sum(1 for y in v[1] if bys.get(y,{}).get("category")==c)*10>=len(v[1])*4],key=lambda k:-len(SUB[k][1]))[:6]
        if cg: html+=f'<h2 style="font-size:16px;margin:24px 0 10px">Task guides</h2>'+chips([(f"../tasks/{k}.html",SUB[k][0]) for k in cg]); stats["cat_subtask"]+=len(cg)
        if html: stats["cat_rel_s"]+=len(rs); stats["cat_rel_for"]+=len(ro); stats["cat_best"]+=len(cb)
        edit(f"categories/{cs}.html",lambda s,html=html:put(s,"cat",html,'<p class="disclose">'))
    edit("categories/index.html",lambda s:put(s,"cathub",' Or browse <a href="../for/index.html">by role</a>, <a href="../s/">popular searches</a> or <a href="../best/index.html">best-of lists</a>.',r'<p class="lede"[^>]*>[^<]*(?=</p>)',before=False,regex=True))
    # (5) task pages
    for f in glob.glob("tasks/*.html"):
        k=os.path.basename(f)[:-5]
        if k=="index": continue
        ro=[r for r in RO if k in r[3]][:3]; sr=[a for a in S if a[6]==k][:3]
        html=""
        if ro or sr:
            html='<p style="margin:24px 0 0">'+("Popular with: "+" · ".join(f'<a href="../for/{r[0]}.html">{e(CAP(r[1]))}</a>' for r in ro) if ro else "")+(" · " if ro and sr else "")+("Related searches: "+" · ".join(f'<a href="../s/{a[0]}.html">{e(a[1])}</a>' for a in sr) if sr else "")+'</p>'
            stats["task_lines"]+=1
        edit(f,lambda s,html=html:put(s,"task",html,'<p class="disclose">Tools are matched to tasks'))
    # (6) compare pages + hub
    for a,b in X.PAIRS:
        A,Bt=bys[a],bys[b]; f=f"compare/{X.cslug(a,b)}.html"
        both=[z for z in S if {a,b}<= {y["slug"] for y in z[4]}]
        one=sorted([z for z in S if a in {y["slug"] for y in z[4]} or b in {y["slug"] for y in z[4]}],key=lambda z:min([i for i,y in enumerate(z[4]) if y["slug"] in (a,b)]))
        sr=(both or one)[:1]; parts=[]
        if cost_pair(A,Bt): parts.append('<a href="../free-tools/ai-cost-calculator.html">Compare running costs</a> of the AI models behind them with our free cost calculator'); stats["compare_cost"]+=1
        if sr: parts.append(f'Related search: <a href="../s/{sr[0][0]}.html">{e(sr[0][1])}</a>'); stats["compare_search"]+=1
        html=('<p style="margin-top:12px">'+" · ".join(parts)+'</p>') if parts else ""
        edit(f,lambda s,html=html:put(s,"cmp",html,r'<p style="margin-top:20px">Related: .*?</p>',before=False,regex=True))
    edit("compare/index.html",lambda s:put(s,"cmphub",'<p style="margin:0 0 18px">Comparing AI coding agents or model APIs? <a href="../free-tools/ai-cost-calculator.html">Compare running costs</a> across GPT, Claude, Gemini and Grok models, or browse <a href="../s/">popular searches</a>.</p>','using only facts from our listings.</p>',before=False))
    # (7) best pages
    for f in glob.glob("best/*.html"):
        k=os.path.basename(f)[:-5]
        if k=="index": continue
        rs=[a for a in S if a[7]==k]
        if len(rs)<4:
            s0=open(f).read(); listed=set(re.findall(r'href="\.\./tools/([^"]+)\.html"',s0))
            more=sorted([a for a in S if a not in rs and len(listed&{y["slug"] for y in a[4]})>=5],key=lambda a:-len(listed&{y["slug"] for y in a[4]}))
            rs+=more[:4-len(rs)]
        html=('<p style="margin-top:12px">Related searches: '+" · ".join(f'<a href="../s/{a[0]}.html">{e(a[1])}</a>' for a in rs[:4])+'</p>') if rs else ""
        if html: stats["best_lines"]+=1
        def fn(s,html=html):
            if re.search(r'<p style="margin-top:24px">Related: .*?</p>',s,re.S): return put(s,"best",html,r'<p style="margin-top:24px">Related: .*?</p>',before=False,regex=True)
            return put(s,"best",html,r'<p class="disclose">|</section></main>',regex=True)
        edit(f,fn)
    # (A) best-of links on search, role and free-tool pages
    for a in S:
        f=f"s/{a[0]}.html"; bb=[a[7]] if a[7] in BEST else best_for([y["slug"] for y in a[4]],1)
        html=f'<p>Best-of lists: '+" · ".join([blink(k) for k in bb]+['<a href="../best/index.html">All best lists</a>'])+'</p>'
        if not a[7] or a[7] not in BEST: edit(f,lambda s,html=html:put(s,"sbest",html,'<p class="disclose">'))
    for r in RO:
        bb=best_for(r[4],2,2)
        html=f'<p>Best-of lists for {e(r[1])}: '+" · ".join([blink(k) for k in bb]+['<a href="../best/index.html">All best lists</a>'])+'</p>'
        stats["role_best"]+=len(bb); edit(f"for/{r[0]}.html",lambda s,html=html:put(s,"rbest",html,'<p class="disclose">'))
    def catline(slugs,d="../"):
        cc=collections.Counter(bys[y]["category"] for y in slugs if y in bys)
        top=[(c,n) for c,n in cc.most_common() if n>=3 or n*5>=max(1,len(slugs))][:5]
        return ('<p>Related categories: '+" · ".join(f'<a href="{d}categories/{X.catslug(c)}.html">{e(CAP(c))}</a>' for c,n in top)+'</p>') if top else ""
    for a in S:
        edit(f"s/{a[0]}.html",lambda s,html=catline([y["slug"] for y in a[4]]):put(s,"scat",html,'<p class="disclose">')); stats["s_catline"]+=1
    for r in RO:
        edit(f"for/{r[0]}.html",lambda s,html=catline(r[4]):put(s,"rcat",html,'<p class="disclose">')); stats["role_catline"]+=1
    FB={"ai-cost-calculator":["ai-agent-frameworks","ai-coding-agents"],"token-counter":["ai-agent-frameworks","ai-agent-observability-tools"],"prompt-builder":["ai-productivity-tools","personal-ai-agents"],"agent-setup-generator":["ai-coding-agents","ai-agent-frameworks"]}
    for k,v in FB.items():
        html='<p>Best-of lists: '+" · ".join([blink(b) for b in v if b in BEST]+['<a href="../best/index.html">All best lists</a>'])+'</p>'
        edit(f"free-tools/{k}.html",lambda s,html=html:put(s,"ftbest",html,'<p>More free tools from AgentScout:'))
    edit("free-tools.html",lambda s:put(s,"fthubbest",'<p style="font-size:14px;margin:6px 0 0">Ranked picks: <a href="best/free-ai-agents.html">Best free AI agents</a> · <a href="best/self-hosted-ai-agents.html">Best self-hosted AI agents</a> · <a href="best/most-starred-open-source-ai-agents.html">Most-starred open-source projects</a> · <a href="best/index.html">All best lists</a></p>','<h2 style="font-size:18px;margin:24px 0 4px">Featured: free from AgentScout</h2>'))
    # (8) free-tools.html
    edit("free-tools.html",lambda s:put(s,"ftroles",'<p style="font-size:14px;margin:6px 0 0">Free tools by role: '+" · ".join(f'<a href="for/{r[0]}.html">{e(CAP(r[1]))}</a>' for r in RO)+'</p>','<h2 style="font-size:18px;margin:24px 0 4px">Featured: free from AgentScout</h2>'))
    # (9) static pages
    edit("submit.html",lambda s:put(s,"submit",'<p style="margin:0 0 16px;font-size:14.5px"><b>Prepare your listing:</b> describe what your agent does in a sentence or two. Our free <a href="free-tools/agent-setup-generator.html">agent setup generator</a> can draft a clear system prompt and starter config to share with users.</p>','<form id="sf"'))
    ft=" · ".join(f'<a href="free-tools/{s}.html">{e(n)}</a>' for s,n,_,_ in F.TOOLS)
    edit("generate.html",lambda s:put(s,"gen",f'<p style="margin:18px 0 0">More free tools: {ft} · <a href="free-tools.html">All free tools</a></p>','</section></main>'))
    line=f'<p style="margin:18px 0 0;font-size:14px">Free tools: {ft} · Popular searches: <a href="s/free-ai-coding-agents.html">Free AI coding agents</a> · <a href="s/open-source-browser-agents.html">Open-source browser agents</a> · <a href="s/">All searches</a></p>'
    edit("news.html",lambda s:put(s,"news",line,'</section></main>'))
    edit("newsletter.html",lambda s:put(s,"nl",line,'</section></main>'))
    # (4) homepage
    def home(s):
        strip=(f'<section id="xfree" class="band" aria-labelledby="xfree-h"><div class="wrap"><div class="sh"><div><h2 id="xfree-h">Free AI tools</h2><p>Calculators and generators that run in your browser. No sign-up. <a href="free-tools.html">All free tools →</a></p></div></div>'
               f'<div class="grid fill">{F.hub_cards("")}{F.see_all_card("")}</div></div></section>')
        s=put(s,"homefree",strip,'<div class="layout">')
        role=(f'<section id="xroles" class="band" aria-labelledby="xroles-h"><div class="wrap"><div class="sh"><div><h2 id="xroles-h">Browse by role</h2><p>AI agent tools picked for the work you do. <a href="for/index.html">All roles →</a></p></div></div>'
              +chips([(f"for/{r[0]}.html",CAP(r[1])) for r in RO])+'</div></section>')
        cc=collections.Counter(x["category"] for x in t)
        cats_=(f'<section id="xcats" class="band" aria-labelledby="xcats-h"><div class="wrap"><div class="sh"><div><h2 id="xcats-h">All categories</h2><p>Every AI agent tool category, with its own page. <a href="categories/index.html">All categories →</a></p></div></div>'
              +chips([(f"categories/{X.catslug(c)}.html",f"{CAP(c)} ({n})") for c,n in cc.most_common()])+'</div></section>')
        role=cats_+role
        s=put(s,"homeroles",role,r'<div class="cats" id="catgrid"></div>\s*</div></section>',before=False,regex=True)
        s=put(s,"homeguide",' · <a href="s/">Popular searches</a> · <a href="for/index.html">By role</a>',r'<h3>Browse by guide</h3><p>.*?(?=</p>)',before=False,regex=True)
        return s
    edit("index.html",home)
    print("internal links:",dict(stats),"missing anchors:",dict(miss) or "none")
