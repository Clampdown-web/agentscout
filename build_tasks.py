import build_extras,build_subtasks
_cap=lambda s:str(s)[:1].upper()+str(s)[1:]  # keeps acronyms (RAG, MCP, SQL, QA) intact
"""Task pages (/tasks/), submit page, and sitewide nav/footer/newsletter injection. Called from build_extras/build_site; reads tools at build time."""
import re,os,json,glob,urllib.parse
from build_extras import e,B,shell,card
# (slug, label, categories, use_cases, keyword regex over name+description, intro)
TASKS=[
("writing-code","writing code",{"coding"},{"write code"},r"\bcoding agent|\bwrites? code|code generation|pair program","Coding agents that write, edit and refactor code from plain-language requests, in your terminal, editor or browser."),
("reviewing-pull-requests","reviewing pull requests",set(),set(),r"pull request|\bPRs?\b|code review|review(s|ing)? code","Agents that read diffs, leave review comments and catch bugs before a pull request is merged."),
("terminal-coding","coding in the terminal",set(),set(),r"\bCLI\b|terminal|command[- ]line|shell","Agents that live in your terminal: give them a task and they read files, run commands and propose changes."),
("browsing-the-web","browsing the web",{"browser/computer use"},{"automate the browser"},r"\bbrowser\b|web navigation|headless","Agents that open pages, click, type and fill in forms in a real browser so you don't have to."),
("computer-use","controlling a computer",set(),{"control a computer"},r"computer use|computer-use|desktop agent|operate (a|your) computer","Agents that see the screen and use the mouse and keyboard to work across desktop apps."),
("web-scraping","scraping websites",set(),set(),r"scrap|crawl|extract(s|ing)? (data|content)|web data","Tools that turn websites into clean data or text an agent can use, from single pages to whole sites."),
("automating-workflows","automating workflows",{"no-code builders"},{"automate workflows"},r"workflow|automat","Platforms for chaining apps, triggers and AI steps into workflows that run on their own."),
("building-apps-without-code","building apps without code",{"app builders"},{"build apps without code"},r"no-code|without code|app builder|prompt to app","Builders that turn a description into a working app or site, no coding required."),
("building-ai-agents","building AI agents",{"frameworks"},{"build an agent"},r"framework|\bSDK\b|agent development kit","Frameworks and SDKs for developers building their own agents, with tools, state and orchestration built in."),
("multi-agent-systems","building multi-agent systems",set(),{"build multi-agent systems"},r"multi-agent|crew|swarm|subagent|orchestrat","Frameworks for teams of agents that hand work to each other, split tasks and check each other's output."),
("building-voice-agents","building voice agents",{"voice"},{"voice & phone calls"},r"\bvoice\b|speech|phone call","Platforms for agents that talk: phone lines, voice assistants and real-time speech in and out."),
("phone-calls","handling phone calls",set(),set(),r"phone|call center|inbound call|outbound call|telephon","Voice agents that answer and place phone calls, book appointments and route callers."),
("customer-support","customer support",{"customer support"},{"sales & support"},r"support|helpdesk|help desk|customer service|ticket","Agents that answer customer questions, resolve tickets and hand off to people when needed."),
("sales-outreach","sales outreach",{"sales & marketing"},set(),r"\bsales\b|outreach|\bSDR\b|lead|prospect|\bCRM\b","Agents that find leads, write outreach and keep your pipeline moving."),
("writing-emails","writing and managing email",set(),set(),r"\bemails?\b|inbox|gmail","Assistants that draft replies, sort your inbox and follow up so email takes less of your day."),
("business-automation","running business operations",{"business agents"},{"business agents"},r"enterprise|back office|operations|business process","Ready-made agents for business teams: operations, finance, HR and other repeatable work."),
("personal-assistants","personal assistance",{"personal agents"},{"personal agents"},r"personal (assistant|agent)|your (day|life)|always-on","Personal agents that run errands online, keep track of tasks and act on your behalf."),
("research","research",{"research"},{"research the web"},r"research|cited|citation|papers","Agents that search, read many sources and come back with a cited answer or report."),
("searching-the-web","web search for agents",set(),set(),r"search API|web search|search engine|retriev","Search APIs and engines built for agents, returning clean results an LLM can use directly."),
("reading-papers","reading scientific papers",set(),set(),r"papers|scientific|academic|literature","Research assistants for academic work: finding papers, summarizing them and extracting findings."),
("data-analysis","data analysis",set(),set(),r"\bdata\b|analytic|spreadsheet|\bSQL\b|dashboard","Agents that query, clean and chart data and explain what it shows."),
("documents","working with documents",set(),set(),r"document|\bPDF|\bRAG\b|knowledge base","Tools that let agents read, search and answer questions over your documents and files."),
("connecting-tools-mcp","connecting tools with MCP",set(),{"connect tools via MCP"},r"\bMCP\b|Model Context Protocol","MCP servers, clients and registries that give agents safe access to your apps and data."),
("building-mcp-servers","building MCP servers",set(),set(),r"MCP server|build(ing)? MCP|MCP SDK|MCP framework|registry","Tools and SDKs for building, hosting and publishing your own MCP servers."),
("agent-memory","memory for agents",set(),{"give agents memory"},r"\bmemory\b|remember|long-term|stateful","Memory layers that let agents remember users, past conversations and facts across sessions."),
("evaluating-agents","evaluating agents",{"evals & observability"},{"monitor & evaluate agents"},r"\beval|benchmark|test(s|ing)? (agents|LLM)","Evaluation tools for scoring agent outputs, catching regressions and comparing prompts and models."),
("monitoring-agents","monitoring agents in production",set(),set(),r"observab|tracing|traces|monitor|logging","Observability for agents in production: traces, costs, latency and errors in one place."),
("running-code-safely","running code safely",{"sandboxes & code execution"},{"run code safely"},r"sandbox|isolated|secure (runtime|execution)|microVM","Sandboxes that let agents run code and tools in isolation, away from your machine and data."),
("agent-security","agent security and safety",set(),set(),r"secur|safety|guardrail|permission|policy|governance","Guardrails, policies and monitoring that keep agents from doing what they shouldn't."),
("testing-apps","testing apps",set(),set(),r"\bQA\b|\btest(s|ing)?\b|end-to-end|\bE2E\b","Agents that write and run tests, click through your app and report what breaks."),
("making-videos","making videos",set(),set(),r"video","AI agents and tools that script, edit or generate video."),
("making-images-and-design","images and design",{"image generation","graphic design & branding","3D & concept art","photography & photo editing"},{"make diagrams","generate images","design graphics","logos & branding","UI design"},r"\bimage|design|diagram|visual","AI agents for visual work: design agents that build graphics and brand assets from a brief, image generators you can direct by chat, diagram makers, and MCP servers that let agents work in Figma, Canva and Penpot."),
("games","AI games and game makers",{"games"},set(),r"\bgames?\b|game master|dungeon|NPC|Minecraft","AI-made and AI-driven games: text adventures, AI game masters for tabletop, games against AI agents, AI NPC engines and tools that make games."),
("crypto-and-wallets","crypto and wallets",{"crypto"},set(),r"crypto|wallet|blockchain|onchain|stablecoin|x402|web3","Wallets, payment rails and tools that let agents hold funds and pay for things on their own."),
("agent-payments","agent payments",set(),set(),r"payment|pay for|checkout|billing|x40[12]","Tools that let agents pay, get paid and handle checkout without a human clicking buy."),
("deploying-agents","deploying and hosting agents",set(),set(),r"\bdeploy(s|ing)? (\w+ ){0,3}agents\b|\bagent (hosting|runtime|cloud)\b|\bhost(s|ing)? (AI )?agents\b|\bagents? in production\b|\bserverless\b","Infrastructure for running agents in production: hosting, scaling and serverless runtimes."),
("open-source-agents","open-source agents",set(),set(),r"\bopen[- ]source (\w+[- ]){0,2}(AI )?(agent|assistant)s?\b(?! (framework|platform|SDK|library|memory|infrastructure))","Open-source agents you can run yourself, inspect and extend, from coding agents to personal assistants."),
("security-testing","security testing",set(),set(),r"penetration|pentest|red[- ]team|vulnerab|bug bount|security (audit|analysis|scan|testing)","Agents that probe your app, code and smart contracts the way an attacker would: running penetration tests, red-teaming AI systems and flagging vulnerabilities with suggested fixes."),
("devops-and-incidents","site reliability and incident response",set(),set(),r"\bSRE\b|incident|on-call|production alerts|root cause|Terraform|Kubernetes UI|(?<!inference )on Kubernetes|cloud infrastructure|pipelines, builds|failed jobs","AI SRE agents and MCP servers that investigate alerts, read dashboards and CI logs, and help manage cloud infrastructure, so incidents get a first look before anyone is paged."),
("parallel-coding-agents","running coding agents in parallel",set(),set(),r"parallel (coding )?agents|(multiple|many) coding agents|worktrees|verifies tasks in parallel|control plane for dispatching","Command centers, IDEs and CLIs for running several coding agents at once, each on its own task or Git worktree, then reviewing what they hand back."),
("agent-identity","agent identity and logins",set(),set(),r"\bidentity\b|\bauth\b(?! and storage)|credential handling|payment credentials|login layer","Identity, auth and credential tools that let agents sign in to apps, prove who they act for and use secrets without ever seeing the raw passwords or keys."),
("spreadsheets-and-slides","spreadsheets, slides and docs",set(),set(),r"spreadsheet|Excel|Google Sheets|slides|PowerPoint|office suite|Airtable|Google Workspace|Microsoft 365","AI spreadsheets, slide makers and office tools, plus MCP servers that let agents read and edit Excel, Airtable and Google Workspace files."),
("training-agents","training and fine-tuning agents",set(),set(),r"fine[- ]tun|post[- ]train|reinforcement learning|\bRL\b|train(s|ing)? (better |LLM-based )?(agents|agentic models)","Platforms and open-source libraries for fine-tuning models and training agents with reinforcement learning, so they get better at your specific tasks."),
("running-agents-locally","running agents locally",set(),set(),r"\blocal[- ]first\b|run(s|ning)? (\w+ ){0,4}locally|fully local|on your own hardware|on your (GPU|NPU)|local and hosted models","Agents, model servers and tools that run on your own computer or hardware, keeping your data local and cutting out per-call API costs where possible."),
("databases","working with databases",set(),set(),r"vector database|search database|multimodal database|\bPostgres|MySQL|MongoDB|ClickHouse|Supabase|PlanetScale|text-to-SQL|SQL engine|Toolbox for Databases|Database MCP|spreadsheet and database|gives coding agents a database","Database MCP servers, vector stores and text-to-SQL tools that let agents query, manage and store data in Postgres, MySQL, MongoDB and more."),
("trading","trading",set(),set(),r"\btrad(ing|es)\b|\bswaps?\b|\bperps\b|prediction markets|market signals","AI trading agents and copilots that research markets, turn plain-language strategies into trades and execute swaps, mostly in crypto, some across stocks and forex. Trading is risky; none of this is financial advice."),
("chat-apps","chat apps like Slack and Telegram",set(),set(),r"Telegram|WhatsApp|iMessage|\bDiscord\b|\bSlack\b(?! alerts)","Agents you can talk to, or hand work to, from the chat apps you already use: Slack, Telegram, WhatsApp, Discord and iMessage."),
("marketing","marketing",set(),set(),r"marketing|go-to-market|\bSEO\b|social media","AI agents for marketing and go-to-market work: running campaigns and outbound, handling social media and pulling SEO, ad and social data for your agents."),
("smart-contract-security","smart contract security",set(),set(),r"smart[- ]contract|contract analysis","AI auditors and agents that review smart contracts for exploitable bugs before and after deployment, plus tools that help build and check Web3 code."),
("coding-docs","feeding docs to coding agents",set(),set(),r"documentation|up-to-date docs|docs and best practices|searching docs","MCP servers that give coding agents current, version-specific documentation, so they stop guessing at outdated APIs."),
("storyboarding","storyboarding and previs",set(),{"plan & storyboard"},r"storyboard|previs|animatic|shot list|script breakdown|call sheet|screenplay|script coverage","Tools that turn a script into storyboards, shot lists, animatics and 3D previs, plus script breakdowns and coverage for pre-production."),
("rough-cuts","rough cuts and assembly edits",set(),set(),r"rough (cut|assembl)|stringout|selects|auto-edit|multicam|bad takes|silences|filler words|highlights","Assistant editors that log footage, pick selects, remove bad takes and silences and assemble a first cut you can finish in your editor."),
("subtitles","subtitles and captions",set(),{"subtitles & transcripts"},r"subtitle|caption|transcri","Transcription, captioning and translated subtitles for film, TV and online video, from editor plugins to live broadcast captions."),
("dubbing","dubbing and lip sync",set(),{"dub & localize"},r"\bdub|lip.?sync|locali[sz]|voice clon","AI dubbing: translated voices that keep the actor's sound, and visual dubbing that matches lip movement to the new language."),
("vfx","VFX and compositing",set(),set(),r"\bVFX|composit|roto|relight|clean plate|planar|object removal|motion capture|mocap|camera track|virtual production|CG scenes","AI for visual effects: rotoscoping and masks, relighting, compositing, tracking, markerless mocap and virtual production."),
("dialogue-cleanup","dialogue cleanup and repair",set(),{"clean up audio"},r"dialogue|noise|de-?reverb|reverb|repair|filler words|mouth sounds|speech enhance|Enhance Speech","Plugins and apps that remove noise, reverb, hum and clicks from dialogue and rebalance voice against background, for film, TV and podcasts."),
("scoring","scoring and soundtracks",set(),set(),r"\bscore\b|soundtrack|background music|royalty-free|compos|music generat|songs?\b","AI music for picture: generate or compose score, background tracks and songs you can license for film, TV, ads and video."),
("stem-separation","stem separation",set(),{"separate stems"},r"\bstems?\b|vocal remov|separat|splitter|unmix|isolat|\bDME\b","Split a mix into vocals, drums, bass and other stems, or dialogue, music and effects (DME), for remixing, karaoke, dubbing and clean-up."),
("video-post-production","video post-production",set(),set(),r"\bedit|rough cut|subtitle|caption|colou?r|grading|\bVFX|upscal|enhanc|lip.?sync|visual dubbing|composit|roto|footage|transcri","Picture post in one place: editing and assistant-editor agents, subtitles, color, VFX, upscaling and visual dubbing, grouped by stage."),
("audio-post-production","audio post-production",set(),set(),r"dialogue (clean|repair|isolat|level)|dialogue,|Foley|sound effects?|\bADR\b|loudness|de-?reverb|reverb|noise|echo|voice isolation|sound to picture|\bDME\b|\bdubbing\b|audio repair|audio post|sound design|clean up audio","Sound for picture, grouped by stage: dialogue cleanup, ADR and dubbing voices, Foley and sound effects, and the editors and mixing tools that tie it together."),
("music-mixing-mastering","music mixing and mastering",set(),{"mix & master"},r"\bmix|master|pitch correction|vocal (mixing|tuning)|AutoTune|level rider","Mixing and mastering assistants for music: AI mix and master services, mixing and vocal plugin suites, pitch correction and loudness tools."),
# Art, design, 3D & photo tasks (Oct 18, 2026): art-only pages (see ART_TASKS)
('open-source-image-generation','open-source image generation',set(),{'open image models'},r'open[- ](?:source|weights?)','Open models and free local apps for AI image generation: run FLUX, Stable Diffusion, Qwen-Image and more on your own computer, with no per-image fees and full control.'),
('illustration-and-concept-art','illustration and concept art',set(),{'concept art'},r'illustrat|concept art|character design|sketch(?:es)? (?:to|into)','Tools for illustrators and concept artists: style-controlled generation, sketch-to-render, painting assistants and private style models.'),
('logo-and-brand-design','logos and brand kits',set(),{'logos & branding'},r'\\blogos?\\b|brand kit|brand identity|on-brand','AI logo makers and brand tools that create a logo, colors, fonts and on-brand assets from a short brief.'),
('vectorizing-images','vectorizing images',set(),{'vectorize'},r'\\bvectors?\\b|\\bSVG\\b|vectoriz','Turn bitmaps into clean SVG, PDF or EPS vectors, or generate vector art directly.'),
('ui-design-and-mockups','UI design and mockups',set(),{'UI design'},r'\\bUI\\b|wireframe|mockup|prototyp','Prompt-to-UI tools that turn a description, sketch or screenshot into editable screens, wireframes, prototypes and front-end code.'),
('social-posts-and-ad-creatives','social posts and ad creatives',set(),{'social posts & ads'},r'social (?:media )?posts?|\\bads?\\b|ad creatives?|posters?|flyers?|campaigns?','AI design tools and agents that make social posts, ads, posters and whole campaigns from a brief, in your brand style.'),
('text-to-3d','text and image to 3D',set(),{'generate 3D'},r'\\b3D (?:models?|assets?|mesh\\w*|worlds?|objects)|text-to-3D|image-to-3D|to 3D\\b','Generate textured 3D models, scenes and worlds from a prompt or a picture, ready for games, AR, printing or product design.'),
('3d-rigging-and-animation','3D rigging and character animation',set(),{'animate characters'},r'auto-?rig|rigg(?:ed|ing)|character animation|motion capture|mocap','Auto-riggers and AI animation tools that turn a static character into one that moves, from text, video or keyframes.'),
('architecture-and-real-estate-visuals','architecture and real estate visuals',set(),{'real estate photos', 'architecture visuals'},r'architect|interior|SketchUp|Revit|real[- ]estate|virtual(?:ly)? stag','AI renderers for architects and interior designers, plus real-estate photo editing and virtual staging for listings.'),
('photo-culling','photo culling',set(),{'cull photos'},r'\\bcull','AI culling that picks the keepers from a shoot: flags blinks, focus misses and duplicates so you edit only the best frames.'),
('photo-editing-in-your-style','AI photo editing in your style',set(),{'edit in your style'},r'learns your (?:\\w+ )?(?:editing )?style|in your (?:own )?style|editing profile','AI that learns how you edit, from your past Lightroom catalogs or presets, and batch-edits new shoots the same way.'),
('portrait-retouching','portrait retouching',set(),{'retouch portraits'},r'retouch|portrait','Batch portrait retouching: skin, blemishes, eyes and lighting, with control over how natural it stays.'),
('upscaling-and-restoring-photos','upscaling and restoring photos',set(),{'upscale images', 'restore photos'},r'upscal|enlarg|restor\\w* (?:old|faces|photos)|blurry','Upscale low-resolution images and restore old, blurry or damaged photos with AI.'),
('background-removal','background removal',set(),{'remove backgrounds'},r'background remov|remove backgrounds?|cutouts?','One-click background removal and replacement for product shots, portraits and design work, with APIs for bulk jobs.'),
('product-photography','AI product photography',set(),{'product photos'},r'product photo|e-commerce|on-model|fashion (?:brands|photos)|listings?','AI product photoshoots for online sellers: studio backgrounds, lifestyle scenes and on-model fashion images from one product shot.'),
('ai-headshots','AI headshots',set(),{'headshots'},r'headshot','Professional headshots made from your own selfies. Every tool here works from photos of you that you upload yourself.'),
('organizing-photos','organizing photo libraries',set(),{'organize photos'},r'photo (?:library|libraries)|organi[sz]|face recognition|keyword','AI photo libraries and catalogers that tag, search and sort large collections, including private self-hosted options.'),
]
ORIG={T[0] for T in TASKS[:37]}  # the first 37 task pages (Oct 2026); later batches only append to their related links
MEDIA_CATS={"film & TV production","video generation","film & TV audio","music production"}
TASK_NEG={"sales-outreach":r"AI marketing department","agent-payments":r"payments (?:are |is )?disabled|real-money payments|no money moves","audio-post-production":r"upscal|deinterlace|script coverage|lip sync|footage","building-voice-agents":r"from a voice or text request"}  # keeps picture tools off the sound page
MEDIA_TASKS={"storyboarding","rough-cuts","subtitles","dubbing","vfx","dialogue-cleanup","scoring","stem-separation","video-post-production","audio-post-production","music-mixing-mastering"}
_MEDIA_ONLY_TASKS=MEDIA_TASKS  # these pages only list film, TV, video and music tools
ART_CATS={"image generation","graphic design & branding","3D & concept art","photography & photo editing"}
ART_TASKS={'open-source-image-generation','illustration-and-concept-art','logo-and-brand-design','vectorizing-images','ui-design-and-mockups','social-posts-and-ad-creatives','text-to-3d','3d-rigging-and-animation','architecture-and-real-estate-visuals','photo-culling','photo-editing-in-your-style','portrait-retouching','upscaling-and-restoring-photos','background-removal','product-photography','ai-headshots','organizing-photos'}
import relevance  # relevance score (Oct 18, 2026): one generic keyword is no longer enough; see relevance.py and scripts/check_relevance.py
def match(x,T):
    _,_,cats,ucs,rx,_=T
    c=x.get("category"); _m=c in MEDIA_CATS; _a=c in ART_CATS
    if T[0] in _MEDIA_ONLY_TASKS and not _m: return False
    if T[0] in ART_TASKS:  # art-only pages: art tools, plus tools explicitly tagged with the page's use case
        if not _a: return bool(set(x.get("use_cases",[]))&ucs)
        return c in cats or bool(set(x.get("use_cases",[]))&ucs) or bool(re.search(rx,x.get("description",""),re.I))
    if _m and T[0] not in MEDIA_TASKS and not x.get("agentic"): return False  # non-agentic media tools stay off the agent task pages
    if _a and not x.get("agentic"): return False  # same for art, design, 3D and photo tools
    if T[0] in TASK_NEG and re.search(TASK_NEG[T[0]],x.get("description",""),re.I): return False
    return relevance.relevant(x,T)
