"""Search landing pages (s/) and job-role pages (for/), Oct 18 2026. Called from build_extras.build().
Every list is built from tools.json at build time (category, pricing as the maker states it, use cases and task matching
from build_tasks). Ranking uses only directory data: tracked GitHub stars, then listing maturity. No invented scores."""
import os,re,glob,collections
import build_extras as X, build_tasks as T, build_best as BB
B=X.B; e=X.e
CAP=lambda s:s[:1].upper()+s[1:]
OS={"Open source","Open source + cloud"}
FREE=OS|{"Freemium","Free","Open weights","Open standard"}
def isfree(x): return x["pricing"] in FREE or bool(X.FREE_RE.search(x.get("pricing_detail") or ""))
def live(x): return BB.live(x)
def rank(items):
    return sorted(items,key=lambda x:(x.get("github_stars") is None,-(x.get("github_stars") or 0),BB.MAT(x),x["name"].lower()))
D=lambda x:x["name"]+" "+x["description"]
UC=lambda x,u:u in x.get("use_cases",[])
# Tighter checks on top of build_tasks matching, so broad keyword hits (e.g. "supports", "leaderboard") don't leak in
REFINE={
 "customer-support":lambda x:bool(re.search(r"customer|helpdesk|help desk|ticket|support (team|agent|inbox)",D(x),re.I)),
 "sales-outreach":lambda x:(bool(re.search(r"\bsales\b|outreach|\bSDR\b|prospect|\bCRM\b|\bleads?\b(?!erboard)",D(x),re.I)) or UC(x,"sales & support")) and "eaderboard" not in x["name"],
 "monitoring-agents":lambda x:x["category"]=="evals & observability" or bool(re.search(r"observab|tracing|traces",D(x),re.I)),
 "evaluating-agents":lambda x:x["category"]=="evals & observability" or UC(x,"monitor & evaluate agents"),
 "research":lambda x:x["category"]=="research" or UC(x,"research the web"),
 "searching-the-web":lambda x:bool(re.search(r"search API|web search|search engine|SERP",D(x),re.I)),
 "automating-workflows":lambda x:x["category"]=="no-code builders" or UC(x,"automate workflows"),
 "computer-use":lambda x:x["category"]=="browser/computer use" or UC(x,"control a computer") or bool(re.search(r"computer[- ]use",D(x),re.I)),
 "running-code-safely":lambda x:UC(x,"run code safely") or bool(re.search(r"sandbox|microVM|isolated",D(x),re.I)),
 "testing-apps":lambda x:bool(re.search(r"(?<!back)\btest(s|ing)?\b|\bQA\b|\bE2E\b|end-to-end",x["description"],re.I)) and x["category"]!="crypto",
 "agent-memory":lambda x:UC(x,"give agents memory") or bool(re.search(r"\bmemory\b",D(x),re.I)),
}
def tm(m):
    """build_tasks mapping with REFINE applied: {task: (T, items)}"""
    return {k:(Tk,[x for x in it if REFINE.get(k,lambda x:True)(x)]) for k,(Tk,it) in m.items()}
