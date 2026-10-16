"""Task pages (/tasks/), submit page, and sitewide nav/footer/newsletter injection. Called from build_extras/build_site; reads tools at build time."""
import re,os,json,glob,urllib.parse
from build_extras import e,B,shell,card
# (slug, label, categories, use_cases, keyword regex over name+description, intro)
TASKS=[
("writing-code","writing code",{"coding"},{"write code"},r"\bcoding agent|\bwrites? code|code generation|pair program","Coding agents that write, edit and refactor code from plain-language requests, in your terminal, editor or browser."),
("reviewing-pull-requests","reviewing pull requests",set(),set(),r"pull request|\bPRs?\b|code review|review(s|ing)? code","Agents that read diffs, leave review comments and catch bugs before a pull request is merged."),
("terminal-coding","coding in the terminal",set(),set(),r"\bCLI\b|terminal|command[- ]line|shell","Agents that live in your terminal: give them a task and they read files, run commands and propose changes."),
("browsing-the-web","browsing the web",{"browser/computer use"},{"automate the browser"},r"\bbrowser\b|web navigation|headless","Agents that open pages, click, type and fill in forms in a real browser so you don't have to."),
("computer-use","controlling a computer",set(),{"control a computer"},r"computer use|computer-use|desktop agent|operate (a|your) computer","Agents that see the screen and use the mouse and keyboard to work across desktop apps."),
("web-scraping","scraping websites",set(),set(),r"scrap|crawl|extract(s|ing)? (data|content)|web data","Tools that turn websites into clean data or text an agent can use, from single pages to whole sites."),
("automating-workflows","automating workflows",{"no-code builders"},{"automate workflows"},r"workflow|automat","Platforms for chaining apps, triggers and AI steps into workflows that run on their own."),
("building-apps-without-code","building apps without code",{"app builders"},{"build apps without code"},r"no-code|without code|app builder|prompt to app","Builders that turn a description into a working app or site, no coding required."),
("building-ai-agents","building AI agents",{"frameworks"},{"build an agent"},r"framework|\bSDK\b|agent development kit","Frameworks and SDKs for developers building their own agents, with tools, state and orchestration built in."),
("multi-agent-systems","building multi-agent systems",set(),{"build multi-agent systems"},r"multi-agent|crew|swarm|subagent|orchestrat","Frameworks for teams of agents that hand work to each other, split tasks and check each other's output."),
("building-voice-agents","building voice agents",{"voice"},{"voice & phone calls"},r"\bvoice\b|speech|phone call","Platforms for agents that talk: phone lines, voice assistants and real-time speech in and out."),
("phone-calls","handling phone calls",set(),set(),r"phone|call center|inbound call|outbound call|telephon","Voice agents that answer and place phone calls, book appointments and route callers."),
("customer-support","customer support",set(),{"sales & support"},r"support|helpdesk|help desk|customer service|ticket","Agents that answer customer questions, resolve tickets and hand off to people when needed."),
("sales-outreach","sales outreach",set(),set(),r"\bsales\b|outreach|\bSDR\b|lead|prospect|\bCRM\b","Agents that find leads, write outreach and keep your pipeline moving."),
("writing-emails","writing and managing email",set(),set(),r"\bemails?\b|inbox|gmail","Assistants that draft replies, sort your inbox and follow up so email takes less of your day."),
("business-automation","running business operations",{"business agents"},{"business agents"},r"enterprise|back office|operations|business process","Ready-made agents for business teams: operations, finance, HR and other repeatable work."),
("personal-assistants","personal assistance",{"personal agents"},{"personal agents"},r"personal (assistant|agent)|your (day|life)|always-on","Personal agents that run errands online, keep track of tasks and act on your behalf."),
("research","research",{"research"},{"research the web"},r"research|cited|citation|papers","Agents that search, read many sources and come back with a cited answer or report."),
("searching-the-web","web search for agents",set(),set(),r"search API|web search|search engine|retriev","Search APIs and engines built for agents, returning clean results an LLM can use directly."),
("reading-papers","reading scientific papers",set(),set(),r"papers|scientific|academic|literature","Research assistants for academic work: finding papers, summarizing them and extracting findings."),
("data-analysis","data analysis",set(),set(),r"\bdata\b|analytic|spreadsheet|\bSQL\b|dashboard","Agents that query, clean and chart data and explain what it shows."),
("documents","working with documents",set(),set(),r"document|\bPDF|\bRAG\b|knowledge base","Tools that let agents read, search and answer questions over your documents and files."),
("connecting-tools-mcp","connecting tools with MCP",set(),{"connect tools via MCP"},r"\bMCP\b|Model Context Protocol","MCP servers, clients and registries that give agents safe access to your apps and data."),
("building-mcp-servers","building MCP servers",set(),set(),r"MCP server|build(ing)? MCP|MCP SDK|MCP framework|registry","Tools and SDKs for building, hosting and publishing your own MCP servers."),
("agent-memory","memory for agents",set(),{"give agents memory"},r"\bmemory\b|remember|long-term|stateful","Memory layers that let agents remember users, past conversations and facts across sessions."),
("evaluating-agents","evaluating agents",{"evals & observability"},{"monitor & evaluate agents"},r"\beval|benchmark|test(s|ing)? (agents|LLM)","Evaluation tools for scoring agent outputs, catching regressions and comparing prompts and models."),
("monitoring-agents","monitoring agents in production",set(),set(),r"observab|tracing|traces|monitor|logging","Observability for agents in production: traces, costs, latency and errors in one place."),
("running-code-safely","running code safely",set(),{"run code safely"},r"sandbox|isolated|secure (runtime|execution)|microVM","Sandboxes that let agents run code and tools in isolation, away from your machine and data."),
("agent-security","agent security and safety",set(),set(),r"secur|safety|guardrail|permission|policy|governance","Guardrails, policies and monitoring that keep agents from doing what they shouldn't."),
("testing-apps","testing apps",set(),set(),r"\bQA\b|\btest(s|ing)?\b|end-to-end|\bE2E\b","Agents that write and run tests, click through your app and report what breaks."),
("making-videos","making videos",set(),set(),r"video","AI agents and tools that script, edit or generate video."),
("making-images-and-design","images and design",{"vision"},{"computer vision","make diagrams"},r"\bimage|design|diagram|vision|visual","Agents for visual work: generating images, diagrams and designs, or understanding what's in a picture."),
("crypto-and-wallets","crypto and wallets",set(),set(),r"crypto|wallet|blockchain|onchain|stablecoin|x402|web3","Wallets, payment rails and tools that let agents hold funds and pay for things on their own."),
("agent-payments","agent payments",set(),set(),r"payment|pay for|checkout|billing|x40[12]","Tools that let agents pay, get paid and handle checkout without a human clicking buy."),
("deploying-agents","deploying and hosting agents",set(),set(),r"\bdeploy(s|ing)? (\w+ ){0,3}agents\b|\bagent (hosting|runtime|cloud)\b|\bhost(s|ing)? (AI )?agents\b|\bagents? in production\b|\bserverless\b","Infrastructure for running agents in production: hosting, scaling and serverless runtimes."),
("open-source-agents","open-source agents",set(),set(),r"\bopen[- ]source (\w+[- ]){0,2}(AI )?(agent|assistant)s?\b(?! (framework|platform|SDK|library|memory|infrastructure))","Open-source agents you can run yourself, inspect and extend, from coding agents to personal assistants."),
]
def match(x,T):
    _,_,cats,ucs,rx,_=T
    if x.get("category") in cats or set(x.get("use_cases",[]))&ucs: return True
    return bool(re.search(rx,f'{x.get("name","")} {x.get("description","")} {x.get("pricing","")}',re.I))
