"""Competitive-intel pass (owner-approved Oct 22 2026 PT):
- /skills/: Agent Skills section with install commands copied from each project's own README (checked Oct 22 2026).
- Homepage hero line + og/twitter description: "<N> MCP servers, link-checked daily", N from tools.json.
- Free listing vs other directories ($49 to $437, prices checked Oct 2026; no competitor named, owner request Oct 22 2026) on index.html and submit.html.
Idempotent (marker blocks). Every count is computed from tools.json."""
import json,re,html,os
e=lambda s:html.escape(str(s),quote=True)
B="https://agentscouthq.com/"
CHECKED="Oct 22, 2026"
# (slug, client label, [commands], README url). Commands are verbatim from the README; nothing invented.
SKILLS=[
 ("skills-sh","Any agent via the skills CLI (Claude Code, Codex, Cursor, OpenCode and more)",["npx skills add vercel-labs/agent-skills"],"https://github.com/vercel-labs/skills"),
 ("playwright-skill","skills CLI, installed globally",["npx skills add lackeyjb/playwright-skill --skill playwright-skill --global --yes"],"https://github.com/lackeyjb/playwright-skill"),
 ("agents-cli","skills CLI",["npx skills add google/agents-cli"],"https://github.com/google/agents-cli"),
 ("hyperframes","skills CLI",["npx skills add heygen-com/hyperframes"],"https://github.com/heygen-com/hyperframes"),
 ("binance-agent-os","skills CLI",["npx skills add https://github.com/binance/binance-skills-hub"],"https://github.com/binance/binance-skills-hub"),
 ("ultralytics-agents","Claude Code (terminal)",["claude plugin marketplace add ultralytics/skills","claude plugin install yolo@ultralytics"],"https://github.com/ultralytics/skills"),
 ("nvidia-tao-agent-skills","Claude Code (inside a session)",["/plugin marketplace add NVIDIA-TAO/tao-skill-bank@7.3.0","/plugin install tao-skills@tao-skill-bank"],"https://github.com/NVIDIA-TAO/tao-skill-bank"),
 ("onetake","Claude Code (copy into your skills folder)",["git clone https://github.com/feitangyuan/onetake.git ~/.claude/skills/onetake"],"https://github.com/feitangyuan/onetake"),
 ("antalpha-wallet-guard","ClawHub",["clawhub install antalpha-wallet-guard"],"https://github.com/AntalphaAI/wallet-guard"),
]
def mcp_n(t): return sum(1 for x in t if x["category"]=="MCP servers")
def _blk(s,tag,html_,anchor,after=True):
    s=re.sub(rf"<!--ci:{tag}-->.*?<!--/ci:{tag}-->","",s,flags=re.S)
    b=f"<!--ci:{tag}-->{html_}<!--/ci:{tag}-->"
    if anchor not in s: raise SystemExit(f"build_ci: anchor for {tag} missing")
    return s.replace(anchor,anchor+b if after else b+anchor,1)
def cmp_table():
    return ('<div style="overflow-x:auto;margin:12px 0 16px"><table style="border-collapse:collapse;font-size:14px;min-width:0;width:100%;max-width:640px">'
     '<caption style="text-align:left;font-weight:700;margin-bottom:6px">Free listing vs $49–$437 elsewhere</caption>'
     '<thead><tr><th style="text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)">Directory</th><th style="text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)">Cost to get listed</th></tr></thead><tbody>'
     '<tr><td style="padding:6px 8px;border-bottom:1px solid var(--line)"><b>AgentScout</b></td><td style="padding:6px 8px;border-bottom:1px solid var(--line)"><b>Free ($0 forever).</b> Every submission is reviewed; optional <b>$49 Featured (30 full days featured vs. 5-day boosts elsewhere)</b> &amp; $99/wk Sponsor boosts available. Featured slots are clearly labeled and sit above the list; rankings are never paid.</td></tr>'
     '<tr><td style="padding:6px 8px;border-bottom:1px solid var(--line)">Other directories</td><td style="padding:6px 8px;border-bottom:1px solid var(--line)">$49 to $437 to get listed</td></tr>'
     f'</tbody></table><p class="muted" style="font-size:12.5px;margin:6px 0 0">Prices checked Oct 2026, may change.</p></div>')
