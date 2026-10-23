"""Hand-written, keyword-targeted titles/descriptions for new pages (Oct 21 2026 owner-approved SEO pass).
data/seo_overrides.json: {path: [title or null, description or null]}; {crypto_n} = live crypto count.
Also appends the 50 community Grok Bot templates to llms.txt. Idempotent; runs after build_seo.run()."""
import json,re,html,os
def _set(s,attr,name,v):
    return re.sub(rf'(<meta {attr}="{re.escape(name)}" content=")[^"]*(")',lambda m:m.group(1)+v+m.group(2),s,1)
def run(t):
    O=json.load(open("data/seo_overrides.json")); n=0
    cn=sum(1 for x in t if x["category"]=="crypto")
    for f,(ti,de) in O.items():
        if not os.path.exists(f): continue
        s0=s=open(f).read()
        if ti:
            v=html.escape(ti,quote=True)
            s=re.sub(r"<title>.*?</title>",f"<title>{v}</title>",s,1,flags=re.S)
            s=_set(s,"property","og:title",v); s=_set(s,"name","twitter:title",v)
        if de:
            m=re.search(r"(\d+) ready-made",s); v=html.escape(de.replace("{crypto_n}",str(cn)).replace("{mcp_n}",str(sum(1 for x in t if x["category"]=="MCP servers"))).replace("{bt_n}",m.group(1) if m else ""),quote=True)
            s=_set(s,"name","description",v); s=_set(s,"property","og:description",v); s=_set(s,"name","twitter:description",v)
        if s!=s0: open(f,"w").write(s); n+=1
    if os.path.exists("llms.txt") and os.path.exists("data/bot-templates-community.json"):
        L=open("llms.txt").read(); L=re.sub(r"\n?<!-- cb:start -->.*?<!-- cb:end -->\n?","\n",L,flags=re.S).rstrip()+"\n"
        cb=json.load(open("data/bot-templates-community.json"))
        L+="\n<!-- cb:start -->\n## Community Grok Bot templates\n\n"+"\n".join(f"- [{e['name']}](https://agentscouthq.com/bot-templates/#{e['id']}): {e['desc']}" for e in cb)+"\n<!-- cb:end -->\n"
        open("llms.txt","w").write(L)
    print("seo overrides:",n,"pages"); crypto_links(t); bt_rename(); long_titles(); answer_blocks(t); mcp_links()

# Crypto guide links (Oct 21 2026): crypto category + every crypto tool page link the two crypto guides.
def crypto_links(t):
    G=[("../mcp/crypto-mcp-servers.html","Best MCP servers for crypto and on-chain data"),("../mcp/crypto-wallet-mcp-servers.html","Best MCP servers for crypto wallets"),("../s/ai-crypto-scam-checkers.html","AI crypto wallet scam and risk checkers")]
    n=0
    files=["categories/crypto.html"]+[f"tools/{x['slug']}.html" for x in t if x["category"]=="crypto"]
    for f in files:
        if not os.path.exists(f): continue
        s0=s=open(f).read(); s=re.sub(r"<!--sn:cg-->.*?<!--/sn:cg-->","",s,flags=re.S)
        blk='<!--sn:cg--><h2 style="font-size:16px;margin:28px 0 10px">Crypto guides</h2><div class="badges">'+"".join(f'<a class="b uc" href="{h}">{html.escape(l)}</a>' for h,l in G)+'</div><!--/sn:cg-->'
        s=s.replace("</main>",blk+"</main>",1)
        if s!=s0: open(f,"w").write(s); n+=1
    print("crypto guide links:",n)

# Rename "Bot templates" -> "AI bot templates" in nav/footer/home/breadcrumbs (owner, Oct 21 2026 7:49 PM PT). URL unchanged.
def bt_rename():
    import glob; n=0
    for f in glob.glob("*.html")+glob.glob("*/*.html")+glob.glob("*/*/*.html"):
        if f.startswith(("pagefind","sponsor")): continue
        s0=s=open(f).read()
        s=re.sub(r'(<a class="navbt" href="[^"]*bot-templates/">)Bot templates</a>',r'\1AI bot templates</a>',s)
        s=re.sub(r'(<a class="navbt" href="[^"]*bot-templates/"><span class="npill npbt"><svg class="npico".*?</svg>)Bot templates</span></a>',r'\1AI bot templates</span></a>',s)  # neon pill form (Oct 23 2026): a fresh build pills the link before this rename runs
        s=s.replace('"name": "Bot templates"','"name": "AI bot templates"').replace('"name":"Bot templates"','"name":"AI bot templates"')
        s=s.replace('</svg>Bot templates</h2><a href="bot-templates/">','</svg>AI bot templates</h2><a href="bot-templates/">')
        if f=="bot-templates/index.html": s=s.replace('Bot templates<span id="bt-count"','AI bot templates<span id="bt-count"',1)
        if s!=s0: open(f,"w").write(s); n+=1
    print("bt rename:",n)

