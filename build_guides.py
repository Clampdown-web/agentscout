"""How-to guides in guides/. Called from build_extras.build() so the next rebuild keeps the pages.

Guides come from the GUIDES list below: one entry per guide, each with its own
metadata, body and JSON-LD builders, and contextual-link notes. The workflow
guide keeps the output it had when it shipped; a new guide adds one entry.

Facts in the workflow guide were checked against vendor docs and pricing pages on 2026-11-16.
Facts in the crawl guide were checked against vendor docs and pricing pages on 2026-11-18.
A claim that could not be checked is left out of the page.
"""
import json, os, re
import build_extras as X
B = X.B
e = X.e
GUIDE = "guides/how-to-automate-workflows-with-ai-agents.html"
HUB = "guides/index.html"
CANON = B + GUIDE
HUB_CANON = B + "guides/"
QUERY = "how to automate workflows with AI agents"
TITLE = "How to automate workflows with AI agents · AgentScout"
DESC = "How to automate workflows with AI agents: choose the tool type, keep a person on irreversible steps, and test on real past cases."
H1 = "How to automate workflows with AI agents"
CHECKED = "2026-11-16"
CHECKED_LABEL = "November 16, 2026"
HREF = "../" + GUIDE
SLUG = "how-to-automate-workflows-with-ai-agents"

CRAWL_GUIDE = "guides/how-to-crawl-websites-for-ai-agents.html"
CRAWL_SLUG = "how-to-crawl-websites-for-ai-agents"
CRAWL_CANON = B + CRAWL_GUIDE
CRAWL_QUERY = "how to crawl websites for AI agents"
# 64 chars: over the 60-char guard, kept verbatim from the brief because it leads
# with the top Search Console query ("ai web crawler", 15 impressions Oct 21-Nov 17)
# and still shows the full target query. The per-guide cap is set in GUIDES.
CRAWL_TITLE = "AI web crawler: how to crawl websites for AI agents · AgentScout"
CRAWL_DESC = "How to crawl websites for AI agents: pick the right tool for clean Markdown, JS pages or structured JSON, respect robots.txt, and feed agents safely."
CRAWL_H1 = "How to crawl websites for AI agents (and pick an AI web crawler)"
CRAWL_CHECKED = "2026-11-18"
CRAWL_CHECKED_LABEL = "November 18, 2026"
CRAWL_HREF = "../" + CRAWL_GUIDE

STEPS = [
    ("Pick one workflow",
     "Name the trigger, the finish line, and what done means. Keep it to one workflow. A support queue and a lead inbox are two workflows."),
    ("Map the current process",
     "Write the steps a person does today, in order, including the waits. Use tickets or leads you already closed, not a blank diagram."),
    ("Mark agent steps and rule steps",
     "A rule step has one right action, such as routing an enterprise-plan customer to the enterprise queue or sending the password-reset link you already use. An agent step is the one where a person reads and decides, such as which category a ticket is or what the reply should say. Leave the rule steps as rules."),
    ("Choose the tool type",
     "Use the table below. A no-code automator fits a trigger plus app steps. An agent builder fits when you are designing the agent. A code framework fits when the agent needs your own tools and saved state. A durable engine fits when a step waits hours, retries, or must still be there after a restart."),
    ("Connect tools with the smallest permission that still works",
     "Give the agent a credential that can do the job and nothing adjacent. A help-desk token that can read tickets and create drafts is a different token from one that can refund or close accounts. n8n MCP and Zapier MCP are two ways to expose those tools. Zapier's help center says each successful Zapier MCP tool call uses 2 tasks."),
    ("Add an approval gate before anything irreversible",
     "Sending the reply, issuing a refund, deleting a record, and posting in a customer channel wait for a named person. A sentence in the prompt is not the gate. The table lists how each tool actually pauses."),
    ("Test on 20 to 50 real past cases",
     "Replay closed tickets or leads. Compare the agent's category and draft with what a person did. Count the ones you would not have sent. Fix the rules and the tools before you let it act."),
    ("Monitor and iterate",
     "Log the trigger, the tool the agent wanted, the approval decision, and the result. Turn the agent step off without turning off the rules. Widen what the agent is allowed to do only after the misses on new cases are ones you can accept."),
]
FAQ = [
    ("Can AI agents automate workflows without code?",
     "Yes. Zapier, Make, n8n, Activepieces, Dify, Flowise, and Langflow let you build the flow on a canvas. You still write the outcome, the trigger, and which steps a person must approve. LangGraph, CrewAI, and Mastra are the path when the agent needs your own runtime."),
    ("What is the difference between workflow automation and an AI agent?",
     "A workflow runs steps you already specified: when this happens, do that. An AI agent chooses a next action from the tools you gave it. Most production setups use both. Rules handle the steps that should never vary. The agent handles only the step that needs judgment."),
    ("Is n8n better than Zapier for AI agents?",
     "Neither is better for every workflow. n8n can self-host under its Sustainable Use License, bills n8n Cloud per workflow execution, and can require a person to approve an AI Agent tool before it runs. Zapier is hosted, bills per successful task, and its Human in the Loop step pauses a Zap on paid accounts. Pick n8n when you want self-hosting or one charge for a whole run. Pick Zapier when the work is a short chain across apps you already connect there."),
    ("Are there free AI workflow automation tools?",
     "Yes. n8n's Community edition is free to self-host under the Sustainable Use License. Activepieces' MIT core is free to self-host and has no credit meter. Dify's Community edition is free to self-host. Trigger.dev, Windmill's Community Edition, Kestra, and Dagu also publish a free self-host option. Hosted plans often have a limited free start, and the model API is usually a separate bill. Check the vendor page before you rely on a free tier."),
    ("How do I keep a human in the loop?",
     "Put a person on the step that sends, pays, deletes, or changes a customer record. n8n can pause before an AI Agent tool runs. Zapier's Human in the Loop step pauses a Zap until someone approves, declines, or changes the data, and Zapier says that step needs a paid account. Dify, Langflow, and Flowise pause on a human-input step. LangGraph's interrupt() and Mastra's suspend() pause code until you resume it. Inngest waits for an approval event without holding the process open. Do not use a sentence in the prompt as the only gate."),
    ("How much does AI workflow automation cost?",
     "It depends on the meter. Zapier charges per successful task. Make charges credits, and most actions use 1 credit. n8n Cloud charges per workflow execution, one run of the whole workflow. Inngest counts the function run plus each step as executions. Trigger.dev charges compute-seconds while a task is executing, plus $0.000025 per run, and does not bill a checkpointed wait as compute. Lindy bills credits per active user, from $29.99 a month. Self-hosting n8n, Activepieces, Dify, Windmill Community Edition, Kestra, or Dagu removes that vendor meter. You still pay for the machine and, where the tool calls one, the model."),
]