REDIRECTED_TASKS={"games"}  # Oct 18 2026: same tools as categories/games (redirect in redirects.json)
def mapping(t):
    m={}
    for T in TASKS:
        if T[0] in REDIRECTED_TASKS: continue
        items=[x for x in t if match(x,T)]
        if len(items)>=3:
            items.sort(key=lambda x:(not x.get("featured"),x.get("category") not in T[2],not (set(x.get("use_cases",[]))&T[3]),-(x.get("github_stars") or 0),x["name"].lower()))
            m[T[0]]=(T,items)
    return m
def tasks_for(x,m): return [T for s,(T,items) in m.items() if x in items]
def _grid(items,task=None):
    r=build_subtasks.sections(items,task=task)
    if not r: return f'<div class="grid">{"".join(card(x) for x in build_extras.newfirst(items))}</div>'
    secs,other=r
    chips='<div class="badges stchips" role="navigation" aria-label="Sub-tasks" style="margin:10px 0 4px">'+"".join(f'<a class="b uc" href="#st-{sl}">{e(l[0].upper()+l[1:])} ({len(v)})</a>' for sl,l,v in secs)+(f'<a class="b uc" href="#st-more">More tools ({len(other)})</a>' if other else "")+('<a class="b uc" href="#repos">GitHub repos</a>' if len(build_subtasks.repo_rows(items)[0])>=3 else "")+'</div>'
    sp={(p_,sub):sl for sl,p_,sub,_ in SUBP}
    h=lambda i,l,n:f'<h2 id="st-{i}" style="font-size:18px;margin:32px 0 10px;scroll-margin-top:84px">{e(l)} <span style="color:var(--muted);font-weight:400">({n})</span>'+(f' <a href="{sp[(task,i)]}.html" style="font-size:14px;font-weight:500;margin-left:6px">See the full list →</a>' if (task,i) in sp else "")+'</h2>'
    out=chips+"".join(h(sl,l[0].upper()+l[1:],len(v))+f'<div class="grid">{"".join(card(x) for x in build_extras.newfirst(v))}</div>' for sl,l,v in secs)
    if other: out+=h("more","More tools",len(other))+f'<div class="grid">{"".join(card(x) for x in build_extras.newfirst(other))}</div>'
    return out
