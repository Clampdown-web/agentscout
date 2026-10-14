"""Badges section, comparison pages, badges page and sitemap. Called from build_site.py."""
import html,json,re,datetime
B="https://clampdown-web.github.io/agentscout/"
e=lambda s:html.escape(str(s or ""))
PAIRS=[("claude-code","openai-codex-cli"),("cursor","windsurf"),("cline","roo-code"),("langgraph","crewai"),("crewai","autogen"),
("browser-use","stagehand"),("exa","tavily"),("livekit-agents","pipecat"),("vapi","retell-ai"),("n8n","make"),("dify","flowise"),
("langfuse","langsmith"),("e2b","modal"),("bolt","v0")]
def cslug(a,b): return f"{a}-vs-{b}"
def badge_html(x,depth="../"):
    url=f"{B}tools/{x['slug']}.html"; kind="featured" if x.get("featured") else "listed"; lab=kind.title()
    out=""
    for th in ["light","dark"]:
        img=f"{B}badges/{kind}-{th}.svg"
        h=f'<a href="{url}" target="_blank" rel="noopener"><img src="{img}" alt="{lab} on AgentScout" width="220" height="54"></a>'
        m=f"[![{lab} on AgentScout]({img})]({url})"
        out+=f'<div class="embed"><img src="{depth}badges/{kind}-{th}.svg" alt="{lab} on AgentScout ({th})" width="220" height="54"><label>HTML</label><textarea readonly rows="3" onclick="this.select()">{e(h)}</textarea><button class="btn" type="button" onclick="navigator.clipboard.writeText(this.previousElementSibling.value);this.textContent=\'Copied\'">Copy HTML</button><label>Markdown</label><textarea readonly rows="2" onclick="this.select()">{e(m)}</textarea><button class="btn" type="button" onclick="navigator.clipboard.writeText(this.previousElementSibling.value);this.textContent=\'Copied\'">Copy Markdown</button></div>'
    return f'<h2 style="font-size:16px;margin:36px 0 6px">Badge for makers</h2><p class="muted" style="margin:0 0 14px">Built {e(x["name"])}? Add this badge to your README or site. It links back to this page. <a href="../badges.html">About badges</a></p><div class="embeds">{out}</div>'
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
<script type="application/ld+json">{json.dumps(ld,ensure_ascii=False)}</script>
</head>{nav}<main class="wrap">{body}</main>
{foot}'''
def facts(x):
    f=[("Description",x["description"]),("Category",x["category"]),("Audience","For builders" if x["audience"]=="builders" else "Ready to use"),
       ("Pricing (as stated)",x.get("pricing_detail",x["pricing"])),("Maturity",x["maturity"]),
       ("GitHub stars",f'{x["github_stars"]:,}' if x.get("github_stars") is not None else "Not tracked"),("Use cases",", ".join(x["use_cases"])),("Link checked",x["verified"])]
    return f
def build(t):
    bs={y["slug"]:y for y in t}; today=datetime.date.today().isoformat(); urls=[]
    for a,b in PAIRS:
        A,Bt=bs[a],bs[b]; s=cslug(a,b); canon=f"{B}compare/{s}.html"
        title=f"{A['name']} vs {Bt['name']}: side-by-side comparison · AgentScout"
        desc=f"{A['name']} vs {Bt['name']} compared: pricing as stated by the makers, audience, maturity and use cases. {A['description']}"[:158]
        fa,fb=facts(A),facts(Bt)
        rows="".join(f"<tr><th>{e(k)}</th><td>{e(va)}</td><td>{e(vb)}</td></tr>" for (k,va),(_,vb) in zip(fa,fb))
        shared=sorted(set(A["use_cases"])&set(Bt["use_cases"]))
        sh=f"Both are listed for: {', '.join(shared)}." if shared else "They're listed under different use cases, so check which fits your job."
        body=f'''<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">Compare</a> / {e(A["name"])} vs {e(Bt["name"])}</div>