# slug, h1, short query label, filter(x,inT), intro, related (task slug, best slug or None)
S=[
("free-ai-coding-agents","Free AI coding agents with a free plan","free AI coding agents",lambda x,k:x["category"]=="coding" and isfree(x) and x["pricing"] not in OS,"Commercial AI coding agents, editors and CLIs with a free plan or free tier, so you can try them without paying. Open-source coding agents have their own list.","writing-code","ai-coding-agents"),
("open-source-ai-coding-agents","Open-source AI coding agents","open-source AI coding agents",lambda x,k:x["category"]=="coding" and x["pricing"] in OS,"Coding agents whose source code is public, so you can read it, self-host it and bring your own model API key.","writing-code","ai-coding-agents"),
("terminal-ai-coding-agents","AI coding agents for the terminal (CLI)","terminal AI coding agents",lambda x,k:x["category"]=="coding" and k("terminal-coding"),"Coding agents that run in your terminal: they read files, run commands and propose changes from a prompt.","terminal-coding","ai-coding-agents"),
# s/ai-code-review-tools removed Oct 18 2026: same tools as tasks/reviewing-pull-requests (redirect in redirects.json)
# Oct 20 2026: s/free-browser-automation-agents merged into this page (owner-approved; redirect in redirects.json).
# The list is the union of the top 25 open-source and top 25 free browser tools (see MERGED below); every count is computed.
("open-source-browser-agents","Free & open-source browser agents","free and open-source browser agents",lambda x,k:(x["category"]=="browser/computer use" or k("browsing-the-web")) and isfree(x),"Open-source libraries, MCP servers, headless browsers and agents that drive a real browser, plus free browser automation tools with a free plan.","browsing-the-web","ai-browser-agents"),
("computer-use-agents","AI computer-use agents","computer-use agents",lambda x,k:k("computer-use"),"Agents that look at the screen and use the mouse and keyboard to work across desktop apps and websites.","computer-use","ai-browser-agents"),
("open-source-ai-agent-frameworks","Open-source AI agent frameworks","open-source AI agent frameworks",lambda x,k:x["category"]=="frameworks" and x["pricing"] in OS,"Frameworks and SDKs for building your own agents, with public source code you can inspect and extend.","building-ai-agents","ai-agent-frameworks"),
("python-ai-agent-frameworks","Python AI agent frameworks","Python AI agent frameworks",lambda x,k:x["category"]=="frameworks" and re.search(r"\bPython\b",x["description"]+" "+x["name"]),"Agent frameworks and SDKs whose listings say they are built for Python.","building-ai-agents","ai-agent-frameworks"),
("typescript-ai-agent-frameworks","TypeScript and JavaScript AI agent frameworks","TypeScript AI agent frameworks",lambda x,k:x["category"]=="frameworks" and re.search(r"TypeScript|JavaScript|\bNode(\.js)?\b|\bJS\b",x["description"]+" "+x["name"]),"Agent frameworks and SDKs for TypeScript, JavaScript and Node.js developers.","building-ai-agents","ai-agent-frameworks"),
("multi-agent-frameworks","Multi-agent frameworks","multi-agent frameworks",lambda x,k:k("multi-agent-systems") and x["audience"]=="builders","Frameworks for teams of agents that split work, hand off tasks and check each other's output.","multi-agent-systems","ai-agent-frameworks"),
# Oct 20 2026: long-tail "MCP servers for <app>" pages (owner's free-traffic push). Strict filters: MCP listing + named app/service in the listing text.
("figma-and-design-mcp-servers","MCP servers for Figma, Canva and design tools","Figma and design MCP servers",lambda x,k:(x["category"]=="MCP servers" or re.search(r"\bMCP\b",x["name"])) and re.search(r"Figma|Canva|Webflow|Penpot|Framer|design[- ]system|design assets|\bdesigns\b",D(x)),"MCP servers that connect Claude Code, Cursor and other AI agents to Figma, Canva, Webflow and other design tools, so they can read layouts, edit designs and turn them into code.","connecting-tools-mcp","open-source-mcp-servers"),
("cloud-and-devops-mcp-servers","MCP servers for AWS, Azure, Cloudflare, Kubernetes and Vercel","cloud and DevOps MCP servers",lambda x,k:(x["category"]=="MCP servers" or re.search(r"\bMCP\b",x["name"])) and re.search(r"\bAWS\b|Azure|Cloudflare|Kubernetes|Google Cloud|Cloud Run|Vercel|Terraform|Netlify",D(x)),"Official and open-source MCP servers that let AI agents work with cloud platforms and DevOps tools: AWS, Azure, Google Cloud, Cloudflare, Kubernetes, Terraform and Vercel.","connecting-tools-mcp","open-source-mcp-servers"),
("web-search-mcp-servers","Web search MCP servers for AI agents","web search MCP servers",lambda x,k:(x["category"]=="MCP servers" or re.search(r"\bMCP\b",x["name"])) and re.search(r"web search|search API|search engine|Brave Search|SearXNG",D(x),re.I) and not re.search(r"\bSEO\b|rank-tracking",D(x)),"MCP servers that give Claude, Cursor, Codex and other AI agents live web search, so they can look things up and cite sources instead of guessing.","searching-the-web","open-source-mcp-servers"),
("free-mcp-servers","Free MCP servers","free MCP servers",lambda x,k:x["category"]=="MCP servers" and isfree(x) and k("connecting-tools-mcp"),"Model Context Protocol servers you can use for free, connecting Claude, Cursor, Codex and other MCP clients to your tools and data.","connecting-tools-mcp","open-source-mcp-servers"),
# s/database-mcp-servers removed Oct 18 2026: same tools as tasks/databases (redirect in redirects.json)
# s/ai-agent-memory-tools removed Oct 18 2026: duplicated categories/memory-rag + tasks/agent-memory (redirect in redirects.json)
("ai-code-sandboxes","Sandboxes for AI agents to run code","AI code sandboxes",lambda x,k:k("running-code-safely"),"Sandboxes and isolated runtimes where agents can run code and tools away from your machine and data.","running-code-safely",None),
("open-source-llm-observability-tools","Open-source LLM observability and eval tools","open-source LLM observability",lambda x,k:x["category"]=="evals & observability" and x["pricing"] in OS,"Open-source tracing, evaluation and monitoring tools for LLM apps and agents that you can self-host.","monitoring-agents","ai-agent-observability-tools"),
("open-source-voice-ai-agents","Open-source voice AI agent frameworks","open-source voice AI agents",lambda x,k:x["category"]=="voice" and x["pricing"] in OS,"Open-source frameworks and tools for building voice agents that listen, think and talk in real time.","building-voice-agents","ai-voice-agent-platforms"),
# s/ai-phone-call-agents removed Oct 18 2026: same tools as tasks/phone-calls (redirect in redirects.json)
("free-no-code-ai-agent-builders","Free no-code AI agent builders","free no-code AI agent builders",lambda x,k:x["category"] in ("no-code builders","app builders") and isfree(x),"Visual and prompt-based builders for making agents and apps without code, with a free plan or open-source edition.","building-apps-without-code","no-code-ai-agent-builders"),
("open-source-workflow-automation-tools","Open-source AI workflow automation tools","open-source workflow automation",lambda x,k:k("automating-workflows") and x["pricing"] in OS,"Open-source platforms for chaining apps, triggers and AI steps into workflows you can self-host.","automating-workflows","no-code-ai-agent-builders"),
("open-source-ai-research-agents","Open-source AI research agents","open-source AI research agents",lambda x,k:x["category"]=="research" and x["pricing"] in OS,"Open-source deep-research agents that search many sources and write up a cited answer or report.","research",None),
("ai-research-assistants","AI research assistants (ready to use)","AI research assistants",lambda x,k:k("research") and x["audience"]=="ready to use","Ready-to-use research assistants that search, read and summarize sources for you, no setup required.","research",None),
("web-search-apis-for-ai-agents","Web search APIs for AI agents","web search APIs for AI agents",lambda x,k:k("searching-the-web"),"Search APIs and engines built for agents and LLM apps, returning clean results a model can use directly.","searching-the-web",None),
# s/ai-web-scraping-tools removed Oct 18 2026: same tools as tasks/web-scraping (redirect in redirects.json)
# s/local-ai-agents removed Oct 18 2026: same tools as tasks/running-agents-locally (redirect in redirects.json)
("open-source-personal-ai-assistants","Open-source personal AI assistants","open-source personal AI assistants",lambda x,k:(x["category"]=="personal agents" or k("personal-assistants")) and x["pricing"] in OS,"Personal assistants and always-on agents with public source code you can run and customize yourself.","personal-assistants","personal-ai-agents"),
# s/ai-agents-for-slack-telegram-whatsapp removed Oct 18 2026: same tools as tasks/chat-apps (redirect in redirects.json)
("ai-customer-support-agents","AI customer support agents","AI customer support agents",lambda x,k:k("customer-support"),"Agents that answer customer questions, resolve tickets and hand off to a person when needed.","customer-support","ai-business-agents"),
# s/ai-sales-agents removed Oct 18 2026: same tools as tasks/sales-outreach (redirect in redirects.json)
# s/ai-marketing-agents removed Oct 18 2026: same tools as tasks/marketing (redirect in redirects.json)
("open-source-crypto-ai-agents","Open-source crypto AI agents","open-source crypto AI agents",lambda x,k:x["category"]=="crypto" and x["pricing"] in OS,"Open-source agent kits, MCP servers and tools for wallets, on-chain data and DeFi. Not financial advice.","crypto-and-wallets","crypto-ai-agents"),
# s/ai-trading-agents removed Oct 18 2026: same tools as tasks/trading (redirect in redirects.json)
# s/ai-security-testing-tools removed Oct 18 2026: same tools as tasks/security-testing (redirect in redirects.json)
# s/ai-agents-for-spreadsheets-and-slides removed Oct 18 2026: same tools as tasks/spreadsheets-and-slides (redirect in redirects.json)
# s/ai-video-agents removed Oct 18 2026: same tools as tasks/making-videos (redirect in redirects.json)
# s/ai-sre-agents removed Oct 18 2026: same tools as tasks/devops-and-incidents (redirect in redirects.json)
("enterprise-ai-agent-platforms","Enterprise AI agent platforms and AI employees","enterprise AI agent platforms",lambda x,k:x["category"]=="business agents" and (x["pricing"]=="Enterprise" or re.search(r"\benterprise",x["name"]+" "+x["description"],re.I)) and re.search(r"platform|AI employee|workforce|AI workers|assistant|workspace",x["description"],re.I),"Platforms for running AI agents and AI employees across a large organization's operations, IT, HR and business systems, mostly sold on enterprise plans.","business-automation","ai-business-agents"),
("ai-game-masters-and-tabletop-rpg-tools","AI game masters and tabletop RPG tools","AI game masters",lambda x,k:x["category"]=="games" and re.search(r"tabletop|dungeon|\bRPGs?\b|game master|D&D",x["name"]+" "+x["description"],re.I),"AI game masters, narrators and map makers for D&D-style tabletop RPGs and story adventures, solo or with a group.","games",None),
("defi-ai-agents","DeFi AI agents","DeFi AI agents",lambda x,k:x["category"]=="crypto" and re.search(r"\bDeFi\b|\byield\b|on-chain capital",x["description"]) and not re.search(r"vulnerab|audit|security",x["description"],re.I),"Agents and SDKs that swap, bridge, lend and manage yield across DeFi protocols. DeFi is risky and nothing here is financial advice.","crypto-and-wallets","crypto-ai-agents"),
("ai-crypto-investing-agents","AI investing and portfolio agents for crypto","AI crypto investing agents",lambda x,k:x["category"]=="crypto" and re.search(r"\binvest(?!igat)|portfolio|hedge-fund|capital strategies|yield vaults",x["description"],re.I),"Agents that build portfolios, run strategies or vaults, or follow other investors' moves. Investing is risky and nothing here is financial advice.","trading","crypto-ai-agents"),
("web3-ai-agent-platforms","Web3 AI agent platforms and networks","Web3 AI agent platforms",lambda x,k:x["category"]=="crypto" and re.search(r"tokeni[sz]ed AI agents|co-own|Agentverse|coordinate work on-chain|launch DeFi agents|agent operating system|Web3-native AI agents",x["description"],re.I),"Networks, launchpads and agent operating systems for building, launching and co-owning on-chain AI agents.","crypto-and-wallets","crypto-ai-agents"),
("openclaw-and-hermes-agent-hosting","OpenClaw and Hermes agents: hosting and tools","OpenClaw and Hermes agent tools",lambda x,k:x["category"] in ("personal agents","frameworks") and re.search(r"OpenClaw|Hermes",x["name"]+" "+x["description"]),"The open-source OpenClaw and Hermes agents, plus hosted services, apps and dashboards for keeping them running.","personal-assistants","personal-ai-agents"),
]
# role slug, name (plural noun), h1 stem, intro, [(section heading, task slug)], free tools [(href,label)], search slugs
R=[
("developers","developers","AI agents for developers","Coding agents, review bots, docs servers and sandboxes that help software developers ship faster.",
 [("Write and edit code","writing-code"),("Work in the terminal","terminal-coding"),("Review pull requests","reviewing-pull-requests"),("Give agents current docs","coding-docs"),("Test your app","testing-apps"),("Run several coding agents at once","parallel-coding-agents")],
 [("agent-setup-generator","Agent setup generator (CLAUDE.md, AGENTS.md, Cursor rules)"),("token-counter","Token counter")],["free-ai-coding-agents","terminal-ai-coding-agents","ai-code-sandboxes","free-mcp-servers"]),
("ai-engineers","AI engineers","AI agent tools for AI engineers","Frameworks, memory, MCP, evals and observability for engineers who build and run their own agents.",
 [("Build agents","building-ai-agents"),("Multi-agent systems","multi-agent-systems"),("Memory","agent-memory"),("Build MCP servers","building-mcp-servers"),("Evaluate agents","evaluating-agents"),("Monitor in production","monitoring-agents"),("Deploy and host","deploying-agents")],
 [("ai-cost-calculator","AI API cost calculator"),("agent-setup-generator","Agent setup generator")],["open-source-ai-agent-frameworks","python-ai-agent-frameworks","typescript-ai-agent-frameworks","open-source-llm-observability-tools","free-mcp-servers","open-source-browser-agents","computer-use-agents"]),
("marketers","marketers","AI agents for marketers","Agents for campaigns, social media, SEO data, email, images and video, so a small marketing team can do more.",
 [("Marketing and go-to-market","marketing"),("Email","writing-emails"),("Images and design","making-images-and-design"),("Video","making-videos"),("Research","research"),("Automate the busywork","automating-workflows")],
 [("prompt-builder","Prompt builder"),("../generate","Free AI image generator")],["ai-research-assistants"]),
("sales-teams","sales teams","AI agents for sales teams","Agents that find and research leads, write outreach, handle calls and keep the CRM up to date.",
 [("Sales outreach","sales-outreach"),("Email","writing-emails"),("Phone calls","phone-calls"),("Chat apps","chat-apps"),("Data and reporting","data-analysis")],
 [("prompt-builder","Prompt builder")],[]),
("customer-support-teams","customer support teams","AI agents for customer support teams","Agents that answer customers, resolve tickets, take calls and search your knowledge base.",
 [("Customer support","customer-support"),("Phone calls","phone-calls"),("Chat apps","chat-apps"),("Search your documents","documents"),("Email","writing-emails")],
 [("prompt-builder","Prompt builder"),("agent-setup-generator","Agent setup generator")],["ai-customer-support-agents"]),
("designers","designers","AI tools for designers","Design agents and AI tools for UI, branding, social graphics, vectors and 3D, including MCP servers that let AI agents work inside Figma, Canva and Penpot.",
 [('Design agents', 'making-images-and-design'), ('UI design and mockups', 'ui-design-and-mockups'), ('Logos and brand kits', 'logo-and-brand-design'), ('Social posts and ad creatives', 'social-posts-and-ad-creatives'), ('Vectorizing images', 'vectorizing-images'), ('Text and image to 3D', 'text-to-3d')],
 [('../generate', 'Free AI image generator'), ('prompt-builder', 'Prompt builder')],[]),
("artists","artists","AI tools for artists","Tools that keep the artist in control: painting assistants, private style models, open-source generators you run yourself, 3D from concept art, upscaling, and Glaze to protect your work.",
 [('Illustration and concept art', 'illustration-and-concept-art'), ('Open-source image generation', 'open-source-image-generation'), ('Image and design agents', 'making-images-and-design'), ('Text and image to 3D', 'text-to-3d'), ('Vectorizing images', 'vectorizing-images'), ('Upscaling and restoring', 'upscaling-and-restoring-photos')],
 [('../generate', 'Free AI image generator'), ('prompt-builder', 'Prompt builder')],[]),
("photographers","photographers","AI tools for photographers","AI that gives photographers their time back: culling, editing in your own style, portrait retouching, upscaling, background removal, product shots, headshots and private photo libraries.",
 [('Photo culling', 'photo-culling'), ('Editing in your style', 'photo-editing-in-your-style'), ('Portrait retouching', 'portrait-retouching'), ('Upscaling and restoring', 'upscaling-and-restoring-photos'), ('Background removal', 'background-removal'), ('Product photography', 'product-photography'), ('AI headshots', 'ai-headshots'), ('Organizing your library', 'organizing-photos'), ('Real estate and architecture', 'architecture-and-real-estate-visuals')],
 [('prompt-builder', 'Prompt builder')],[]),
("filmmakers","filmmakers","AI tools for filmmakers","AI for every stage of a film or series: script breakdowns and storyboards, previs and virtual production, rough cuts, VFX, subtitles, dubbing and sound.",
 [("Storyboarding and previs","storyboarding"),("Rough cuts","rough-cuts"),("VFX and compositing","vfx"),("Video post-production","video-post-production"),("Audio post-production","audio-post-production"),("Dubbing and lip sync","dubbing"),("Scoring and soundtracks","scoring")],
 [("prompt-builder","Prompt builder")],[]),
("video-editors","video editors","AI tools for video editors","Assistant-editor agents, rough-cut and multicam tools, subtitles, color, upscaling, VFX and dialogue cleanup that fit into Premiere, Resolve, Avid and Final Cut.",
 [("Rough cuts","rough-cuts"),("Video post-production","video-post-production"),("Subtitles and captions","subtitles"),("VFX and compositing","vfx"),("Dialogue cleanup","dialogue-cleanup"),("Dubbing and lip sync","dubbing")],
 [("prompt-builder","Prompt builder")],[]),
("musicians-producers","musicians and producers","AI tools for musicians and producers","Song and score generators, vocal synthesis and tuning, stem splitters, and AI mixing and mastering assistants for making and finishing music.",
 [("Music mixing and mastering","music-mixing-mastering"),("Stem separation","stem-separation"),("Scoring and soundtracks","scoring")],
 [("token-counter","Token counter")],[]),
("researchers","researchers","AI agents for researchers","Research agents, paper readers, search APIs and scrapers that find, read and cite sources for you.",
 [("Research","research"),("Read scientific papers","reading-papers"),("Web search","searching-the-web"),("Scrape websites","web-scraping"),("Work with documents","documents"),("Analyze data","data-analysis")],
 [("token-counter","Token counter"),("prompt-builder","Prompt builder")],["ai-research-assistants","open-source-ai-research-agents","web-search-apis-for-ai-agents"]),
("data-analysts","data analysts","AI agents for data analysts","Agents that query databases, clean and chart data, and work inside spreadsheets.",
 [("Data analysis","data-analysis"),("Databases","databases"),("Spreadsheets and slides","spreadsheets-and-slides"),("Scrape data from websites","web-scraping")],
 [("ai-cost-calculator","AI API cost calculator")],[]),
("crypto-traders","crypto traders","AI agents for crypto traders","Trading copilots, wallet and on-chain tools, and smart-contract checkers. Trading is risky and nothing here is financial advice.",
 [("Trading","trading"),("Crypto and wallets","crypto-and-wallets"),("Smart contract security","smart-contract-security"),("Agent payments","agent-payments")],
 [("token-counter","Token counter"),("prompt-builder","Prompt builder")],["open-source-crypto-ai-agents","defi-ai-agents","ai-crypto-investing-agents","web3-ai-agent-platforms"]),
("founders","founders and small businesses","AI agents for founders and small businesses","Ready-made agents for operations, support, marketing and building your first app, so a small team can cover more ground.",
 [("Business operations","business-automation"),("Automate workflows","automating-workflows"),("Build apps without code","building-apps-without-code"),("Customer support","customer-support"),("Marketing","marketing"),("Personal assistants","personal-assistants")],
 [("ai-cost-calculator","AI API cost calculator"),("prompt-builder","Prompt builder")],["free-no-code-ai-agent-builders","ai-customer-support-agents","open-source-browser-agents"]),
("devops-engineers","DevOps and SRE engineers","AI agents for DevOps and SRE engineers","AI SRE agents, observability, sandboxes and deployment tools for keeping systems and agents running.",
 [("Incidents and infrastructure","devops-and-incidents"),("Monitor agents in production","monitoring-agents"),("Deploy and host agents","deploying-agents"),("Run code safely","running-code-safely"),("Agent security","agent-security")],
 [("agent-setup-generator","Agent setup generator")],["ai-code-sandboxes","open-source-llm-observability-tools"]),
("security-engineers","security engineers","AI agents for security engineers","Pentest agents, guardrails, identity and sandboxing tools for securing apps and the agents that touch them.",
 [("Security testing","security-testing"),("Agent security and guardrails","agent-security"),("Smart contract security","smart-contract-security"),("Agent identity and logins","agent-identity"),("Sandboxes","running-code-safely")],
 [("agent-setup-generator","Agent setup generator (guardrail rules in CLAUDE.md, AGENTS.md)")],["ai-code-sandboxes"]),
("game-developers","game developers","AI tools for game developers","AI game makers, NPC engines, image and voice tools for building games.",
 [("Concept art","illustration-and-concept-art"),("3D assets","text-to-3d"),("Voice","building-voice-agents")],
 [("../generate","Free AI image generator")],["open-source-voice-ai-agents"]),
("content-creators","content creators","AI agents for content creators","Video, image and social tools, plus research helpers, for people who publish online.",
 [("Video","making-videos"),("Images and design","making-images-and-design"),("Marketing and social","marketing"),("Research","research")],
 [("prompt-builder","Prompt builder"),("../generate","Free AI image generator")],[]),
 # Batch (i), Oct 18 2026: more roles (published only with >=10 tools across their sections)
 ("qa-engineers","QA engineers","AI agents for QA engineers","Testing agents, review bots and security scanners that help QA engineers find bugs before users do.",
 [("Test your app","testing-apps"),("Review pull requests","reviewing-pull-requests"),("Security testing","security-testing"),("Evaluate AI features","evaluating-agents")],
 [("prompt-builder","Prompt builder")],[]),
 ("data-engineers","data engineers","AI agents for data engineers","Database MCP servers, scrapers and workflow tools that help data engineers move, query and clean data with agents.",
 [("Databases","databases"),("Data analysis","data-analysis"),("Scrape websites","web-scraping"),("Pipelines and workflows","automating-workflows"),("Documents and RAG","documents")],
 [("ai-cost-calculator","AI API cost calculator"),("token-counter","Token counter")],["open-source-workflow-automation-tools"]),
 ("product-managers","product managers","AI agents for product managers","Research assistants, data tools and no-code builders that help product managers learn faster and prototype ideas.",
 [("Research","research"),("Analyze data","data-analysis"),("Prototype without code","building-apps-without-code"),("Slides and docs","spreadsheets-and-slides"),("Understand customers","customer-support")],
 [("prompt-builder","Prompt builder")],["ai-research-assistants","free-no-code-ai-agent-builders"]),
 ("students","students","AI agents for students","Research assistants, paper readers and document tools that help students find sources, read faster and keep track of their work.",
 [("Research","research"),("Read scientific papers","reading-papers"),("Work with documents","documents"),("Personal assistants","personal-assistants")],
 [("token-counter","Token counter"),("prompt-builder","Prompt builder")],["ai-research-assistants","open-source-ai-research-agents"]),
 ("operations-teams","operations teams","AI agents for operations teams","Ready-made business agents, workflow automation and office tools that take repetitive operations work off your team's plate.",
 [("Business operations","business-automation"),("Automate workflows","automating-workflows"),("Spreadsheets and slides","spreadsheets-and-slides"),("Email","writing-emails"),("Chat apps","chat-apps")],
 [("ai-cost-calculator","AI API cost calculator")],["open-source-workflow-automation-tools"]),
 ("startup-ctos","startup CTOs","AI agents for startup CTOs","Coding agents, agent infrastructure, monitoring and security tools for CTOs deciding what their small team builds and buys.",
 [("Run several coding agents at once","parallel-coding-agents"),("Build agents","building-ai-agents"),("Deploy and host agents","deploying-agents"),("Monitor in production","monitoring-agents"),("Agent security","agent-security")],
 [("ai-cost-calculator","AI API cost calculator"),("agent-setup-generator","Agent setup generator")],["open-source-ai-agent-frameworks","open-source-llm-observability-tools","ai-code-sandboxes"]),
 ("agencies","agencies","AI agents for agencies","Marketing, design, video and no-code tools that help agencies deliver more client work with the same team.",
 [("Marketing","marketing"),("Images and design","making-images-and-design"),("Video","making-videos"),("Automate client workflows","automating-workflows"),("Build apps without code","building-apps-without-code")],
 [("prompt-builder","Prompt builder"),("../generate","Free AI image generator")],["free-no-code-ai-agent-builders"]),
 ("open-source-maintainers","open-source maintainers","AI agents for open-source maintainers","Review bots, docs servers, testing and security agents that help maintainers keep up with issues and pull requests.",
 [("Review pull requests","reviewing-pull-requests"),("Write and fix code","writing-code"),("Keep docs current for agents","coding-docs"),("Test changes","testing-apps"),("Security testing","security-testing")],
 [("agent-setup-generator","Agent setup generator (AGENTS.md, CLAUDE.md)"),("llms-txt-generator","llms.txt generator")],["open-source-ai-coding-agents"]),
 ("mcp-developers","MCP developers","AI tools for MCP developers","SDKs, gateways, registries and identity tools for developers building and running Model Context Protocol servers.",
 [("Build MCP servers","building-mcp-servers"),("Connect tools with MCP","connecting-tools-mcp"),("Agent identity and logins","agent-identity"),("Run code safely","running-code-safely")],
 [("mcp-config-builder","MCP config builder"),("tool-schema-builder","Tool schema builder")],["free-mcp-servers"]),
 ("automation-engineers","automation engineers","AI agents for automation engineers","Workflow platforms, browser and computer-use agents and scrapers for engineers who automate repetitive work.",
 [("Automate workflows","automating-workflows"),("Browse the web","browsing-the-web"),("Control a computer","computer-use"),("Scrape websites","web-scraping")],
 [("tool-schema-builder","Tool schema builder"),("ai-cost-calculator","AI API cost calculator")],["open-source-workflow-automation-tools","open-source-browser-agents","computer-use-agents"]),
 ("ecommerce-teams","e-commerce teams","AI agents for e-commerce teams","Support, marketing, phone and payment agents for teams running an online store.",
 [("Customer support","customer-support"),("Marketing","marketing"),("Phone calls","phone-calls"),("Agent payments and checkout","agent-payments")],
 [("prompt-builder","Prompt builder")],["ai-customer-support-agents"])
]
def ftl(h,d="../"):
    if h.startswith("../"): return f'{d}{h[3:]}.html'
    return f'{d}free-tools/{h}.html'
