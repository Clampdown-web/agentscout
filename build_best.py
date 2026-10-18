"""Ranked 'best of' list pages in best/ (Oct 2026 batch) + the best/ hub. Called from build_extras.build().
Ranking uses only directory data: GitHub stars as tracked on each listing, or listing maturity. No invented ratings."""
import re,os,glob,datetime,collections
import build_extras as X
B=X.B; e=X.e
OS={"Open source","Open source + cloud"}
MAT=lambda x:0 if x["maturity"].startswith("Mature") else 1 if x["maturity"].startswith("Active") else 2
def live(x): return "iscontinued" not in x["maturity"]
# slug, h1/title stem, filter, ranking ("stars"|"maturity"), cap, intro, see-also html
PAGES=[
("ai-coding-agents","Best AI Coding Agents",lambda x:x["category"]=="coding","stars",20,
 "AI coding agents, AI editors and CLI coding tools that write, edit and review code for you.",
 '<a href="cursor-alternatives.html">Cursor alternatives</a> · <a href="../tasks/writing-code.html">AI agents for writing code</a> · <a href="../tasks/terminal-coding.html">Coding in the terminal</a>'),
("ai-agent-frameworks","Best AI Agent Frameworks",lambda x:x["category"]=="frameworks","stars",20,
 "Frameworks, SDKs and harnesses developers use to build their own AI agents.",
 '<a href="../tasks/building-ai-agents.html">AI agents for building AI agents</a> · <a href="../tasks/multi-agent-systems.html">Multi-agent systems</a>'),
("ai-browser-agents","Best AI Browser Agents",lambda x:x["category"]=="browser/computer use","stars",20,
 "Agents and libraries that browse websites, fill in forms and control a computer the way a person would.",
 '<a href="../tasks/browsing-the-web.html">AI agents for browsing the web</a> · <a href="../tasks/computer-use.html">Controlling a computer</a>'),
("open-source-mcp-servers","Best Open-Source MCP Servers",lambda x:x["category"]=="MCP & infra" and x["pricing"] in OS,"stars",25,
 "Open-source MCP servers and MCP infrastructure you can run yourself and connect to Claude Code, Cursor, Codex and other MCP clients.",
 '<a href="mcp-servers.html">Best MCP servers (all)</a> · <a href="mcp-servers-for-claude-code.html">for Claude Code</a> · <a href="mcp-servers-for-cursor.html">for Cursor</a> · <a href="mcp-servers-for-codex.html">for Codex</a>'),
("most-starred-open-source-ai-agents","Most-Starred Open-Source AI Agent Projects",lambda x:x["pricing"] in OS|{"Open weights","Open standard"},"stars",25,
 "The open-source AI agent projects in our directory with the most GitHub stars, across every category.",
 '<a href="../tasks/open-source-agents.html">Open-source agents by task</a> · <a href="self-hosted-ai-agents.html">Self-hosted AI agents</a>'),
("self-hosted-ai-agents","Best Self-Hosted AI Agents",lambda x:x["audience"]=="ready to use" and x["pricing"] in OS,"stars",20,
 "Ready-to-use AI agent apps that are open source, so you can run them on your own computer or server instead of only in someone else's cloud.",
 '<a href="../tasks/running-agents-locally.html">AI agents for running agents locally</a> · <a href="free-ai-agents.html">Free AI agents (free plans)</a>'),
("free-ai-agents","Best Free AI Agents (Free Plans)",lambda x:x["audience"]=="ready to use" and x["pricing"]=="Freemium","maturity",20,
 "Ready-to-use AI agents whose makers list a free plan (freemium), so you can try them before paying.",
 '<a href="self-hosted-ai-agents.html">Self-hosted AI agents (open source)</a> · <a href="personal-ai-agents.html">Personal AI agents</a>'),
("no-code-ai-agent-builders","Best No-Code AI Agent Builders",lambda x:x["category"] in ("no-code builders","app builders"),"stars",20,
 "Visual, drag-and-drop and prompt-to-app builders for making AI agents and apps without writing code.",
 '<a href="../tasks/building-apps-without-code.html">Building apps without code</a> · <a href="../tasks/automating-workflows.html">Automating workflows</a>'),
("ai-voice-agent-platforms","Best AI Voice Agent Platforms",lambda x:x["category"]=="voice","stars",20,
 "Platforms and open-source frameworks for building AI voice agents that talk, listen and handle phone calls.",
 '<a href="../tasks/building-voice-agents.html">Building voice agents</a> · <a href="../tasks/phone-calls.html">Handling phone calls</a> · <a href="../compare/livekit-agents-vs-pipecat.html">LiveKit Agents vs Pipecat</a>'),
("ai-vision-tools","Best AI Vision Tools for Agents",lambda x:x["category"]=="vision","stars",20,
 "Computer vision tools, image and video agents, and vision MCP servers that let AI agents see and understand images and video.",
 '<a href="../tasks/making-images-and-design.html">Images and design</a> · <a href="../generate.html">Free AI image generator</a>'),
("ai-agent-observability-tools","Best AI Agent Observability & Eval Tools",lambda x:x["category"]=="evals & observability","stars",20,
 "Tracing, evaluation, guardrail and monitoring tools for seeing what your AI agents do and checking that they work.",
 '<a href="../tasks/monitoring-agents.html">Monitoring agents in production</a> · <a href="../tasks/evaluating-agents.html">Evaluating agents</a> · <a href="../compare/langfuse-vs-langsmith.html">Langfuse vs LangSmith</a>'),
("personal-ai-agents","Best Personal AI Agents",lambda x:x["category"]=="personal agents","stars",20,
 "Personal AI agents and assistants that work for you directly: chat apps, desktop assistants and always-on helpers.",
 '<a href="../tasks/personal-assistants.html">AI agents for personal assistance</a> · <a href="../tasks/chat-apps.html">Agents in chat apps</a>'),
("ai-business-agents","Best AI Agents for Business Teams",lambda x:x["category"]=="business agents","maturity",20,
 "Ready-made AI agents for business work: operations, finance, support, sales and back-office tasks.",
 '<a href="../tasks/business-automation.html">Running business operations</a> · <a href="../tasks/customer-support.html">Customer support</a> · <a href="../tasks/sales-outreach.html">Sales outreach</a>'),
("crypto-ai-agents","Best Crypto AI Agents",lambda x:x["category"]=="crypto","maturity",20,
 "AI agents, MCP servers and toolkits for crypto: on-chain data, wallets, DeFi and research. None of this is financial advice.",
 '<a href="../tasks/crypto-and-wallets.html">Crypto and wallets</a> · <a href="../tasks/trading.html">Trading</a> · <a href="../tasks/smart-contract-security.html">Smart contract security</a>'),
("ai-productivity-tools","Best AI Productivity Agents",lambda x:x["category"]=="productivity","stars",20,
 "AI agents and tools for everyday productivity: documents, diagrams, spreadsheets, video and design work.",
 '<a href="../tasks/spreadsheets-and-slides.html">Spreadsheets, slides and docs</a> · <a href="../tasks/documents.html">Working with documents</a>'),
]
OLD=[("mcp-servers","Best MCP Servers"),("mcp-servers-for-claude-code","Best MCP servers for Claude Code"),("mcp-servers-for-cursor","Best MCP servers for Cursor"),("mcp-servers-for-codex","Best MCP servers for Codex"),("cursor-alternatives","Cursor alternatives")]
def rank(items,how):
    st=lambda x:-(x.get("github_stars") or 0)
    has=lambda x:x.get("github_stars") is None
    if how=="stars": return sorted(items,key=lambda x:(has(x),st(x),x["name"].lower()))
    return sorted(items,key=lambda x:(MAT(x),has(x),st(x),x["name"].lower()))
