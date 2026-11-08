"""Guide blocks for the pages Google stopped surfacing.

Copy lives in data/quality_guides.json. Counts, names, and pricing mixes are filled from
tools.json (and the bot-template catalog) at build time, so a rebuild cannot leave a stale total.
Tool pros, cons, and setup are rendered by build_rich from data/quality_tool_extras.json.
"""
import html, json, os, re
import build_extras as X
import build_subtasks as S
import quality_picks

e = html.escape
MARK_A = "<!--quality-guide-->"
MARK_B = "<!--/quality-guide-->"
GUIDES = json.load(open("data/quality_guides.json")) if os.path.exists("data/quality_guides.json") else []

def _items(t, cat):
    return [x for x in t if x.get("category") == cat]

def _top(items, k=5):
    starred = sorted([x for x in items if x.get("github_stars")], key=lambda x: (-x["github_stars"], x["name"].lower()))
    names = starred[:k] or sorted(items, key=lambda x: x["name"].lower())[:k]
    return names

def _see(items):
    return sum(1 for x in items if (x.get("pricing") or "").strip().lower() in ("see site", "unknown", ""))

def cat_facts(t, cat, page):
    items = _items(t, cat)
    top = _top(items)
    leader = top[0] if top else None
    depth = "../" if page.startswith(("categories/", "best/", "for/")) else ""
    link = ""
    if leader:
        link = f'<a href="{depth}tools/{e(leader["slug"])}.html">{e(leader["name"])}</a>'
    return {
        "n": len(items),
        "price_line": S.price_line(items) or "pricing as each maker states it",
        "builders": sum(1 for x in items if x.get("audience") == "builders"),
        "ready": sum(1 for x in items if x.get("audience") != "builders"),
        "top": ", ".join(x["name"] for x in top),
        "see_site": _see(items),
        "os_n": sum(1 for x in items if x.get("pricing") in S.OPEN),
        "leader_html": link or "the first card",
        "leader_stars": f'{leader["github_stars"]:,}' if leader and leader.get("github_stars") else "not tracked",
        "discontinued": sum(1 for x in items if re.search(r"discontinu|archived", (x.get("maturity") or ""), re.I)),
    }

def home_facts(t):
    import build_bot_templates as bt
    import build_free_tools as ft
    cats = len({x["category"] for x in t})
    mcp = sum(1 for x in t if x["category"] == "MCP servers")
    parts = bt.template_count_agreement()
    return {
        "n": f"{len(t):,}",
        "cats": cats,
        "mcp": mcp,
        "see_site": _see(t),
        "os_n": sum(1 for x in t if x.get("pricing") in S.OPEN),
        "own": len(ft.TOOLS),
        "templates": parts["page"] or parts["total"],
    }

def free_facts(t):
    import build_free_tools as ft
    pr = lambda x: (x.get("pricing_detail") or x.get("pricing") or "")
    items = [x for x in t if X.FREE_RE.search(pr(x)) and not re.search(r"discontinu|archived|shut down", (x.get("maturity") or "") + " " + pr(x), re.I)]
    return {
        "n": len(items),
        "cats": len({x["category"] for x in items}),
        "own": len(ft.TOOLS),
        "price_line": S.price_line(items) or "open source, free, or freemium",
        "see_site": _see(items),
        "top": ", ".join(x["name"] for x in _top(items, 4)),
    }

def bot_facts(t):
    import build_bot_templates as bt
    parts = bt.template_count_agreement()
    return {"n": parts["page"] or parts["total"], "builtin": parts["builtin"], "community": parts["community"]}

def codex_facts(t):
    import build_rich
    named = []
    for x in t:
        if x["category"] != "MCP servers" and "connect tools via MCP" not in (x.get("use_cases") or []):
            continue
        r = build_rich.R.get(x["slug"]) or {}
        blob = x.get("description") or ""
        blob += " " + json.dumps([r.get("long"), r.get("features")], ensure_ascii=False)
        if re.search(r"\bCodex\b", blob):
            named.append(x)
    named.sort(key=lambda x: (x.get("github_stars") is None, -(x.get("github_stars") or 0), x["name"].lower()))
    return {
        "n": len(named),
        "top": ", ".join(x["name"] for x in named[:5]),
        "os_n": sum(1 for x in named if x.get("pricing") in S.OPEN),
        "see_site": _see(named),
        "price_line": S.price_line(named) or "pricing as each maker states it",
        "mcp_n": sum(1 for x in t if x["category"] == "MCP servers"),
    }

