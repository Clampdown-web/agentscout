"""Badges section, comparison pages, badges page and sitemap. Called from build_site.py."""
import html,json,re,datetime
B="https://agentscouthq.com/"
e=lambda s:html.escape(str(s or ""))
def su(u):
    u=str(u or "").strip()
    return u if re.match(r"(?i)^https?://",u) else "#"
PAIRS=[("claude-code","openai-codex-cli"),("cursor","windsurf"),("cline","roo-code"),("langgraph","crewai"),("crewai","autogen"),
("browser-use","stagehand"),("exa","tavily"),("livekit-agents","pipecat"),("vapi","retell-ai"),("n8n","make"),("dify","flowise"),
("langfuse","langsmith"),("e2b","modal"),("bolt","v0")]
NEW=json.load(open("compare_new.json")); NEW.pop("_note",None)  # Oct 18 batch: recommendation copy, keyed by slug
PAIRS+=[tuple(k.split("-vs-")) for k in NEW]
def ico(x,d="../",cls=""):
    L=e(x["name"].strip()[:1].upper()); im=f'<img src="{d}{x["logo"]}" alt="{e(x["name"])} logo" width="40" height="40" loading="lazy" decoding="async" onerror="this.remove()">' if x.get("logo") else ""
    return f'<span class="ico {cls}"><span aria-hidden="true">{L}</span>{im}</span>'
def ico24(x): return ico(x,"","sm").replace('width="40" height="40"','width="24" height="24"')
def cslug(a,b): return f"{a}-vs-{b}"
def badge_html(x,depth="../"):
    url=f"{B}tools/{x['slug']}.html"; kind="featured" if x.get("featured") else "listed"; lab=kind.title()
    out=""
    for th in ["light","dark"]:
        img=f"{B}badges/{kind}-{th}.svg"
        h=f'<a href="{url}" target="_blank" rel="noopener noreferrer"><img src="{img}" alt="{lab} on AgentScout" width="220" height="54"></a>'
        m=f"[![{lab} on AgentScout]({img})]({url})"
        out+=f'<div class="embed"><img src="{depth}badges/{kind}-{th}.svg" alt="{lab} on AgentScout ({th})" width="220" height="54"><label>HTML</label><textarea readonly rows="3" onclick="this.select()">{e(h)}</textarea><button class="btn" type="button" onclick="navigator.clipboard.writeText(this.previousElementSibling.value);this.textContent=\'Copied\'">Copy HTML</button><label>Markdown</label><textarea readonly rows="2" onclick="this.select()">{e(m)}</textarea><button class="btn" type="button" onclick="navigator.clipboard.writeText(this.previousElementSibling.value);this.textContent=\'Copied\'">Copy Markdown</button></div>'
    return f'<h2 style="font-size:16px;margin:36px 0 6px">Badge for makers</h2><p class="muted" style="margin:0 0 14px">Built {e(x["name"])}? Add this badge to your README or site. It links back to this page. <a href="../badges.html">About badges</a></p><div class="embeds">{out}</div>'
def featured_generic():
    out=""
    for th in ["light","dark"]:
        img=f"{B}badges/featured-{th}.svg"
        h=f'<a href="{B}" target="_blank" rel="noopener noreferrer"><img src="{img}" alt="Featured on AgentScout" width="220" height="54"></a>'
        m=f"[![Featured on AgentScout]({img})]({B})"
        cp=lambda kind:f'<button class="btn" type="button" onclick="navigator.clipboard.writeText(this.previousElementSibling.value);this.textContent=\'Copied\'">Copy {kind}</button>'
        out+=f'<div class="embed"><img src="badges/featured-{th}.svg" alt="Featured on AgentScout ({th})" width="220" height="54"><label>HTML ({th})</label><textarea readonly rows="3" onclick="this.select()">{e(h)}</textarea>{cp("HTML")}<label>Markdown ({th})</label><textarea readonly rows="2" onclick="this.select()">{e(m)}</textarea>{cp("Markdown")}</div>'
    return f'<h2 id="featured-badge" style="font-size:18px;margin:32px 0 8px">Featured on AgentScout badge</h2><p style="margin:0 0 14px">Copy a ready-made snippet. It links to the AgentScout homepage.</p><div class="embeds">{out}</div>'
