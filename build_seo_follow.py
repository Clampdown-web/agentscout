"""SEO follow-up that does not rebuild the homepage, shared header, or bot store.

Fixes shipped HTML in place and is safe to re-run:
- broken tool JSON-LD script closers
- category ItemList entries for every tool the page actually links
- ItemList on guide pages that list tools but had none
- guide and category titles (<=60) and descriptions (<=156)
- thin new tool pages stay noindex (the daily index cap), launch slices and outreach drafts noindex
- sitemap gains only indexable canonical URLs that were missing, with a git lastmod
- one redirect chain flattened
- rank-badge and poster dimensions for layout stability
"""
import html, json, os, re, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

B = "https://agentscouthq.com/"
TODAY = datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
GUIDE_GLOBS = ("best/*.html", "mcp/*.html", "mcp/status/index.html", "s/*.html", "for/*.html", "tasks/*.html", "categories/*.html")
THIN_NOINDEX = ("tools/1zheai.html", "tools/popnow.html")  # under 80 words, no enrichment record, not admitted


def _read(path):
    return Path(path).read_text(encoding="utf-8")


def _write(path, text):
    if Path(path).read_text(encoding="utf-8") != text:
        Path(path).write_text(text, encoding="utf-8")
        return True
    return False


def _git_day(path):
    try:
        d = subprocess.run(["git", "log", "-1", "--format=%cI", "--", path], capture_output=True, text=True, timeout=20).stdout.strip()
        if d:
            return datetime.fromisoformat(d).astimezone(ZoneInfo("America/Los_Angeles")).date().isoformat()
    except Exception:
        pass
    return ""


def repair_jsonld_closers():
    """The pagefind h1 pass once treated a `<h1` inside head JSON as a tag and ate the script closer."""
    n = 0
    for path in ("tools/cmux.html", "tools/diagram-design.html"):
        text = _read(path)
        fixed = text.replace("</script data-pagefind-weight=\"10\">", "</script>", 1)
        if fixed != text:
            Path(path).write_text(fixed, encoding="utf-8")
            n += 1
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', fixed):
            json.loads(raw)
    return n


def _graphs(text):
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', text, flags=re.S):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        out.append((m, data))
    return out


def _dump(data):
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")


def _tool_names():
    return {x["slug"]: x["name"] for x in json.load(open("tools.json")) if x.get("slug")}


def _linked_tools(text):
    main = text.split("<footer", 1)[0]
    slugs = []
    for slug in re.findall(r'href="(?:\.\./)*tools/([a-z0-9-]+)\.html"', main):
        if slug not in slugs:
            slugs.append(slug)
    return slugs


def _itemlist_slugs(data):
    nodes = data.get("@graph") if isinstance(data, dict) and isinstance(data.get("@graph"), list) else []
    for n in nodes:
        if isinstance(n, dict) and n.get("@type") == "ItemList":
            out = []
            for item in n.get("itemListElement") or []:
                url = item.get("url") or ""
                m = re.search(r"/tools/([a-z0-9-]+)\.html", url)
                if m:
                    out.append(m.group(1))
            return out, n.get("numberOfItems")
    return None, None


def _set_itemlist(text, slugs, names, list_name):
    """Put every linked tool on the page's ItemList. Header Organization script is left alone."""
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, flags=re.S):
        try:
            data = json.loads(raw)
        except Exception:
            continue
        have, count = _itemlist_slugs(data)
        if have is not None and have == slugs and count == len(slugs):
            return text
    items = [{"@type": "ListItem", "position": i + 1, "name": names.get(slug, slug), "url": f"{B}tools/{slug}.html"} for i, slug in enumerate(slugs)]
    node = {"@type": "ItemList", "name": list_name, "numberOfItems": len(items), "itemListElement": items}
    found = False

    def repl(m):
        nonlocal found
        if found:
            return m.group(0)
        try:
            data = json.loads(m.group(1))
        except Exception:
            return m.group(0)
        if not isinstance(data, dict):
            return m.group(0)
        nodes = data.get("@graph")
        if not isinstance(nodes, list):
            return m.group(0)
        if nodes and isinstance(nodes[0], dict) and nodes[0].get("@type") == "Organization" and "logo" in nodes[0]:
            return m.group(0)
        for n in nodes:
            if isinstance(n, dict) and n.get("@type") == "ItemList":
                n.clear()
                n.update(node)
                found = True
                return '<script type="application/ld+json">' + _dump(data) + "</script>"
        nodes.append(dict(node))
        found = True
        return '<script type="application/ld+json">' + _dump(data) + "</script>"

    text2 = re.sub(r'<script type="application/ld\+json">(.*?)</script>', repl, text, flags=re.S)
    if not found:
        block = '<script type="application/ld+json">' + _dump({"@context": "https://schema.org", **node}) + "</script>"
        text2 = text2.replace("</head>", block + "</head>", 1)
    return text2


