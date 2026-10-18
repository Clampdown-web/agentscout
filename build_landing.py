"""Search landing pages (s/) and job-role pages (for/), Oct 18 2026. Called from build_extras.build().
Every list is built from tools.json at build time (category, pricing as the maker states it, use cases and task matching
from build_tasks). Ranking uses only directory data: tracked GitHub stars, then listing maturity. No invented scores."""
import os,re,glob,collections
import build_extras as X, build_tasks as T, build_best as BB
B=X.B; e=X.e
OS={"Open source","Open source + cloud"}
FREE=OS|{"Freemium","Free","Open weights","Open standard"}
def isfree(x): return x["pricing"] in FREE or bool(X.FREE_RE.search(x.get("pricing_detail") or ""))
def live(x): return BB.live(x)
def rank(items):
    return sorted(items,key=lambda x:(x.get("github_stars") is None,-(x.get("github_stars") or 0),BB.MAT(x),x["name"].lower()))
D=lambda x:x["name"]+" "+x["description"]
UC=lambda x,u:u in x.get("use_cases",[])
# Tighter checks on top of build_tasks matching, so broad keyword hits (e.g. "supports", "leaderboard") don't leak in
REFINE={
 "customer-support":lambda x:bool(re.search(r"customer|helpdesk|help desk|ticket|support (team|agent|inbox)",D(x),re.I)),
 "sales-outreach":lambda x:(bool(re.search(r"\bsales\b|outreach|\bSDR\b|prospect|\bCRM\b|\bleads?\b(?!erboard)",D(x),re.I)) or UC(x,"sales & support")) and "eaderboard" not in x["name"],
 "monitoring-agents":lambda x:x["category"]=="evals & observability" or bool(re.search(r"observab|tracing|traces",D(x),re.I)),
 "evaluating-agents":lambda x:x["category"]=="evals & observability" or UC(x,"monitor & evaluate agents"),
 "research":lambda x:x["category"]=="research" or UC(x,"research the web"),
 "searching-the-web":lambda x:bool(re.search(r"search API|web search|search engine|SERP",D(x),re.I)),
 "automating-workflows":lambda x:x["category"]=="no-code builders" or UC(x,"automate workflows"),
 "computer-use":lambda x:x["category"]=="browser/computer use" or UC(x,"control a computer") or bool(re.search(r"computer[- ]use",D(x),re.I)),
 "running-code-safely":lambda x:UC(x,"run code safely") or bool(re.search(r"sandbox|microVM|isolated",D(x),re.I)),
 "testing-apps":lambda x:bool(re.search(r"(?<!back)\btest(s|ing)?\b|\bQA\b|\bE2E\b|end-to-end",x["description"],re.I)) and x["category"]!="crypto",
 "agent-memory":lambda x:UC(x,"give agents memory") or bool(re.search(r"\bmemory\b",D(x),re.I)),
}
def tm(m):
    """build_tasks mapping with REFINE applied: {task: (T, items)}"""
    return {k:(Tk,[x for x in it if REFINE.get(k,lambda x:True)(x)]) for k,(Tk,it) in m.items()}