SUBP=[]
def _existing_sets():
    out=[]
    import build_landing as _bl
    out+=_bl.absorbed_sets()
    for f in glob.glob("s/*.html")+glob.glob("best/*.html"):
        if f.endswith("index.html"): continue
        body=open(f).read().split("<main",1)[-1].split('id="nlblock"')[0]
        out.append(set(re.findall(r'tools/([a-z0-9-]+)\.html',body)))
    return [x for x in out if x]
# --- Natural <title> wording (Oct 18 2026): sentence case, no repeated words ---
_TT_LABEL={"agent-memory":"agent memory","searching-the-web":"agent web search","games":"games and game making"}
_TT_FULL={"open-source-agents":"Best open-source AI agents","storyboarding":"Best AI storyboarding and previs tools","rough-cuts":"Best AI tools for rough cuts and assembly edits",
 "subtitles":"Best AI subtitle and caption tools","dubbing":"Best AI dubbing and lip sync tools","vfx":"Best AI VFX and compositing tools","dialogue-cleanup":"Best AI dialogue cleanup and repair tools",
 "scoring":"Best AI music for scoring and soundtracks","stem-separation":"Best AI stem separation tools","video-post-production":"AI video post-production tools by stage",
 "audio-post-production":"AI audio post-production tools by stage","music-mixing-mastering":"Best AI music mixing and mastering tools",
 "open-source-image-generation":"Best open-source AI image generators","illustration-and-concept-art":"Best AI tools for illustration and concept art","logo-and-brand-design":"Best AI logo makers and brand kit tools","vectorizing-images":"Best AI tools to vectorize images","ui-design-and-mockups":"Best AI UI design and mockup tools","social-posts-and-ad-creatives":"Best AI tools for social posts and ad creatives","text-to-3d":"Best AI text and image to 3D tools","3d-rigging-and-animation":"Best AI 3D rigging and character animation tools","architecture-and-real-estate-visuals":"Best AI tools for architecture and real estate visuals","photo-culling":"Best AI photo culling tools","photo-editing-in-your-style":"Best AI photo editors that learn your style","portrait-retouching":"Best AI portrait retouching tools","upscaling-and-restoring-photos":"Best AI photo upscalers and restoration tools","background-removal":"Best AI background removal tools","product-photography":"Best AI product photography tools","ai-headshots":"Best AI headshot generators","organizing-photos":"Best AI photo library and organizing tools","making-images-and-design":"Best AI agents for images and design"}
_ART_NOTE='<p style="margin:0 0 6px;font-size:13px;color:var(--muted)">Selling AI-assisted art? Check each tool\'s license and see the short <a href="../for/artists.html#copyright">commercial-use and copyright note</a>.</p>'
_MEDIA_PTR={"making-images-and-design":'<p style="margin:0 0 6px;font-size:14px">This page lists AI agents and MCP servers that create or edit visuals for you. For every art, design, 3D and photo tool, see <a href="../categories/image-generation.html">Image generation</a>, <a href="../categories/graphic-design-branding.html">Graphic design &amp; branding</a>, <a href="../categories/3d-concept-art.html">3D &amp; concept art</a> and <a href="../categories/photography-photo-editing.html">Photography &amp; photo editing</a>.</p>',
 "illustration-and-concept-art":_ART_NOTE,"open-source-image-generation":_ART_NOTE,
 "making-videos":'<p style="margin:0 0 6px;font-size:14px">This page lists AI agents that script, edit or generate video. For every film and video tool, see <a href="../categories/film-tv-production.html">Film &amp; TV production</a>, <a href="../categories/video-generation.html">AI video generation</a>, <a href="../categories/film-tv-audio.html">Film &amp; TV audio</a> and <a href="../categories/music-production.html">Music production</a>.</p>',
 "video-post-production":'<p style="margin:0 0 6px;font-size:14px">Picture post only. For sound, see <a href="audio-post-production.html">audio post-production</a>; for music, see <a href="music-mixing-mastering.html">music mixing and mastering</a>. Every tool: <a href="../categories/film-tv-production.html">Film &amp; TV production</a>.</p>',
 "audio-post-production":'<p style="margin:0 0 6px;font-size:14px">Sound for picture only. For music, see <a href="music-mixing-mastering.html">music mixing and mastering</a>; for picture, see <a href="video-post-production.html">video post-production</a>. Every tool: <a href="../categories/film-tv-audio.html">Film &amp; TV audio</a>.</p>',
 "music-mixing-mastering":'<p style="margin:0 0 6px;font-size:14px">Music post only. For dialogue and sound for picture, see <a href="audio-post-production.html">audio post-production</a>. Every tool: <a href="../categories/music-production.html">Music production</a>.</p>'}
# Distinct angle for task pages that overlap a category (Oct 18 2026): the category page is the main
# target for the head keyword; the task page answers "how do I add X", grouped by use case.
_TASK_ANGLE={"agent-memory":{"h1":"How to add long-term memory to AI agents: tools by use case",
  "title":"Add long-term memory to AI agents: tools by use case (2026)",
  "desc":lambda n,items:f"How to add long-term memory to an AI agent: {n} tools grouped by use case, from RAG over documents to local memory and codebase context."[:158],
  "pointer":'<p style="margin:0 0 6px;font-size:14px">Want the ranked list of memory and RAG products? See the <a href="../categories/memory-rag.html">Memory &amp; RAG category</a>.</p>'},
 "personal-assistants":{"h1":"What a personal AI assistant can do for you: tools by use case",
  "title":"Personal AI assistants by use case: desktop, chat, local (2026)",
  "desc":lambda n,items:f"Pick a personal AI assistant by what you need it to do: {n} tools grouped by use case, from desktop control and chat apps to local and private setups."[:158],
  "pointer":'<p style="margin:0 0 6px;font-size:14px">Want the full ranked list? See the <a href="../categories/personal-agents.html">Personal agents category</a>.</p>'},
 "crypto-and-wallets":{"h1":"Crypto AI agents by job: trading, wallets, payments and data",
  "title":"Crypto AI agents by job: trading, wallets and payments (2026)",
  "desc":lambda n,items:f"Find a crypto AI agent by job: {n} tools grouped into trading agents, agent wallets, agent payments and on-chain data MCP servers. Not financial advice."[:158],
  "pointer":'<p style="margin:0 0 6px;font-size:14px">Want every crypto tool in one list? See the <a href="../categories/crypto.html">Crypto category</a>.</p>'},
 "connecting-tools-mcp":{"h1":"How to connect AI agents to your tools with MCP, by use case",
  "title":"Connect AI agents to your tools with MCP: picks by use case (2026)",
  "desc":lambda n,items:f"How to connect an AI agent to apps and data with MCP: {n} servers, gateways and tools grouped by job, from databases to browsers and auth."[:158],
  "pointer":'<p style="margin:0 0 6px;font-size:14px">Looking for the full list of MCP servers? See the <a href="../categories/mcp-servers.html">MCP servers category</a>.</p>'}}
