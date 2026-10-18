"""Persistent HTML redirects for pages that left the sitemap.
Data: redirects.json — map of "from/path.html" -> "to/path.html" (site-root relative).
Writes a small noindex page at each from-path with meta refresh, canonical to the target,
and JS location.replace. Kept out of sitemap.xml (generators only emit their own URLs).
Re-applied at exit of every generator that imports build_extras, so cleanup passes that
delete unknown files in best/ or tasks/ cannot drop these redirects.
Auto-redirect for every vanished sitemap URL is not attempted: choosing a target needs
a human or a heuristics pass. Add entries to redirects.json as Search Console reports 404s.
"""
import json, os, html
B = "https://agentscouthq.com/"

def load():
    try:
        d = json.load(open("redirects.json"))
    except Exception:
        return {}
    return d if isinstance(d, dict) else {}

def page(src, dst):
    """src and dst are site-root-relative paths like 'best/foo.html'."""
    if not dst or dst == src:
        return None
    # Prefer a same-tree relative href for the visible link; fall back to root-absolute.
    src_dir = os.path.dirname(src)
    rel = os.path.relpath(dst, src_dir or ".").replace(os.sep, "/")
    abs_dst = B + dst
    abs_src = B + src
    name = os.path.basename(dst).replace(".html", "").replace("-", " ")
    e = html.escape
    # Immediate client redirect; 0-second meta refresh; canonical consolidates SEO to the target.
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
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

def run():
    m = load()
    if not m:
        print("redirects: none")
        return 0
    n = 0
    for src, dst in sorted(m.items()):
        if not isinstance(src, str) or not isinstance(dst, str):
            continue
        src = src.lstrip("/")
        dst = dst.lstrip("/")
        if not src.endswith(".html") or not dst.endswith(".html"):
            print("redirects: skip bad paths", src, "->", dst)
            continue
        if not os.path.exists(dst):
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

if __name__ == "__main__":
    run()
