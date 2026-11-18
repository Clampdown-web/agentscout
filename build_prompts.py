"""Prompt library (Nov 18 2026): data/prompts.json -> /prompts/ landing page + one page per category.
Hand-written, original prompts only -- no scraped or image-prompt content. Idempotent; runs from
build_site.py after build_bot_templates, and the daily build regenerates the pages from this file
plus the data file (no generated HTML is committed for this section).

Local shell: this module builds pages from data/detail.tpl with the same head/nav/footer slicing
as build_extras.shell, instead of importing build_extras -- that import registers an atexit hook
that rebuilds the Pagefind search index, which a small section builder must not trigger on a
standalone run. ASSET_V is read from build_tasks.py source the same way (no import).
"""
import datetime
import html
import json
import os
import re

SITE = "https://agentscouthq.com"
D = "prompts"
DATA = "data/prompts.json"

# slug: (name, blurb, [(link, label), ...] related pages on this site)
CATS = {
    "coding-agents": (
        "Coding agents",
        "Prompts that keep a coding agent honest: plan first, prove the fix, never weaken a test.",
        [("best/ai-coding-agents.html", "Best AI coding agents"),
         ("categories/coding.html", "Coding tools")],
    ),
    "mcp": (
        "MCP",
        "Prompts for working with MCP servers: wire one up, audit what it can touch, debug it when it goes quiet.",
        [("s/best-mcp-servers.html", "Best MCP servers"),
         ("categories/mcp-servers.html", "MCP servers")],
    ),
    "browser-agents": (
        "Browser agents",
        "Prompts for agents that open pages for you: research with sources, forms without guessing, prices with proof.",
        [("best/ai-browser-agents.html", "Best AI browser agents"),
         ("categories/browser-computer-use.html", "Browser agents")],
    ),
}

LANDING_TITLE = "Prompt library for AI agents \u00b7 AgentScout"
LANDING_DESC = ("Copy-paste prompts for coding agents, MCP and browser agents. "
                "Hand-written, original, and free \u2014 plus how to submit your own.")
CAT_DESC = {
    "coding-agents": ("Copy-paste prompts for coding agents: plan before you code, review diffs, "
                      "fix failures without weakening tests, and reproduce bugs first."),
    "mcp": ("Copy-paste prompts for MCP: wire up a server, audit what it can touch, "
            "debug silent tool calls, and pick the right server."),
    "browser-agents": ("Copy-paste prompts for browser agents: research with citations, fill forms "
                       "without guessing, compare prices, and watch pages."),
}

CSS = ('<style id="pr-css">.pr-cats{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));margin:16px 0 24px}'
       '.pr-cat{display:block;border:1px solid var(--line);border-radius:12px;padding:16px;background:var(--card);text-decoration:none;color:var(--text)}'
       '.pr-cat b{display:block;font-size:17px;margin-bottom:4px}.pr-cat span{color:var(--muted);font-size:13.5px;line-height:1.5;display:block}'
       '.pr-grid{display:grid;gap:16px;margin:14px 0 28px}'
       '.pr-card{border:1px solid var(--line);border-radius:12px;padding:18px;background:var(--card);min-width:0}'
       '.pr-card h3{margin:0 0 6px;font-size:18px}.pr-card p{margin:0 0 8px}'
       '.pr-meta{font-size:13.5px;color:var(--muted)}'
       '.pr-code{white-space:pre-wrap;overflow-wrap:anywhere;background:var(--soft);border:1px solid var(--line);border-radius:8px;padding:12px;font-size:13.5px;line-height:1.55;margin:10px 0;max-width:100%;box-sizing:border-box}'
       '.pr-copy{min-height:44px}.pr-cta{border:1px solid var(--line);border-radius:12px;padding:16px 18px;background:var(--card);margin:20px 0}'
       '.pr-cta h2{margin:0 0 6px;font-size:17px}.pr-cta p{margin:0 0 10px}</style>')

JS = ('<script id="pr-js">(function(){document.querySelectorAll("[data-copy]").forEach(function(b){'
      'b.addEventListener("click",function(){var c=b.closest(".pr-card");var t=c?c.querySelector(".pr-code"):null;'
      'if(!t)return;var txt=t.textContent;'
      'function done(){var o=b.textContent;b.textContent="Copied";setTimeout(function(){b.textContent=o},2000)}'
      'function fb(){var ta=document.createElement("textarea");ta.value=txt;document.body.appendChild(ta);ta.select();'
      'try{document.execCommand("copy");done()}catch(e){}document.body.removeChild(ta)}'
      'if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(done,function(){fb()})}else{fb()}})})})();</script>')

