"""Homepage stats, how-it-started, free tools, badges, launch board, Launch Pack, Fast-Track IndexNow line.
Run: python3 scripts/apply_growth.py
Numbers on the stats bar and the origin page are read from api/metrics.json and tools.json at build time.
"""
import datetime, html, json, os, re
from zoneinfo import ZoneInfo

import build_extras as X
import build_sponsor as BS
import build_status

B = X.B
e = X.e
PT = ZoneInfo("America/Los_Angeles")
TODAY = datetime.datetime.now(PT).date()
FAST = "https://buy.stripe.com/3cIaEY6T15hlfJr135e7m0e"
NL = ('<section id="nlblock" class="nlwrap"><div class="wrap"><div class="nlbox"><div class="nltxt"><h2>AgentScout Weekly + Free 50 AI Agents &amp; 50 MCP Servers Cheat Sheets</h2>'
      '<p>Get the 5 best new AI agent tools, copy-paste MCP workflows, and our high-res 50 AI Agents &amp; 50 MCP Servers Cheat Sheet Pack free every Tuesday — plus daily founder stack teardowns on X from <a href="https://x.com/intent/user?screen_name=clampdown19" target="_blank" rel="noopener noreferrer"><b>@clampdown19</b></a> &amp; <a href="https://x.com/intent/user?screen_name=AgentScoutHQ" target="_blank" rel="noopener noreferrer"><b>@AgentScoutHQ</b></a>.</p></div>'
      '<div class="nlgo" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center">'
      '<a class="btn primary" href="https://agentscout.beehiiv.com/subscribe?utm_source=agentscout&amp;utm_medium=website&amp;utm_campaign=newsletter" target="_blank" rel="noopener noreferrer" data-nl>Get Free 50-Tool Cheat Sheet →</a>'
      '<a class="btn" href="https://x.com/intent/user?screen_name=clampdown19" target="_blank" rel="noopener noreferrer">Follow @clampdown19 on X ↗</a>'
      '<a class="btn" href="https://x.com/intent/user?screen_name=AgentScoutHQ" target="_blank" rel="noopener noreferrer">Follow @AgentScoutHQ ↗</a>'
      '</div></div></div></section>')
SIGNUP = ('<aside class="nlin" aria-label="Newsletter signup"><h2>Email me maker notes</h2>'
          '<p>The score stays on this page. Subscribe if you want the Tuesday maker brief. One email. Unsubscribe anytime.</p>'
          '<form class="nlgo" action="https://agentscout.beehiiv.com/subscribe" method="get" target="_blank" data-nlform>'
          '<input type="hidden" name="utm_source" value="agentscout"><input type="hidden" name="utm_medium" value="roast">'
          '<label class="sr-only" for="nl-roast-email">Email</label>'
          '<input id="nl-roast-email" name="email" type="email" required autocomplete="email" maxlength="120" placeholder="you@example.com">'
          '<button class="btn primary" type="submit">Subscribe free</button></form></aside>')
CHECK_SIGNUP = SIGNUP.replace("nl-roast-email", "nl-check-email").replace('name="utm_medium" value="roast"', 'name="utm_medium" value="checklist"').replace("The score stays on this page. ", "Your checklist stays in this browser. ")


def pt_today():
    return datetime.datetime.now(PT).date()


def week_span(day):
    start = day - datetime.timedelta(days=day.weekday())
    end = start + datetime.timedelta(days=6)
    iso = start.isocalendar()
    return start, end, f"{iso.year}-w{iso.week:02d}"


def fmt_day(day):
    return day.strftime("%b %-d, %Y")


def fmt_short(day):
    return day.strftime("%b %-d")


# A week earns #N badges only after that Pacific Sunday, and not before 2026-11-01.
# Earlier weeks had no vote log, so backfilling a rank would invent one.
RANK_NOT_BEFORE = datetime.date(2026, 11, 1)
PAGE_SIZE = 100


def load_tools():
    return json.load(open("tools.json", encoding="utf-8"))


def load_metrics(tools):
    m = json.load(open("api/metrics.json", encoding="utf-8"))
    import build_bot_templates
    m["templates_count"] = int(build_bot_templates.live_bot_template_count() or m.get("templates_count") or 0)
    m["tools_count"] = int(m.get("tools_count") or len(tools))
    m["mcp_servers_count"] = int(m.get("mcp_servers_count") or sum(1 for x in tools if x.get("category") == "MCP servers"))
    m["x_combined_followers"] = int(m.get("x_combined_followers") or 0)
    json.dump(m, open("api/metrics.json", "w", encoding="utf-8"), indent=2)
    open("api/metrics.json", "a", encoding="utf-8").write("\n")
    return m


def comma(n):
    return f"{int(n):,}"