def mapping(t):
    m={}
    for T in TASKS:
        items=[x for x in t if match(x,T)]
        if len(items)>=3:
            items.sort(key=lambda x:(not x.get("featured"),x.get("category") not in T[2],not (set(x.get("use_cases",[]))&T[3]),-(x.get("github_stars") or 0),x["name"].lower()))
            m[T[0]]=(T,items)
    return m
def tasks_for(x,m): return [T for s,(T,items) in m.items() if x in items]
def pages(t):
    os.makedirs("tasks",exist_ok=True); m=mapping(t); urls=[]
    for f in glob.glob("tasks/*.html"):
        if os.path.basename(f)!="index.html" and os.path.basename(f)[:-5] not in m: os.remove(f)
    for s,(T,items) in m.items():
        _,label,_,_,_,intro=T; n=len(items); canon=f"{B}tasks/{s}.html"
        h1=f"Best AI agents for {label} (2026)"
        title=f"Best AI Agents for {label.title()} (2026) · AgentScout"
        desc=f"Compare {n} AI agents and tools for {label}, including {', '.join(x['name'] for x in items[:3])}. Link-checked, with pricing as makers state it."[:158]
        rel=[(s2,T2) for s2,(T2,i2) in m.items() if s2!=s and len(set(id(a) for a in i2)&set(id(a) for a in items))>=2]
        rel=sorted(rel,key=lambda r:-len(set(id(a) for a in m[r[0]][1])&set(id(a) for a in items)))[:8]
        relh='<h2 style="font-size:16px;margin:32px 0 10px">Related tasks</h2><div class="badges">'+"".join(f'<a class="b uc" href="{s2}.html">{e(T2[1].capitalize())}</a>' for s2,T2 in rel)+'<a class="b uc" href="index.html">All tasks →</a></div>'
        body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">Tasks</a> / {e(label.capitalize())}</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">{e(h1)}</h1>'
              f'<p class="lede" style="margin-left:0;text-align:left">{e(intro)} We list {n} tools for {e(label)} below, each with a link-checked page, pricing as the maker states it and alternatives.</p>'
              f'<div class="grid">{"".join(card(x) for x in items)}</div>{relh}<p class="disclose">Tools are matched to tasks by category, use cases and what each tool says it does. Missing one? <a href="../submit.html">Submit it free</a>.</p></section>')
        ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":h1,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
            {"@type":"ItemList","numberOfItems":n,"itemListElement":[{"@type":"ListItem","position":i+1,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate(items)]},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Tasks","item":B+"tasks/index.html"},{"@type":"ListItem","position":3,"name":label.capitalize(),"item":canon}]}]}
        open(f"tasks/{s}.html","w").write(shell("../",title,desc,canon,body,ld)); urls.append(canon)
    canon=B+"tasks/index.html"; title=f"AI Agents by Task: {len(m)} Jobs, Best Tools for Each · AgentScout"
    desc=f"Find the best AI agents for {len(m)} tasks, from writing code and browsing the web to voice agents, research and customer support."[:158]
    tiles="".join(f'<a class="card" href="{s}.html"><div class="ct"><h3>{e(T[1].capitalize())}</h3></div><p>{len(items)} tools · {e(", ".join(x["name"] for x in items[:3]))}</p></a>' for s,(T,items) in sorted(m.items(),key=lambda kv:kv[1][0][1]))
    body=f'<div class="crumb"><a href="../index.html">AgentScout</a> / Tasks</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">AI agents by task</h1><p class="lede" style="margin-left:0;text-align:left">Start from the job you need done. {len(m)} tasks, each with the agent tools that handle it.</p><div class="grid">{tiles}</div></section>'
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":"AI agents by task","description":desc,"url":canon},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Tasks","item":canon}]}]}
    open("tasks/index.html","w").write(shell("../",title,desc,canon,body,ld)); urls.insert(0,canon)
    urls.append(submit_page(t)); return urls