def home(t):
    import build_aicite as _bac; _ul=_bac.mcp_uptime_line(t)
    n=mcp_n(t); s=open("index.html").read()
    line=f'<p class="lede" style="margin-top:6px"><a href="categories/mcp-servers.html"><b>{n:,} MCP servers</b>, link-checked daily</a> (<a href="mcp/link-status.html">{e(_ul)}</a>) · <a href="skills/">Agent Skills with install commands</a></p>'
    s=_blk(s,"mcp",line,'</p><p class="quizcta">',after=False) if '<!--ci:mcp-->' not in s else re.sub(r"<!--ci:mcp-->.*?<!--/ci:mcp-->",f"<!--ci:mcp-->{line}<!--/ci:mcp-->",s,flags=re.S)
    tot=len(t)
    d=f"AgentScout: {tot:,} AI agent tools, including {n:,} MCP servers, link-checked daily. Coding agents, frameworks, browser use, voice and no-code."
    for a,k in (("name","description"),("property","og:description"),("name","twitter:description")):
        s=re.sub(rf'(<meta {a}="{k}" content=")[^"]*',lambda m:m.group(1)+e(d),s,count=1)
    s=re.sub(r'(<a href="categories/mcp-servers.html">)\d[\d,]* MCP servers(</a>)',lambda m:m.group(1)+f"{n:,} MCP servers"+m.group(2),s)
    blk=f'<h3 style="font-size:16px;margin:0 0 8px">Get listed free</h3>{cmp_table()}<p style="margin:0 0 16px"><a href="submit.html">Submit your tool free →</a></p>'
    s=_blk(s,"free",blk,'<h3 style="font-size:16px;margin:0 0 8px">FAQ</h3>',after=False)
    open("index.html","w").write(s)
    u=open("submit.html").read()
    u=_blk(u,"free",cmp_table(),"<!--/xl:submit-->") if "<!--/xl:submit-->" in u else _blk(u,"free",cmp_table(),'<form id="sf"',after=False)
    open("submit.html","w").write(u)
    print(f"build_ci: homepage MCP line {n}, free-listing comparison on index + submit")
def pages(t):
    import build_extras as X
    bs={x["slug"]:x for x in t}; rows=[]
    for slug,client,cmds,src in SKILLS:
        x=bs.get(slug)
        if not x: print("build_ci: skill tool missing, skipped:",slug); continue
        code="".join(f'<pre style="overflow-x:auto;white-space:pre;margin:6px 0;padding:8px 10px;border:1px solid var(--line);border-radius:8px;font-size:13px"><code>{e(c)}</code></pre>' for c in cmds)
        rows.append(f'<section style="margin:0 0 22px"><h2 style="font-size:17px;margin:0 0 4px"><a href="../tools/{e(slug)}.html">{e(x["name"])}</a></h2><p style="margin:0 0 6px">{e(x["description"])}</p>'
                    f'<p class="muted" style="margin:0;font-size:13px">Install with: {e(client)}</p>{code}<p class="muted" style="margin:0;font-size:12.5px">Command from the <a href="{e(src)}" rel="noopener noreferrer" target="_blank">official README</a>.</p></section>')
    k=len(rows)
    title=f"Agent Skills with Install Commands ({k} picks) · AgentScout"
    desc=f"{k} agent skills for Claude Code, Codex, Cursor and other coding agents, each with the install command from its official README. Checked {CHECKED}."
    body=(f'<p class="crumb"><a href="../index.html">AgentScout</a> › Agent Skills</p><h1>Agent Skills with install commands</h1>'
          f'<p class="lede" style="margin-left:0;text-align:left">Agent skills are folders of instructions and scripts (a SKILL.md plus files) that coding agents load when a task needs them. '
          f'Here are {k} skills from the AgentScout directory, each with the install command copied from its official README on {CHECKED}. Anthropic\'s own example skills install in Claude Code with '
          f'<code>/plugin marketplace add anthropics/skills</code> (<a href="https://github.com/anthropics/skills" rel="noopener noreferrer" target="_blank">README</a>).</p>'
          +"".join(rows)+'<p class="disclose">Read a skill before you install it: skills can run scripts on your machine. Know a skill we should add? <a href="../submit.html">Submit it free</a>.</p>')
    canon=B+"skills/"
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon},
        {"@type":"ItemList","itemListElement":[{"@type":"ListItem","position":i+1,"url":f"{B}tools/{s}.html","name":bs[s]["name"]} for i,(s,*_) in enumerate([r for r in SKILLS if r[0] in bs])]}]}
    os.makedirs("skills",exist_ok=True)
    h=X.shell("../",title,desc,canon,body,ld).replace('<meta property="og:url"',f'<meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta property="og:url"',1)
    if 'name="twitter:image"' not in h:  # mirror og:image so X cards show the share image (post-update pass Oct 22 2026)
        m=re.search(r'<meta property="og:image" content="([^"]+)">',h)
        if m: h=h.replace('<meta name="twitter:title"',f'<meta name="twitter:image" content="{m.group(1)}"><meta name="twitter:title"',1)
    open("skills/index.html","w").write(h); print("build_ci: skills page",k,"skills")
    return [canon]
