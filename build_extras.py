"""Badges section, comparison pages, badges page and sitemap. Called from build_site.py."""
import html,json,re,datetime
import atexit as _ax0
def _pf_last():
    import sys as _s
    if _s.argv and 'scripts/' in _s.argv[0]: return  # check/helper scripts: the build itself reindexes at exit
    import build_search; build_search.run()
_ax0.register(_pf_last)  # site search index, runs after every other exit hook (Oct 21 2026)
_cap=lambda s:str(s)[:1].upper()+str(s)[1:]  # keeps acronyms (RAG, MCP, SQL, QA) intact
B="https://agentscouthq.com/"
e=lambda s:html.escape(str(s or ""))
def su(u):
    u=str(u or "").strip()
    return u if re.match(r"(?i)^https?://",u) else "#"

# Standard outbound tracking on tool-page Visit buttons (owner-approved Oct 20 2026). Official-site links and JSON-LD stay clean.
# Per-tool opt-out: tools.json "no_utm": true (for sites that break on query params).
UTM="utm_source=agentscouthq&utm_medium=referral&utm_campaign=directory"
def utm(u,x=None):
    u=su(u)
    if u=="#" or (x and x.get("no_utm")) or re.search(r"(?i)[?&]utm_[a-z]+=",u): return u
    base,hsh,frag=u.partition("#")
    if re.match(r"(?i)^https?://[^/?]+$",base): base+="/"
    sep="" if base.endswith(("?","&")) else ("&" if "?" in base else "?")
    return base+sep+UTM+hsh+frag
PAIRS=[("claude-code","openai-codex-cli"),("cursor","windsurf"),("cline","roo-code"),("langgraph","crewai"),("crewai","autogen"),
("browser-use","stagehand"),("exa","tavily"),("livekit-agents","pipecat"),("vapi","retell-ai"),("n8n","make"),("dify","flowise"),
("langfuse","langsmith"),("e2b","modal"),("bolt","v0")]
NEW=json.load(open("compare_new.json")); NEW.pop("_note",None)  # Oct 18 batch: recommendation copy, keyed by slug
PAIRS+=[tuple(k.split("-vs-")) for k in NEW]
# Logo <img> error handler (Oct 18 2026 logo fix): retry twice (1.5 s, 3 s) with a cache-busting query before
# falling back to the letter, so a transient GitHub Pages 503/404 (e.g. during a deploy) no longer drops logos for good.
ONERR='onerror="'+"var i=this,n=+(i.dataset.r||0);if(n<2){i.dataset.r=n+1;setTimeout(function(){i.src=i.src.split('?')[0]+'?r='+(n+1)},1500*(n+1))}else i.remove()"+'"'
def wordmark(d=""):
    """AgentScout wordmark inline in a heading or sentence (same logo-wordmark.svg as the site header, so it is already cached
    and follows the theme). alt="AgentScout" keeps the text reading "... built by AgentScout". Sized/aligned in styles.css (.aswm)."""
    return f'<span class="sr-only">AgentScout</span><img class="aswm" src="{d}logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32">'
BUILT_BY=lambda d="": f'Free AI tools built by {wordmark(d)}'
def ico(x,d="../",cls=""):
    L=e(x["name"].strip()[:1].upper()); im=f'<img src="{d}{x["logo"]}" alt="{e(x["name"])} logo" width="40" height="40" loading="lazy" decoding="async" {ONERR}>' if x.get("logo") else ""
    if cls=="lg": im=im.replace('width="40" height="40" loading="lazy"','width="56" height="56" fetchpriority="high"')  # tool-page header logo is above the fold: load it right away
    return f'<span class="ico {cls}"><span aria-hidden="true" data-l="{L}"></span>{im}</span>'  # letter drawn by CSS (::before), so it never joins the name in copied or extracted text
def ico24(x): return ico(x,"","sm").replace('width="40" height="40"','width="24" height="24"')
def cslug(a,b): return f"{a}-vs-{b}"
def badge_html(x,depth="../"):
    url=f"{B}tools/{x['slug']}.html"; kind="featured" if x.get("featured") else "listed"; lab=kind.title()
    out=""
    for th in ["light","dark"]:
        img=f"{B}badges/{kind}-{th}.svg"
        h=f'<a href="{url}" target="_blank" rel="noopener noreferrer"><img src="{img}" alt="{lab} on AgentScout" width="220" height="54"></a>'
        m=f"[![{lab} on AgentScout]({img})]({url})"
        out+=f'<div class="embed"><img src="{depth}badges/{kind}-{th}.svg" alt="{lab} on AgentScout ({th})" width="220" height="54"><label>HTML</label><textarea readonly rows="3" aria-label="HTML badge code" onclick="this.select()">{e(h)}</textarea><button class="btn" type="button" onclick="navigator.clipboard.writeText(this.previousElementSibling.value);this.textContent=\'Copied\'">Copy HTML</button><label>Markdown</label><textarea readonly rows="2" aria-label="Markdown badge code" onclick="this.select()">{e(m)}</textarea><button class="btn" type="button" onclick="navigator.clipboard.writeText(this.previousElementSibling.value);this.textContent=\'Copied\'">Copy Markdown</button></div>'
    return f'<h2 style="font-size:16px;margin:36px 0 6px">Badge for makers</h2><p class="muted" style="margin:0 0 14px">Built {e(x["name"])}? Add this badge to your README or site. It links back to this page. <a href="../badges.html">About badges</a></p><div class="embeds">{out}</div>'
def featured_generic():
    out=""
    for th in ["light","dark"]:
        img=f"{B}badges/featured-{th}.svg"
        h=f'<a href="{B}" target="_blank" rel="noopener noreferrer"><img src="{img}" alt="Featured on AgentScout" width="220" height="54"></a>'
        m=f"[![Featured on AgentScout]({img})]({B})"
        cp=lambda kind:f'<button class="btn" type="button" onclick="navigator.clipboard.writeText(this.previousElementSibling.value);this.textContent=\'Copied\'">Copy {kind}</button>'
        out+=f'<div class="embed"><img src="badges/featured-{th}.svg" alt="Featured on AgentScout ({th})" width="220" height="54"><label>HTML ({th})</label><textarea readonly rows="3" aria-label="HTML ({th}) badge code" onclick="this.select()">{e(h)}</textarea>{cp("HTML")}<label>Markdown ({th})</label><textarea readonly rows="2" aria-label="Markdown ({th}) badge code" onclick="this.select()">{e(m)}</textarea>{cp("Markdown")}</div>'
    return f'<h2 id="featured-badge" style="font-size:18px;margin:32px 0 8px">Featured on AgentScout badge</h2><p style="margin:0 0 14px">Copy a ready-made snippet. It links to the AgentScout homepage.</p><div class="embeds">{out}</div>'
def cmp_links(x,t):
    ps=[(a,b) for a,b in PAIRS if x["slug"] in (a,b)]
    if not ps: return ""
    bs={y["slug"]:y for y in t}
    li="".join(f'<a class="b uc" href="../compare/{cslug(a,b)}.html">{e(bs[a]["name"])} vs {e(bs[b]["name"])}</a>' for a,b in ps)
    return f'<h2 style="font-size:16px;margin:0 0 10px">Compare</h2><div class="badges" style="margin-bottom:32px">{li}</div>'
def shell(depth,title,desc,canon,body,ld):
    tpl=open("data/detail.tpl").read()
    head=tpl.split("<title>")[0].replace("../",depth)
    foot="<footer"+tpl.split("<footer",1)[1].replace("../",depth)
    nav=tpl.split("</head>",1)[1].split("<main")[0].replace("../",depth)
    return f'''{head}<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="article"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canon}">
<script type="application/ld+json">{json.dumps(ld,ensure_ascii=False).replace("</","<\\/")}</script>
</head>{nav}<main class="wrap">{body}</main>
{foot}'''
def facts(x):
    f=[("Description",x["description"]),("Category",x["category"]),("Audience","For builders" if x["audience"]=="builders" else "Ready to use"),
       ("Pricing (as stated)",(x.get("pricing_detail") or x["pricing"])),("Maturity",x["maturity"]),
       ("GitHub stars",f'{x["github_stars"]:,}' if x.get("github_stars") is not None else "Not tracked"),("Use cases",", ".join(x["use_cases"])),("Link checked",x["verified"])]
    return f
