"""Persistent HTML redirects for pages that left the sitemap.
Data: redirects.json — map of "from/path.html" -> "to/path.html" (site-root relative).
Writes a small noindex page at each from-path with meta refresh, canonical to the target,
and JS location.replace. Kept out of sitemap.xml (generators only emit their own URLs).
Re-applied at exit of every generator that imports build_extras, so cleanup passes that
delete unknown files in best/ or tasks/ cannot drop these redirects.
Automatic redirects (owner-approved Oct 21 2026): before writing pages, run() compares the
committed sitemap.xml (git HEAD, i.e. the live set) with the freshly built sitemap.xml. Every URL
that vanished and is neither in redirects.json nor still a real page on disk gets a redirect
auto-added to redirects.json, to the best target (tool page for X-alternatives, parent task for
a subtask, closest-named live page, else the section index / home). Each auto-add is printed
loudly as "REDIRECT AUTO-ADDED" so it can be reviewed in the commit diff; edit redirects.json
to change a target. Targets may be .html pages or directory URLs ending in "/".
"""
import json, os, html, re
import csp
B = "https://agentscouthq.com/"

def load():
    try:
        d = json.load(open("redirects.json"))
    except Exception:
        return {}
    return d if isinstance(d, dict) else {}

def page(src, dst):
    """src and dst are site-root-relative paths like 'best/foo.html'."""
    if dst == src:
        return None
    # Prefer a same-tree relative href for the visible link; fall back to root-absolute.
    src_dir = os.path.dirname(src)
    rel = os.path.relpath(dst.rstrip("/") or ".", src_dir or ".").replace(os.sep, "/") + ("/" if dst.endswith("/") else "")
    abs_dst = B + dst
    abs_src = B + src
    name = (os.path.basename(dst.rstrip("/")).replace(".html", "").replace("-", " ")) or "home"
    e = html.escape
    # Immediate client redirect; 0-second meta refresh; canonical consolidates SEO to the target.
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
{csp._meta(csp.POLICY)}
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Moved · AgentScout</title>
<meta name="robots" content="noindex,follow">
<meta http-equiv="refresh" content="0;url={e(rel)}">
<link rel="canonical" href="{e(abs_dst)}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<script>location.replace({json.dumps(rel)})</script>
</head><body>
<p>This page has moved to <a href="{e(rel)}">{e(name)}</a>.</p>
<p><a href="{e(rel)}">{e(abs_dst)}</a> · was <code>{e(abs_src)}</code></p>
</body></html>
"""

def _locs(text):
    return set(x.replace(B, "") for x in re.findall(r"<loc>([^<]+)</loc>", text))

def _exists(dst):
    return os.path.exists(dst + "index.html" if dst.endswith("/") else dst) or dst == ""

def _is_redirect(path):
    try:
        return 'http-equiv="refresh"' in open(path).read(3000)
    except Exception:
        return False

def _target(src, live):
    d, f = os.path.split(src)
    stem = f[:-5] if f.endswith(".html") else f
    if src.startswith("best/") and stem.endswith("-alternatives") and "tools/" + stem[:-13] + ".html" in live:
        return "tools/" + stem[:-13] + ".html"
    if d in ("tasks", "categories", "s", "best"):
        parts = stem.split("-")
        for k in range(len(parts) - 1, 0, -1):
            c = f"{d}/{'-'.join(parts[:k])}.html"
            if c in live and c != src:
                return c
    if d.startswith("bot-templates") and "bot-templates/" in live:
        return "bot-templates/"
    w = set(stem.split("-")) - {"ai", "agent", "agents", "tools", "free", "best", "for", "and", "the"}
    best, sc = None, 0.0
    for u in live:
        if not u.endswith(".html") or u.startswith(("preview/", "tools/")):
            continue
        uw = set(os.path.basename(u)[:-5].split("-")) - {"ai", "agent", "agents", "tools", "free", "best", "for", "and", "the"}
        if not w or not uw:
            continue
        j = len(w & uw) / len(w | uw)
        if j > sc:
            best, sc = u, j
    if best and sc >= 0.34:
        return best
    for idx in (d + "/", "leaderboard/" if d == "tools" else None):
        if idx and idx in live:
            return idx
    return ""  # home page

def _save(m):
    with open("redirects.json", "w") as f:
        json.dump(m, f, indent=1)
        f.write("\n")

def detect(m):
    """Auto-add redirects for URLs in the committed (live) sitemap that the new build dropped."""
    import subprocess, urllib.request
    try:
        cur = _locs(open("sitemap.xml").read())
    except Exception as ex:
        print("redirects: vanished-URL check skipped:", ex)
        return m
    prev, srcname = None, "live " + B + "sitemap.xml"
    try:  # the live sitemap is the real "previous" set; git HEAD only if the fetch fails
        req = urllib.request.Request(B + "sitemap.xml", headers={"User-Agent": "AgentScout-build"})
        prev = _locs(urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace"))
        if not prev:
            prev = None
    except Exception as ex:
        print("redirects: live sitemap fetch failed, using git HEAD:", ex)
    if prev is None:
        srcname = "git HEAD sitemap.xml"
        try:
            prev = _locs(subprocess.run(["git", "show", "HEAD:sitemap.xml"], capture_output=True, text=True, check=True).stdout)
        except Exception as ex:
            print("redirects: vanished-URL check skipped:", ex)
            prev = set()
    norm = lambda u: u.replace(B, "").replace("http://agentscouthq.com/", "").lstrip("/")
    cur = set(norm(u) for u in cur)
    prev = set(norm(u) for u in prev) if prev else prev
    back = sorted(k for k in m if norm(k) in cur)  # keys and locs both as site-root paths
    for k in back:  # page is live in the sitemap again: drop its redirect entry
        print("redirects: page is live again, removing entry", k, "->", m.pop(k))
    if back:
        _save(m)
    if not prev:
        return m
    if len(cur) < 0.8 * len(prev):
        print(f"redirects: REFUSING auto-add, new sitemap has {len(cur)} URLs vs {len(prev)} in {srcname} (partial build?)")
        return m
    added = 0
    for src in sorted(prev - cur):
        if src in m or src == "" or src.endswith("/"):
            if src.endswith("/") and src not in m:
                print("redirects: WARNING directory URL vanished, add a redirect by hand:", src)
            continue
        if src in HTML_FORWARDERS or (os.path.exists(src) and not _is_redirect(src)):
            continue  # page still exists (e.g. made noindex on purpose); not a 404
        dst = _target(src, cur)
        if dst == "":  # 5: homepage fallback is a soft-404 risk, never add silently
            print(f"redirects: WARNING (soft-404 risk) no good target for vanished {src}; NOT auto-added. Add a redirects.json entry by hand.")
            continue
        m[src] = dst
        added += 1
        print(f"redirects: REDIRECT AUTO-ADDED {src} -> {dst}  (review / edit redirects.json)")
    if added:
        _save(m)
    return m

# GitHub Pages ignores _redirects. These paths are real HTML forwarders and must not be deleted or rewritten.
HTML_FORWARDERS = {"mcp/link-status.html"}

def ensure_cf_redirects():
    """Drop _redirects rules for HTML forwarders. The rule is harmless on Cloudflare and ignored on GitHub Pages."""
    path = "_redirects"
    if not os.path.exists(path):
        return
    kept = []
    for ln in open(path, encoding="utf-8"):
        parts = ln.split()
        if parts and parts[0].lstrip("/") in HTML_FORWARDERS:
            continue
        if ln.strip():
            kept.append(ln.rstrip("\n"))
    open(path, "w", encoding="utf-8").write(("\n".join(kept) + "\n") if kept else "")

def run():
    ensure_cf_redirects()
    m = detect(load())
    dropped = [k for k in list(m) if k.lstrip("/") in HTML_FORWARDERS]
    for k in dropped:
        print("redirects: html forwarder, not a _redirects rule", k, "->", m.pop(k))
    if dropped:
        _save(m)
    if not m:
        print("redirects: none")
        return 0
    n = 0
    try:  # never overwrite a page the current build lists in sitemap.xml (it came back)
        live = set(l.split("<loc>")[1].split("</loc>")[0].replace(B, "") for l in open("sitemap.xml") if "<loc>" in l)
    except Exception:
        live = set()
    for src, dst in sorted(m.items()):
        if not isinstance(src, str) or not isinstance(dst, str):
            continue
        src = src.lstrip("/")
        dst = dst.lstrip("/")
        if not src.endswith(".html") or not (dst.endswith(".html") or dst.endswith("/") or dst == ""):
            print("redirects: skip bad paths", src, "->", dst)
            continue
        if src in HTML_FORWARDERS:
            continue
        if src in live:
            print("redirects: page is live again, skip", src)
            continue
        if os.path.exists(src) and not _is_redirect(src):  # 3: never overwrite a real page
            print("redirects: real page exists at source, skip", src)
            continue
        if not _exists(dst):
            print("redirects: target missing, skip", src, "->", dst)
            continue
        body = page(src, dst)
        if not body:
            continue
        os.makedirs(os.path.dirname(src) or ".", exist_ok=True)
        open(src, "w").write(body)
        n += 1
    print(f"redirects: wrote {n}/{len(m)}")
    return n

def redirected_slugs(tools=None):
    """Tool slugs whose page is a redirect and which are not in the live catalog."""
    live=set()
    if tools:
        live={x.get("slug") for x in tools if x.get("slug")}
    out=set()
    for src in load():
        if not isinstance(src,str): continue
        src=src.lstrip("/")
        if src.startswith("tools/") and src.endswith(".html"):
            slug=src[len("tools/"):-len(".html")]
            if slug not in live: out.add(slug)
    return out
def _drop_slug_html(html, slug):
    """Remove a generated card, table row, or list item that links at a removed tool. Leaves the redirect stub page alone."""
    html=re.sub(rf'<li class="card tile lb-card" data-slug="{re.escape(slug)}"[\s\S]*?</li>','',html,count=1)
    html=re.sub(rf'<li style="margin:0 0 10px"><a href="(?:\.\./)?tools/{re.escape(slug)}\.html"[\s\S]*?</li>','',html,count=1)
    html=re.sub(rf'<tr><td><a class="icol" href="(?:\.\./)?tools/{re.escape(slug)}\.html"[\s\S]*?</tr>','',html,count=1)
    html=re.sub(rf'<tr><td><a href="(?:\.\./)?tools/{re.escape(slug)}\.html"[\s\S]*?</tr>','',html,count=1)
    html=re.sub(rf',?\s*\{{"@type": "ListItem", "position": \d+, "name": "[^"]*", "url": "https://agentscouthq.com/tools/{re.escape(slug)}\.html"\}}','',html)
    html=re.sub(rf',?\s*\{{"@type":"ListItem","position":\d+,"name":"[^"]*","url":"https://agentscouthq.com/tools/{re.escape(slug)}\.html"\}}','',html)
    return html.replace("[,","[").replace(",]","]")
def _sync_itemlist_counts(html):
    """Keep numberOfItems equal to the list after a removed tool is dropped, without reformatting the script."""
    def repl(m):
        raw=m.group(1)
        try:
            data=json.loads(raw)
        except Exception:
            return m.group(0)
        nodes=data.get("@graph") if isinstance(data, dict) else None
        nodes=nodes if isinstance(nodes, list) else [data]
        out=m.group(0)
        for node in nodes:
            if not isinstance(node, dict) or node.get("@type")!="ItemList": continue
            items=node.get("itemListElement")
            if not isinstance(items, list): continue
            old=node.get("numberOfItems")
            if old==len(items): continue
            out=out.replace(f'"numberOfItems": {old}', f'"numberOfItems": {len(items)}', 1)
        return out
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', repl, html, flags=re.S)
def scrub_redirected_listings(tools=None):
    """Drop internal cards that point at tool pages which now redirect. The daily build calls this so a kept page cannot grow the link back."""
    slugs=redirected_slugs(tools)
    if not slugs: return 0
    n=0
    roots=("launches","best")
    for root in roots:
        if not os.path.isdir(root): continue
        for dirpath, dirs, files in os.walk(root):
            for fn in files:
                if not fn.endswith(".html"): continue
                path=os.path.join(dirpath, fn)
                if os.path.basename(path)[:-5] in slugs and path.startswith("tools/"): continue
                html=open(path,encoding="utf-8").read()
                nxt=html
                for slug in slugs:
                    if f"tools/{slug}.html" in nxt or f'data-slug="{slug}"' in nxt:
                        nxt=_drop_slug_html(nxt, slug)
                if nxt!=html:
                    nxt=_sync_itemlist_counts(nxt)
                    open(path,"w",encoding="utf-8").write(nxt)
                    n+=1
    if n: print(f"redirects: removed links to {len(slugs)} redirected tools from {n} pages")
    return n

if __name__ == "__main__":
    run()