def task_title(s,label):
    if s in _TT_FULL: return _TT_FULL[s]
    lab=_TT_LABEL.get(s,label)
    return f"Best tools for {lab}" if "agent" in lab.lower() else f"Best AI agents for {lab}"
# parent context for sub-task titles (short noun phrase)
_SUB_CTX={"agent-memory":"agent memory","automating-workflows":"workflow automation","browsing-the-web":"web browsing agents","building-ai-agents":"building AI agents",
  "crypto-and-wallets":"crypto agents","evaluating-agents":"agent evaluation","making-images-and-design":"image and design agents","personal-assistants":"personal AI assistants",
  "research":"research agents","terminal-coding":"terminal coding","testing-apps":"app testing","writing-code":"coding agents","agent-security":"agent security",
  "searching-the-web":"agent web search","building-voice-agents":"voice agents","customer-support":"customer support","data-analysis":"data analysis"}
# sub-task noun phrase used in titles
_SUB_NOUN={"vector-rag":"RAG and document tools","images-design":"image and design tools","research-agents":"research and report agents","text-to-sql":"SQL and database tools",
  "evals":"eval and benchmark tools","no-code-apps":"no-code app builders","agent-memory":"memory tools","agent-wallets":"agent wallet tools","agent-payments":"agent payment tools",
  "guardrails":"guardrail and policy tools","agent-frameworks":"agent frameworks and SDKs","local-models":"local and self-hosted tools","multi-agent":"multi-agent orchestration tools",
  "workflow-automation":"workflow automation tools","testing-qa":"testing and QA tools","voice-phone":"voice and phone agents"}
def _stem(w): return w.lower().strip(",")[:4]
def subtask_title(parent,sub,lab,plabel,n):
    noun=_SUB_NOUN.get(sub) or (lab if lab.split()[-1] in ("agents","tools","builders","SDKs") else f"{lab} tools")
    ctx=_SUB_CTX.get(parent,plabel)
    stop={"and","for","the","with","tool","tools","agen","ai"}
    overlap={_stem(w) for w in noun.split()}&{_stem(w) for w in ctx.split()}-stop
    return f"{n} AI {noun}" if overlap else f"{n} {noun} for {ctx}"
def subtask_h1(parent,sub,lab,plabel):
    t=subtask_title(parent,sub,lab,plabel,0)[2:]
    return t[0].upper()+t[1:]
def _sublabel(sub): return build_subtasks.LABEL[sub]
def _subindex(m):
    if not SUBP: return ""
    return ('<h2 style="font-size:19px;margin:36px 0 12px">Narrower lists</h2><p class="muted" style="margin:0 0 12px">Sub-tasks with enough tools to get their own page.</p><div class="badges">'
        +"".join(f'<a class="b uc" href="{sl}.html">{e(_cap(m[p_][0][1]))}: {e(_sublabel(sub))} ({len(its)})</a>' for sl,p_,sub,its in sorted(SUBP,key=lambda z:(m[z[1]][0][1],z[2])))+'</div>')
def _subpages_write(m):
    urls=[]
    for sl,p_,sub,its in SUBP:
        T,pitems=m[p_]; plabel=T[1]; lab=_sublabel(sub); n=len(its); canon=f"{B}tasks/{sl}.html"
        its=sorted(its,key=lambda x:(not x.get("featured"),-(x.get("github_stars") or 0),x["name"].lower()))
        h1=subtask_h1(p_,sub,lab,plabel)
        title=f"{subtask_title(p_,sub,lab,plabel,n)} · AgentScout"
        _st=subtask_title(p_,sub,lab,plabel,n); _nm=', '.join(x['name'] for x in its[:3])
        desc=next((d for d in (f"{_st}, including {_nm}. Link-checked, with pricing as makers state it.",f"{_st}, including {_nm}. Link-checked.",f"{_st}, including {_nm}.") if len(d)<=158),f"{_st}, including {_nm}."[:158])
        starred=[x for x in its if x.get("github_stars")][:3]
        from collections import Counter
        cats=Counter(x["category"] for x in its).most_common(3)
        intro=(f"{e(build_subtasks.SUBDESC[sub])} Of the {len(pitems)} tools on our <a href=\"{p_}.html\">{e(plabel)}</a> page, {n} fit this narrower job. "
               f"By pricing: {e(build_subtasks.price_line(its))}. "
               +(f"The most-starred open repos here are "+", ".join(f'<a href="../tools/{x["slug"]}.html">{e(x["name"])}</a> ({x["github_stars"]:,} stars)' for x in starred)+". " if starred else "")
               +"Most come from the "+", ".join(f'<a href="../categories/{build_extras.catslug(c)}.html">{e(c)}</a> ({k})' for c,k in cats)+" categor"+("ies." if len(cats)>1 else "y."))
        sibs=[(sl2,sub2,its2) for sl2,p2,sub2,its2 in SUBP if p2==p_ and sl2!=sl]
        sibh=('<h2 style="font-size:16px;margin:32px 0 10px">More from '+e(plabel)+'</h2><div class="badges"><a class="b uc" href="'+p_+'.html">All '+e(plabel)+f' tools ({len(pitems)})</a>'+"".join(f'<a class="b uc" href="{sl2}.html">{e(_sublabel(sub2).capitalize())} ({len(i2)})</a>' for sl2,sub2,i2 in sibs)+'<a class="b uc" href="index.html">All tasks →</a></div>')
        top=its[:3]
        faq=[(f"What are the best AI tools for {plabel} focused on {lab}?",f"We list {n}. The first three by GitHub stars and featured status are "+"; ".join(f"{x['name']}: {x['description']}" for x in top)),
             (f"Are there free or open-source options?",f"Yes: {build_subtasks.price_line(its)}. Pricing is as each maker states it." if any(x["pricing"] in build_subtasks.OPEN|build_subtasks.FREE for x in its) else f"Pricing breakdown: {build_subtasks.price_line(its)}.")]
        faqh='<h2 style="font-size:16px;margin:32px 0 10px">FAQ</h2>'+"".join(f'<h3 style="font-size:15px;margin:16px 0 6px">{e(q)}</h3><p style="margin:0">{e(a)}</p>' for q,a in faq)
        body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">Tasks</a> / <a href="{p_}.html">{e(_cap(plabel))}</a> / {e(_cap(lab))}</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">{e(h1)}</h1>'
              f'<p class="lede" style="margin-left:0;text-align:left">{intro}</p><div class="grid">{"".join(card(x) for x in its)}</div>{build_subtasks.repo_table(its)}{faqh}{sibh}<p class="disclose">Tools are grouped by what each says it does. Missing one? <a href="../submit.html">Submit it free</a>.</p></section>')
        ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":h1,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
            {"@type":"ItemList","numberOfItems":n,"itemListElement":[{"@type":"ListItem","position":i+1,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate(its)]},
            {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Tasks","item":B+"tasks/index.html"},{"@type":"ListItem","position":3,"name":_cap(plabel),"item":f"{B}tasks/{p_}.html"},{"@type":"ListItem","position":4,"name":_cap(lab),"item":canon}]}]}
        open(f"tasks/{sl}.html","w").write(shell("../",title,desc,canon,body,ld)); urls.append(canon)
    return urls
def pages(t):
    build_subtasks.dump(t)
    os.makedirs("tasks",exist_ok=True); m=mapping(t); urls=[]
    global SUBP
    SUBP=build_subtasks.subpages(m,t,_existing_sets())
    keep=set(m)|{sp[0] for sp in SUBP}
    for f in glob.glob("tasks/*.html"):
        if os.path.basename(f)!="index.html" and os.path.basename(f)[:-5] not in keep: os.remove(f)
    for s,(T,items) in m.items():
        _,label,_,_,_,intro=T; n=len(items); canon=f"{B}tasks/{s}.html"
        h1=f"{task_title(s,label)} (2026)"
        title=f"{task_title(s,label)} (2026) · AgentScout"
        desc=f"Compare {n} AI agents and tools for {label}, including {', '.join(x['name'] for x in items[:3])}. Link-checked, with pricing as makers state it."[:158]
        _ang=_TASK_ANGLE.get(s)
        if _ang: h1,title,desc=_ang["h1"],_ang["title"]+" · AgentScout",_ang["desc"](n,items)
        rel=[(s2,T2) for s2,(T2,i2) in m.items() if s2!=s and len(set(id(a) for a in i2)&set(id(a) for a in items))>=2]
        rel=sorted(rel,key=lambda r:-len(set(id(a) for a in m[r[0]][1])&set(id(a) for a in items)))
        if s in ORIG: rel=[r for r in rel if r[0] in ORIG][:8]+[r for r in rel if r[0] not in ORIG][:3]  # original pages keep their related list; newer tasks are appended
        else: rel=rel[:8]
        relh='<h2 style="font-size:16px;margin:32px 0 10px">Related tasks</h2><div class="badges">'+"".join(f'<a class="b uc" href="{s2}.html">{e(_cap(T2[1]))} ({len(m[s2][1])})</a>' for s2,T2 in rel)+'<a class="b uc" href="index.html">All tasks →</a></div>'
        if s not in ORIG:  # newer task pages also link the categories their tools come from
            from collections import Counter
            cc=Counter(x["category"] for x in items).most_common()
            relh='<h2 style="font-size:16px;margin:32px 0 10px">Browse these categories</h2><div class="badges">'+"".join(f'<a class="b uc" href="../categories/{build_extras.catslug(c)}.html">{e(c)} ({k})</a>' for c,k in cc)+'</div>'+relh
        body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">Tasks</a> / {e(_cap(label))}</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">{e(h1)}</h1>'
              f'<p class="lede" style="margin-left:0;text-align:left">{e(intro)} We list {n} tools for {e(label)} below, each with a link-checked page, pricing as the maker states it and alternatives.</p><p class="tcount" style="margin:0 0 6px;font-size:14px;color:var(--muted)">{n} tools: {e(build_subtasks.price_line(items))}.</p>'+(_ang["pointer"] if _ang else "")+_MEDIA_PTR.get(s,"")+
              f'{_grid(items,s)}{build_subtasks.repo_table(items)}{relh}<p class="disclose">Tools are matched to tasks by category, use cases and what each tool says it does. Missing one? <a href="../submit.html">Submit it free</a>.</p></section>')
        ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":h1,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
            {"@type":"ItemList","numberOfItems":n,"itemListElement":[{"@type":"ListItem","position":i+1,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate(items)]},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Tasks","item":B+"tasks/index.html"},{"@type":"ListItem","position":3,"name":_cap(label),"item":canon}]}]}
        open(f"tasks/{s}.html","w").write(shell("../",title,desc,canon,body,ld)); urls.append(canon)
    canon=B+"tasks/index.html"; title=f"AI Agents by Task: {len(m)} Jobs, Best Tools for Each · AgentScout"
    desc=f"Find the best AI agents for {len(m)} tasks, from writing code and browsing the web to voice agents, research and customer support."[:158]
    tiles="".join(f'<a class="card" href="{s}.html"><div class="ct"><h3>{e(_cap(T[1]))}</h3></div><p>{len(items)} tools · {e(", ".join(x["name"] for x in items[:3]))}</p></a>' for s,(T,items) in sorted(m.items(),key=lambda kv:kv[1][0][1]))
    body=f'<div class="crumb"><a href="../index.html">AgentScout</a> / Tasks</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">AI agents by task</h1><p class="lede" style="margin-left:0;text-align:left">Start from the job you need done. {len(m)} tasks, each with the agent tools that handle it.</p><div class="grid">{tiles}</div>{_subindex(m)}</section>'
    ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":"AI agents by task","description":desc,"url":canon},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Tasks","item":canon}]}]}
    open("tasks/index.html","w").write(shell("../",title,desc,canon,body,ld)); urls.insert(0,canon)
    urls+=_subpages_write(m)
    urls.append(submit_page(t)); urls.append(about_page(t)); urls.append(privacy_page(t)); return urls