def mini(x):
    gs=f' · ★ {x["github_stars"]:,}' if x.get("github_stars") is not None else ""
    return f'<li style="margin:0 0 10px"><a href="../tools/{x["slug"]}.html" style="display:inline-flex;align-items:center;gap:8px;vertical-align:middle;max-width:100%">{X.ico(x,"../","sm").replace('width="40" height="40"','width="24" height="24"')}<b>{e(x["name"])}</b></a> <span class="b" style="font-size:12px">{e(x["pricing"])}</span><br><span style="color:var(--muted);font-size:14px">{e(x["description"])}</span><span class="muted" style="font-size:12.5px">{gs}</span></li>'
DATA={}
# ---- Modifier /s/ pages (TAAFT item 7, Oct 18 2026): "<modifier> <target>", strict gate, capped ----
MOD_CAP=20; MOD_MIN=8
MODS=[("open-source","Open-source",lambda x:x["pricing"] in OS,"with public source code you can read, self-host and extend"),
      ("free","Free",lambda x:isfree(x),"that you can use without paying: open-source projects plus tools with a free plan"),
      ("self-hosted","Self-hosted",lambda x:x["pricing"] in OS and x["audience"]!="builders","that are ready to use and open source, so you can run them on your own machine or server"),
      ("python","Python",lambda x:bool(re.search(r"\bPython\b",D(x))),"whose listings say they are built for Python"),
      ("typescript","TypeScript",lambda x:bool(re.search(r"TypeScript|JavaScript|\bNode(\.js)?\b",D(x))),"whose listings say they are built for TypeScript, JavaScript or Node.js"),
      ("mcp","MCP-ready",lambda x:bool(re.search(r"\bMCP\b|Model Context Protocol",D(x))) and x["category"]!="MCP servers","that work with the Model Context Protocol (MCP), so Claude, Cursor and other MCP clients can use them")]