def method(how,asof):
    if how=="stars": return f"Ranked by GitHub stars as recorded on each AgentScout listing (link checks {asof}). Tools without a tracked public repo come after, in alphabetical order. Stars measure developer popularity, not quality or fit for your job, so read each listing before you choose. No paid placements."
    return "Most tools here are commercial products without public GitHub repos, so we rank by the maturity stated on each listing: Mature first, then Active, then newer launches. Within each group, tools with more tracked GitHub stars come first, then alphabetical order. This is not a quality score. No paid placements."
def item(i,x):
    gs=f'<span class="b">★ {x["github_stars"]:,} GitHub stars</span>' if x.get("github_stars") is not None else ""
    return (f'<li class="card tile" style="list-style:none"><a class="stretch" href="../tools/{x["slug"]}.html" aria-label="{e(x["name"])}"></a><div class="ct">{X.ico(x)}<div class="tn"><h3>{i}. {e(x["name"])}</h3><div class="badges">'
            f'<a class="b cat has-cico" href="../categories/{X.catslug(x["category"])}.html">{X.cico(x["category"])}{e(x["category"])}</a><span class="b">{e(x["pricing"])}</span>{gs}</div></div></div>'
            f'<p class="hook">{e(x["description"])}</p><p class="muted" style="font-size:12.5px;flex:0">Pricing (as stated): {e(x.get("pricing_detail") or x["pricing"])} · {e(x["maturity"])}</p></li>')
