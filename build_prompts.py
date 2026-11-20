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
import pacific
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

# Alt text describes the frame in assets/prompts/thumbs/<slug>.webp.
THUMB_ALT = {
    "plan-before-you-code": "Illustration of a checklist with arrows pointing at code blocks.",
    "review-my-diff": "Illustration of a diff panel with red and green lines and two comment bubbles.",
    "fix-the-failure-not-the-test": "Illustration of a failing test turning into a passing test, with the test file locked.",
    "refactor-without-changing-behavior": "Illustration of tangled blocks becoming tidy blocks beside an equals sign.",
    "reproduce-the-bug-first": "Illustration of a bug inside a loop, then a checkmark.",
    "wire-up-mcp-server": "Illustration of an agent node linked to a server node with a green handshake.",
    "audit-mcp-permissions": "Illustration of a server node with permission rays, a shield, and one red flag.",
    "debug-mcp-tool-call": "Illustration of a broken link between two nodes under a magnifying glass.",
    "pick-the-right-mcp-server": "Illustration of three server cards with the middle one selected.",
    "minimal-mcp-server-spec": "Illustration of a short spec card with two tool chips and a lock.",
    "browse-with-citations": "Illustration of a browser window with three numbered citation badges linked to source cards and a small flag.",
    "fill-form-without-guessing": "Illustration of a form with three checked fields, two empty fields marked with a question, and a disabled submit bar.",
    "compare-prices-three-stores": "Illustration of three store cards and a bar chart, with the shortest bar and store B marked lowest.",
    "watch-page-for-changes": "Illustration of three page thumbnails on a timeline, the last one highlighted, with an eye and a bell.",
    "summarize-page-for-decision": "Illustration of a long page shrinking into a short card with three icon rows and a checkmark.",
}