# target key, plural noun, filter(x,k), task slug for related links
TARGETS=[("ai-sre-agents","AI SRE agents",lambda x,k:k("devops-and-incidents"),"devops-and-incidents"),
 ("ai-research-agents","AI research agents",lambda x,k:k("research"),"research"),
 ("ai-browser-agents","AI browser agents",lambda x,k:k("browsing-the-web"),"browsing-the-web"),
 ("computer-use-agents","computer-use agents",lambda x,k:k("computer-use"),"computer-use"),
 ("ai-workflow-automation-tools","AI workflow automation tools",lambda x,k:k("automating-workflows"),"automating-workflows"),
 ("ai-agent-evaluation-tools","AI agent evaluation tools",lambda x,k:k("evaluating-agents"),"evaluating-agents"),
 ("ai-agent-monitoring-tools","AI agent monitoring tools",lambda x,k:k("monitoring-agents"),"monitoring-agents"),
 ("ai-agent-security-tools","AI agent security tools",lambda x,k:k("agent-security"),"agent-security"),
 ("ai-agent-sandboxes","AI agent sandboxes",lambda x,k:k("running-code-safely"),"running-code-safely"),
 ("ai-voice-agents","AI voice agents",lambda x,k:k("building-voice-agents"),"building-voice-agents"),
 ("multi-agent-frameworks","multi-agent frameworks",lambda x,k:k("multi-agent-systems"),"multi-agent-systems"),
 ("ai-agent-frameworks","AI agent frameworks",lambda x,k:x["category"]=="frameworks","building-ai-agents"),
 ("mcp-servers","MCP servers",lambda x,k:x["category"]=="MCP servers" and k("connecting-tools-mcp"),"connecting-tools-mcp"),
 ("mcp-servers-for-databases","MCP servers for databases",lambda x,k:k("databases"),"databases"),
 ("ai-coding-agents","AI coding agents",lambda x,k:x["category"]=="coding","writing-code"),
 ("ai-code-review-tools","AI code review tools",lambda x,k:k("reviewing-pull-requests"),"reviewing-pull-requests"),
 ("ai-testing-agents","AI testing agents",lambda x,k:k("testing-apps"),"testing-apps"),
 ("personal-ai-assistants","personal AI assistants",lambda x,k:k("personal-assistants"),"personal-assistants"),
 ("ai-data-analysis-agents","AI data analysis agents",lambda x,k:k("data-analysis"),"data-analysis"),
 ("ai-document-agents","AI document and RAG tools",lambda x,k:k("documents"),"documents"),
 ("ai-agent-builders","no-code AI agent builders",lambda x,k:x["category"] in ("no-code builders","app builders"),"building-apps-without-code"),
 ("ai-image-and-design-agents","AI image and design agents",lambda x,k:k("making-images-and-design"),"making-images-and-design"),
 ("crypto-ai-agents","crypto AI agents",lambda x,k:x["category"]=="crypto","crypto-and-wallets"),
 ("ai-agent-payment-tools","AI agent payment tools",lambda x,k:k("agent-payments"),"agent-payments"),
 ("local-ai-agents","local AI agents",lambda x,k:k("running-agents-locally"),"running-agents-locally"),
 ("ai-web-scraping-tools","AI web scraping tools",lambda x,k:k("web-scraping"),"web-scraping"),
 ("deep-research-agents","deep research agents",lambda x,k:x["category"]=="research","research")]