# slug, h1, short query label, filter(x,inT), intro, related (task slug, best slug or None)
S=[
("free-ai-coding-agents","Free AI coding agents","free AI coding agents",lambda x,k:x["category"]=="coding" and isfree(x),"AI coding agents, editors and CLIs you can start using without paying: open-source projects plus tools with a free plan.","writing-code","ai-coding-agents"),
("open-source-ai-coding-agents","Open-source AI coding agents","open-source AI coding agents",lambda x,k:x["category"]=="coding" and x["pricing"] in OS,"Coding agents whose source code is public, so you can read it, self-host it and bring your own model API key.","writing-code","ai-coding-agents"),
("terminal-ai-coding-agents","AI coding agents for the terminal (CLI)","terminal AI coding agents",lambda x,k:x["category"]=="coding" and k("terminal-coding"),"Coding agents that run in your terminal: they read files, run commands and propose changes from a prompt.","terminal-coding","ai-coding-agents"),
("ai-code-review-tools","AI code review tools for pull requests","AI code review tools",lambda x,k:k("reviewing-pull-requests"),"Agents and bots that read pull-request diffs, leave review comments and catch bugs before merge.","reviewing-pull-requests",None),
("open-source-browser-agents","Open-source browser agents","open-source browser agents",lambda x,k:(x["category"]=="browser/computer use" or k("browsing-the-web")) and x["pricing"] in OS,"Open-source libraries and agents that drive a real browser: clicking, typing, filling forms and extracting data.","browsing-the-web","ai-browser-agents"),
("free-browser-automation-agents","Free AI browser automation tools","free AI browser automation",lambda x,k:(x["category"]=="browser/computer use" or k("browsing-the-web")) and isfree(x),"Browser and computer-use agents you can try for free, from open-source libraries to hosted tools with free tiers.","browsing-the-web","ai-browser-agents"),
("computer-use-agents","AI computer-use agents","computer-use agents",lambda x,k:k("computer-use"),"Agents that look at the screen and use the mouse and keyboard to work across desktop apps and websites.","computer-use","ai-browser-agents"),
("open-source-ai-agent-frameworks","Open-source AI agent frameworks","open-source AI agent frameworks",lambda x,k:x["category"]=="frameworks" and x["pricing"] in OS,"Frameworks and SDKs for building your own agents, with public source code you can inspect and extend.","building-ai-agents","ai-agent-frameworks"),
("python-ai-agent-frameworks","Python AI agent frameworks","Python AI agent frameworks",lambda x,k:x["category"]=="frameworks" and re.search(r"\bPython\b",x["description"]+" "+x["name"]),"Agent frameworks and SDKs whose listings say they are built for Python.","building-ai-agents","ai-agent-frameworks"),
("typescript-ai-agent-frameworks","TypeScript and JavaScript AI agent frameworks","TypeScript AI agent frameworks",lambda x,k:x["category"]=="frameworks" and re.search(r"TypeScript|JavaScript|\bNode(\.js)?\b|\bJS\b",x["description"]+" "+x["name"]),"Agent frameworks and SDKs for TypeScript, JavaScript and Node.js developers.","building-ai-agents","ai-agent-frameworks"),
("multi-agent-frameworks","Multi-agent frameworks","multi-agent frameworks",lambda x,k:k("multi-agent-systems") and x["audience"]=="builders","Frameworks for teams of agents that split work, hand off tasks and check each other's output.","multi-agent-systems","ai-agent-frameworks"),
("free-mcp-servers","Free MCP servers","free MCP servers",lambda x,k:x["category"]=="MCP & infra" and isfree(x) and k("connecting-tools-mcp"),"Model Context Protocol servers you can use for free, connecting Claude, Cursor, Codex and other MCP clients to your tools and data.","connecting-tools-mcp","open-source-mcp-servers"),
("database-mcp-servers","MCP servers and AI tools for databases","database MCP servers",lambda x,k:k("databases"),"MCP servers, vector stores and text-to-SQL tools that let agents query and manage databases.","databases",None),
("ai-agent-memory-tools","AI agent memory tools","AI agent memory",lambda x,k:k("agent-memory"),"Memory layers that let agents remember users, past conversations and facts between sessions.","agent-memory",None),
("ai-code-sandboxes","Sandboxes for AI agents to run code","AI code sandboxes",lambda x,k:k("running-code-safely"),"Sandboxes and isolated runtimes where agents can run code and tools away from your machine and data.","running-code-safely",None),
("open-source-llm-observability-tools","Open-source LLM observability and eval tools","open-source LLM observability",lambda x,k:x["category"]=="evals & observability" and x["pricing"] in OS,"Open-source tracing, evaluation and monitoring tools for LLM apps and agents that you can self-host.","monitoring-agents","ai-agent-observability-tools"),
("open-source-voice-ai-agents","Open-source voice AI agent frameworks","open-source voice AI agents",lambda x,k:x["category"]=="voice" and x["pricing"] in OS,"Open-source frameworks and tools for building voice agents that listen, think and talk in real time.","building-voice-agents","ai-voice-agent-platforms"),
("ai-phone-call-agents","AI agents that make and answer phone calls","AI phone call agents",lambda x,k:k("phone-calls"),"Voice agents and platforms that answer and place phone calls, book appointments and route callers.","phone-calls","ai-voice-agent-platforms"),
("free-no-code-ai-agent-builders","Free no-code AI agent builders","free no-code AI agent builders",lambda x,k:x["category"] in ("no-code builders","app builders") and isfree(x),"Visual and prompt-based builders for making agents and apps without code, with a free plan or open-source edition.","building-apps-without-code","no-code-ai-agent-builders"),
("open-source-workflow-automation-tools","Open-source AI workflow automation tools","open-source workflow automation",lambda x,k:k("automating-workflows") and x["pricing"] in OS,"Open-source platforms for chaining apps, triggers and AI steps into workflows you can self-host.","automating-workflows","no-code-ai-agent-builders"),
("open-source-ai-research-agents","Open-source AI research agents","open-source AI research agents",lambda x,k:x["category"]=="research" and x["pricing"] in OS,"Open-source deep-research agents that search many sources and write up a cited answer or report.","research",None),
("ai-research-assistants","AI research assistants (ready to use)","AI research assistants",lambda x,k:k("research") and x["audience"]=="ready to use","Ready-to-use research assistants that search, read and summarize sources for you, no setup required.","research",None),
("web-search-apis-for-ai-agents","Web search APIs for AI agents","web search APIs for AI agents",lambda x,k:k("searching-the-web"),"Search APIs and engines built for agents and LLM apps, returning clean results a model can use directly.","searching-the-web",None),
("ai-web-scraping-tools","AI web scraping and crawling tools","AI web scraping tools",lambda x,k:k("web-scraping"),"Tools that turn websites into clean text or structured data for agents, from single pages to whole sites.","web-scraping",None),
("local-ai-agents","AI agents that run locally","local AI agents",lambda x,k:k("running-agents-locally"),"Agents, model servers and tools that run on your own computer or hardware, keeping data local.","running-agents-locally","self-hosted-ai-agents"),
("open-source-personal-ai-assistants","Open-source personal AI assistants","open-source personal AI assistants",lambda x,k:(x["category"]=="personal agents" or k("personal-assistants")) and x["pricing"] in OS,"Personal assistants and always-on agents with public source code you can run and customize yourself.","personal-assistants","personal-ai-agents"),
("ai-agents-for-slack-telegram-whatsapp","AI agents for Slack, Telegram and WhatsApp","AI agents for Slack and Telegram",lambda x,k:k("chat-apps"),"Agents you can talk to or hand work to from the chat apps you already use.","chat-apps",None),
("ai-customer-support-agents","AI customer support agents","AI customer support agents",lambda x,k:k("customer-support"),"Agents that answer customer questions, resolve tickets and hand off to a person when needed.","customer-support","ai-business-agents"),
("ai-sales-agents","AI sales agents and SDR tools","AI sales agents",lambda x,k:k("sales-outreach"),"Agents that find leads, research prospects, write outreach and keep the pipeline moving.","sales-outreach","ai-business-agents"),
("ai-marketing-agents","AI marketing agents","AI marketing agents",lambda x,k:k("marketing"),"Agents for campaigns, social media, SEO and go-to-market data.","marketing",None),
("open-source-crypto-ai-agents","Open-source crypto AI agents","open-source crypto AI agents",lambda x,k:x["category"]=="crypto" and x["pricing"] in OS,"Open-source agent kits, MCP servers and tools for wallets, on-chain data and DeFi. Not financial advice.","crypto-and-wallets","crypto-ai-agents"),
("ai-trading-agents","AI trading agents","AI trading agents",lambda x,k:k("trading"),"Agents and copilots that research markets and turn plain-language strategies into trades. Trading is risky; nothing here is financial advice.","trading","crypto-ai-agents"),
("ai-security-testing-tools","AI security testing and pentest agents","AI pentest agents",lambda x,k:k("security-testing"),"Agents that probe apps, code and smart contracts the way an attacker would and suggest fixes.","security-testing",None),
("ai-agents-for-spreadsheets-and-slides","AI agents for spreadsheets, slides and docs","AI agents for spreadsheets",lambda x,k:k("spreadsheets-and-slides"),"AI spreadsheets, slide makers and MCP servers that let agents read and edit Excel, Sheets and office files.","spreadsheets-and-slides","ai-productivity-tools"),
("ai-video-agents","AI video agents and generators","AI video agents",lambda x,k:k("making-videos"),"Agents and tools that script, edit or generate video.","making-videos",None),
("ai-sre-agents","AI SRE and incident response agents","AI SRE agents",lambda x,k:k("devops-and-incidents"),"AI SRE agents and MCP servers that investigate alerts, read logs and help manage cloud infrastructure.","devops-and-incidents",None),
]
# role slug, name (plural noun), h1 stem, intro, [(section heading, task slug)], free tools [(href,label)], search slugs
R=[
("developers","developers","AI agents for developers","Coding agents, review bots, docs servers and sandboxes that help software developers ship faster.",
 [("Write and edit code","writing-code"),("Work in the terminal","terminal-coding"),("Review pull requests","reviewing-pull-requests"),("Give agents current docs","coding-docs"),("Test your app","testing-apps"),("Run several coding agents at once","parallel-coding-agents")],
 [("agent-setup-generator","Agent setup generator (CLAUDE.md, AGENTS.md, Cursor rules)"),("token-counter","Token counter")],["free-ai-coding-agents","terminal-ai-coding-agents","ai-code-review-tools","ai-code-sandboxes"]),
("ai-engineers","AI engineers","AI agent tools for AI engineers","Frameworks, memory, MCP, evals and observability for engineers who build and run their own agents.",
 [("Build agents","building-ai-agents"),("Multi-agent systems","multi-agent-systems"),("Memory","agent-memory"),("Build MCP servers","building-mcp-servers"),("Evaluate agents","evaluating-agents"),("Monitor in production","monitoring-agents"),("Deploy and host","deploying-agents")],
 [("ai-cost-calculator","AI API cost calculator"),("agent-setup-generator","Agent setup generator")],["open-source-ai-agent-frameworks","python-ai-agent-frameworks","typescript-ai-agent-frameworks","open-source-llm-observability-tools"]),
("marketers","marketers","AI agents for marketers","Agents for campaigns, social media, SEO data, email, images and video, so a small marketing team can do more.",
 [("Marketing and go-to-market","marketing"),("Email","writing-emails"),("Images and design","making-images-and-design"),("Video","making-videos"),("Research","research"),("Automate the busywork","automating-workflows")],
 [("prompt-builder","Prompt builder"),("../generate","Free AI image generator")],["ai-marketing-agents","ai-video-agents","ai-research-assistants"]),
("sales-teams","sales teams","AI agents for sales teams","Agents that find and research leads, write outreach, handle calls and keep the CRM up to date.",
 [("Sales outreach","sales-outreach"),("Email","writing-emails"),("Phone calls","phone-calls"),("Chat apps","chat-apps"),("Data and reporting","data-analysis")],
 [("prompt-builder","Prompt builder")],["ai-sales-agents","ai-phone-call-agents","ai-agents-for-slack-telegram-whatsapp"]),
("customer-support-teams","customer support teams","AI agents for customer support teams","Agents that answer customers, resolve tickets, take calls and search your knowledge base.",
 [("Customer support","customer-support"),("Phone calls","phone-calls"),("Chat apps","chat-apps"),("Search your documents","documents"),("Email","writing-emails")],
 [("prompt-builder","Prompt builder"),("agent-setup-generator","Agent setup generator")],["ai-customer-support-agents","ai-phone-call-agents"]),
("designers","designers","AI agents for designers","Image, diagram and video tools, plus app builders that turn a design idea into something people can click.",
 [("Images and design","making-images-and-design"),("Video","making-videos"),("Build apps without code","building-apps-without-code"),("Slides and docs","spreadsheets-and-slides")],
 [("../generate","Free AI image generator"),("prompt-builder","Prompt builder")],["ai-video-agents","free-no-code-ai-agent-builders"]),
("researchers","researchers","AI agents for researchers","Research agents, paper readers, search APIs and scrapers that find, read and cite sources for you.",
 [("Research","research"),("Read scientific papers","reading-papers"),("Web search","searching-the-web"),("Scrape websites","web-scraping"),("Work with documents","documents"),("Analyze data","data-analysis")],
 [("token-counter","Token counter"),("prompt-builder","Prompt builder")],["ai-research-assistants","open-source-ai-research-agents","web-search-apis-for-ai-agents","ai-web-scraping-tools"]),
("data-analysts","data analysts","AI agents for data analysts","Agents that query databases, clean and chart data, and work inside spreadsheets.",
 [("Data analysis","data-analysis"),("Databases","databases"),("Spreadsheets and slides","spreadsheets-and-slides"),("Scrape data from websites","web-scraping")],
 [("ai-cost-calculator","AI API cost calculator")],["database-mcp-servers","ai-agents-for-spreadsheets-and-slides","ai-web-scraping-tools"]),
("crypto-traders","crypto traders","AI agents for crypto traders","Trading copilots, wallet and on-chain tools, and smart-contract checkers. Trading is risky and nothing here is financial advice.",
 [("Trading","trading"),("Crypto and wallets","crypto-and-wallets"),("Smart contract security","smart-contract-security"),("Agent payments","agent-payments")],
 [],["ai-trading-agents","open-source-crypto-ai-agents"]),
("founders","founders and small businesses","AI agents for founders and small businesses","Ready-made agents for operations, support, marketing and building your first app, so a small team can cover more ground.",
 [("Business operations","business-automation"),("Automate workflows","automating-workflows"),("Build apps without code","building-apps-without-code"),("Customer support","customer-support"),("Marketing","marketing"),("Personal assistants","personal-assistants")],
 [("ai-cost-calculator","AI API cost calculator"),("prompt-builder","Prompt builder")],["free-no-code-ai-agent-builders","ai-customer-support-agents","ai-marketing-agents"]),
("devops-engineers","DevOps and SRE engineers","AI agents for DevOps and SRE engineers","AI SRE agents, observability, sandboxes and deployment tools for keeping systems and agents running.",
 [("Incidents and infrastructure","devops-and-incidents"),("Monitor agents in production","monitoring-agents"),("Deploy and host agents","deploying-agents"),("Run code safely","running-code-safely"),("Agent security","agent-security")],
 [("agent-setup-generator","Agent setup generator")],["ai-sre-agents","ai-code-sandboxes","open-source-llm-observability-tools"]),
("security-engineers","security engineers","AI agents for security engineers","Pentest agents, guardrails, identity and sandboxing tools for securing apps and the agents that touch them.",
 [("Security testing","security-testing"),("Agent security and guardrails","agent-security"),("Smart contract security","smart-contract-security"),("Agent identity and logins","agent-identity"),("Sandboxes","running-code-safely")],
 [],["ai-security-testing-tools","ai-code-sandboxes"]),
("game-developers","game developers","AI tools for game developers","AI game makers, NPC engines, image and voice tools for building games.",
 [("Games and game makers","games"),("Images and design","making-images-and-design"),("Voice","building-voice-agents")],
 [("../generate","Free AI image generator")],["open-source-voice-ai-agents"]),
("content-creators","content creators","AI agents for content creators","Video, image and social tools, plus research helpers, for people who publish online.",
 [("Video","making-videos"),("Images and design","making-images-and-design"),("Marketing and social","marketing"),("Research","research")],
 [("prompt-builder","Prompt builder"),("../generate","Free AI image generator")],["ai-video-agents","ai-marketing-agents"]),
]
def ftl(h,d="../"):
    if h.startswith("../"): return f'{d}{h[3:]}.html'
    return f'{d}free-tools/{h}.html'