def finish_page(path, html_text):
    import ga4
    html_text = html_text.replace('<main class="wrap">', '<main class="wrap" data-pagefind-body>', 1)
    html_text = ga4.apply(html_text, path)
    if 'id="nlblock"' not in html_text and "<footer" in html_text:
        html_text = html_text.replace("<footer", NL + "<footer", 1)
    open(path, "w", encoding="utf-8").write(html_text)


def stats_bar(m):
    s = open("index.html", encoding="utf-8").read()
    bar = (
        f'<div class="stats" id="dir-stats">'
        f'<a href="categories/index.html"><b id="s-total">{comma(m["tools_count"])}</b> tools</a>'
        f'<a href="categories/mcp-servers.html"><b>{comma(m["mcp_servers_count"])}</b> MCP servers</a>'
        f'<a href="mcp/status/">MCP status</a>'
        f'<a href="bot-templates/"><b>{comma(m["templates_count"])}</b> templates</a>'
        f'<a href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer"><b>{comma(m["x_combined_followers"])}</b> combined followers</a>'
        f'<a href="how-it-started.html">How it started</a></div>'
    )
    s2, n = re.subn(r'<div class="stats">.*?</div>', bar, s, count=1, flags=re.S)
    if not n:
        raise SystemExit("stats bar not found on index.html")
    s2 = s2.replace(
        '$("s-new").textContent=d.filter(t=>t.new).length;$("s-cats").textContent=Object.keys(cats).length;',
        'var sn=$("s-new");if(sn)sn.textContent=d.filter(t=>t.new).length;var sc=$("s-cats");if(sc)sc.textContent=Object.keys(cats).length;',
    )
    open("index.html", "w", encoding="utf-8").write(s2)


def how_it_started(tools, m):
    seed = [x for x in tools if x.get("seed") and x.get("added")]
    dates = sorted(x["added"] for x in seed)
    seed_n, seed_a, seed_b = len(seed), dates[0] if dates else "", dates[-1] if dates else ""
    title = "How AgentScout started · AgentScout"
    desc = "Founder-run, mostly automated with AI agents. @clampdown19 (m lk) makes the calls. Counts come from the directory metrics file."
    body = f'''<div class="crumb"><a href="index.html">AgentScout</a> / How it started</div>
<section style="padding-top:20px;text-align:left;max-width:760px">
<h1 style="text-align:left">How it started</h1>
<p class="lede" style="margin-left:0;text-align:left">Founder-run, mostly automated with AI agents.</p>
<p>I'm <a href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer">@clampdown19</a> (m lk). I make the calls. AI agents do most of the daily work: tool checks, listings, link and status checks, and reports.</p>
<p>The starting catalog is {seed_n:,} tools dated {e(seed_a)} through {e(seed_b)}. As of {e(m.get("updated_display") or m.get("updated"))}, this site lists {comma(m["tools_count"])} tools, including {comma(m["mcp_servers_count"])} MCP servers, and {comma(m["templates_count"])} templates. Combined followers of @clampdown19 and @AgentScoutHQ: {comma(m["x_combined_followers"])}. Those figures are read from <a href="api/metrics.json">api/metrics.json</a> and the directory file when the page is built.</p>
<p>Listing prices are $0, $15, $49, and $99 per week. The <a href="submit.html#launch-pack">Directory Launch Pack</a> is a separate $49 add-on, not a listing tier.</p>
<p>MCP server links are checked at 7 AM and 7 PM Pacific. The <a href="mcp/status/">status page</a> shows up, down, and not-yet-checked counts from those checks. Updated twice daily, 7 AM &amp; 7 PM PT. A server with no check on file stays not yet checked.</p>
<p>More: <a href="about.html">About</a> · <a href="launches/">This week's launches</a> · <a href="submit.html">Submit a tool</a>.</p>
</section>'''
    ld = {"@context": "https://schema.org", "@type": "AboutPage", "name": title, "description": desc, "url": B + "how-it-started.html"}
    finish_page("how-it-started.html", X.shell("", title, desc, B + "how-it-started.html", body, ld))


def paid(x):
    tier = str(x.get("listing_tier") or "").lower().replace("-", "_")
    return bool(x.get("fast_track") or tier in ("fast_track", "category_pin", "featured_49", "sponsor", "weekly_sponsor"))


def week_tools(tools, start, end, current=False):
    rows = [x for x in tools if not x.get("seed") and start.isoformat() <= (x.get("added") or "") <= end.isoformat()]
    if current:
        have = {x["slug"] for x in rows}
        rows += [x for x in tools if paid(x) and x["slug"] not in have]
    rows.sort(key=lambda x: (x.get("added") or "", x.get("name") or ""), reverse=True)
    return rows


def launch_svg(slug, rank, label):
    os.makedirs("badges/launch", exist_ok=True)
    text = html.escape(f"#{rank} this week")
    sub = html.escape(label)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="260" height="54" viewBox="0 0 260 54" role="img" aria-label="Launched on AgentScout, {text}">
