"""AI-cited directory pages, step 1 (Oct 22 2026, owner-approved):
- /mcp/pricing.html: dated MCP server pricing table, from tools.json
- /mcp/link-status.html: dated MCP link-status table, from data/mcp_link_status.json (scripts/check_mcp_links.py)
- change history on both pages, kept in data/mcp_history.json (a snapshot diff each build; only real changes are logged)
- /.well-known/agent-card.json and /.well-known/agent.json: read-only description of the directory (no endpoints that don't exist)
Every count, label and date is read from the data files at build time. Never names other directories."""
import json,os,datetime as d,zoneinfo as z
import build_extras as X
B=X.B; e=X.e
PT=z.ZoneInfo("America/Los_Angeles")
HIST="data/mcp_history.json"; SNAP="data/mcp_snapshot.json"; LS="data/mcp_link_status.json"
def today(): return d.datetime.now(PT).date().isoformat()
def nice(s):
    try: return d.date.fromisoformat(s[:10]).strftime("%b %-d, %Y")
    except Exception: return s
def mcp(t):
    try: A={a["slug"]:a for a in json.load(open("api/tools.json"))["tools"]}
    except Exception: A={}
    return sorted([{**A.get(x["slug"],{}),**x} for x in t if x.get("category")=="MCP servers"],key=lambda x:x["name"].lower())
def ptype(x):
    p=(x.get("pricing") or "").lower(); tag=(x.get("price_tag") or "").lower()
    if tag in("free","freemium","paid"): return tag
    if "free" in p and any(k in p for k in("paid","pro","$","plan","tier","usage","credit")): return "freemium"
    if "free" in p or "open source" in p or "open-source" in p: return "free"
    return "paid" if p else "unknown"
def lstat(codes):
    if not codes: return ("not checked","")
    worst=None
    for c in codes.values():
        s=("ok" if 200<=c<400 or c==405 else "blocked" if c in(401,403,429) else "broken")
        if worst is None or ["ok","blocked","broken"].index(s)>["ok","blocked","broken"].index(worst): worst=s
    return ({"ok":"OK","blocked":"Reachable, blocks automated checks","broken":"Not responding" if 0 in codes.values() else "Error"}[worst],
            ", ".join(f"{k} {c if c else 'no response'}" for k,c in codes.items()))
def history(t,LSD):
    snap={x["slug"]:{"name":x["name"],"pricing":x.get("pricing",""),"link":lstat((LSD.get("results") or {}).get(x["slug"],{}))[0]} for x in mcp(t)}
    try: old=json.load(open(SNAP))
    except Exception: old=None
    try: H=json.load(open(HIST))
    except Exception: H=[]
    day=today(); ev=[]
    if old is None: ev.append(f"Tables started with {len(snap)} MCP servers.")
    else:
        for s,v in snap.items():
            o=old.get(s)
            if o is None: ev.append(f"Added {v['name']} (pricing: {v['pricing'] or 'not stated'}).")
            else:
                if o["pricing"]!=v["pricing"]: ev.append(f"{v['name']} pricing changed from \"{o['pricing']}\" to \"{v['pricing']}\".")
                if o["link"]!=v["link"] and "not checked" not in (o["link"],v["link"]): ev.append(f"{v['name']} link status changed from {o['link']} to {v['link']}.")
        for s,o in old.items():
            if s not in snap: ev.append(f"Removed {o['name']}.")
    if ev:
        if H and H[-1]["date"]==day: H[-1]["changes"]+= [x for x in ev if x not in H[-1]["changes"]]
        else: H.append({"date":day,"changes":ev})
        json.dump(H,open(HIST,"w"),indent=1)
    if old!=snap: json.dump(snap,open(SNAP,"w"),indent=1,sort_keys=True)
    return H
def hist_html(H):
    if not H: return ""
    r=['<h2 style="font-size:18px;margin:28px 0 6px">Change history</h2><p class="muted">Logged automatically each time the site is rebuilt, newest first (Pacific dates).</p><ul>']
    for h in reversed(H[-60:]):
        ch=h["changes"]; more=f" <span class=\"muted\">(+{len(ch)-25} more)</span>" if len(ch)>25 else ""
        r.append(f'<li><b>{e(nice(h["date"]))}</b>: '+" ".join(e(c) for c in ch[:25])+more+"</li>")
    return "".join(r)+"</ul>"