def mini(x):
    gs=f' · ★ {x["github_stars"]:,}' if x.get("github_stars") is not None else ""
    return f'<li style="margin:0 0 10px"><a href="../tools/{x["slug"]}.html"><b>{e(x["name"])}</b></a> <span class="b" style="font-size:12px">{e(x["pricing"])}</span><br><span style="color:var(--muted);font-size:14px">{e(x["description"])}</span><span class="muted" style="font-size:12.5px">{gs}</span></li>'
def search_pages(t,m,asof):
    made=[]; inT=lambda x:(lambda s:s in m and x in m[s][1])
    for s,h,q,f,intro,task,best in S:
        allm=[x for x in t if live(x) and f(x,inT(x))]
        if len(allm)<6: print("skip search page (too few):",s,len(allm)); continue
        items=rank(allm)[:25]; made.append((s,h,q,len(allm),items,intro,task,best,allm))
    titles={a[0]:a[1] for a in made}
    for s,h,q,n,items,intro,task,best,allm in made:
        canon=f"{B}s/{s}.html"; title=f"{h} (2026): {len(items)} picks · AgentScout"
        desc=f"{h} in 2026: {n} matching tools in AgentScout's link-checked directory, including {', '.join(x['name'] for x in items[:3])}. Pricing as makers state it."
        if len(desc)>158: desc=f"{h} (2026): {n} tools, including {', '.join(x['name'] for x in items[:2])}. Link-checked; pricing as stated."[:158]
        pc=collections.Counter(x["pricing"] for x in items); cats=collections.Counter(x["category"] for x in allm).most_common()
        star=[x for x in items if x.get("github_stars")]
        osn=sum(1 for x in allm if x["pricing"] in OS); frn=sum(1 for x in allm if isfree(x))
        facts=(f'<div class="badges" style="margin:0 0 18px"><span class="b">{n} matching tools</span><span class="b">{osn} open source</span><span class="b">{frn} free or with a free tier</span>'
               +(f'<span class="b">Most starred: {e(star[0]["name"])} (★ {star[0]["github_stars"]:,})</span>' if star else "")+'</div>')
        faq=[(f"What are the best {q}?",f"Ranked by tracked GitHub stars, the top {q} in our directory are "+", ".join(x["name"] for x in items[:5])+". Stars measure popularity, not fit, so compare a few against your own task."),
             (f"How many {q} does AgentScout list?",f"{n} tools match. This page shows the top {len(items)}. Pricing mix on this page: "+", ".join(f"{k} ({v})" for k,v in pc.most_common())+"."),
             ("Are these tools really free?" if "free" in s else "How much do these tools cost?","Pricing is what each maker states on their site. Open-source tools are free to self-host but may need a paid model API key or offer paid cloud plans; freemium tools have a free plan with limits. Check each official site.")]
        if task in m: faq.append((f"Where can I see every tool for {m[task][0][1]}?",f"Our task page lists all {len(m[task][1])} tools we match to {m[task][0][1]}."))
        fq="".join(f'<h3 style="font-size:15px;margin:18px 0 4px">{e(a)}</h3><p style="margin:0">{e(b)}</p>' for a,b in faq)
        rel=[f'<a href="../tasks/{task}.html">All tools for {e(m[task][0][1])}</a>'] if task in m else []
        if best: rel.append(f'<a href="../best/{best}.html">{e(next((p[1] for p in BB.PAGES if p[0]==best),"Best list"))}</a>')
        rel+=[f'<a href="../categories/{X.catslug(c)}.html">{e(c)} ({k})</a>' for c,k in cats[:4]]
        sib=[a for a in made if a[0]!=s and (a[6]==task or (best and a[7]==best))][:5]
        sibh=" · ".join(f'<a href="{a[0]}.html">{e(a[1])}</a>' for a in sib)
        roles=[r for r in R if s in r[6]]
        roleh=" · ".join(f'<a href="../for/{r[0]}.html">For {e(r[1])}</a>' for r in roles)
        ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
            {"@type":"ItemList","name":h,"itemListOrder":"https://schema.org/ItemListOrderDescending","numberOfItems":len(items),"itemListElement":[{"@type":"ListItem","position":i+1,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate(items)]},
            {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":a,"acceptedAnswer":{"@type":"Answer","text":b}} for a,b in faq]},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Popular searches","item":B+"s/"},{"@type":"ListItem","position":3,"name":h,"item":canon}]}]}
        body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">Popular searches</a> / {e(h)}</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left;margin-left:0">{e(h)} (2026)</h1>'
              f'<p class="lede" style="margin-left:0;text-align:left">{e(intro)} {"Here are the top "+str(len(items))+" of "+str(n) if n>len(items) else "Here are all "+str(n)} from the AgentScout directory.</p>{facts}'
              f'<p class="muted" style="margin:0 0 18px"><strong>How we picked and ranked:</strong> tools are matched by category, the pricing each maker states and what each tool says it does. They are ranked by GitHub stars as recorded on each listing (link checks {asof}); tools without a tracked repo follow, by listing maturity. No paid placements.</p>'
              f'<ol class="grid" style="padding:0;margin:0">{"".join(BB.item(i+1,x) for i,x in enumerate(items))}</ol>'
              f'<h2 style="font-size:18px;margin:36px 0 6px">FAQ</h2>{fq}'
              f'<p style="margin-top:28px">Related: {" · ".join(rel)}</p>'+(f'<p>Similar searches: {sibh}</p>' if sibh else "")+(f'<p>By role: {roleh}</p>' if roleh else "")+
              f'<p><a href="index.html">All popular searches</a> · <a href="../for/index.html">AI agents by role</a> · <a href="../free-tools.html">Free tools</a></p>'
              f'<p class="disclose">Facts come from our directory listings; pricing is as each maker states it and can change. Check official sites before you choose.</p></section>')
        open(f"s/{s}.html","w").write(X.shell("../",title,desc,canon,body,ld))
    canon=B+"s/"; title="Popular AI Agent Tool Searches (2026) · AgentScout"
    desc=f"{len(made)} focused lists of AI agent tools: free coding agents, open-source browser agents, Python frameworks, MCP servers, voice and more."[:158]
    tiles="".join(f'<a class="card" href="{a[0]}.html"><div class="ct"><h3>{e(a[1])}</h3></div><p>{a[3]} tools · {e(", ".join(x["name"] for x in a[4][:3]))}</p></a>' for a in made)
    ld={"@context":"https://schema.org","@type":"CollectionPage","name":title,"description":desc,"url":canon,"hasPart":[{"@type":"WebPage","name":a[1],"url":f"{B}s/{a[0]}.html"} for a in made]}
    body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / Popular searches</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left;margin-left:0">Popular AI agent tool searches</h1>'
          f'<p class="lede" style="margin-left:0;text-align:left">Quick answers to the searches people make most, each built from the AgentScout directory with the ranking method stated.</p><div class="grid">{tiles}</div>'
          f'<p style="margin-top:24px">See also: <a href="../for/index.html">AI agents by role</a> · <a href="../best/index.html">Best lists</a> · <a href="../tasks/index.html">AI agents by task</a> · <a href="../free-tools.html">Free tools</a></p></section>')
    open("s/index.html","w").write(X.shell("../",title,desc,canon,body,ld))
    return [canon]+[f"{B}s/{a[0]}.html" for a in made],made
