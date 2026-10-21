"""Best MCP servers by task (Oct 21 2026, owner-approved): mcp/index.html hub + one page per task with >=5 MCP servers.
Membership is a hand-checked slug list per task (each listing's own description names the job); every count, star
figure, pricing label and date is read from tools.json / data/github.json / reviews.json at build time. Tasks with an
existing focused page (docs, cloud, design) or fewer than 5 solid servers are folded into the hub."""
import os,json,urllib.parse,collections
import build_extras as X, build_best as BB
B=X.B; e=X.e
MIN=5
try: GH=json.load(open("data/github.json"))
except Exception: GH={}
try: RV=json.load(open("reviews.json")).get("tools",{})
except Exception: RV={}
def pushed(x): return (GH.get(x["slug"]) or {}).get("pushed") or ""
def archived(x): return bool((GH.get(x["slug"]) or {}).get("archived"))
def rating(x):
    r=RV.get(x["slug"]) or {}; return (r.get("avg") or 0, r.get("count") or 0)
def rank(items):
    # 1) tracked GitHub stars, 2) visitor star rating, 3) most recent code push, 4) listing maturity, 5) name
    return sorted(items,key=lambda x:(x.get("github_stars") is None,-(x.get("github_stars") or 0),-rating(x)[0],
                                      "".join(chr(255-ord(c)) for c in pushed(x)) if pushed(x) else "~",BB.MAT(x),x["name"].lower()))