def _fill_item_count(text, n_items):
    def repl(m):
        try:
            data = json.loads(m.group(1))
        except Exception:
            return m.group(0)
        nodes = data.get("@graph") if isinstance(data, dict) else None
        if not isinstance(nodes, list):
            return m.group(0)
        hit = False
        for node in nodes:
            if isinstance(node, dict) and node.get("@type") == "ItemList" and node.get("numberOfItems") != n_items:
                node["numberOfItems"] = n_items
                hit = True
        if not hit:
            return m.group(0)
        return '<script type="application/ld+json">' + _dump(data) + "</script>"
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', repl, text, flags=re.S)


def sync_itemlists():
    names = _tool_names()
    n = 0
    paths = list(Path("categories").glob("*.html"))
    for g in ("best/*.html", "mcp/*.html", "s/*.html", "for/*.html", "tasks/*.html"):
        paths += list(Path(".").glob(g))
    for path in paths:
        if path.name == "index.html" and path.parent.name == "categories":
            continue
        text = path.read_text(encoding="utf-8")
        if 'http-equiv="refresh"' in text[:4000] or 'name="robots" content="noindex' in text[:2500]:
            continue
        slugs = _linked_tools(text)
        have = None
        count = None
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, flags=re.S):
            try:
                data = json.loads(raw)
            except Exception:
                continue
            got, got_n = _itemlist_slugs(data)
            if got is not None:
                have, count = got, got_n
                break
        if path.parent.name != "categories":
            if have is not None or len(slugs) < 3:
                continue
        elif have is not None and set(have) == set(slugs):
            if count == len(slugs):
                continue
            text2 = _fill_item_count(text, len(slugs))
            if text2 != text:
                path.write_text(text2, encoding="utf-8")
                n += 1
            continue
        elif len(slugs) < 1:
            continue
        h = re.search(r"<h1\b[^>]*>(.*?)</h1>", text, flags=re.S)
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h.group(1))).strip() if h else path.stem
        updated = _set_itemlist(text, slugs, names, html.unescape(label)[:140])
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            n += 1
    return n


def _fit_title(title):
    t = title.strip()
    for suf in (" · AgentScout", " | AgentScout"):
        if len(t) > 60 and t.endswith(suf):
            t = t[: -len(suf)].rstrip()
    if len(t) > 60 and t.endswith(" (2026)"):
        t = t[: -len(" (2026)")].rstrip()
    if len(t) > 60:
        cut = t[:59].rsplit(" ", 1)[0].rstrip(" :,;-–")
        if len(cut) >= 40:
            t = cut
    return t


def _fit_desc(desc):
    d = " ".join(desc.split())
    if len(d) <= 156:
        return d
    cut = d[:156].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return cut if cut.endswith(".") else cut + "."


def _replace_attr(text, pattern, new, old):
    def repl(m):
        cur = html.unescape(m.group(1))
        if cur != old:
            return m.group(0)
        return m.group(0).replace(m.group(1), html.escape(new, quote=True), 1)
    return re.sub(pattern, repl, text, count=1)