def role_pages(t,m,made):
    ok={a[0]:a[1] for a in made}; urls=[]; info=[]
    for s,who,h,intro,secs,fts,ss in R:
        canon=f"{B}for/{s}.html"; title=f"{h} (2026) · AgentScout"; secs=[(a,b) for a,b in secs if b in m]
        seen=set(); body_s=""; allitems=[]
        for hd,task in secs:
            items=[y for y in m[task][1] if live(y)][:6]  # build_tasks order: category match, use-case match, then stars
            allitems+=[x for x in items if x["slug"] not in seen]; seen|={x["slug"] for x in items}
            body_s+=(f'<h2 style="font-size:18px;margin:32px 0 6px">{e(hd)}</h2><p class="muted" style="margin:0 0 10px;font-size:14px">{e(m[task][0][5])} <a href="../tasks/{task}.html">All {len(m[task][1])} tools →</a></p>'
                     f'<ul style="list-style:none;padding:0;margin:0">{"".join(mini(x) for x in items)}</ul>')
        n=len(seen)
        desc=f"{h} in 2026: {n} picks across {len(secs)} jobs, including {', '.join(x['name'] for x in allitems[:3])}. Link-checked; pricing as makers state it."
        if len(desc)>158: desc=f"{h} (2026): {n} picks across {len(secs)} jobs, including {', '.join(x['name'] for x in allitems[:2])}."[:158]
        jump=" · ".join(f'<a href="#{T2}">{e(a)}</a>' for a,T2 in [(a,X.catslug(a)) for a,_ in secs])
        body_s=re.sub(r'<h2 style="font-size:18px;margin:32px 0 6px">([^<]+)</h2>',lambda mm:f'<h2 id="{X.catslug(__import__("html").unescape(mm.group(1)))}" style="font-size:18px;margin:32px 0 6px">{mm.group(1)}</h2>',body_s)
        ft=" · ".join(f'<a href="{ftl(a)}">{e(b)}</a>' for a,b in fts)
        sr=" · ".join(f'<a href="../s/{x}.html">{e(ok[x])}</a>' for x in ss if x in ok)
        oth=" · ".join(f'<a href="{r[0]}.html">{e(r[1].capitalize())}</a>' for r in R if r[0]!=s)
        free_n=sum(1 for x in allitems if isfree(x))
        ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B},"audience":{"@type":"Audience","audienceType":who}},
            {"@type":"ItemList","numberOfItems":len(allitems),"itemListElement":[{"@type":"ListItem","position":i+1,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate(allitems)]},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"By role","item":B+"for/"},{"@type":"ListItem","position":3,"name":h,"item":canon}]}]}
        body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">By role</a> / {e(who.capitalize())}</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left;margin-left:0">{e(h)} (2026)</h1>'
              f'<p class="lede" style="margin-left:0;text-align:left">{e(intro)} We picked the top tools for {len(secs)} jobs {e(who)} do every day: {n} tools in all, {free_n} of them free or with a free tier.</p>'
              f'<p style="font-size:14px">Jump to: {jump}</p>'
              +(f'<p style="font-size:14px">Free tools from AgentScout for {e(who)}: {ft}</p>' if ft else "")+
              f'<p class="muted" style="margin:0 0 6px;font-size:13.5px"><strong>How we picked:</strong> each section takes the tools matched to that task in our directory, putting tools whose category and stated use cases fit the task first, then ordering by tracked GitHub stars. No paid placements.</p>'
              f'{body_s}'+(f'<h2 style="font-size:16px;margin:32px 0 10px">Popular searches for {e(who)}</h2><p>{sr}</p>' if sr else "")+
              f'<p style="margin-top:24px">Other roles: {oth} · <a href="index.html">All roles</a></p>'
              f'<p class="disclose">Facts come from our directory listings; pricing is as each maker states it and can change. Missing a tool? <a href="../submit.html">Submit it free</a>.</p></section>')
        open(f"for/{s}.html","w").write(X.shell("../",title,desc,canon,body,ld)); urls.append(canon); info.append((s,who,h,n))
    canon=B+"for/"; title="AI Agents by Role: Tools for Every Team (2026) · AgentScout"
    desc=f"AI agent tools picked for {len(info)} roles: developers, marketers, sales, support, designers, researchers, crypto traders and more."[:158]
    tiles="".join(f'<a class="card" href="{s}.html"><div class="ct"><h3>For {e(who)}</h3></div><p>{n} tools picked</p></a>' for s,who,h,n in info)
    ld={"@context":"https://schema.org","@type":"CollectionPage","name":title,"description":desc,"url":canon,"hasPart":[{"@type":"WebPage","name":h,"url":f"{B}for/{s}.html"} for s,_,h,_ in info]}
    body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / By role</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left;margin-left:0">AI agents by role</h1>'
          f'<p class="lede" style="margin-left:0;text-align:left">Pick your job and see the AI agent tools that fit the work you actually do, grouped by task.</p><div class="grid">{tiles}</div>'
          f'<p style="margin-top:24px">See also: <a href="../s/">Popular searches</a> · <a href="../tasks/index.html">AI agents by task</a> · <a href="../best/index.html">Best lists</a> · <a href="../free-tools.html">Free tools</a></p></section>')
    open("for/index.html","w").write(X.shell("../",title,desc,canon,body,ld))
    return [canon]+urls,info
