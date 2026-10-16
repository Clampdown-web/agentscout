"""Generates use-case tags, slugs and static detail pages from tools.json."""
import json,re,html,os,build_extras
t=json.load(open("tools.json"))
RULES=[("write code",r"cod|IDE|PR|ticket|repo|program"),("automate the browser",r"browser|web browser|headless"),("control a computer",r"computer-use|desktop|operating system|cloud computer"),
("build multi-agent systems",r"multi-agent|crew|swarm|subagent"),("build an agent",r"framework|SDK|library|toolkit|harness|Development Kit"),("research the web",r"research|search|web data|website|cited|papers"),
("voice & phone calls",r"voice|phone|call|speech|TTS|talk"),("automate workflows",r"workflow|automation|automate|Zapier|apps"),("build apps without code",r"prompt-to-app|full apps|web apps|No-code|no-code|Drag-and-drop|visually"),
("connect tools via MCP",r"MCP"),("run code safely",r"sandbox|Sandbox|secure|policies"),("monitor & evaluate agents",r"observab|trac|evals|monitor|Evals|evaluat"),
("give agents memory",r"memory|Memory"),("sales & support",r"sales|prospect|customer|account"),("make diagrams",r"diagram"),("computer vision",r"vision")]
import datetime as _dt
from zoneinfo import ZoneInfo as _Z
_c=(_dt.datetime.now(_Z("America/Los_Angeles")).date()-_dt.timedelta(days=13)).isoformat()
for x in t:
    x["new"]=x.get("added","")>=_c
    d=x["name"]+" "+x["description"]+" "+x["category"]
    x["use_cases"]=[u for u,p in RULES if re.search(p,d)][:3] or [x["category"]]
    x["slug"]=re.sub(r"[^a-z0-9]+","-",x["name"].lower()).strip("-")
    if os.path.exists(f"assets/logos/{x['slug']}.png"): x["logo"]=f"assets/logos/{x['slug']}.png"
    else: x.pop("logo",None)
json.dump(t,open("tools.json","w"),indent=2,ensure_ascii=False)
os.makedirs("tools",exist_ok=True)
e=lambda s:html.escape(str(s or ""))
tpl=open("detail.tpl.html").read()
for x in t:
    rel=[y for y in t if y is not x and y["category"]==x["category"]][:6]
    relh="".join(f'<a class="card" href="{y["slug"]}.html"><div class="ct">{build_extras.ico(y,"../","sm")}<h3 style="flex:1">{e(y["name"])}</h3></div><p>{e(y["description"])}</p></a>' for y in rel)
    facts=[("Category",x["category"]),("Audience","For builders" if x["audience"]=="builders" else "Ready to use"),("Pricing",x.get("pricing_detail",x["pricing"])),("Maturity",x["maturity"])]
    if x.get("github_stars") is not None: facts.append(("GitHub stars",f'{x["github_stars"]:,} (as of {x["verified"]})'))
    if x.get("added"): facts.append(("Added",x["added"]))
    facts.append(("Link checked",x["verified"]))
    fh="".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a,b in facts)
    uc="".join(f'<a class="b uc" href="../index.html?uc={e(u)}#directory">{e(u)}</a>' for u in x["use_cases"])
    prim=build_extras.su(x.get("website") or x["url"])
    host=re.sub(r"^https?://(www\.)?","",prim).split("/")[0]
    gh=build_extras.su(x.get("github","")) if x.get("github") else ""
    ghb=f' <a class="btn" href="{e(gh)}" target="_blank" rel="noopener noreferrer">GitHub ↗</a>' if gh and gh!=prim else ""
    aud="builders" if x["audience"]=="builders" else "people who want a ready-to-use product"
    about=f'<h2 style="font-size:16px;margin-bottom:10px">About {e(x["name"])}</h2><p style="margin:0 0 28px">{e(x["name"])} is listed in our {e(x["category"])} category and is aimed at {aud}. {e(x["description"])} Pricing, as the maker states it: {e(x.get("pricing_detail",x["pricing"]))}. Maturity: {e(x["maturity"])}. We last checked the official link on {e(x["verified"])}.</p>'
    out=tpl.replace("{{META}}",e(build_extras.meta(x))).replace("{{ABOUT}}",about).replace("{{CATSLUG}}",build_extras.catslug(x["category"]))
    for k,v in {"ICO":build_extras.ico(x,"../","lg"),"NAME":e(x["name"]),"DESC":e(x["description"]),"URL":e(prim),"HOST":e(host),"GHBTN":ghb,"FACTS":fh,"UC":uc,"REL":relh,"SLUG":x["slug"],"CAT":e(x["category"]),"PRICE":e(x["pricing"]),"BADGE":build_extras.badge_html(x),"CMP":build_extras.cmp_links(x,t),"NEW":(('<span class="b new">New</span>' if x["new"] else "")+(f'<span class="b added">Added {_dt.date.fromisoformat(x["added"]).strftime("%b %-d, %Y")}</span>' if x.get("added") else ""))}.items():
        out=out.replace("{{"+k+"}}",v)
    B="https://clampdown-web.github.io/agentscout/";pg=f"{B}tools/{x['slug']}.html"
    ld={"@context":"https://schema.org","@graph":[{"@type":"WebPage","@id":pg,"url":pg,"name":f"{x['name']}: what it does, pricing and alternatives","dateModified":x["verified"],"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B},
        "about":{"@type":"SoftwareApplication","name":x["name"],"description":x["description"],"url":prim,**({"sameAs":[gh]} if gh and gh!=prim else {}),**({"codeRepository":gh} if gh else {}),"applicationCategory":"DeveloperApplication" if x["audience"]=="builders" else "BusinessApplication","keywords":", ".join([x["category"]]+x["use_cases"])}},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":x["category"],"item":f"{B}categories/{build_extras.catslug(x['category'])}.html"},{"@type":"ListItem","position":3,"name":x["name"],"item":pg}]}]}
    out=out.replace("</head>",'<script type="application/ld+json">'+json.dumps(ld,ensure_ascii=False).replace("</","<\\/")+"</script></head>",1)
    open(f"tools/{x['slug']}.html","w").write(out)
print(len(t),"pages")
build_extras.build(t)
import build_api
build_api.build(t)

# Keep homepage static counts in sync with tools.json
def _sync_index_counts():
    import re, json as _j, datetime as _dt
    n = len(_j.load(open("tools.json")))
    s = open("index.html").read()
    s = re.sub(r"\b\d+ AI Agent Tools", f"{n} AI Agent Tools", s)
    s = re.sub(r"Directory of \d+ link-checked", f"Directory of {n} link-checked", s)
    s = re.sub(r'(id="s-eyebrow">)\d+ tools · Links checked [^<]+', lambda m: m.group(1) + f"{n} tools · Links checked " + _dt.date.today().strftime("%b %-d, %Y"), s)
    s = re.sub(r'(id="s-total">)\d+', lambda m: m.group(1) + str(n), s)
    s = s.replace('fetch("tools.json").then', 'fetch("tools.json",{cache:"no-cache"}).then')
    open("index.html", "w").write(s)
_sync_index_counts()
import build_recent
build_recent.build(t)

import build_tasks
build_tasks.sitewide(t)