def fit_guide_meta():
    n = 0
    paths = []
    for g in GUIDE_GLOBS:
        paths += list(Path(".").glob(g))
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if 'http-equiv="refresh"' in text[:4000] or 'name="robots" content="noindex' in text[:2500]:
            continue
        tm = re.search(r"<title>(.*?)</title>", text, flags=re.S)
        dm = re.search(r'<meta name="description" content="([^"]*)"', text)
        if not tm or not dm:
            continue
        old_t, old_d = html.unescape(tm.group(1)).strip(), html.unescape(dm.group(1))
        new_t, new_d = _fit_title(old_t), _fit_desc(old_d)
        if new_t == old_t and new_d == old_d:
            continue
        if new_t != old_t:
            text = re.sub(r"<title>.*?</title>", f"<title>{html.escape(new_t)}</title>", text, count=1, flags=re.S)
            for pat in (r'<meta property="og:title" content="([^"]*)"', r'<meta name="twitter:title" content="([^"]*)"'):
                text = _replace_attr(text, pat, new_t, old_t)
        if new_d != old_d:
            for pat in (r'<meta name="description" content="([^"]*)"', r'<meta property="og:description" content="([^"]*)"', r'<meta name="twitter:description" content="([^"]*)"'):
                text = _replace_attr(text, pat, new_d, old_d)
        path.write_text(text, encoding="utf-8")
        n += 1
    return n


def _noindex(path, canonical=None):
    p = Path(path)
    if not p.exists():
        return False
    text = p.read_text(encoding="utf-8")
    orig = text
    if 'name="robots" content="noindex' not in text[:4000]:
        tag = '<meta name="robots" content="noindex,follow">\n'
        if "<head>" in text:
            text = text.replace("<head>", "<head>\n" + tag, 1)
        else:
            text = tag + text
    if canonical:
        if 'rel="canonical"' in text:
            text = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{canonical}">', text, count=1)
        else:
            text = text.replace("<head>", f'<head>\n<link rel="canonical" href="{canonical}">', 1)
        text = re.sub(r'(<meta property="og:url" content=")[^"]*', lambda m: m.group(1) + canonical, text, count=1)
    if text != orig:
        p.write_text(text, encoding="utf-8")
        return True
    return False


