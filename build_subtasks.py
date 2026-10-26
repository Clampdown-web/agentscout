"""Sub-task sections, sibling counts and open-source repo tables for /tasks/ and /categories/ pages (directory-style task template, Oct 18 2026).
Sub-tasks are assigned by keyword rules over each tool's name + description. Within a page a tool appears once, under the first eligible sub-task
(order below = most specific first). A sub-task is shown on a page only if it has >=3 tools there and covers <=75% of the page."""
import re,json,os,html
e=lambda s:html.escape(str(s or ""))
SUBTASKS=[
("penetration-testing","penetration and security testing",r"penetration|pentest|red[- ]team|vulnerab|bug bount"),
("smart-contracts","smart contracts",r"smart[- ]contract"),
("ai-sre","SRE and incident response",r"\bSRE\b|incident|production alerts|root cause|on-call"),
("trading-agents","trading agents",r"\btrad(ing|es|er)\b|\bswaps?\b|\bperps\b|prediction market"),
("agent-wallets","agent wallets",r"wallet"),
("agent-payments","agent payments",r"payment|\bpay(s)? for\b|checkout|x40[12]|stablecoin"),
("code-review","code review",r"code review|review(s|ing)? (code|pull|PRs|diffs)|pull request|\bdiffs?\b"),
("testing-qa","testing and QA",r"\bQA\b|end-to-end|\bE2E\b|\btest(s|ing)? (agent|generation|automation|every|your)|writes? tests|testing agent"),
("parallel-orchestration","running many agents in parallel",r"parallel|fleet of|many (coding )?agents|multiple (coding )?agents|worktree|command center|control plane|side by side|teams? of (coding |specialized )?agents"),
("codebase-context","codebase context and code search",r"codebase|code search|knowledge graph|monorepo|context (layer|window)|large codebases"),
("agent-memory","memory",r"\bmemory\b|remember|long-term|across sessions"),
("planning-tasks","planning and task tracking",r"\bplan(s|ning)?\b|kanban|task board|issue[- ]track"),
("token-costs","token usage and cost tracking",r"token (usage|use)|\bspend\b|cost tracking|cheaper"),
("notebooks","notebooks",r"jupyter|notebook"),
("text-to-sql","SQL and databases",r"\bSQL\b|Postgres|MySQL|MongoDB|database"),
("vector-rag","RAG and documents",r"\bRAG\b|retriev|document|\bPDF|knowledge base|vector"),
("voice-phone","voice and phone agents",r"\bvoice\b|phone|speech|\bcalls?\b|telephon"),
("chat-app-agents","agents in chat apps",r"Telegram|WhatsApp|iMessage|\bDiscord\b|\bSlack\b"),
("email-agents","email",r"\bemails?\b|inbox|gmail"),
("sales-agents","sales and lead generation",r"\bsales\b|\bleads?\b|prospect|\bCRM\b|\bSDR\b|outbound"),
("support-agents","customer support",r"customer (support|service)|helpdesk|help desk|support tickets|resolves? support"),
("marketing-agents","marketing and social media",r"marketing|\bSEO\b|social media|\bads?\b"),
("research-agents","research and reports",r"research|cited|citation|papers"),
("web-scraping","scraping and crawling",r"scrap|crawl|extract"),
("search-apis","search APIs",r"search API|web search|search engine"),
("browser-automation","browser automation",r"\bbrowsers?\b|headless|Playwright|Puppeteer|Selenium"),
("computer-use","computer and desktop control",r"computer[- ]use|desktop|\bscreen\b|mouse"),
("sandboxes","sandboxes and secure execution",r"sandbox|microVM|isolated|secure (runtime|execution)"),
("guardrails","guardrails and policies",r"guardrail|policy|policies|permission|governance|safety"),
("agent-auth","identity, auth and secrets",r"\bidentity\b|\bauth|credential|secrets?\b|login"),
("observability","tracing and observability",r"observab|tracing|traces|monitor|logging|dashboard"),
("evals","evals and benchmarks",r"\bevals?\b|evaluat|benchmark"),
("fine-tuning","training and fine-tuning",r"fine[- ]tun|reinforcement learning|\bRL\b|post[- ]train|training"),
("mcp-gateways","MCP gateways and registries",r"gateway|registry|proxy|marketplace"),
("mcp-servers","MCP servers",r"MCP server"),
("workflow-automation","workflow automation",r"workflow|automation platform|automates? (your )?(work|tasks|business|processes)"),
("no-code-apps","no-code app building",r"no-code|without code|drag-and-drop|prompt-to-app|full apps|web apps|app builder"),
("multi-agent","multi-agent orchestration",r"multi-agent|crew|swarm|subagent|orchestrat"),
("agent-frameworks","agent frameworks and SDKs",r"framework|\bSDK\b|library|toolkit|harness"),
("local-models","local and self-hosted",r"\blocal|self-hosted|on-device|on your own|offline"),
("terminal-agents","terminal and CLI agents",r"terminal|\bCLI\b|command[- ]line|\bTUI\b|shell"),
("ide-agents","IDE and editor agents",r"\bIDE\b|editor|VS Code|JetBrains|Jupyter"),
("cloud-coding-agents","autonomous and cloud coding agents",r"autonomous (software|developer|coding)|cloud (coding )?agent|takes tickets|GitHub issues|opens PRs|asynchronous coding"),
("script-tools","script breakdown and coverage",r"screenplay|script (breakdown|coverage|analys)|scripts?\b.*(breakdown|budget|schedul)"),
("storyboards-previs","storyboards and previs",r"storyboard|previs|animatic|shot list|3D studio"),
("virtual-production-mocap","virtual production and motion capture",r"virtual production|motion capture|mocap|camera track|LED volume"),
("visual-dubbing","visual dubbing and lip sync",r"lip.?sync|visual dubbing"),
("vfx-compositing","VFX and compositing",r"\bVFX|composit|roto|relight|clean plate|planar|object removal"),
("color-upscaling","color and upscaling",r"colou?r grad|upscal|enhanc|denoise|HDR"),
("subtitles-transcripts","subtitles and transcripts",r"subtitle|caption|transcri"),
("video-editing","editing and rough cuts",r"rough (cut|assembl)|stringout|\bedit|selects|multicam|clips?\b|footage"),
("foley-sfx","Foley and sound effects",r"Foley|sound effects?|\bSFX|sound design"),
("dialogue-cleanup","dialogue cleanup and repair",r"dialogue|noise|reverb|repair|filler|speech"),
("ai-dubbing-voices","ADR, dubbing and voices",r"\bdub|voice ?over|voice clon|voices|narration|voice-chang|voice conv|\bADR\b"),
("stem-separation","stem separation",r"\bstems?\b|vocal remov|separat|splitter|unmix|isolat"),
("mastering","mastering",r"master"),
("vocal-tuning","vocal tuning and vocal plugins",r"pitch|tuning|vocal (mix|plugin|chain)|AutoTune"),
("mixing","mixing",r"\bmix"),
("video","video",r"video"),
("images-design","images and design",r"\bimages?\b|design|diagram|visual"),
("games","games",r"\bgames?\b|NPC|Minecraft"),
("personal-assistants","personal assistants",r"personal (assistant|agent)|errands|always-on|your day"),
("mobile","mobile and remote control",r"mobile|phone app|iOS|Android"),
("rules-config","rules, skills and config",r"\brules\b|skills|configur|settings"),
]
_RX=[(s,l,re.compile(r,re.I)) for s,l,r in SUBTASKS]
# Hand-checked sub-tasks for tools the regex tags wrongly (Oct 22 2026).
TAG_OVERRIDE={"editara":["images-design","color-upscaling"],"puremidi":[],"lakewood-agents":["personal-assistants","research-agents","local-models"],"aiartflow":["images-design","color-upscaling"],"midiflow":[],"trybestspecs":["images-design"],"machine-like":["email-agents","chat-app-agents","workflow-automation"],"kiwi":["sales-agents","email-agents","workflow-automation"],"lobstermatch":["multi-agent","agent-auth","workflow-automation"],"tanatasa-beauty-mcp":["mcp-servers","workflow-automation"],"neverapply":["mcp-servers","workflow-automation"],"ai-music-mastering":["mastering","mixing"],"book-cover-generator":["images-design"],"raydo-agent-os":["computer-use","browser-automation","workflow-automation","sandboxes","local-models"],"havetml":["sandboxes","mcp-servers"],"hiredov":["email-agents","workflow-automation"],"system-one-api":["agent-frameworks"],"conductor":["parallel-orchestration","multi-agent","cloud-coding-agents"]}
def tags(x):
    if x.get("slug") in TAG_OVERRIDE: return list(TAG_OVERRIDE[x["slug"]])
    d=f'{x.get("name","")} {x.get("description","")}'
    return [s for s,_,r in _RX if r.search(d)]
