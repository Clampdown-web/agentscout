"""AI-cited directory pages, step 1 (Oct 22 2026, owner-approved):
- /mcp/pricing.html: dated MCP server pricing table, from tools.json
- /mcp/status/: dated MCP status page, from data/mcp_link_status.json (scripts/check_mcp_links.py). /mcp/link-status.html is a noindex HTML forwarder.
- change history on both pages, kept in data/mcp_history.json (a snapshot diff each build; only real changes are logged)
- /.well-known/agent-card.json and /.well-known/agent.json: read-only description of the directory (no endpoints that don't exist)
Every count, label and date is read from the data files at build time. Never names other directories."""
import json,os,re,datetime as d,zoneinfo as z
import build_extras as X
B=X.B; e=X.e
PT=z.ZoneInfo("America/Los_Angeles")
HIST="data/mcp_history.json"; SNAP="data/mcp_snapshot.json"; LS="data/mcp_link_status.json"
def today(): return d.datetime.now(PT).date().isoformat()
def load_api_tools(path="api/tools.json"):
    """api/tools.json is either {"count","updated","tools":[...]} or a bare list."""
    data=json.load(open(path))
    if isinstance(data,list): return data,{}
    if isinstance(data,dict): return data.get("tools",[]),data
    return [],{}
def nice(s):
    try: return d.date.fromisoformat(s[:10]).strftime("%b %-d, %Y")
    except Exception: return s
def mcp(t):
    try:
        tools,_=load_api_tools()
        A={a["slug"]:a for a in tools}
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
    gh_ok=200<=codes.get("github",0)<400
    for c in codes.values():
        s=("ok" if 200<=c<400 or c==405 or (c in(401,403,429) and (gh_ok or len(codes)==1)) else "blocked" if c in(401,403,429) else "broken")
        if worst is None or ["ok","blocked","broken"].index(s)>["ok","blocked","broken"].index(worst): worst=s
    return ({"ok":"OK","blocked":"Reachable, blocks automated checks","broken":"Not responding" if 0 in codes.values() else "Error"}[worst],
            ", ".join(f"{k} {c if c else 'no response'}" for k,c in codes.items()))
def mcp_uptime_line(t=None):
    if t is None: t=json.load(open("tools.json"))
    M=mcp(t)
    LSD=json.load(open(LS)) if os.path.exists(LS) else {"checked":today(),"results":{}}
    chk=LSD.get("checked","") or today(); R=LSD.get("results") or {}
    st=[(x,)+lstat(R.get(x["slug"],{})) for x in M]
    ok=sum(1 for s in st if s[1]=="OK")
    return f"{ok} of {len(M)} MCP servers responded today (verified {nice(chk)})"