esc = html.escape


def _asset_v():
    m = re.search(r'ASSET_V\s*=\s*"([^"]+)"', open("build_tasks.py", encoding="utf-8").read())
    return m.group(1) if m else "0"


def _shell(title, desc, canon, body, ld):
    """Same head/nav/footer slicing as build_extras.shell (see module docstring)."""
    tpl = open("data/detail.tpl", encoding="utf-8").read()
    head = tpl.split("<title>")[0].replace("../", "../")
    foot = "<footer" + tpl.split("<footer", 1)[1].replace("../", "../")
    nav = tpl.split("</head>", 1)[1].split("<main")[0].replace("../", "../")
    page = (f'{head}<title>{esc(title)}</title>\n'
            f'<meta name="description" content="{esc(desc)}">\n'
            f'<link rel="canonical" href="{canon}">\n'
            '<meta property="og:type" content="article">'
            f'<meta property="og:title" content="{esc(title)}">'
            f'<meta property="og:description" content="{esc(desc)}">'
            f'<meta property="og:url" content="{canon}">'
            f'<meta name="twitter:title" content="{esc(title)}">'
            f'<meta name="twitter:description" content="{esc(desc)}">\n'
            '<script type="application/ld+json">'
            + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
            + '</script>\n'
            f'</head>{nav}<main class="wrap">{body}</main>\n{foot}')
    v = _asset_v()
    page = re.sub(r'(app\.js|styles\.css|home-mobile\.css|track\.js|compare-picker\.js|consent\.js|share\.js|reviews\.js|submit-turnstile\.js)\?v=\d+',
                  lambda mm: mm.group(1) + "?v=" + v, page)
    return page


def _ld(title, desc, canon, crumbs, items):
    graph = [
        {"@context": "https://schema.org", "@type": "CollectionPage",
         "name": title, "description": desc, "url": canon},
        {"@context": "https://schema.org", "@type": "BreadcrumbList",
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u}
                             for i, (n, u) in enumerate(crumbs)]},
    ]
    if items:
        graph.append({"@context": "https://schema.org", "@type": "ItemList",
                      "name": title, "numberOfItems": len(items),
                      "itemListElement": [{"@type": "ListItem", "position": i + 1,
                                           "name": t, "url": u}
                                          for i, (t, u) in enumerate(items)]})
    return {"@context": "https://schema.org", "@graph": graph}


def _card(p):
    return (f'<article class="pr-card" id="{esc(p["slug"])}">'
            f'<h3>{esc(p["title"])}</h3>'
            f'<p>{esc(p["desc"])}</p>'
            f'<p class="pr-meta">Works with: {esc(p["works_with"])}</p>'
            f'<p class="pr-meta">Use it when: {esc(p["when"])}</p>'
            f'<pre class="pr-code">{esc(p["prompt"])}</pre>'
            '<button type="button" class="btn pr-copy" data-copy>Copy prompt</button>'
            '</article>')


def _cta():
    return ('<section class="pr-cta"><h2>Have a prompt worth sharing?</h2>'
            '<p>Send us one prompt that makes a coding, MCP or browser agent do better work. '
            'Hand-written and original only \u2014 we check every prompt by hand before it goes live.</p>'
            '<p style="margin:0"><a class="btn primary" href="../submit.html?type=prompt">Submit a prompt</a></p>'
            '</section>')


def _related(cat):
    links = "".join(f'<a href="../{u}">{esc(label)}</a>'
                    for u, label in CATS[cat][2])
    return (f'<p style="margin-top:20px">Related: {links} \u00b7 '
            '<a href="../bot-templates/">AI bot templates</a></p>')