CRAWL_STEPS = [
    ("Decide the output",
     "Markdown for RAG or agent context, typed JSON for a database, or actions for a browser agent. The output decides the tool: a Markdown crawler will not give you a typed schema, and a browser agent is slow, expensive bulk crawling."),
    ("Scope the crawl",
     "List seed URLs or a sitemap, include-patterns, a depth cap, and a page cap. Then check robots.txt and the site's terms before you fetch anything."),
    ("Pick the fetch layer",
     "Plain HTTP is enough for static pages. Reach for a headless browser only when the content needs JavaScript to appear."),
    ("Pick the tool",
     "Use the table below. A hosted API fits when you want reliability without running browsers. A local library fits when the crawl is free and yours to run. A browser agent fits only for logged-in or interactive pages."),
    ("Clean and chunk",
     "Strip navigation, ads, and boilerplate. Chunk by headings. Keep the URL, the page title, the crawl date, and a content hash with every chunk, so you can trace an answer back to its source."),
    ("Treat crawled text as untrusted input",
     "Page text can carry prompt injection: instructions hidden in a page that try to make your agent act. Restrict the seeds you crawl, and never let page text trigger tool calls on its own."),
    ("Give it to an agent",
     "Expose the crawler through an MCP server: Firecrawl MCP, ScrapeGraph MCP, or Playwright MCP. Use a search API such as Tavily or Exa when the agent needs to find pages rather than crawl a known site."),
    ("Recrawl incrementally and spot-check",
     "Compare content hashes and re-embed only the pages that changed. Then spot-check five pages against their source: a clean-looking crawl can still drop a table or merge two sections."),
]
CRAWL_FAQ = [
    ("What is an AI web crawler?",
     "An AI web crawler fetches pages, renders JavaScript when needed, and returns clean Markdown or JSON a model can read. It is the step between a website and an agent: the crawler turns pages into text the model can use as context or store for retrieval."),
    ("Is there a free or open-source AI web crawler?",
     "Yes. Crawl4AI (Apache-2.0), ScrapeGraphAI (MIT), Scrapling (BSD-3-Clause), and Spider (MIT) are free to run on your own machine. Firecrawl's core is open source under AGPL-3.0 and self-hostable, and its hosted plan starts with 1,000 free credits a month."),
    ("Is Firecrawl free?",
     "Firecrawl's hosted Free plan gives you 1,000 credits a month, about 1,000 pages, with no card required. Hobby is $19 a month for 5,000 credits and Standard is $99 a month for 100,000. A scrape or crawl costs 1 credit per page, and the JSON format adds 4 credits per page. Credits do not roll over below the Scale plan."),
    ("Firecrawl vs Crawl4AI: which should I use?",
     "Use Firecrawl when you want a hosted API and do not want to run browsers yourself. Use Crawl4AI when you want a free local crawl under the permissive Apache-2.0 license and are happy running Python and Playwright. If you self-host Firecrawl's core and build a closed service on it, read the AGPL-3.0 copyleft terms first."),
    ("How do I scrape a website with AI?",
     "Decide the output first: Markdown for reading, typed JSON for a database. Then scope the crawl, check robots.txt and the site's terms, and pick the tool from the table below. Clean and chunk the result, keep the source URL and crawl date, and treat the crawled text as untrusted input before you hand it to an agent."),
    ("Can an AI agent scrape websites through MCP?",
     "Yes. Firecrawl MCP, ScrapeGraph MCP, and Playwright MCP expose scrape, crawl, and browser tools to any MCP client, so the agent can fetch a page without you writing the crawler. Use a search API such as Tavily or Exa instead when the agent needs to find pages it does not already know."),
    ("Is web scraping legal?",
     "There is no single answer, and this is not legal advice. Scraping public data is the usual starting point, but you should respect robots.txt and the site's terms, and rules on personal data vary by country. When in doubt, check the rules where you operate or ask a lawyer."),
]


def _tool_link(slug, name):
    """Logo sits in the link so the listing logo gate accepts table cells and link rows."""
    icon = X.ico({"name": name, "slug": slug, "logo": f"assets/logos/{slug}.png"}, "../", "sm")
    icon = icon.replace('width="40" height="40"', 'width="24" height="24"')
    return f'<a class="icol" href="../tools/{slug}.html">{icon}{e(name)}</a>'