# Published reachability uses the same labels as /mcp/status/ (build_status._bucket): OK and
# "Reachable, blocks automated checks" are reachable. Counts and the date come only from
# tools.json plus data/mcp_link_status.json. A missing check file does not invent today's date.
REACH_OK=("OK","Reachable, blocks automated checks")
def mcp_reachability(t=None):
    if t is None: t=json.load(open("tools.json"))
    listed=[x for x in t if x.get("category")=="MCP servers"]
    try: raw=json.load(open(LS))
    except Exception: raw={}
    results=raw.get("results") or {}
    checked=str(raw.get("checked") or "").strip()
    day=checked[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?", checked) else ""
    by={}; reachable=down=unchecked=0
    for x in listed:
        codes=results.get(x["slug"])
        if not codes:
            status="not yet checked"; unchecked+=1
        else:
            label,_detail=lstat(codes)
            if label in REACH_OK:
                status="reachable"; reachable+=1
            elif label in ("Error","Not responding"):
                status="down"; down+=1
            else:
                status="not yet checked"; unchecked+=1
        by[x["slug"]]=status
    return {"reachable":reachable,"total":len(listed),"down":down,"not_yet_checked":unchecked,
            "checked":checked if day else "","day":day,"by_slug":by}
def reach_sentence(st):
    """Quotable line. Empty check file does not invent a date or a count."""
    if not st.get("day") or st.get("total") is None:
        return "The daily MCP reachability check has no timestamp on file yet."
    return f"Checked daily, {st['reachable']} of {st['total']} reachable, last checked {st['day']}."
def methodology_plain():
    return ("Once a day, AgentScout requests each listed MCP server URL and, when it is a different link, its GitHub URL. "
            "The request is HEAD, then GET, with a 20-second timeout. If that fails on TLS or gets no response, it retries once with a browser user agent. "
            "A server counts as reachable when its stored label is OK or Reachable, blocks automated checks. "
            "OK is HTTP 200-399 or 405, and also 401, 403 or 429 when the GitHub URL succeeded or that URL is the only one checked. "
            "Reachable, blocks automated checks means those 401, 403 or 429 responses without a harder error. "
            "Any other checked result is not reachable. A server missing from the check file is not yet checked and is not counted. "
            "The last-checked time is the checked field, in America/Los_Angeles. The rows are on the MCP status page and in status.json.")
def _reach_time(st):
    checked=st.get("checked") or ""
    dt=st["day"]+(("T"+checked[11:16]) if len(checked)>=16 else "")
    return f'<time datetime="{e(dt)}">{e(st["day"])}</time>'
def reach_sentence_html(st):
    if not st.get("day"):
        return e(reach_sentence(st))
    return f"Checked daily, {st['reachable']} of {st['total']} reachable, last checked {_reach_time(st)}."
def llms_reach_section(st=None):
    st=st or mcp_reachability()
    sentence=reach_sentence(st)
    return "\n".join(["<!-- mcp-reach:start -->","",
        "## MCP server reachability","",
        sentence,"",
        methodology_plain(),"",
        f"- [MCP server status]({B}mcp/status/): the same reachability rows, with HTTP result and history",
        f"- [status.json]({B}status.json): machine-readable rows for every listed MCP server",
        f"- [Best MCP servers by task]({B}mcp/): ranked lists, with the same daily check",
        "","<!-- mcp-reach:end -->"])
def stamp_llms_docs(st=None):
    """Put the reachability section in llms.txt and llms-full.txt. Idempotent. Does not rewrite the homepage."""
    st=st or mcp_reachability()
    section=llms_reach_section(st)
    sentence=reach_sentence(st)
    old=re.compile(r" \(\d+ of \d+ MCP servers responded today \(verified [^)]+\)\)")
    for path in ("llms.txt","llms-full.txt"):
        if not os.path.exists(path): continue
        s=open(path,encoding="utf-8").read()
        s2=old.sub(". "+sentence.rstrip("."), s, count=1)
        block=re.compile(r"\n?<!-- mcp-reach:start -->.*?<!-- mcp-reach:end -->\n?", re.S)
        if block.search(s2):
            s2=block.sub("\n\n"+section+"\n\n", s2, count=1)
        else:
            m=re.search(r"^> .*$", s2, re.M)
            if m:
                s2=s2[:m.end()]+"\n\n"+section+"\n"+s2[m.end():]
            else:
                s2=section+"\n\n"+s2
        s2=re.sub(r"\n{3,}","\n\n",s2)
        if s2!=s: open(path,"w",encoding="utf-8").write(s2)
    return sentence
_SEARCH={"@type":"SearchAction","target":{"@type":"EntryPoint","urlTemplate":"https://agentscouthq.com/?q={search_term_string}#directory"},"query-input":"required name=search_term_string"}
_Q_COUNT="How many listed MCP servers are reachable?"
_Q_HOW="How does AgentScout check which MCP servers are reachable?"
def _fit_desc(desc, n=156):
    desc=" ".join(str(desc).split())
    if len(desc)<=n: return desc
    cut=desc[:n].rsplit(" ",1)[0].rstrip(" ,;:-")
    return cut if cut.endswith(".") else cut+"."
def _set_desc(s, desc):
    v=e(desc)
    for pat in (r'(<meta name="description" content=")[^"]*(")', r'(<meta property="og:description" content=")[^"]*(")', r'(<meta name="twitter:description" content=")[^"]*(")'):
        s=re.sub(pat, lambda m, v=v: m.group(1)+v+m.group(2), s, count=1)
    return s
def _h1_text(s):
    m=re.search(r"<h1\b[^>]*>(.*?)</h1>", s, re.S)
    if not m: return ""
    return re.sub(r"\s+"," ", re.sub(r"<[^>]+>","", m.group(1))).replace("&amp;","&").strip()
def _status_href(path):
    if path.startswith("mcp/status/"): return "./"
    if path.startswith("mcp/"): return "status/"
    if path.startswith("categories/"): return "../mcp/status/"
    return "/mcp/status/"
def _json_href(path):
    if path.startswith("mcp/status/"): return "../../status.json"
    if path.startswith(("mcp/","categories/")): return "../status.json"
    return "/status.json"
def _reach_block(st, path):
    method=e(methodology_plain()).replace("MCP status page", f'<a href="{_status_href(path)}">MCP status page</a>').replace("status.json", f'<a href="{_json_href(path)}">status.json</a>')
    return ("<!--mcp:reach-->\n"
            f'<p class="qa" id="mcp-reach"><b>Quick answer:</b> {reach_sentence_html(st)}</p>\n'
            f'<h2 id="mcp-reachable">{e(_Q_COUNT)}</h2>\n<p>{reach_sentence_html(st)}</p>\n'
            f'<h2 id="mcp-check">{e(_Q_HOW)}</h2>\n<p>{method}</p>\n'
            "<!--/mcp:reach-->")
def _is_header_org(data):
    """The shared header's Organization script (it carries the logo). Do not add page schema to it."""
    nodes=data.get("@graph") if isinstance(data.get("@graph"), list) else [data]
    if not nodes or not isinstance(nodes[0], dict): return False
    org=nodes[0]
    return org.get("@type")=="Organization" and "logo" in org
def _patch_graph(s, st, meta_desc, faq, slugs=None, names=None, allow_list=True):
    def fix(m):
        try: data=json.loads(m.group(1))
        except Exception: return m.group(0)
        if not isinstance(data, dict): return m.group(0)
        if _is_header_org(data):
            org=(data["@graph"][0] if isinstance(data.get("@graph"), list) else data).copy()
            org.pop("@context", None)
            if isinstance(data.get("@graph"), list):
                return '<script type="application/ld+json">'+json.dumps({"@context":"https://schema.org",**org},ensure_ascii=False).replace("</","<\\/")+"</script>"
            return m.group(0)
        wrapped=False
        if isinstance(data.get("@graph"), list): graph=data["@graph"]
        elif data.get("@type"): graph=[data]; wrapped=True
        else: return m.group(0)
        for n in graph:
            if not isinstance(n, dict): continue
            part=n.get("isPartOf")
            if isinstance(part, dict) and part.get("@type")=="WebSite":
                part.setdefault("potentialAction", dict(_SEARCH))
            if meta_desc and n.get("@type") in ("CollectionPage","WebPage"):
                n["description"]=meta_desc
            if st.get("day") and n.get("@type") in ("CollectionPage","WebPage") and not n.get("dateModified"):
                n["dateModified"]=st["day"]
        desc=(reach_sentence(st)+" "+methodology_plain()) if st.get("day") else methodology_plain()
        def _is_reach(n):
            name=(n.get("name") or "").lower()
            return n.get("@type")=="Dataset" and (n.get("@id","").endswith("#reachability") or "reachab" in name or "link status" in name)
        ds=next((n for n in graph if isinstance(n, dict) and _is_reach(n)), None)
        fields={"@id":B+"mcp/status/#reachability","name":"AgentScout MCP server reachability","description":desc,"url":B+"mcp/status/",
                "measurementTechnique":"Daily HTTP HEAD then GET of each listed MCP server URL and its GitHub URL when different. America/Los_Angeles.",
                "variableMeasured":"reachable","isAccessibleForFree":True,
                "distribution":{"@type":"DataDownload","encodingFormat":"application/json","contentUrl":B+"status.json"}}
        if st.get("day"):
            fields["dateModified"]=st["day"]; fields["temporalCoverage"]=st["day"]
        if ds:
            ds.update(fields)
            ds.setdefault("creator",{"@type":"Organization","name":"AgentScout","url":B})
        else:
            graph.append({"@type":"Dataset","creator":{"@type":"Organization","name":"AgentScout","url":B},**fields})
        if not any(isinstance(n, dict) and (n.get("@type")=="WebSite" or (isinstance(n.get("isPartOf"), dict) and n["isPartOf"].get("potentialAction"))) for n in graph):
            graph.append({"@type":"WebSite","name":"AgentScout","url":B,"potentialAction":dict(_SEARCH)})
        for n in graph:
            if isinstance(n, dict) and n.get("@type")=="ItemList" and n.get("numberOfItems") is None and isinstance(n.get("itemListElement"), list):
                n["numberOfItems"]=len(n["itemListElement"])
        if allow_list and not any(isinstance(n, dict) and n.get("@type")=="ItemList" for n in graph):
            has=next((n.get("hasPart") for n in graph if isinstance(n, dict) and n.get("hasPart")), None)
            items=[{"@type":"ListItem","position":i+1,"name":p.get("name"),"url":p.get("url")} for i,p in enumerate(has or []) if isinstance(p, dict)]
            label="Best MCP servers by task" if items else "MCP servers"
            if not items and slugs:
                items=[{"@type":"ListItem","position":i+1,"name":(names or {}).get(slug, slug),"url":f"{B}tools/{slug}.html"} for i,slug in enumerate(slugs)]
            if items:
                graph.append({"@type":"ItemList","name":label,"numberOfItems":len(items),"itemListElement":items})
        if faq:
            ents=[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]
            fq=next((n for n in graph if isinstance(n, dict) and n.get("@type")=="FAQPage"), None)
            if fq is None:
                graph.append({"@type":"FAQPage","mainEntity":ents})
            else:
                have=fq.setdefault("mainEntity", [])
                by={q.get("name"):q for q in have if isinstance(q, dict)}
                for ent in ents:
                    if ent["name"] in by: by[ent["name"]]["acceptedAnswer"]=ent["acceptedAnswer"]
                    else: have.append(ent)
        if wrapped and len(graph)>1:
            ctx=data.get("@context","https://schema.org")
            data={"@context":ctx,"@graph":graph}
        elif wrapped:
            ctx=data.get("@context","https://schema.org")
            data=graph[0]; data["@context"]=ctx
        return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False).replace("</","<\\/")+"</script>"
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', fix, s, flags=re.S)
def stamp_mcp_pages(t=None):
    """Answer-first reachability block, methodology, and Dataset JSON-LD on /mcp/ pages and the MCP category.
    Skips the homepage, the shared header, and tool pages. Idempotent."""
    import glob
    if t is None: t=json.load(open("tools.json"))
    names={x.get("slug"):x.get("name") for x in t if x.get("slug")}
    st=mcp_reachability(t)
    sentence=reach_sentence(st)
    faq=[(_Q_COUNT, sentence), (_Q_HOW, methodology_plain())]
    tails={"mcp/index.html":"Best MCP servers by task: databases, web search, GitHub, monitoring, gateways and more.",
           "mcp/status/index.html":"Up, down and not-yet-checked for every listed MCP server.",
           "mcp/pricing.html":"Pricing for every listed MCP server, as each maker states it.",
           "categories/mcp-servers.html":"Every MCP server in the AgentScout directory."}
    paths=sorted(glob.glob("mcp/*.html"))+["mcp/status/index.html","categories/mcp-servers.html"]
    n=0
    old=re.compile(r"\d+ of \d+ MCP servers responded today \(verified [^)]+\)")
    for path in paths:
        if not os.path.exists(path): continue
        s=open(path,encoding="utf-8").read()
        if 'http-equiv="refresh"' in s[:4000]: continue
        s=old.sub(sentence.rstrip("."), s)
        slugs=[]
        for slug in re.findall(r'href="(?:\.\./)*tools/([a-z0-9-]+)\.html"', s):
            if slug in st["by_slug"] and slug not in slugs: slugs.append(slug)
        block=_reach_block(st, path)
        s=re.sub(r"<!--mcp:reach-->.*?<!--/mcp:reach-->","",s,flags=re.S)
        if path=="mcp/connect.html":
            m=re.search(r'(<p class="lede"[^>]*>.*?</p>)', s, flags=re.S)
            s=(s[:m.end()]+block+s[m.end()]) if m else s
            meta=None
        else:
            m=re.search(r"<h1\b[^>]*>.*?</h1>(\s*<div class=\"shareacts\">.*?</div>)?", s, flags=re.S)
            if m: s=s[:m.end()]+block+s[m.end():]
            tail=tails.get(path) or (_h1_text(s) or "MCP servers on AgentScout")
            meta=_fit_desc(sentence+" "+tail)
            s=_set_desc(s, meta)
        s=_patch_graph(s, st, meta, faq, slugs, names, allow_list=path!="mcp/connect.html")
        open(path,"w",encoding="utf-8").write(s); n+=1
    print(f"mcp reachability: stamped {n} pages; {sentence}")
    return st
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
    H=history(t,LSD); M=mcp(t); upd=""
    if os.path.exists("api/tools.json"):
        try:
            _,meta=load_api_tools(); upd=(meta.get("last_checked") or "") if isinstance(meta,dict) else ""
        except Exception: upd=""
    upd=upd or today(); os.makedirs("mcp",exist_ok=True); urls=[]
    cnt={k:sum(1 for x in M if ptype(x)==k) for k in("free","freemium","paid","unknown")}
    link=lambda x:f'<a href="../tools/{e(x["slug"])}.html">{e(x["name"])}</a>'
    # pricing
    canon=B+"mcp/pricing.html"; title=f"MCP server pricing table ({nice(upd)}) · AgentScout"
    desc=f"Pricing for all {len(M)} MCP servers in AgentScout: {cnt['free']} free, {cnt['freemium']} free plus paid plans, {cnt['paid']} paid. As stated by makers, dated {nice(upd)}."[:158]
    rows=[[link(x),e(x.get("pricing") or "Not stated"),{"free":"Free","freemium":"Free + paid","paid":"Paid","unknown":"Not stated"}[ptype(x)],"Yes" if x.get("open_source") else "No",f'{int(x["github_stars"]):,}' if x.get("github_stars") else "–"] for x in M]
    body=(f'<section style="padding-top:28px"><h1>MCP server pricing table</h1><p class="lede">Pricing for all {len(M)} MCP servers listed on AgentScout, as each maker states it. Data as of <time datetime="{e(upd)}">{e(nice(upd))}</time> (Pacific).</p>'
          f'<p>{cnt["free"]} free, {cnt["freemium"]} free with paid plans, {cnt["paid"]} paid'+(f', {cnt["unknown"]} not stated' if cnt["unknown"] else "")+'. Always confirm on the maker\'s site before you buy. See also the <a href="status/">MCP status</a>, <a href="./">best MCP servers by task</a> and the <a href="../categories/mcp-servers.html">MCP servers category</a>. The same data is in <a href="../api/tools.json">api/tools.json</a> and our <a href="connect.html">read-only MCP server</a>.</p>'
          +tbl(["MCP server","Pricing (as stated)","Type","Open source","GitHub stars"],rows)+hist_html(H)+"</section>")
    ld={"@context":"https://schema.org","@type":"Dataset","name":"MCP server pricing table","description":desc,"url":canon,"dateModified":upd,"creator":{"@type":"Organization","name":"AgentScout","url":B},"license":B+"about.html"}
    open("mcp/pricing.html","w").write(X.shell("../",title,desc,canon,body,ld)); urls.append(canon)
    import build_status
    urls.append(build_status.write_dashboard(t))
    urls.append(connect_page(t))
    agent_cards(t)
    return urls