# Titles over 65 chars anywhere (bot template details, leaderboard badges): drop the brand suffix (Oct 21 2026)
def long_titles():
    import glob; n=0
    for f in glob.glob("bot-templates/*.html")+glob.glob("leaderboard/*.html")+glob.glob("s/*.html"):
        s0=s=open(f).read(); m=re.search(r"<title>(.*?)</title>",s,re.S)
        if not m or len(html.unescape(m.group(1)))<=65: continue
        t=re.sub(r" · AgentScout$","",m.group(1).strip())
        s=s.replace(m.group(0),f"<title>{t}</title>",1)
        if s!=s0: open(f,"w").write(s); n+=1
    print("long titles trimmed:",n)

# <meta charset> must sit in the first 1024 bytes (Lighthouse best-practices "charset"); move it right after <head> on every page (Oct 21 2026)
def charset_first():
    import glob; n=0
    for f in glob.glob("**/*.html",recursive=True):
        if f.startswith(("pagefind","sponsor")): continue
        s0=s=open(f).read()
        if '<meta charset="utf-8">' not in s or s.find('<meta charset="utf-8">')<600: continue
        s=s.replace('<meta charset="utf-8">',"",1)
        s=re.sub(r"<head>\s*",lambda m:'<head>\n<meta charset="utf-8">',s,1)
        if s!=s0: open(f,"w").write(s); n+=1
    print("charset moved:",n)