LABEL={s:l for s,l,_ in SUBTASKS}
# Sub-tasks that make sense under each parent task (quality pass, Oct 18 2026). Tasks not listed stay flat.
ALLOW={
"writing-code":["terminal-agents","ide-agents","cloud-coding-agents","parallel-orchestration","code-review","testing-qa","codebase-context","agent-memory","planning-tasks","token-costs","sandboxes","penetration-testing","mcp-servers","rules-config"],
"terminal-coding":["code-review","mcp-servers","local-models","agent-frameworks"],
"browsing-the-web":["browser-automation","computer-use","web-scraping","mobile"],
"computer-use":["browser-automation","agent-memory","mcp-servers"],
"automating-workflows":["workflow-automation","browser-automation","computer-use","no-code-apps","mcp-servers"],
"building-apps-without-code":["no-code-apps","workflow-automation"],
"building-ai-agents":["multi-agent","vector-rag","agent-memory","voice-phone","fine-tuning","evals","workflow-automation","mcp-servers"],
"multi-agent-systems":["agent-frameworks","parallel-orchestration","research-agents","workflow-automation"],
"building-voice-agents":["voice-phone","agent-payments"],
"customer-support":["support-agents","voice-phone","sales-agents","vector-rag"],
"business-automation":["sales-agents","support-agents","email-agents","workflow-automation"],
"personal-assistants":["computer-use","local-models","agent-memory","chat-app-agents","research-agents","browser-automation"],
"research":["research-agents","search-apis","web-scraping","vector-rag","text-to-sql","trading-agents"],
"data-analysis":["text-to-sql","vector-rag","web-scraping","mcp-servers","observability"],
"documents":["vector-rag","web-scraping","research-agents"],
"connecting-tools-mcp":["mcp-servers","mcp-gateways","agent-memory","text-to-sql","sandboxes","codebase-context","computer-use","browser-automation","web-scraping","search-apis","agent-auth","agent-payments","observability"],
"building-mcp-servers":["mcp-gateways","agent-frameworks","agent-auth","observability","text-to-sql"],
"agent-memory":["vector-rag","codebase-context","local-models","agent-frameworks"],
"evaluating-agents":["observability","evals","guardrails","penetration-testing","sandboxes"],
"monitoring-agents":["evals","guardrails"],
"agent-security":["guardrails","sandboxes","penetration-testing","agent-wallets"],
"testing-apps":["testing-qa","code-review","penetration-testing"],
"making-images-and-design":["mcp-servers"],  # Oct 18 2026: images-design sub-page retired (redirect), page rebuilt on art categories
"crypto-and-wallets":["trading-agents","agent-wallets","agent-payments","mcp-servers","penetration-testing"],
"agent-payments":["agent-wallets","agent-auth"],
"video-post-production":["visual-dubbing","vfx-compositing","color-upscaling","subtitles-transcripts","video-editing"],
"audio-post-production":["foley-sfx","dialogue-cleanup","ai-dubbing-voices","stem-separation","mixing"],
"music-mixing-mastering":["mastering","vocal-tuning","mixing"],
"storyboarding":["script-tools","storyboards-previs"],
}
def sections(items,min_n=3,max_share=.75,min_page=12,task=None,allow=None):
    """Return [(slug,label,[tools])...] + others list, or None when the page should stay flat."""
    if len(items)<min_page: return None
    tg={id(x):tags(x) for x in items}; n=len(items)
    cnt={}
    for x in items:
        for s in tg[id(x)]: cnt[s]=cnt.get(s,0)+1
    if allow is None: allow=ALLOW.get(task)
    if not allow: return None
    elig=[s for s,_,_ in SUBTASKS if s in allow and cnt.get(s,0)>=min_n and cnt[s]<=max_share*n]
    for _ in range(3):  # re-check after exclusive assignment
        grp={s:[] for s in elig}; other=[]
        for x in items:
            s=next((s for s in tg[id(x)] if s in grp),None)
            (grp[s] if s else other).append(x)
        small=[s for s in elig if len(grp[s])<min_n]
        if not small: break
        elig=[s for s in elig if s not in small]
    secs=sorted([(s,LABEL[s],v) for s,v in grp.items() if v],key=lambda z:(-len(z[2]),z[1]))
    if len(secs)<2: return None
    return secs,other