MCP_URL="https://mcp.agentscouthq.com/mcp"  # public read-only MCP server (custom domain + worker agentscout-mcp)
MCP_TOOLS=[("search_tools","Search by keyword, with optional category, pricing (free, freemium, paid), open-source and runs_locally filters. Up to 25 results."),
           ("get_tool","Full listing for one tool by its slug: features, platforms, GitHub repo and stars, AgentScout page."),
           ("list_categories","Every category with its tool count and page link."),
           ("best_for_task","Describe a task in plain words and get the most relevant tools, with optional pricing, open-source and runs_locally filters."),
           ("list_packages","List AgentScout's 4 maker listing & sponsorship tiers ($0 Free, $15 Fast-Track, $49 30-Day Category Pin, $99/wk Weekly Sponsor) with direct Stripe Checkout URLs, plus the Made by AgentScout pre-trained bot catalog.")]
LOCAL_LINE="Optional runs_locally filter on search_tools and best_for_task: offline (runs fully on your own machine), self_hosted_or_offline (also tools you can deploy on your own server) or any. Each result has a data_locality label inferred from its listing; verify with the vendor before relying on it for compliance."
def connect_page(t):
    import build_counts
    _c=build_counts.require(t)
    M=_c["mcp_servers"]; canon=B+"mcp/connect.html"; uline=reach_sentence(mcp_reachability(t))
    title="AgentScout MCP Server (com.agentscouthq/directory) · Connect"
    desc=f"Official AgentScout MCP server (com.agentscouthq/directory): free, read-only access to {_c['tools']:,}+ AI agent tools & {M:,} MCP servers. No API key or x402 wallet."
    pre=lambda s:f'<pre style="overflow-x:auto;max-width:100%;white-space:pre;padding:12px;border-radius:8px;border:1px solid rgba(127,127,127,.3);font-size:13px"><code>{e(s)}</code></pre>'
    cfg='{\n  "mcpServers": {\n    "agentscout": {\n      "url": "'+MCP_URL+'"\n    }\n  }\n}'
    faqs=[
        ("Is AgentScout's MCP server free, or does it require x402 / a crypto wallet?",
         "AgentScout's official MCP server (com.agentscouthq/directory at https://agentscouthq.com/mcp/sse) is 100% free, public, and read-only, with no API key, crypto wallet, or x402 payment required. It is completely unrelated to the paid third-party x402 web-fetch package that shares a similar name."),
        ("What is AgentScout's official MCP Registry ID and endpoint URL?",
         f"AgentScout's official MCP Registry ID is com.agentscouthq/directory. You can connect via Streamable HTTP at {MCP_URL} or SSE at https://agentscouthq.com/mcp/sse with no sign-up or API key."),
        ("How many AI agent tools and MCP servers does the AgentScout MCP server cover?",
         f"The server searches {_c['tools']:,}+ curated AI agent tools and {M:,} MCP servers across {_c['categories']} categories. {uline}.")
    ]
    faq_html="".join(f'<details open class="faq" style="margin:10px 0;padding:12px 14px;border:1px solid var(--line);border-radius:10px;background:var(--card)"><summary style="font-weight:600;cursor:pointer">{e(q)}</summary><p style="margin:8px 0 0;color:var(--muted);line-height:1.55">{e(a)}</p></details>' for q,a in faqs)
    body=(f'<section style="padding-top:28px"><h1>Connect to the AgentScout MCP server (<code>com.agentscouthq/directory</code>)</h1>'
          f'<p class="lede">Let your AI assistant search AgentScout directly. AgentScout\'s official MCP server (<code>com.agentscouthq/directory</code> at <code>https://agentscouthq.com/mcp/sse</code>) is <strong>100% free, public, and read-only</strong> — no sign-up, API key, crypto wallet, or x402 payment required. It covers all {_c["tools"]:,}+ tools, including {M:,} MCP servers ({e(uline)}), with pricing as each maker states it.</p>'
          f'<p class="qa"><b>Quick answer:</b> add <code style="overflow-wrap:anywhere">{e(MCP_URL)}</code> (or <code style="overflow-wrap:anywhere">https://agentscouthq.com/mcp/sse</code>) as a remote MCP server in your client. Official MCP Registry ID: <code>com.agentscouthq/directory</code>.</p>'
          f'<p>AgentScout (agentscouthq.com) is not affiliated with other projects named AgentScout.</p>'
          '<figure style="margin:18px 0 24px;border-radius:14px;overflow:hidden;border:1px solid var(--border);background:#080810"><video autoplay loop muted playsinline preload="metadata" poster="../assets/animations/agentscout-mcp-terminal-poster.png" style="display:block;width:100%;height:auto;max-width:100%"><source src="../assets/animations/agentscout-mcp-terminal.mp4" type="video/mp4"></video></figure>'
          '<h2>Server URL</h2>'+pre(MCP_URL)+
          '<p style="font-size:14px;color:var(--muted);margin:6px 0 14px">Canonical SSE / discovery alias: <code>https://agentscouthq.com/mcp/sse</code> · Official MCP Registry ID: <code>com.agentscouthq/directory</code></p>'
          '<h2>Add it to your client</h2><p><b>Claude Code</b></p>'+pre("claude mcp add --transport http agentscout "+MCP_URL)+
          '<p><b>Cursor, Windsurf and other clients that use an mcpServers file</b></p>'+pre(cfg)+
          '<p><b>VS Code</b>: run <i>MCP: Add Server</i>, choose HTTP and paste the server URL. <b>Claude.ai and Claude Desktop</b>: Settings, Connectors, Add custom connector, then paste the URL.</p>'
          '<h2>Tools</h2>'+tbl(["Tool","What it does"],[[f'<code>{n}</code>',e(d)] for n,d in MCP_TOOLS])+
          f'<p><b>Keep data on your side:</b> {e(LOCAL_LINE)}</p>'
          '<h2>Try asking</h2><ul><li>"Find free, open-source MCP servers for browser automation on AgentScout."</li><li>"What does AgentScout list for voice agents that make phone calls?"</li><li>"Show me the AgentScout listing for Cursor."</li><li>"Find no-code automation tools on AgentScout that I can self-host."</li></ul>'
          '<h2>Limits and data</h2><p>Read-only: the server can only look things up, it cannot change anything. Up to 60 requests per minute per IP address. Data comes from the same catalog as the site (<a href="../api/tools.json">api/tools.json</a>) and refreshes within about 10 minutes of each site update. Usage is counted anonymously: only the day, the tool used, the type of app and whether it was a public or test request. No IP addresses, search text or arguments are stored (see our <a href="../privacy.html">privacy policy</a>). '
          'Also see the <a href="pricing.html">MCP pricing table</a>, <a href="status/">MCP status</a> ('+e(uline)+'), the <a href="../openapi.json">OpenAPI description</a>, <a href="../llms.txt">llms.txt</a> and <a href="../llms-full.txt">llms-full.txt</a>.</p>'
          '<h2 id="faq">Frequently asked questions</h2>'+faq_html+
          '<p style="font-size:14px;color:var(--muted);margin:14px 0 0"><b>Entity note:</b> AgentScout (also searched as Agent Scout or AgentScoutHQ) is the independent AI agent and MCP server directory at <a href="../index.html">https://agentscouthq.com</a>, published in the <a href="https://registry.modelcontextprotocol.io/v0/servers?search=com.agentscouthq/directory" rel="noopener noreferrer">official MCP Registry</a> as <code>com.agentscouthq/directory</code> with endpoint <code>https://agentscouthq.com/mcp/sse</code> (and <code>https://agentscout-mcp.agentscouthq.workers.dev/mcp</code>), and indexed on <a href="https://glama.ai/mcp/connectors/com.agentscouthq/directory" rel="noopener noreferrer">Glama</a>, <a href="https://mcpservers.org/servers/agentscouthq-com-mcp-connect-html" rel="noopener noreferrer">MCPServers.org</a>, <a href="https://sourceweft.com/mcp/com.agentscouthq%2Fdirectory" rel="noopener noreferrer">SourceWeft</a>, and <a href="https://protogrid.dev/servers/com.agentscouthq/directory" rel="noopener noreferrer">Protogrid</a>. It is 100% free and read-only, and is unrelated to any paid third-party x402 web-fetch tool.</p></section>')
    _alt=["Agent Scout","AgentScoutHQ","agentscouthq.com","com.agentscouthq/directory"]
    _same=["https://x.com/clampdown19","https://x.com/AgentScoutHQ","https://agentscout.beehiiv.com/","https://github.com/clampdown19/agentscout","https://github.com/Clampdown-web/agentscout","https://registry.modelcontextprotocol.io/v0/servers?search=com.agentscouthq/directory","https://glama.ai/mcp/connectors/com.agentscouthq/directory","https://mcpservers.org/servers/agentscouthq-com-mcp-connect-html","https://sourceweft.com/mcp/com.agentscouthq%2Fdirectory","https://protogrid.dev/servers/com.agentscouthq/directory"]
    ld={"@context":"https://schema.org","@graph":[
        {"@type":"WebAPI","name":"AgentScout MCP server (com.agentscouthq/directory)","alternateName":["com.agentscouthq/directory","AgentScout Directory MCP"],"identifier":"com.agentscouthq/directory","description":desc,"url":canon,"documentation":canon,"sameAs":_same,
         "provider":{"@type":"Organization","name":"AgentScout","alternateName":_alt,"url":B,"identifier":"com.agentscouthq/directory","sameAs":_same},"isAccessibleForFree":True,"potentialAction":{"@type":"SearchAction","target":MCP_URL}},
        {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faqs]},
        {"@type":"VideoObject","name":"AgentScout MCP Command Center & Zero-Auth Setup","description":"Animated terminal walkthrough showing how to connect Claude Code, Cursor, and Windsurf to AgentScout's free MCP server (com.agentscouthq/directory).","thumbnailUrl":B+"assets/animations/agentscout-mcp-terminal-poster.png","contentUrl":B+"assets/animations/agentscout-mcp-terminal.mp4","uploadDate":"2026-10-26T18:00:00-07:00","duration":"PT20S"}
    ]}
    open("mcp/connect.html","w").write(X.shell("../",title,desc,canon,body,ld))
    card={"$schema":"https://static.modelcontextprotocol.io/schemas/mcp-server-card/v1.json","name":"com.agentscouthq/directory","title":"AgentScout MCP server","version":"1.0.2","protocolVersion":"2025-06-18","endpoint":MCP_URL,
          "serverInfo":{"name":"agentscout","title":"AgentScout directory","version":"1.0.2"},
          "description":f"Read-only search over {_c['tools']:,}+ AI agent tools and {M:,} MCP servers listed on AgentScout (com.agentscouthq/directory at https://agentscouthq.com/mcp/sse). 100% free, public, no authentication or x402 wallet required.",
          "documentationUrl":canon,"transport":{"type":"streamable-http","endpoint":MCP_URL},"authentication":{"required":False},
          "capabilities":{"tools":{"listChanged":False}},"dataLocalityFilter":LOCAL_LINE,"tools":[{"name":n,"description":d} for n,d in MCP_TOOLS]}
    os.makedirs(".well-known",exist_ok=True); open(".well-known/mcp.json","w").write(json.dumps(card,indent=2,ensure_ascii=False)+"\n")
    srv_reg={"$schema":"https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json","name":"com.agentscouthq/directory","title":"AgentScout",
             "description":f"Read-only search over {_c['tools']:,}+ AI agent tools and {M:,} MCP servers. Free, no sign-up needed.",
             "version":"1.0.2","websiteUrl":canon,"remotes":[{"type":"streamable-http","url":MCP_URL}]}
    open("server.json","w").write(json.dumps(srv_reg,indent=2,ensure_ascii=False)+"\n")
    if os.path.isdir("/workspace/mcp-registry"):
        try: open("/workspace/mcp-registry/server.json","w").write(json.dumps(srv_reg,indent=2,ensure_ascii=False)+"\n")
        except Exception: pass
    return canon