def browser_facts(t):
    x = next((y for y in t if y["slug"] == "browser-use"), None)
    peers = [y for y in t if y.get("category") == "browser/computer use" and "discontinu" not in (y.get("maturity") or "").lower()]
    stars = f'{x["github_stars"]:,}' if x and x.get("github_stars") else "not tracked"
    return {
        "name": x["name"] if x else "Browser Use",
        "desc": (x.get("description") if x else "") or "a browser agent library",
        "pricing": (x.get("pricing_detail") or x.get("pricing") if x else "") or "see the listing",
        "stars": stars,
        "peers": len(peers),
        "os_n": sum(1 for y in peers if y.get("pricing") in S.OPEN),
        "price_line": S.price_line(peers) or "mixed",
    }

def role_facts(t, slug):
    import build_landing as L
    import build_tasks as T
    row = next(r for r in L.R if r[0] == slug)
    _s, who, _h, _intro, secs, _fts, _ss = row
    m = T.mapping(t)
    bits = []; shown = []; pool = {}
    for hd, task in secs:
        if task not in m:
            continue
        items = [y for y in m[task][1] if "iscontinued" not in (y.get("maturity") or "").lower()]
        for y in items:
            pool[y["slug"]] = y
        take = items[:6]
        shown.extend(take)
        bits.append(f"{hd} ({len(take)} of {len(items)})")
    uniq = {y["slug"]: y for y in shown}
    return {
        "who": who,
        "jobs": len(bits),
        "sections": "; ".join(bits),
        "shown": len(uniq),
        "pool": len(pool),
        "price_line": S.price_line(list(uniq.values())) or "pricing as each maker states it",
        "top": ", ".join(x["name"] for x in _top(list(uniq.values()), 4)),
        "see_site": _see(list(uniq.values())),
    }

FACTS = {
    "index.html": home_facts,
    "categories/agent-infra.html": lambda t: cat_facts(t, "agent infra", "categories/agent-infra.html"),
    "categories/games.html": lambda t: cat_facts(t, "games", "categories/games.html"),
    "free-tools.html": free_facts,
    "bot-templates/index.html": bot_facts,
    "best/mcp-servers-for-codex.html": codex_facts,
    "best/browser-use-alternatives.html": browser_facts,
    "for/devops-engineers.html": lambda t: role_facts(t, "devops-engineers"),
    "for/founders.html": lambda t: role_facts(t, "founders"),
}

def _fill(text, facts):
    def repl(m):
        k = m.group(1)
        if k not in facts:
            return m.group(0)
        v = facts[k]
        return str(v) if k.endswith("_html") else e(str(v))
    return re.sub(r"\{([a-z_]+)\}", repl, text)

def _block(g, facts, tools=None):
    def P(s):
        return f'<p style="margin:0 0 12px">{_fill(s, facts)}</p>'
    def items(key):
        return "".join(f"<li>{_fill(s, facts)}</li>" for s in g.get(key) or [])
    alts = "".join(f'<a class="b uc" href="{e(a["href"])}">{e(_fill(a["label"], facts))}</a>' for a in g.get("alts") or [])
    faq = [(_fill(q, facts), _fill(a, facts)) for q, a in g.get("faq") or []]
    body = (
        f'{MARK_A}<div class="qguide" id="quality-guide" style="margin:8px 0 22px;overflow-wrap:anywhere;max-width:100%">'
        f'<h2 style="font-size:18px;margin:8px 0 8px">What this is</h2>{"".join(P(s) for s in g["what"])}'
        f'<h2 style="font-size:18px;margin:18px 0 8px">Who it is for</h2>{P(g["who"])}'
        f'<h2 style="font-size:18px;margin:18px 0 8px">Pros and cons</h2>'
        f'<p style="margin:0 0 6px"><strong>Pros</strong></p><ul style="margin:0 0 12px;padding-left:20px;line-height:1.7">{items("pros")}</ul>'
        f'<p style="margin:0 0 6px"><strong>Cons</strong></p><ul style="margin:0 0 12px;padding-left:20px;line-height:1.7">{items("cons")}</ul>'
        f'<h2 style="font-size:18px;margin:18px 0 8px">How to use it</h2><ol style="margin:0 0 12px;padding-left:20px;line-height:1.7">{items("setup")}</ol>'
        + (quality_picks.choice_html(g.get("picks"), {x["slug"]: x for x in (tools or [])}, bridge=bool(g.get("picks_bridge"))) if g.get("picks") else "")
        + f'<h2 style="font-size:18px;margin:18px 0 8px">Alternatives</h2><div class="badges" style="margin:0 0 12px">{alts}</div>'
        f'<h2 style="font-size:18px;margin:18px 0 8px">FAQ</h2>'
        + "".join(f'<details style="margin:0 0 10px"><summary style="cursor:pointer;font-weight:600">{e(q)}</summary><p style="margin:8px 0 0">{a}</p></details>' for q, a in faq)
        + "</div>" + MARK_B
    )
    return body, faq