def submit_page(t):
    canon=B+"submit.html"; cats=sorted({x["category"] for x in t}); title="Submit an AI Agent Tool Free · AgentScout"
    desc="Submit your AI agent tool to AgentScout for free. We review every submission, write the listing ourselves and link-check it."
    inp='style="width:100%;height:44px;padding:0 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text);font:inherit;box-sizing:border-box"'
    def f(id,label,typ="text",req=True,extra=""): return f'<label style="display:block;margin:14px 0 6px;font-weight:600;font-size:14px" for="{id}">{label}{"" if req else " <span style=\"color:var(--faint);font-weight:400\">(optional)</span>"}</label><input id="{id}" name="{id}" type="{typ}" {"required" if req else ""} {extra} {inp}>'
    opts="".join(f'<option>{e(c)}</option>' for c in cats)+"<option>other</option>"
    form=(f'<form id="sf" style="max-width:560px;text-align:left" novalidate>'+f("name","Tool name",extra='maxlength="80"')+f("website","Website","url",extra='placeholder="https://" maxlength="300"')+f("github","GitHub repo","url",False,'placeholder="https://github.com/…" maxlength="300"')
          +f'<label style="display:block;margin:14px 0 6px;font-weight:600;font-size:14px" for="category">Category</label><select id="category" name="category" {inp}>{opts}</select>'
          +f'<label style="display:block;margin:14px 0 6px;font-weight:600;font-size:14px" for="pricing">Pricing</label><select id="pricing" name="pricing" {inp}><option>Open source</option><option>Free</option><option>Freemium</option><option>Paid</option><option>Open source + cloud</option><option>Enterprise / contact sales</option></select>'
          +f'<label style="display:block;margin:14px 0 6px;font-weight:600;font-size:14px" for="desc">Short description</label><textarea id="desc" name="desc" required maxlength="500" rows="3" style="width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text);font:inherit;box-sizing:border-box"></textarea>'
          +f("email","Your email (maker)","email",extra='maxlength="120"')+f("x","X handle","text",False,'placeholder="@yourhandle" maxlength="30"')
          +'<div aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden"><label for="company">Company (leave empty)</label><input id="company" name="company" type="text" tabindex="-1" autocomplete="off"></div><p id="serr" role="alert" style="color:#e5484d;min-height:20px;margin:12px 0 0;font-size:14px"></p><button class="btn primary" type="submit" style="height:46px;margin-top:6px">Submit for free review</button></form>'
          +'<div id="sdone" hidden style="max-width:560px;text-align:left;border:1px solid var(--accent);border-radius:12px;padding:18px;margin-top:8px"><b>Thanks, your submission is in.</b> We\'ll review it, usually within a few days. Questions? Email <a href="mailto:agentscout@mail.grokbot.com">agentscout@mail.grokbot.com</a>.<p style="margin:10px 0 0">While you wait, grab a <a href="badges.html#featured-badge">Featured on AgentScout badge</a> for your site or README.</p></div>')
    js=r'''<script>var SUBMIT_URL="https://agentscout-image.agentscouthq.workers.dev/submit";(function(){var f=document.getElementById("sf"),er=document.getElementById("serr");function v(id){return document.getElementById(id).value.trim()}
function okUrl(u,gh){try{var x=new URL(u);return(x.protocol==="https:"||x.protocol==="http:")&&(!gh||/(^|\.)github\.com$/.test(x.hostname))}catch(e){return false}}
f.addEventListener("submit",function(e){e.preventDefault();var n=v("name"),w=v("website"),g=v("github"),d=v("desc"),m=v("email"),x=v("x").replace(/^@/,"");
var bad=!n?"Please add the tool name.":!okUrl(w)?"Please add a full website link starting with https://":(g&&!okUrl(g,1))?"The GitHub link should be a github.com URL.":!d?"Please add a short description.":!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(m)?"Please add a valid email.":(x&&!/^[A-Za-z0-9_]{1,15}$/.test(x))?"X handles use letters, numbers and _ only.":"";
er.textContent=bad;if(bad)return;
var body="Tool name: "+n+"\nWebsite: "+w+"\nGitHub: "+(g||"-")+"\nCategory: "+v("category")+"\nPricing: "+v("pricing")+"\nDescription: "+d+"\nMaker email: "+m+"\nX: "+(x?"@"+x:"-")+"\n";
var mail="mailto:agentscout@mail.grokbot.com?subject="+encodeURIComponent("Tool submission: "+n)+"&body="+encodeURIComponent(body);document.getElementById("smail").href=mail;
var btn=f.querySelector("button[type=submit]");btn.disabled=true;btn.textContent="Sending…";
fetch(SUBMIT_URL,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:n,website:w,github:g,category:v("category"),pricing:v("pricing"),desc:d,email:m,x:x,company:v("company")})}).then(function(r){return r.json().catch(function(){return{}}).then(function(j){if(!r.ok||!j.ok)throw new Error(j.error||"Something went wrong.");f.hidden=true;document.getElementById("sdone").hidden=false;})}).catch(function(e){er.innerHTML="";er.appendChild(document.createTextNode((e&&e.message&&e.message!=="Failed to fetch"?e.message:"We couldn't send it right now.")+" "));var a=document.createElement("a");a.href=mail;a.textContent="Send it by email instead";er.appendChild(a);}).finally(function(){btn.disabled=false;btn.textContent="Submit for free review";});})})()</script>'''
    body=(f'<div class="crumb"><a href="index.html">AgentScout</a> / Submit a tool</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">Submit your AI agent tool</h1>'
          '<p class="lede" style="margin-left:0;text-align:left">Listing on AgentScout is free. We review every submission, check the links and write the description ourselves in plain words, so you don\'t need marketing copy. Sponsored placements are separate and always labeled.</p>'
          f'{form}<p class="disclose" style="max-width:560px">Submissions go straight to the AgentScout team. Prefer email? <a id="smail" href="mailto:agentscout@mail.grokbot.com?subject=Tool%20submission">Send it from your email app instead</a>. After you\'re listed, add a <a href="badges.html">free AgentScout badge</a>.</p></section>{js}')
    ld={"@context":"https://schema.org","@type":"WebPage","name":title,"description":desc,"url":canon}
    open("submit.html","w").write(shell("",title,desc,canon,body,ld)); return canon