def pages(t):
    os.makedirs("s",exist_ok=True); os.makedirs("for",exist_ok=True)
    m=tm(T.mapping(t)); asof=max(x["verified"] for x in t)
    su,made=search_pages(t,m,asof); ru,info=role_pages(t,m,made)
    keep={f"s/{a[0]}.html" for a in made}|{f"for/{r[0]}.html" for r in info}|{"s/index.html","for/index.html"}
    for f in glob.glob("s/*.html")+glob.glob("for/*.html"):
        if f not in keep: os.remove(f)
    # hub links (additive)
    BB.link_in("best/index.html",'See also: ','<a href="../s/">Popular searches</a> · <a href="../for/index.html">AI agents by role</a> · ','href="../s/"')
    BB.link_in("tasks/index.html",'each with the agent tools that handle it.',' Or browse <a href="../for/index.html">by role</a> and <a href="../s/">popular searches</a>.','href="../for/index.html"')
    BB.link_in("free-tools.html",'grouped by category.</p>',f'<p style="font-size:14px;margin:-6px 0 0">Looking for something specific? Try <a href="s/">popular searches</a> like <a href="s/free-ai-coding-agents.html">free AI coding agents</a> or browse <a href="for/index.html">AI agents by role</a>.</p>','href="s/"')
    BB.link_in("llms.txt",f"- [All best-of lists]({B}best/)",f"\n- [Popular searches]({B}s/)\n- [AI agents by role]({B}for/)\n- [Free tools: AI cost calculator]({B}free-tools/ai-cost-calculator.html)\n- [Free tools: token counter]({B}free-tools/token-counter.html)\n- [Free tools: prompt builder]({B}free-tools/prompt-builder.html)\n- [Free tools: agent setup generator]({B}free-tools/agent-setup-generator.html)",f"]({B}s/)")
    print("landing:",len(made),"search pages,",len(info),"role pages + 2 hubs")
    return su+ru