def _flatten_redirects():
    path = Path("redirects.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for src in list(data):
        seen = {src}
        cur = data[src]
        while cur in data and cur not in seen:
            seen.add(cur)
            cur = data[cur]
        if cur != data[src] and cur != src:
            data[src] = cur
            changed = True
    if changed:
        path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    # Keep the one known HTML redirect pointed at the final page, CSP included.
    src = "tasks/evaluating-agents-guardrails.html"
    final = data.get(src)
    if final and Path(src).exists():
        leaf = os.path.basename(final)
        text = _read(src)
        text2 = text.replace("agent-security-guardrails.html", leaf)
        if text2 != text:
            Path(src).write_text(text2, encoding="utf-8")
    return changed


def _robots():
    path = Path("robots.txt")
    text = path.read_text(encoding="utf-8")
    line = "Disallow: /data/outreach/"
    if line in text:
        return False
    text = text.replace("Sitemap:", line + "\n\nSitemap:", 1)
    path.write_text(text, encoding="utf-8")
    return True


def _sitemap_add(urls):
    """Append indexable canonical URLs. lastmod is the file's last commit day, never a guessed today."""
    sm = Path("sitemap.xml").read_text(encoding="utf-8")
    have = set(re.findall(r"<loc>([^<]+)</loc>", sm))
    rows = []
    for rel, loc in urls:
        if loc in have or not Path(rel).exists():
            continue
        text = _read(rel)
        if 'name="robots" content="noindex' in text[:4000] or 'http-equiv="refresh"' in text[:4000]:
            continue
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', text)
        if canon and canon.group(1).rstrip("/") != loc.rstrip("/"):
            continue
        day = _git_day(rel)
        if not day or day > TODAY:
            continue
        rows.append(f"  <url><loc>{loc}</loc><lastmod>{day}</lastmod></url>")
        have.add(loc)
    if not rows:
        return 0
    sm = sm.replace("</urlset>", "\n".join(rows) + "\n</urlset>")
    Path("sitemap.xml").write_text(sm, encoding="utf-8")
    return len(rows)


def _sitemap_drop_unindexable():
    sm = Path("sitemap.xml").read_text(encoding="utf-8")
    kept = []
    drop = 0
    buf = []
    def flush(keep):
        nonlocal drop
        if keep:
            kept.extend(buf)
        else:
            drop += 1
    for line in sm.splitlines(True):
        if line.strip().startswith("<url>"):
            buf = [line]
            if "</url>" in line:
                loc = re.search(r"<loc>([^<]+)</loc>", line)
                kept_ok = _url_ok(loc.group(1) if loc else "")
                flush(kept_ok)
                buf = []
            continue
        if buf:
            buf.append(line)
            if "</url>" in line:
                blob = "".join(buf)
                loc = re.search(r"<loc>([^<]+)</loc>", blob)
                flush(_url_ok(loc.group(1) if loc else ""))
                buf = []
            continue
        kept.append(line)
    text = "".join(kept)
    if text != sm:
        Path("sitemap.xml").write_text(text, encoding="utf-8")
    return drop


def _url_ok(loc):
    if not loc.startswith(B):
        return False
    rel = loc[len(B):]
    path = "index.html" if rel in ("",) else (rel + "index.html" if rel.endswith("/") else rel)
    if not Path(path).exists():
        return False
    if not path.endswith((".html", ".txt", ".xml")):
        return True
    head = Path(path).read_text(encoding="utf-8", errors="replace")[:5000]
    if 'name="robots" content="noindex' in head or 'http-equiv="refresh"' in head:
        return False
    if path.endswith(".html"):
        m = re.search(r'<link rel="canonical" href="([^"]+)"', head)
        if m and m.group(1).rstrip("/") != loc.rstrip("/"):
            return False
    return True


def crawl():
    n = 0
    for rel in THIN_NOINDEX:
        n += _noindex(rel)
    hub = B + "launches/"
    for path in Path("launches").glob("*.html"):
        if path.name == "index.html":
            continue
        n += _noindex(path, hub)
    for path in Path("data/outreach").glob("*.html"):
        n += _noindex(path)
    _flatten_redirects()
    _robots()
    added = _sitemap_add([
        ("free-tools/ai-tool-launch-day-checklist.html", B + "free-tools/ai-tool-launch-day-checklist.html"),
        ("free-tools/roast-my-ai-tool-listing.html", B + "free-tools/roast-my-ai-tool-listing.html"),
    ])
    dropped = _sitemap_drop_unindexable()
    return {"noindex": n, "sitemap_added": added, "sitemap_dropped": dropped}


def cwv():
    """Reserve space for rank badges (235x54) and the known 1200x640 animation posters."""
    n = 0
    for path in Path(".").rglob("*.html"):
        sp = str(path)
        if sp.startswith(("pagefind/", "preview/", "bot-packages/", "bot-store/")) or sp == "index.html":
            continue
        text = path.read_text(encoding="utf-8")
        orig = text

        def badge(m):
            tag = m.group(0)
            if "width=" in tag or "badges/rank/" not in tag:
                return tag
            return tag[:-1] + ' width="235">'

        text = re.sub(r'<img\b[^>]*badges/rank/[^>]*>', badge, text)

        def video(m):
            tag = m.group(0)
            if "width=" in tag or "agentscout-" not in tag or "poster=" not in tag:
                return tag
            return tag[:-1] + ' width="1200" height="640">'

        text = re.sub(r"<video\b[^>]*>", video, text)
        if text != orig:
            path.write_text(text, encoding="utf-8")
            n += 1
    return n


def run():
    stats = {
        "jsonld": repair_jsonld_closers(),
        "itemlists": sync_itemlists(),
        "meta": fit_guide_meta(),
        "crawl": crawl(),
        "cwv": cwv(),
    }
    print("seo follow-up", stats)
    return stats


if __name__ == "__main__":
    run()