def build(t):
    bs={y["slug"]:y for y in t}; today=datetime.datetime.now(datetime.timezone.utc).date().isoformat(); urls=[]
    for a,b in PAIRS:
        A,Bt=bs[a],bs[b]; s=cslug(a,b); canon=f"{B}compare/{s}.html"
        title=f"{A['name']} vs {Bt['name']}: side-by-side comparison · AgentScout"
        desc=f"{A['name']} vs {Bt['name']} compared: pricing as stated by the makers, audience, maturity and use cases. {A['description']}"[:158]
        h1=f"{A['name']} vs {Bt['name']}"; faq=[]
        if s=="claude-code-vs-openai-codex-cli":
            h1="Codex vs Claude Code (2026)"; title="Codex vs Claude Code (2026): OpenAI Codex CLI vs Claude Code compared · AgentScout"
            desc="Codex vs Claude Code in 2026: OpenAI's open-source Codex CLI vs Anthropic's Claude Code, compared on pricing as stated, audience and maturity."
            faq=[("What is the difference between Codex and Claude Code?",f"Claude Code is {A['description'][0].lower()+A['description'][1:]} OpenAI Codex CLI is {Bt['description'][0].lower()+Bt['description'][1:]}"),
                 ("Is Codex CLI open source?",f"Yes. Our listing for OpenAI Codex CLI states its pricing as: {Bt['pricing_detail']}."),
                 ("How much does Claude Code cost?",f"As Anthropic states it: {A['pricing_detail']}. Check the official site for current plans."),
                 ("Which one should I choose?","We don't benchmark or rank them. Both are mature terminal coding agents aimed at builders; compare pricing and try each on your own repo.")]
        if s=="n8n-vs-make":
            h1="n8n vs Make (2026)"; title="n8n vs Make (2026): pricing, self-hosting and features compared · AgentScout"
            desc="n8n vs Make in 2026: pricing as each maker states it (n8n: self-host free, paid cloud; Make: free tier + paid plans), plus audience and maturity."
            faq=[("How much does n8n cost?",f"As n8n states it: {A['pricing_detail']}. Check n8n's official pricing page for current cloud plans."),
                 ("Does Make have a free plan?",f"As Make states it: {Bt['pricing_detail']}. Check Make's official pricing page for current limits."),
                 ("Can I self-host n8n or Make?","Our n8n listing says it can be self-hosted or used in the cloud. Our Make listing describes it as a visual automation platform and doesn't list a self-host option.")]
        N=NEW.get(s)
        if N:
            import build_rich; RA,RB=build_rich.R.get(a,{}),build_rich.R.get(b,{})
            h1=f"{A['name']} vs {Bt['name']}: Which AI Agent Is Better in 2026?"; title=f"{h1} · AgentScout"
            desc=f"{A['name']} vs {Bt['name']} (2026): pricing, open source, GitHub stars, key features and who each is best for, from AgentScout's verified listings."[:160]
            def osl(x): return "Yes" if "open source" in (x.get("pricing_detail") or x["pricing"]).lower() else ("Public GitHub repo listed" if x.get("github") else "Not listed as open source")
            def kf(x,R): return "; ".join(R["features"][:3]) if R.get("features") else x["description"]
            def pr(x,R):
                P=R.get("pricing") or {}
                return ", ".join(f"{n} {p}" for n,p,_ in P["tiers"])+(f". {P['trial']}" if P.get("trial") else "") if P.get("tiers") else ""
            faq=[(f"What is the difference between {A['name']} and {Bt['name']}?",f"{A['name']}: {A['description']} {Bt['name']}: {Bt['description']}"),
                 (f"Is {A['name']} or {Bt['name']} open source?",f"{A['name']}: {osl(A)}. {Bt['name']}: {osl(Bt)}. Pricing as each maker states it: {A['name']}, {A.get('pricing_detail') or A['pricing']}; {Bt['name']}, {Bt.get('pricing_detail') or Bt['pricing']}."),
                 (f"Should I choose {A['name']} or {Bt['name']}?",f"Choose {A['name']} if {N['choose'][0]} Choose {Bt['name']} if {N['choose'][1]}")]
        faqh="".join(f"<h3 style=\"font-size:15px;margin:18px 0 4px\">{e(q)}</h3><p style=\"margin:0\">{e(a_)}</p>" for q,a_ in faq)
        faqh=f'<h2 style="font-size:18px;margin:32px 0 4px">FAQ</h2>{faqh}' if faq else ""
        rel=f'<p style="margin-top:20px">Related: <a href="../tools/{a}.html">{e(A["name"])}</a> · <a href="../tools/{b}.html">{e(Bt["name"])}</a> · <a href="../categories/{catslug(A["category"])}.html">More {e(A["category"])} tools</a> · <a href="../categories/mcp-servers.html">MCP servers</a></p>'

        fa,fb=facts(A),facts(Bt)
        if N:
            fa=[(k,(v or A["pricing"]) if k.startswith("Pricing") else v) for k,v in fa]; fb=[(k,(v or Bt["pricing"]) if k.startswith("Pricing") else v) for k,v in fb]
            def pm(x,R): return "Paid plans with a free trial" if (R.get("pricing") or {}).get("free") is False and R["pricing"].get("trial") else x["pricing"]
            fa=[(k,pm(A,RA) if k.startswith("Pricing") and v==A["pricing"] else v) for k,v in fa]; fb=[(k,pm(Bt,RB) if k.startswith("Pricing") and v==Bt["pricing"] else v) for k,v in fb]
            ex=[("Pricing model",pm(A,RA),pm(Bt,RB)),("Open source",osl(A),osl(Bt))]
            if pr(A,RA) or pr(Bt,RB): ex.append(("Plans (official pricing page)",pr(A,RA) or "Not listed",pr(Bt,RB) or "Not listed"))
            ex+=[("Key features",kf(A,RA),kf(Bt,RB)),("Best for",N["best"][0],N["best"][1])]
            fa=fa[:1]+[(k,va) for k,va,_ in ex]+fa[1:]; fb=fb[:1]+[(k,vb) for k,_,vb in ex]+fb[1:]
            rel=f'<p style="margin-top:20px">Related: <a href="../tools/{a}.html">{e(A["name"])}</a> · <a href="../tools/{b}.html">{e(Bt["name"])}</a> · '+" · ".join(f'<a href="../categories/{catslug(c)}.html">More {e(c)} tools</a>' for c in dict.fromkeys([A["category"],Bt["category"]]))+' · <a href="../categories/mcp-servers.html">MCP servers</a></p>'
            faqh=f'<h2 style="font-size:18px;margin:32px 0 8px">Our recommendation</h2><p style="margin:0 0 8px"><b>Choose <a href="../tools/{a}.html">{e(A["name"])}</a> if</b> {e(N["choose"][0])}</p><p style="margin:0"><b>Choose <a href="../tools/{b}.html">{e(Bt["name"])}</a> if</b> {e(N["choose"][1])}</p>'+faqh
        rows="".join(f"<tr><th>{e(k)}</th><td>{e(va)}</td><td>{e(vb)}</td></tr>" for (k,va),(_,vb) in zip(fa,fb))
        shared=sorted(set(A["use_cases"])&set(Bt["use_cases"]))
        sh=f"Both are listed for: {', '.join(shared)}." if shared else "They're listed under different use cases, so check which fits your job."
        body=f'''<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">Compare</a> / {e(A["name"])} vs {e(Bt["name"])}</div>
<section style="padding-top:20px;text-align:left"><h1 style="text-align:left">{e(h1)}</h1>
<p class="lede" style="margin-left:0;text-align:left">{f"Two closely related {e(A['category'])} tools" if A["category"]==Bt["category"] else f"A {e(A['category'])} tool and a {e(Bt['category'])} tool that overlap"}, side by side. Everything here comes from our directory listing; pricing is as each maker states it. {e(sh)}</p>
<div class="tablewrap"><table class="cmp"><thead><tr><th><span class="sr">Feature</span></th><th><a class="icol" href="../tools/{a}.html">{ico(A,"../","sm")}{e(A["name"])}</a></th><th><a class="icol" href="../tools/{b}.html">{ico(Bt,"../","sm")}{e(Bt["name"])}</a></th></tr></thead><tbody>{rows}
<tr><th>Official site</th><td><a href="{e(A["url"])}" target="_blank" rel="noopener noreferrer">Visit ↗</a></td><td><a href="{e(Bt["url"])}" target="_blank" rel="noopener noreferrer">Visit ↗</a></td></tr></tbody></table></div>
<p class="disclose">{"We don't run benchmarks. The recommendation below is based on the listing facts in this table, not on testing." if N else "We don't benchmark tools or rank one above the other here."} Check each official site for current pricing and features before you choose.</p>
{faqh}{rel}<p style="margin-top:20px"><a href="index.html">← All comparisons</a></p></section>'''
        ld={"@context":"https://schema.org","@graph":[{"@type":"WebPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B},
            "about":[{"@type":"SoftwareApplication","name":x["name"],"url":x["url"],"applicationCategory":x["category"]} for x in (A,Bt)]},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Compare","item":B+"compare/"},{"@type":"ListItem","position":3,"name":f"{A['name']} vs {Bt['name']}","item":canon}]}]}
        if faq: ld["@graph"].append({"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a_}} for q,a_ in faq]})
        open(f"compare/{s}.html","w").write(shell("../",title,desc,canon,body,ld)); urls.append(canon)
    cards="".join(f'<a class="card" href="{cslug(a,b)}.html"><div class="ct"><span class="icopair">{ico(bs[a],"../","sm")}{ico(bs[b],"../","sm")}</span><h3 style="flex:1">{e(bs[a]["name"])} vs {e(bs[b]["name"])}</h3></div><p>{e(bs[a]["category"])}: {e(bs[a]["description"])}</p></a>' for a,b in PAIRS)
    canon=B+"compare/"; title="Compare AI agent tools side by side · AgentScout"; desc="Side-by-side comparisons of related AI agent tools: coding agents, frameworks, browser automation, voice, search APIs, no-code builders and observability."
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"hasPart":[{"@type":"WebPage","url":f"{B}compare/{cslug(a,b)}.html","name":f"{bs[a]['name']} vs {bs[b]['name']}"} for a,b in PAIRS]},{"@type":"VideoObject","name":"AgentScout Head-to-Head VS Radar & Benchmark Arena","description":"Animated 6-axis capability radar and side-by-side tug-of-war benchmark comparison across leading AI agent tools on AgentScout.","thumbnailUrl":B+"assets/animations/agentscout-vs-arena-poster.png","contentUrl":B+"assets/animations/agentscout-vs-arena.mp4","uploadDate":"2026-10-26T18:00:00-07:00","duration":"PT9S"},{"@type":"VideoObject","name":"3-Stage Autonomous AI Agent & MCP Production Pipeline","description":"Animated architecture breakdown showing how engineering teams chain MCP context servers, coding agents, and browser verification.","thumbnailUrl":B+"assets/animations/agentscout-workflow-infographic-poster.png","contentUrl":B+"assets/animations/agentscout-workflow-infographic.mp4","uploadDate":"2026-10-26T17:00:00-07:00","duration":"PT8S"}]}
    open("compare/index.html","w").write(shell("../",title,desc,canon,f'<div class="crumb"><a href="../index.html">AgentScout</a> / Compare</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">Compare AI agent tools</h1><p class="lede" style="margin-left:0;text-align:left">Closely related tools, side by side, using only facts from our listings.</p><div class="cpick" id="cpick" data-pairs="{",".join(cslug(a,b) for a,b in PAIRS)}"><h2>Compare any two tools</h2><p class="muted" style="margin:0">Pick any two of the {len(t)} tools in the directory and see them side by side.</p><div class="cp-row"><div class="cp-f"><label for="cp-a">Tool A</label><input id="cp-a" type="text" autocomplete="off" placeholder="Type a tool name" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="cp-a-l"><ul class="cp-l" id="cp-a-l" role="listbox" hidden></ul></div><button class="btn cp-swap" id="cp-swap" type="button" title="Swap" aria-label="Swap tools">⇄</button><div class="cp-f"><label for="cp-b">Tool B</label><input id="cp-b" type="text" autocomplete="off" placeholder="Type a tool name" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="cp-b-l"><ul class="cp-l" id="cp-b-l" role="listbox" hidden></ul></div><button class="btn primary" id="cp-go" type="button">Compare</button><button class="btn" id="cp-copy" type="button">Copy link</button></div><div id="cp-res"></div></div><figure style="margin:18px 0 24px;border-radius:14px;overflow:hidden;border:1px solid var(--border);background:#080810"><video autoplay loop muted playsinline preload="metadata" poster="../assets/animations/agentscout-vs-arena-poster.png" style="display:block;width:100%;height:auto;max-width:100%"><source src="../assets/animations/agentscout-vs-arena.mp4" type="video/mp4"></video></figure><h2 style="font-size:19px;margin:0 0 14px">Written comparisons</h2><div class="grid">{cards}</div></section><script src="../compare-picker.js?v=202610170400" defer></script>',ld)); urls.insert(0,canon)
    # badges page
    canon=B+"badges.html"; title="AgentScout badges for makers · AgentScout"; desc="Free badges for tools listed or featured on AgentScout. Add one to your README or site; it links back to your tool's page."
    ex=bs["langgraph"]
    body=f'''<div class="crumb"><a href="index.html">AgentScout</a> / Badges</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">Badges for makers</h1>
<p class="lede" style="margin-left:0;text-align:left">If your tool is on AgentScout, you can show it. Badges are free and link to your tool's page, so readers can see how it compares.</p>
<div class="embeds"><div class="embed"><img src="badges/listed-light.svg" alt="Listed on AgentScout (light)" width="220" height="54"><img src="badges/listed-dark.svg" alt="Listed on AgentScout (dark)" width="220" height="54"><p><b>Listed</b>: for any tool in the directory.</p></div>
<div class="embed"><img src="badges/featured-light.svg" alt="Featured on AgentScout (light)" width="220" height="54"><img src="badges/featured-dark.svg" alt="Featured on AgentScout (dark)" width="220" height="54"><p><b>Featured</b>: for tools we've picked as featured.</p></div></div>
{featured_generic()}<h2 style="font-size:18px;margin:32px 0 8px">How to get your snippet</h2><ol><li>Find your tool in the <a href="index.html#directory">directory</a> and open its page.</li><li>Scroll to "Badge for makers" and copy the HTML or Markdown, in light or dark.</li><li>Paste it into your README, docs or site footer.</li></ol>
<p>Not listed yet? <a href="https://github.com/Clampdown-web/agentscout/issues/new?labels=submission&amp;title=Tool%20submission%3A%20" target="_blank" rel="noopener noreferrer">Submit your tool</a>. Example from the {e(ex["name"])} page:</p>
{badge_html(ex,"").replace('<a href="../badges.html">About badges</a>','')}
<p class="disclose">Badges are SVG files hosted on this site. Please don't change the wording. Featured placements that are paid are always labeled as sponsored on AgentScout.</p></section>'''
    ld={"@context":"https://schema.org","@type":"WebPage","name":title,"description":desc,"url":canon}
    open("badges.html","w").write(shell("",title,desc,canon,body,ld).replace('href="index.html#','href="index.html#')); urls.insert(0,canon)
    import build_news; urls+=build_news.pages(t)  # per-story news pages + archives (before news.html)
    urls+=seo(t,urls)
    import build_tasks; urls+=build_tasks.pages(t)
    import build_best; urls+=build_best.pages(t)
    import build_free_tools; urls+=build_free_tools.pages(t)
    import build_landing; urls+=build_landing.pages(t)
    import build_mcp_tasks; urls+=build_mcp_tasks.pages(t)
    import build_ci; urls+=build_ci.pages(t)  # /skills/ Agent Skills (Oct 22 2026)
    import build_leaderboard; urls+=build_leaderboard.pages(t)  # /leaderboard/ (Oct 21 2026)
    import build_search; urls+=build_search.page()  # /search/ page (Oct 21 2026)  # Best MCP servers by task (Oct 21 2026)
    import build_trending; urls+=build_trending.pages(t)
    import build_aicite; urls+=build_aicite.pages(t)
    import build_videos; urls+=build_videos.pages(t)
    import build_bot_store; urls+=build_bot_store.pages(t)  # /videos/ How-To Video Guides & Pro Tips Hub (Oct 28 2026)  # MCP pricing + link-status tables, agent cards (Oct 22 2026)
    import os as _os2
    import glob as _g; urls+=[B+"bot-templates/"]+[B+"bot-templates/"+_os2.path.basename(x) for x in sorted(_g.glob("bot-templates/*.html")) if not x.endswith("/index.html")]  # Bot templates (launched Oct 19 2026 PT)
    _have=set(urls); urls+=[B+x for x in sorted(_g.glob("best/*-alternatives.html")) if B+x not in _have and 'http-equiv="refresh"' not in open(x).read(4000)]  # kept alternatives pages stay in the sitemap (Oct 20 2026)
    sm=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in [B,B+"new.html",B+"quiz.html",B+"llms.txt",B+"llms-full.txt",B+"generate.html",B+"sponsor.html"]+[f"{B}tools/{x['slug']}.html" for x in t]+urls:
        import build_rich; _r=build_rich.R.get(u.rsplit("/",1)[-1][:-5],{}) if "/tools/" in u else {}
        sm.append(f"  <url><loc>{u}</loc><lastmod>{max(today,_r.get('updated',today))}</lastmod></url>")
    open("sitemap.xml","w").write("\n".join(sm+["</urlset>",""]))
    print(len(PAIRS),"comparisons, badges page, sitemap",len(sm)-2,"urls")

# ---- SEO pages: categories, best-of guides, 404, llms.txt ----
CAT_INTRO={  # hand-written intros for categories added Oct 18, 2026 (others use the generic lede)
"memory & RAG":"Memory layers, vector and graph stores, and document parsers that give agents long-term memory and let them search your files: tools like Mem0, Zep, Supermemory, Cognee, LlamaParse and MarkItDown.",
"customer support":"AI support agents that answer customer questions, resolve tickets and take actions such as refunds, then hand off to a person when needed: Intercom Fin, Decagon, Sierra, Forethought and more.",
"sales & marketing":"AI SDRs, outbound and lead-research agents, plus marketing, SEO and social media agents for go-to-market teams: 11x, Artisan, Clay, Close, Jasper and more.",
"sandboxes & code execution":"Isolated sandboxes, microVMs and code-execution runtimes where agents can run generated code, shell commands and files without touching your machine: E2B, Modal, microsandbox, forkd, Judge0, Cloudflare Sandbox SDK and more.",
"security & governance":"Tools that keep agents safe and accountable: guardrails, prompt-injection and MCP scanners, credential brokers, sandbox policies and AI security-operations agents.",
"film & TV production":"AI tools for every stage of making film and TV: script breakdowns, storyboards and previs, virtual production and mocap, then post: editing, subtitles, color, VFX, upscaling and visual dubbing. Agentic tools that edit or plan for you on request (Descript's Underlord, Premiere AI Assistant, Eddie AI, Quickture, OpenMontage, VideoDB Director) come first.",
"video generation":"Models and apps that generate video from text, images or references, from Runway, Luma, Google Flow, Kling and Firefly to open models you can run yourself, like LTX-2, Wan and HunyuanVideo. Tools with agents that plan and run multi-shot work come first.",
"film & TV audio":"Audio post for film, TV and video: dialogue cleanup and repair, ADR and AI dubbing voices, Foley and sound effects, and mixing. Plugins like iZotope RX and sonible sit alongside dubbing services and open Foley models. For AI sound effects, also see ElevenLabs in Voice.",
"music production":"AI for making and finishing music: song and score generation, vocal synthesis and tuning, stem separation, and mixing and mastering assistants such as iZotope Ozone and LANDR. Agentic music editors come first.",
"image generation":"AI image generators and open image models: Midjourney, Leonardo, Ideogram, FLUX, Recraft, Nano Banana and Krea, plus open-source apps you run yourself such as Invoke, Krita AI Diffusion, SwarmUI and Qwen-Image. Tools that are commercially safe (licensed training data) say so in their listing.",
"graphic design & branding":"Design agents and AI design tools for logos, brand kits, social posts, ads, UI mockups and vectors: Canva AI, Lovart, Adobe Express, Figma Make, Google Stitch, Pomelli and Penpot's MCP lead the page, since they plan and build designs for you on request.",
"3D & concept art":"Text and image to 3D models and worlds, auto-rigging and character animation, sketch-to-render for product and architecture, and 3D scanning: Meshy, Tripo, Rodin, Spline, Vizcom, Hunyuan3D, TRELLIS, World Labs Marble and more.",
"photography & photo editing":"AI for photographers: culling, editing in your own style, portrait retouching, upscaling and restoration, background removal, product photos, headshots, real-estate editing and private AI photo libraries. Lightroom and Photoshop's AI Assistant come first, then Aftershoot, Imagen, Evoto, Topaz and others.",
"MCP servers":"Model Context Protocol (MCP) servers that plug Claude, Cursor, Codex, ChatGPT and other MCP clients into databases, docs, payments, browsers and SaaS apps, plus MCP gateways, registries and frameworks for building and running them: Context7, Smithery, DBHub, Serena, ToolHive, Obot and more. For hosting, model gateways, auth and other agent plumbing, see agent infra.",
"agent infra":"The infrastructure behind AI agents that is not primarily MCP: LLM and AI gateways, inference clouds, agent runtimes and control planes, tool-integration and auth platforms, agent email, payments and identity layers, and agent filesystems: LiteLLM, Portkey, Composio, Nango, Groq, Replicate, Together AI and more. MCP servers have their own page.",
"models & local runtimes":"Agentic models and the apps that run open models on your own computer or server, such as Ollama, LM Studio, LocalAI and Jan.",
}
def catslug(c): return re.sub(r"[^a-z0-9]+","-",c.lower()).strip("-")
def meta(x,n=155):
    s=f'{x["name"]}: {x["description"].rstrip(".")}. {x["category"]} tool; pricing: {(x.get("pricing_detail") or x["pricing"])}.'
    if len(s)<120: s+=" Alternatives and facts on AgentScout."
    if len(s)>n: s=s[:n-1].rsplit(" ",1)[0].rstrip(",;:")+"…"
    return s
import datetime as _dt
from zoneinfo import ZoneInfo as _Z
def week_new(x): return (not x.get("seed")) and x.get("added","")>=(_dt.datetime.now(_Z("America/Los_Angeles")).date()-_dt.timedelta(days=6)).isoformat()
def newfirst(items): return sorted(items,key=lambda x:(not week_new(x),"" if not week_new(x) else "~"+"".join(chr(255-ord(c)) for c in x.get("added",""))))
def added_line(x):
    a=x.get("added")
    if not a: return ""
    try: lab=_dt.date.fromisoformat(a).strftime("%b %-d, %Y")
    except Exception: return ""
    return f'<p class="addedago">Added <time class="ago" datetime="{e(a)}">{e(lab)}</time></p>'
def ptag(p):
    """Pricing class for search filters (Oct 21 2026); mirrors pc() in index.html. 'See site' and plain source-available stay unknown, never free."""
    p=(p or "").lower()
    if re.match(r"^(open|free$)",p): return "freemium" if re.search(r"cloud|enterprise|paid|hosted",p) else "free"
    if "freemium" in p or "+ cloud" in p: return "freemium"
    if re.match(r"^(paid|usage|enterprise)",p): return "paid"
    return "unknown"
FUNDS='<span class="b funds" title="Can move money: this tool can sign or send crypto transactions from a connected wallet. Use spend limits, a separate wallet and human approval for large amounts.">⚠ Moves funds</span>'
def card(x,d="../"): return f'<a class="card tile" data-s="{e(x["slug"])}" data-p="{ptag(x.get("pricing"))}" data-o="{1 if (x.get("pricing") or "").lower().startswith("open") else 0}" data-a="{e(x.get("added") or "")}" data-g="{x.get("github_stars") if x.get("github_stars") is not None else -1}" href="{d}tools/{x["slug"]}.html"><div class="ct">{ico(x,d)}<div class="tn"><h3>{e(x["name"])}</h3><div class="badges">{"<span class=\"b new\">New</span>" if week_new(x) else ""}<span class="b cat has-cico">{cico(x["category"])}{e(x["category"])}</span><span class="b">{e(x["pricing"])}</span>{FUNDS if x.get("moves_funds") else ""}</div></div></div><p class="hook">{e(x["description"])}</p>{added_line(x)}</a>'

# Category icons baked into HTML (paths read from app.js so site JS and build share one map; "tag" fallback).
def _load_icons():
    import re
    s=open("app.js").read(); blk=s[s.index("var P={")+7:s.index("},FB=")]
    m={k.strip('"'):v for k,v in re.findall(r'("[^"]+"|\w+):\'([^\']*)\'',blk)}
    m["__fb"]=re.search(r"FB='([^']*)'",s).group(1); return m
_ICONS=None
def cico(c):
    global _ICONS
    if _ICONS is None: _ICONS=_load_icons()
    p=_ICONS.get((c or "").strip().lower(),_ICONS["__fb"])
    return f'<svg class="cico" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{p}</svg>'
MEDIA_CATS={"film & TV production","video generation","film & TV audio","music production"}
# Related tools that stay in their own category but belong with the media categories (cross-linked both ways, Oct 18, 2026)
MEDIA_XLINK={"film & TV production":["davinci-resolve-mcp","mux-mcp","picsart-genai-mcp","mcp-for-blender","happyscribe-mcp","vidiq-mcp","twelvelabs-jockey-mcp","valossa-assistant-mcp","genspark","skywork"],
 "video generation":["minimax-mcp","picsart-genai-mcp","genspark","skywork","krea"],
 "film & TV audio":["elevenlabs-agents","deepgram","happyscribe-mcp","minimax-mcp"],
 "music production":["elevenlabs-agents","minimax-mcp"],
 # Art, design, 3D & photo categories (Oct 18, 2026)
 "image generation":["comfyui","adobe-firefly","higgsfield","dreamina","luma-dream-machine","picsart-genai-mcp","minimax-mcp"],
 "graphic design & branding":["canva-mcp","figma-mcp-server","talk-to-figma-mcp","framelink-figma-mcp","figma-console-mcp","icons8-mcp","brandfetch-mcp","logo-dev-mcp"],
 "3D & concept art":["mcp-for-blender","scenario","intangible","simulon"],
 "photography & photo editing":["imagesorcery-mcp","picsart-genai-mcp","topaz-video","magic-studio"],
 # Secondary placements (Oct 20, 2026, owner-approved): main category stays as-is
 "MCP servers":["tinyfish","cosvoice"]}
ART_CATS={"image generation","graphic design & branding","3D & concept art","photography & photo editing"}
LEAD_CATS=MEDIA_CATS|ART_CATS  # category pages that lead with agentic tools
def media_xlink_cats(slug): return [c for c,v in MEDIA_XLINK.items() if slug in v]
def media_xlink_html(c,t):
    by={x["slug"]:x for x in t}; its=[by[s] for s in MEDIA_XLINK.get(c,[]) if s in by]
    if not its: return ""
    note=' ElevenLabs also makes AI sound effects and music.' if c in("film & TV audio","music production") else ""
    return f'<h2 style="font-size:18px;margin:32px 0 10px">Related tools in other categories</h2><p class="muted" style="margin:0 0 10px;font-size:14px">These are listed under their main category but are useful for {e(c)} work too.{note}</p><div class="grid">{"".join(card(x) for x in its)}</div>'
def agentic_first(path,items):
    """Media category pages (Oct 18, 2026) lead with agentic tools; the order is otherwise unchanged."""
    if path in {f"categories/{catslug(c)}.html" for c in LEAD_CATS}: return sorted(items,key=lambda x:not x.get("agentic"))
    return items
def catbar(n): return ('<div class="filters cfilters" id="cfilters" role="group" aria-label="Filter and sort these tools"><label for="fprice">Pricing</label><select id="fprice" class="ucsel"><option value="">Any pricing</option><option value="free">Free</option><option value="freeplan">Free or free plan</option><option value="freemium">Freemium</option><option value="paid">Paid</option><option value="unknown">Pricing not listed</option></select>'
 '<label class="fchk"><input type="checkbox" id="fos"> Open source only</label><label for="fsort">Sort</label><select id="fsort" class="ucsel"><option value="">Recommended</option><option value="new">Newest first</option><option value="loved">Most loved</option><option value="stars">GitHub stars</option><option value="az">Name A–Z</option></select>'
 '<button type="button" class="chip" id="freset" hidden>Clear all filters</button></div><p class="count" id="ccount" aria-live="polite">Showing {n} of {n} tools</p><p class="snote muted" id="snote" hidden></p>').replace("{n}",str(n))
def listing_page(path,title,desc,h1,lede,items,crumb,extra="",pre=""):
    canon=B+path
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
        {"@type":"ItemList","itemListElement":[{"@type":"ListItem","position":i+1,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate(agentic_first(path,newfirst(items)))]},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":crumb,"item":canon}]}]}
    body=f'<div class="crumb"><a href="../index.html">AgentScout</a> / {e(crumb)}</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left"{' class="has-cico"' if path.startswith("categories/") else ""}>{cico(crumb) if path.startswith("categories/") else ""}{e(h1)}</h1><p class="lede" style="margin-left:0;text-align:left">{lede}</p>{pre}{catbar(len(items)) if path.startswith("categories/") else ""}<div class="grid"{' id="cgrid"' if path.startswith("categories/") else ""}>{"".join(card(x) for x in agentic_first(path,newfirst(items)))}</div>{extra}{'<script src="../catfilter.js?v=20261022a" defer></script>' if path.startswith("categories/") else ""}<p class="disclose">Facts come from our directory listings; pricing is as each maker states it. Check official sites before you choose.</p></section>'
    open(path,"w").write(shell("../",title,desc,canon,body,ld)); return canon
# --- Natural category <title> wording (Oct 18 2026) ---
_CAT_TT={"app builders":"AI app builders","browser/computer use":"browser and computer use agents","business agents":"AI business agents","coding":"AI coding agents and tools",
  "crypto":"crypto AI agent tools","customer support":"AI customer support agents","evals & observability":"AI agent evals & observability tools","frameworks":"AI agent frameworks",
  "games":"AI game agents and tools","MCP servers":"MCP servers & MCP tools","agent infra":"AI agent infrastructure tools","film & TV production":"AI film & TV production tools","video generation":"AI video generation tools","film & TV audio":"AI film & TV audio tools","music production":"AI music production tools","image generation":"AI image generators","graphic design & branding":"AI graphic design & branding tools","3D & concept art":"AI 3D & concept art tools","photography & photo editing":"AI photography & photo editing tools","memory & RAG":"AI agent memory & RAG tools","models & local runtimes":"models & local runtimes for AI agents",
  "no-code builders":"no-code AI agent builders","personal agents":"personal AI agents","productivity":"AI productivity agents","research":"AI research agents",
  "sales & marketing":"AI sales & marketing agents","sandboxes & code execution":"AI agent sandboxes & code execution tools","security & governance":"AI agent security & governance tools","vision":"AI vision agent tools","voice":"AI voice agents"}
def cat_phrase(c): return _CAT_TT.get(c, c+' AI agent tools')
def cat_title(c,n): return f"{n} best {cat_phrase(c)} (2026) · AgentScout"
def seo(t,urls):
    import os,collections
    os.makedirs("categories",exist_ok=True); os.makedirs("best",exist_ok=True)
    cats=collections.Counter(x["category"] for x in t); out=[]
    nav='<h2 style="font-size:16px;margin:32px 0 10px">All categories</h2><div class="badges">'+"".join(f'<a class="b uc has-cico" href="{catslug(c)}.html">{cico(c)}{e(c)} ({n})</a>' for c,n in cats.most_common())+'</div>'
    for c,n in cats.most_common():
        items=[x for x in t if x["category"]==c]
        title=cat_title(c,n)
        _nm=', '.join(x['name'] for x in (agentic_first(f"categories/{catslug(c)}.html",newfirst(items)) if c in LEAD_CATS else items)[:3])
        desc=next((d for d in (f"{n} link-checked {cat_phrase(c)}, including {_nm}. Pricing as stated by makers, audience and maturity.",f"{n} link-checked {cat_phrase(c)}, including {_nm}. Pricing as makers state it.",f"{n} link-checked {cat_phrase(c)}, including {_nm}.") if len(d)<=158),f"{n} link-checked {cat_phrase(c)}, including {_nm}."[:158])
        import build_tasks as _bt,build_subtasks as _bs
        _tm=_bt.mapping(t); _ids={id(x) for x in items}
        _tc=sorted([(s2,T2[1],sum(id(y) in _ids for y in i2)) for s2,(T2,i2) in _tm.items()],key=lambda z:(-z[2],z[1]))
        _tc=[z for z in _tc if z[2]>=3][:14]
        _chips=('<h2 style="font-size:16px;margin:18px 0 8px">Tasks in this category</h2><div class="badges">'+"".join(f'<a class="b uc" href="../tasks/{s2}.html">{e(_cap(l))} ({k})</a>' for s2,l,k in _tc)+'</div>') if _tc else ""
        _cn={"MCP servers":"MCP servers and MCP tools","agent infra":"agent infrastructure tools"}.get(c,c+" tools"); _lede=f"{n} {e(_cn)} in the AgentScout directory, each with a link-checked listing."
        if c in CAT_INTRO: _lede+=" "+CAT_INTRO[c]
        if c=="MCP servers":
            import build_aicite as _bac
            _lede+=f' <strong>{e(_bac.mcp_uptime_line(t))}</strong> (<a href="../mcp/link-status.html">daily MCP link status</a> · <a href="../mcp/pricing.html">MCP pricing table</a> · <a href="../mcp/connect.html">connect our free MCP server</a>).'
        _pin_cta=(f'<div class="cat-pin-cta"><div class="cpc-body"><span class="npill npmcp cpc-pill"><svg class="npico" aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="14" height="14"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 2l2.4 7.2H22l-6 4.6 2.3 7.2L12 16.5 5.7 21l2.3-7.2-6-4.6h7.6z"/></svg>Featured Slot Open</span>'
                  f'<span class="cpc-txt"><b>Building in {e(c)}?</b> List free ($0 · 3–5d queue), fast-track with a 7-day boost for <b>$29</b>, pin at the top of <b>{e(c)}</b> for <b>30 days</b> + permanent <code style="font-size:12px">/best/</code> &amp; <code style="font-size:12px">/compare/</code> placement for <b>$49</b>, or book the exclusive <b>$99/wk</b> sitewide &amp; newsletter sponsor slot.</span></div>'
                  f'<div class="cpc-acts"><a class="btn primary pkg-cta-free cpc-btn" href="../submit.html#free-form">Submit Free ($0)</a>'
                  f'<a class="btn primary pkg-cta-fast cpc-btn" href="https://buy.stripe.com/fZufZi7X5cJNbtbdPRe7m02" target="_blank" rel="noopener noreferrer">Fast-Track — $29 →</a>'
                  f'<a class="btn primary pkg-cta-pop cpc-btn" href="https://buy.stripe.com/bJefZi4KT6lp9l3dPRe7m00" target="_blank" rel="noopener noreferrer">30-Day Category Pin — $49 ★ →</a>'
                  f'<a class="btn primary pkg-cta-vip cpc-btn" href="https://buy.stripe.com/6oU4gA2CL9xB2WFcLNe7m01" target="_blank" rel="noopener noreferrer">Sitewide Sponsor — $99/wk →</a>'
                  f'<a class="btn cpc-btn" href="../sponsor.html#packages">Compare Packages ($0/$29/$49/$99)</a></div></div>')
        _pre=f'<p class="tcount" style="margin:0 0 6px;font-size:14px;color:var(--muted)">There are {n} {e(_cn)}: {e(_bs.price_line(items))}.</p>'+_chips+_pin_cta
        if c=="crypto":  # Wallet safety sub-section + Moves funds explainer (Oct 21 2026, owner-approved)
            _ws=[x for x in items if x.get("wallet_safety")]; _mf=sum(1 for x in items if x.get("moves_funds"))
            if _ws: _pre+=(f'<section id="wallet-safety" aria-labelledby="wallet-safety-h"><h2 id="wallet-safety-h" style="font-size:18px;margin:24px 0 6px">Wallet safety</h2>'
                f'<p style="margin:0 0 10px;font-size:14px">{len(_ws)} tools that check a token, contract, address or site before you or your agent sign: scam and phishing flags, risky approvals, honeypots, sanctions and transaction simulation. '
                f'Run one of these before any tool marked <span class="b funds">⚠ Moves funds</span> ({_mf} in this category) sends money. Those tools can sign or send transactions from a connected wallet, so give them a separate wallet, spend limits and human approval for large amounts. Not financial advice.</p>'
                f'<div class="grid">{"".join(card(x) for x in sorted(_ws,key=lambda x:x["name"].lower()))}</div></section><h2 style="font-size:18px;margin:28px 0 6px">All crypto tools</h2>')
        out.append(listing_page(f"categories/{catslug(c)}.html",title,desc,({"MCP servers":"MCP servers and MCP tools","agent infra":"AI agent infrastructure tools"}.get(c) or (f"{c[0].upper()+c[1:]} AI tools" if c in LEAD_CATS else f"{c[0].upper()+c[1:]} AI agent tools")),_lede,items,c[0].upper()+c[1:],media_xlink_html(c,t)+_bs.repo_table(items,title=f"Top {c} repos on GitHub")+nav,pre=_pre))
    tiles="".join(f'<a class="card" href="{catslug(c)}.html"><div class="ct"><h3 class="has-cico">{cico(c)}{e(c[0].upper()+c[1:])}</h3></div><p>{n} tool{"s" if n!=1 else ""}</p></a>' for c,n in cats.most_common())
    canon=B+"categories/"; title=f"AI agent tool categories · AgentScout"; desc=f"Browse {len(t)} AI agent tools by category: coding agents, MCP servers and infra, frameworks, browser use, voice, research, evals and more."
    open("categories/index.html","w").write(shell("../",title,desc,canon,f'<div class="crumb"><a href="../index.html">AgentScout</a> / Categories</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">AI agent tool categories</h1><p class="lede" style="margin-left:0;text-align:left">{len(cats)} categories, {len(t)} tools.</p><div class="grid">{tiles}</div></section>',{"@context":"https://schema.org","@type":"CollectionPage","name":title,"description":desc,"url":canon}))
    out.insert(0,canon)
    mcp=[x for x in t if x["category"]=="MCP servers" or "connect tools via MCP" in x["use_cases"]]
    # MCP cluster (Oct 18 2026; Oct 20 split): categories/mcp-servers is the main "MCP servers" page (best/mcp-servers redirects there).
    # Client guides are client-specific: only listings whose text says they work with that client.
    try: _RICH=json.load(open("tool_rich.json"))
    except Exception: _RICH={}
    def _says(x,pat):
        r=_RICH.get(x["slug"]) or {}
        txt=x["description"]+" "+json.dumps([r.get("long"),r.get("features")],ensure_ascii=False)
        return bool(re.search(pat,txt))
    CLIENTS=[("claude-code","Claude Code",r"\bClaude\b(?! (?:Sonnet|Opus|Haiku|models?\b))"),("cursor","Cursor",r"\bCursor\b"),("codex","Codex",r"\bCodex\b")]
    guides=' · '.join(f'<a href="mcp-servers-for-{s}.html">MCP servers for {c}</a>' for s,c,_ in CLIENTS)
    for s,client,pat in CLIENTS:
        named=[x for x in mcp if _says(x,pat)]
        named=sorted(named,key=lambda x:(x.get("github_stars") is None,-(x.get("github_stars") or 0),x["name"].lower()))
        cl=[x for x in t if x["name"] in {"Claude Code":["Claude Code"],"Cursor":["Cursor"],"Codex":["OpenAI Codex CLI"]}[client]]
        cll=f' See our <a href="../tools/{cl[0]["slug"]}.html">{e(cl[0]["name"])} listing</a>.' if cl else ""
        out.append(listing_page(f"best/mcp-servers-for-{s}.html",f"Best MCP servers for {client} (2026) · AgentScout",
            f"{len(named)} MCP servers whose listings say they work with {client}, including {', '.join(x['name'] for x in named[:3])}. Link-checked, pricing as stated."[:158],
            f"MCP servers that work with {client}",f"{client} is an MCP client. These {len(named)} MCP servers and MCP tools say in their own listing or docs that they work with {e(client)}, sorted by GitHub stars. Check each tool's docs for {e(client)} setup.{cll} For every MCP server in the directory, see the <a href=\"../categories/mcp-servers.html\">MCP servers category</a>.",named,f"MCP servers for {client}",'<p style="margin-top:24px">More guides: <a href="../categories/mcp-servers.html">All MCP servers</a> · '+guides+'</p>'))
    out.append(news_page(t)); out.append(free_tools(t)); out.append(newsletter_page())
    alt=[x for x in t if x["category"]=="coding" and x["slug"]!="cursor"]
    out.append(listing_page("best/cursor-alternatives.html",f"{len(alt)} Best Cursor Alternatives (2026): Free & Open-Source · AgentScout",
        f"Compare {len(alt)} Cursor alternatives in 2026 ({sum(1 for x in alt if x['pricing'].startswith('Open'))} open source), including Windsurf, Claude Code, Cline and GitHub Copilot. Pricing & stars."[:158],
        "Cursor alternatives (2026)",f'{len(alt)} other coding agents and AI editors in the AgentScout directory. See also our <a href="../tools/cursor.html">Cursor listing</a> and <a href="../compare/cursor-vs-windsurf.html">Cursor vs Windsurf</a>.',alt,"Cursor alternatives"))
    # 404
    s=shell("/","Page not found · AgentScout","This page doesn't exist on AgentScout.",B,f'<section style="padding-top:40px"><h1>Page not found</h1><p class="lede">That page doesn\'t exist. Try the <a href="/index.html#directory">directory</a> or <a href="/categories/index.html">categories</a>.</p></section>',{"@context":"https://schema.org","@type":"WebPage","name":"Not found"})
    open("404.html","w").write(s.replace('<link rel="canonical" href="'+B+'">','<meta name="robots" content="noindex">'))
    # llms.txt
    _nm=sum(1 for _x in t if _x['category']=='MCP servers')
    try: _lc=json.load(open("api/tools.json")).get("last_checked","")
    except Exception: _lc=""
    import build_aicite as _bac2; _ul2=_bac2.mcp_uptime_line(t)
    L=["# AgentScout","",f"> AgentScout is a curated, read-only directory of {len(t):,} AI agent tools in {len(cats)} categories, including {_nm:,} MCP servers ({_ul2}). Listings are link-checked daily; pricing is as makers state it. Featured slots are clearly labeled and sit above the list; rankings are never paid. This file tells AI agents and assistants how to use the directory.","",f"Entity note: AgentScout (also searched as Agent Scout or AgentScoutHQ) is the independent AI agent and MCP server directory at https://agentscouthq.com, published in the official MCP Registry as com.agentscouthq/directory with endpoint https://mcp.agentscouthq.com/mcp (and https://agentscouthq.com/mcp/sse). AgentScout's official MCP server (com.agentscouthq/directory at https://agentscouthq.com/mcp/sse) is 100% free, public, and read-only, with no API key, crypto wallet, or x402 payment required. It is completely unrelated to the paid third-party x402 web-fetch package that shares a similar name.","",f"Site: {B}","Contact: support@agentscouthq.com","X: https://x.com/AgentScoutHQ, https://x.com/clampdown19","MCP Registry ID: com.agentscouthq/directory","MCP Endpoint: https://mcp.agentscouthq.com/mcp (and https://agentscouthq.com/mcp/sse — 100% free, read-only, no API key or x402 wallet required)"]+([f"Catalog last checked: {_lc} (Pacific)"] if _lc else [])+["",
    "## For AI agents","",
    f"- Fastest path: fetch [api/tools.json]({B}api/tools.json) once and filter it locally. No key, no rate-limited API, plain HTTPS GET.",
    "- api/tools.json is an object with `count`, `last_checked` (YYYY-MM-DD, Pacific) and `tools`, an array where each tool has `name`, `slug`, `category`, `description`, `url`, `website`, `github`, `pricing` (maker's wording), `price_tag` (free / freemium / paid), `platforms`, `open_source`, `license`, `github_stars`, `tags`, `added` and `page` (its AgentScout listing).",
    "- To cite a tool, link its `page` (https://agentscouthq.com/tools/<slug>.html). To cite a category, use the category links below.",
    "- Treat `pricing` as the maker's own claim on the date shown; it can change. GitHub stars are refreshed daily.",
    "- Everything here is read-only. There is no chat, search or write endpoint for agents; to list a tool, a person uses the submit form.","",
    "## Update cadence","",
    "- New tools: added most days; see the Recently added section below and new.html.",
    "- Links: checked daily (`last_checked` in api/tools.json).",
    f"- MCP pricing and link-status tables: rebuilt with every site update, each with a dated change history.",
    "- GitHub stars: snapshot daily.",
    f"- [sitemap.xml]({B}sitemap.xml) carries a per-page lastmod.","",
    "## Machine-readable catalog","",f"- [llms-full.txt]({B}llms-full.txt): single-file Markdown context with category comparison tables and all {_nm:,} verified MCP servers (pricing, link status, runs_locally, license, stars, endpoints)",f"- [api/tools.json]({B}api/tools.json): full catalog with counts and check date",f"- [tools.json]({B}tools.json): same tools in the site's internal format",f"- [api/products.json]({B}api/products.json): Stripe Agentic Commerce product feed for maker listing packages ($0, $29, $49, $99/wk) and Made by AgentScout pre-trained bots (also at [.well-known/acp.json]({B}.well-known/acp.json))",f"- [.well-known/ai-plugin.json]({B}.well-known/ai-plugin.json): AI plugin manifest with prompt-engineered model instructions",f"- [openapi.json]({B}openapi.json) & [openapi.yaml]({B}openapi.yaml): OpenAPI 3.1 JSON & YAML descriptions of the feeds under /api/ (also at [.well-known/openapi.json]({B}.well-known/openapi.json) and [.well-known/openapi.yaml]({B}.well-known/openapi.yaml))",f"- [manifest.json]({B}manifest.json): Web app brand manifest with icons and theme colors",f"- [.well-known/mcp.json]({B}.well-known/mcp.json): MCP server card pointing to https://mcp.agentscouthq.com/mcp",f"- [.well-known/agent-card.json]({B}.well-known/agent-card.json): agent card describing this directory (also at /.well-known/agent.json)",f"- [sitemap.xml]({B}sitemap.xml): all public pages","",
    "## Key pages","",f"- [MCP server pricing table]({B}mcp/pricing.html): every MCP server's stated pricing, dated, with change history",f"- [MCP server link status]({B}mcp/link-status.html): latest automated link check for every MCP server, with change history",f"- [AgentScout MCP server]({B}mcp/connect.html): free, read-only MCP endpoint https://mcp.agentscouthq.com/mcp (Streamable HTTP, no key; also at https://agentscouthq.com/mcp/sse) with search_tools, get_tool, list_categories, best_for_task and list_packages. Optional runs_locally filter: offline, self_hosted_or_offline or any; locality is inferred from listings, so verify with the vendor before relying on it for compliance",f"- [MCP servers category]({B}categories/mcp-servers.html): {_nm:,} tools",f"- [New tools, last 30 days]({B}new.html)",f"- [AI agent news]({B}news/): daily AI agent and MCP news stories with sources",f"- [Free AI agent tools]({B}free-tools.html): AgentScout's free calculators and builders plus free and open-source tools from the directory",f"- [Free AI image generator]({B}generate.html): no sign-up image generator","",
    "## Browse","",f"- [Directory]({B}index.html#directory)",f"- [Compare]({B}compare/)",f"- [Leaderboard]({B}leaderboard/): tools ranked by visitor ratings, reviews and GitHub stars",f"- [Badges]({B}badges.html)",f"- [Submit a tool]({B}submit.html)",f"- [Sponsor & Get Featured]({B}sponsor.html): Free Community Listing ($0 forever, 3–5 day standard review queue at {B}submit.html#free-form), Fast-Track + 7-Day Launch Boost ($29 one-time at https://buy.stripe.com/fZufZi7X5cJNbtbdPRe7m02), 30-Day Category Pin + Permanent SEO/AEO Placement ($49 one-time at https://buy.stripe.com/bJefZi4KT6lp9l3dPRe7m00), and Weekly Sitewide Sponsor + Newsletter Top Slot ($99/week at https://buy.stripe.com/6oU4gA2CL9xB2WFcLNe7m01) via Stripe or X Money (@clampdown19)",f"- [About AgentScout]({B}about.html): what AgentScout is, how tools are picked and checked",f"- [Privacy policy]({B}privacy.html)","","## Categories",""]
    L+=[f"- [{c}]({B}categories/{catslug(c)}.html): {n} tool{'s' if n!=1 else ''}" for c,n in cats.most_common()]
    L+=["","## Guides","",f"- [MCP servers]({B}categories/mcp-servers.html)",f"- [Agent Skills with install commands]({B}skills/)",f"- [Agent infra]({B}categories/agent-infra.html)",f"- [Best MCP servers for Claude Code]({B}best/mcp-servers-for-claude-code.html)",f"- [Best MCP servers for Cursor]({B}best/mcp-servers-for-cursor.html)",f"- [Best MCP servers for Codex]({B}best/mcp-servers-for-codex.html)",f"- [Cursor alternatives 2026]({B}best/cursor-alternatives.html)",f"- [Best open-source browser automation agents]({B}best/open-source-browser-automation-agents.html)",f"- [Best local & offline AI agents]({B}best/local-offline-ai-agents.html)",""]
    # every tool added in the last 2 days (today PT + yesterday), no fixed cap (owner bug fix Oct 20 2026); falls back to the 12 newest if none
    import datetime as _d,zoneinfo as _z
    _today=_d.datetime.now(_z.ZoneInfo("America/Los_Angeles")).date(); _cut=(_today-_d.timedelta(days=1)).isoformat()
    _srt=sorted(t,key=lambda x:(not x.get("seed"),x.get("added",""),x.get("id",0)),reverse=True)
    rec=[x for x in _srt if x.get("added","")>=_cut] or _srt[:12]
    L+=["## Recently added",f"- [All new tools, last 30 days]({B}new.html)",f"- Tools added in the last 2 days ({_cut} to {_today.isoformat()}): {len(rec)}",""]+[f"- [{x['name']}]({B}tools/{x['slug']}.html) (added {x.get('added','')}): {x['description']}" for x in rec]+[""]
    open("llms.txt","w").write("\n".join(L)); return out


# Pacific display for stored UTC timestamps (Oct 18 2026: site shows Pacific, never UTC; datetime attrs/JSON-LD stay ISO UTC)
def _pt_dt(iso):
    from zoneinfo import ZoneInfo
    try:
        d=datetime.datetime.fromisoformat(str(iso).replace("Z","+00:00"))
        if d.tzinfo is None: d=d.replace(tzinfo=datetime.timezone.utc)
        return d.astimezone(ZoneInfo("America/Los_Angeles"))
    except Exception: return None
def pt_time(iso):
    d=_pt_dt(iso); return d.strftime("%b %-d, %Y, %-I:%M %p")+" PT" if d else str(iso)
def pt_date(iso):
    d=_pt_dt(iso) if "T" in str(iso) else None
    return d.date().isoformat() if d else str(iso)[:10]
def news_page(t):
    import os
    bs={x["slug"]:x for x in t}; canon=B+"news.html"
    arc=json.load(open("news-archive.json")) if os.path.exists("news-archive.json") else {"items":[],"updated":""}
    days={}
    for x in arc["items"]: days.setdefault(pt_date(x["date"]),[]).append(x)
    def item(x):
        tl=(f' · <a class="icol" href="tools/{e(x["tool"])}.html">'+ico(bs[x["tool"]],"","sm").replace('width="40" height="40"','width="24" height="24"').replace(f'alt="{e(bs[x["tool"]]["name"])} logo"','alt=""')+f'{e(bs[x["tool"]]["name"])} on AgentScout →</a>') if x.get("tool") in bs else ""
        sm=f'<p class="nsum">{e(x["summary"])}</p>' if x.get("summary") else ""
        h3=f'<a href="{e(x["page"])}">{e(x["title"])}</a>' if x.get("page") and os.path.exists(x["page"]) else f'<a href="{e(su(x["url"]))}" target="_blank" rel="noopener noreferrer">{e(x["title"])}</a>'
        return f'<li class="nitem"><h3>{h3}</h3>{sm}<span class="nm">{e(x["source"])} · <time datetime="{e(x["date"])}">{e(pt_time(x["date"]))}</time> · <a href="{e(su(x["url"]))}" target="_blank" rel="noopener noreferrer">Source ↗</a>{tl}</span></li>'
    body='<div class="crumb"><a href="index.html">AgentScout</a> / Agent news</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">AI agent news today</h1><p class="lede" style="margin-left:0;text-align:left">Daily launches and updates about AI agents, coding agents and MCP, with short summaries in our own words. Updated '+e(pt_time(arc.get("updated","")))+'.</p>'
    for d in sorted(days,reverse=True):
        dd=datetime.date.fromisoformat(d).strftime("%A, %B %-d, %Y")
        body+=f'<h2 class="nday">{dd}</h2><ol class="nlist">'+"".join(item(x) for x in days[d])+'</ol>'
    if not days: body+='<p>No agent news yet.</p>'
    body+='<p class="disclose">Headlines and summaries are written by AgentScout from each source; follow the source link for the full story. Older stories: <a href="news/index.html">news archive by month</a>.</p></section>'
    title="AI Agent News Today: Daily Agent Launches & Updates | AgentScout"
    desc="Daily AI agent news: new agent launches, coding agents, MCP servers and agent frameworks, summarized in plain words with links to the original sources."
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon},{"@type":"ItemList","itemListElement":[{"@type":"ListItem","position":i+1,"item":{"@type":"NewsArticle","headline":x["title"][:110],"datePublished":x["date"],"url":(B+x["page"]) if x.get("page") else x["url"],**({"isBasedOn":x["url"]} if x.get("page") else {}),"description":x.get("summary",x["title"]),"publisher":{"@type":"Organization","name":x["source"]}}} for i,x in enumerate(arc["items"][:50])]}]}
    open("news.html","w").write(shell("",title,desc,canon,body,ld).replace('<script type="application/ld+json">','<script type="application/ld+json">',1)); return canon