CSS = """<style id="pr-css">
main.wrap{max-width:1280px}
main.wrap>h1{margin:0 0 12px;max-width:none;text-align:left}
main.wrap>.lede{margin:0 0 18px;max-width:none;text-align:left}
.pr-nav{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 18px}
.pr-nav a{display:inline-flex;align-items:center;min-height:40px;padding:0 14px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--text);text-decoration:none;font-size:14px;font-weight:650}
.pr-nav a[aria-current=page]{background:#4338CA;border-color:#4338CA;color:#fff}
.pr-nav a:hover{border-color:#9393FF}
.pr-nav a:focus-visible,.pr-card .pr-copy:focus-visible,.pr-share:focus-visible,.pr-more summary:focus-visible{outline:2px solid #C4C4FF;outline-offset:2px}
.pr-cats{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));margin:0 0 22px}
.pr-cat{display:block;border:1px solid var(--line);border-radius:12px;padding:16px;background:var(--card);text-decoration:none;color:var(--text)}
.pr-cat b{display:block;font-size:17px;margin-bottom:4px}.pr-cat span{color:var(--muted);font-size:13.5px;line-height:1.5;display:block}
.pr-grid{display:grid;gap:16px;margin:8px 0 28px;grid-template-columns:1fr;align-items:stretch}
@media(min-width:760px){.pr-grid{grid-template-columns:1fr 1fr}}
@media(min-width:1100px){.pr-grid{grid-template-columns:1fr 1fr 1fr}}
.pr-card{position:relative;display:flex;flex-direction:column;height:100%;border:1px solid #2A2F3A;border-radius:16px;background:#171A22;color:#E8EAF0;min-width:0;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.35);transition:border-color .15s,box-shadow .15s,transform .15s}
.pr-card:hover{transform:translateY(-2px);border-color:#9393FF;box-shadow:0 10px 24px rgba(0,0,0,.35),0 0 0 1px rgba(147,147,255,.55),0 0 22px rgba(91,91,247,.32)}
@media(prefers-reduced-motion:reduce){.pr-card{transition:none}.pr-card:hover{transform:none}}
.pr-thumb{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;margin:0 0 12px;border-radius:16px 16px 0 0;background:#0E1015}
.pr-lead{display:flex;flex-direction:column;flex:1 1 auto;padding:0}
.pr-badge{display:inline-flex;align-items:center;align-self:flex-start;margin:0 14px 6px;padding:2px 9px;border-radius:999px;background:#25264D;color:#E4E4FF;font-size:12px;font-weight:650;letter-spacing:.02em}
.pr-card h3{margin:0 14px 8px;font-size:17px;font-weight:700;line-height:1.3;color:#E8EAF0}
.pr-tags{display:flex;flex-wrap:wrap;gap:6px;margin:0 14px 8px}
.pr-chip{display:inline-flex;align-items:center;gap:5px;max-width:100%;padding:2px 8px;border:1px solid #2A2F3A;border-radius:999px;background:#12151c;color:#C5CDD8;font-size:12px;line-height:1.45}
.pr-chip.cat{color:#E4E4FF;border-color:#3C3C78}
.pr-ico{width:14px;height:14px;flex:0 0 14px}
.pr-desc{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.9em;margin:0 14px 8px;color:#C5CDD8;font-size:14px;line-height:1.45}
.pr-when{margin:0 14px 8px;color:#C5CDD8;font-size:13px;line-height:1.4}
.pr-more{margin:0 14px 10px}
.pr-more summary{cursor:pointer;color:#E4E4FF;font-size:13.5px;font-weight:650;list-style:none}
.pr-more summary::-webkit-details-marker{display:none}
.pr-more .pr-hide{display:none}
.pr-more[open] .pr-show{display:none}
.pr-more[open] .pr-hide{display:inline}
.pr-code{white-space:pre-wrap;overflow-wrap:anywhere;background:#0E1015;color:#E8EAF0;border:1px solid #2A2F3A;border-radius:10px;padding:12px;font-size:13px;line-height:1.5;margin:8px 0 0;max-height:220px;overflow:auto}
.pr-foot{display:flex;align-items:center;gap:8px;margin-top:auto;padding:0 14px 14px}
.pr-card .pr-copy{flex:1;min-width:0;min-height:44px;margin:0;background:#4338CA;color:#fff;border-color:#4338CA}
.pr-card .pr-copy:hover{background:#5145E5;border-color:#5145E5;color:#fff}
.pr-share{flex:0 0 44px;width:44px;height:44px;padding:0;display:inline-flex;align-items:center;justify-content:center;border-radius:10px;border:1px solid #3A4150;background:#0E1015;color:#E8EAF0;cursor:pointer}
.pr-share:hover,.pr-share[data-done]{border-color:#9393FF;color:#fff;box-shadow:0 0 12px rgba(147,147,255,.45)}
.pr-cta{border:1px solid var(--line);border-radius:12px;padding:16px 18px;background:var(--card);margin:20px 0}
.pr-cta h2{margin:0 0 6px;font-size:17px}.pr-cta p{margin:0 0 10px}
</style>"""

JS = """<script id="pr-js">(function(){
function copyText(txt, done){
  function fb(){var ta=document.createElement("textarea");ta.value=txt;document.body.appendChild(ta);ta.select();
    try{document.execCommand("copy");done()}catch(e){}document.body.removeChild(ta)}
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(done,fb)}else{fb()}
}
document.querySelectorAll("[data-copy]").forEach(function(b){
  b.addEventListener("click",function(){var c=b.closest(".pr-card");var t=c?c.querySelector(".pr-code"):null;
    if(!t)return;var o=b.textContent;
    copyText(t.textContent,function(){b.textContent="Copied";setTimeout(function(){b.textContent=o},2000)})});
});
document.querySelectorAll("[data-share]").forEach(function(b){
  b.addEventListener("click",function(){
    var url=location.href.split("#")[0]+"#"+b.getAttribute("data-share");
    copyText(url,function(){b.setAttribute("data-done","1");setTimeout(function(){b.removeAttribute("data-done")},2000)});
  });
});
})();</script>"""

esc = html.escape


def _asset_v():
    m = re.search(r'ASSET_V\s*=\s*"([^"]+)"', open("build_tasks.py", encoding="utf-8").read())
    return m.group(1) if m else "0"


def _social_image(head, image, alt):
    """Replace the template's default share image with one absolute thumbnail URL."""
    slots = (
        ('<meta property="og:image" content="', image),
        ('<meta property="og:image:width" content="', "1200"),
        ('<meta property="og:image:height" content="', "675"),
        ('<meta property="og:image:alt" content="', esc(alt)),
        ('<meta name="twitter:image" content="', image),
    )
    for prefix, value in slots:
        start = head.find(prefix)
        if start < 0:
            raise SystemExit(f"prompt pages: missing {prefix}")
        end = head.find('"', start + len(prefix))
        head = head[:start + len(prefix)] + value + head[end:]
    return head