def page(t,P,asof):
    s,h,f,how,cap,intro,see=P
    allm=[x for x in t if f(x) and live(x)]; items=rank(allm,how)[:cap]
    path=f"best/{s}.html"; canon=B+path; title=f"{h} in 2026 · AgentScout"
    top=", ".join(x["name"] for x in items[:3])
    desc=f"{h} in 2026: top {len(items)} from AgentScout's link-checked directory, including {top}. Ranking method stated; pricing as makers state it."
    if len(desc)>158: desc=f"{h} (2026): top {len(items)}, including {top}. Ranking method stated; pricing as stated."[:158]
    cats=collections.Counter(x["category"] for x in allm).most_common()
    catl="".join(f'<a class="b uc has-cico" href="../categories/{X.catslug(c)}.html">{X.cico(c)}{e(c)} ({n})</a>' for c,n in cats)
    more=f"the top {len(items)} of {len(allm)} matching tools" if len(allm)>len(items) else f"all {len(items)} matching tools"
    others=" · ".join(f'<a href="{p[0]}.html">{e(p[1])}</a>' for p in PAGES if p[0]!=s)
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
        {"@type":"ItemList","name":h,"itemListOrder":"https://schema.org/ItemListOrderDescending","numberOfItems":len(items),"itemListElement":[{"@type":"ListItem","position":i+1,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate(items)]},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Best lists","item":B+"best/"},{"@type":"ListItem","position":3,"name":h,"item":canon}]}]}
    body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">Best lists</a> / {e(h)}</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">{e(h)} (2026)</h1>'
          f'<p class="lede" style="margin-left:0;text-align:left">{e(intro)} Below are {more} in the AgentScout directory, ranked.</p>'
          f'<p class="muted" style="margin:0 0 18px"><strong>How we ranked:</strong> {method(how,asof)}</p>'
          f'<ol class="grid" style="padding:0;margin:0">{"".join(item(i+1,x) for i,x in enumerate(items))}</ol>'
          f'<h2 style="font-size:16px;margin:32px 0 10px">Browse by category</h2><div class="badges">{catl}</div>'
          f'<p style="margin-top:24px">Related: {see}</p><p style="margin-top:12px">More best-of lists: <a href="index.html">All best lists</a> · {others}</p>'
          f'<p class="disclose">Facts come from our directory listings; pricing is as each maker states it and GitHub stars are as recorded on each listing. Check official sites before you choose.</p></section>')
    open(path,"w").write(X.shell("../",title,desc,canon,body,ld)); return canon,h,len(items)
def hub(t,made):
    canon=B+"best/"; title="Best AI Agent Tools Lists (2026) · AgentScout"
    desc=f"{len(made)+len(OLD)} ranked and curated best-of lists from AgentScout: coding agents, agent frameworks, MCP servers, browser, voice, crypto and free AI agents."
    tiles="".join(f'<a class="card" href="{s}.html"><div class="ct"><h3>{e(h)}</h3></div><p>Top {n}, ranked</p></a>' for _,h,n,s in made)
    old="".join(f'<a class="card" href="{s}.html"><div class="ct"><h3>{e(h)}</h3></div><p>Curated list</p></a>' for s,h in OLD)
    ld={"@context":"https://schema.org","@type":"CollectionPage","name":title,"description":desc,"url":canon,"hasPart":[{"@type":"WebPage","name":h,"url":u} for u,h,_,_ in made]+[{"@type":"WebPage","name":h,"url":f"{B}best/{s}.html"} for s,h in OLD]}
    body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / Best lists</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">Best AI agent tools lists (2026)</h1>'
          f'<p class="lede" style="margin-left:0;text-align:left">Ranked lists built from the AgentScout directory. Each list says how it is ranked (GitHub stars or listing maturity). We use no invented scores and sell no placements.</p>'
          f'<h2 style="font-size:16px;margin:24px 0 10px">Ranked lists</h2><div class="grid">{tiles}</div><h2 style="font-size:16px;margin:32px 0 10px">MCP and coding guides</h2><div class="grid">{old}</div>'
          f'<p style="margin-top:24px">See also: <a href="../tasks/index.html">AI agents by task</a> · <a href="../categories/index.html">All categories</a> · <a href="../compare/index.html">Comparisons</a></p></section>')
    open("best/index.html","w").write(X.shell("../",title,desc,canon,body,ld)); return canon
def link_in(path,anchor,add,marker):
    if not os.path.exists(path): return
    s=open(path).read()
    if marker in s or anchor not in s: return
    open(path,"w").write(s.replace(anchor,anchor+add,1))
def pages(t):
    os.makedirs("best",exist_ok=True)
    asof=max(x["verified"] for x in t)
    made=[]
    for P in PAGES:
        u,h,n=page(t,P,asof); made.append((u,h,n,P[0]))
    urls=[hub(t,made)]+[m[0] for m in made]
    # link from where best/ pages are already listed (additive)
    link_in("index.html",'<a href="best/cursor-alternatives.html">Cursor alternatives 2026</a>',' · <a href="best/index.html">All best lists</a> · '+" · ".join(f'<a href="best/{s}.html">{e(h)}</a>' for _,h,_,s in made),'href="best/index.html"')
    link_in("best/mcp-servers.html",'Guides by client: ','<a href="index.html">All best lists</a> · <a href="open-source-mcp-servers.html">Best open-source MCP servers</a> · ','href="open-source-mcp-servers.html"')
    link_in("best/cursor-alternatives.html",'<a href="../compare/cursor-vs-windsurf.html">Cursor vs Windsurf</a>','. More: <a href="ai-coding-agents.html">Best AI coding agents (ranked)</a> · <a href="index.html">All best lists</a>','href="ai-coding-agents.html"')
    link_in("llms.txt",f'- [Cursor alternatives 2026]({B}best/cursor-alternatives.html)',"\n"+f"- [All best-of lists]({B}best/)\n"+"\n".join(f"- [{h} 2026]({u})" for u,h,_,_ in made),f"]({B}best/)")
    print("best-of:",len(made),"new ranked pages +hub;",len(glob.glob("best/*.html"))-1,"best pages total")
    return urls