def _anchor_end(html_s, kind):
    if kind == "after-ci-free":
        m = re.search(r"<!--/ci:free-->", html_s)
        return m.end() if m else None
    if kind == "before-tcount":
        m = re.search(r'<p class="tcount"', html_s)
        return m.start() if m else None
    if kind == "after-bt-lede":
        m = re.search(r'<p class="bt-lede">.*?</p>', html_s, re.S)
        return m.end() if m else None
    if kind == "after-lede":
        m = re.search(r'<p class="lede"[^>]*>.*?</p>', html_s, re.S)
        return m.end() if m else None
    return None

def _faq_ld(pairs):
    data = {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in pairs]}
    return '<script type="application/ld+json" data-quality-faq>' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>"

def _merge_faq(html_s, pairs):
    html_s = re.sub(r'<script type="application/ld\+json" data-quality-faq>.*?</script>', "", html_s, flags=re.S)
    found = {"ok": False}
    def walk(node):
        if isinstance(node, dict):
            if node.get("@type") == "FAQPage" and isinstance(node.get("mainEntity"), list):
                have = {q.get("name") for q in node["mainEntity"] if isinstance(q, dict)}
                for q, a in pairs:
                    plain = re.sub("<[^>]+>", "", a)
                    if q not in have:
                        node["mainEntity"].append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": plain}})
                found["ok"] = True
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    def sub(m):
        raw = m.group(1)
        try:
            data = json.loads(raw)
        except Exception:
            return m.group(0)
        before = found["ok"]
        walk(data)
        if found["ok"] == before:
            return m.group(0)
        return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    html_s = re.sub(r'<script type="application/ld\+json">(.*?)</script>', sub, html_s, flags=re.S)
    if not found["ok"]:
        html_s = html_s.replace("</head>", _faq_ld(pairs) + "</head>", 1)
    return html_s

def inject(t):
    """Insert the guide block on each quality page. Idempotent if a page is rewritten twice."""
    done = []
    for g in GUIDES:
        path = g["path"]
        if not os.path.exists(path):
            print("quality guide missing file", path)
            continue
        facts = FACTS[path](t) if path in FACTS else {}
        block, faq = _block(g, facts, t)
        html_s = open(path, encoding="utf-8").read()
        html_s = re.sub(re.escape(MARK_A) + r".*?" + re.escape(MARK_B), "", html_s, flags=re.S)
        at = _anchor_end(html_s, g.get("anchor") or "after-lede")
        if at is None:
            print("quality guide missing anchor", path, g.get("anchor"))
            continue
        html_s = html_s[:at] + block + html_s[at:]
        html_s = _merge_faq(html_s, faq)
        banned = ("hand-tested", "personally reviewed", "fully automated", "no humans")
        low = re.sub("<[^>]+>", " ", block).lower()
        hit = [w for w in banned if w in low]
        if hit:
            raise SystemExit(f"quality guide used a blocked phrase on {path}: {hit}")
        open(path, "w", encoding="utf-8").write(html_s)
        done.append(path)
    print("quality guides:", ", ".join(done))
    return done
