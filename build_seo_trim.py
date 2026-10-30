"""SEO length trims + /best/ index Quick answer + Verification card on every /tools/ listing (owner-approved Oct 29 2026).

Idempotent. Runs after build_status.apply in build_site.py so later passes can't revert it.
Titles: <=60 chars (raw HTML). Meta descriptions: <=156 chars (decoded). URLs/canonicals untouched.
"""
import glob, html, json, re, os

import build_status as BS

TMAX, DMAX = 60, 156
e = html.escape

TITLE_STEPS = [(" · AgentScout", ""), (": Free & Open-Source", ""), (": Free &amp; Open-Source", ""),
               (": Top Competitors", ""), (" &amp; Competitors", ""), (" & Competitors", ""),
               (": 10 similar tools", ""), (" & Eval Tools", " Tools"), (" &amp; Eval Tools", " Tools"),
               ("10 Best ", "Best "), (" in 2026", " (2026)")]
DESC_STEPS = [("and and ", "and "), ("Compare the 10 closest ", "Compare 10 "), (" in 2026 (", " ("),
              ("Verified pricing & stars.", "Pricing & stars."), ("Pricing & GitHub stars.", "Pricing & stars.")]


def _cut_words(s, n):
    if len(s) <= n:
        return s
    s = s[:n - 1].rsplit(" ", 1)[0].rstrip(",;:&(- ")
    return s + "."


def fix_title(raw):
    t = raw
    for a, b in TITLE_STEPS:
        if len(t) <= TMAX:
            break
        t = t.replace(a, b)
    return t if len(t) <= TMAX else _cut_words(t, TMAX).rstrip(".")


def fix_desc(d):
    if len(d) <= DMAX:
        return d
    for a, b in DESC_STEPS:
        if len(d) <= DMAX:
            break
        d = d.replace(a, b)
    if len(d) > DMAX:  # a pre-truncated "Verified pricing & sta" tail
        d2 = re.sub(r"\s*Verified pricing.*$", "", d).rstrip(" ,") 
        if d2 != d:
            d2 = d2.rstrip(".") + "."
            d = d2 + " Pricing & stars." if len(d2) + 17 <= DMAX else d2
    return _cut_words(d, DMAX)


def _meta_re(attr, name):
    return re.compile(rf'<meta (?:{attr}="{re.escape(name)}" content="([^"]*)"|content="([^"]*)" {attr}="{re.escape(name)}")\s*/?>')


def _set_meta(s, attr, name, val):
    rx = _meta_re(attr, name)
    return rx.sub(lambda m: f'<meta {attr}="{name}" content="{e(val)}">', s)


def _get_meta(s, attr, name):
    m = _meta_re(attr, name).search(s)
    return html.unescape(m.group(1) if m.group(1) is not None else m.group(2)) if m else None


def _fix_ld(s, mapping):
    def fix(m):
        try:
            data = json.loads(m.group(1))
        except Exception:
            return m.group(0)
        hit = False

        def walk(n):
            nonlocal hit
            if isinstance(n, dict):
                for k, v in n.items():
                    if isinstance(v, str) and v in mapping and k in ("name", "headline", "description"):
                        n[k] = mapping[v]; hit = True
                    else:
                        walk(v)
            elif isinstance(n, list):
                for v in n:
                    walk(v)
        walk(data)
        if not hit:
            return m.group(0)
        return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', fix, s, flags=re.S)


def trim_page(path):
    s = open(path).read()
    orig = s
    mapping = {}
    m = re.search(r"<title>(.*?)</title>", s, re.S)
    if m and len(m.group(1)) > TMAX:
        old = m.group(1); new = fix_title(old)
        s = s.replace(m.group(0), f"<title>{new}</title>", 1)
        mapping[html.unescape(old)] = html.unescape(new)
        for attr, name in (("property", "og:title"), ("name", "twitter:title")):
            if _get_meta(s, attr, name) == html.unescape(old):
                s = _set_meta(s, attr, name, html.unescape(new))
    d = _get_meta(s, "name", "description")
    if d and len(d) > DMAX:
        nd = fix_desc(d)
        mapping[d] = nd
        s = _set_meta(s, "name", "description", nd)
        for attr, name in (("property", "og:description"), ("name", "twitter:description")):
            if _get_meta(s, attr, name) == d:
                s = _set_meta(s, attr, name, nd)
    if mapping:
        s = _fix_ld(s, mapping)
    if s != orig:
        open(path, "w").write(s)
        return mapping
    return {}