<rect x=".5" y=".5" width="259" height="53" rx="10" fill="#111111" stroke="#2a2a30"/>
<circle cx="24" cy="25" r="9" fill="none" stroke="#ffffff" stroke-width="3"/><path d="M31 32l7 7" stroke="#ffffff" stroke-width="3.2" stroke-linecap="round"/>
<path d="M24 19l1.6 4.4L30 25l-4.4 1.6L24 31l-1.6-4.4L18 25l4.4-1.6z" fill="#5B5BF7"/>
<text x="46" y="22" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="10" font-weight="600" letter-spacing=".06em" fill="#a9a9b6">LAUNCHED ON AGENTSCOUT</text>
<text x="46" y="40" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="15" font-weight="700" fill="#ffffff">{text} · {sub}</text></svg>'''
    open(f"badges/launch/{slug}.svg", "w", encoding="utf-8").write(svg)


def clear_launch_svgs():
    folder = "badges/launch"
    if not os.path.isdir(folder):
        return
    for fn in os.listdir(folder):
        if fn.endswith(".svg"):
            os.remove(os.path.join(folder, fn))


def closed_rank_week(tools):
    """Latest ISO week that has fully ended in PT and is eligible for a rank badge."""
    today = pt_today()
    best = None
    for x in tools:
        if x.get("seed") or not x.get("added"):
            continue
        try:
            a, b, w = week_span(datetime.date.fromisoformat(x["added"]))
        except ValueError:
            continue
        if b < today and b >= RANK_NOT_BEFORE and (best is None or b > best[1]):
            best = (a, b, w)
    return best


def assign_ranks(tools):
    """#N this week only after the Pacific week has ended. Nothing is backfilled."""
    X.LAUNCH_RANKS.clear()
    clear_launch_svgs()
    found = closed_rank_week(tools)
    if not found:
        return None
    a, b, w = found
    label = f"{fmt_short(a)}–{fmt_short(b)}"
    for i, x in enumerate(week_tools(tools, a, b, current=False)[:10], 1):
        launch_svg(x["slug"], i, label)
        X.LAUNCH_RANKS[x["slug"]] = (i, w, label)
    return found


def _page_name(wid, current, n):
    if current:
        return "index.html" if n == 1 else f"page-{n}.html"
    return f"{wid}.html" if n == 1 else f"{wid}-p{n}.html"


def launch_page(tools, start, end, wid, current):
    rows = week_tools(tools, start, end, current=current)
    label = f"{fmt_short(start)} – {fmt_day(end)}"
    open_week = end >= pt_today()
    weeks = sorted({week_span(datetime.date.fromisoformat(x["added"]))[2] for x in tools if not x.get("seed") and x.get("added")})
    other = " · ".join(f'<a href="{w}.html">{e(w)}</a>' for w in weeks if w != wid)
    if current:
        other = f'<a href="{wid}.html">This week’s archive</a>' + ((" · " + other) if other else "")
    pages = [rows[i:i + PAGE_SIZE] for i in range(0, len(rows), PAGE_SIZE)] or [[]]
    npages = len(pages)
    indexable = current or len(rows) >= 10
    urls = []
    os.makedirs("launches", exist_ok=True)
    for n, chunk in enumerate(pages, 1):
        name = _page_name(wid, current, n)
        path = f"launches/{name}"
        canon = B + ("launches/" if current and n == 1 else f"launches/{name}")
        if open_week:
            h1 = f"AI agent tools launched this week ({label})"
        else:
            h1 = f"AI agent tools launched {label}"
        if n > 1:
            h1 += f", page {n}"
        title = f"Launches {fmt_short(start)}–{fmt_short(end)}"
        if n > 1:
            title += f" p{n}"
        title += " · AgentScout"
        if len(title) > 60:
            title = title[:60].rsplit(" ", 1)[0]
        names = ", ".join(x["name"] for x in chunk[:3]) or "none yet"
        desc = f"{len(rows)} tools added {label}."
        if npages > 1:
            desc += f" Page {n} of {npages}."
        ranked = "Ranked by votes this week, then by the date added." if open_week else "Ranked by that week’s votes, then by the date added."
        desc = (desc + " " + ranked + f" Top: {names}.")[:156]
        when = "this week" if open_week else label
        top = chunk[:3]
        qa = (f"The newest additions on this page are {e(', '.join(x['name'] for x in top))}." if top else "No tools were added in this week.")
        qa += f" This page covers tools launched {e(when)}. Vote counts start at zero and come from the server, one vote per visitor per day. Ties stay in the order the tools were added, newest first."
        items = []
        list_items = []
        offset = (n - 1) * PAGE_SIZE
        for i, x in enumerate(chunk, 1):
            pos = offset + i
            flag = '<span class="b">Fast-Track</span>' if paid(x) else ""
            items.append(
                f'<li class="lb-row" data-slug="{e(x["slug"])}" data-added="{e(x.get("added") or "")}">'
                f'<b class="lb-pos">{pos}</b><div><a href="../tools/{e(x["slug"])}.html"><b>{e(x["name"])}</b></a>'
                f'<div class="lb-meta">{e(x.get("category") or "")} · added {e(x.get("added") or "")} {flag}</div>'
                f'<p style="margin:4px 0 0">{e(x.get("description") or "")}</p></div>'
                f'<div class="lb-vote"><button class="vote" data-vote="{e(x["slug"])}" aria-pressed="false" title="Upvote (one per visitor per day)"><span>0</span></button>'
                f'<span class="muted" data-today>+0 today</span></div></li>'
            )
            list_items.append({"@type": "ListItem", "position": pos, "name": x["name"], "url": f"{B}tools/{x['slug']}.html"})
        def href(k):
            return _page_name(wid, current, k) if 1 <= k <= npages else ""
        pager = ""
        if npages > 1:
            prev_h, next_h = href(n - 1), href(n + 1)
            bits = [f'<span>Page {n} of {npages}</span>']
            if prev_h:
                bits.append(f'<a href="{prev_h}" rel="prev">Previous</a>')
            if next_h:
                bits.append(f'<a href="{next_h}" rel="next">Next</a>')
            pager = f'<p class="lb-pager">{"".join(bits)}</p>'
        body = f'''<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="./">Launches</a> / {e(label)}</div>