<section style="padding-top:20px;text-align:left"><h1 style="text-align:left">{e(A["name"])} vs {e(Bt["name"])}</h1>
<p class="lede" style="margin-left:0;text-align:left">Two closely related {e(A["category"])} tools, side by side. Everything here comes from our directory listing; pricing is as each maker states it. {e(sh)}</p>
<div class="tablewrap"><table class="cmp"><thead><tr><th></th><th><a href="../tools/{a}.html">{e(A["name"])}</a></th><th><a href="../tools/{b}.html">{e(Bt["name"])}</a></th></tr></thead><tbody>{rows}
<tr><th>Official site</th><td><a href="{e(A["url"])}" target="_blank" rel="noopener">Visit ↗</a></td><td><a href="{e(Bt["url"])}" target="_blank" rel="noopener">Visit ↗</a></td></tr></tbody></table></div>
<p class="disclose">We don't benchmark tools or rank one above the other here. Check each official site for current pricing and features before you choose.</p>
<p style="margin-top:20px"><a href="index.html">← All comparisons</a></p></section>'''
        ld={"@context":"https://schema.org","@graph":[{"@type":"WebPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B},
            "about":[{"@type":"SoftwareApplication","name":x["name"],"url":x["url"],"applicationCategory":x["category"]} for x in (A,Bt)]},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Compare","item":B+"compare/"},{"@type":"ListItem","position":3,"name":f"{A['name']} vs {Bt['name']}","item":canon}]}]}
        open(f"compare/{s}.html","w").write(shell("../",title,desc,canon,body,ld)); urls.append(canon)
    cards="".join(f'<a class="card" href="{cslug(a,b)}.html"><div class="ct"><h3>{e(bs[a]["name"])} vs {e(bs[b]["name"])}</h3></div><p>{e(bs[a]["category"])}: {e(bs[a]["description"])}</p></a>' for a,b in PAIRS)
    canon=B+"compare/"; title="Compare AI agent tools side by side · AgentScout"; desc="Side-by-side comparisons of closely related AI agent tools: coding agents, frameworks, browser automation, voice, search APIs, no-code builders and observability."
    ld={"@context":"https://schema.org","@type":"CollectionPage","name":title,"description":desc,"url":canon,"hasPart":[{"@type":"WebPage","url":f"{B}compare/{cslug(a,b)}.html","name":f"{bs[a]['name']} vs {bs[b]['name']}"} for a,b in PAIRS]}
    open("compare/index.html","w").write(shell("../",title,desc,canon,f'<div class="crumb"><a href="../index.html">AgentScout</a> / Compare</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">Compare AI agent tools</h1><p class="lede" style="margin-left:0;text-align:left">Closely related tools, side by side, using only facts from our listings.</p><div class="grid">{cards}</div></section>',ld)); urls.insert(0,canon)
    # badges page
    canon=B+"badges.html"; title="AgentScout badges for makers · AgentScout"; desc="Free badges for tools listed or featured on AgentScout. Add one to your README or site; it links back to your tool's page."
    ex=bs["langgraph"]
    body=f'''<div class="crumb"><a href="index.html">AgentScout</a> / Badges</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">Badges for makers</h1>
<p class="lede" style="margin-left:0;text-align:left">If your tool is on AgentScout, you can show it. Badges are free and link to your tool's page, so readers can see how it compares.</p>
<div class="embeds"><div class="embed"><img src="badges/listed-light.svg" alt="Listed on AgentScout (light)" width="220" height="54"><img src="badges/listed-dark.svg" alt="Listed on AgentScout (dark)" width="220" height="54"><p><b>Listed</b>: for any tool in the directory.</p></div>
<div class="embed"><img src="badges/featured-light.svg" alt="Featured on AgentScout (light)" width="220" height="54"><img src="badges/featured-dark.svg" alt="Featured on AgentScout (dark)" width="220" height="54"><p><b>Featured</b>: for tools we've picked as featured.</p></div></div>
<h2 style="font-size:18px;margin:32px 0 8px">How to get your snippet</h2><ol><li>Find your tool in the <a href="index.html#directory">directory</a> and open its page.</li><li>Scroll to "Badge for makers" and copy the HTML or Markdown, in light or dark.</li><li>Paste it into your README, docs or site footer.</li></ol>
<p>Not listed yet? <a href="https://github.com/Clampdown-web/agentscout/issues/new?labels=submission&amp;title=Tool%20submission%3A%20" target="_blank" rel="noopener">Submit your tool</a>. Example from the {e(ex["name"])} page:</p>
{badge_html(ex,"").replace('<a href="../badges.html">About badges</a>','')}
<p class="disclose">Badges are SVG files hosted on this site. Please don't change the wording. Featured placements that are paid are always labeled as sponsored on AgentScout.</p></section>'''
    ld={"@context":"https://schema.org","@type":"WebPage","name":title,"description":desc,"url":canon}
    open("badges.html","w").write(shell("",title,desc,canon,body,ld).replace('href="index.html#','href="index.html#')); urls.insert(0,canon)
    sm=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in [B,B+"llms.txt"]+[f"{B}tools/{x['slug']}.html" for x in t]+urls: sm.append(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>")
    open("sitemap.xml","w").write("\n".join(sm+["</urlset>",""]))
    print(len(PAIRS),"comparisons, badges page, sitemap",len(sm)-2,"urls")