def submit_page(t):
    canon=B+"submit.html"; cats=sorted({x["category"] for x in t}); title="Submit an AI Agent Tool Free · AgentScout"
    desc="Submit your AI agent tool to AgentScout for free. We review every submission, write the listing ourselves and link-check it."
    inp='style="width:100%;height:44px;padding:0 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text);font:inherit;box-sizing:border-box"'
    def f(id,label,typ="text",req=True,extra=""): return f'<label style="display:block;margin:14px 0 6px;font-weight:600;font-size:14px" for="{id}">{label}{"" if req else " <span style=\"color:var(--faint);font-weight:400\">(optional)</span>"}</label><input id="{id}" name="{id}" type="{typ}" {"required" if req else ""} {extra} {inp}>'
    opts="".join(f'<option>{e(c)}</option>' for c in cats)+"<option>other</option>"
    form=(f'<form id="sf" style="max-width:560px;text-align:left" novalidate>'+f("name","Tool name",extra='maxlength="80"')+f("website","Website","url",extra='placeholder="https://" maxlength="300"')+f("github","GitHub repo","url",False,'placeholder="https://github.com/…" maxlength="300"')
          +f'<label style="display:block;margin:14px 0 6px;font-weight:600;font-size:14px" for="category">Category</label><select id="category" name="category" {inp}>{opts}</select>'
          +f'<label style="display:block;margin:14px 0 6px;font-weight:600;font-size:14px" for="pricing">Pricing</label><select id="pricing" name="pricing" {inp}><option>Open source</option><option>Free</option><option>Freemium</option><option>Paid</option><option>Open source + cloud</option><option>Enterprise / contact sales</option></select>'
          +f'<label id="desclab" style="display:block;margin:14px 0 6px;font-weight:600;font-size:14px" for="desc">Short description</label><textarea id="desc" name="desc" required maxlength="500" rows="3" style="width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text);font:inherit;box-sizing:border-box"></textarea>'
          +f("email","Your email (maker)","email",False,'maxlength="120"')+f("x","X handle","text",False,'placeholder="@yourhandle" maxlength="30"')
          +'<label style="display:block;margin:14px 0 6px;font-weight:600;font-size:14px" for="found">How did you find us? <span aria-hidden="true" style="color:#e5484d">*</span><span class="sr-only" style="position:absolute;left:-9999px">(required)</span></label><select id="found" name="found" required aria-required="true" style="width:100%;height:44px;padding:0 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text);font:inherit;box-sizing:border-box"><option value="">Choose one</option><option value="X (Twitter)">X (Twitter)</option><option value="Google search">Google search</option><option value="Another AI directory">Another AI directory</option><option value="Newsletter">Newsletter</option><option value="Friend or colleague">Friend or colleague</option><option value="Reddit">Reddit</option><option value="Product Hunt">Product Hunt</option><option value="GitHub">GitHub</option><option value="Other">Other</option></select><div id="foundotherwrap" hidden><label style="display:block;margin:14px 0 6px;font-weight:600;font-size:14px" for="foundother">Where did you find us? <span aria-hidden="true" style="color:#e5484d">*</span></label><input id="foundother" name="foundother" type="text" maxlength="100" aria-required="true" placeholder="e.g. a website or community" style="width:100%;height:44px;padding:0 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text);font:inherit;box-sizing:border-box"></div><div aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden"><label for="company">Company (leave empty)</label><input id="company" name="company" type="text" tabindex="-1" autocomplete="off"></div><p id="serr" role="alert" style="color:#e5484d;min-height:20px;margin:12px 0 0;font-size:14px"></p><button class="btn primary" type="submit" style="height:46px;margin-top:6px">Submit for free review</button></form>'
          +'<div id="sdone" hidden style="max-width:560px;text-align:left;border:1px solid var(--accent);border-radius:12px;padding:18px;margin-top:8px"><b>Thanks, your submission is in.</b> We\'ll review it, usually within a few days. Questions? Email <a href="mailto:support@agentscouthq.com">support@agentscouthq.com</a>.<p style="margin:10px 0 0">While you wait, grab a <a href="badges.html#featured-badge">Featured on AgentScout badge</a> for your site or README.</p></div>')
    js=r'''<script>var SUBMIT_URL="https://agentscout-image.agentscouthq.workers.dev/submit";var UPD="";(function(){var P=new URLSearchParams(location.search),tl=(P.get("tool")||"").toLowerCase();if(P.get("type")!=="update"||!/^[a-z0-9-]{1,100}$/.test(tl))return;
fetch("tools.json",{cache:"no-cache"}).then(function(r){return r.json()}).then(function(T){var x=(T||[]).filter(function(y){return y.slug===tl})[0];if(!x)return;UPD=tl;function s(id,v){var el=document.getElementById(id);if(el&&v)el.value=v}
s("name",x.name);s("website",x.website||x.url);s("github",x.github);var c=document.getElementById("category");if([].some.call(c.options,function(o){return o.text===x.category}))c.value=x.category;
var pm={"Open source":"Open source","Free":"Free","Freemium":"Freemium","Paid":"Paid","Open source + cloud":"Open source + cloud","Enterprise":"Enterprise / contact sales"};if(pm[x.pricing])document.getElementById("pricing").value=pm[x.pricing];
var h=document.querySelector("section h1");if(h)h.textContent="Suggest an edit: "+x.name;var l=document.querySelector("section .lede");if(l)l.innerHTML='Spotted something wrong or out of date on the <a></a> listing? Fix the fields below and tell us what changed. We check every suggestion before anything on the site changes. It\'s free, also for makers.';if(l){var la=l.querySelector("a");la.textContent=x.name;la.setAttribute("href","tools/"+tl+".html")}
document.getElementById("desclab").textContent="What should change? (no links here)";document.getElementById("desc").placeholder="e.g. Pricing is now $20/month; the repo moved to a new org.";var b=document.querySelector("#sf button[type=submit]");if(b)b.textContent="Send suggested edit"}).catch(function(){})})();(function(){var f=document.getElementById("sf"),er=document.getElementById("serr");function v(id){return document.getElementById(id).value.trim()}var fs=document.getElementById("found"),fo=document.getElementById("foundotherwrap");function fop(){return fs&&fs.selectedIndex>=0?fs.options[fs.selectedIndex]:null}if(fs&&fo)fs.addEventListener("change",function(){var q=fop();fo.hidden=!(fs.value==="Other"&&!(q&&q.getAttribute("data-o")));document.getElementById("foundother").required=!fo.hidden});function fnd(){var a=v("found"),q=fop(),d=q&&q.getAttribute("data-o"),o=a==="Other"?(d||v("foundother")):"";return{a:a,o:o}}
function okUrl(u,gh){try{var x=new URL(u);return(x.protocol==="https:"||x.protocol==="http:")&&(!gh||/(^|\.)github\.com$/.test(x.hostname))}catch(e){return false}}
f.addEventListener("submit",function(e){e.preventDefault();var n=v("name"),w=v("website"),g=v("github"),d=v("desc"),m=v("email"),x=v("x").replace(/^@/,"");
var bad=!n?"Please add the tool name.":!okUrl(w)?"Please add a full website link starting with https://":(g&&!okUrl(g,1))?"The GitHub link should be a github.com URL.":!d?"Please add a short description.":(m&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(m))?"Please add a valid email.":(x&&!/^[A-Za-z0-9_]{1,15}$/.test(x))?"X handles use letters, numbers and _ only.":"";
if(!bad){var F=fnd();if(!F.a){bad="Please tell us how you found us.";fs.focus()}else if(F.a==="Other"&&!F.o){bad="Please say where you found us.";document.getElementById("foundother").focus()}}er.textContent=bad;if(bad)return;
var body="Tool name: "+n+"\nWebsite: "+w+"\nGitHub: "+(g||"-")+"\nCategory: "+v("category")+"\nPricing: "+v("pricing")+"\nDescription: "+d+"\nMaker email: "+(m||"-")+"\nX: "+(x?"@"+x:"-")+"\n"+(fnd().a?"How I found you: "+fnd().a+(fnd().o?" ("+fnd().o+")":"")+"\n":"");
var mail="mailto:support@agentscouthq.com?subject="+encodeURIComponent("Tool submission: "+n)+"&body="+encodeURIComponent(body);document.getElementById("smail").href=mail;
var btn=f.querySelector("button[type=submit]");btn.disabled=true;btn.textContent="Sending…";
fetch(SUBMIT_URL,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:n,website:w,github:g,category:v("category"),pricing:v("pricing"),desc:d,email:m,x:x,company:v("company"),type:UPD?"update":"new",tool:UPD||"",found:fnd().a,found_other:fnd().o})}).then(function(r){return r.json().catch(function(){return{}}).then(function(j){if(!r.ok||!j.ok)throw new Error(j.error||"Something went wrong.");f.hidden=true;document.getElementById("sdone").hidden=false;})}).catch(function(e){er.innerHTML="";er.appendChild(document.createTextNode((e&&e.message&&e.message!=="Failed to fetch"?e.message:"We couldn't send it right now.")+" "));var a=document.createElement("a");a.href=mail;a.textContent="Send it by email instead";er.appendChild(a);}).finally(function(){btn.disabled=false;btn.textContent=UPD?"Send suggested edit":"Submit for free review";});})})()</script>'''
    body=(f'<div class="crumb"><a href="index.html">AgentScout</a> / Submit a tool</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left">Submit your AI agent tool</h1>'
          '<p class="lede" style="margin-left:0;text-align:left">Listing on AgentScout is free. We review every submission, check the links and write the description ourselves in plain words, so you don\'t need marketing copy.</p>'
          f'{form}<p class="disclose" style="max-width:560px">Submissions go straight to the AgentScout team. Prefer email? <a id="smail" href="mailto:support@agentscouthq.com?subject=Tool%20submission">Send it from your email app instead</a>. After you\'re listed, add a <a href="badges.html">free AgentScout badge</a>.</p></section>{js}')
    ld={"@context":"https://schema.org","@type":"WebPage","name":title,"description":desc,"url":canon}
    open("submit.html","w").write(shell("",title,desc,canon,body,ld)); return canon