def tbl(head,rows):
    return ('<div style="overflow-x:auto;max-width:100%"><table class="cmp-table" style="width:100%;border-collapse:collapse;font-size:14px"><thead><tr>'+
            "".join(f'<th style="text-align:left;padding:6px 8px;border-bottom:1px solid #ddd">{h}</th>' for h in head)+"</tr></thead><tbody>"+
            "".join("<tr>"+"".join(f'<td style="padding:6px 8px;border-bottom:1px solid #eee;vertical-align:top;overflow-wrap:anywhere">{c}</td>' for c in r)+"</tr>" for r in rows)+"</tbody></table></div>")
def pages(t):
    LSD=json.load(open(LS)) if os.path.exists(LS) else {}
    H=history(t,LSD); M=mcp(t); upd=X.json.load(open("api/tools.json")).get("last_checked","") if os.path.exists("api/tools.json") else today()
    upd=upd or today(); os.makedirs("mcp",exist_ok=True); urls=[]
    cnt={k:sum(1 for x in M if ptype(x)==k) for k in("free","freemium","paid","unknown")}
    link=lambda x:f'<a href="../tools/{e(x["slug"])}.html">{e(x["name"])}</a>'
    # pricing
    canon=B+"mcp/pricing.html"; title=f"MCP server pricing table ({nice(upd)}) · AgentScout"
    desc=f"Pricing for all {len(M)} MCP servers in AgentScout: {cnt['free']} free, {cnt['freemium']} free plus paid plans, {cnt['paid']} paid. As stated by makers, dated {nice(upd)}."[:158]
    rows=[[link(x),e(x.get("pricing") or "Not stated"),{"free":"Free","freemium":"Free + paid","paid":"Paid","unknown":"Not stated"}[ptype(x)],"Yes" if x.get("open_source") else "No",f'{int(x["github_stars"]):,}' if x.get("github_stars") else "–"] for x in M]
    body=(f'<section style="padding-top:28px"><h1>MCP server pricing table</h1><p class="lede">Pricing for all {len(M)} MCP servers listed on AgentScout, as each maker states it. Data as of <time datetime="{e(upd)}">{e(nice(upd))}</time> (Pacific).</p>'
          f'<p>{cnt["free"]} free, {cnt["freemium"]} free with paid plans, {cnt["paid"]} paid'+(f', {cnt["unknown"]} not stated' if cnt["unknown"] else "")+'. Always confirm on the maker\'s site before you buy. See also the <a href="link-status.html">MCP link-status table</a>, <a href="./">best MCP servers by task</a> and the <a href="../categories/mcp-servers.html">MCP servers category</a>. The same data is in <a href="../api/tools.json">api/tools.json</a> and our <a href="connect.html">read-only MCP server</a>.</p>'
          +tbl(["MCP server","Pricing (as stated)","Type","Open source","GitHub stars"],rows)+hist_html(H)+"</section>")
    ld={"@context":"https://schema.org","@type":"Dataset","name":"MCP server pricing table","description":desc,"url":canon,"dateModified":upd,"creator":{"@type":"Organization","name":"AgentScout","url":B},"license":B+"about.html"}
    open("mcp/pricing.html","w").write(X.shell("../",title,desc,canon,body,ld)); urls.append(canon)
    # link status
    chk=LSD.get("checked",""); R=LSD.get("results") or {}
    st=[(x,)+lstat(R.get(x["slug"],{})) for x in M]
    ok=sum(1 for s in st if s[1]=="OK")
    canon=B+"mcp/link-status.html"; title=f"MCP server link status ({nice(chk) if chk else 'not yet checked'}) · AgentScout"
    desc=f"Link check for {len(M)} MCP servers on AgentScout: {ok} OK. Listing and GitHub links requested automatically, checked {nice(chk) if chk else 'soon'} (Pacific)."[:158]
    BROKEN=("Error","Not responding")  # only these are problems; "Reachable, blocks automated checks" answered, so it is not
    rows=[[link(x),e(s),e(c)] for x,s,c in sorted(st,key=lambda s:(0 if s[1] in BROKEN else 1,s[0]["name"].lower()))]
    brk=[x for x,s,c in st if s in BROKEN]; blk=sum(1 for s in st if s[1]=="Reachable, blocks automated checks"); unc=sum(1 for s in st if s[1]=="not checked")
    def _and(n): n=[f'<a href="../tools/{x["slug"]}.html">{e(x["name"])}</a>' for x in n]; return n[0] if len(n)==1 else ", ".join(n[:-1])+" and "+n[-1]
    extra=(f' ({blk} of them answered but block automated checks)' if blk else '')
    if not chk: qa=''
    elif not brk: qa=(f'All {len(M)-unc:,} checked MCP server links are reachable'+extra+(f'; {unc} not checked yet' if unc else '')+'.')
    else: qa=(f'{len(brk)} of {len(M):,} MCP server links did not respond or returned an error: {_and(brk[:5])}'+(f' and {len(brk)-5} more' if len(brk)>5 else '')+f'. The other {len(M)-len(brk)-unc:,} are reachable'+extra+'.')
    qa=f'<p class="qa"><b>Quick answer:</b> {qa}</p>' if qa else ''
    body=(f'<section style="padding-top:28px"><h1>MCP server link status</h1><p class="lede">Every MCP server on AgentScout, with the result of an automated request to its listed link and GitHub repo. Last checked <time datetime="{e(chk[:10])}">{e(chk)} PT</time>.</p>'+qa if chk else '<section style="padding-top:28px"><h1>MCP server link status</h1><p class="lede">Not checked yet.</p>')
    body+=(f'<p>{ok} of {len(M)} OK. "Reachable, blocks automated checks" means the site answered but refuses scripted requests (HTTP 401, 403 or 429); it usually works in a browser. HTTP 405 counts as OK because MCP endpoints often accept only POST. Links that did not respond or returned an error are listed first. See also the <a href="pricing.html">MCP pricing table</a> and <a href="connect.html">how to connect to the AgentScout MCP server</a>.</p>'
           +tbl(["MCP server","Status","HTTP result"],rows)+hist_html(H)+"</section>")
    ld={"@context":"https://schema.org","@type":"Dataset","name":"MCP server link status","description":desc,"url":canon,"dateModified":(chk[:10] or upd),"creator":{"@type":"Organization","name":"AgentScout","url":B}}
    open("mcp/link-status.html","w").write(X.shell("../",title,desc,canon,body,ld)); urls.append(canon)
    urls.append(connect_page(t))
    agent_cards(t)
    return urls