def _links(pairs):
    return "<br>".join(_tool_link(slug, name) for slug, name in pairs)


# tool type, example pairs, best for, approval, pricing, self-host. Checked 2026-11-16.
ROWS = [
    ("No-code automators",
     [("zapier-agents", "Zapier Agents"), ("make", "Make"), ("n8n", "n8n"), ("activepieces", "Activepieces")],
     "A trigger plus app steps, with an agent only where a step needs judgment.",
     "Zapier pauses a Zap on its Human in the Loop step, and its help center says that step needs a paid account. Make's Human in the Loop app is on the Enterprise plan and in closed beta for invited customers. n8n can require approval before an AI Agent tool runs. Activepieces publishes an Approval (Legacy) piece that pauses a flow until someone approves or disapproves.",
     "Zapier charges per successful task. Make charges credits. Credits replaced operations, and most actions use 1 credit. n8n Cloud charges per workflow execution: one run of the whole workflow, however many steps it has. Activepieces hosted plans use credits. The MIT Community Edition has no credit meter.",
     "n8n yes, under the Sustainable Use License. Activepieces yes, MIT core. Zapier and Make: no self-host plan on the pricing pages checked."),
    ("Agent builders",
     [("dify", "Dify"), ("flowise", "Flowise"), ("langflow", "Langflow"), ("lindy", "Lindy"), ("relevance-ai", "Relevance AI")],
     "Designing the agent on a canvas, then connecting the apps it should touch.",
     "Dify's Human Input node pauses for a form by web app or email. Flowise's published Human Input node has Proceed and Reject outputs. Langflow's Human Input component pauses until a person picks an action, and an agent tool can require approval. Lindy's pricing page says anything with outside impact, such as sending an email or updating a ticket, waits for approval. Relevance AI's public pricing page does not describe an approval step.",
     "Dify Cloud is billed per workspace and includes message credits. Community self-host is free. Lindy bills credits per active user, from $29.99 a month for 3,000 credits, with a $50 credit start that lasts 7 days. Relevance AI's public pricing page lists Enterprise with custom Actions and Vendor Credits. A current hosted price for Flowise or Langflow was not on the docs checked.",
     "Dify, Flowise, and Langflow yes. Lindy no. No self-host plan for Relevance AI on the pricing page checked."),
    ("Code frameworks",
     [("langgraph", "LangGraph"), ("crewai", "CrewAI"), ("mastra", "Mastra")],
     "The agent needs your own code, tools, and saved state.",
     "LangGraph's interrupt() pauses a node until you resume it, and the docs say this needs a checkpointer. CrewAI's human_input flag has a person review the task's final answer. It defaults to off. Mastra's suspend and resume pauses a step for human input and stores a snapshot.",
     "You run the libraries yourself. LangSmith, the hosted product next to LangGraph, bills seats and usage. Mastra Platform bills compute, egress, and observability, and lists a free plan. CrewAI's task docs do not list a price.",
     "Yes. You run the framework in your own process. Mastra also sells a hosted platform."),
    ("Durable workflow engines",
     [("inngest", "Inngest"), ("trigger-dev", "Trigger.dev"), ("windmill", "Windmill"), ("kestra", "Kestra"), ("dagu", "Dagu")],
     "A step that waits, retries, or must still be there after a process restart.",
     "Inngest's step.waitForEvent() pauses until an approval event or a timeout, and the docs say the function is suspended while it waits. Trigger.dev checkpoints a wait longer than 5 seconds. Windmill's docs say approval steps are in the open-source Community Edition: the flow suspends until someone approves, rejects, or the timeout passes. Dagu's API treats a waiting step as human approval and has an approve endpoint. Kestra's FAQ does not describe an approval step.",
     "Inngest Cloud counts an execution as the function run plus each step. Trigger.dev charges compute-seconds while a task is executing, plus $0.000025 per run, and does not bill a checkpointed wait as compute. Windmill's paid plans bill seats and compute units. Kestra is free to self-host. Dagu's community self-host needs no license key.",
     "Yes for all five. Inngest documents a self-hosted server. Trigger.dev is Apache 2.0. Windmill's Community Edition is free and open source. Kestra is Apache 2.0. Dagu is GPL-3.0."),
]


def _cta(heading):
    return (
        f'<h2 style="font-size:18px;margin:28px 0 8px">{e(heading)}</h2>'
        '<ul class="guide-list">'
        '<li><a href="../s/free-ai-workflow-automation-tools.html">Free AI workflow automation tools</a></li>'
        '<li><a href="../s/open-source-workflow-automation-tools.html">Open-source workflow automation tools</a></li>'
        '<li><a href="../submit.html">Submit a tool</a></li>'
        '<li><a href="../newsletter.html">Newsletter, every Wednesday</a></li>'
        "</ul>"
    )


def _table():
    body = []
    for kind, tools, best, approval, price, host in ROWS:
        body.append(
            "<tr>"
            f'<th scope="row">{e(kind)}</th>'
            f"<td>{_links(tools)}</td>"
            f"<td>{e(best)}</td>"
            f"<td>{e(approval)}</td>"
            f"<td>{e(price)}</td>"
            f"<td>{e(host)}</td>"
            "</tr>"
        )
    return (
        '<div class="cmpwrap"><div class="cmpscroll"><table class="cmptbl">'
        f'<caption class="muted" style="caption-side:bottom;text-align:left;padding:8px 10px;font-size:12.5px">Checked <time datetime="{CHECKED}">{CHECKED_LABEL}</time>. Pricing models are what each vendor described that day.</caption>'
        "<thead><tr>"
        '<th scope="col">Tool type</th><th scope="col">Examples</th><th scope="col">Best for</th>'
        '<th scope="col">Human approval</th><th scope="col">Pricing model</th><th scope="col">Self-host</th>'
        "</tr></thead><tbody>"
        + "".join(body) + "</tbody></table></div></div>"
    )