NL=('<section id="nlblock" class="nlwrap"><div class="wrap"><div class="nlbox"><div class="nltxt"><h2>Get the best new AI agents, weekly</h2>'
    '<p>One short email with new tools, launches and what\'s worth trying. Free, unsubscribe anytime.</p></div>'
    '<form class="nlgo" action="https://agentscout.beehiiv.com/subscribe" method="get" data-nlform><button class="btn primary" type="submit">Subscribe free</button></form>'
    '</div></div></section>')  # compact card; Beehiiv's form loads in-page only on click (app.js), Oct 18 2026
ASSET_V="202610211555"  # bump when app.js/styles.css change
SKIP={"og.html","outreach-tracker.html"}
def sitewide(t):
    m=mapping(t); bys={x["slug"]:x for x in t}
    for f in glob.glob("**/*.html",recursive=True):
        if os.path.basename(f) in SKIP or f.startswith(("node_modules","app/","preview/")): continue
        s=open(f).read(); o=s
        s=re.sub(r'<section class="nlband".*?</section>\n?',"",s,flags=re.S)  # dark "5 agent tools" strip removed sitewide
        d="/" if f=="404.html" else "../"*f.count("/")
        s=re.sub(r'<a([^>]*?) href="https://github\.com/Clampdown-web/agentscout/issues/new\?[^"]*?[Ss]ubmission[^"]*"(?: target="_blank")?(?: rel="noopener(?: noreferrer)?")?',lambda mm:f'<a{mm.group(1)} href="{d}submit.html"',s)
        s=re.sub(r'(<div class="links"><a href="[^"]*categories/index\.html">Categories</a>)(?!<a href="[^"]*tasks/)',lambda mm:mm.group(1)+f'<a href="{d}tasks/index.html">Tasks</a>',s)
        s=re.sub(r'(<p><a href="[^"]*categories/index\.html">Categories</a>)(?! · <a href="[^"]*tasks/)',lambda mm:mm.group(1)+f' · <a href="{d}tasks/index.html">AI agents by task</a>',s)
        # Nav "Best" goes to the best-of hub
        s=re.sub(r'<a href="[^"]*best/mcp-servers\.html">Best</a>',lambda mm:f'<a href="{d}best/index.html">Best</a>',s)
        # "For you" (role hub) and "Searches" (search hub) in the main nav, right after Best (Oct 18 2026)
        s=re.sub(r'(<a href="([^"]*)best/index\.html">Best</a>)(?!<a href="[^"]*for/index\.html">For you</a>)',lambda mm:mm.group(1)+f'<a href="{mm.group(2)}for/index.html">For you</a><a href="{mm.group(2)}s/index.html">Searches</a>',s)
        # Footer links (scoped to <footer> so body "See also" lines don't satisfy the check, Oct 18 2026):
        # Newsletter archive right after Free tools; Popular searches + AI agents by role right after Free tools
        # (generate.html has no footer Free tools link: after Badges)
        # Paid listings on hold (Oct 18 2026, owner-approved): strip the footer 'Get featured' link + sponsorship mailto and the
        # 'sponsorships' JSON-LD contactType sitewide so no rebuild/daily routine brings them back. Hidden Featured machinery untouched.
        s=re.sub(r'(?: · )?<a [^>]*>Get featured(?: →)?</a>(?: \(<a href="mailto:[^"]*Sponsorship[^"]*">or email</a>\))?','',s)
        s=s.replace('"contactType": "sponsorships and submissions"','"contactType": "submissions and support"')
        fm=re.search(r'<footer\b.*?</footer>',s,re.S)
        if fm:
            fo=fm.group(0); fn=fo
            if 'newsletter.html">Newsletter archive</a>' not in fn: fn=re.sub(r'(<a href="[^"]*free-tools\.html">Free tools</a>)',lambda mm:mm.group(1)+f' · <a href="{d}newsletter.html">Newsletter archive</a>',fn,count=1)
            if 's/index.html">Popular searches</a>' not in fn:
                fn,k=re.subn(r'(<a href="[^"]*free-tools\.html">Free tools</a>)(?= · <a href="[^"]*newsletter\.html">Newsletter archive)',lambda mm:mm.group(1)+f' · <a href="{d}s/index.html">Popular searches</a> · <a href="{d}for/index.html">AI agents by role</a>',fn,count=1)
                if not k: fn=re.sub(r'(<a href="[^"]*badges\.html">Badges for makers</a>)',lambda mm:mm.group(1)+f' · <a href="{d}s/index.html">Popular searches</a> · <a href="{d}for/index.html">AI agents by role</a>',fn,count=1)
            # New tools page (new.html) in every footer, right before Agent news (Oct 18 2026: it was only linked from the homepage)
            if 'new.html">New tools</a>' not in fn: fn=re.sub(r'(<a href="[^"]*news\.html">Agent news</a>)',lambda mm:f'<a href="{d}new.html">New tools</a> · '+mm.group(1),fn,count=1)
            if 'new.html">New tools</a>' not in fn: fn=re.sub(r'(<a href="[^"]*for/index\.html">AI agents by role</a>)',lambda mm:mm.group(1)+f' · <a href="{d}new.html">New tools</a>',fn,count=1)
            # Footers that lack the standard Free tools / Newsletter archive / Agent news links (generate.html) get them in the standard order
            if 'free-tools.html">Free tools</a>' not in fn: fn=re.sub(r'(<a href="[^"]*s/index\.html">Popular searches</a>)',lambda mm:f'<a href="{d}free-tools.html">Free tools</a> · '+mm.group(1),fn,count=1)
            if 'newsletter.html">Newsletter archive</a>' not in fn: fn=re.sub(r'(<a href="[^"]*for/index\.html">AI agents by role</a>)',lambda mm:mm.group(1)+f' · <a href="{d}newsletter.html">Newsletter archive</a>',fn,count=1)
            if 'news.html">Agent news</a>' not in fn: fn=re.sub(r'(<a href="[^"]*new\.html">New tools</a>)',lambda mm:mm.group(1)+f' · <a href="{d}news.html">Agent news</a>',fn,count=1)
            # News archive (news/) in every footer, right after Agent news (Oct 18 2026: archive was only linked from news.html and story pages)
            if 'news/index.html">News archive</a>' not in fn: fn=re.sub(r'(<a href="[^"]*news\.html">Agent news</a>)',lambda mm:mm.group(1)+f' · <a href="{d}news/index.html">News archive</a>',fn,count=1)
            # Image generator link in every footer, right after Badges (generate.html's own footer lacked it; audit Oct 18 2026)
            if 'class="footgen"' not in fn: fn=re.sub(r'(<a href="[^"]*badges\.html">Badges for makers</a>)',lambda mm:mm.group(1)+f' · <a class="footgen" href="{d}generate.html">✨ Free AI Image Generator</a>',fn,count=1)
            if fn!=fo: s=s[:fm.start()]+fn+s[fm.end():]
        # Bot templates (launched Oct 19 2026 PT, owner approved): red flame nav link left of Quiz, footer link before Free tools,
        # homepage strip after the makers strip (data/bt-strip.inc). Sponsor page stays untouched.
        if f!="sponsor.html":
            if 'class="navbt"' not in s.split("</nav>")[0]: s=re.sub(r'(<div class="links">.*?)(<a href="[^"]*quiz\.html">Quiz</a>)',lambda mm:mm.group(1)+f'<a class="navbt" href="{d}bot-templates/">Bot templates</a>'+mm.group(2),s,count=1,flags=re.S)
            # Leaderboard (Oct 21 2026, owner-approved): one nav link right before Bot templates
            if 'class="navlb"' not in s.split("</nav>")[0]: s=re.sub(r'(<div class="links">.*?)(<a class="navbt")',lambda mm:mm.group(1)+f'<a class="navlb" href="{d}leaderboard/">Leaderboard</a>'+mm.group(2),s,count=1,flags=re.S)
            fm2=re.search(r'<footer\b.*?</footer>',s,re.S)
            if fm2 and 'class="navbt"' not in fm2.group(0):
                fn2=re.sub(r'(<a href="[^"]*free-tools\.html">Free tools</a>)',lambda mm:f'<a class="navbt" href="{d}bot-templates/">Bot templates</a> · '+mm.group(1),fm2.group(0),count=1)
                s=s[:fm2.start()]+fn2+s[fm2.end():]
            if f.startswith("tools/") and os.path.exists("data/bt-links.json"):  # related Bot templates on matching tool pages (SEO pass Oct 19 2026)
                s=re.sub(r'<p class="btrel".*?</p>','',s,flags=re.S)
                L=__import__("json").load(open("data/bt-links.json")).get(os.path.basename(f)[:-5])
                if L: s=re.sub(r'(\n\s*</div>\s*<aside class="panel">)',lambda mm:'<p class="btrel" style="margin:0 0 28px;font-size:14px">Bot templates: '+", ".join(f'<a href="../bot-templates/{a}.html">{e(n)}</a> ({e(pl)})' for a,n,pl in L)+' · <a href="../bot-templates/">All Bot templates</a></p>'+mm.group(1),s,count=1)
            if f=="index.html" and os.path.exists("data/bt-strip.inc"):
                s=re.sub(r'<section id="bt-strip".*?</section>','',s,flags=re.S)
                s=s.replace("<!--MAKERS-END-->","<!--MAKERS-END-->"+open("data/bt-strip.inc").read(),1)
        # Free-tools hub in the main nav, right after Image Gen
        if 'free-tools.html">Free tools</a><a href="https://agentscout.beehiiv.com/" data-nl>' not in s: s=re.sub(r'(<a class="navgen" href="[^"]*generate\.html">[^<]*</a>)(?!<a href="[^"]*free-tools\.html")',lambda mm:mm.group(1)+f'<a href="{d}free-tools.html">Free tools</a>',s)
        s=s.replace("form-action 'self'\"","form-action 'self' https://agentscout.beehiiv.com\"")
        s=re.sub(r'<section id="nlblock".*?</section>',lambda mm:NL,s,count=1,flags=re.S)  # refresh older signup markup in place
        if 'id="nlblock"' not in s and "<footer" in s: s=s.replace("<footer",NL+"<footer",1)
        if f.startswith("tools/"):
            x=bys.get(os.path.basename(f)[:-5]); s=re.sub(r'<p class="goodfor".*?</p>','',s)
            ts=tasks_for(x,m) if x else []
            # anchor = end of the action row, with or without the Share button (build_share) inside it
            if ts: s=re.sub(r'(style="display:contents"></span>(?:<span class="sharewrap">.*?</span></span>)?</div>)',lambda mm:mm.group(1)+'<p class="goodfor" style="margin:-12px 0 24px;font-size:14px;color:var(--muted)">Good for: '+", ".join(f'<a href="../tasks/{T[0]}.html">{e(T[1])}</a>' for T in ts[:8])+'</p>',s,count=1,flags=re.S)
        # Anonymous analytics (track.js) on every page, right after app.js
        # Privacy pages + choices in every footer
        s=s.replace('<p><a href="mailto:support@agentscouthq.com">support@agentscouthq.com</a> · ©',f'<p><a href="{d}about.html">About</a> · <a href="{d}privacy.html">Privacy</a> · <a href="{d}privacy.html#privacy-choices" data-consent-open>Privacy choices</a> · <a href="mailto:support@agentscouthq.com">support@agentscouthq.com</a> · ©')
        if "track.js" not in s and "app.js?v=" in s: s=re.sub(r'(<script src="[^"]*?)app\.js\?v=\d+"></script>',lambda mm:mm.group(0)+mm.group(1)+'track.js?v='+ASSET_V+'" defer></script>',s,count=1)
        # Consent manager (consent.js) loads right before track.js so analytics wait for the visitor's choice
        if "consent.js" not in s and "track.js?v=" in s: s=re.sub(r'<script src="([^"]*?)track\.js\?v=\d+" defer></script>',lambda mm:f'<script src="{mm.group(1)}consent.js?v={ASSET_V}" defer></script>'+mm.group(0),s,count=1)
        s=__import__("build_share").apply(f,s,d,ASSET_V)  # Share button + counter (Oct 18 2026)
        s=__import__("ga4").apply(s,f)  # Google Analytics 4 tag + CSP hosts, consent-aware (ga4.py, Oct 19 2026)
        PC='<link rel="preconnect" href="https://agentscout-image.agentscouthq.workers.dev" crossorigin>'  # share counter host (Lighthouse preconnect, Oct 19 2026)
        if PC not in s and "share.js" in s and "</head>" in s: s=s.replace("</head>",PC+"</head>",1)
        s=re.sub(r'(app\.js|styles\.css|track\.js|compare-picker\.js|consent\.js|share\.js|reviews\.js)\?v=\d+',lambda mm:mm.group(1)+"?v="+ASSET_V,s)
        if s!=o: open(f,"w").write(s)