# Past issues on the public Beehiiv archive (https://agentscout.beehiiv.com/archive), checked read-only 2026-10-18.
NL_ISSUES=json.load(open("data/newsletter-issues.json"))  # refreshed by scripts/update_latest_issue.py (Oct 20 2026)
def newsletter_page():
    canon=B+"newsletter.html"; title="AgentScout Weekly: AI Agent Newsletter Archive | AgentScout"
    desc="Past issues of AgentScout Weekly, a free weekly email with the best new AI agents, launches and what's worth trying. Read the archive or subscribe."
    iss=sorted(NL_ISSUES,key=lambda x:x["date"],reverse=True)
    li="".join(f'<li class="nitem"><h3><a href="{e(x["url"])}" target="_blank" rel="noopener noreferrer">{e(x["title"])}</a></h3>'+(f'<p class="nsum">{e(x["subtitle"])}</p>' if x.get("subtitle") else "")+f'<span class="nm"><time datetime="{e(x["date"])}">{datetime.date.fromisoformat(x["date"]).strftime("%B %-d, %Y")}</time> · <a href="{e(x["url"])}" target="_blank" rel="noopener noreferrer">Read on Beehiiv ↗</a></span></li>' for x in iss)
    lst=f'<ol class="nlist">{li}</ol>' if iss else '<p>Issues will appear here.</p>'
    body=('<div class="crumb"><a href="index.html">AgentScout</a> / Newsletter</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">AgentScout Weekly</h1>'
          '<p class="lede" style="margin-left:0;text-align:left">One short email a week with the best new AI agents, launches and what\'s worth trying. Free, unsubscribe anytime. Subscribe below.</p>'
          f'<h2 style="font-size:18px;margin:28px 0 10px">Past issues</h2>{lst}<p style="margin-top:18px;font-size:14px"><a href="https://agentscout.beehiiv.com/archive" target="_blank" rel="noopener noreferrer">Full archive on Beehiiv ↗</a></p>'
          '<p class="disclose">The newsletter is sent with Beehiiv. Issues open on the Beehiiv site. See our <a href="privacy.html">privacy policy</a>.</p></section>')
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
        {"@type":"ItemList","itemListElement":[{"@type":"ListItem","position":i+1,"url":x["url"],"name":x["title"]} for i,x in enumerate(iss)]},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Newsletter","item":canon}]}]}
    open("newsletter.html","w").write(shell("",title,desc,canon,body,ld)); return canon