def _body():
    answer = (
        "<p class=\"lede\" style=\"margin-left:0;text-align:left;max-width:68ch\">"
        "How to automate workflows with AI agents comes down to one split: rules for the steps that should never vary, and an agent only where a step needs judgment. "
        "A person approves anything that sends, pays, deletes, or changes a customer record. "
        "The tool type follows the work: a no-code automator for app-to-app steps, an agent builder when you are designing the agent, a code framework when the agent needs your own runtime, or a durable engine when a step can wait for hours or must survive a restart."
        "</p>"
    )
    steps = "<ol style=\"margin:0 0 8px;padding-left:1.3em;line-height:1.55;max-width:68ch\">" + "".join(
        f'<li style="margin:0 0 12px"><strong>{e(name)}.</strong> {e(text)}</li>' for name, text in STEPS
    ) + "</ol>"
    example = (
        '<h2 id="example" style="font-size:18px;margin:28px 0 8px">Worked example: support-ticket triage</h2>'
        '<p style="margin:0 0 12px;max-width:68ch">This is a pattern for the eight steps, not a measured result.</p>'
        '<ul style="margin:0 0 8px;padding-left:1.2em;line-height:1.55;max-width:68ch">'
        "<li style=\"margin:0 0 8px\"><strong>Trigger.</strong> A new ticket arrives.</li>"
        "<li style=\"margin:0 0 8px\"><strong>Rules.</strong> Enterprise-plan customers go to the enterprise queue. Password-reset tickets get the reset link you already send. Those two never go to the agent.</li>"
        "<li style=\"margin:0 0 8px\"><strong>Agent.</strong> Read the ticket and the help-center articles you allow, pick a category, and draft a reply.</li>"
        "<li style=\"margin:0 0 8px\"><strong>Approval.</strong> A person approves the draft before it is sent. A refund or an account change is a second gate, or it stays manual.</li>"
        "<li style=\"margin:0 0 8px\"><strong>Tool type.</strong> A no-code automator fits when the help desk and the mail tool already connect and the draft is the only judgment. A durable engine fits when the approval can sit overnight and the run has to resume after a restart. A code framework fits when the agent needs a scratch workspace, not just a prompt and a few app actions.</li>"
        "<li style=\"margin:0 0 8px\"><strong>Test.</strong> Replay 20 to 50 closed tickets. A wrong category, or a draft that invents a policy, is a miss.</li>"
        "</ul>"
    )
    checklist = (
        '<h2 id="checklist" style="font-size:18px;margin:28px 0 8px">Checklist</h2>'
        '<ul style="margin:0;padding-left:1.2em;line-height:1.55;max-width:68ch">'
        "<li style=\"margin:0 0 8px\">One workflow, one outcome, one trigger.</li>"
        "<li style=\"margin:0 0 8px\">Every step marked rule or agent.</li>"
        "<li style=\"margin:0 0 8px\">Irreversible steps have a named approver.</li>"
        "<li style=\"margin:0 0 8px\">Each tool uses a scoped credential, not an admin key.</li>"
        "<li style=\"margin:0 0 8px\">20 to 50 real past cases, compared with what a person did.</li>"
        "<li style=\"margin:0 0 8px\">A log of the agent's proposed action, and a way to turn that step off.</li>"
        "</ul>"
    )
    faq = '<h2 id="faq" style="font-size:18px;margin:28px 0 8px">FAQ</h2>' + "".join(
        f'<details style="margin:0 0 10px;max-width:68ch"><summary style="cursor:pointer;font-weight:600;min-height:44px;display:flex;align-items:center">{e(q)}</summary>'
        f'<p style="margin:8px 0 0">{e(a)}</p></details>' for q, a in FAQ
    )
    more = (
        '<h2 style="font-size:18px;margin:28px 0 8px">Related reading</h2>'
        '<ul class="guide-list">'
        '<li><a href="../compare/n8n-vs-make.html">n8n vs Make</a></li>'
        '<li><a href="../compare/n8n-vs-zapier-agents.html">n8n vs Zapier Agents</a></li>'
        '<li><a href="../compare/dify-vs-flowise.html">Dify vs Flowise</a></li>'
        '<li><a href="../best/no-code-ai-agent-builders.html">Best no-code AI agent builders</a></li>'
        '<li><a href="../best/n8n-alternatives.html">n8n alternatives</a></li>'
        f'<li>{_tool_link("n8n", "n8n")}</li>'
        f'<li>{_tool_link("n8n-mcp", "n8n MCP")}</li>'
        f'<li>{_tool_link("zapier-mcp", "Zapier MCP")}</li>'
        "</ul>"
    )
    return (
        f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="index.html">Guides</a> / {e(H1)}</div>'
        '<section class="calm">'
        f'<h1 style="text-align:left">{e(H1)}</h1>'
        + answer
        + '<h2 style="font-size:18px;margin:8px 0">Steps</h2>'
        + steps + example
        + '<h2 id="which-tool" style="font-size:18px;margin:28px 0 8px">Which tool type fits</h2>'
        + '<p style="margin:0 0 12px;max-width:68ch">Same workflow, four kinds of tool. Human approval, the pricing meter, and whether you can run it yourself are what the usual six-step guides leave out.</p>'
        + _table()
        + '<p style="margin:0;max-width:68ch">Model API fees are separate wherever the tool calls a model you pay for.</p>'
        + _cta("Browse, submit, or subscribe")
        + checklist + faq + more
        + _cta("When you are ready")
        + f'<p class="disclose">Feature details were checked on each vendor\'s docs or pricing page on <time datetime="{CHECKED}">{CHECKED_LABEL}</time>. Prices change. Read the vendor page before you buy. No vendor paid for a mention.</p>'
        + "</section>"
    )