<section class="lb-board" style="padding-top:20px;text-align:left">
<h1 style="text-align:left">{e(h1)}</h1>
<p class="lede" style="margin-left:0;text-align:left">{e(desc)}</p>
<p><b>Quick answer:</b> {qa}</p>
<p>Today’s votes on this page: <b data-today-total>0</b>. <a href="../new.html">New tools, last 30 days</a> · <a href="../submit.html">Submit free</a> · <a href="{FAST}">Fast-Track ($15)</a></p>
{pager}
<ol style="list-style:none;padding:0;margin:12px 0">{"".join(items) or "<li>No tools were added in this week.</li>"}</ol>
{pager}
<p class="muted">Other weeks: {other or "—"}</p>
</section>'''
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "CollectionPage", "name": h1, "description": desc, "url": canon},
            {"@type": "ItemList", "name": h1, "numberOfItems": len(chunk), "itemListElement": list_items},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "AgentScout", "item": B},
                {"@type": "ListItem", "position": 2, "name": "Launches", "item": B + "launches/"},
                {"@type": "ListItem", "position": 3, "name": label if n == 1 else f"{label}, page {n}", "item": canon},
            ]},
        ]}
        page = X.shell("../", title, desc, canon, body, ld)
        extra = ""
        if not indexable:
            extra += '<meta name="robots" content="noindex,follow">'
        if current and n == 2:
            extra += f'<link rel="prev" href="{B}launches/">'
        elif href(n - 1):
            extra += f'<link rel="prev" href="{B}launches/{href(n - 1)}">'
        if href(n + 1):
            extra += f'<link rel="next" href="{B}launches/{href(n + 1)}">'
        if extra:
            page = page.replace("</head>", extra + "</head>", 1)
        finish_page(path, page)
        if indexable:
            urls.append(canon)
    return urls


def launches(tools):
    assign_ranks(tools)
    if os.path.isdir("launches"):
        for fn in os.listdir("launches"):
            if re.fullmatch(r"page-\d+\.html", fn) or re.fullmatch(r"\d{4}-w\d{2}-p\d+\.html", fn):
                os.remove(os.path.join("launches", fn))
    start, end, wid = week_span(pt_today())
    seen = {}
    for x in tools:
        if x.get("seed") or not x.get("added"):
            continue
        a, b, w = week_span(datetime.date.fromisoformat(x["added"]))
        seen[w] = (a, b)
    seen[wid] = (start, end)
    urls = []
    for w, (a, b) in sorted(seen.items()):
        urls += launch_page(tools, a, b, w, current=False)
        if w == wid:
            urls += launch_page(tools, a, b, w, current=True)
    # shell() copies data/detail.tpl, whose Submit button is the old GitHub issue form.
    # Stamp the shared index.html nav and footer before these pages are considered done.
    import build_seo_new
    build_seo_new.unify_all_nav_and_footer()
    return urls


def patch_tool_badges(tools):
    n = 0
    for x in tools:
        path = f"tools/{x['slug']}.html"
        if not os.path.exists(path):
            continue
        s = open(path, encoding="utf-8").read()
        start = s.find(">Badge for makers</h2>")
        start2 = s.find(">Get your badge</h2>")
        anchor = start if start >= 0 else start2
        if anchor < 0:
            continue
        h = s.rfind("<h2", 0, anchor)
        i = s.find('<div class="embeds">', h)
        if i < 0:
            continue
        depth = 0
        j = i
        end = None
        while j < len(s):
            if s.startswith("<div", j):
                depth += 1
                j = s.find(">", j) + 1
                continue
            if s.startswith("</div>", j):
                depth -= 1
                j += 6
                if depth == 0:
                    end = j
                    break
                continue
            j += 1
        if end is None:
            continue
        block = X.badge_html(x, "../")
        s = s[:h] + block + s[end:]
        if 'class="botstore-cta"' not in s:
            cta = ('<aside class="botstore-cta" aria-label="AgentScout Bot Store"><p class="lp-kicker">Bot Store</p>'
                   '<p>Separate from this listing. <a href="../bot-store/">AI Agent Packs from $35</a>. Flagship Pro Bots $39–$149.</p>'
                   '<p style="margin:8px 0 0"><a class="btn" href="../bot-store/">Browse the Bot Store</a></p></aside>')
            s = s.replace(block, cta + block, 1)
        s = s.replace("Upvotes and saves stay on this device.", "Saves stay on this device. Upvotes are one per visitor per day.")
        open(path, "w", encoding="utf-8").write(s)
        n += 1
    print("badge boxes", n)


def badge_page_note():
    path = "badges.html"
    if not os.path.exists(path):
        return
    s = open(path, encoding="utf-8").read()
    note = ('<h2 style="font-size:18px;margin:32px 0 8px">#N this week</h2>'
            '<p>After a Pacific week has ended (Monday through Sunday), the top 10 tools on that week’s <a href="launches/">launch board</a> get a badge with the rank and the week baked into the image, so it still says the truth later. '
            'A week that is still open does not get a rank badge. Showing a badge is a thank-you. It does not change your rank and it does not earn a Featured spot.</p>')
    if "#N this week" not in s:
        s = s.replace("<h2 id=\"featured-badge\"", note + "<h2 id=\"featured-badge\"", 1)
        if "#N this week" not in s:
            s = s.replace("</section>", note + "</section>", 1)
    s = s.replace("makers who show the badge get a free Featured spot", "thank you for listing — the badge is optional and does not change placement")
    open(path, "w", encoding="utf-8").write(s)


def tool_card(slug, name, desc, icon):
    return (f'<div class="card tile" style="position:relative"><a class="stretch" href="free-tools/{slug}.html" aria-label="{e(name)}"></a>'
            f'<div class="ct"><span class="ico"><span aria-hidden="true">{icon}</span></span><div class="tn"><h3>{e(name)}</h3><div class="badges"><span class="b new">Free</span></div></div></div>'
            f'<p class="hook">{e(desc)}</p></div>')


def free_tools():
    os.makedirs("free-tools", exist_ok=True)
    roast_inner = f'''<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="../free-tools.html">Free tools</a> / Roast My AI Tool Listing</div>