# Tool lists of pages that were redirected into a main page (Oct 18 2026). They still count as existing
# lists, so the auto generators don't re-create near-duplicate search/sub-task pages for the same tools.
def absorbed_sets():
    import json
    try: t=json.load(open("tools.json"))
    except Exception: return []
    mcp={x["slug"] for x in t if x["category"]=="MCP servers" or "connect tools via MCP" in x.get("use_cases",[])}  # was best/mcp-servers
    try: frozen=[set(v) for v in json.load(open("data/absorbed_sets.json"))["sets"].values()]
    except Exception: frozen=[]
    return [mcp]+frozen
def _existing_sets(made):
    sets=[{x["slug"] for x in a[8]} for a in made]
    sets+=absorbed_sets()
    for f in glob.glob("best/*.html"):
        if f.endswith("index.html"): continue
        sets.append(set(re.findall(r'tools/([a-z0-9-]+)\.html',open(f).read().split("<main",1)[-1].split('id="nlblock"')[0])))
    if os.path.exists("free-tools.html"):  # each category section of the free-tools hub
        for sec in open("free-tools.html").read().split('<h2 id=')[1:]: sets.append(set(re.findall(r'tools/([a-z0-9-]+)\.html',sec)))
    return [x for x in sets if x]
try: _REDIR=set(__import__("json").load(open("redirects.json")))
except Exception: _REDIR=set()
def modifier_pages(t,m,made,inT):
    have={a[0] for a in made}; ex=_existing_sets(made); tasksets=[{x["slug"] for x in it} for _,it in m.values()]
    cands=[]
    for ms,ml,mf,mtxt in MODS:
        for tk,noun,tf,task in TARGETS:
            slug=f"{ms}-{tk}"
            if slug in have or (ms=="mcp" and "mcp" in tk): continue
            if f"s/{slug}.html" in _REDIR: continue  # redirected page (redirects.json): never re-create it
            allm=[x for x in t if live(x) and mf(x) and tf(x,inT(x))]
            A={x["slug"] for x in allm}
            if len(A)<MOD_MIN: continue
            base={x["slug"] for x in t if live(x) and tf(x,inT(x))}
            if len(A)>=.85*len(base): continue  # modifier must actually narrow the list
            if any(len(A&B)/len(A)>=.7 for B in ex): continue
            cands.append((len(A),slug,ml,noun,mtxt,task,allm,A))
    cands.sort(key=lambda z:-z[0]); out=[]; chosen=[]
    for n,slug,ml,noun,mtxt,task,allm,A in cands:
        if len(out)>=MOD_CAP: break
        if any(len(A&B)/min(len(A),len(B))>=.7 for B in chosen): continue
        chosen.append(A); h=f"{ml} {noun}"; intro=f"{noun[0].upper()+noun[1:]} {mtxt}." 
        out.append((slug,h,h[0].lower()+h[1:] if ml not in ("Python","TypeScript","MCP-ready") else h,len(allm),rank(allm)[:25],intro,task,None,allm))
    print("modifier search pages:",len(out),"of",len(cands),"candidates")
    return out