def _ld():
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "HowTo",
                "name": H1,
                "description": DESC,
                "url": CANON,
                "datePublished": CHECKED,
                "dateModified": CHECKED,
                "step": [
                    {"@type": "HowToStep", "position": i, "name": name, "text": text}
                    for i, (name, text) in enumerate(STEPS, 1)
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in FAQ
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "AgentScout", "item": B},
                    {"@type": "ListItem", "position": 2, "name": "Guides", "item": HUB_CANON},
                    {"@type": "ListItem", "position": 3, "name": H1, "item": CANON},
                ],
            },
        ],
    }


# tool pairs, best for, runs where, JS rendering, license or pricing model, agent hookup.
# Checked 2026-11-18. Firecrawl prices re-checked against firecrawl.dev/pricing that day.
CRAWL_ROWS = [
    ([("firecrawl", "Firecrawl")],
     "Hosted scraping and crawling that returns clean Markdown or JSON, without running browsers.",
     "Hosted API, or self-host the core with Docker.",
     "Yes, headless browser rendering.",
     "Core AGPL-3.0. Hosted Free plan 1,000 credits a month (about 1,000 pages, no card); Hobby $19 a month for 5,000 credits; Standard $99 a month for 100,000. Scrape and crawl cost 1 credit per page; the JSON format adds 4 per page. Credits do not roll over below Scale.",
     "Firecrawl MCP server, plus SDKs and a REST API."),
    ([("crawl4ai", "Crawl4AI")],
     "Free local crawls that turn sites into Markdown for RAG or agent context.",
     "Your machine, as a Python library or a Docker API.",
     "Yes, Playwright rendering.",
     "Apache-2.0. Free to run; you pay only for your machine and, where you use one, the model.",
     "Import it in Python, or call the Docker API from any runtime."),
    ([("scrapegraphai", "ScrapeGraphAI"), ("scrapegraph-mcp", "ScrapeGraph MCP")],
     "LLM-driven extraction to structured output from a prompt or a schema.",
     "Your machine, as a Python library.",
     "Yes, through Playwright.",
     "MIT. Free to run; the model you call is a separate bill.",
     "ScrapeGraph MCP for agents."),
    ([("scrapling", "Scrapling")],
     "Python crawling where pages change markup and selectors keep breaking.",
     "Your machine, as a Python library.",
     "Yes, browser fetchers alongside the HTTP fetcher.",
     "BSD-3-Clause. Free to run.",
     "Import it in Python; pair it with your own agent code."),
    ([("spider", "Spider")],
     "High-speed crawling of many pages.",
     "Your machine, as a Rust library or binary.",
     "Yes, optional headless Chrome.",
     "MIT. Free to run.",
     "Call it from Rust, or drive it from your agent's code."),
    ([("browser-use", "Browser Use"), ("stagehand", "Stagehand"), ("playwright-mcp", "Playwright MCP"), ("browserbase", "Browserbase"), ("steel", "Steel")],
     "Logged-in or interactive pages, where a crawl cannot go. Not bulk crawling.",
     "Your machine for the libraries; hosted browsers from Browserbase or Steel.",
     "Yes. That is the point: a real browser.",
     "Browser Use MIT, Stagehand MIT, Playwright MCP Apache-2.0, Steel Browser Apache-2.0. You pay for the model and, where you use one, the hosted browser.",
     "Playwright MCP plugs a browser into any MCP client; Browser Use and Stagehand are libraries your agent code calls."),
    ([("tavily", "Tavily"), ("exa", "Exa")],
     "Finding pages when the agent does not already know the URL.",
     "Hosted APIs.",
     "No. They search and return results; they do not render pages.",
     "Hosted, freemium. Check the vendor page for the current free allowance.",
     "REST APIs, and MCP servers for agent clients."),
]


def _crawl_table():
    body = []
    for tools, best, runs, js, price, hookup in CRAWL_ROWS:
        body.append(
            "<tr>"
            f"<td>{_links(tools)}</td>"
            f"<td>{e(best)}</td>"
            f"<td>{e(runs)}</td>"
            f"<td>{e(js)}</td>"
            f"<td>{e(price)}</td>"
            f"<td>{e(hookup)}</td>"
            "</tr>"
        )
    return (
        '<div class="cmpwrap"><div class="cmpscroll"><table class="cmptbl">'
        f'<caption class="muted" style="caption-side:bottom;text-align:left;padding:8px 10px;font-size:12.5px">Checked <time datetime="{CRAWL_CHECKED}">{CRAWL_CHECKED_LABEL}</time>. Pricing models are what each vendor described that day.</caption>'
        "<thead><tr>"
        '<th scope="col">Tool</th><th scope="col">Best for</th><th scope="col">Runs where</th>'
        '<th scope="col">JS rendering</th><th scope="col">License or pricing</th><th scope="col">Agent hookup</th>'
        "</tr></thead><tbody>"
        + "".join(body) + "</tbody></table></div></div>"
    )