# slug, h1 job phrase, short label, intro, how-to-choose bullets, search keyword for the live directory filter, members
TASKS=[
("database-mcp-servers","databases","Databases","MCP servers that let Claude, Cursor, Codex and other MCP clients query and manage databases: Postgres, MySQL, MongoDB, Redis, ClickHouse, DuckDB, Neo4j and hosted platforms like Supabase, Neon and PlanetScale.",
 ["Start with the official server for the database you already run (Supabase, Neon, MongoDB, Redis, ClickHouse and others publish their own), then look at multi-database servers like MCP Toolbox for Databases or DBHub if you need several engines.",
  "Give the agent a read-only database user or a branch/staging copy first. Several of these servers can run writes and migrations.",
  "Check what the server exposes: plain SQL execution, schema browsing, or admin actions such as creating projects and branches."],"database",
 ["mcp-toolbox-for-databases","dbhub","postgres-mcp-pro","supabase-mcp","mongodb-mcp-server","clickhouse-mcp","neon-mcp","redis-mcp-server","motherduck-mcp","planetscale-mcp","upstash-mcp","neo4j-mcp","aiven-mcp","dbt-mcp","appwrite-mcp","stackql"]),
("web-search-and-scraping-mcp-servers","web search and scraping","Web search and scraping","MCP servers that give AI agents live web search, page reading and scraping, so they can look things up and pull data from websites instead of guessing.",
 ["Decide whether you need search results (Brave Search, SearXNG, Kagi, Linkup), full-page fetching and crawling (Wigolo, Oxylabs), or ready-made scrapers for specific sites (Apify, Bright Data).",
  "Hosted search and scraping APIs usually need an API key and bill by usage past any free allowance. SearXNG (self-hosted metasearch) and Wigolo (local, no API keys) avoid that, but you run them yourself.",
  "Respect each site's terms and robots rules when you scrape."],"web search",
 ["brave-search-mcp","searxng-mcp","kagi-mcp","linkup-mcp","parallel-search-mcp","anysearch","wigolo","bright-data-mcp","apify-mcp-server","scrapegraph-mcp","oxylabs-mcp","agentkey","liner-mcp"]),
("software-development-mcp-servers","GitHub, issues and CI","Code, issues and CI","MCP servers that connect coding agents to the rest of the software workflow: repositories and pull requests, issue trackers, CI pipelines, error tracking and code-quality tools, plus servers that help agents navigate large codebases.",
 ["Install the server for the platform your team already uses (GitHub, GitLab, Azure DevOps, Linear, Jira) before adding general tools.",
  "Scope tokens tightly. A repo or CI server with write access can open PRs, comment and re-run jobs on your behalf.",
  "For large codebases, a code-navigation server (Serena, Codebase Memory MCP, jCodeMunch) can cut how much code the agent has to read."],"issues",
 ["github-mcp-server","gitlab-mcp","gitkraken-mcp","azure-devops-mcp","linear-mcp","atlassian-rovo-mcp-server","sentry-mcp","circleci-mcp","buildkite-mcp","sonarqube-mcp-server","postman-mcp-server","serena","codebase-memory-mcp","jcodemunch-mcp","testkube-mcp","smartbear-mcp"]),
("monitoring-mcp-servers","monitoring and incidents","Monitoring and incidents","MCP servers that let agents read dashboards, logs, metrics and alerts, and work with incidents and uptime monitors, so an on-call engineer gets a first look before digging in.",
 ["Pick the server for the observability stack you already pay for (Grafana, New Relic, Axiom, Sentry, OneUptime, UptimeRobot).",
  "Start read-only: querying logs and metrics is low-risk, while creating monitors or changing incidents should stay behind approval.",
  "Large log queries can return a lot of text, so watch the model's context and token costs."],"monitor",
 ["grafana-mcp","oneuptime-mcp","new-relic-mcp","axiom-mcp","uptimerobot-mcp","sentry-mcp","cloudflare-mcp-servers"]),
("mcp-gateways-and-registries","running many MCP servers (gateways and registries)","Gateways and registries","Gateways, proxies, registries and hosting platforms for teams that run many MCP servers: one endpoint for agents, central auth and access policy, logging, and a catalog of approved servers.",
 ["If you only need to find servers, a registry (the official MCP Registry, Smithery) is enough. If you need one endpoint, auth and policy across many servers, look at a gateway.",
  "Open-source gateways (agentgateway, ContextForge, MetaMCP, MCPHub, Unla) can run on your own infrastructure; hosted platforms trade that for less setup.",
  "Check which transports each one supports (stdio, Streamable HTTP) and whether it can isolate servers in containers."],"gateway",
 ["kong-gateway","agentgateway","contextforge","metamcp","mcphub","unla","mcpo","mcp-proxy","toolhive","obot","archestra","jarvis-registry","klavis-ai","metorial","mcp-registry","smithery","observal"]),
("productivity-mcp-servers","Notion, Google Workspace and team apps","Productivity and team apps","MCP servers that connect AI assistants to everyday work apps: Google Workspace, Notion, Airtable, monday.com, Atlassian, Excel, meeting notes and automation hubs like Zapier and IFTTT.",
 ["Prefer the app maker's official server where one exists. It usually supports the app's own login and permissions.",
  "Automation hubs (Zapier, IFTTT) reach thousands of apps through one server, but each action runs through their platform and plan limits.",
  "Agents can send email and edit shared docs through some of these, so turn on confirmations for actions that other people see."],"workspace",
 ["google-workspace-mcp","notion-mcp","airtable-mcp","monday-com-mcp","atlassian-rovo-mcp-server","excel-mcp-server","zapier-mcp","ifttt-mcp","imcp","anytype-mcp","teamwork-com-mcp","fireflies-mcp"]),
("marketing-and-analytics-mcp-servers","marketing, SEO and analytics","Marketing, SEO and analytics","MCP servers from analytics, SEO and marketing platforms, so an agent can pull keyword, ranking, campaign and product-analytics data into its answers and reports.",
 ["Most of these are official servers from the data provider, so you need an account (and often a paid plan) with that provider.",
  "Match the server to the question: SEO research (SE Ranking, Serpstat, Frase, FlexQueries), product analytics (Amplitude, Statsig), or marketing and attribution data (Supermetrics, AppsFlyer, Polar Analytics).",
  "Check how each one counts usage, since some bill per query or per data row."],"analytics",
 ["amplitude-mcp","se-ranking-mcp","serpstat-mcp","frase-mcp","flexqueries","manifold-mcp","supermetrics-mcp","appsflyer-mcp","polar-analytics-mcp","parse-ly-mcp","statsig-mcp","gtmetrix-mcp","vidiq-mcp","beehiiv-mcp"]),
]
# Folded into the hub: an existing focused page already covers them, or fewer than MIN solid servers
FOLD=[("Docs for coding agents","Up-to-date library and API documentation for coding agents.",["context7","gitmcp","grounded-docs-mcp","microsoft-learn-mcp","stack-overflow-mcp","pg-aiguide"],("../tasks/coding-docs.html","All tools for feeding docs to coding agents")),
      ("Cloud and DevOps","Work with AWS, Azure, Google Cloud, Cloudflare, Kubernetes, Terraform and Vercel.",["aws-mcp-servers","cloudflare-mcp-servers","azure-mcp-server","kubernetes-mcp-server","terraform-mcp-server","cloud-run-mcp","vercel-mcp"],("../s/cloud-and-devops-mcp-servers.html","Cloud and DevOps MCP servers")),
      ("Figma and design","Read and edit designs in Figma, Canva and Webflow.",["framelink-figma-mcp","talk-to-figma-mcp","figma-console-mcp","figma-mcp-server","canva-mcp","webflow-mcp"],("../s/figma-and-design-mcp-servers.html","Figma and design MCP servers")),
      ("Payments and billing","Customers, payments, subscriptions and invoices.",["stripe-agent-toolkit","paypal-mcp","paddle-mcp","gocardless-mcp","slash"],None)]