def _shell(title, desc, canon, body, ld, image, image_alt):
    """Same head/nav/footer slicing as build_extras.shell (see module docstring)."""
    tpl = open("data/detail.tpl", encoding="utf-8").read()
    head = _social_image(tpl.split("<title>")[0].replace("../", "../"), image, image_alt)
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


def _icon(cat):
    if cat == "coding-agents":
        return ('<svg class="pr-ico" viewBox="0 0 16 16" aria-hidden="true">'
                '<path d="M6 3.5 2.5 8 6 12.5M10 3.5 13.5 8 10 12.5" fill="none" '
                'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    if cat == "mcp":
        return ('<svg class="pr-ico" viewBox="0 0 16 16" aria-hidden="true">'
                '<circle cx="3.5" cy="8" r="1.5" fill="currentColor"/>'
                '<circle cx="12.5" cy="3.5" r="1.5" fill="currentColor"/>'
                '<circle cx="12.5" cy="12.5" r="1.5" fill="currentColor"/>'
                '<path d="M5 8h3.2a2.2 2.2 0 0 0 2.2-2.2V5M8.2 8a2.2 2.2 0 0 1 2.2 2.2v1.2" '
                'fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>')
    return ('<svg class="pr-ico" viewBox="0 0 16 16" aria-hidden="true">'
            '<rect x="2" y="3" width="12" height="10" rx="1.6" fill="none" stroke="currentColor" stroke-width="1.4"/>'
            '<path d="M2 6.2h12" stroke="currentColor" stroke-width="1.4"/></svg>')


_SHARE = ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" '
          'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
          '<path d="M12 4v10"/><path d="m8 8 4-4 4 4"/><path d="M6 13v5a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2v-5"/></svg>')


def _agent_tags(p):
    """Category plus up to two named agents from works_with. Skips a catch-all like 'any MCP client'."""
    names = []
    for part in p["works_with"].split(","):
        name = part.strip()
        if name and not name.lower().startswith("any "):
            names.append(name)
    return names[:2]


def _when_repeats_desc(p):
    """True when the when-line mostly restates the description."""
    stop = {"a", "an", "the", "to", "of", "and", "or", "you", "your", "it", "is", "with", "for", "on", "in"}
    def words(s):
        return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in stop and len(w) > 2]
    desc, when = set(words(p["desc"])), words(p["when"])
    if not when:
        return True
    def hit(w):
        return w in desc or any(len(d) > 3 and (w.startswith(d[:5]) or d.startswith(w[:5])) for d in desc)
    return sum(hit(w) for w in when) / len(when) >= 0.65


def _tabs(current):
    items = [("index.html", "All prompts", "index")]
    items += [(f"{c}.html", CATS[c][0], c) for c in CATS]
    links = []
    for href, label, key in items:
        current_attr = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{href}"{current_attr}>{esc(label)}</a>')
    return '<nav class="pr-nav" aria-label="Prompt categories">' + "".join(links) + "</nav>"


def _card(p):
    slug = p["slug"]
    chips = (f'<span class="pr-chip cat">{_icon(p["category"])}{esc(CATS[p["category"]][0])}</span>'
             + "".join(f'<span class="pr-chip">{esc(name)}</span>' for name in _agent_tags(p)))
    badge = (f'<span class="pr-badge">{esc(p["badge"])}</span>' if p.get("badge") else "")
    when = "" if _when_repeats_desc(p) else f'<p class="pr-when">Use it when: {esc(p["when"])}</p>'
    return (f'<article class="pr-card" id="{esc(slug)}">'
            f'<div class="pr-lead">'
            f'<img class="pr-thumb" src="../{esc(p["thumb"])}" alt="{esc(THUMB_ALT[slug])}" '
            f'width="1200" height="675" loading="lazy">'
            f'{badge}'
            f'<h3>{esc(p["title"])}</h3>'
            f'<p class="pr-tags">{chips}</p>'
            f'<p class="pr-desc">{esc(p["desc"])}</p>'
            f'</div>'
            f'{when}'
            f'<details class="pr-more"><summary>'
            f'<span class="pr-show">Show prompt</span><span class="pr-hide">Hide prompt</span>'
            f'</summary><pre class="pr-code">{esc(p["prompt"])}</pre></details>'
            f'<div class="pr-foot">'
            f'<button type="button" class="btn pr-copy" data-copy>Copy prompt</button>'
            f'<button type="button" class="pr-share" data-share="{esc(slug)}" '
            f'aria-label="Copy link to this prompt">{_SHARE}</button>'
            f'</div>'
            f'</article>')


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