def _crawl_cta(heading):
    return (
        f'<h2 style="font-size:18px;margin:28px 0 8px">{e(heading)}</h2>'
        '<ul class="guide-list">'
        '<li><a href="../tasks/web-scraping.html">Browse every web scraping tool</a></li>'
        '<li><a href="../newsletter.html">Newsletter, every Wednesday</a></li>'
        '<li><a href="../submit.html">Submit your scraper</a></li>'
        "</ul>"
    )


def _crawl_body():
    answer = (
        "<p class=\"lede\" style=\"margin-left:0;text-align:left;max-width:68ch\">"
        "An AI web crawler fetches pages, renders JavaScript when needed, and returns clean Markdown or JSON a model can read. "
        "Pick by job: an open-source library like Crawl4AI for free local crawls, a hosted API like Firecrawl when you want reliability without running browsers, "
        "and a browser agent like Browser Use or Stagehand only for logged-in or interactive pages."
        "</p>"
    )
    steps = "<ol style=\"margin:0 0 8px;padding-left:1.3em;line-height:1.55;max-width:68ch\">" + "".join(
        f'<li style="margin:0 0 12px"><strong>{e(name)}.</strong> {e(text)}</li>' for name, text in CRAWL_STEPS
    ) + "</ol>"
    checklist = (
        '<h2 id="checklist" style="font-size:18px;margin:28px 0 8px">Checklist</h2>'
        '<ul style="margin:0;padding-left:1.2em;line-height:1.55;max-width:68ch">'
        "<li style=\"margin:0 0 8px\">Output format chosen: Markdown, typed JSON, or actions.</li>"
        "<li style=\"margin:0 0 8px\">Scope set: seed URLs or sitemap, include-patterns, depth and page caps.</li>"
        "<li style=\"margin:0 0 8px\">robots.txt and the site's terms checked.</li>"
        "<li style=\"margin:0 0 8px\">JavaScript rendering only where the content needs it.</li>"
        "<li style=\"margin:0 0 8px\">Every chunk keeps its URL, title, crawl date, and content hash.</li>"
        "<li style=\"margin:0 0 8px\">Crawled text treated as untrusted: no tool calls from page text.</li>"
        "<li style=\"margin:0 0 8px\">Agent hookup chosen: an MCP server, or a search API for finding pages.</li>"
        "<li style=\"margin:0 0 8px\">Recrawl plan set, and five pages spot-checked against their source.</li>"
        "</ul>"
    )
    faq = '<h2 id="faq" style="font-size:18px;margin:28px 0 8px">FAQ</h2>' + "".join(
        f'<details style="margin:0 0 10px;max-width:68ch"><summary style="cursor:pointer;font-weight:600;min-height:44px;display:flex;align-items:center">{e(q)}</summary>'
        f'<p style="margin:8px 0 0">{e(a)}</p></details>' for q, a in CRAWL_FAQ
    )
    more = (
        '<h2 style="font-size:18px;margin:28px 0 8px">Related reading</h2>'
        '<ul class="guide-list">'
        '<li><a href="../tasks/browsing-the-web-web-scraping.html">Scraping and crawling tools for web browsing agents</a></li>'
        '<li><a href="../s/free-ai-web-scraping-tools.html">Free AI web scraping tools</a></li>'
        '<li><a href="../mcp/web-search-and-scraping-mcp-servers.html">Best MCP servers for web search and scraping</a></li>'
        '<li><a href="../guides/how-to-automate-workflows-with-ai-agents.html">How to automate workflows with AI agents</a></li>'
        f'<li>{_tool_link("scout-outcrawl", "Scout (Outcrawl)")}</li>'
        f'<li>{_tool_link("n8n", "n8n")}</li>'
        "</ul>"
    )
    return (
        f'<div class="crumb"><a href="../">AgentScout</a> / <a href="./">Guides</a> / {e(CRAWL_H1)}</div>'
        '<section class="calm">'
        f'<h1 style="text-align:left">{e(CRAWL_H1)}</h1>'
        + answer
        + '<h2 style="font-size:18px;margin:8px 0">Steps</h2>'
        + steps
        + '<h2 id="which-tool" style="font-size:18px;margin:28px 0 8px">Which tool fits the job</h2>'
        + '<p style="margin:0 0 12px;max-width:68ch">Most top results for this query are single-tool tutorials: a Crawl4AI quickstart, or a cloud walkthrough. This guide is the tool-agnostic version: pick by the job, the license and cost model, and the safety rules, then hook the result into an agent.</p>'
        + _crawl_table()
        + '<p style="margin:0;max-width:68ch">Model API fees are separate wherever the tool calls a model you pay for.</p>'
        + _crawl_cta("Browse, submit, or subscribe")
        + checklist + faq + more
        + _crawl_cta("When you are ready")
        + f'<p class="disclose">Feature details were checked on each vendor\'s docs or pricing page on <time datetime="{CRAWL_CHECKED}">{CRAWL_CHECKED_LABEL}</time>. Prices change. Read the vendor page before you buy. No vendor paid for a mention.</p>'
        + "</section>"
    )