FREE_RE=re.compile(r"open[- ]?source|open weights|open[- ]weight|open standard|\bfree\b|freemium",re.I)
def free_tools(t):
    """Free-tools hub: AgentScout's own free tools first, then every directory listing whose maker-stated pricing
    (pricing_detail, else pricing; the same value as "pricing" in api/tools.json) says open source, open weights/standard,
    free, free tier/plan or freemium. Listings marked discontinued or archived are left out."""
    import collections
    pr=lambda x:(x.get("pricing_detail") or x["pricing"])
    items=[x for x in t if FREE_RE.search(pr(x)) and not re.search(r"discontinu|archived|shut down",x.get("maturity","")+" "+pr(x),re.I)]
    cats=collections.Counter(x["category"] for x in items)
    canon=B+"free-tools.html"; title="Free AI Agent Tools (2026): Open-Source & Free Tiers | AgentScout"
    desc=f"{len(items)} free and open-source AI agent tools in {len(cats)} categories, plus AgentScout's free AI cost calculator, token counter, prompt builder and image generator."[:158]
    feat=('<div class="card tile" style="margin:18px 0 8px;max-width:640px"><div class="ct"><span class="ico"><span aria-hidden="true">✨</span></span><div class="tn"><h3>Unlimited Free AI Image Generator</h3>'
          '<div class="badges"><span class="b new">Free</span></div></div></div><p class="hook">Type a prompt and get an image in seconds. No sign-up needed. Powered by FLUX.1 [schnell].</p>'
          '<a class="btn primary" href="generate.html">Open the image generator</a></div>'
          # Oct 23 2026 (owner): MCP server card, same plug icon as the header MCP pill; links to the connect page
          '<div class="card tile" style="margin:8px 0 8px;max-width:640px"><div class="ct"><span class="ico"><svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="22" height="22" style="color:var(--accent)"><path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M9 2v5M15 2v5M6 7h12v4a6 6 0 0 1-12 0zM12 17v5"/></svg></span><div class="tn"><h3>AgentScout MCP server</h3>'
          '<div class="badges"><span class="b new">Free</span></div></div></div><p class="hook">Let Claude, Cursor and ChatGPT pull live AgentScout results. Free, no sign-up or API key, focused on AI agents.</p>'
          '<a class="btn primary" href="mcp/connect.html">Connect the MCP server</a></div>')
    jump=" · ".join(f'<a href="#{catslug(c)}">{e(c)} ({n})</a>' for c,n in cats.most_common())
    sec=""
    for c,n in cats.most_common():
        li="".join(f'<li style="margin:0 0 10px"><a href="tools/{x["slug"]}.html" style="display:inline-flex;align-items:center;gap:8px;vertical-align:middle;max-width:100%">{ico24(x)}<b>{e(x["name"])}</b></a> <span class="b" style="font-size:12px">{e(pr(x))}</span><br><span style="color:var(--muted);font-size:14px">{e(x["description"])}</span></li>'
                   for x in sorted([x for x in items if x["category"]==c],key=lambda x:(x.get("slug") in __import__("build_api").HW,-(x.get("github_stars") or 0),x["name"].lower())))
        sec+=f'<h2 id="{catslug(c)}" class="has-cico" style="font-size:18px;margin:32px 0 10px">{cico(c)}{e(c[0].upper()+c[1:])} <span style="color:var(--muted);font-weight:400">({n})</span></h2><p style="margin:0 0 10px;font-size:14px"><a href="categories/{catslug(c)}.html">All {e(c)} tools →</a></p><ul style="list-style:none;padding:0;margin:0">{li}</ul>'
    body=('<div class="crumb"><a href="index.html">AgentScout</a> / Free tools</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">Free AI agent tools</h1>'
          f'<p class="lede" style="margin-left:0;text-align:left">Free tools built by AgentScout, plus {len(items)} free and open-source AI agent tools from our directory, grouped by category.</p>'
          '<figure style="margin:18px 0 24px;border-radius:14px;overflow:hidden;border:1px solid var(--border);background:#080810"><video autoplay loop muted playsinline preload="metadata" poster="assets/animations/agentscout-bot-constellation-poster.png" style="display:block;width:100%;height:auto;max-width:100%"><source src="assets/animations/agentscout-bot-constellation.mp4" type="video/mp4"></video></figure>'
          '<h2 style="font-size:18px;margin:24px 0 4px">Featured: free from AgentScout</h2>'+feat+'<h2 id="agentscout-tools" style="font-size:18px;margin:28px 0 10px">'+BUILT_BY("")+'</h2><p style="font-size:14px;color:var(--muted);margin:0 0 12px">Calculators and generators that run entirely in your browser. No sign-up, no API key, nothing sent to a server.</p><div class="grid">'+__import__("build_free_tools").hub_cards()+'</div>'+
          f'<h2 style="font-size:18px;margin:32px 0 8px">Free and open-source tools in the directory</h2><p style="font-size:14px;color:var(--muted)">Included when the pricing the maker states says open source, open weights or open standard, free, a free tier or plan, or freemium. Open-source tools can still have paid cloud plans or need a paid model API key. Check each official site.</p><p style="font-size:14px">{jump}</p>'
          +sec+'<p class="disclose">Facts come from our directory listings; pricing is as each maker states it and can change. Listings marked discontinued are left out. Within each category, tools are sorted by GitHub stars where known.</p></section>')
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B},
        "hasPart":[{"@type":"WebApplication","name":"AgentScout AI Image Generator","url":B+"generate.html","isAccessibleForFree":True,"applicationCategory":"MultimediaApplication","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"}},{"@type":"WebApplication","name":"AgentScout MCP server","url":B+"mcp/connect.html","isAccessibleForFree":True,"applicationCategory":"DeveloperApplication","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"}}]+[{"@type":"WebApplication","name":"AgentScout "+n,"url":f"{B}free-tools/{sl}.html","isAccessibleForFree":True,"applicationCategory":"DeveloperApplication","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"}} for sl,n,_,_ in __import__("build_free_tools").TOOLS]},
        {"@type":"ItemList","numberOfItems":len(items)+2,"itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout AI Image Generator","url":B+"generate.html"},{"@type":"ListItem","position":2,"name":"AgentScout MCP server","url":B+"mcp/connect.html"}]+[{"@type":"ListItem","position":i+3,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate([y for c,_ in cats.most_common() for y in sorted([z for z in items if z["category"]==c],key=lambda z:(-(z.get("github_stars") or 0),z["name"].lower()))])]},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Free tools","item":canon}]},{"@type":"VideoObject","name":"AgentScout One-Stop AI Agent, Bot Template & Free Calculator Constellation","description":f"Animated orbital node constellation showcasing AgentScout's {len(__import__('re').findall(r'<li class=\"bt-row\"', open('bot-templates/index.html').read())) if __import__('os').path.exists('bot-templates/index.html') else 189} ready-made bot templates, 19 zero-signup browser calculators, {sum(1 for x in t if x.get('category') == 'MCP servers')}+ MCP servers, and open-source AI agents.","thumbnailUrl":B+"assets/animations/agentscout-bot-constellation-poster.png","contentUrl":B+"assets/animations/agentscout-bot-constellation.mp4","uploadDate":"2026-10-26T18:00:00-07:00","duration":"PT9S"}]}
    open("free-tools.html","w").write(shell("",title,desc,canon,body,ld))
    p="categories/vision.html"; v=open(p).read()
    if "gencall" not in v: v=v.replace('</p><div class="grid">','</p><a class="gencall" href="../generate.html">✨ Try AgentScout\'s free AI image generator →</a><div class="grid">',1); open(p,"w").write(v)
    return canon

# Featured listings: re-apply featured.json after any generator run that imports this module,
# so rebuilds keep active Featured blocks and drop expired ones (no-op with an empty list).
import atexit as _atexit, os as _os
_FEAT_CWD=_os.getcwd()
def _apply_featured():
    try:
        _here=_os.getcwd(); _os.chdir(_FEAT_CWD)
        if _os.path.exists("featured.json") and _os.path.exists("index.html"):
            import build_featured; build_featured.run()
        # Google Analytics 4 tag on every page (ga4.py, Oct 19 2026); before lastmod, which ignores the tag block
        if _os.path.exists("ga4.py"):
            import ga4; ga4.apply_all()
        if _os.path.exists("sitemap.xml"):
            import build_lastmod; build_lastmod.run()
        # Re-write redirects.json pages after cleanup in best/ and tasks/ may have deleted them.
        if _os.path.exists("redirects.json"):
            import build_redirects; build_redirects.run()
        if _os.path.exists("llms.txt"):
            import build_seo; build_seo.llms_extra()
        _os.chdir(_here)
    except Exception as _ex: print("featured skipped:",_ex)
_atexit.register(_apply_featured)