SHORT={"marketing-and-analytics-mcp-servers":"SEO and analytics","mcp-gateways-and-registries":"gateways and registries","monitoring-mcp-servers":"monitoring and incidents","productivity-mcp-servers":"Notion and Google Workspace","software-development-mcp-servers":"GitHub, issues and CI","web-search-and-scraping-mcp-servers":"web search and scraping"}
def flink(q,d="../"): return f'{d}index.html?'+urllib.parse.urlencode({"cat":"MCP servers","q":q,"sort":"stars"})+"#directory"
def item(i,x):
    h=BB.item(i,x).replace('href="../','href="../')
    p=pushed(x); rv=rating(x)
    extra=(f' · Last code push {p}' if p else "")+(f' · Visitor rating {rv[0]:g}/5 ({rv[1]})' if rv[1] else "")
    return h.replace(f'· {e(x["maturity"])}</p></li>',f'· {e(x["maturity"])}{extra}</p></li>',1)
def mini(x):
    gs=f' · ★ {x["github_stars"]:,}' if x.get("github_stars") is not None else ""
    return f'<li style="margin:0 0 10px"><a href="../tools/{x["slug"]}.html" style="display:inline-flex;align-items:center;gap:8px;vertical-align:middle;max-width:100%">{X.ico(x,"../","sm").replace('width="40" height="40"','width="24" height="24"')}<b>{e(x["name"])}</b></a> <span class="b" style="font-size:12px">{e(x["pricing"])}</span><span class="muted" style="font-size:12.5px">{gs}</span><br><span style="color:var(--muted);font-size:14px">{e(x["description"])}</span></li>'
H2='style="font-size:18px;margin:32px 0 8px"'
def _catlink(made):
    p="categories/mcp-servers.html"
    if not os.path.exists(p): return
    z=open(p).read()
    if 'data-mcptask' in z or '<p class="updated">' not in z: return
    links=" · ".join(f'<a href="../mcp/{a[0]}.html">{e(a[2])}</a>' for a in made)
    z=z.replace('<p class="updated">',f'<p data-mcptask style="margin:8px 0;font-size:14px"><b>Best MCP servers by task:</b> {links} · <a href="../mcp/">All tasks</a></p><p class="updated">',1); open(p,"w").write(z)