def _sitemap_add(rels):
    """Append indexable canonical URLs, same pattern as build_lighten._sitemap_add."""
    p = "sitemap.xml"
    if not os.path.exists(p) or not rels:
        return 0
    s = open(p, encoding="utf-8").read()
    day = datetime.date.today().isoformat()
    extra = ""
    for rel in rels:
        loc = SITE + "/" + rel
        if loc in s:
            continue
        extra += f'  <url><loc>{loc}</loc><lastmod>{day}</lastmod></url>\n'
    if extra:
        open(p, "w", encoding="utf-8").write(s.replace("</urlset>", extra + "</urlset>"))
    return extra.count("<url>")


def run():
    prompts = json.load(open(DATA, encoding="utf-8"))
    seen = set()
    for p in prompts:
        assert p["category"] in CATS, f"unknown category {p['category']} on {p['id']}"
        assert p["slug"] not in seen, f"duplicate slug {p['slug']}"
        assert p["prompt"].strip() and p["title"].strip(), f"empty prompt {p['id']}"
        seen.add(p["slug"])
    by_cat = {c: [p for p in prompts if p["category"] == c] for c in CATS}
    os.makedirs(D, exist_ok=True)
    rels = []

    # Landing page: category cards, then every prompt grouped by category.
    cards = "".join(
        f'<a class="pr-cat" href="{c}.html"><b>{esc(CATS[c][0])}</b>'
        f'<span>{esc(CATS[c][1])}</span><span>{len(by_cat[c])} prompts \u2192</span></a>'
        for c in CATS)
    sections = "".join(
        f'<h2 id="{c}">{esc(CATS[c][0])}</h2><div class="pr-grid">'
        + "".join(_card(p) for p in by_cat[c]) + '</div>'
        for c in CATS)
    body = (CSS + '<div class="crumb"><a href="../index.html">AgentScout</a> / Prompt library</div>'
            f'<h1>Prompt library</h1><p class="lede">{esc(LANDING_DESC)}</p>'
            f'<div class="pr-cats">{cards}</div>{sections}{_cta()}'
            '<p>Related: <a href="../best/ai-coding-agents.html">Best AI coding agents</a> \u00b7 '
            '<a href="../s/best-mcp-servers.html">Best MCP servers</a> \u00b7 '
            '<a href="../best/ai-browser-agents.html">Best AI browser agents</a> \u00b7 '
            '<a href="../bot-templates/">AI bot templates</a></p>' + JS)
    canon = f"{SITE}/{D}/"
    ld = _ld("Prompt library for AI agents", LANDING_DESC, canon,
             [("AgentScout", SITE + "/"), ("Prompt library", canon)],
             [(p["title"], f"{canon}#{p['slug']}") for p in prompts])
    open(f"{D}/index.html", "w", encoding="utf-8").write(
        _shell(LANDING_TITLE, LANDING_DESC, canon, body, ld))
    rels.append(f"{D}/index.html")

    # One page per category.
    for c in CATS:
        name, blurb, _ = CATS[c]
        title = f"{name} prompts \u00b7 AgentScout"
        desc = CAT_DESC[c]
        others = "".join(
            f'<a href="{o}.html">{esc(CATS[o][0])}</a>'
            for o in CATS if o != c)
        body = (CSS + '<div class="crumb"><a href="../index.html">AgentScout</a> / '
                f'<a href="index.html">Prompt library</a> / {esc(name)}</div>'
                f'<h1>{esc(name)} prompts</h1><p class="lede">{esc(blurb)}</p>'
                '<div class="pr-grid">' + "".join(_card(p) for p in by_cat[c]) + '</div>'
                f'<p>More prompts: <a href="index.html">All prompts</a> \u00b7 {others}</p>'
                f'{_cta()}{_related(c)}' + JS)
        canon = f"{SITE}/{D}/{c}.html"
        ld = _ld(f"{name} prompts", desc, canon,
                 [("AgentScout", SITE + "/"), ("Prompt library", SITE + f"/{D}/"),
                  (f"{name} prompts", canon)],
                 [(p["title"], f"{canon}#{p['slug']}") for p in by_cat[c]])
        open(f"{D}/{c}.html", "w", encoding="utf-8").write(_shell(title, desc, canon, body, ld))
        rels.append(f"{D}/{c}.html")

    added = _sitemap_add(rels)
    print(f"prompts: {len(prompts)} prompts, {len(rels)} pages, sitemap +{added}")
    return {"prompts": len(prompts), "pages": len(rels), "sitemap_added": added}


if __name__ == "__main__":
    run()