def _page_for(rel):
    """Site-relative path of the HTML file a sitemap rel names."""
    if rel.endswith("/"):
        return rel + "index.html"
    return rel


def _canonical(path):
    """Canonical URL from the page head, or None when the file has none."""
    if not path or not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        head = fh.read(20000)
    m = re.search(r'<link rel="canonical" href="([^"]+)"', head)
    return m.group(1) if m else None


def _loc_for(rel):
    """Sitemap loc is the page canonical.

    A directory index is listed at the URL the page declares. prompts/index.html
    is served as /prompts/, so the loc is https://agentscouthq.com/prompts/
    and not .../prompts/index.html.
    """
    canon = _canonical(_page_for(rel))
    if canon:
        return canon
    return SITE + "/" + rel


def _align_index_html_locs(text):
    """Rewrite every sitemap loc that ends in /index.html when it is not the page canonical.

    lastmod is kept. The row is dropped only when that canonical is already listed,
    so a correction does not add a second URL. A loc whose canonical matches
    (tasks/index.html) is left as it is.
    """
    existing = set(re.findall(r"<loc>([^<]+)</loc>", text))
    out = []
    for line in text.splitlines(True):
        m = re.search(r"<loc>([^<]+)</loc>", line)
        if not m or not m.group(1).endswith("/index.html"):
            out.append(line)
            continue
        loc = m.group(1)
        rel = loc[len(SITE) + 1:] if loc.startswith(SITE + "/") else ""
        canon = _canonical(rel) if rel.endswith("/index.html") else None
        if not canon or canon == loc:
            out.append(line)
            continue
        if canon in existing:
            existing.discard(loc)
            continue
        out.append(line.replace(f"<loc>{loc}</loc>", f"<loc>{canon}</loc>", 1))
        existing.discard(loc)
        existing.add(canon)
    return "".join(out)


def _sitemap_add(rels):
    """Append indexable canonical URLs, same pattern as build_lighten._sitemap_add.

    Directory indexes use the page canonical. An older /index.html loc that
    does not match its page is replaced in place.
    """
    p = "sitemap.xml"
    if not os.path.exists(p) or not rels:
        return 0
    original = open(p, encoding="utf-8").read()
    s = _align_index_html_locs(original)
    day = pacific.today().isoformat()
    extra = ""
    for rel in rels:
        loc = _loc_for(rel)
        if loc in s:
            continue
        extra += f'  <url><loc>{loc}</loc><lastmod>{day}</lastmod></url>\n'
    if extra:
        s = s.replace("</urlset>", extra + "</urlset>")
    if s != original:
        open(p, "w", encoding="utf-8").write(s)
    return extra.count("<url>")


def _thumb_url(p):
    return f"{SITE}/{p['thumb']}"


def _assert_cards(html, expected, label):
    """Each card's image slug matches that card, and the title and description sit under it."""
    cards = re.findall(r'<article class="pr-card" id="([^"]+)">(.*?)</article>', html, re.S)
    slugs = [slug for slug, _ in cards]
    want = [p["slug"] for p in expected]
    if slugs != want:
        raise SystemExit(f"{label}: card order {slugs} != {want}")
    for slug, body in cards:
        prompt = next(p for p in expected if p["slug"] == slug)
        lead = re.search(r'<div class="pr-lead">(.*?)</div>', body, re.S)
        if not lead:
            raise SystemExit(f"{label}: {slug} has no lead")
        block = lead.group(1)
        img = re.search(
            r'<img class="pr-thumb" src="([^"]+)" alt="[^"]*" width="1200" height="675" loading="lazy">',
            block)
        if not img:
            raise SystemExit(f"{label}: {slug} missing thumb img")
        src_slug = img.group(1).rsplit("/", 1)[-1].removesuffix(".webp")
        if src_slug != slug:
            raise SystemExit(f"{label}: img {img.group(1)} does not match card {slug}")
        img_at, h3_at, desc_at = block.find("<img"), block.find("<h3>"), block.find('class="pr-desc"')
        if not (0 <= img_at < h3_at < desc_at):
            raise SystemExit(f"{label}: {slug} image, title, and description are out of order")
        if f'<h3>{esc(prompt["title"])}</h3>' not in block or esc(prompt["desc"]) not in block:
            raise SystemExit(f"{label}: {slug} title or description missing under the image")
    return len(cards)