def repo_rows(items,limit=15):
    import build_rich
    gh=json.load(open("data/github.json")) if os.path.exists("data/github.json") else {}
    rows=[]
    for x in items:
        if x.get("github_stars") is None or not x.get("github"): continue
        F=(build_rich.R.get(x["slug"]) or {}).get("facts") or {}
        lic=re.sub(r"^the ","",F.get("license") or "")
        lic=re.sub(r" (License|Licence)$","",lic)
        g=gh.get(x["slug"]) or {}
        rows.append((x,x["github_stars"],lic,g.get("pushed","")))
    rows.sort(key=lambda r:-r[1]); return rows[:limit],len(rows)
def repo_table(items,d="../",title="GitHub repos"):
    rows,total=repo_rows(items)
    if len(rows)<3: return ""
    haspush=any(r[3] for r in rows)
    th='<tr><th scope="col">Repo</th><th scope="col">GitHub stars</th><th scope="col">Licence</th>'+('<th scope="col">Last push</th>' if haspush else "")+'</tr>'
    tr="".join(f'<tr><td><a href="{d}tools/{x["slug"]}.html">{e(x["name"])}</a> <a class="ghx" href="{e(x["github"])}" target="_blank" rel="noopener noreferrer" aria-label="{e(x["name"])} on GitHub">↗</a></td><td>{s:,}</td><td>{e(l) or "—"}</td>'+(f'<td>{e(p[:10]) or "—"}</td>' if haspush else "")+'</tr>' for x,s,l,p in rows)
    note=f"Top {len(rows)} of {total} by stars." if total>len(rows) else f"{total} repos."
    return (f'<h2 id="repos" style="font-size:18px;margin:32px 0 10px;scroll-margin-top:84px">{e(title)} <span style="color:var(--muted);font-weight:400">({total})</span></h2>'
            f'<div style="overflow-x:auto"><table class="cmp" style="width:100%;border-collapse:collapse;font-size:14px"><thead>{th}</thead><tbody>{tr}</tbody></table></div>'
            f'<p class="muted" style="font-size:13px;margin:6px 0 0">{note} Stars and licence come from each repo, checked when the listing was last verified.</p>')
