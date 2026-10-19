"""Generates use-case tags, slugs and static detail pages from tools.json."""
import json,re,html,os,build_extras,build_rich,build_related
t=json.load(open("tools.json"))
import build_logocheck; build_logocheck.run(t)  # stop the build if any tool lacks a valid local logo (Oct 18 2026)
# Sponsor bar on every page (build_sponsor.py). OFF until a sponsor is booked: set True and fill data/sponsor_bar.json, then rebuild.
SPONSOR_ENABLED = False
RULES=[("write code",r"cod|IDE|PR|ticket|repo|program"),("automate the browser",r"browser|web browser|headless"),("control a computer",r"computer-use|desktop|operating system|cloud computer"),
("build multi-agent systems",r"multi-agent|crew|swarm|subagent"),("build an agent",r"framework|SDK|library|toolkit|harness|Development Kit"),("research the web",r"research|search|web data|website|cited|papers"),
("voice & phone calls",r"voice|phone|call|speech|TTS|talk"),("automate workflows",r"workflow|automation|automate|Zapier|apps"),("build apps without code",r"prompt-to-app|full apps|web apps|No-code|no-code|Drag-and-drop|visually"),
("connect tools via MCP",r"MCP"),("run code safely",r"sandbox|Sandbox|secure|policies"),("monitor & evaluate agents",r"observab|trac|evals|monitor|Evals|evaluat"),
("give agents memory",r"memory|Memory"),("sales & support",r"sales|prospect|customer|account"),("make diagrams",r"diagram"),("computer vision",r"vision")]
# Film, TV, video and music categories (added Oct 18, 2026) get their own use-case tags; agent rules above don't fit media tools
MEDIA_CATS={"film & TV production","video generation","film & TV audio","music production"}
MEDIA_RULES=[("plan & storyboard",r"storyboard|screenplay|script coverage|pre-production|previs|shot list|call sheet"),("edit video",r"\bedit|rough cut|stringout|\bcuts?\b|timeline|footage"),
("generate video",r"video generat|text to video|image to video|video model|generate video|AI video generator"),("visual effects",r"\bVFX|composit|roto|motion capture|mocap|relight|camera track|upscal|enhanc|grading|color"),
("subtitles & transcripts",r"subtitle|caption|transcri"),("dub & localize",r"\bdub|lip.?sync|locali[sz]|translat"),("clean up audio",r"noise|dialogue|de-?reverb|repair|clean"),
("sound effects & Foley",r"sound effect|\bSFX|Foley|sound design"),("voiceover",r"voice ?over|narration|voice clon|voice convers|voices"),
("make music",r"song|music generat|compos|melod|beats?\b|singing|score|soundtrack"),("mix & master",r"\bmix|master"),("separate stems",r"\bstems?\b|vocal remov|separat|splitter|unmix")]
# Art, design, 3D & photo categories (added Oct 18, 2026): hand-set use_cases in tools.json are kept; ART_RULES only fill empty ones.
ART_CATS={"image generation","graphic design & branding","3D & concept art","photography & photo editing"}
ART_UC={"generate images","open image models","concept art","logos & branding","vectorize","UI design","design graphics","social posts & ads","generate 3D","animate characters","3D scanning","3D texturing","architecture visuals","real estate photos","cull photos","edit photos","edit in your style","retouch portraits","upscale images","restore photos","remove backgrounds","product photos","headshots","organize photos","protect artwork"}
ART_RULES=[("generate images",r"image generat|text-to-image|generat\w* images"),("concept art",r"illustrat|concept art"),("logos & branding",r"\blogos?\b|brand kit"),("vectorize",r"\bSVG\b|vectoriz"),
("UI design",r"\bUI\b|wireframe|mockup|prototyp"),("social posts & ads",r"social posts?|\bads?\b|ad creatives?"),("design graphics",r"graphic design|posters?|infographic"),("generate 3D",r"\b3D (?:models?|assets?|worlds?)|to 3D\b"),
("animate characters",r"rigg|character animation|mocap"),("cull photos",r"\bcull"),("retouch portraits",r"retouch|portrait"),("upscale images",r"upscal"),("remove backgrounds",r"background remov"),
("product photos",r"product photo|on-model"),("headshots",r"headshot"),("real estate photos",r"real[- ]estate|virtual stag"),("organize photos",r"photo librar|face recognition"),("edit photos",r"photo edit|raw editor")]
# Existing tools in other categories that also belong on the art task pages (explicit tags, Oct 18, 2026)
ART_XLINK_UC={"canva-mcp":["design graphics","social posts & ads"],"figma-mcp-server":["UI design"],"talk-to-figma-mcp":["UI design"],"framelink-figma-mcp":["UI design"],
"figma-console-mcp":["UI design"],"picsart-genai-mcp":["generate images","edit photos"],"icons8-mcp":["design graphics"],"brandfetch-mcp":["logos & branding"],
"logo-dev-mcp":["logos & branding"],"mcp-for-blender":["generate 3D"],"imagesorcery-mcp":["remove backgrounds"],"comfyui":["generate images","open image models"],
"adobe-firefly":["generate images"],"higgsfield":["generate images"],"dreamina":["generate images"],"luma-dream-machine":["generate images"],
"scenario":["concept art","generate 3D"],"intangible":["concept art"],"simulon":["concept art"]}
# Reviewed use cases that replace the keyword guess (Oct 19, 2026 PT). agent-resource-market: agent-to-agent discovery and coordination;
# its site says it does not claim MCP or A2A support, so the MCP & infra category default ("connect tools via MCP") would be wrong.
UC_SET={"agent-resource-market":["build multi-agent systems"],
"robottraining-jobs":["connect tools via MCP","research the web"],  # Oct 19 PT audit: "hiring data" tripped the customer/sales rule; it is a job board + MCP server, not customer support
"ceofans":["business agents","automate workflows"],
"9bot":["connect tools via MCP","automate workflows"],
"pragor":["security & governance","build multi-agent systems"],  # Pragor (Oct 19 PT, maker request): coordination and governance layer for people and agents, not an autonomous agent; the keyword guess would add "write code"
"mailveri-mcp":["connect tools via MCP"]}  # MailVeri MCP: email/list verification; kept off customer support (not a support desk); the keyword guess would add "write code"  # CEOFans: the keyword guess would tag it "write code" (it mentions Codex) and "control a computer" ("desktop")
import datetime as _dt
from zoneinfo import ZoneInfo as _Z
_c=(_dt.datetime.now(_Z("America/Los_Angeles")).date()-_dt.timedelta(days=13)).isoformat()
for x in t:
    x["new"]=(not x.get("seed")) and x.get("added","")>=_c and "discontinued" not in x.get("maturity","").lower()  # seed = starting catalog (launch Oct 14 + bulk import Oct 16), never "new"
    d=x["name"]+" "+x["description"]+" "+x["category"]
    if x["category"] in ART_CATS:
        _k=[u for u in (x.get("use_cases") or []) if u in ART_UC]
        x["use_cases"]=_k or [u for u,p in ART_RULES if re.search(p,x["name"]+" "+x["description"],re.I)][:3] or [x["category"]]
    else: x["use_cases"]=([u for u,p in MEDIA_RULES if re.search(p,x["name"]+" "+x["description"],re.I)][:3] or [x["category"]]) if x["category"] in MEDIA_CATS else ([u for u,p in RULES if re.search(p,d)][:3] or [x["category"]])
    x["slug"]=re.sub(r"[^a-z0-9]+","-",x["name"].lower()).strip("-")
    if x["slug"] in ART_XLINK_UC: x["use_cases"]=list(dict.fromkeys(x["use_cases"]+ART_XLINK_UC[x["slug"]]))
    if x["slug"] in UC_SET: x["use_cases"]=list(UC_SET[x["slug"]])
    if os.path.exists(f"assets/logos/{x['slug']}.png"): x["logo"]=f"assets/logos/{x['slug']}.png"
    else: x.pop("logo",None)