MCP_URL="https://agentscout-mcp.agentscouthq.workers.dev/mcp"  # public read-only MCP server (worker agentscout-mcp)
MCP_TOOLS=[("search_tools","Search by keyword, with optional category, pricing (free, freemium, paid), open-source and runs_locally filters. Up to 25 results."),
           ("get_tool","Full listing for one tool by its slug: features, platforms, GitHub repo and stars, AgentScout page."),
           ("list_categories","Every category with its tool count and page link."),
           ("best_for_task","Describe a task in plain words and get the most relevant tools, with optional pricing, open-source and runs_locally filters.")]
LOCAL_LINE="Optional runs_locally filter on search_tools and best_for_task: offline (runs fully on your own machine), self_hosted_or_offline (also tools you can deploy on your own server) or any. Each result has a data_locality label inferred from its listing; verify with the vendor before relying on it for compliance."
def connect_page(t):
    M=sum(1 for x in t if x.get("category")=="MCP servers"); canon=B+"mcp/connect.html"
    title="Connect to the AgentScout MCP server · AgentScout"
    desc=f"Free, read-only MCP server: search {len(t):,} AI agent tools and {M:,} MCP servers from Claude, Cursor, VS Code or any MCP client. No sign-up needed."  # full sentence, no truncation (Oct 23 2026)
    pre=lambda s:f'<pre style="overflow-x:auto;max-width:100%;white-space:pre;padding:12px;border-radius:8px;border:1px solid rgba(127,127,127,.3);font-size:13px"><code>{e(s)}</code></pre>'
    cfg='{\n  "mcpServers": {\n    "agentscout": {\n      "url": "'+MCP_URL+'"\n    }\n  }\n}'
    body=(f'<section style="padding-top:28px"><h1>Connect to the AgentScout MCP server</h1>'
          f'<p class="lede">Let your AI assistant search AgentScout directly. The server is free, read-only and needs no sign-up or key. It covers all {len(t):,} tools, including {M:,} MCP servers, with pricing as each maker states it.</p>'
          f'<p class="qa"><b>Quick answer:</b> add <code style="overflow-wrap:anywhere">{e(MCP_URL)}</code> as a remote MCP server (Streamable HTTP) in your client.</p>'
          '<h2>Server URL</h2>'+pre(MCP_URL)+
          '<h2>Add it to your client</h2><p><b>Claude Code</b></p>'+pre("claude mcp add --transport http agentscout "+MCP_URL)+
          '<p><b>Cursor, Windsurf and other clients that use an mcpServers file</b></p>'+pre(cfg)+
          '<p><b>VS Code</b>: run <i>MCP: Add Server</i>, choose HTTP and paste the server URL. <b>Claude.ai and Claude Desktop</b>: Settings, Connectors, Add custom connector, then paste the URL.</p>'
          '<h2>Tools</h2>'+tbl(["Tool","What it does"],[[f'<code>{n}</code>',e(d)] for n,d in MCP_TOOLS])+
          f'<p><b>Keep data on your side:</b> {e(LOCAL_LINE)}</p>'
          '<h2>Try asking</h2><ul><li>"Find free, open-source MCP servers for browser automation on AgentScout."</li><li>"What does AgentScout list for voice agents that make phone calls?"</li><li>"Show me the AgentScout listing for Cursor."</li><li>"Find no-code automation tools on AgentScout that I can self-host."</li></ul>'
          '<h2>Limits and data</h2><p>Read-only: the server can only look things up, it cannot change anything. Up to 60 requests per minute per IP address. Data comes from the same catalog as the site (<a href="../api/tools.json">api/tools.json</a>) and refreshes within about 10 minutes of each site update. Usage is counted anonymously: only the day, the tool used, the type of app and whether it was a public or test request. No IP addresses, search text or arguments are stored (see our <a href="../privacy.html">privacy policy</a>). '
          'Also see the <a href="pricing.html">MCP pricing table</a>, <a href="link-status.html">MCP link status</a>, the <a href="../openapi.json">OpenAPI description</a>, <a href="../llms.txt">llms.txt</a> and <a href="../llms-full.txt">llms-full.txt</a>.</p>'
          '<p style="font-size:14px;color:var(--muted);margin:10px 0 0"><b>Entity note:</b> AgentScout (also searched as Agent Scout or AgentScoutHQ) is the independent AI agent and MCP server directory at <a href="../index.html">https://agentscouthq.com</a>, published in the <a href="https://registry.modelcontextprotocol.io/v0/servers?search=com.agentscouthq/directory" rel="noopener">official MCP Registry</a> as <code>com.agentscouthq/directory</code> with endpoint <code>https://mcp.agentscouthq.com/mcp</code> (and <code>https://agentscout-mcp.agentscouthq.workers.dev/mcp</code>), and indexed on <a href="https://glama.ai/mcp/connectors/com.agentscouthq/directory" rel="noopener">Glama</a>, <a href="https://mcpservers.org/servers/agentscouthq-com-mcp-connect-html" rel="noopener">MCPServers.org</a>, <a href="https://sourceweft.com/mcp/com.agentscouthq%2Fdirectory" rel="noopener">SourceWeft</a>, and <a href="https://protogrid.dev/servers/com.agentscouthq/directory" rel="noopener">Protogrid</a>.</p></section>')
    _alt=["Agent Scout","AgentScoutHQ","agentscouthq.com"]
    _same=["https://x.com/AgentScoutHQ","https://github.com/Clampdown-web/agentscout","https://github.com/michaellk220-ops/agent-tool-finder","https://agentscout.beehiiv.com/","https://registry.modelcontextprotocol.io/v0/servers?search=com.agentscouthq/directory","https://glama.ai/mcp/connectors/com.agentscouthq/directory","https://mcpservers.org/servers/agentscouthq-com-mcp-connect-html","https://sourceweft.com/mcp/com.agentscouthq%2Fdirectory","https://protogrid.dev/servers/com.agentscouthq/directory"]
    ld={"@context":"https://schema.org","@type":"WebAPI","name":"AgentScout MCP server","alternateName":["com.agentscouthq/directory","AgentScout Directory MCP"],"identifier":"com.agentscouthq/directory","description":desc,"url":canon,"documentation":canon,"sameAs":_same,
        "provider":{"@type":"Organization","name":"AgentScout","alternateName":_alt,"url":B,"identifier":"com.agentscouthq/directory","sameAs":_same},"isAccessibleForFree":True,"potentialAction":{"@type":"SearchAction","target":MCP_URL}}
    open("mcp/connect.html","w").write(X.shell("../",title,desc,canon,body,ld))
    card={"$schema":"https://static.modelcontextprotocol.io/schemas/mcp-server-card/v1.json","name":"com.agentscouthq/directory","title":"AgentScout MCP server","version":"1.0.1","protocolVersion":"2025-06-18","endpoint":MCP_URL,
          "serverInfo":{"name":"agentscout","title":"AgentScout directory","version":"1.0.0"},
          "description":f"Read-only search over {len(t):,} AI agent tools and {M:,} MCP servers listed on AgentScout. No authentication.",
          "documentationUrl":canon,"transport":{"type":"streamable-http","endpoint":MCP_URL},"authentication":{"required":False},
          "capabilities":{"tools":{"listChanged":False}},"dataLocalityFilter":LOCAL_LINE,"tools":[{"name":n,"description":d} for n,d in MCP_TOOLS]}
    os.makedirs(".well-known",exist_ok=True); open(".well-known/mcp.json","w").write(json.dumps(card,indent=2,ensure_ascii=False)+"\n")
    return canon