OPEN={"Open source","Open source + cloud","Open standard","Open weights"}
SRC={"Source-available","Source-available + cloud"}
FREE={"Free","Freemium"}
PAID={"Paid","Enterprise","Usage-based"}
def price_line(items):
    o=sum(x["pricing"] in OPEN for x in items); s=sum(x["pricing"] in SRC for x in items)
    f=sum(x["pricing"] in FREE for x in items); p=sum(x["pricing"] in PAID for x in items); u=len(items)-o-s-f-p
    parts=[(o,"open source"),(s,"source-available"),(f,"free or freemium"),(p,"paid, usage-based or enterprise"),(u,"pricing on the maker's site")]
    return ", ".join(f"{n} {l}" for n,l in parts if n)
def dump(t):
    json.dump({x["slug"]:tags(x) for x in t},open("subtasks.json","w"),indent=0,ensure_ascii=False)
# One-line explanations used on sub-task pages (only sub-tasks that can get a page need one).
SUBDESC={
"rules-config":"Tools that give coding agents shared rules, skills and settings, so Claude Code, Cursor, Codex and others follow the same conventions in every repo.",
"browser-automation":"Agents and libraries that drive a real browser: opening pages, clicking, typing and filling in forms from plain-language instructions.",
"computer-use":"Agents that see the screen and use the mouse and keyboard, so they can work in desktop apps as well as the browser.",
"mobile":"Tools that run or control agents from phones, or let agents operate mobile apps and devices.",
"workflow-automation":"Platforms that chain apps, triggers and AI steps into workflows that run on their own.",
"no-code-apps":"Builders that turn a description or a drag-and-drop canvas into a working app or agent, without writing code.",
"multi-agent":"Frameworks for teams of agents that hand work to each other, split tasks and check each other's output.",
"vector-rag":"Retrieval tools that let agents search documents, PDFs and knowledge bases and answer from them (RAG).",
"agent-memory":"Memory layers that let agents remember users, past sessions and facts over time.",
"voice-phone":"Platforms for agents that listen and talk: phone lines, real-time speech and voice assistants.",
"local-models":"Agents and assistants that can run on your own machine or server, keeping data local.",
"research-agents":"Agents that search, read many sources and return a cited answer or report.",
"text-to-sql":"Tools that let agents query databases, from text-to-SQL to database MCP servers.",
"evals":"Evaluation tools that score agent outputs, catch regressions and compare prompts and models.",
"guardrails":"Guardrails, policy engines and permission layers that limit what agents are allowed to do.",
"images-design":"Agents and tools for visual work: generating images, diagrams and designs.",
"agent-wallets":"Wallets built for agents, so they can hold funds and sign transactions within limits you set.",
"agent-payments":"Payment rails that let agents pay for APIs and services on their own, including x402 and stablecoin payments.",
"agent-frameworks":"Frameworks and SDKs for building agents in code.",
"code-review":"Agents that read diffs and pull requests and flag bugs before merge.",
"parallel-orchestration":"Tools for running several agents at once and reviewing what each hands back.",
"codebase-context":"Context layers and code search that help agents understand large codebases with fewer tokens.",
"sandboxes":"Isolated sandboxes where agents can run code and tools away from your machine and data.",
"search-apis":"Search APIs built for agents, returning clean results an LLM can use.",
"web-scraping":"Tools that turn websites into clean data an agent can use.",
"observability":"Tracing and monitoring for agents: costs, latency and errors in one place.",
"terminal-agents":"Agents that run in your terminal: they read files, run commands and propose changes.",
"ide-agents":"Agents that live inside your editor or IDE.",
"planning-tasks":"Planning boards and task trackers that coding agents can read and update.",
"mcp-servers":"MCP servers that connect agents to outside apps and data.",
"mcp-gateways":"Gateways and registries for finding, hosting and securing MCP servers.",
"agent-auth":"Identity and credential tools that let agents sign in without seeing raw secrets.",
"trading-agents":"Agents that research markets and execute trades. Trading is risky; none of this is financial advice.",
"sales-agents":"Agents that find leads, write outreach and update your CRM.",
"support-agents":"Agents that answer customer questions and resolve tickets.",
"email-agents":"Assistants that draft replies and manage your inbox.",
"fine-tuning":"Platforms for fine-tuning models and training agents on your own tasks.",
"penetration-testing":"Agents that probe apps and code the way an attacker would and report vulnerabilities.",
"chat-app-agents":"Agents you can reach from Slack, Telegram, WhatsApp, Discord or iMessage.",
"testing-qa":"Agents that write and run tests and report what breaks.",
"token-costs":"Trackers for token usage and spend across coding agents.",
"cloud-coding-agents":"Autonomous coding agents that take an issue and come back with a pull request.",
}
try: _REDIR=set(__import__("json").load(open("redirects.json")))
except Exception: _REDIR=set()
def subpages(m,t,existing_sets):
    """Sub-task pages: >=8 tools, <=75% of the parent, <70% overlap (share of the new page's tools) with any /s/ or /best/ page,
    Jaccard <70% with any task page, <70% contained in an earlier sub-task page. Returns [(slug,parent_slug,sub,items)]."""
    tasksets={s:{x["slug"] for x in it} for s,(T,it) in m.items()}; out=[]; made=[]
    for s,(T,items) in m.items():
        for sub in ALLOW.get(s) or []:
            if sub not in SUBDESC: continue
            if f"tasks/{s}-{sub}.html" in _REDIR: continue  # redirected page (redirects.json): never re-create it
            its=[x for x in items if sub in tags(x)]; A={x["slug"] for x in its}
            if len(A)<8 or len(A)>.75*len(items): continue
            if any(len(A&B)/len(A)>=.7 for B in existing_sets): continue
            if any(len(A&B)/len(A|B)>=.7 for f,B in tasksets.items() if f!=s): continue
            if any(len(A&B)/min(len(A),len(B))>=.7 for B in made): continue
            made.append(A); out.append((f"{s}-{sub}",s,sub,its))
    return out