# ---- About + Privacy pages (relative links; canonical from B, so a domain switch only changes B) ----
def _featured_href():
    m=re.search(r'<a href="(https://github\.com/Clampdown-web/agentscout/issues/new\?title=Featured[^"]*)">Get featured</a>',open("data/detail.tpl").read())
    return m.group(1) if m else "mailto:support@agentscouthq.com?subject=Sponsorship%20%2F%20featured%20listing"
H2='style="font-size:19px;margin:32px 0 8px"'
def _page(fn,crumb,title,desc,h1,lede,inner,ld_type="WebPage"):
    canon=B+fn
    body=(f'<div class="crumb"><a href="index.html">AgentScout</a> / {e(crumb)}</div><section style="padding-top:20px;text-align:left;max-width:760px">'
          f'<h1 style="text-align:left">{e(h1)}</h1><p class="lede" style="margin-left:0;text-align:left">{lede}</p>{inner}</section>')
    ld={"@context":"https://schema.org","@graph":[{"@type":ld_type,"name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":crumb,"item":canon}]}]}
    open(fn,"w").write(shell("",title,desc,canon,body,ld)); return canon
def about_page(t):
    n=len(t); nc=len({x["category"] for x in t})
    inner=(f'<h2 {H2}>What AgentScout is</h2><p>AgentScout is a curated directory of <b>{n} AI agents and agent tools</b> in {nc} categories: coding agents, browser and computer use, agent frameworks, MCP servers, voice agents, research, evals, games, crypto and more. Every tool has its own page with a short description we write ourselves, pricing as the maker states it, links and alternatives. It\'s for builders who want parts to build with and for anyone looking for a ready-to-use agent. Browse the <a href="index.html#directory">directory</a>, <a href="categories/index.html">categories</a> or <a href="tasks/index.html">tasks</a>, or take the <a href="quiz.html">Agent Finder quiz</a>.</p>'
      f'<h2 {H2}>How tools are picked</h2><p>New tools are found every day. Our main sources are:</p><ul>'
      '<li><b>GitHub</b>: agent-related topics such as ai-agents, agent-framework, mcp-server, coding-agent and browser-agent.</li>'
      '<li><b>The official MCP registry</b>, keeping well-known publishers and popular repositories.</li>'
      '<li><b>Product Hunt</b> and <b>Hugging Face</b>, for launched products and Spaces.</li>'
      '<li><b>The wider web</b>: Hacker News Show HN launches, news, web searches and community lists.</li>'
      '<li><b>Your submissions</b> through the <a href="submit.html">submit form</a>.</li></ul>'
      '<p>We use other directories and lists only to find names. We never copy their descriptions, screenshots or ratings.</p>'
      '<p>A tool gets in when:</p><ul><li>It\'s clearly about agents: frameworks, coding agents, browser or computer use, MCP servers and gateways, agent memory, sandboxes, evals and observability, voice agents, and business or personal agents.</li>'
      '<li>Open-source projects have at least 500 GitHub stars, were updated in the last six months and aren\'t archived.</li>'
      '<li>The official website works and the tool has a real logo, not a generic placeholder.</li>'
      '<li>It isn\'t already listed under another name, domain or repository.</li></ul>'
      '<p>We leave out tutorials, courses, awesome lists, prompt collections, CAPTCHA solvers and anti-bot tools, trading bots, and general infrastructure with no agent angle. Each description is one sentence written by us after reading the official site or README, and pricing is labeled the way the maker states it.</p>'
      f'<h2 {H2}>How tools are checked</h2><p>The site is rebuilt every day. When a tool is added we confirm that the repository exists and isn\'t archived, that the website loads, and that the logo is real. After that, listings are re-checked: official links, logos and GitHub details such as stars. Every tool page shows the date its link was last checked, and the homepage shows when links were last checked across the directory. If something looks wrong, <a href="mailto:support@agentscouthq.com?subject=Listing%20correction">tell us</a>.</p>'
      f'<h2 {H2}>Submit a tool</h2><p>Listing is free. Use the <a href="submit.html">submit form</a>. We review every submission, check the links and write the listing ourselves, so you don\'t need marketing copy. Once you\'re listed you can add a <a href="badges.html">free AgentScout badge</a>.</p>'
      f'<h2 {H2}>Newsletter</h2><p>One short email a week with new tools, launches and what\'s worth trying. Free, unsubscribe anytime. <a href="https://agentscout.beehiiv.com/" data-nl>Subscribe to the newsletter</a>. You can also follow daily <a href="news.html">agent news</a> on the site.</p>'
      f'<h2 {H2}>The app</h2><p>An AgentScout app for phones and tablets is in testing. It uses the same live directory as this site, with search, saved tools, the quiz, comparisons and the newsletter. It isn\'t in the App Store or Google Play yet; we\'ll announce it here and on X when it is.</p>'
      f'<h2 {H2}>Contact</h2><p>Email <a href="mailto:support@agentscouthq.com">support@agentscouthq.com</a> or find us on X at <a href="https://x.com/AgentScoutHQ" target="_blank" rel="noopener noreferrer">@AgentScoutHQ</a>. See our <a href="privacy.html">privacy policy</a> for how we handle data.</p>')
    return _page("about.html","About","About AgentScout: how AI agent tools are picked and checked",
        f"AgentScout is a curated directory of {n} AI agents and tools. How we find tools, what gets in, how listings are checked daily, and and how to submit a tool.",
        "About AgentScout",f"A curated, link-checked directory of {n} AI agents and agent tools, updated daily.",inner,"AboutPage")