def cmp_links(x,t):
    ps=[(a,b) for a,b in PAIRS if x["slug"] in (a,b)]
    if not ps: return ""
    bs={y["slug"]:y for y in t}
    li="".join(f'<a class="b uc" href="../compare/{cslug(a,b)}.html">{e(bs[a]["name"])} vs {e(bs[b]["name"])}</a>' for a,b in ps)
    return f'<h2 style="font-size:16px;margin:0 0 10px">Compare</h2><div class="badges" style="margin-bottom:32px">{li}</div>'
def shell(depth,title,desc,canon,body,ld):
    tpl=open("detail.tpl.html").read()
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
       ("Pricing (as stated)",x.get("pricing_detail",x["pricing"])),("Maturity",x["maturity"]),
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
        rel=f'<p style="margin-top:20px">Related: <a href="../tools/{a}.html">{e(A["name"])}</a> · <a href="../tools/{b}.html">{e(Bt["name"])}</a> · <a href="../categories/{catslug(A["category"])}.html">More {e(A["category"])} tools</a> · <a href="../best/mcp-servers.html">Best MCP servers</a></p>'

        fa,fb=facts(A),facts(Bt)
        if N:
            fa=[(k,(v or A["pricing"]) if k.startswith("Pricing") else v) for k,v in fa]; fb=[(k,(v or Bt["pricing"]) if k.startswith("Pricing") else v) for k,v in fb]
            def pm(x,R): return "Paid plans with a free trial" if (R.get("pricing") or {}).get("free") is False and R["pricing"].get("trial") else x["pricing"]
            fa=[(k,pm(A,RA) if k.startswith("Pricing") and v==A["pricing"] else v) for k,v in fa]; fb=[(k,pm(Bt,RB) if k.startswith("Pricing") and v==Bt["pricing"] else v) for k,v in fb]
            ex=[("Pricing model",pm(A,RA),pm(Bt,RB)),("Open source",osl(A),osl(Bt))]
            if pr(A,RA) or pr(Bt,RB): ex.append(("Plans (official pricing page)",pr(A,RA) or "Not listed",pr(Bt,RB) or "Not listed"))
            ex+=[("Key features",kf(A,RA),kf(Bt,RB)),("Best for",N["best"][0],N["best"][1])]
            fa=fa[:1]+[(k,va) for k,va,_ in ex]+fa[1:]; fb=fb[:1]+[(k,vb) for k,_,vb in ex]+fb[1:]
            rel=f'<p style="margin-top:20px">Related: <a href="../tools/{a}.html">{e(A["name"])}</a> · <a href="../tools/{b}.html">{e(Bt["name"])}</a> · '+" · ".join(f'<a href="../categories/{catslug(c)}.html">More {e(c)} tools</a>' for c in dict.fromkeys([A["category"],Bt["category"]]))+' · <a href="../best/mcp-servers.html">Best MCP servers</a></p>'
            faqh=f'<h2 style="font-size:18px;margin:32px 0 8px">Our recommendation</h2><p style="margin:0 0 8px"><b>Choose <a href="../tools/{a}.html">{e(A["name"])}</a> if</b> {e(N["choose"][0])}</p><p style="margin:0"><b>Choose <a href="../tools/{b}.html">{e(Bt["name"])}</a> if</b> {e(N["choose"][1])}</p>'+faqh
        rows="".join(f"<tr><th>{e(k)}</th><td>{e(va)}</td><td>{e(vb)}</td></tr>" for (k,va),(_,vb) in zip(fa,fb))
        shared=sorted(set(A["use_cases"])&set(Bt["use_cases"]))
        sh=f"Both are listed for: {', '.join(shared)}." if shared else "They're listed under different use cases, so check which fits your job."
        body=f'''<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">Compare</a> / {e(A["name"])} vs {e(Bt["name"])}</div>
<section style="padding-top:20px;text-align:left"><h1 style="text-align:left">{e(h1)}</h1>
<p class="lede" style="margin-left:0;text-align:left">{f"Two closely related {e(A['category'])} tools" if A["category"]==Bt["category"] else f"A {e(A['category'])} tool and a {e(Bt['category'])} tool that overlap"}, side by side. Everything here comes from our directory listing; pricing is as each maker states it. {e(sh)}</p>
<div class="tablewrap"><table class="cmp"><thead><tr><th></th><th><a class="icol" href="../tools/{a}.html">{ico(A,"../","sm")}{e(A["name"])}</a></th><th><a class="icol" href="../tools/{b}.html">{ico(Bt,"../","sm")}{e(Bt["name"])}</a></th></tr></thead><tbody>{rows}
<tr><th>Official site</th><td><a href="{e(A["url"])}" target="_blank" rel="noopener noreferrer">Visit ↗</a></td><td><a href="{e(Bt["url"])}" target="_blank" rel="noopener noreferrer">Visit ↗</a></td></tr></tbody></table></div>
<p class="disclose">{"We don't run benchmarks. The recommendation below is based on the listing facts in this table, not on testing." if N else "We don't benchmark tools or rank one above the other here."} Check each official site for current pricing and features before you choose.</p>
{faqh}{rel}<p style="margin-top:20px"><a href="index.html">← All comparisons</a></p></section>'''
        ld={"@context":"https://schema.org","@graph":[{"@type":"WebPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B},
            "about":[{"@type":"SoftwareApplication","name":x["name"],"url":x["url"],"applicationCategory":x["category"]} for x in (A,Bt)]},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Compare","item":B+"compare/"},{"@type":"ListItem","position":3,"name":f"{A['name']} vs {Bt['name']}","item":canon}]}]}
        if faq: ld["@graph"].append({"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a_}} for q,a_ in faq]})
        open(f"compare/{s}.html","w").write(shell("../",title,desc,canon,body,ld)); urls.append(canon)
    cards="".join(f'<a class="card" href="{cslug(a,b)}.html"><div class="ct"><span class="icopair">{ico(bs[a],"../","sm")}{ico(bs[b],"../","sm")}</span><h3 style="flex:1">{e(bs[a]["name"])} vs {e(bs[b]["name"])}</h3></div><p>{e(bs[a]["category"])}: {e(bs[a]["description"])}</p></a>' for a,b in PAIRS)
    canon=B+"compare/"; title="Compare AI agent tools side by side · AgentScout"; desc="Side-by-side comparisons of closely related AI agent tools: coding agents, frameworks, browser automation, voice, search APIs, no-code builders and observability."
    ld={"@context":"https://schema.org","@type":"CollectionPage","name":title,"description":desc,"url":canon,"hasPart":[{"@type":"WebPage","url":f"{B}compare/{cslug(a,b)}.html","name":f"{bs[a]['name']} vs {bs[b]['name']}"} for a,b in PAIRS]}
    open("compare/index.html","w").write(shell("../",title,desc,canon,f'<div class="crumb"><a href="../index.html">AgentScout</a> / Compare</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">Compare AI agent tools</h1><p class="lede" style="margin-left:0;text-align:left">Closely related tools, side by side, using only facts from our listings.</p><div class="cpick" id="cpick" data-pairs="{",".join(cslug(a,b) for a,b in PAIRS)}"><h2>Compare any two tools</h2><p class="muted" style="margin:0">Pick any two of the {len(t)} tools in the directory and see them side by side.</p><div class="cp-row"><div class="cp-f"><label for="cp-a">Tool A</label><input id="cp-a" type="text" autocomplete="off" placeholder="Type a tool name" role="combobox" aria-controls="cp-a-l"><ul class="cp-l" id="cp-a-l" role="listbox" hidden></ul></div><button class="btn cp-swap" id="cp-swap" type="button" title="Swap" aria-label="Swap tools">⇄</button><div class="cp-f"><label for="cp-b">Tool B</label><input id="cp-b" type="text" autocomplete="off" placeholder="Type a tool name" role="combobox" aria-controls="cp-b-l"><ul class="cp-l" id="cp-b-l" role="listbox" hidden></ul></div><button class="btn primary" id="cp-go" type="button">Compare</button><button class="btn" id="cp-copy" type="button">Copy link</button></div><div id="cp-res"></div></div><h2 style="font-size:19px;margin:0 0 14px">Written comparisons</h2><div class="grid">{cards}</div></section><script src="../compare-picker.js?v=202610170400" defer></script>',ld)); urls.insert(0,canon)
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
    import build_trending; urls+=build_trending.pages(t)
    sm=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in [B,B+"new.html",B+"quiz.html",B+"llms.txt",B+"generate.html"]+[f"{B}tools/{x['slug']}.html" for x in t]+urls:
        import build_rich; _r=build_rich.R.get(u.rsplit("/",1)[-1][:-5],{}) if "/tools/" in u else {}
        sm.append(f"  <url><loc>{u}</loc><lastmod>{max(today,_r.get('updated',today))}</lastmod></url>")
    open("sitemap.xml","w").write("\n".join(sm+["</urlset>",""]))
    print(len(PAIRS),"comparisons, badges page, sitemap",len(sm)-2,"urls")

# ---- SEO pages: categories, best-of guides, 404, llms.txt ----
def catslug(c): return re.sub(r"[^a-z0-9]+","-",c.lower()).strip("-")
def meta(x,n=155):
    s=f'{x["name"]}: {x["description"].rstrip(".")}. {x["category"]} tool; pricing: {x.get("pricing_detail",x["pricing"])}.'
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
def card(x,d="../"): return f'<a class="card tile" href="{d}tools/{x["slug"]}.html"><div class="ct">{ico(x,d)}<div class="tn"><h3>{e(x["name"])}</h3><div class="badges">{"<span class=\"b new\">New</span>" if week_new(x) else ""}<span class="b cat has-cico">{cico(x["category"])}{e(x["category"])}</span><span class="b">{e(x["pricing"])}</span></div></div></div><p class="hook">{e(x["description"])}</p>{added_line(x)}</a>'

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
def listing_page(path,title,desc,h1,lede,items,crumb,extra="",pre=""):
    canon=B+path
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
        {"@type":"ItemList","itemListElement":[{"@type":"ListItem","position":i+1,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate(items)]},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":crumb,"item":canon}]}]}
    body=f'<div class="crumb"><a href="../index.html">AgentScout</a> / {e(crumb)}</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left"{' class="has-cico"' if path.startswith("categories/") else ""}>{cico(crumb) if path.startswith("categories/") else ""}{e(h1)}</h1><p class="lede" style="margin-left:0;text-align:left">{lede}</p>{pre}<div class="grid">{"".join(card(x) for x in newfirst(items))}</div>{extra}<p class="disclose">Facts come from our directory listings; pricing is as each maker states it. Check official sites before you choose.</p></section>'
    open(path,"w").write(shell("../",title,desc,canon,body,ld)); return canon
def seo(t,urls):
    import os,collections
    os.makedirs("categories",exist_ok=True); os.makedirs("best",exist_ok=True)
    cats=collections.Counter(x["category"] for x in t); out=[]
    nav='<h2 style="font-size:16px;margin:32px 0 10px">All categories</h2><div class="badges">'+"".join(f'<a class="b uc has-cico" href="{catslug(c)}.html">{cico(c)}{e(c)} ({n})</a>' for c,n in cats.most_common())+'</div>'
    for c,n in cats.most_common():
        items=[x for x in t if x["category"]==c]
        title=f"{n} best {c} AI agent tools (2026) · AgentScout"[:70]
        desc=f"{n} link-checked {c} AI agent tools, including {', '.join(x['name'] for x in items[:3])}. Pricing as stated by makers, audience and maturity."[:158]
        import build_tasks as _bt,build_subtasks as _bs
        _tm=_bt.mapping(t); _ids={id(x) for x in items}
        _tc=sorted([(s2,T2[1],sum(id(y) in _ids for y in i2)) for s2,(T2,i2) in _tm.items()],key=lambda z:(-z[2],z[1]))
        _tc=[z for z in _tc if z[2]>=3][:14]
        _chips=('<h2 style="font-size:16px;margin:18px 0 8px">Tasks in this category</h2><div class="badges">'+"".join(f'<a class="b uc" href="../tasks/{s2}.html">{e(l.capitalize())} ({k})</a>' for s2,l,k in _tc)+'</div>') if _tc else ""
        _lede=f"{n} {e(c)} tools in the AgentScout directory, each with a link-checked listing."
        _pre=f'<p class="tcount" style="margin:0 0 6px;font-size:14px;color:var(--muted)">There are {n} {e(c)} tools: {e(_bs.price_line(items))}.</p>'+_chips
        out.append(listing_page(f"categories/{catslug(c)}.html",title,desc,f"{c.capitalize()} AI agent tools",_lede,items,c.capitalize(),_bs.repo_table(items,title=f"Top {c} repos on GitHub")+nav,pre=_pre))
    tiles="".join(f'<a class="card" href="{catslug(c)}.html"><div class="ct"><h3 class="has-cico">{cico(c)}{e(c.capitalize())}</h3></div><p>{n} tool{"s" if n!=1 else ""}</p></a>' for c,n in cats.most_common())
    canon=B+"categories/"; title=f"AI agent tool categories · AgentScout"; desc=f"Browse {len(t)} AI agent tools by category: coding agents, MCP servers and infra, frameworks, browser use, voice, research, evals and more."
    open("categories/index.html","w").write(shell("../",title,desc,canon,f'<div class="crumb"><a href="../index.html">AgentScout</a> / Categories</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">AI agent tool categories</h1><p class="lede" style="margin-left:0;text-align:left">{len(cats)} categories, {len(t)} tools.</p><div class="grid">{tiles}</div></section>',{"@context":"https://schema.org","@type":"CollectionPage","name":title,"description":desc,"url":canon}))
    out.insert(0,canon)
    mcp=[x for x in t if x["category"]=="MCP & infra" or "connect tools via MCP" in x["use_cases"]]
    guides=' · '.join(f'<a href="mcp-servers-for-{s}.html">Best MCP servers for {c}</a>' for s,c in [("claude-code","Claude Code"),("cursor","Cursor"),("codex","Codex")])
    for s,client,keys in [("claude-code","Claude Code",["Claude"]),("cursor","Cursor",["Cursor"]),("codex","Codex",["Codex"])]:
        named=[x for x in mcp if any(k in x["description"] for k in keys)]; rest=[x for x in mcp if x not in named]
        note=f" Listings whose descriptions name {client} come first: {', '.join(e(x['name']) for x in named)}." if named else ""
        cl=[x for x in t if x["name"] in {"Claude Code":["Claude Code"],"Cursor":["Cursor"],"Codex":["OpenAI Codex CLI"]}[client]]
        cll=f' See our <a href="../tools/{cl[0]["slug"]}.html">{e(cl[0]["name"])} listing</a>.' if cl else ""
        out.append(listing_page(f"best/mcp-servers-for-{s}.html",f"Best MCP servers for {client} (2026) · AgentScout",
            f"{len(mcp)} MCP servers and MCP tools from our directory you can try with {client}, including {', '.join(x['name'] for x in (named+rest)[:3])}. Pricing as stated."[:158],
            f"Best MCP servers for {client}",f"{client} is an MCP client, so it can connect to MCP servers. These are the {len(mcp)} MCP servers and MCP-related tools in the AgentScout directory.{note} Check each tool's docs for {e(client)} setup.{cll}",named+rest,f"MCP servers for {client}",'<p style="margin-top:24px">More guides: <a href="mcp-servers.html">Best MCP servers (all)</a> · '+guides+'</p>'))
    out.append(listing_page("best/mcp-servers.html","Best MCP Servers (2026): curated list · AgentScout",
        f"Best MCP servers in 2026: {len(mcp)} link-checked MCP servers and MCP tools, including {', '.join(x['name'] for x in mcp[:3])}. Pricing as stated by makers."[:158],
        "Best MCP Servers (2026)",f'A curated list of the {len(mcp)} MCP servers and MCP-related tools in the AgentScout directory. MCP (Model Context Protocol) lets agents like Claude Code, Cursor and Codex connect to tools and data. See also the <a href="../categories/mcp-infra.html">MCP &amp; infra category</a>.',mcp,"Best MCP servers",'<p style="margin-top:24px">Guides by client: '+guides+'</p>'))
    out.append(news_page(t)); out.append(free_tools(t)); out.append(newsletter_page())
    alt=[x for x in t if x["category"]=="coding" and x["slug"]!="cursor"]
    out.append(listing_page("best/cursor-alternatives.html","Cursor alternatives 2026: AI coding agents · AgentScout",
        f"{len(alt)} Cursor alternatives from our directory, including Windsurf, Claude Code, Cline and GitHub Copilot. Pricing as stated by makers, open-source options marked."[:158],
        "Cursor alternatives (2026)",f'{len(alt)} other coding agents and AI editors in the AgentScout directory. See also our <a href="../tools/cursor.html">Cursor listing</a> and <a href="../compare/cursor-vs-windsurf.html">Cursor vs Windsurf</a>.',alt,"Cursor alternatives"))
    # 404
    s=shell("/","Page not found · AgentScout","This page doesn't exist on AgentScout.",B,f'<section style="padding-top:40px"><h1>Page not found</h1><p class="lede">That page doesn\'t exist. Try the <a href="/index.html#directory">directory</a> or <a href="/categories/index.html">categories</a>.</p></section>',{"@context":"https://schema.org","@type":"WebPage","name":"Not found"})
    open("404.html","w").write(s.replace('<link rel="canonical" href="'+B+'">','<meta name="robots" content="noindex">'))
    # llms.txt
    L=["# AgentScout","",f"> AgentScout is a curated directory of {len(t)} AI agent tools for builders and ready-to-use products. Facts are verified; pricing is as makers state it.","",f"Site: {B}","X: https://x.com/AgentScoutHQ","Contact: support@agentscouthq.com","","## Machine-readable catalog","",f"- [tools.json]({B}tools.json): full catalog",f"- [sitemap.xml]({B}sitemap.xml): all public pages","","## Browse","",f"- [Directory]({B}index.html#directory)",f"- [Compare]({B}compare/)",f"- [Badges]({B}badges.html)",f"- [Submit a tool]({B}submit.html)",f"- [About AgentScout]({B}about.html): what AgentScout is, how tools are picked and checked",f"- [Privacy policy]({B}privacy.html)","","## Categories",""]
    L+=[f"- [{c}]({B}categories/{catslug(c)}.html): {n} tool{'s' if n!=1 else ''}" for c,n in cats.most_common()]
    L+=["","## Guides","",f"- [Best MCP servers 2026]({B}best/mcp-servers.html)",f"- [Best MCP servers for Claude Code]({B}best/mcp-servers-for-claude-code.html)",f"- [Best MCP servers for Cursor]({B}best/mcp-servers-for-cursor.html)",f"- [Best MCP servers for Codex]({B}best/mcp-servers-for-codex.html)",f"- [Cursor alternatives 2026]({B}best/cursor-alternatives.html)",""]
    rec=sorted(t,key=lambda x:(not x.get("seed"),x.get("added",""),x.get("id",0)),reverse=True)[:12]
    L+=["## Recently added",f"- [All new tools, last 30 days]({B}new.html)",""]+[f"- [{x['name']}]({B}tools/{x['slug']}.html) (added {x.get('added','')}): {x['description']}" for x in rec]+[""]
    open("llms.txt","w").write("\n".join(L)); return out

def news_page(t):
    import os
    bs={x["slug"]:x for x in t}; canon=B+"news.html"
    arc=json.load(open("news-archive.json")) if os.path.exists("news-archive.json") else {"items":[],"updated":""}
    days={}
    for x in arc["items"]: days.setdefault(x["date"][:10],[]).append(x)
    def item(x):
        tl=f' · <a href="tools/{e(x["tool"])}.html">On AgentScout →</a>' if x.get("tool") in bs else ""
        sm=f'<p class="nsum">{e(x["summary"])}</p>' if x.get("summary") else ""
        h3=f'<a href="{e(x["page"])}">{e(x["title"])}</a>' if x.get("page") and os.path.exists(x["page"]) else f'<a href="{e(su(x["url"]))}" target="_blank" rel="noopener noreferrer">{e(x["title"])}</a>'
        return f'<li class="nitem"><h3>{h3}</h3>{sm}<span class="nm">{e(x["source"])} · <time datetime="{e(x["date"])}">{e(x["date"][:16].replace("T"," "))} UTC</time> · <a href="{e(su(x["url"]))}" target="_blank" rel="noopener noreferrer">Source ↗</a>{tl}</span></li>'
    body='<div class="crumb"><a href="index.html">AgentScout</a> / Agent news</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">AI agent news today</h1><p class="lede" style="margin-left:0;text-align:left">Daily launches and updates about AI agents, coding agents and MCP, with short summaries in our own words. Updated '+e(arc.get("updated","")[:16].replace("T"," "))+' UTC.</p>'
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
NL_ISSUES=[{"title":"AgentScout Weekly #1: 5 agent tools worth trying","subtitle":"Labeled for builders and everyday users","date":"2026-10-16","url":"https://agentscout.beehiiv.com/p/agentscout-weekly-1-5-agent-tools-worth-trying"}]
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
          '<div class="badges"><span class="b new">Free</span><span class="b cat">by AgentScout</span></div></div></div><p class="hook">Type a prompt and get an image in seconds. No sign-up needed. Powered by FLUX.1 [schnell].</p>'
          '<a class="btn primary" href="generate.html">Open the image generator</a></div>')
    jump=" · ".join(f'<a href="#{catslug(c)}">{e(c)} ({n})</a>' for c,n in cats.most_common())
    sec=""
    for c,n in cats.most_common():
        li="".join(f'<li style="margin:0 0 10px"><a href="tools/{x["slug"]}.html" style="display:inline-flex;align-items:center;gap:8px;vertical-align:middle;max-width:100%">{ico24(x)}<b>{e(x["name"])}</b></a> <span class="b" style="font-size:12px">{e(pr(x))}</span><br><span style="color:var(--muted);font-size:14px">{e(x["description"])}</span></li>'
                   for x in sorted([x for x in items if x["category"]==c],key=lambda x:(-(x.get("github_stars") or 0),x["name"].lower())))
        sec+=f'<h2 id="{catslug(c)}" class="has-cico" style="font-size:18px;margin:32px 0 10px">{cico(c)}{e(c[0].upper()+c[1:])} <span style="color:var(--muted);font-weight:400">({n})</span></h2><p style="margin:0 0 10px;font-size:14px"><a href="categories/{catslug(c)}.html">All {e(c)} tools →</a></p><ul style="list-style:none;padding:0;margin:0">{li}</ul>'
    body=('<div class="crumb"><a href="index.html">AgentScout</a> / Free tools</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">Free AI agent tools</h1>'
          f'<p class="lede" style="margin-left:0;text-align:left">Free tools built by AgentScout, plus {len(items)} free and open-source AI agent tools from our directory, grouped by category.</p>'
          '<h2 style="font-size:18px;margin:24px 0 4px">Featured: free from AgentScout</h2>'+feat+'<h2 id="agentscout-tools" style="font-size:18px;margin:28px 0 10px">More free tools from AgentScout</h2><p style="font-size:14px;color:var(--muted);margin:0 0 12px">Calculators and generators that run entirely in your browser. No sign-up, no API key, nothing sent to a server.</p><div class="grid">'+__import__("build_free_tools").hub_cards()+'</div>'+
          f'<h2 style="font-size:18px;margin:32px 0 8px">Free and open-source tools in the directory</h2><p style="font-size:14px;color:var(--muted)">Included when the pricing the maker states says open source, open weights or open standard, free, a free tier or plan, or freemium. Open-source tools can still have paid cloud plans or need a paid model API key. Check each official site.</p><p style="font-size:14px">{jump}</p>'
          +sec+'<p class="disclose">Facts come from our directory listings; pricing is as each maker states it and can change. Listings marked discontinued are left out. Within each category, tools are sorted by GitHub stars where known.</p></section>')
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B},
        "hasPart":[{"@type":"WebApplication","name":"AgentScout AI Image Generator","url":B+"generate.html","isAccessibleForFree":True,"applicationCategory":"MultimediaApplication","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"}}]+[{"@type":"WebApplication","name":"AgentScout "+n,"url":f"{B}free-tools/{sl}.html","isAccessibleForFree":True,"applicationCategory":"DeveloperApplication","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"}} for sl,n,_,_ in __import__("build_free_tools").TOOLS]},
        {"@type":"ItemList","numberOfItems":len(items)+1,"itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout AI Image Generator","url":B+"generate.html"}]+[{"@type":"ListItem","position":i+2,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate([y for c,_ in cats.most_common() for y in sorted([z for z in items if z["category"]==c],key=lambda z:(-(z.get("github_stars") or 0),z["name"].lower()))])]},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Free tools","item":canon}]}]}
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
        if _os.path.exists("sitemap.xml"):
            import build_lastmod; build_lastmod.run()
        _os.chdir(_here)
    except Exception as _ex: print("featured skipped:",_ex)
_atexit.register(_apply_featured)