def best_index_quick_answer():
    path = "best/index.html"
    if not os.path.exists(path):
        return
    s = open(path).read()
    n = len([p for p in glob.glob("best/*.html") if not p.endswith("index.html")])
    picks = [("ai-coding-agents.html", "AI coding agents"), ("ai-agent-frameworks.html", "AI agent frameworks"),
             ("open-source-mcp-servers.html", "open-source MCP servers"), ("free-ai-agents.html", "free AI agents")]
    picks = [(h, t) for h, t in picks if os.path.exists("best/" + h)]
    links = ", ".join(f'<a href="{h}">{t}</a>' for h, t in picks[:-1]) + (f' and <a href="{picks[-1][0]}">{picks[-1][1]}</a>' if picks else "")
    qa = (f'<!--qa:bestidx--><p class="qa"><b>Quick answer:</b> AgentScout has {n} ranked best-of lists of AI agent tools. '
          f'Start with {links}. Each list states how it is ranked (GitHub stars or listing maturity), '
          'uses data from link-checked directory listings, and sells no placements.</p><!--/qa:bestidx-->')
    if "<!--qa:bestidx-->" in s:
        s2 = re.sub(r"<!--qa:bestidx-->.*?<!--/qa:bestidx-->", lambda _: qa, s, count=1, flags=re.S)
    else:
        s2, k = re.subn(r'(<p class="lede"[^>]*>.*?</p>)', lambda m: m.group(1) + qa, s, count=1, flags=re.S)
    if s2 != s:
        open(path, "w").write(s2)


def dir_rows(x, directory_checked):
    checked = x.get("verified") or ""
    body = [BS.VC_CSS, '<div class="vc">', BS._card_head("Verification", 0),
            '<ul class="vc-chips"><li class="vc-chip vc-ok">Listing link: <b>checked</b></li></ul>']
    if checked:
        body.append(f'<p>This listing\'s link was last checked {BS._time_html(checked)}.</p>')
    if directory_checked:
        body.append(f'<p style="color:#94a3b8;font-size:13px">Directory links last checked {BS._time_html(directory_checked)}.</p>')
    body.append('<div class="vc-btns"><a class="vc-btn" href="../status.json">status.json</a><a class="vc-btn" href="../mcp/status/">MCP status</a></div></div>')
    return "<!--vs:tool-->" + '<dd class="vc-row">' + "".join(body) + "</dd><!--/vs:tool-->"


def tool_cards(tools):
    try:
        cat = json.load(open("status.json"))["catalog"]
    except Exception:
        cat = {}
    dchk = cat.get("directory_last_checked") or ""
    n = 0
    for x in tools:
        if x.get("category") == "MCP servers":
            continue  # build_status.apply_tool_pages owns these
        path = f"tools/{x['slug']}.html"
        if not os.path.exists(path):
            continue
        s = open(path).read()
        if 'http-equiv="refresh"' in s[:800]:
            continue
        block = dir_rows(x, dchk)
        sw = BS._swap(s, "vs:tool", block)
        if sw is None:
            m = re.search(r"<dt>Link checked</dt><dd>.*?</dd>", s, flags=re.S)
            if m:
                sw = s[:m.end()] + block + s[m.end():]
            elif "</dl>" in s:
                sw = s.replace("</dl>", block + "</dl>", 1)
            else:
                sw = s
        if sw != s:
            open(path, "w").write(sw); n += 1
    print(f"seo_trim: directory listing verification cards updated {n}")


def run(tools):
    changed = {}
    for p in sorted(glob.glob("best/*.html")) + ["about.html"]:
        if os.path.exists(p):
            mp = trim_page(p)
            if mp:
                changed[p] = mp
    best_index_quick_answer()
    tool_cards(tools)
    print(f"seo_trim: trimmed {len(changed)} pages")
    return changed


if __name__ == "__main__":
    import sys
    ch = run(json.load(open("tools.json")))
    if "-v" in sys.argv:
        for p, mp in ch.items():
            for a, b in mp.items():
                print(p, "|", a, "=>", b)