def agent_cards(t):
    os.makedirs(".well-known",exist_ok=True)
    import build_counts
    _c=build_counts.require(t); M=_c["mcp_servers"]
    desc=f"AgentScout is a read-only directory of {_c['tools']:,} AI agent tools, including {M:,} MCP servers, with link checks and pricing as makers state it. It has no chat or task endpoint; read the static JSON feeds below or use the read-only MCP server ({MCP_URL})."
    feeds=[{"id":"tools-catalog","name":"Full tool catalog","description":"Every listed tool with category, pricing, platforms, GitHub stars and listing URL.","url":B+"api/tools.json","mediaType":"application/json"},
           {"id":"products-feed","name":"Purchasable Stripe packages & bot catalog (ACP feed)","description":"Machine-readable product feed for AgentScout's 4 maker listing tiers ($0, $15, $49, $99/wk) with Stripe Checkout URLs and Made by AgentScout pre-trained bots.","url":B+"api/products.json","mediaType":"application/json"},
           {"id":"acp-feed","name":"Agentic Commerce Protocol (ACP) feed","description":"Well-known mirror of the AgentScout Stripe Agentic Commerce product feed.","url":B+".well-known/acp.json","mediaType":"application/json"},
           {"id":"ai-plugin","name":"AI Plugin manifest","description":"AI plugin manifest with prompt-engineered description_for_model and OpenAPI/MCP links.","url":B+".well-known/ai-plugin.json","mediaType":"application/json"},
           {"id":"openapi","name":"OpenAPI 3.1 description (JSON)","description":"OpenAPI 3.1 JSON specification of the read-only JSON feeds under /api/.","url":B+"openapi.json","mediaType":"application/json"},
           {"id":"openapi-yaml","name":"OpenAPI 3.1 description (YAML)","description":"OpenAPI 3.1 YAML specification of the read-only JSON feeds under /api/.","url":B+"openapi.yaml","mediaType":"application/yaml"},
           {"id":"web-manifest","name":"Web App Manifest","description":"Brand manifest with AgentScout icons and theme colors (#0B0F19 / #0EA5E9).","url":B+"manifest.json","mediaType":"application/manifest+json"},
           {"id":"llms-txt","name":"llms.txt","description":"Guide to the site for AI models.","url":B+"llms.txt","mediaType":"text/markdown"},
           {"id":"llms-full-txt","name":"llms-full.txt","description":"Full single-file Markdown context with category comparison tables and all verified MCP servers.","url":B+"llms-full.txt","mediaType":"text/markdown"},
           {"id":"mcp-pricing","name":"MCP server pricing table","url":B+"mcp/pricing.html","mediaType":"text/html"},
           {"id":"mcp-link-status","name":"MCP server status","url":B+"mcp/status/","mediaType":"text/html"},
           {"id":"mcp-server","name":"AgentScout MCP server (read-only, Streamable HTTP)","description":"Search tools, get one tool, list categories, best tools for a task, and list Stripe packages/bots. No authentication.","url":MCP_URL,"mediaType":"application/json"},
           {"id":"mcp-connect","name":"How to connect to the MCP server","url":B+"mcp/connect.html","mediaType":"text/html"},
           {"id":"sitemap","name":"Sitemap","url":B+"sitemap.xml","mediaType":"application/xml"}]
    card={"name":"AgentScout","description":desc,"url":B,"provider":{"organization":"AgentScout","url":B},"version":today(),
          "documentationUrl":B+"llms.txt","contact":"support@agentscouthq.com",
          "capabilities":{"streaming":False,"pushNotifications":False,"stateTransitionHistory":False},
          "interaction":"static, read-only files over HTTPS GET, plus a read-only MCP server (Streamable HTTP); no authentication; no A2A task endpoint",
          "defaultInputModes":[],"defaultOutputModes":["application/json","text/html","text/markdown"],
          "skills":[{"id":"find-ai-agent-tools","name":"Find AI agent tools","description":"Look up AI agent tools and MCP servers by category, pricing or name by reading api/tools.json or calling the MCP server at https://mcp.agentscouthq.com/mcp.","tags":["directory","ai agents","mcp","tools"],"examples":["Which MCP servers are free?","List coding agents with open-source code."]},{"id":"compare-packages-and-bots","name":"Compare Stripe listing packages & Made by AgentScout bots","description":"Read api/products.json (or /.well-known/acp.json) to compare AgentScout's 4 maker listing tiers ($0, $15, $49, $99/wk) with direct Stripe Checkout URLs and Made by AgentScout pre-trained bot templates.","tags":["commerce","stripe","sponsorship","bot templates"],"examples":["How much does a 30-day category pin on AgentScout cost?","What pre-trained bots does AgentScout offer?"]}],
          "resources":feeds}
    s=json.dumps(card,indent=2,ensure_ascii=False)+"\n"
    for f in(".well-known/agent-card.json",".well-known/agent.json"): open(f,"w").write(s)