# Answer-first blocks + FAQPage JSON-LD (visibility report Oct 21 2026): homepage and /bot-templates/. Facts only from tools.json and the page itself.
def _ld(o): return '<script type="application/ld+json">'+json.dumps(o,ensure_ascii=False).replace("</","<\\/")+"</script>"
def _faq_html(faq): return "".join(f'<details style="margin:0 0 10px"><summary style="cursor:pointer;font-weight:600">{html.escape(q)}</summary><p style="margin:8px 0 0">{a}</p></details>' for q,a in faq)
def _faq_ld(faq): return _ld({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":re.sub(r"<[^>]+>","",a)}} for q,a in faq]})
def answer_blocks(t):
    import datetime
    from zoneinfo import ZoneInfo
    today=datetime.datetime.now(ZoneInfo("America/Los_Angeles")); d=today.strftime("%B %-d, %Y")
    n=len(t); nc=len({x["category"] for x in t}); nmcp=sum(1 for x in t if x["category"]=="MCP servers")
    f="index.html"
    if os.path.exists(f):
        s=open(f).read(); s=re.sub(r"<!--sn:home-->.*?<!--/sn:home-->","",s,flags=re.S)
        faq=[("What is the best AI agent directory?",f"AgentScout is a free AI agent directory that tracks {n:,} AI agent tools and MCP servers across {nc} categories. Every listing links to the official site, says what the tool does, and shows pricing as the maker states it. There are no paid placements in the rankings."),
             ("How does AgentScout vet tools?","Each listing is reviewed before it goes live: the link must work, the tool must be a real AI agent tool, and the description must match what the official site or README says. Links are re-checked daily, and GitHub stars come from the repository."),
             ("How often is the directory updated?",f"New tools are added every day and links are re-checked daily. Last checked {d}."),
             ("Are there free tools on AgentScout?",'Yes. Besides free and open-source listings, AgentScout has free browser tools such as the <a href="free-tools/mcp-config-builder.html">free MCP config generator for Claude Desktop, Cursor and VS Code</a> and the <a href="free-tools/agent-run-cost-estimator.html">AI agent cost calculator</a>. No sign-up needed.')]
        blk=('<!--sn:home--><section class="band" id="about-directory"><div class="wrap" style="max-width:860px">'
             f'<h2 style="font-size:20px;margin:0 0 10px">The AI agent directory, at a glance</h2>'
             f'<p style="margin:0 0 10px">AgentScout tracks <b>{n:,}</b> AI agent tools across <b>{nc}</b> categories, including <a href="categories/mcp-servers.html">{nmcp} MCP servers</a>, coding agents, browser agents, voice agents and no-code builders. We check every link daily, describe each tool from its official site or README, show pricing as the maker states it, and have no paid placements in the rankings. <span class="muted">Last checked {d}.</span></p>'
             '<p style="margin:0 0 16px">Free tools: <a href="free-tools/mcp-config-builder.html">MCP config generator for Claude Desktop, Cursor &amp; VS Code</a> · <a href="free-tools/agent-run-cost-estimator.html">AI agent cost calculator</a> · <a href="s/best-mcp-servers.html">Best MCP servers</a></p>'
             f'<h3 style="font-size:16px;margin:0 0 8px">FAQ</h3>{_faq_html(faq)}</div></section>{_faq_ld(faq)}<!--/sn:home-->')
        s=s.replace("</header>","</header>"+blk,1); open(f,"w").write(s)  # Oct 22 2026: about block goes after the top search panel
    f="bot-templates/index.html"
    if os.path.exists(f):
        s=open(f).read(); s=re.sub(r"<!--sn:bt-->.*?<!--/sn:bt-->","",s,flags=re.S)
        m=re.search(r'aria-label="(\d+) templates"',s) or re.search(r"(\d+) ready-made",s); bn=m.group(1) if m else ""
        if 'id="bt-count"' not in s and bn:  # build_bot_templates only adds the count badge to 'Bot templates</h1>'; restore it after the rename
            s=re.sub(r'(<h1 class="bt-h1"[^>]*>.*?)(</h1>)',lambda mm:mm.group(1)+f'<span id="bt-count" class="bt-count" aria-label="{bn} templates">{bn}</span>'+mm.group(2),s,1,flags=re.S)
        import json as J; ncb=len(J.load(open("data/bot-templates-community.json"))) if os.path.exists("data/bot-templates-community.json") else 0
        s=re.sub(r'(</svg>)(?:AI bot templates|Bot templates|Grok Bot templates, plugins &amp; skills)(<span id="bt-count")',r'\1Grok Bot templates, plugins &amp; skills\2',s,1)
        faq=[("What are Grok Bot templates?",f"Ready-made bots you can import into Grok Bot and use right away. This page lists {bn} templates, skills, plugins and workflows, including {ncb} community-made Grok Bot templates, plus templates for Claude, Codex, OpenClaw, Cursor and n8n."),
             ("Are these templates free?","Yes. Every template here is free to import or install. Some connect to apps or APIs that have their own plans."),
             ("How are templates checked?",f"Each template's link, name, description, category and maker credit is checked before it is listed, and the list is re-checked regularly. Last checked {d}."),
             ("Can I submit my own template?",'Yes. Use the <a href="../submit.html">submit form</a> and include the share link and what the template does.')]
        blk=(f'<!--sn:bt--><section class="wrap" style="max-width:860px;margin:28px auto"><p class="muted" style="margin:0 0 14px">Last checked {d}.</p><h2 style="font-size:18px;margin:0 0 10px">Grok Bot templates FAQ</h2>{_faq_html(faq)}</section>{_faq_ld(faq)}<!--/sn:bt-->')
        s=s.replace("</main>",blk+"</main>",1); open(f,"w").write(s)
    print("answer blocks: home + bot templates")

# MCP guide links (Ops follow-up Oct 21 2026): page -> [(href, label)], one marker block before </main>
MCP_LINKS={
 "categories/browser-computer-use.html":[("../mcp/browser-automation-mcp-servers.html","Best MCP servers for browser automation")],
 "s/best-mcp-servers.html":[("../mcp/browser-automation-mcp-servers.html","Best MCP servers for browser automation"),("../mcp/crypto-wallet-mcp-servers.html","Best MCP servers for crypto wallets"),("../mcp/crypto-mcp-servers.html","Best MCP servers for crypto and on-chain data"),("../mcp/index.html","All MCP servers by task")],
}
def mcp_links():
    n=0
    for f,L in MCP_LINKS.items():
        if not os.path.exists(f): continue
        s0=s=open(f).read(); s=re.sub(r"<!--sn:ml-->.*?<!--/sn:ml-->","",s,flags=re.S)
        blk='<!--sn:ml--><h2 style="font-size:16px;margin:28px 0 10px">MCP server guides</h2><div class="badges">'+"".join(f'<a class="b uc" href="{h}">{html.escape(l)}</a>' for h,l in L)+'</div><!--/sn:ml-->'
        s=s.replace("</main>",blk+"</main>",1)
        if s!=s0: open(f,"w").write(s); n+=1
    print("mcp guide links:",n)