def privacy_page(t):
    li=lambda *xs:"<ul>"+"".join(f"<li>{x}</li>" for x in xs)+"</ul>"
    inner=('<p><b>Effective date:</b> October 19, 2026</p>'
      '<p>This page explains, in plain words, what the AgentScout website and app collect and why. It describes what our code actually does. It isn\'t legal advice, and we don\'t claim certification under any particular privacy law.</p>'
      f'<h2 {H2}>The short version</h2>'+li('No accounts and no ads. We don\'t sell or share data for advertising.','Our own code sets no cookies. If you allow analytics, Google Analytics sets its own cookies (see below).','Our own analytics are anonymous counts (for example "the Cursor page was viewed 40 times today"). They contain no names, emails or device IDs.','Where privacy law requires opt-in, analytics and the newsletter form stay off until you allow them. You can change your mind anytime under <a href="#privacy-choices" data-consent-open>Privacy choices</a>.','Things you save, like favorites and your theme, stay on your device.')+
      f'<h2 id="privacy-choices" {H2}>Your privacy choices</h2><p>We sort what the site and app use into three groups:</p>'+li('<b>Necessary</b> (always on): saved tools, upvotes, light or dark theme and the image generator cooldown. These stay on your device and are never sent to us.','<b>Analytics</b>: the anonymous counts and Google Analytics usage stats described below.','<b>Embedded content</b>: the newsletter sign-up, which is run by Beehiiv and may set Beehiiv\'s own cookies.')+
      '<p>When you first visit, the site asks our server which country (and, in the US, which state) your connection comes from. Cloudflare provides this from your connection; we don\'t store it. If you\'re in the EU or EEA, the UK, Switzerland, Brazil, or a US state with a consumer privacy law (such as California), or if the location can\'t be determined, you\'ll see a banner with <b>Accept all</b>, <b>Reject all</b> and <b>Customize</b>. Nothing in Analytics or Embedded content runs until you choose. If you turn off embedded content, you\'ll see a "Load newsletter form" button in place of the sign-up form.</p>'
      '<p>Everywhere else, you\'ll see a small notice. Anonymous analytics are on by default, and you can opt out with one tap.</p>'
      '<p>Your choice is saved on your device (in your browser\'s local storage on the site, and in the app\'s local storage in the app), so we don\'t ask again. To change it, use <a href="#privacy-choices" data-consent-open>Privacy choices</a> in the footer of any page or on the app\'s About screen. Clearing your browser data resets it.</p>'
      '<p><button type="button" class="btn primary" data-consent-open>Open privacy choices</button></p>'
      f'<h2 {H2}>Anonymous analytics (website and app)</h2><p>To see which pages and tools are useful, the site and app send small event counts to our server, which runs on Cloudflare Workers. The events are: page views, app opens, searches, tool clicks, outbound link clicks (tool page and link type only), button clicks (like submit, quiz, newsletter, compare, generate), quiz completed (the goal you picked), favorites added, tool submitted and image generated.</p>'
      +li('Each event is stored without any visitor ID, cookie or IP address, so events can\'t be linked to each other or to you. We only look at them as totals, for example per day, page, tool or button.','On the website, page views also note the name of the site that linked you here, for example google.com or x.com (only the site name, never the full link), and which of our addresses you visited (agentscouthq.com or the older GitHub address). If you typed the address yourself, it\'s counted as direct.','Search terms are stored as typed text (lowercased, up to 60 characters), so we can count popular searches and see recent ones. Please don\'t type personal information into search.','No cookies and no device or user ID are sent. On the website, a note in your browser\'s session storage makes sure a page is counted once per tab; it\'s deleted when you close the tab.','Your IP address is not stored for analytics. To prevent abuse, the server makes a one-way scrambled code from your IP address, the date and a secret, and counts requests under that code for a short time (at most about 2 hours).','Analytics data is deleted automatically after about 3 to 4 months.')+
      f'<h2 id="google-analytics" {H2}>Google Analytics</h2><p>The website also uses Google Analytics to see anonymous usage stats, such as how many people visit, which pages they read and which sites sent them. It only runs if analytics are allowed under <a href="#privacy-choices" data-consent-open>Privacy choices</a>, and it sets Google Analytics cookies when it does. We turned off Google signals and ad personalization, there are no ads on AgentScout, and we don\'t sell your data. Google Analytics doesn\'t log or store IP addresses. Besides Google Analytics, we keep our own anonymous counter on Cloudflare, described above. You can also block Google Analytics on every site with <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener noreferrer">Google\'s opt-out browser add-on</a>.</p>'
      f'<h2 {H2}>The submit form</h2><p>When you submit a tool, we store what you enter: tool name, website, GitHub link, category, pricing, description and, if you give them, your email and X handle. We use these to review the submission and, if you left an email, to contact you about it. We don\'t store your IP address or browser details with a submission. Submissions are kept for 90 days in Cloudflare\'s storage and then deleted automatically. To limit submissions to 5 per hour, the server keeps a count under a one-way scrambled code made from your IP address, the hour and a secret; it expires after about an hour. If you choose "send it by email instead", the message goes through your own email app to our inbox.</p>'
      f'<h2 {H2}>The image generator</h2><p>Your prompt is sent to our server and on to Cloudflare Workers AI, which creates the image. We don\'t save prompts or images. To keep the free generator fair, a counter tied to your IP address limits use to 5 images per hour and expires after about 2 hours. Your browser or app also remembers when you last generated an image, so it can show a short cooldown.</p>'
      f'<h2 id="reviews" {H2}>Ratings and reviews</h2><p>Each tool page lets you leave a 1 to 5 star rating and, if you like, a short review and a name. We store the stars, the review text, the name you give (optional), the time, and a random visitor ID that your browser creates when you first rate (kept in local storage, used only so each visitor rates a tool once). To stop abuse we also store a salted one-way hash of your IP address, not the address itself; it can\'t be turned back into your IP. Star ratings count right away. Written reviews are read by us first and appear only if approved; rejected reviews are deleted together with their rating. Approved reviews and names are public on the tool page and in our API, so please don\'t include personal details. Reviews come from site visitors and aren\'t verified. To have a rating or review removed, email <a href="mailto:support@agentscouthq.com?subject=Review%20removal">support@agentscouthq.com</a> with the tool name.</p>'
      f'<h2 {H2}>Saved tools and settings</h2><p>Favorites, upvotes and your theme are kept in your browser\'s local storage. They aren\'t sent to us. Clearing your browser data removes them.</p>'
      f'<h2 {H2}>Newsletter</h2><p>The newsletter is run by Beehiiv. When you subscribe, your email address goes to Beehiiv, not to our server, and Beehiiv\'s privacy policy applies. Beehiiv may set its own cookies. The sign-up form only appears if embedded content is allowed. You can unsubscribe from any issue.</p>'
      f'<h2 {H2}>The AgentScout app</h2><p>The app follows the same rules. It asks for your choice on first launch (a full choice screen in the regions listed above, a small notice elsewhere), and you can change it under Privacy choices on the About screen. It keeps these on your device only:</p>'+li('A random install code, created only if analytics are allowed. It\'s used only to tell whether this is the app\'s first open, and it\'s never sent to us. Turning analytics off deletes it.','Your privacy choice, saved tools, theme, a cached copy of the tool list and the image generator cooldown.')+
      '<p>With analytics allowed, it sends the same anonymous events as the website. The submit form and image generator work exactly as described above. The newsletter sign-up loads Beehiiv\'s page inside the app, and only if embedded content is allowed.</p>'
      f'<h2 {H2}>Hosting and other services</h2>'+li('The website is hosted on <b>GitHub Pages</b>. GitHub may log technical data such as IP addresses when it delivers pages; see GitHub\'s privacy statement.','Our server runs on <b>Cloudflare</b> (Workers, Workers AI and storage). Cloudflare handles requests, including your IP address, to deliver them; see Cloudflare\'s privacy policy.','Website fonts load from <b>Google Fonts</b>, so Google receives your IP address when a page loads.','Links to tools take you to other websites, which have their own policies.')+
      f'<h2 {H2}>Your rights and questions</h2><p>To ask about your data, or to have a submission deleted before it expires, email <a href="mailto:support@agentscouthq.com?subject=Privacy%20question">support@agentscouthq.com</a>. Our own analytics can\'t be linked back to you, so there\'s nothing personal there to look up or delete. Google Analytics only shows us combined, anonymous reports. AgentScout isn\'t aimed at children.</p>'
      f'<h2 {H2}>Changes</h2><p>If what we collect changes, we\'ll update this page and the effective date at the top. See also <a href="about.html">About AgentScout</a>.</p>')
    return _page("privacy.html","Privacy","Privacy policy · AgentScout","How AgentScout handles data: anonymous analytics (consent where required), no cookies of our own, the submit form, image generator, newsletter and your choices.",
        "Privacy policy","What the AgentScout website and app collect, why, and how to change your choices.",inner)