def run():
    prompts = json.load(open(DATA, encoding="utf-8"))
    seen = set()
    for p in prompts:
        assert p["category"] in CATS, f"unknown category {p['category']} on {p['id']}"
        assert p["slug"] not in seen, f"duplicate slug {p['slug']}"
        assert p["prompt"].strip() and p["title"].strip(), f"empty prompt {p['id']}"
        expect = f"assets/prompts/thumbs/{p['slug']}.webp"
        assert p.get("thumb") == expect, f"thumb path {p.get('thumb')} != {expect}"
        assert os.path.isfile(p["thumb"]), f"missing {p['thumb']}"
        assert p["slug"] in THUMB_ALT, f"no alt for {p['slug']}"
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
            f'{_tabs("index")}<div class="pr-cats">{cards}</div>{sections}{_cta()}'
            '<p>Related: <a href="../best/ai-coding-agents.html">Best AI coding agents</a> \u00b7 '
            '<a href="../s/best-mcp-servers.html">Best MCP servers</a> \u00b7 '
            '<a href="../best/ai-browser-agents.html">Best AI browser agents</a> \u00b7 '
            '<a href="../bot-templates/">AI bot templates</a></p>' + JS)
    canon = f"{SITE}/{D}/"
    ld = _ld("Prompt library for AI agents", LANDING_DESC, canon,
             [("AgentScout", SITE + "/"), ("Prompt library", canon)],
             [(p["title"], f"{canon}#{p['slug']}") for p in prompts])
    cover = prompts[0]
    page = _shell(LANDING_TITLE, LANDING_DESC, canon, body, ld,
                  _thumb_url(cover), THUMB_ALT[cover["slug"]])
    checked = _assert_cards(page, prompts, "prompts/index.html")
    open(f"{D}/index.html", "w", encoding="utf-8").write(page)
    # Canonical is the directory URL (https://agentscouthq.com/prompts/), not the file path.
    rels.append(f"{D}/")

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
                f'{_tabs(c)}'
                '<div class="pr-grid">' + "".join(_card(p) for p in by_cat[c]) + '</div>'
                f'<p>More prompts: <a href="index.html">All prompts</a> \u00b7 {others}</p>'
                f'{_cta()}{_related(c)}' + JS)
        canon = f"{SITE}/{D}/{c}.html"
        ld = _ld(f"{name} prompts", desc, canon,
                 [("AgentScout", SITE + "/"), ("Prompt library", SITE + f"/{D}/"),
                  (f"{name} prompts", canon)],
                 [(p["title"], f"{canon}#{p['slug']}") for p in by_cat[c]])
        cover = by_cat[c][0]
        page = _shell(title, desc, canon, body, ld, _thumb_url(cover), THUMB_ALT[cover["slug"]])
        checked += _assert_cards(page, by_cat[c], f"prompts/{c}.html")
        open(f"{D}/{c}.html", "w", encoding="utf-8").write(page)
        rels.append(f"{D}/{c}.html")

    if checked != len(prompts) + sum(len(v) for v in by_cat.values()):
        raise SystemExit(f"card check count {checked}")
    added = _sitemap_add(rels)
    print(f"prompts: {len(prompts)} prompts, {len(rels)} pages, sitemap +{added}, "
          f"card thumbs checked {checked}")
    return {"prompts": len(prompts), "pages": len(rels), "sitemap_added": added, "cards_checked": checked}


if __name__ == "__main__":
    run()