def pages(t):
    os.makedirs("mcp",exist_ok=True); bs={x["slug"]:x for x in t}; asof=max(x["verified"] for x in t)
    def members(L): return [bs[s] for s in dict.fromkeys(L) if s in bs and BB.live(bs[s]) and not archived(bs[s])]
    made=[]; urls=[]
    for s,job,lab,intro,how,kw,L in TASKS:
        it=rank(members(L))
        if len(it)<MIN: print("mcp task page skipped (too few):",s,len(it)); continue
        made.append((s,job,lab,intro,how,kw,it))
    nmcp=sum(1 for x in t if x["category"]=="MCP servers")
    for s,job,lab,intro,how,kw,it in made:
        n=len(it); canon=f"{B}mcp/{s}.html"; h1=f"Best MCP servers for {job}"
        title=f"{h1} (2026): {n} ranked · AgentScout"
        if len(title)>70: title=f"Best MCP servers for {SHORT.get(s,lab)} (2026) · AgentScout"
        desc=f"The {n} best MCP servers for {job} in 2026, ranked by GitHub stars, ratings and recent activity: {', '.join(x['name'] for x in it[:3])} and more."
        if len(desc)>158: desc=f"{n} MCP servers for {job}, ranked by GitHub stars and activity: {', '.join(x['name'] for x in it[:2])} and more. Pricing as stated."
        if len(desc)>158: desc=desc[:157].rsplit(" ",1)[0]+"…"
        osn=sum(1 for x in it if x["pricing"].startswith("Open source")); st=[x for x in it if x.get("github_stars")]
        pc=collections.Counter(x["pricing"] for x in it)
        faq=[(f"What are the best MCP servers for {job}?",f"Ranked by tracked GitHub stars, then visitor ratings and recent code activity, the top MCP servers for {job} in our directory are "+", ".join(x["name"] for x in it[:5])+". Stars show popularity, not fit, so try two or three on your own setup."),
             (f"Are there free MCP servers for {job}?",(f"{osn} of the {n} servers here are listed as open source" if osn else "None of the servers here are listed as open source")+". Pricing on this page, as each maker states it: "+", ".join(f"{k} ({v})" for k,v in pc.most_common())+". Open-source servers can still need a paid account with the service they connect to."),
             ("How does AgentScout rank these MCP servers?","By the GitHub stars recorded on each listing, then visitor star ratings, then the most recent code push to the repo, then listing maturity. Servers without a tracked public repo come after those with one. There are no paid placements."),
             ("Which apps can use these MCP servers?","Any MCP client: Claude Desktop, Claude Code, Cursor, Codex, VS Code with Copilot, Windsurf and others. Each server's own docs give the exact config; our free MCP config builder can write the JSON for you.")]
        fq="".join(f'<h3 style="font-size:15px;margin:18px 0 4px">{e(a)}</h3><p style="margin:0">{e(b)}</p>' for a,b in faq)
        rel=" · ".join(f'<a href="{a[0]}.html">{e(a[2])}</a>' for a in made if a[0]!=s)
        facts=(f'<div class="badges" style="margin:0 0 18px"><span class="b">{n} MCP servers</span><span class="b">{osn} open source</span>'
               +(f'<span class="b">Most starred: {e(st[0]["name"])} (★ {st[0]["github_stars"]:,})</span>' if st else "")+'</div>')
        ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
            {"@type":"ItemList","name":h1,"itemListOrder":"https://schema.org/ItemListOrderDescending","numberOfItems":n,"itemListElement":[{"@type":"ListItem","position":i+1,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate(it)]},
            {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":a,"acceptedAnswer":{"@type":"Answer","text":b}} for a,b in faq]},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Best MCP servers by task","item":B+"mcp/"},{"@type":"ListItem","position":3,"name":h1,"item":canon}]}]}
        body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">MCP servers by task</a> / {e(lab)}</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left;margin-left:0">{e(h1)} (2026)</h1>'
              f'<p class="lede" style="margin-left:0;text-align:left">{e(intro)} Here are the {n} we list, ranked.</p>{facts}'
              f'<p class="muted" style="margin:0 0 18px"><strong>How we ranked them:</strong> each server here is listed in our <a href="../categories/mcp-servers.html">MCP servers category</a> and its listing says it does this job. We order them by the GitHub stars recorded on each listing, then visitor star ratings, then the most recent code push to the repo, then listing maturity. Servers without a tracked public repo come last. Links checked {asof}. No paid placements.</p>'
              f'<ol class="grid" style="padding:0;margin:0">{"".join(item(i+1,x) for i,x in enumerate(it))}</ol>'
              f'<p style="margin:18px 0 0"><a href="{flink(kw)}">Filter these live in the directory</a>: MCP servers matching “{e(kw)}”, sorted by GitHub stars. You can add pricing and open-source filters there.</p>'
              f'<h2 {H2}>How to choose</h2><ul>{"".join(f"<li>{e(b)}</li>" for b in how)}<li>Only connect servers you trust: an MCP server can read and act on whatever its credentials allow.</li></ul>'
              f'<h2 {H2}>FAQ</h2>{fq}'
              f'<h2 {H2}>Related tasks</h2><p>{rel} · <a href="index.html">All MCP servers by task</a></p>'
              f'<p>More: <a href="../categories/mcp-servers.html">All {nmcp} MCP servers</a> · <a href="../s/free-mcp-servers.html">Free MCP servers</a> · <a href="../best/mcp-servers-for-claude-code.html">For Claude Code</a> · <a href="../best/mcp-servers-for-cursor.html">For Cursor</a> · <a href="../free-tools/mcp-config-builder.html">MCP config builder</a></p>'
              f'<p class="disclose">Facts come from our directory listings and each project\'s GitHub repo; pricing is as each maker states it and can change. Missing a server? <a href="../submit.html">Submit it free</a>.</p></section>')
        open(f"mcp/{s}.html","w").write(X.shell("../",title,desc,canon,body,ld)); urls.append(canon)
    # hub
    canon=B+"mcp/"; title="Best MCP Servers by Task (2026): Ranked Picks · AgentScout"
    tot=len({x["slug"] for a in made for x in a[6]}|{s for f in FOLD for s in f[2] if s in bs})
    desc=f"The best MCP servers by task in 2026: databases, web search, GitHub and CI, monitoring, gateways, productivity and marketing. {tot} servers, ranked."[:158]
    secs=""
    for s,job,lab,intro,how,kw,it in made:
        secs+=(f'<h2 id="{s}" {H2}><a href="{s}.html">Best MCP servers for {e(job)}</a></h2><p class="muted" style="margin:0 0 10px;font-size:14px">{e(intro)}</p>'
               f'<ul style="list-style:none;padding:0;margin:0">{"".join(mini(x) for x in it[:4])}</ul><p style="margin:4px 0 0"><a href="{s}.html">See all {len(it)} ranked →</a></p>')
    fold=""
    for lab,txt,L,lnk in FOLD:
        it=rank(members(L))
        if not it: continue
        fold+=(f'<h3 style="font-size:16px;margin:22px 0 6px">{e(lab)}</h3><p class="muted" style="margin:0 0 8px;font-size:14px">{e(txt)}</p><ul style="list-style:none;padding:0;margin:0">{"".join(mini(x) for x in it)}</ul>'
               +(f'<p style="margin:4px 0 0"><a href="{lnk[0]}">{e(lnk[1])} →</a></p>' if lnk else ""))
    faq=[("What is the best MCP server?","It depends on the job. By tracked GitHub stars, the leaders on this page are "+", ".join(f"{a[6][0]['name']} for {a[1]}" for a in made[:4])+". Pick the task first, then compare two or three servers."),
         ("How are these MCP servers ranked?","Within each task, by the GitHub stars recorded on each listing, then visitor star ratings, then the most recent code push, then listing maturity. No paid placements."),
         ("Why do some tasks not have their own page?",f"We only build a task page when at least {MIN} solid MCP servers in our directory do that job and no other AgentScout page already covers the same list. Docs, cloud and design already have focused pages, and payments has fewer than {MIN} servers, so they're listed here instead."),
         ("How many MCP servers does AgentScout list?",f"{nmcp} in the MCP servers category, each with a link-checked listing. This page covers {tot} of them, grouped by task.")]
    fq="".join(f'<h3 style="font-size:15px;margin:18px 0 4px">{e(a)}</h3><p style="margin:0">{e(b)}</p>' for a,b in faq)
    jump=" · ".join(f'<a href="#{a[0]}">{e(a[2])}</a>' for a in made)+' · <a href="#more">More tasks</a>'
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B},"hasPart":[{"@type":"WebPage","name":f"Best MCP servers for {a[1]}","url":f"{B}mcp/{a[0]}.html"} for a in made]},
        {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":a,"acceptedAnswer":{"@type":"Answer","text":b}} for a,b in faq]},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Best MCP servers by task","item":canon}]}]}
    body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / MCP servers by task</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left;margin-left:0">Best MCP servers by task (2026)</h1>'
          f'<p class="lede" style="margin-left:0;text-align:left">MCP (Model Context Protocol) servers plug Claude, Cursor, Codex and other AI clients into your databases, apps and data. Instead of one giant list, start with the job you need done. Each task links to a ranked page with a short guide to choosing.</p>'
          f'<p style="font-size:14px">Jump to: {jump}</p>'
          f'<p class="muted" style="margin:0 0 6px;font-size:13.5px"><strong>How we ranked them:</strong> GitHub stars recorded on each listing, then visitor star ratings, then the most recent code push, then listing maturity. Every server is listed in our <a href="../categories/mcp-servers.html">MCP servers category</a>; links checked {asof}. No paid placements.</p>'
          f'{secs}<h2 id="more" {H2}>More tasks</h2>{fold}'
          f'<h2 {H2}>FAQ</h2>{fq}'
          f'<p style="margin-top:28px">More: <a href="../categories/mcp-servers.html">All {nmcp} MCP servers</a> · <a href="{flink("mcp").replace("&q=mcp","")}">Filter MCP servers by pricing and open source</a> · <a href="../s/free-mcp-servers.html">Free MCP servers</a> · <a href="../best/open-source-mcp-servers.html">Open-source MCP servers</a> · <a href="../best/mcp-servers-for-claude-code.html">For Claude Code</a> · <a href="../best/mcp-servers-for-cursor.html">For Cursor</a> · <a href="../best/mcp-servers-for-codex.html">For Codex</a> · <a href="../free-tools/mcp-server-picker.html">MCP server picker</a></p>'
          f'<p class="disclose">Facts come from our directory listings and each project\'s GitHub repo; pricing is as each maker states it and can change. Missing a server? <a href="../submit.html">Submit it free</a>.</p></section>')
    open("mcp/index.html","w").write(X.shell("../",title,desc,canon,body,ld)); urls.insert(0,canon)
    # inbound links (idempotent)
    BB.link_in("index.html",'<a href="s/index.html">Popular searches</a>',' · <a href="mcp/">Best MCP servers by task</a>','href="mcp/"')
    import atexit; atexit.register(_catlink,made)  # category pages are rewritten later in build_site, so link in at exit
    BB.link_in("llms.txt",f"- [Best MCP servers for Codex]({B}best/mcp-servers-for-codex.html)","\n"+f"- [Best MCP servers by task]({B}mcp/)"+"".join(f"\n- [Best MCP servers for {a[1]}]({B}mcp/{a[0]}.html)" for a in made),f"]({B}mcp/)")
    print("mcp task pages:",len(made),[(a[0],len(a[6])) for a in made])
    return urls