def _crawl_ld():
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "HowTo",
                "name": CRAWL_H1,
                "description": CRAWL_DESC,
                "url": CRAWL_CANON,
                "datePublished": CRAWL_CHECKED,
                "dateModified": CRAWL_CHECKED,
                "step": [
                    {"@type": "HowToStep", "position": i, "name": name, "text": text}
                    for i, (name, text) in enumerate(CRAWL_STEPS, 1)
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in CRAWL_FAQ
                ],
            },
            {
                "@type": "Article",
                "headline": CRAWL_H1,
                "description": CRAWL_DESC,
                "url": CRAWL_CANON,
                "datePublished": CRAWL_CHECKED,
                "dateModified": CRAWL_CHECKED,
                "author": {"@type": "Organization", "name": "AgentScout", "url": B},
                "publisher": {"@type": "Organization", "name": "AgentScout", "url": B},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "AgentScout", "item": B},
                    {"@type": "ListItem", "position": 2, "name": "Guides", "item": HUB_CANON},
                    {"@type": "ListItem", "position": 3, "name": CRAWL_H1, "item": CRAWL_CANON},
                ],
            },
        ],
    }


def _hub_body():
    return (
        '<div class="crumb"><a href="../index.html">AgentScout</a> / Guides</div>'
        '<section class="calm">'
        '<h1 style="text-align:left">How-to guides</h1>'
        '<p class="lede" style="margin-left:0;text-align:left">Short guides for choosing and running AI agent tools. Each one says what was checked and what was left out.</p>'
        '<ul class="guide-list">'
        + "".join(f'<li><a href="{g["slug"]}.html">{e(g["h1"])}</a></li>' for g in GUIDES)
        + "</ul>"
        '<h2 style="font-size:18px;margin:28px 0 8px">Elsewhere on AgentScout</h2>'
        '<ul class="guide-list">'
        '<li><a href="../best/index.html">Best lists</a></li>'
        '<li><a href="../compare/index.html">Comparisons</a></li>'
        '<li><a href="../s/index.html">Popular lists</a></li>'
        '</ul>'
        "</section>"
    )


def _hub_ld():
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "name": "How-to guides · AgentScout",
                "description": "How-to guides from AgentScout: automating workflows with AI agents, and crawling websites for AI agents.",
                "url": HUB_CANON,
                "isPartOf": {"@type": "WebSite", "name": "AgentScout", "url": B},
                "hasPart": [{"@type": "HowTo", "name": g["h1"], "url": g["canon"]} for g in GUIDES],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "AgentScout", "item": B},
                    {"@type": "ListItem", "position": 2, "name": "Guides", "item": HUB_CANON},
                ],
            },
        ],
    }


def _finish(html, path):
    import build_tasks
    import ga4
    if 'name="robots"' not in html:
        html = html.replace(
            '<link rel="canonical"',
            '<meta name="robots" content="index, follow">\n<link rel="canonical"',
            1,
        )
    html = html.replace('<main class="wrap">', '<main class="wrap" data-pagefind-body>', 1)
    depth = "../" * path.count("/")
    html = build_tasks.ensure_shared_scripts(path, html, depth)
    html = ga4.apply(html, path)
    sibling = open("compare/n8n-vs-make.html", encoding="utf-8").read()
    nav = re.search(r"<nav\b.*?</nav>", sibling, re.S).group(0)
    foot = re.search(r"<footer\b.*?</footer>", sibling, re.S).group(0)
    html = re.sub(r"<nav\b.*?</nav>", lambda m: nav, html, count=1, flags=re.S)
    html = re.sub(r"<footer\b.*?</footer>", lambda m: foot, html, count=1, flags=re.S)
    return html


def _check_lengths(title, desc, h1, query, max_title=60):
    if len(title) > max_title:
        raise SystemExit(f"guide title is {len(title)} chars")
    if len(desc) > 156:
        raise SystemExit(f"guide description is {len(desc)} chars")
    q = query.lower()
    if q not in title.lower() or q not in h1.lower() or q not in desc.lower():
        raise SystemExit("target query missing from title, H1, or description")


def _ensure(path, snippet, anchor, slug, before=False):
    """Add one contextual link. A later rebuild that already emits the href is left alone."""
    if not os.path.exists(path):
        return
    s = open(path, encoding="utf-8").read()
    if f"guides/{slug}.html" in s:
        return
    if anchor not in s:
        raise SystemExit(f"guide link anchor missing in {path}")
    repl = snippet + anchor if before else anchor + snippet
    open(path, "w", encoding="utf-8").write(s.replace(anchor, repl, 1))


def _link_existing():
    note_free = (
        '<p>A free plan and a fit are different questions. '
        f'<a href="{HREF}">How to automate workflows with AI agents</a> '
        "maps which tool type fits, including the ones you can run without a hosted meter.</p>"
    )
    note_os = (
        "<p>Self-hosting is one part of the choice. "
        f'<a href="{HREF}">How to automate workflows with AI agents</a> '
        "shows which engines you can run yourself, and which approval and pricing models stay on a hosted plan.</p>"
    )
    note_cmp = (
        "<p>Approval gates and long waits are where these two split from the rest of the field. "
        f'<a href="{HREF}">How to automate workflows with AI agents</a> '
        "maps that against Zapier, Make, code frameworks, and durable engines.</p>"
    )
    note_n8n = (
        '<p style="margin:-12px 0 28px">If you are choosing n8n against Zapier, Make, or a code runtime, read '
        f'<a href="{HREF}">how to automate workflows with AI agents</a>.</p>'
    )
    _ensure("s/free-ai-workflow-automation-tools.html", note_free, "<!--/ci:aeo-->", SLUG)
    _ensure("s/open-source-workflow-automation-tools.html", note_os, "<!--/ci:aeo-->", SLUG)
    _ensure("compare/n8n-vs-make.html", note_cmp, '<p class="linkpile-label">Related</p>', SLUG, before=True)
    _ensure("compare/n8n-vs-zapier-agents.html", note_cmp, '<p class="linkpile-label">Related</p>', SLUG, before=True)
    _ensure(
        "best/no-code-ai-agent-builders.html",
        f'<li><a href="{HREF}">How to automate workflows with AI agents</a></li>',
        '<li><a href="../tasks/automating-workflows.html">Automating workflows</a></li>',
        SLUG,
    )
    _ensure(
        "tools/n8n.html",
        note_n8n,
        'Official site: <a href="https://n8n.io" target="_blank" rel="noopener noreferrer">n8n.io</a>.</p>',
        SLUG,
    )


