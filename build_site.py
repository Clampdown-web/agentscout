"""Generates use-case tags, slugs and static detail pages from tools.json."""
import json,re,html,os,build_extras
t=json.load(open("tools.json"))
RULES=[("write code",r"cod|IDE|PR|ticket|repo|program"),("automate the browser",r"browser|web browser|headless"),("control a computer",r"computer-use|desktop|operating system|cloud computer"),
("build multi-agent systems",r"multi-agent|crew|swarm|subagent"),("build an agent",r"framework|SDK|library|toolkit|harness|Development Kit"),("research the web",r"research|search|web data|website|cited|papers"),
("voice & phone calls",r"voice|phone|call|speech|TTS|talk"),("automate workflows",r"workflow|automation|automate|Zapier|apps"),("build apps without code",r"prompt-to-app|full apps|web apps|No-code|no-code|Drag-and-drop|visually"),
("connect tools via MCP",r"MCP"),("run code safely",r"sandbox|Sandbox|secure|policies"),("monitor & evaluate agents",r"observab|trac|evals|monitor|Evals|evaluat"),
("give agents memory",r"memory|Memory"),("sales & support",r"sales|prospect|customer|account"),("make diagrams",r"diagram"),("computer vision",r"vision")]
for x in t:
    d=x["name"]+" "+x["description"]+" "+x["category"]
    x["use_cases"]=[u for u,p in RULES if re.search(p,d)][:3] or [x["category"]]
    x["slug"]=re.sub(r"[^a-z0-9]+","-",x["name"].lower()).strip("-")
json.dump(t,open("tools.json","w"),indent=2,ensure_ascii=False)
os.makedirs("tools",exist_ok=True)
e=lambda s:html.escape(str(s or ""))
tpl=open("detail.tpl.html").read()
for x in t:
    rel=[y for y in t if y is not x and y["category"]==x["category"]][:6]
    relh="".join(f'<a class="card" href="{y["slug"]}.html"><div class="ct"><h3>{e(y["name"])}</h3></div><p>{e(y["description"])}</p></a>' for y in rel)
    facts=[("Category",x["category"]),("Audience","For builders" if x["audience"]=="builders" else "Ready to use"),("Pricing",x.get("pricing_detail",x["pricing"])),("Maturity",x["maturity"])]
    if x.get("github_stars") is not None: facts.append(("GitHub stars",f'{x["github_stars"]:,} (as of {x["verified"]})'))
    facts.append(("Link checked",x["verified"]))
    fh="".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a,b in facts)
    uc="".join(f'<a class="b uc" href="../index.html?uc={e(u)}#directory">{e(u)}</a>' for u in x["use_cases"])
    host=re.sub(r"^https?://(www\.)?","",x["url"]).split("/")[0]
    aud="builders" if x["audience"]=="builders" else "people who want a ready-to-use product"
    about=f'<h2 style="font-size:16px;margin-bottom:10px">About {e(x["name"])}</h2><p style="margin:0 0 28px">{e(x["name"])} is listed in our {e(x["category"])} category and is aimed at {aud}. {e(x["description"])} Pricing, as the maker states it: {e(x.get("pricing_detail",x["pricing"]))}. Maturity: {e(x["maturity"])}. We last checked the official link on {e(x["verified"])}.</p>'
    out=tpl.replace("{{META}}",e(build_extras.meta(x))).replace("{{ABOUT}}",about).replace("{{CATSLUG}}",build_extras.catslug(x["category"]))
    for k,v in {"NAME":e(x["name"]),"DESC":e(x["description"]),"URL":e(x["url"]),"HOST":e(host),"FACTS":fh,"UC":uc,"REL":relh,"SLUG":x["slug"],"CAT":e(x["category"]),"PRICE":e(x["pricing"]),"BADGE":build_extras.badge_html(x),"CMP":build_extras.cmp_links(x,t),"NEW":'<span class="b new">New this week</span>' if x["new"] else ""}.items():
        out=out.replace("{{"+k+"}}",v)
    open(f"tools/{x['slug']}.html","w").write(out)
print(len(t),"pages")
build_extras.build(t)