<section style="padding-top:20px;text-align:left;max-width:860px"><h1 style="text-align:left">Roast My AI Tool Listing</h1>
<p class="lede" style="margin-left:0;text-align:left">Paste a tool URL. We fetch the public page and score the title, one-line pitch, pricing clarity, OG image, JSON-LD, llms.txt, and whether AgentScout already lists it.</p>
<p class="muted">The URL is sent to the AgentScout worker so it can fetch the page. No paid APIs. Private and local addresses are blocked.</p>
<div style="border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:18px 0;background:var(--card)">
<form id="rf"><label style="display:block;margin:0 0 6px;font-weight:600" for="ru">Tool URL</label>
<div style="display:flex;gap:8px;flex-wrap:wrap"><input id="ru" inputmode="url" autocomplete="url" placeholder="https://example.com" style="flex:1 1 220px;min-width:0;min-height:44px;padding:0 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text);font:inherit;box-sizing:border-box">
<button class="btn primary" id="rb" type="submit">Score this listing</button></div></form></div>
<div id="rout" aria-live="polite"></div>
{SIGNUP}
</section><script src="../free_tools_js/roast.js"></script>'''
    check_items = [
        ("pitch", "Write a one-line pitch a stranger can repeat."),
        ("price", "Put pricing on the page: free, paid, or a link to the price."),
        ("title", "Set a page title and a meta description."),
        ("og", "Add an Open Graph image."),
        ("jsonld", "Add JSON-LD (SoftwareApplication or Organization)."),
        ("llms", "Publish llms.txt. The free generator can draft one."),
        ("robots", "Do not block the whole site in robots.txt."),
        ("submit", "Submit the tool free on AgentScout, or buy Fast-Track ($15) for same-day review."),
        ("badge", "Optional: add your AgentScout badge. It does not change your rank."),
        ("x", "Post the launch on X."),
        ("news", "Tell your newsletter list."),
        ("index", "Ping Bing and IndexNow. This does not include Google."),
        ("roast", "Run Roast My AI Tool Listing on the URL."),
    ]
    lis = "".join(f'<li><label><input type="checkbox" value="{i}"> {e(lab)}</label></li>' for i, lab in check_items)
    check_inner = f'''<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="../free-tools.html">Free tools</a> / Launch day checklist</div>