BROWSER=lambda x,k:x["category"]=="browser/computer use" or k("browsing-the-web")
# slug -> list of filters; the page shows the union of the top 25 of each (ranked), so both old lists survive the merge
MERGED={"open-source-browser-agents":[lambda x,k:BROWSER(x,k) and x["pricing"] in OS,lambda x,k:BROWSER(x,k) and isfree(x)]}
def site_stats(t):
    """Directory-wide numbers for stat callouts, computed from tools.json at build time (never hand-written)."""
    return {"total":len(t),"categories":len({x["category"] for x in t})}
def search_pages(t,m,asof):
    made=[]; inT=lambda x:(lambda s:s in m and x in m[s][1])
    for s,h,q,f,intro,task,best in S:
        allm=[x for x in t if live(x) and f(x,inT(x))]
        if len(allm)<6: print("skip search page (too few):",s,len(allm)); continue
        if s in MERGED:
            parts=[rank([x for x in t if live(x) and g(x,inT(x))])[:25] for g in MERGED[s]]
            seen=set(); items=[]
            for x in rank([y for p in parts for y in p]):
                if x["slug"] not in seen: seen.add(x["slug"]); items.append(x)
        else: items=rank(allm)[:25]
        made.append((s,h,q,len(allm),items,intro,task,best,allm))
    made+=modifier_pages(t,m,made,inT)
    titles={a[0]:a[1] for a in made}
    DATA['search']=made
    for s,h,q,n,items,intro,task,best,allm in made:
        canon=f"{B}s/{s}.html"; title=f"{h} (2026): {len(items)} picks · AgentScout"
        if s in MERGED: ST=site_stats(t); title=f"Free & Open-Source Browser Agents: {len(items)} Tools · AgentScout"
        cnt=f"top {len(items)} of {n} matching tools" if n>len(items) else f"{n} matching tools"  # same count basis as the title's "{len(items)} picks" (Oct 18 2026)
        desc=f"{h} in 2026: {cnt} in AgentScout's link-checked directory, including {', '.join(x['name'] for x in items[:3])}. Pricing as makers state it."
        if len(desc)>158: desc=f"{h} (2026): {cnt}, including {', '.join(x['name'] for x in items[:2])}. Link-checked; pricing as stated."
        if len(desc)>158: desc=f"{h} (2026): {cnt}, including {items[0]['name']}. Link-checked; pricing as stated."
        if len(desc)>158: desc=desc[:157].rsplit(" ",1)[0]+"…"
        if s in MERGED:
            desc=f"{len(items)} free and open-source browser agents and automation tools, including {items[0]['name']} and {items[1]['name']}. From a link-checked directory of {ST['total']:,}."
            if len(desc)>155: desc=f"{len(items)} free and open-source browser agents and automation tools, from a link-checked directory of {ST['total']:,} AI tools."
        pc=collections.Counter(x["pricing"] for x in items); cats=collections.Counter(x["category"] for x in allm).most_common()
        star=[x for x in items if x.get("github_stars")]
        osn=sum(1 for x in allm if x["pricing"] in OS); frn=sum(1 for x in allm if isfree(x))
        facts=(f'<div class="badges" style="margin:0 0 18px"><span class="b">{n} matching tools</span><span class="b">{osn} open source</span><span class="b">{frn} free or with a free tier</span>'
               +(f'<span class="b">Most starred: {e(star[0]["name"])} (★ {star[0]["github_stars"]:,})</span>' if star else "")+'</div>')
        faq=[(f"What are the best {q}?",f"Ranked by tracked GitHub stars, the top {q} in our directory are "+", ".join(x["name"] for x in items[:5])+". Stars measure popularity, not fit, so compare a few against your own task."),
             (f"How many {q} does AgentScout list?",f"{n} tools match. This page shows the top {len(items)}. Pricing mix on this page: "+", ".join(f"{k} ({v})" for k,v in pc.most_common())+"."),
             ("Are these tools really free?" if "free" in s else "How much do these tools cost?","Pricing is what each maker states on their site. Open-source tools are free to self-host but may need a paid model API key or offer paid cloud plans; freemium tools have a free plan with limits. Check each official site.")]
        if task in m: faq.append((f"Where can I see every tool for {m[task][0][1]}?",f"Our task page lists all {len(m[task][1])} tools we match to {m[task][0][1]}."))
        if s in MERGED:
            nos=sum(1 for x in items if x["pricing"] in OS)
            faq=[("What are open source browser agents?",f"Open-source browser agents are tools with public source code that let an AI model drive a real web browser: open pages, click, type, fill forms and pull out data. {nos} of the {len(items)} tools on this page are open source, including "+", ".join(x["name"] for x in items[:3])+"."),
                 ("What are the best free browser automation tools?","Ranked by tracked GitHub stars, the most popular free browser automation tools in our directory are "+", ".join(x["name"] for x in items[:5])+". Stars measure popularity, not fit, so try two or three on your own task."),
                 ("Are these browser agents really free?",f"Every tool here is open source or has a free plan. Pricing mix on this page: "+", ".join(f"{k} ({v})" for k,v in pc.most_common())+". Open-source tools may still need a paid model API key, and some sell an optional hosted cloud."),
                 (f"How many browser agents does AgentScout list?",f"{n} free or open-source tools match browser automation in our directory of {ST['total']:,} tools across {ST['categories']} categories. This page shows the top {len(items)}.")]
        fq="".join(f'<h3 style="font-size:15px;margin:18px 0 4px">{e(a)}</h3><p style="margin:0">{e(b)}</p>' for a,b in faq)
        rel=[f'<a href="../tasks/{task}.html">All tools for {e(m[task][0][1])}</a>'] if task in m else []
        if best: rel.append(f'<a href="../best/{best}.html">{e(next((p[1] for p in BB.PAGES if p[0]==best),"Best list"))}</a>')
        rel+=[f'<a href="../categories/{X.catslug(c)}.html">{e(c)} ({k})</a>' for c,k in cats[:4]]
        sib=[a for a in made if a[0]!=s and (a[6]==task or (best and a[7]==best))][:5]
        sibh=" · ".join(f'<a href="{a[0]}.html">{e(a[1])}</a>' for a in sib)
        roles=[r for r in R if s in r[6]]
        if not roles:  # fall back: roles whose sections use this page's task
            roles=[r for r in R if task in [b for _,b in r[4]]][:2]
        roleh=" · ".join(f'<a href="../for/{r[0]}.html">For {e(r[1])}</a>' for r in roles)
        ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B}},
            {"@type":"ItemList","name":h,"itemListOrder":"https://schema.org/ItemListOrderDescending","numberOfItems":len(items),"itemListElement":[{"@type":"ListItem","position":i+1,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate(items)]},
            {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":a,"acceptedAnswer":{"@type":"Answer","text":b}} for a,b in faq]},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Popular searches","item":B+"s/"},{"@type":"ListItem","position":3,"name":h,"item":canon}]}]}
        body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">Popular searches</a> / {e(h)}</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left;margin-left:0">{e(h)} (2026)</h1>'
              f'<p class="lede" style="margin-left:0;text-align:left">{e(intro)} {"Here are the top "+str(len(items))+" of "+str(n) if n>len(items) else "Here are all "+str(n)} from the AgentScout directory.</p>{facts}'
              f'<p class="muted" style="margin:0 0 18px"><strong>How we picked and ranked:</strong> tools are matched by category, the pricing each maker states and what each tool says it does. They are ranked by GitHub stars as recorded on each listing (link checks {asof}); tools without a tracked repo follow, by listing maturity. No paid placements.</p>'
              f'<ol class="grid" style="padding:0;margin:0">{"".join(BB.item(i+1,x) for i,x in enumerate(items))}</ol>'
              f'<h2 style="font-size:18px;margin:36px 0 6px">FAQ</h2>{fq}'
              f'<p style="margin-top:28px">Related: {" · ".join(rel)}</p>'+(f'<p>Similar searches: {sibh}</p>' if sibh else "")+(f'<p>By role: {roleh}</p>' if roleh else "")+
              f'<p><a href="index.html">All popular searches</a> · <a href="../for/index.html">AI agents by role</a> · <a href="../free-tools.html">Free tools</a></p>'
              f'<p class="disclose">Facts come from our directory listings; pricing is as each maker states it and can change. Check official sites before you choose.</p></section>')
        if s in MERGED:
            stat=(f'<div class="badges" style="margin:0 0 18px" aria-label="AgentScout directory stats"><span class="b"><b>{ST["total"]:,}</b>&nbsp;tools tracked</span><span class="b"><b>{ST["categories"]}</b>&nbsp;categories</span><span class="b">Links checked daily</span><span class="b">{len(items)} on this page</span></div>')
            lede=(f'<p class="lede" style="margin-left:0;text-align:left">AgentScout tracks {ST["total"]:,} AI agent tools across {ST["categories"]} categories and checks every link daily. This page is one slice of that directory: the {len(items)} most-starred browser agents and browser automation tools you can use for free, {nos} of them fully open source. Each one links to its listing, code and official site, so you can judge it yourself.</p>')
            why=('<h2 style="font-size:18px;margin:28px 0 6px">What browser agents are for</h2><p style="margin:0 0 18px">Browser agents let an AI model use the web the way a person does: open pages, click, type, log in and pull out data. Developers use them to automate repetitive web work, test UIs from plain-language steps, give coding agents like Claude Code or Cursor a live browser through MCP, and turn messy sites into clean, LLM-ready data. This list covers libraries, MCP servers, headless browsers, browser extensions and full desktop agents.</p>')
            rels=[("../categories/browser-computer-use.html","Browser and computer-use agents (category)"),("../best/ai-browser-agents.html","Best AI browser agents"),("../best/browser-use-alternatives.html","Browser Use alternatives"),("../s/computer-use-agents.html","AI computer-use agents"),("../tasks/browsing-the-web.html","AI agents for browsing the web"),("../tasks/web-scraping.html","AI web scraping tools"),("../categories/mcp-servers.html","MCP servers"),("../s/free-mcp-servers.html","Free MCP servers")]
            relh=('<h2 style="font-size:18px;margin:32px 0 6px">You might also like</h2><div class="badges">'+"".join(f'<a class="b uc" href="{u}">{e(l)}</a>' for u,l in rels)+'</div>')
            body=body.replace(f'<h1 style="text-align:left;margin-left:0">{e(h)} (2026)</h1>',f'<h1 style="text-align:left;margin-left:0">{e(h)} and browser automation tools (2026)</h1>',1)
            body=re.sub(r'<p class="lede".*?</p>'+re.escape(facts),lambda _:stat+lede+why+f'<h2 style="font-size:18px;margin:28px 0 6px">The {len(items)} tools</h2>',body,count=1,flags=re.S)
            body=body.replace(f'<p style="margin-top:28px">Related: ',relh+f'<p style="margin-top:20px">Related: ',1)
            body=body.replace('<p class="disclose">',f'<p style="margin-top:20px">Browser agents are one corner of AgentScout. <a href="../index.html#directory">Browse all {ST["total"]:,} tools across {ST["categories"]} categories</a> to find the rest of your agent stack.</p><p class="disclose">',1)
        open(f"s/{s}.html","w").write(X.shell("../",title,desc,canon,body,ld))
    canon=B+"s/"; title="Popular AI Agent Tool Searches (2026) · AgentScout"
    desc=f"{len(made)} focused lists of AI agent tools: free coding agents, open-source browser agents, Python frameworks, MCP servers, voice and more."[:158]
    tiles="".join(f'<a class="card" href="{a[0]}.html"><div class="ct"><h3>{e(a[1])}</h3></div><p>{a[3]} tools · {e(", ".join(x["name"] for x in a[4][:3]))}</p></a>' for a in made)
    ld={"@context":"https://schema.org","@type":"CollectionPage","name":title,"description":desc,"url":canon,"hasPart":[{"@type":"WebPage","name":a[1],"url":f"{B}s/{a[0]}.html"} for a in made]}
    body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / Popular searches</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left;margin-left:0">Popular AI agent tool searches</h1>'
          f'<p class="lede" style="margin-left:0;text-align:left">Quick answers to the searches people make most, each built from the AgentScout directory with the ranking method stated.</p><div class="grid">{tiles}</div>'
          f'<p style="margin-top:24px">See also: <a href="../for/index.html">AI agents by role</a> · <a href="../best/index.html">Best lists</a> · <a href="../tasks/index.html">AI agents by task</a> · <a href="../free-tools.html">Free tools</a></p></section>')
    open("s/index.html","w").write(X.shell("../",title,desc,canon,body,ld))
    return [canon]+[f"{B}s/{a[0]}.html" for a in made],made
