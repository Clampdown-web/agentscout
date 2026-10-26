"""Generates use-case tags, slugs and static detail pages from tools.json."""
import subprocess as _sp,sys as _sys; _sp.run([_sys.executable,'scripts/update_latest_issue.py'])  # newsletter Latest issue (Oct 20 2026)
import json,re,html,os,build_extras,build_rich,build_related
t=json.load(open("tools.json"))
import build_logocheck; build_logocheck.run(t)  # stop the build if any tool lacks a valid local logo (Oct 18 2026)
# Sponsor bar on every page (build_sponsor.py). OFF until a sponsor is booked: set True and fill data/sponsor_bar.json, then rebuild.
SPONSOR_ENABLED = False
RULES=[("write code",r"cod|IDE|PR|ticket|repo|program"),("automate the browser",r"browser|web browser|headless"),("control a computer",r"computer-use|desktop|operating system|cloud computer"),
("build multi-agent systems",r"multi-agent|crew|swarm|subagent"),("build an agent",r"framework|SDK|library|toolkit|harness|Development Kit"),("research the web",r"research|search|web data|website|cited|papers"),
("voice & phone calls",r"voice|phone|(?<!tool )(?<!tool-)(?<!API )(?<!function )(?<!RPC )\bcall(s|ers?)?\b|speech|TTS|talk"),("automate workflows",r"workflow|automation|automate|Zapier|apps"),("build apps without code",r"prompt-to-app|full apps|web apps|No-code|no-code|Drag-and-drop|visually"),
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
APP_CAT={"krea":"MultimediaApplication"}  # Oct 23 PT: per-tool JSON-LD applicationCategory overrides
LD_KW={"krea":["video generation","text to video","image to video"]}  # Oct 23 PT: extra JSON-LD keywords (Krea video refresh)
UC_SET={"editara":["edit photos","remove backgrounds","restore photos","upscale images"],
"puremidi":["make music"],
"lakewood-agents":["personal agents","research the web","automate workflows"],
"machine-like":["business agents","sales & support","automate workflows"],
"kiwi":["business agents","sales & support","automate workflows"],
"lobstermatch":["build multi-agent systems","automate workflows"],
"tanatasa-beauty-mcp":["connect tools via MCP","automate workflows"],
"neverapply":["connect tools via MCP","automate workflows"],
"ai-music-mastering":["mix & master"],
"book-cover-generator":["design graphics","generate images"],
"raydo-agent-os":["control a computer","automate the browser","automate workflows"],
"zozo-hq":["write code","automate workflows"],  # Oct 24 PM PT: maker submissions
"reverse-image-location-geosolver":["connect tools via MCP","computer vision","research the web"],
"mach":["sales & support","research the web","automate workflows"],
"tta1":["voice & phone calls"],
"ccc":["write code","monitor & evaluate agents"],
"tokenrip":["build multi-agent systems","give agents memory","connect tools via MCP"],
"agiloop":["build apps without code","write code"],
"clipkai":["generate video","edit video"],
"pangolinfo-amazon-data-mcp":["connect tools via MCP","research the web"],
"imgs-ai":["generate images","edit photos"],
"menlo-insurance-mcp":["connect tools via MCP","automate workflows"],
"enhancewizard":["upscale images","restore photos","edit photos"],  # Oct 24 PT: maker submissions + discovery UC overrides
"pudding":["control a computer","automate the browser","write code"],
"orbi":["write code","automate workflows"],
"sora2-hub":["generate images","generate video"],
"massvai":["build apps without code","write code"],
"images-upscale":["upscale images","edit photos","remove backgrounds"],
"siphotoeditor":["edit photos","retouch portraits","remove backgrounds"],
"sigamegen":["games","build apps without code"],
"agenvas":["design graphics","generate images","edit photos"],
"my-green-robot":["personal agents","voice & phone calls","automate workflows"],
"codeaf":["write code","build multi-agent systems"],
"chatacademia":["research the web"],
"json2video-mcp":["connect tools via MCP","generate video"],
"secureauth-mcp-authority":["security & governance","connect tools via MCP"],
"fileaify":["write code","give agents memory","connect tools via MCP"],  # Oct 23 PT: maker submission (project context, vault-brokered credentials, human-approved actions, hosted MCP)
"diri-ai":["sales & support","voice & phone calls"],  # Oct 23 PT: maker submission (voice AI sales role-play with call reports)
"krea":["generate images","generate video","upscale images"],  # Oct 23 PT: Krea refresh (images + text/image-to-video + upscaling, per krea.ai/features/ai-video-generator)
"crolytics":["sales & support","connect tools via MCP","automate workflows"],  # Oct 23 PT: owner request (governed GTM agent workspace; GA4/Search Console/CMS via MCP)
"vellm":["generate video","connect tools via MCP"],  # Oct 23 PT: maker submission (photo-to-video templates with OAuth MCP)
"vidmoat":["edit video","connect tools via MCP"],"salestouch":["sales & support","connect tools via MCP"],  # Oct 23 PT: maker submissions (hosted AI video editor with MCP; LinkedIn MCP for sales agents)
"system-one-api":["build an agent","automate workflows"],"peekpanda":["research the web","social posts & ads","connect tools via MCP"],"hiredov":["business agents","automate workflows"],  # Oct 23 PT: maker submissions, hand-checked ("call logs" wrongly matched voice)
"flogpt":["voice & phone calls","sales & support"],  # Oct 22 PT: "website" keyword wrongly added research the web
"superagnt":["connect tools via MCP","research the web","give agents memory"],  # submission Oct 22: hosted MCP server + REST API (social data, scraping, enrichment, Postgres, memory, inbox)
"gmapsscraper-ai":["sales & support","research the web","connect tools via MCP"],  # submission Oct 21: AI Google Maps lead scraper with REST API and MCP server
"metix-ai":["business agents","automate workflows"],  # submission Oct 21: AI recruiter agent (Mira) that sources, does approved outreach and books interviews
"playable-notes":["make music"],  # submission Oct 21: AI piano sheet music reader and arranger for teachers
"fireply-ai":["social posts & ads"],  # submission Oct 21: AI agent that finds X conversations and replies in your voice
"cliptalk":["generate video","edit video"],  # submission Oct 21: AI video agent for short-form social videos
"bidhelm":["social posts & ads","automate workflows"],  # submission Oct 21: AI marketing department (Google Ads, X); maker edit Oct 21: not customer support or sales outreach
"sphinx":["write code"],  # upkeep Oct 21: git push quiz hook for agent-written code
"reticle":["write code","monitor & evaluate agents"],  # upkeep Oct 21: verifies coding-agent work in the running app
"openknowledge":["give agents memory","productivity","write code"],  # daily discovery Oct 21: keyword guess gave control a computer
"cumora":["build multi-agent systems","productivity","give agents memory"],  # Oct 21: guess gave browser/computer/voice
"monocode":["write code"],  # Oct 21
"pr-lens":["write code","make diagrams"],  # Oct 21
"openappa":["security & governance","monitor & evaluate agents"],  # Oct 21: guess gave write code + voice
"hermex":["personal agents"],  # Oct 21
"wake":["write code"],  # Oct 21: guess gave computer + research
"superlog":["monitor & evaluate agents","automate workflows","write code"],  # Oct 21
"ida-mcp-hex-rays":["connect tools via MCP","security & governance"],  # Oct 21: guess gave automate the browser
"layerfs":["agent infra","run code safely","build multi-agent systems"],  # Oct 21: guess gave voice
"co-op-anything":["games","write code"],  # Oct 21
"tov":["write code"],  # Oct 21: "Tov song" tripped voice
"concat":["edit video","subtitles & transcripts","voiceover"],  # Oct 21
"onetake":["generate video","edit video"],  # Oct 21: guess gave make music
"opencomputer":["build an agent","run code safely","agent infra"],  # Oct 21
"fish-audio":["voiceover","voice & phone calls","build an agent"],  # Oct 21
"lvlz":["personal agents","automate the browser","business agents"],  # Oct 21: guess gave voice
"sundae":["personal agents","automate the browser"],  # Oct 21: guess gave sales & support
"wavespeed-mcp":["connect tools via MCP","generate images","generate video"],  # Oct 21
"trivago-mcp":["connect tools via MCP","research the web"],  # Oct 21: guess gave voice
"wren-x402-doctor":["crypto"],  # maker edit Oct 21: x402 seller tool; "30-day calls" tripped the voice rule
"wren-pre-sign-check":["security & governance","build an agent"],  # submission Oct 21: pre-sign wallet check API
"iart":["generate video","design graphics","voiceover"],  # submission Oct 20 PM: keyword guess gave subtitles & transcripts
"moltgate":["automate workflows"],  # submission Oct 20 PM: "research task" keyword added research the web
"ai-memory":["give agents memory","write code"],  # upkeep Oct 20 PM: keyword guess added build an agent
"smolvm":["run code safely"],"lemonade":["models & local runtimes"],"recall-ai":["voice & phone calls","connect tools via MCP"],"agentic-scientist":["research the web"],"opengcua":["control a computer","automate the browser"],  # upkeep Oct 20 2026 PT: keyword guess added write code / evals
"robylon":["sales & support","voice & phone calls","automate workflows"],"agent-resource-market":["build multi-agent systems"],
# Oct 20, 2026 PT weekly batch: keyword rules mis-tagged these (e.g. "extracts" -> monitor, "browser interface" -> browser automation, "phone number" -> code), so pinned by hand
"mem0":["give agents memory","build an agent"],"zcode":["write code","build multi-agent systems"],"andee":["control a computer","voice & phone calls"],
# Oct 20, 2026 PT afternoon discovery: keyword guess added computer use / browsing / email / multi-agent
"memmy":["give agents memory","personal agents"],"thclaws":["build an agent","models & local runtimes"],"tel-agent":["voice & phone calls","sales & support"],"open-kritt":["security & governance"],
"bops":["automate workflows","control a computer","voice & phone calls"],"graphicle":["give agents memory","write code","connect tools via MCP"],"shipyard":["write code"],
"puter-ai-builder":["build apps without code"],"agentenv-framework":["monitor & evaluate agents","build an agent","connect tools via MCP"],"vicoa":["write code","build multi-agent systems"],
"halofy":["run code safely","connect tools via MCP"],"hiroute":["write code"],"sentio":["automate workflows","connect tools via MCP"],"agent-tincan":["build multi-agent systems","connect tools via MCP"],
"robottraining-jobs":["connect tools via MCP","research the web"],  # Oct 19 PT audit: "hiring data" tripped the customer/sales rule; it is a job board + MCP server, not customer support
"ceofans":["business agents","automate workflows"],
"9bot":["connect tools via MCP","automate workflows"],
"pragor":["security & governance","build multi-agent systems"],  # Pragor (Oct 19 PT, maker request): coordination and governance layer for people and agents, not an autonomous agent; the keyword guess would add "write code"
"cosvoice":["voice & phone calls","connect tools via MCP"],  # CosVoice (Oct 20 PT, owner): phone/email for AI assistants; keyword guess would add "write code" (mentions Cursor, repo)
"mailveri-mcp":["connect tools via MCP"],
# Oct 20, 2026 PT morning discovery: keyword rules mis-tagged these ("call"/"phone" -> voice, "browser" -> browser automation, "search" -> research), so pinned by hand
"opcode":["write code"],"memori":["give agents memory","build an agent"],"cloudcli":["write code"],"xerj":["give agents memory","connect tools via MCP"],
"onlook":["build apps without code","write code"],"agentos":["run code safely","write code"],"agent-sandbox-kubernetes":["run code safely","automate the browser"],
"pooled":["build an agent"],"thinkwatch-lite":["security & governance","write code"],"eleven":["security & governance","write code"],"hy-memory":["give agents memory"],
"oneuptime-mcp":["connect tools via MCP"],"openlayer-mcp":["monitor & evaluate agents","connect tools via MCP"],"mapbox-mcp":["connect tools via MCP"],
"browserstack-mcp":["connect tools via MCP","write code","automate the browser"],"phase":["security & governance"],"zapia":["personal agents","research the web"],
"agentbay":["run code safely","automate the browser","control a computer"],"microsoft-copilot-studio":["build apps without code","build an agent","connect tools via MCP"],
"reason-network":["write code","build multi-agent systems"]}  # MailVeri MCP: email/list verification; kept off customer support (not a support desk); the keyword guess would add "write code"  # CEOFans: the keyword guess would tag it "write code" (it mentions Codex) and "control a computer" ("desktop")
import datetime as _dt
from zoneinfo import ZoneInfo as _Z
_c=(_dt.datetime.now(_Z("America/Los_Angeles")).date()-_dt.timedelta(days=13)).isoformat()
GH=json.load(open("data/github.json")) if os.path.exists("data/github.json") else {}
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
    _g=GH.get(x["slug"]) or {}
    if x.get("github") and _g.get("stars") is not None:
        x["github_stars"]=_g["stars"]
        if _g.get("fetched"): x["stars_checked"]=_g["fetched"]
json.dump(t,open("tools.json","w"),indent=2,ensure_ascii=False)
os.makedirs("tools",exist_ok=True)
e=lambda s:html.escape(str(s or ""))
tpl=open("data/detail.tpl").read()
SOC=[("x.com","X"),("twitter.com","X"),("discord.gg","Discord"),("discord.com","Discord"),("reddit.com","Reddit"),("github.com","GitHub"),("linkedin.com","LinkedIn"),("youtube.com","YouTube")]
def soc_lab(u):
    h=re.sub(r"^https?://(www\.)?","",u).split("/")[0].lower()
    return next((l for d,l in SOC if h==d),None)
def demo_row(x):
    # maker demo video. Served from our own domain (CSP default-src 'self' blocks off-site media), poster + link to the maker's original
    v=x.get("demo_video")
    if not v: return ""
    src=x.get("demo_video_local") or v
    pos=x.get("demo_poster")
    pa=f' poster="{e(pos)}"' if pos else ""
    return f'<h2 style="font-size:16px;margin-bottom:10px">Demo video</h2><div style="margin-bottom:32px;max-width:100%"><video controls preload="none" playsinline{pa} style="display:block;width:100%;max-width:100%;height:auto;aspect-ratio:16/9;border-radius:10px;background:#000" aria-label="{e(x["name"])} demo video"><source src="{e(src)}" type="video/mp4"></video><p style="margin:8px 0 0;font-size:14px"><a href="{e(v)}" target="_blank" rel="nofollow noopener">Watch the original demo video ↗</a> (MP4, from the maker)</p></div>'
def soc_row(x):
    # verified official social links only (tools.json "socials"); no block when empty
    ls=[(u,soc_lab(u)) for u in x.get("socials") or [] if soc_lab(u)]
    if not ls: return ""
    a="".join(f'<a class="b" href="{e(u)}" target="_blank" rel="nofollow noopener" aria-label="{e(x["name"])} on {l}">{l} ↗</a>' for u,l in ls)
    return f'<h2 style="font-size:16px;margin-bottom:10px">Official channels</h2><div class="badges soc" style="margin-bottom:32px;flex-wrap:wrap">{a}</div>'

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
    for k,v in {"ICO":build_extras.ico(x,"../","lg"),"NAME":e(x["name"]),"DESC":e(x["description"]),"URL":e(build_extras.utm(x.get("visit_url") or prim,x)),"HOST":e(host),"GHBTN":ghb,"FACTS":fh,"UC":uc,"REL":relh,"SLUG":x["slug"],"CAT":e(x["category"]),"PRICE":e(x["pricing"]),"BADGE":build_extras.badge_html(x),"CMP":build_extras.cmp_links(x,t),"NEW":(('<span class="b new">New</span>' if x["new"] else "")+(f'<span class="b added">Added {_dt.date.fromisoformat(x["added"]).strftime("%b %-d, %Y")}</span>' if x.get("added") else ""))}.items():
        out=out.replace("{{"+k+"}}",v)
    # Archived GitHub repo label (tools.json "repo_archived": true, owner-approved Oct 22 2026)
    if x.get("repo_archived"):
        out=out.replace('<div class="badges">','<div class="badges"><span class="b warn" title="The GitHub repository is archived (read-only) and no longer updated.">Archived repo</span>',1)
    # Visible status note for archived or stale listings (tools.json "status_note", owner-approved Oct 18 2026)
    if x.get("status_note"):
        _arch=x.get("maturity","").lower().startswith(("archived","discontinued"))
        if _arch or not x.get("repo_archived"):
            out=out.replace('<div class="badges">','<div class="badges"><span class="b warn">'+(("Discontinued" if "discontinued" in x.get("maturity","").lower() else "Archived") if _arch else "No recent updates")+'</span>',1)
        out=out.replace('<p class="lede">'+e(x["description"])+'</p>','<p class="lede">'+e(x["description"])+'</p><p class="statusnote" role="note" style="margin:-6px 0 16px;padding:10px 14px;border:1px solid #b45309;border-radius:10px;font-size:14px">⚠️ '+e(x["status_note"])+'</p>',1)
    # Maker-submitted listings (tools.json "maker_submitted": true + "submitted": YYYY-MM-DD, Pacific): small badge by the name (standing perk, Oct 18 2026)
    if x.get("maker_submitted"):
        _sd=x.get("submitted") or x.get("added","")
        _sdt=_dt.date.fromisoformat(_sd).strftime("%b %-d, %Y") if _sd else ""
        out=re.sub(r'(<div class="badges">.*?)(</div>\s*<h1 class="icoh">)',lambda m:m.group(1)+f'<span class="b maker" title="The maker submitted this tool through our submit form{(" on "+_sdt) if _sdt else ""}. We reviewed and wrote the listing.">✓ Submitted by maker</span>'+m.group(2),out,count=1,flags=re.S)
    # Moves funds label (Oct 21 2026, owner-approved): tools that can sign or send transactions from a wallet
    if x.get("moves_funds"):
        out=re.sub(r'(<div class="badges">.*?)(</div>\s*<h1 class="icoh">)',lambda m:m.group(1)+'<span class="b funds" title="Can move money: this tool can sign or send crypto transactions from a connected wallet. Use spend limits, a separate wallet and human approval for large amounts.">⚠ Moves funds</span>'+m.group(2),out,count=1,flags=re.S)
        out=out.replace('<p class="lede">'+e(x["description"])+'</p>','<p class="lede">'+e(x["description"])+'</p><p class="fundsnote" role="note"><b>⚠ Moves funds.</b> This tool can sign or send crypto transactions from a connected wallet. Give it a separate wallet with only what it needs, set spend limits, and keep human approval on for large amounts. Not financial advice.</p>',1)
    out=out.replace('<h2 style="font-size:16px;margin-bottom:10px">Use cases</h2>',soc_row(x)+demo_row(x)+'<h2 style="font-size:16px;margin-bottom:10px">Use cases</h2>',1)
    B="https://agentscouthq.com/";pg=f"{B}tools/{x['slug']}.html"
    out,_rich=build_rich.apply(out,x,t,build_extras.catslug,prim,B)
    if _rich: out=out.replace(about,(about+_rich[0]) if _rich[4:]==("lite",) else _rich[0],1)  # lite entries keep the About paragraph (additive)
    ld={"@context":"https://schema.org","@graph":[{"@type":"WebPage","@id":pg,"url":pg,"name":f"{x['name']}: what it does, pricing and alternatives","dateModified":x["verified"],"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B},
        "about":{"@type":"SoftwareApplication","name":x["name"],"description":x["description"],"url":prim,**({"sameAs":([gh] if gh and gh!=prim else [])+[u for u in x.get("socials") or [] if soc_lab(u)]} if (gh and gh!=prim) or x.get("socials") else {}),**({"codeRepository":gh} if gh else {}),"applicationCategory":APP_CAT.get(x["slug"],"DeveloperApplication" if x["audience"]=="builders" else "BusinessApplication"),"keywords":", ".join(dict.fromkeys([x["category"]]+x["use_cases"]+LD_KW.get(x["slug"],[])))}},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":x["category"],"item":f"{B}categories/{build_extras.catslug(x['category'])}.html"},{"@type":"ListItem","position":3,"name":x["name"],"item":pg}]}]}
    if _rich:
        ld["@graph"][0]["name"]=_rich[3]; ld["@graph"][0]["about"]={**ld["@graph"][0]["about"],**_rich[1]}; ld["@graph"].append(_rich[2])
    import build_api as _ba
    _ab=ld["@graph"][0]["about"]
    if "operatingSystem" not in _ab: _ab["operatingSystem"]=", ".join(_ba.platforms(x))
    _pt=_ba.tag(x["pricing"])
    _ofs=_ab.get("offers")
    _ofl=_ofs if isinstance(_ofs,list) else ([_ofs] if isinstance(_ofs,dict) else [])
    if _pt in ("free","freemium") or any(isinstance(o,dict) and str(o.get("price",""))=="0" for o in _ofl): _ab["isAccessibleForFree"]=True
    elif _pt=="paid": _ab["isAccessibleForFree"]=False
    if "offers" not in _ab and _pt=="free": _ab["offers"]={"@type":"Offer","price":"0","priceCurrency":"USD","description":x.get("pricing_detail") or x["pricing"]}
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

import build_sponsor
# sponsor.html is frozen (Oct 20 2026): rebuilt only when missing or SPONSOR_REBUILD=1, and restored byte-for-byte at the end of the
# build so sitewide passes (asset versions, nav, footer, live stats) never touch the hidden page.
_SP=open("sponsor.html","rb").read() if os.path.exists("sponsor.html") and os.environ.get("SPONSOR_REBUILD")!="1" else None
if _SP is None: build_sponsor.page(t)  # hidden sponsor page: noindex, not in sitemap, not linked (Oct 18 2026)
import build_bot_templates; build_bot_templates.run()  # extra Bot templates from data/bot-templates-extra.json (Oct 21 2026)
import build_tasks
build_tasks.sitewide(t)
import build_sections
build_sections.build(t)
import build_pick
build_pick.pick(t)
import build_links
import build_openapi
build_openapi.run()  # /openapi.json + /.well-known/openapi.json from the real api/*.json (Oct 21 2026)
build_links.run(t)
import build_seo; build_seo.run(t)
import build_seo_new; build_seo_new.run(t)  # keyword-targeted titles/descriptions for new pages (Oct 21 2026)
import build_ci; build_ci.home(t)  # MCP line, og/twitter desc, free-listing comparison (Oct 22 2026); after build_seo_new, which rewrites the homepage about block
import build_fresh; build_fresh.run(t)  # Updated dates, dateModified, quick comparison tables (Oct 18 2026)
import build_aeo; build_aeo.run(t)  # quick answer + ranked table + verified date on best/mcp/s pages (Oct 22 2026)
import build_listlogos; build_listlogos.run(t)  # logos next to tool names in tables and inline tool lists (Oct 18 2026)
import build_og; build_og.run(t)  # per-page share images (Oct 18 2026)
build_logocheck.listings_gate()  # stop the build if any tool link in a listing lacks its logo (Oct 18 2026)
import build_lighten; build_lighten.run(t)  # lighter leaderboard, writing-code and mcp-servers pages (Oct 22 2026)
import build_fonts; build_fonts.run()  # self-hosted Inter on every page (idempotent)
import build_intlinks; build_intlinks.run(t)  # Popular lists internal links on home/hub/top best pages (owner-approved Oct 22 2026)
import build_fix1022; build_fix1022.run(t)  # category options in HTML, agent.json copy, lighter free-tools/new pages (Oct 22 2026)
import build_aeo as _baeo; _baeo.sync_entity_schema()
build_sponsor.apply_bar(SPONSOR_ENABLED)  # last step: adds the bar when on, removes it when off
if _SP is not None: open("sponsor.html","wb").write(_SP)  # keep the hidden sponsor page untouched
import build_seo_new as _bsn; _bsn.charset_first()  # charset within first 1024 bytes (Oct 21 2026)
# Relevance check (Oct 18, 2026): flag any tasks/, s/, for/ or best/ page with >10% off-topic tools; the build exits 1 so nothing gets committed
import subprocess as _sp, sys as _sys
if _sp.run([_sys.executable,"scripts/check_relevance.py","--strict","--write"]).returncode: print("BUILD FAILED: relevance check (see data/relevance_report.json)"); _sys.exit(1)