<section style="padding-top:20px;text-align:left;max-width:860px"><h1 style="text-align:left">AI Tool Launch Day Checklist</h1>
<p class="lede" style="margin-left:0;text-align:left">Work through launch day. Progress stays in this browser.</p>
<p id="lprog" style="font-weight:700">0 of {len(check_items)} done</p>
<ul class="chk-list" id="lchks">{lis}</ul>
<p><a href="roast-my-ai-tool-listing.html">Roast My AI Tool Listing</a> · <a href="../submit.html">Submit free</a> · <a href="{FAST}">Fast-Track ($15)</a> · <a href="../launches/">This week’s launch board</a></p>
{CHECK_SIGNUP}
</section><script src="../free_tools_js/launch-checklist.js"></script>'''
    pages = [
        ("free-tools/roast-my-ai-tool-listing.html", "Roast My AI Tool Listing (free) · AgentScout", "Score an AI tool URL for title, pitch, pricing, OG image, JSON-LD, llms.txt, and an AgentScout listing. Free.", roast_inner, "roast-my-ai-tool-listing.html"),
        ("free-tools/ai-tool-launch-day-checklist.html", "AI Tool Launch Day Checklist (free) · AgentScout", "Interactive launch-day checklist for an AI tool. Progress stays in your browser. Free.", check_inner, "ai-tool-launch-day-checklist.html"),
    ]
    urls = []
    for path, title, desc, inner, slug in pages:
        canon = B + path
        ld = {"@context": "https://schema.org", "@type": "WebApplication", "name": title.split(" (")[0], "url": canon, "description": desc, "isAccessibleForFree": True, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}}
        finish_page(path, X.shell("../", title, desc, canon, inner, ld))
        urls.append(canon)
    cards = tool_card("roast-my-ai-tool-listing", "Roast My AI Tool Listing", "Paste a URL and get a score plus concrete fixes for the title, pitch, pricing, OG image, schema, llms.txt, and AgentScout listing.", "🔥")
    cards += tool_card("ai-tool-launch-day-checklist", "AI Tool Launch Day Checklist", "Check off directories, IndexNow, an X post, your newsletter, and badges. Progress stays in this browser.", "✅")
    edits = (
        ("free-tools.html", r'(<h2 id="agentscout-tools"[^>]*>.*?<div class="grid">)'),
        ("index.html", r'(<section id="xfree"[^>]*>.*?<div class="grid fill">)'),
    )
    for path, pat in edits:
        if not os.path.exists(path):
            continue
        s = open(path, encoding="utf-8").read()
        if "roast-my-ai-tool-listing.html" not in s:
            s2, n = re.subn(pat, lambda m: m.group(1) + cards, s, count=1, flags=re.S)
            if n:
                s = s2
        s = s.replace("All 18 calculators", "All 20 calculators")
        open(path, "w", encoding="utf-8").write(s)
    return urls


def chrome():
    s = open("index.html", encoding="utf-8").read()
    s = s.replace('<a href="news.html">News</a><a class="navvid"', '<a href="news.html">News</a><a href="launches/">Launches</a><a class="navvid"', 1)
    s = s.replace(
        '<a href="new.html">New tools</a> · <a href="news.html">Agent news</a>',
        '<a href="new.html">New tools</a> · <a href="launches/">Launches</a> · <a href="mcp/status/">MCP status</a> · <a href="news.html">Agent news</a>',
        1,
    )
    tag = " Founder-run, mostly automated with AI agents."
    needle = "We check every link, label pricing as the makers state it, and say so when a claim is unverified."
    if tag.strip() not in s:
        s = s.replace(needle, needle + tag, 1)
    open("index.html", "w", encoding="utf-8").write(s)
    about = open("about.html", encoding="utf-8").read()
    lede = "A curated, link-checked directory of "
    if "Founder-run, mostly automated with AI agents." not in about and lede in about:
        about = about.replace("updated daily.</p>", "updated daily. Founder-run, mostly automated with AI agents.</p>", 1)
        open("about.html", "w", encoding="utf-8").write(about)
    mcp = open("mcp/index.html", encoding="utf-8").read()
    link = ' <a href="status/">MCP server status</a> shows up, down, and not-yet-checked counts. Updated twice daily, 7 AM &amp; 7 PM PT.'
    if "MCP server status" not in mcp:
        mcp = mcp.replace("connect to the free AgentScout MCP server</a>.", "connect to the free AgentScout MCP server</a>." + link, 1)
        open("mcp/index.html", "w", encoding="utf-8").write(mcp)
    new = open("new.html", encoding="utf-8").read()
    if "launches/" not in new.split("<h1", 1)[-1][:800]:
        new = new.replace("</h1>", '</h1><p><a href="launches/">Weekly launch board</a> ranks this week’s tools by server-side votes.</p>', 1)
    def wrap(m):
        slug = m.group(1)
        inner = m.group(2)
        return (f'<div class="card rcard"><a class="stretch" href="tools/{slug}.html">{inner}</a>'
                f'<div class="acts"><button class="vote" data-vote="{slug}" aria-pressed="false" title="Upvote (one per visitor per day)"><span>0</span></button></div></div>')
    new2, n = re.subn(r'<a class="card rcard" href="tools/([a-z0-9-]+)\.html">(.*?)</a>', wrap, new, flags=re.S)
    if n:
        new = new2
    open("new.html", "w", encoding="utf-8").write(new)


def insert_launch_pack():
    block = BS.launch_pack_html()
    targets = {
        "submit.html": '<h2 id="free-form"',
        "sponsor.html": '<div class="pkg-trust">',
        "index.html": "<!--SPONSOR-CTA-END-->",
    }
    for path, anchor in targets.items():
        if not os.path.exists(path):
            continue
        s = open(path, encoding="utf-8").read()
        s = re.sub(r'<aside id="launch-pack".*?</aside>', "", s, count=1, flags=re.S)
        if anchor not in s:
            continue
        s = s.replace(anchor, block + anchor, 1)
        open(path, "w", encoding="utf-8").write(s)


def patch_indexnow(text):
    pairs = [
        ("and a dedicated launch post on @AgentScoutHQ.",
         "and a dedicated launch post on @AgentScoutHQ. Same-day indexing ping to Bing and IndexNow search engines (does not include Google)."),
        ("and a launch post on @AgentScoutHQ.",
         "and a launch post on @AgentScoutHQ, and a same-day indexing ping to Bing and IndexNow search engines (does not include Google)."),
        ("Launch post on @AgentScoutHQ</span>",
         "Launch post on @AgentScoutHQ · Same-day indexing ping to Bing and IndexNow search engines (does not include Google).</span>"),
        ("Launch post on <b>@AgentScoutHQ</b></span>",
         "Launch post on <b>@AgentScoutHQ</b> · <b>Same-day indexing ping to Bing and IndexNow search engines (does not include Google).</b></span>"),
    ]
    for old, new in pairs:
        if old in text and new not in text:
            text = text.replace(old, new)
    bullet = '<li><span class="pkg-chk pkg-chk-fast">⚡</span><span><b>Same-day indexing ping to Bing and IndexNow search engines (does not include Google).</b></span></li>'
    if "pkg-chk-fast" in text and "Same-day indexing ping to Bing and IndexNow search engines (does not include Google).</b> Bing" not in text and "Launch post on X:" in text:
        text = text.replace("Launch post on X:</b>", "Launch post on X:</b>", 1)
        text = re.sub(
            r'(Launch post on X:</b>.*?</li>)',
            lambda m: m.group(1) + bullet if "Same-day indexing ping" not in m.group(1) else m.group(1),
            text,
            count=2,
            flags=re.S,
        )
    return text


def walk_indexnow():
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "preview", "app", "pagefind")]
        for fn in files:
            if not fn.endswith((".html", ".py", ".json", ".txt", ".md", ".yaml", ".yml")):
                continue
            path = os.path.join(root, fn)
            try:
                s = open(path, encoding="utf-8").read()
            except Exception:
                continue
            n = patch_indexnow(s)
            if n != s:
                open(path, "w", encoding="utf-8").write(n)


def sitemap(extra):
    sm = open("sitemap.xml", encoding="utf-8").read()
    sm = re.sub(r"\s*<url><loc>[^<]*mcp/link-status\.html</loc>.*?</url>\n?", "\n", sm)
    day = pt_today().isoformat()
    block = ""
    for u in extra:
        if u not in sm:
            block += f"  <url><loc>{u}</loc><lastmod>{day}</lastmod></url>\n"
    if block:
        sm = sm.replace("</urlset>", block + "</urlset>")

    def keep(m):
        loc = m.group(1)
        if "/launches/" not in loc:
            return m.group(0)
        rel = loc.split("agentscouthq.com/", 1)[-1]
        path = (rel + "index.html") if rel.endswith("/") else rel
        return m.group(0) if os.path.exists(path) else ""

    sm = re.sub(r"  <url><loc>([^<]+)</loc><lastmod>[^<]*</lastmod></url>\n", keep, sm)
    open("sitemap.xml", "w", encoding="utf-8").write(sm)


def llms():
    import build_seo
    build_seo.llms_extra()
    s = open("llms.txt", encoding="utf-8").read()
    if "Directory Launch Pack" not in s:
        s += (
            "\n## Launches, status, and the Directory Launch Pack\n\n"
            f"- [How AgentScout started]({B}how-it-started.html): founder-run, mostly automated with AI agents. @clampdown19 (m lk) makes the calls.\n"
            f"- [Weekly launch board]({B}launches/): tools added each ISO week (Pacific), with server-side upvotes.\n"
            f"- [MCP server status]({B}mcp/status/): up, down, and not-yet-checked counts. Updated twice daily, 7 AM & 7 PM PT.\n"
            f"- [Directory Launch Pack]({B}submit.html#launch-pack): $49 one-time add-on, separate from the four listing tiers ($0 / $15 / $49 / $99/wk). {BS.LAUNCH_PACK_PROMISE} {BS.LAUNCH_PACK_ACCOUNTS} {BS.LAUNCH_PACK_SKIP} {BS.LAUNCH_PACK_LIMITS} Checkout: {BS.LAUNCH_PACK_URL}\n"
            f"- Fast-Track ($15) includes: {BS.FAST_TRACK_INDEX_LINE}\n"
        )
        open("llms.txt", "w", encoding="utf-8").write(s)


def emails(tools):
    os.makedirs("data/outreach", exist_ok=True)
    snippet = (
        '<p>Thank you for your AgentScout listing. If you want to, you can paste this badge on your site or README. '
        'It is optional. Showing it does not change your rank and does not earn a Featured spot.</p>\n'
        '<p><a href="https://agentscouthq.com/tools/{{SLUG}}.html"><img src="https://agentscouthq.com/badges/featured-dark.svg" '
        'alt="Featured on AgentScout" width="220" height="54"></a></p>\n'
        '<pre>&lt;a href="https://agentscouthq.com/tools/{{SLUG}}.html"&gt;&lt;img src="https://agentscouthq.com/badges/featured-dark.svg" alt="Featured on AgentScout" width="220" height="54"&gt;&lt;/a&gt;</pre>\n'
    )
    open("data/outreach/paid-listing-confirmation.html", "w", encoding="utf-8").write(
        "<!doctype html><meta charset=\"utf-8\"><title>Thank you for your AgentScout listing</title>\n"
        "<p>Hi {{NAME}},</p>\n<p>Thank you for the paid AgentScout listing ($15 Fast-Track or above) for {{NAME}}.</p>\n"
        + snippet + "<p>Your page: https://agentscouthq.com/tools/{{SLUG}}.html</p>\n"
    )
    found = closed_rank_week(tools)
    parts = ["<!doctype html><meta charset=\"utf-8\"><title>DRAFT weekly rank badges — do not send until the owner approves</title>",
             "<p>Draft only. Not approved to send. A rank is final only after that Pacific week has ended.</p>"]
    if not found:
        start, end, wid = week_span(pt_today())
        parts.append(f"<p>No final ranks. {e(wid)} ({e(fmt_short(start))}–{e(fmt_day(end))}) is still open, or no eligible week has closed yet. Earlier weeks are not backfilled.</p>")
    else:
        a, b, wid = found
        rows = week_tools(tools, a, b, current=False)[:10]
        for i, x in enumerate(rows, 1):
            parts.append(f"<h2>#{i} {e(x['name'])}</h2><p>Thank you. Your rank for {e(wid)} is #{i}. The badge is optional and does not change placement.</p>")
            parts.append(f'<p><img src="../../badges/launch/{e(x["slug"])}.svg" alt="Launched on AgentScout, #{i} this week" width="260" height="54"></p>')
    open("data/outreach/weekly-rank-badge-drafts.html", "w", encoding="utf-8").write("\n".join(parts))


def products():
    import build_openapi
    data = json.load(open("api/tools.json", encoding="utf-8"))
    build_openapi.build_commerce_files(data)


def main():
    tools = load_tools()
    m = load_metrics(tools)
    stats_bar(m)
    chrome()
    how_it_started(tools, m)
    extra = launches(tools)
    patch_tool_badges(tools)
    badge_page_note()
    extra += free_tools()
    build_status.write_dashboard(tools)
    insert_launch_pack()
    walk_indexnow()
    emails(tools)
    products()
    llms()
    extra += [B + "how-it-started.html", B + "mcp/status/"]
    sitemap(extra)
    import build_seo_new
    build_seo_new.unify_all_nav_and_footer()
    build_status.write_link_status_forward()
    if BS.LAUNCH_PACK_URL not in open("api/products.json", encoding="utf-8").read():
        raise SystemExit("Launch Pack URL missing from products.json")
    print("growth build done", len(extra), "urls")


if __name__ == "__main__":
    main()