# Short commercial-use and copyright note on role pages (Oct 18, 2026); also linked from the art task pages
ROLE_NOTE={"artists":'<div id="copyright" class="note" style="margin:10px 0;padding:10px 14px;border:1px solid var(--line);border-radius:10px;font-size:14px"><strong>Commercial use and copyright, in short.</strong> This is general information, not legal advice. In the US, the Copyright Office registers only work with real human authorship, and prompts alone usually don\'t count. The Supreme Court declined to hear <em>Thaler v. Perlmutter</em> on Mar 2, 2026, which leaves that rule in place. Training-data cases are still open: Getty mostly lost its UK case against Stability AI in Nov 2025 and can appeal, and Disney and Universal are suing Midjourney in the US. Before you sell AI-assisted work, read each tool\'s license terms. Some models, such as Adobe Firefly, Bria and Getty\'s generator, are trained only on licensed images and offer indemnity. To keep your own art out of training sets and style copies, look at <a href="../tools/glaze.html">Glaze</a> and <a href="https://cara.app" rel="nofollow noopener">Cara</a>.</div>'}
def role_pages(t,m,made):
    ok={a[0]:a[1] for a in made}; urls=[]; info=[]
    for s,who,h,intro,secs,fts,ss in R:
        canon=f"{B}for/{s}.html"; title=f"{h} (2026) · AgentScout"; secs=[(a,b) for a,b in secs if b in m]
        seen=set(); body_s=""; allitems=[]
        for hd,task in secs:
            items=[y for y in m[task][1] if live(y)][:6]  # build_tasks order: category match, use-case match, then stars
            allitems+=[x for x in items if x["slug"] not in seen]; seen|={x["slug"] for x in items}
            body_s+=(f'<h2 style="font-size:18px;margin:32px 0 6px">{e(hd)}</h2><p class="muted" style="margin:0 0 10px;font-size:14px">{e(m[task][0][5])} <a href="../tasks/{task}.html">All {len(m[task][1])} tools →</a></p>'
                     f'<ul style="list-style:none;padding:0;margin:0">{"".join(mini(x) for x in items)}</ul>')
        n=len(seen)
        if n<10: print('skip role page (too few tools):',s,n); continue
        desc=f"{h} in 2026: {n} picks across {len(secs)} jobs, including {', '.join(x['name'] for x in allitems[:3])}. Link-checked; pricing as makers state it."
        if len(desc)>158: desc=f"{h} (2026): {n} picks across {len(secs)} jobs, including {', '.join(x['name'] for x in allitems[:2])}."[:158]
        jump=" · ".join(f'<a href="#{T2}">{e(a)}</a>' for a,T2 in [(a,X.catslug(a)) for a,_ in secs])
        body_s=re.sub(r'<h2 style="font-size:18px;margin:32px 0 6px">([^<]+)</h2>',lambda mm:f'<h2 id="{X.catslug(__import__("html").unescape(mm.group(1)))}" style="font-size:18px;margin:32px 0 6px">{mm.group(1)}</h2>',body_s)
        ft=" · ".join(f'<a href="{ftl(a)}">{e(b)}</a>' for a,b in fts)
        sr=" · ".join(f'<a href="../s/{x}.html">{e(ok[x])}</a>' for x in ss if x in ok)
        oth=" · ".join(f'<a href="{r[0]}.html">{e(CAP(r[1]))}</a>' for r in R if r[0]!=s)
        free_n=sum(1 for x in allitems if isfree(x))
        ld={"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","name":title,"description":desc,"url":canon,"isPartOf":{"@type":"WebSite","name":"AgentScout","url":B},"audience":{"@type":"Audience","audienceType":who}},
            {"@type":"ItemList","numberOfItems":len(allitems),"itemListElement":[{"@type":"ListItem","position":i+1,"name":x["name"],"url":f"{B}tools/{x['slug']}.html"} for i,x in enumerate(allitems)]},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"By role","item":B+"for/"},{"@type":"ListItem","position":3,"name":h,"item":canon}]}]}
        body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">By role</a> / {e(CAP(who))}</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left;margin-left:0">{e(h)} (2026)</h1>'
              f'<p class="lede" style="margin-left:0;text-align:left">{e(intro)} We picked the top tools for {len(secs)} jobs {e(who)} do every day: {n} tools in all, {free_n} of them free or with a free tier.</p>'
              f'<p style="font-size:14px">Jump to: {jump}</p>'
              +(f'<p style="font-size:14px">Free tools from AgentScout for {e(who)}: {ft}</p>' if ft else "")+
              f'<p class="muted" style="margin:0 0 6px;font-size:13.5px"><strong>How we picked:</strong> each section takes the tools matched to that task in our directory, putting tools whose category and stated use cases fit the task first, then ordering by tracked GitHub stars. No paid placements.</p>'
              +ROLE_NOTE.get(s,"")+f'{body_s}'+(f'<h2 style="font-size:16px;margin:32px 0 10px">Popular searches for {e(who)}</h2><p>{sr}</p>' if sr else "")+
              f'<p style="margin-top:24px">Other roles: {oth} · <a href="index.html">All roles</a></p>'
              f'<p class="disclose">Facts come from our directory listings; pricing is as each maker states it and can change. Missing a tool? <a href="../submit.html">Submit it free</a>.</p></section>')
        open(f"for/{s}.html","w").write(X.shell("../",title,desc,canon,body,ld)); urls.append(canon); info.append((s,who,h,n)); DATA.setdefault('roles',[]).append((s,who,h,[b for _,b in secs],[x['slug'] for x in allitems]))
    canon=B+"for/"; title="AI Agents by Role: Tools for Every Team (2026) · AgentScout"
    desc=f"AI agent tools picked for {len(info)} roles: developers, marketers, sales, support, designers, researchers, crypto traders and more."[:158]
    tiles="".join(f'<a class="card" href="{s}.html"><div class="ct"><h3>For {e(who)}</h3></div><p>{n} tools picked</p></a>' for s,who,h,n in info)
    ld={"@context":"https://schema.org","@type":"CollectionPage","name":title,"description":desc,"url":canon,"hasPart":[{"@type":"WebPage","name":h,"url":f"{B}for/{s}.html"} for s,_,h,_ in info]}
    body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / By role</div><section style="padding-top:20px;text-align:left"><h1 style="text-align:left;margin-left:0">AI agents by role</h1>'
          f'<p class="lede" style="margin-left:0;text-align:left">Pick your job and see the AI agent tools that fit the work you actually do, grouped by task.</p><div class="grid">{tiles}</div>'
          f'<p style="margin-top:24px">See also: <a href="../s/">Popular searches</a> · <a href="../tasks/index.html">AI agents by task</a> · <a href="../best/index.html">Best lists</a> · <a href="../free-tools.html">Free tools</a></p></section>')
    open("for/index.html","w").write(X.shell("../",title,desc,canon,body,ld))
    return [canon]+urls,info
