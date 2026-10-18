"""Sub-task sections, sibling counts and open-source repo tables for /tasks/ and /categories/ pages (TAAFT-style task template, Oct 18 2026).
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
("video","video",r"video"),
("images-design","images and design",r"\bimages?\b|design|diagram|visual"),
("games","games",r"\bgames?\b|NPC|Minecraft"),
("personal-assistants","personal assistants",r"personal (assistant|agent)|errands|always-on|your day"),
("mobile","mobile and remote control",r"mobile|phone app|iOS|Android"),
("rules-config","rules, skills and config",r"\brules\b|skills|configur|settings"),
]
_RX=[(s,l,re.compile(r,re.I)) for s,l,r in SUBTASKS]
def tags(x):
    d=f'{x.get("name","")} {x.get("description","")}'
    return [s for s,_,r in _RX if r.search(d)]
LABEL={s:l for s,l,_ in SUBTASKS}
def sections(items,min_n=3,max_share=.75,min_page=12):
    """Return [(slug,label,[tools])...] + others list, or None when the page should stay flat."""
    if len(items)<min_page: return None
    tg={id(x):tags(x) for x in items}; n=len(items)
    cnt={}
    for x in items:
        for s in tg[id(x)]: cnt[s]=cnt.get(s,0)+1
    elig=[s for s,_,_ in SUBTASKS if cnt.get(s,0)>=min_n and cnt[s]<=max_share*n]
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
    tr="".join(f'<tr><td><a href="{d}tools/{x["slug"]}.html">{e(x["name"])}</a> <a href="{e(x["github"])}" target="_blank" rel="noopener noreferrer" aria-label="{e(x["name"])} on GitHub">↗</a></td><td>{s:,}</td><td>{e(l) or "—"}</td>'+(f'<td>{e(p[:10]) or "—"}</td>' if haspush else "")+'</tr>' for x,s,l,p in rows)
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