json.dump(t,open("tools.json","w"),indent=2,ensure_ascii=False)
os.makedirs("tools",exist_ok=True)
e=lambda s:html.escape(str(s or ""))
tpl=open("data/detail.tpl").read()
GH=json.load(open("data/github.json")) if os.path.exists("data/github.json") else {}
REL=build_related.pick(t)  # similarity + load-balanced, so no tool in a category is left unlinked
build_rich.REL=REL
for x in t:
    rel=REL[x["slug"]]
    relh="".join(f'<a class="card" href="{y["slug"]}.html"><div class="ct">{build_extras.ico(y,"../","sm")}<h3 style="flex:1">{e(y["name"])}</h3></div><p>{e(y["description"])}</p></a>' for y in rel)
    facts=[("Category",x["category"]+(" · "+", ".join(x["tags"]) if x.get("tags") else "")),("Audience","For builders" if x["audience"]=="builders" else "Ready to use"),("Pricing",(x.get("pricing_detail") or x["pricing"])),("Maturity",x["maturity"])]
    if x.get("github_stars") is not None: facts.append(("GitHub stars",f'{x["github_stars"]:,} (as of {x.get("stars_checked") or x["verified"]})'))
    if x.get("added"): facts.append(("Added",x["added"]))
    facts.append(("Link checked",x["verified"]))
    fh="".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a,b in facts)
    g=GH.get(x["slug"]) or {}
    if g.get("release_tag") and x.get("github"):
        _tg=g["release_tag"] if len(g["release_tag"])<=22 else g["release_tag"][:21]+"…"
        fh+=f'<dt>Latest release</dt><dd><a href="{e(g.get("release_url") or x["github"].rstrip("/")+"/releases")}" target="_blank" rel="noopener noreferrer" title="{e(g["release_tag"])} · GitHub data fetched {e(g.get("fetched",""))}">{e(_tg)}</a>, {e(_dt.date.fromisoformat(g["release_date"]).strftime("%b %-d, %Y"))}</dd>'
    fh+=f'<dt>Listing</dt><dd><a class="suggestedit" href="../submit.html?type=update&amp;tool={x["slug"]}" rel="nofollow">Suggest an edit</a></dd>'
    if g.get("pushed") and x.get("github"): fh+=f'<dt>Last commit</dt><dd title="GitHub data fetched {e(g.get("fetched",""))}">{e(_dt.date.fromisoformat(g["pushed"]).strftime("%b %-d, %Y"))}</dd>'
    uc="".join(f'<a class="b uc" href="../index.html?uc={e(u)}#directory">{e(u)}</a>' for u in x["use_cases"])
    uc+="".join(f'<a class="b uc" href="../categories/{build_extras.catslug(c)}.html">Also see: {e(c)}</a>' for c in build_extras.media_xlink_cats(x["slug"]))
    prim=build_extras.su(x.get("website") or x["url"])
    host=re.sub(r"^https?://(www\.)?","",prim).split("/")[0]
    gh=build_extras.su(x.get("github","")) if x.get("github") else ""
    ghb=f' <a class="btn" href="{e(gh)}" target="_blank" rel="noopener noreferrer">GitHub ↗</a>' if gh and gh!=prim else ""
    aud="builders" if x["audience"]=="builders" else "people who want a ready-to-use product"
    about=f'<h2 style="font-size:16px;margin-bottom:10px">About {e(x["name"])}</h2><p style="margin:0 0 28px">{e(x["name"])} is listed in our {e(x["category"])} category and is aimed at {aud}. {e(x["description"])} Pricing, as the maker states it: {e((x.get("pricing_detail") or x["pricing"]))}. Maturity: {e(x["maturity"])}. We last checked the official link on {e(x["verified"])}.</p>'
    out=tpl.replace("{{META}}",e(build_extras.meta(x))).replace("{{ABOUT}}",about).replace("{{CATSLUG}}",build_extras.catslug(x["category"]))
    for k,v in {"ICO":build_extras.ico(x,"../","lg"),"NAME":e(x["name"]),"DESC":e(x["description"]),"URL":e(prim),"HOST":e(host),"GHBTN":ghb,"FACTS":fh,"UC":uc,"REL":relh,"SLUG":x["slug"],"CAT":e(x["category"]),"PRICE":e(x["pricing"]),"BADGE":build_extras.badge_html(x),"CMP":build_extras.cmp_links(x,t),"NEW":(('<span class="b new">New</span>' if x["new"] else "")+(f'<span class="b added">Added {_dt.date.fromisoformat(x["added"]).strftime("%b %-d, %Y")}</span>' if x.get("added") else ""))}.items():
        out=out.replace("{{"+k+"}}",v)
    # Visible status note for archived or stale listings (tools.json "status_note", owner-approved Oct 18 2026)
    if x.get("status_note"):
        _arch=x.get("maturity","").lower().startswith(("archived","discontinued"))
        out=out.replace('<div class="badges">','<div class="badges"><span class="b" style="border-color:#b45309;color:#f59e0b">'+(("Discontinued" if "discontinued" in x.get("maturity","").lower() else "Archived") if _arch else "No recent updates")+'</span>',1)
        out=out.replace('<p class="lede">'+e(x["description"])+'</p>','<p class="lede">'+e(x["description"])+'</p><p class="statusnote" role="note" style="margin:-6px 0 16px;padding:10px 14px;border:1px solid #b45309;border-radius:10px;font-size:14px">⚠️ '+e(x["status_note"])+'</p>',1)
    # Maker-submitted listings (tools.json "maker_submitted": true + "submitted": YYYY-MM-DD, Pacific): small badge by the name (standing perk, Oct 18 2026)
    if x.get("maker_submitted"):
        _sd=x.get("submitted") or x.get("added","")
        _sdt=_dt.date.fromisoformat(_sd).strftime("%b %-d, %Y") if _sd else ""
        out=re.sub(r'(<div class="badges">.*?)(</div>\s*<h1 class="icoh">)',lambda m:m.group(1)+f'<span class="b maker" title="The maker submitted this tool through our submit form{(" on "+_sdt) if _sdt else ""}. We reviewed and wrote the listing.">✓ Submitted by maker</span>'+m.group(2),out,count=1,flags=re.S)
    B="https://agentscouthq.com/";pg=f"{B}tools/{x['slug']}.html"
    out,_rich=build_rich.apply(out,x,t,build_extras.catslug,prim,B)
    if _rich: out=out.replace(about,(about+_rich[0]) if _rich[4:]==("lite",) else _rich[0],1)  # lite entries keep the About paragraph (additive)
    ld={"@context":"https://schema.org","@graph":[{"@type":"WebPage","@id":pg,"url":pg,"name":f"{x['name']}: what it does, pricing and alternatives","dateModified":x["verified"],"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B},
        "about":{"@type":"SoftwareApplication","name":x["name"],"description":x["description"],"url":prim,**({"sameAs":[gh]} if gh and gh!=prim else {}),**({"codeRepository":gh} if gh else {}),"applicationCategory":"DeveloperApplication" if x["audience"]=="builders" else "BusinessApplication","keywords":", ".join(dict.fromkeys([x["category"]]+x["use_cases"]))}},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":x["category"],"item":f"{B}categories/{build_extras.catslug(x['category'])}.html"},{"@type":"ListItem","position":3,"name":x["name"],"item":pg}]}]}
    if _rich:
        ld["@graph"][0]["name"]=_rich[3]; ld["@graph"][0]["about"]={**ld["@graph"][0]["about"],**_rich[1]}; ld["@graph"].append(_rich[2])
    out=out.replace("</head>",'<script type="application/ld+json">'+json.dumps(ld,ensure_ascii=False).replace("</","<\\/")+"</script></head>",1)
    open(f"tools/{x['slug']}.html","w").write(out)
print(len(t),"pages")
build_extras.build(t)
import build_api
build_api.build(t)
import build_reviews
build_reviews.run(t)  # ratings & reviews section + JSON-LD (real data only)

# Keep homepage static counts in sync with tools.json
def _sync_index_counts():
    import re, json as _j, datetime as _dt
    n = len(_j.load(open("tools.json")))
    s = open("index.html").read()
    try:
        _y,_m,_d = map(int, _j.load(open("api/tools.json")).get("last_checked","").split("-"))
        _lc = _dt.date(_y,_m,_d).strftime("%b %-d, %Y")
    except Exception:
        _lc = _dt.date.today().strftime("%b %-d, %Y")
    s = re.sub(r"\b\d[\d,]* AI Agent Tools", f"{n:,} AI Agent Tools", s)
    s = re.sub(r"Directory of \d[\d,]* link-checked", f"Directory of {n:,} link-checked", s)
    s = re.sub(r'(id="s-eyebrow">)\d[\d,]* tools · Links checked [^<]+', lambda m: m.group(1) + f"{n:,} tools · Links checked " + _lc, s)
    s = re.sub(r'(id="s-total">)\d[\d,]*', lambda m: m.group(1) + f"{n:,}", s)
    # homepage JS re-renders the counts from tools.json: keep thousands separators (Oct 18 2026)
    s = s.replace('$("s-total").textContent=d.length;$("s-eyebrow").textContent=$("s-eyebrow").textContent.replace(/^\\d+/,d.length)','$("s-total").textContent=d.length.toLocaleString("en-US");$("s-eyebrow").textContent=$("s-eyebrow").textContent.replace(/^[\\d,]+/,d.length.toLocaleString("en-US"))')
    s = s.replace('fetch("tools.json").then', 'fetch("tools.json",{cache:"no-cache"}).then')
    # main landmark for screen readers (a11y audit Oct 18 2026): hero through the newsletter box, footer stays outside
    if "<main" not in s and '<header class="hero">' in s and "<footer" in s:
        s = s.replace('<header class="hero">', '<main id="main"><header class="hero">', 1)
        i = s.rfind("<footer"); s = s[:i] + "</main>\n" + s[i:]
    open("index.html", "w").write(s)
_sync_index_counts()
import build_recent
build_recent.build(t)

import build_sponsor; build_sponsor.page(t)  # hidden sponsor page: noindex, not in sitemap, not linked (Oct 18 2026)
import build_tasks
build_tasks.sitewide(t)
import build_sections
build_sections.build(t)
import build_pick
build_pick.pick(t)
import build_links
build_links.run(t)
import build_seo; build_seo.run(t)
import build_fresh; build_fresh.run(t)  # Updated dates, dateModified, quick comparison tables (Oct 18 2026)
import build_listlogos; build_listlogos.run(t)  # logos next to tool names in tables and inline tool lists (Oct 18 2026)
import build_og; build_og.run(t)  # per-page share images (Oct 18 2026)
build_logocheck.listings_gate()  # stop the build if any tool link in a listing lacks its logo (Oct 18 2026)
import build_fonts; build_fonts.run()  # self-hosted Inter on every page (idempotent)
build_sponsor.apply_bar(SPONSOR_ENABLED)  # last step: adds the bar when on, removes it when off
# Relevance check (Oct 18, 2026): flag any tasks/, s/, for/ or best/ page with >10% off-topic tools; the build exits 1 so nothing gets committed
import subprocess as _sp, sys as _sys
if _sp.run([_sys.executable,"scripts/check_relevance.py","--strict","--write"]).returncode: print("BUILD FAILED: relevance check (see data/relevance_report.json)"); _sys.exit(1)