def pages(t):
    os.makedirs("s",exist_ok=True); os.makedirs("for",exist_ok=True)
    m=tm(T.mapping(t)); asof=max(x["verified"] for x in t)
    su,made=search_pages(t,m,asof); ru,info=role_pages(t,m,made)
    keep={f"s/{a[0]}.html" for a in made}|{f"for/{r[0]}.html" for r in info}|{"s/index.html","for/index.html"}
    for f in glob.glob("s/*.html")+glob.glob("for/*.html"):
        if f not in keep: os.remove(f)
    # hub links (additive)
    BB.link_in("best/index.html",'See also: ','<a href="../s/">Popular searches</a> · <a href="../for/index.html">AI agents by role</a> · ','href="../s/"')
    BB.link_in("tasks/index.html",'each with the agent tools that handle it.',' Or browse <a href="../for/index.html">by role</a> and <a href="../s/">popular searches</a>.',' Or browse <a href="../for/index.html">by role</a>')
    BB.link_in("free-tools.html",'grouped by category.</p>',f'<p style="font-size:14px;margin:-6px 0 0">Looking for something specific? Try <a href="s/">popular searches</a> like <a href="s/free-ai-coding-agents.html">free AI coding agents</a> or browse <a href="for/index.html">AI agents by role</a>.</p>','href="s/"')
    BB.link_in("llms.txt",f"- [All best-of lists]({B}best/)",f"\n- [Popular searches]({B}s/)\n- [AI agents by role]({B}for/)\n- [Free tools: AI cost calculator]({B}free-tools/ai-cost-calculator.html)\n- [Free tools: token counter]({B}free-tools/token-counter.html)\n- [Free tools: prompt builder]({B}free-tools/prompt-builder.html)\n- [Free tools: agent setup generator]({B}free-tools/agent-setup-generator.html)",f"]({B}s/)")
    # Oct 20 2026: inbound links to the merged browser-agents page from the homepage and the MCP servers category
    BB.link_in("index.html",'<a href="s/index.html">Popular searches</a>',' · <a href="s/open-source-browser-agents.html">Free &amp; open-source browser agents</a>','href="s/open-source-browser-agents.html"')
    # Oct 20 2026: inbound links from category pages to the matching free calculators/builders (they had none)
    FT={"mcp-servers":[("mcp-config-builder","MCP config builder"),("mcp-server-picker","MCP server picker")],"mcp-infra":[("mcp-config-builder","MCP config builder"),("tool-schema-builder","Tool schema builder")],
        "coding":[("rules-file-generator","Rules file generator"),("token-counter","Token counter"),("context-window-planner","Context window planner")],
        "frameworks":[("agent-run-cost-estimator","Agent run cost estimator"),("tool-schema-builder","Tool schema builder"),("system-prompt-linter","System prompt linter")],
        "agent-infra":[("agent-run-cost-estimator","Agent run cost estimator"),("build-vs-buy-calculator","Build vs buy calculator")]}
    for c,L in FT.items():
        BB.link_in(f"categories/{c}.html",'<p class="disclose">','<p style="margin:0 0 14px">Free tools for this: '+" · ".join(f'<a href="../free-tools/{h}.html">{l}</a>' for h,l in L)+'</p>','data-ft="cat"')
        p=f"categories/{c}.html"
        if os.path.exists(p):
            z=open(p).read(); z=z.replace('<p style="margin:0 0 14px">Free tools for this:','<p data-ft="cat" style="margin:0 0 14px">Free tools for this:',1); open(p,"w").write(z)
    print("landing:",len(made),"search pages,",len(info),"role pages + 2 hubs")
    return su+ru