def agent_cards(t):
    os.makedirs(".well-known",exist_ok=True); M=sum(1 for x in t if x.get("category")=="MCP servers")
    desc=f"AgentScout is a read-only directory of {len(t):,} AI agent tools, including {M:,} MCP servers, with link checks and pricing as makers state it. It has no chat or task endpoint; read the static JSON feeds below or use the read-only MCP server ({MCP_URL})."
    feeds=[{"id":"tools-catalog","name":"Full tool catalog","description":"Every listed tool with category, pricing, platforms, GitHub stars and listing URL.","url":B+"api/tools.json","mediaType":"application/json"},
           {"id":"openapi","name":"OpenAPI description","description":"OpenAPI 3.1 description of the read-only JSON feeds under /api/.","url":B+"openapi.json","mediaType":"application/json"},
           {"id":"llms-txt","name":"llms.txt","description":"Guide to the site for AI models.","url":B+"llms.txt","mediaType":"text/markdown"},
           {"id":"llms-full-txt","name":"llms-full.txt","description":"Full single-file Markdown context with category comparison tables and all verified MCP servers.","url":B+"llms-full.txt","mediaType":"text/markdown"},
           {"id":"mcp-pricing","name":"MCP server pricing table","url":B+"mcp/pricing.html","mediaType":"text/html"},
           {"id":"mcp-link-status","name":"MCP server link status","url":B+"mcp/link-status.html","mediaType":"text/html"},
           {"id":"mcp-server","name":"AgentScout MCP server (read-only, Streamable HTTP)","description":"Search tools, get one tool, list categories, best tools for a task. No authentication.","url":MCP_URL,"mediaType":"application/json"},
           {"id":"mcp-connect","name":"How to connect to the MCP server","url":B+"mcp/connect.html","mediaType":"text/html"},
           {"id":"sitemap","name":"Sitemap","url":B+"sitemap.xml","mediaType":"application/xml"}]
    card={"name":"AgentScout","description":desc,"url":B,"provider":{"organization":"AgentScout","url":B},"version":today(),
          "documentationUrl":B+"llms.txt","contact":"support@agentscouthq.com",
          "capabilities":{"streaming":False,"pushNotifications":False,"stateTransitionHistory":False},
          "interaction":"static, read-only files over HTTPS GET, plus a read-only MCP server (Streamable HTTP); no authentication; no A2A task endpoint",
          "defaultInputModes":[],"defaultOutputModes":["application/json","text/html","text/markdown"],
          "skills":[{"id":"find-ai-agent-tools","name":"Find AI agent tools","description":"Look up AI agent tools and MCP servers by category, pricing or name by reading api/tools.json.","tags":["directory","ai agents","mcp","tools"],"examples":["Which MCP servers are free?","List coding agents with open-source code."]}],
          "resources":feeds}
    s=json.dumps(card,indent=2,ensure_ascii=False)+"\n"
    for f in(".well-known/agent-card.json",".well-known/agent.json"): open(f,"w").write(s)
