"""How-to guides in guides/. Called from build_extras.build() so the next rebuild keeps the pages.

Facts in the workflow guide were checked against vendor docs and pricing pages on 2026-11-16.
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
        f'<div class="crumb"><a href="../">AgentScout</a> / <a href="./">Guides</a> / {e(H1)}</div>'
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


def _hub_body():
    return (
        '<div class="crumb"><a href="../">AgentScout</a> / Guides</div>'
        '<section class="calm">'
        '<h1 style="text-align:left">How-to guides</h1>'
        '<p class="lede" style="margin-left:0;text-align:left">Short guides for choosing and running AI agent tools. Each one says what was checked and what was left out.</p>'
        '<ul class="guide-list">'
        f'<li><a href="how-to-automate-workflows-with-ai-agents.html">{e(H1)}</a></li>'
        "</ul>"
        '<h2 style="font-size:18px;margin:28px 0 8px">Elsewhere on AgentScout</h2>'
        '<ul class="guide-list">'
        '<li><a href="../best/">Best lists</a></li>'
        '<li><a href="../compare/">Comparisons</a></li>'
        '<li><a href="../s/">Popular lists</a></li>'
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
                "description": "How-to guides from AgentScout, starting with how to automate workflows with AI agents.",
                "url": HUB_CANON,
                "isPartOf": {"@type": "WebSite", "name": "AgentScout", "url": B},
                "hasPart": [{"@type": "HowTo", "name": H1, "url": CANON}],
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


def _check_lengths():
    if len(TITLE) > 60:
        raise SystemExit(f"guide title is {len(TITLE)} chars")
    if len(DESC) > 156:
        raise SystemExit(f"guide description is {len(DESC)} chars")
    q = QUERY.lower()
    if q not in TITLE.lower() or q not in H1.lower() or q not in DESC.lower():
        raise SystemExit("target query missing from title, H1, or description")


def _ensure(path, snippet, anchor, before=False):
    """Add one contextual link. A later rebuild that already emits the href is left alone."""
    if not os.path.exists(path):
        return
    s = open(path, encoding="utf-8").read()
    if "guides/how-to-automate-workflows-with-ai-agents.html" in s:
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
    _ensure("s/free-ai-workflow-automation-tools.html", note_free, "<!--/ci:aeo-->")
    _ensure("s/open-source-workflow-automation-tools.html", note_os, "<!--/ci:aeo-->")
    _ensure("compare/n8n-vs-make.html", note_cmp, '<p class="linkpile-label">Related</p>', before=True)
    _ensure("compare/n8n-vs-zapier-agents.html", note_cmp, '<p class="linkpile-label">Related</p>', before=True)
    _ensure(
        "best/no-code-ai-agent-builders.html",
        f'<li><a href="{HREF}">How to automate workflows with AI agents</a></li>',
        '<li><a href="../tasks/automating-workflows.html">Automating workflows</a></li>',
    )
    _ensure(
        "tools/n8n.html",
        note_n8n,
        'Official site: <a href="https://n8n.io" target="_blank" rel="noopener noreferrer">n8n.io</a>.</p>',
    )


def _sitemap(urls):
    path = "sitemap.xml"
    if not os.path.exists(path):
        return
    sm = open(path, encoding="utf-8").read()
    block = ""
    for u in urls:
        if u not in sm:
            block += f"  <url><loc>{u}</loc><lastmod>{CHECKED}</lastmod></url>\n"
    if block:
        sm = sm.replace("</urlset>", block + "</urlset>")
        open(path, "w", encoding="utf-8").write(sm)


def pages():
    """Write the guide and the guides hub. Return canonical URLs for the sitemap."""
    _check_lengths()
    os.makedirs("guides", exist_ok=True)
    hub_title = "How-to guides · AgentScout"
    hub_desc = "How-to guides from AgentScout, starting with how to automate workflows with AI agents."
    article = _finish(X.shell("../", TITLE, DESC, CANON, _body(), _ld()), GUIDE)
    hub = _finish(X.shell("../", hub_title, hub_desc, HUB_CANON, _hub_body(), _hub_ld()), HUB)
    open(GUIDE, "w", encoding="utf-8").write(article)
    open(HUB, "w", encoding="utf-8").write(hub)
    _link_existing()
    urls = [CANON, HUB_CANON]
    print("guides:", len(urls), "pages")
    return urls


if __name__ == "__main__":
    import atexit
    atexit._clear()  # importing build_extras registers site-wide exit hooks
    urls = pages()
    _sitemap(urls)
    import build_seo
    build_seo.llms_extra()