def _crawl_link_existing():
    note_tasks = (
        "<p>Before you pick a tool, decide the output and the scope. "
        f'<a href="{CRAWL_HREF}">How to crawl websites for AI agents</a> '
        "walks through the eight steps, from output format to the recrawl plan.</p>"
    )
    note_free = (
        "<p>Free is one part of the choice. "
        f'<a href="{CRAWL_HREF}">How to crawl websites for AI agents</a> '
        "shows which crawlers you can run yourself, and which pricing and license models stay on a hosted plan.</p>"
    )
    note_mcp = (
        "<p>An MCP server is how the crawl reaches the agent. "
        f'<a href="{CRAWL_HREF}">How to crawl websites for AI agents</a> '
        "shows which MCP servers fit which job, and when a search API fits better.</p>"
    )
    note_firecrawl = (
        '<p style="margin:-12px 0 28px">If you are choosing Firecrawl against Crawl4AI or a local library, read '
        f'<a href="{CRAWL_HREF}">how to crawl websites for AI agents</a>.</p>'
    )
    note_crawl4ai = (
        '<p style="margin:-12px 0 28px">If you are choosing Crawl4AI against Firecrawl or a hosted API, read '
        f'<a href="{CRAWL_HREF}">how to crawl websites for AI agents</a>.</p>'
    )
    _ensure("tasks/web-scraping.html", note_tasks, '<p class="updated">', CRAWL_SLUG, before=True)
    _ensure("tasks/browsing-the-web-web-scraping.html", note_tasks, '<p class="updated">', CRAWL_SLUG, before=True)
    _ensure("s/free-ai-web-scraping-tools.html", note_free, "<!--/ci:aeo-->", CRAWL_SLUG)
    _ensure("mcp/web-search-and-scraping-mcp-servers.html", note_mcp, "<!--/ci:aeo-->", CRAWL_SLUG)
    _ensure(
        "tools/firecrawl.html",
        note_firecrawl,
        'Official site: <a href="https://firecrawl.dev" target="_blank" rel="noopener noreferrer">firecrawl.dev</a>.</p>',
        CRAWL_SLUG,
    )
    _ensure(
        "tools/crawl4ai.html",
        note_crawl4ai,
        'Official site: <a href="https://crawl4ai.com/" target="_blank" rel="noopener noreferrer">crawl4ai.com</a>.</p>',
        CRAWL_SLUG,
    )


def _sitemap(urls):
    """urls is a list of (canonical URL, lastmod) pairs. Only missing URLs are added."""
    path = "sitemap.xml"
    if not os.path.exists(path):
        return
    sm = open(path, encoding="utf-8").read()
    block = ""
    for u, lastmod in urls:
        if u not in sm:
            block += f"  <url><loc>{u}</loc><lastmod>{lastmod}</lastmod></url>\n"
    if block:
        sm = sm.replace("</urlset>", block + "</urlset>")
        open(path, "w", encoding="utf-8").write(sm)


GUIDES = [
    {"slug": SLUG, "guide": GUIDE, "canon": CANON, "title": TITLE, "desc": DESC, "h1": H1,
     "query": QUERY, "checked": CHECKED, "body": _body, "ld": _ld, "links": _link_existing},
    {"slug": CRAWL_SLUG, "guide": CRAWL_GUIDE, "canon": CRAWL_CANON, "title": CRAWL_TITLE,
     "desc": CRAWL_DESC, "h1": CRAWL_H1, "query": CRAWL_QUERY, "checked": CRAWL_CHECKED,
     "body": _crawl_body, "ld": _crawl_ld, "links": _crawl_link_existing, "max_title": 65},
]


def pages():
    """Write every guide in GUIDES plus the guides hub. Return canonical URLs for the sitemap."""
    for g in GUIDES:
        _check_lengths(g["title"], g["desc"], g["h1"], g["query"], max_title=g.get("max_title", 60))
    os.makedirs("guides", exist_ok=True)
    hub_title = "How-to guides · AgentScout"
    hub_desc = "How-to guides from AgentScout: automating workflows with AI agents, and crawling websites for AI agents."
    urls = []
    for g in GUIDES:
        html = _finish(X.shell("../", g["title"], g["desc"], g["canon"], g["body"](), g["ld"]()), g["guide"])
        open(g["guide"], "w", encoding="utf-8").write(html)
        urls.append(g["canon"])
    hub = _finish(X.shell("../", hub_title, hub_desc, HUB_CANON, _hub_body(), _hub_ld()), HUB)
    open(HUB, "w", encoding="utf-8").write(hub)
    for g in GUIDES:
        g["links"]()
    urls.append(HUB_CANON)
    print("guides:", len(urls), "pages")
    return urls


if __name__ == "__main__":
    import atexit
    atexit._clear()  # importing build_extras registers site-wide exit hooks
    urls = pages()
    lastmod = {g["canon"]: g["checked"] for g in GUIDES}
    lastmod[HUB_CANON] = max(lastmod.values())
    _sitemap([(u, lastmod.get(u, CHECKED)) for u in urls])
    import build_seo
    build_seo.llms_extra()