NL='<section id="nlblock" class="band" style="border-bottom:0;padding:32px 0"><div class="wrap" style="text-align:center;max-width:620px"><h2 style="font-size:18px;margin:0 0 6px">Get the best new AI agents, weekly</h2><p style="margin:0 0 14px;color:var(--muted)">One short email with new tools, launches and what\'s worth trying. Free, unsubscribe anytime.</p><form class="sub" action="https://agentscout.beehiiv.com/subscribe" method="get" target="_blank" rel="noopener noreferrer" style="max-width:460px;margin:0 auto"><label for="nl-email" class="hide" style="position:absolute;left:-9999px">Email</label><input id="nl-email" type="email" name="email" placeholder="you@example.com" required autocomplete="email"><button class="btn primary" type="submit">Subscribe</button></form></div></section>\n'
ASSET_V="202610162240"  # bump when app.js/styles.css change
SKIP={"og.html","outreach-tracker.html","detail.tpl.html"}
def sitewide(t):
    m=mapping(t); bys={x["slug"]:x for x in t}
    for f in glob.glob("**/*.html",recursive=True):
        if os.path.basename(f) in SKIP or f.startswith(("node_modules","app/")): continue
        s=open(f).read(); o=s
        d="/agentscout/" if f=="404.html" else "../"*f.count("/")
        s=re.sub(r'<a([^>]*?) href="https://github\.com/Clampdown-web/agentscout/issues/new\?[^"]*?[Ss]ubmission[^"]*"(?: target="_blank")?(?: rel="noopener(?: noreferrer)?")?',lambda mm:f'<a{mm.group(1)} href="{d}submit.html"',s)
        s=re.sub(r'(<div class="links"><a href="[^"]*categories/index\.html">Categories</a>)(?!<a href="[^"]*tasks/)',lambda mm:mm.group(1)+f'<a href="{d}tasks/index.html">Tasks</a>',s)
        s=re.sub(r'(<p><a href="[^"]*categories/index\.html">Categories</a>)(?! · <a href="[^"]*tasks/)',lambda mm:mm.group(1)+f' · <a href="{d}tasks/index.html">AI agents by task</a>',s)
        s=s.replace("form-action 'self'\"","form-action 'self' https://agentscout.beehiiv.com\"")
        if 'id="nlblock"' not in s and "<footer" in s: s=s.replace("<footer",NL+"<footer",1)
        if f.startswith("tools/"):
            x=bys.get(os.path.basename(f)[:-5]); s=re.sub(r'<p class="goodfor".*?</p>','',s)
            ts=tasks_for(x,m) if x else []
            if ts: s=s.replace('style="display:contents"></span></div>','style="display:contents"></span></div><p class="goodfor" style="margin:-12px 0 24px;font-size:14px;color:var(--muted)">Good for: '+", ".join(f'<a href="../tasks/{T[0]}.html">{e(T[1])}</a>' for T in ts[:8])+'</p>',1)
        s=re.sub(r'(app\.js|styles\.css)\?v=\d+',lambda mm:mm.group(1)+"?v="+ASSET_V,s)
        if s!=o: open(f,"w").write(s)
