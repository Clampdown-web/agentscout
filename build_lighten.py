"""Lighter heavy list pages (owner-approved SEO audit, Oct 22 2026 PT). Idempotent post-pass at the end of build_site.py.
Pages: leaderboard/, tasks/writing-code.html, categories/mcp-servers.html. Nothing is deleted:
1. The inline logo-retry onerror (~150 bytes on every img) becomes one delegated handler with the same behaviour.
2. Repeated inline category icons become one <symbol> each plus <use>.
3. Card grids show the first KEEP cards; the rest load from <page>.more.json on "Show all" (or at once when a filter/sort is used).
   Leaderboard filter-only rows (data-x, hidden until a filter is on) load from leaderboard/extra.json when a filter is used.
4. Crawlability: every tool that loses its static card keeps a plain text link on the page ("All tools on this page"),
   so every tool stays reachable and crawlable without JavaScript."""
import re,json,os,html,glob
KEEP=48
KEEP_BY={"tasks/writing-code.html":12}  # many sub-grids: show 12 per section
CAT_KEEP=60  # first screen of a heavy category
PAGE_LINKS=160  # crawlable name links per follow-on page
HEAVY=600_000  # paginate a category page above this size
OE=re.compile(r""" onerror="var i=this,n=\+\(i\.dataset\.r\|\|0\);if\(n<2\)\{i\.dataset\.r=n\+1;setTimeout\(function\(\)\{i\.src=i\.src\.split\('\?'\)\[0\]\+'\?r='\+\(n\+1\)\},1500\*\(n\+1\)\)\}else i\.remove\(\)\"""")
RETRY=('<script>document.addEventListener("error",function(ev){var i=ev.target;if(!i||i.tagName!=="IMG"||!i.hasAttribute("data-rt"))return;'
       'var n=+(i.dataset.r||0);if(n<2){i.dataset.r=n+1;setTimeout(function(){i.src=i.src.split("?")[0]+"?r="+(n+1)},1500*(n+1))}else i.remove()},true)</script>')
MORE_JS=('<script>(function(){var B=[].slice.call(document.querySelectorAll("[data-more]"));if(!B.length)return;var done={};'
 'function load(b,cb){var u=b.getAttribute("data-more");if(done[u]){cb&&cb();return}done[u]=1;b.disabled=true;b.textContent="Loading…";'
 'fetch(u,{cache:"no-cache"}).then(function(r){return r.json()}).then(function(J){Object.keys(J).forEach(function(k){var g=document.querySelector("[data-mg=\\""+k+"\\"]");if(!g)return;g.insertAdjacentHTML("beforeend",J[k])});'
 'B.forEach(function(x){if(x.getAttribute("data-more")===u){var w=x.closest(".morewrap");if(w)w.hidden=true}});'
 'var cg=document.getElementById("cgrid");if(cg&&window.__cfsrc){var s=document.createElement("script");s.src=window.__cfsrc+(window.__cfsrc.indexOf("?")<0?"?":"&")+"r=1";document.body.appendChild(s)}cb&&cb()}).catch(function(){b.disabled=false;b.textContent="Show all"})}'
 'B.forEach(function(b){b.addEventListener("click",function(){load(b)})});'
 'var F=document.getElementById("cfilters");var q=/[?&](price|os|sort)=/.test(location.search);if(F){F.addEventListener("change",function(){B.forEach(function(b){load(b)})},true);if(q)B.forEach(function(b){load(b)})}})()</script>')
def _sprite(s):
    sv=re.findall(r'<svg class="cico"[^>]*>.*?</svg>',s,re.S)
    from collections import Counter
    C=Counter(sv); sym=[]; n=0
    for i,(k,c) in enumerate(C.most_common()):
        if c<3 or "<use " in k or "viewBox" not in k: continue
        m=re.match(r'<svg class="cico"([^>]*)>(.*?)</svg>',k,re.S); attrs=m.group(1); inner=m.group(2)
        vb=re.search(r'viewBox="[^"]*"',attrs).group(0); rest=re.sub(r'\s*viewBox="[^"]*"|\s*width="[^"]*"|\s*height="[^"]*"|\s*aria-hidden="[^"]*"|\s*focusable="[^"]*"','',attrs)
        sid=f"ci{n}"; n+=1
        sym.append(f'<symbol id="{sid}" {vb}{rest}>{inner}</symbol>')
        wh=" ".join(re.findall(r'(?:width|height)="[^"]*"',attrs))
        s=s.replace(k,f'<svg class="cico" {wh} aria-hidden="true" focusable="false"><use href="#{sid}"/></svg>')
    if sym: s=s.replace("<main",'<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>'+"".join(sym)+'</defs></svg><main',1)
    return s
def _common(s):
    s=OE.sub(' data-rt',s)
    if "<!--lt:rt-->" not in s: s=s.replace("</head>","<!--lt:rt-->"+RETRY+"</head>",1)
    return _sprite(s)
def _trim_itemlist(s, keep=CAT_KEEP):
    """Drop a multi-thousand ItemList so the first category page stays under the byte budget."""
    def repl(m):
        try: data=json.loads(m.group(1))
        except Exception: return m.group(0)
        graph=data.get("@graph") if isinstance(data, dict) else None
        if not isinstance(graph, list): return m.group(0)
        changed=False
        for node in graph:
            items=node.get("itemListElement") if isinstance(node, dict) else None
            if node.get("@type")=="ItemList" and isinstance(items, list) and len(items)>keep:
                node["itemListElement"]=items[:keep]
                node["numberOfItems"]=keep
                changed=True
        if not changed: return m.group(0)
        raw=json.dumps(data, ensure_ascii=False).replace("</","<\\/")
        return '<script type="application/ld+json">'+raw+'</script>'
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', repl, s, flags=re.S)
def _sitemap_add(paths):
    p="sitemap.xml"
    if not os.path.exists(p) or not paths: return
    s=open(p, encoding="utf-8").read()
    import datetime
    day=datetime.date.today().isoformat()
    extra=""
    for rel in paths:
        loc="https://agentscouthq.com/"+rel
        if loc in s: continue
        extra+=f"  <url><loc>{loc}</loc><lastmod>{day}</lastmod></url>\n"
    if extra:
        open(p,"w",encoding="utf-8").write(s.replace("</urlset>", extra+"</urlset>"))
def _write_list_pages(src, slugs, names, title):
    """Crawlable follow-on pages. Plain links, no logos, so a page stays small."""
    if not slugs: return []
    base=os.path.basename(src)[:-5]
    chunks=[slugs[i:i+PAGE_LINKS] for i in range(0,len(slugs),PAGE_LINKS)]
    rels=[f"categories/{base}-p{i}.html" for i in range(2, 2+len(chunks))]
    import build_extras as X
    for i, chunk in enumerate(chunks):
        n=i+2
        rel=rels[i]
        prev=f"{base}.html" if n==2 else f"{base}-p{n-1}.html"
        nxt=f"{base}-p{n+1}.html" if i+1<len(chunks) else ""
        items="".join(f'<li><a href="../tools/{x}.html">{html.escape(names.get(x,x))}</a></li>' for x in chunk)
        navp=f'<p class="catpager"><a href="{prev}">← Previous</a>'+(f' · <a rel="next" href="{nxt}">Next →</a>' if nxt else "")+f' · <a href="{base}.html">Back to {html.escape(title)}</a></p>'
        body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="{base}.html">{html.escape(title)}</a> / Page {n}</div>'
              f'<section class="calm"><h1 style="text-align:left">More {html.escape(title)}</h1>'
              f'<p class="lede" style="margin-left:0;text-align:left">Page {n}. {len(chunk):,} more tools from this category. Every name links to its listing.</p>'
              f'{navp}<ul class="catmore">{items}</ul>{navp}</section>')
        desc=f"More {title}: page {n}, {len(chunk)} tools."
        canon=X.B+rel
        ld={"@context":"https://schema.org","@type":"CollectionPage","name":f"{title} page {n}","description":desc,"url":canon}
        page=X.shell("../", f"{title}, page {n} · AgentScout", desc, canon, body, ld)
        if prev: page=page.replace("</head>", f'<link rel="prev" href="{prev}"></head>', 1)
        if nxt: page=page.replace("</head>", f'<link rel="next" href="{nxt}"></head>', 1)
        open(rel,"w",encoding="utf-8").write(page)
    _sitemap_add(rels)
    return rels
def _pager(rels, shown, total, noun):
    if not rels: return ""
    links=" · ".join(f'<a href="{os.path.basename(r)}">Page {i}</a>' for i,r in enumerate(rels, start=2))
    return (f'<!--lt:pages--><nav class="catpager" aria-label="More {html.escape(noun)}">'
            f'<p>Showing {shown:,} of {total:,}. The rest are linked, one page at a time. '
            f'<a rel="next" href="{os.path.basename(rels[0])}">Next page →</a></p>'
            f'<p>{links}</p></nav><!--/lt:pages-->')
def _linklist(s, removed, names, head="All tools on this page", src=""):
    have=set(re.findall(r'href="\.\./tools/([a-z0-9-]+)\.html"', s))
    miss=[x for x in removed if x not in have]
    if not miss: return s, 0
    # A few leftovers can stay on the page. A heavy category is paginated instead of one giant logo list.
    if src.startswith("categories/") and len(miss)>40:
        h=re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
        title=re.sub(r"<[^>]+>","", h.group(1)).strip() if h else "This category"
        rels=_write_list_pages(src, miss, names, title)
        blk=_pager(rels, CAT_KEEP, CAT_KEEP+len(miss), title)
        if "<!--lt:pages-->" not in s:
            s=s.replace("</main>", blk+"</main>", 1)
        if rels and 'rel="next"' not in s.split("</head>",1)[0]:
            s=s.replace("</head>", f'<link rel="next" href="{os.path.basename(rels[0])}"></head>', 1)
        return s, len(miss)
    lst=" · ".join(f'<a href="../tools/{x}.html">{html.escape(names.get(x,x))}</a>' for x in miss)
    blk=f'<!--lt:all--><section class="alltools" style="margin:28px 0 0"><h2 style="font-size:16px;margin:0 0 8px">{head}</h2><p class="muted" style="font-size:13.5px;line-height:1.9;overflow-wrap:anywhere">{lst}</p></section><!--/lt:all-->'
    return s.replace("</main>", blk+"</main>", 1), len(miss)
def _slices(s, i, opener, closer):
    """Consecutive opener…closer pieces starting at i. One forward scan, no nested quantifiers."""
    items=[]
    while s.startswith(opener, i):
        end=s.find(closer, i+len(opener))
        if end<0: return [], i
        end+=len(closer)
        items.append(s[i:end])
        i=end
    return items, i
def grids(f,names):
    K=KEEP_BY.get(f, CAT_KEEP if f.startswith("categories/") else KEEP)
    s=open(f).read(); base=os.path.basename(f)[:-5]; mj=f[:-5]+".more.json"; J={}; removed=[]; gi=0
    def trim_grids(s):
        nonlocal gi
        out=[]; pos=0
        for m in re.finditer(r'<div class="grid"(?: id="cgrid")?>', s):
            if m.start()<pos: continue
            cards, i=_slices(s, m.end(), '<a class="card tile"', '</a>')
            if not s.startswith('</div>', i) or len(cards)<=K+4 or "".join(cards)!=s[m.end():i].strip():
                continue
            out.append(s[pos:m.start()])
            k=f"g{gi}"; gi+=1; J[k]="".join(cards[K:])
            removed.extend(re.search(r'data-s="([^"]+)"',c).group(1) for c in cards[K:])
            btn=f'<div class="morewrap" style="margin:14px 0 0;text-align:center"><button type="button" class="btn" data-more="{base}.more.json">Show all {len(cards):,} tools ({len(cards)-K:,} more)</button></div>'
            out.append(s[m.start():m.end()-1]+f' data-mg="{k}" data-total="{len(cards)}">'+"".join(cards[:K])+"</div>"+btn)
            pos=i+len('</div>')
        out.append(s[pos:])
        return "".join(out)
    def trim_tables(s):
        nonlocal gi
        out=[]; pos=0; open_='<tbody>'; close_='</tbody></table></div>'
        while True:
            j=s.find(open_, pos)
            if j<0: out.append(s[pos:]); break
            rows, i=_slices(s, j+len(open_), '<tr>', '</tr>')
            if not s.startswith(close_, i) or len(rows)<=KEEP or "".join(rows)!=s[j+len(open_):i].strip():
                out.append(s[pos:j+len(open_)]); pos=j+len(open_); continue
            out.append(s[pos:j])
            k=f"g{gi}"; gi+=1; J[k]="".join(rows[KEEP:])
            removed.extend(x for r in rows[KEEP:] for x in re.findall(r'href="\.\./tools/([a-z0-9-]+)\.html"', r)[:1])
            btn=f'<div class="morewrap" style="margin:14px 0 0;text-align:center"><button type="button" class="btn" data-more="{base}.more.json">Show all {len(rows):,} rows ({len(rows)-KEEP:,} more)</button></div>'
            out.append(open_[:-1]+f' data-mg="{k}">'+"".join(rows[:KEEP])+close_+btn)
            pos=i+len(close_)
        return "".join(out)
    s=trim_tables(trim_grids(s))
    if not J: print("lighten: no grid trimmed in",f); open(f,"w").write(_common(s)); return
    json.dump(J,open(mj,"w"),ensure_ascii=False,separators=(",",":"))
    m=re.search(r'<script src="([^"]*catfilter\.js[^"]*)"',s)
    if m and "__cfsrc" not in s: s=s.replace(m.group(0),f'<script>window.__cfsrc="{m.group(1)}"</script>'+m.group(0),1)
    s,nl=_linklist(s,removed,names, src=f)
    if f.startswith("categories/"): s=_trim_itemlist(s, K)
    if "<!--lt:more-->" not in s: s=s.replace("</body>","<!--lt:more-->"+MORE_JS+"</body>",1)
    open(f,"w").write(_common(s)); print(f"lighten: {f}: {len(removed)} cards deferred to {mj}, {nl} text links kept")
def leaderboard(names):
    f="leaderboard/index.html"
    if not os.path.exists(f): return
    s=open(f).read(); J={}; removed=[]
    def panel(m):
        pid=m.group(1); body=m.group(2); rows=[]; out=[]; i=0
        for r in re.finditer(r'<li class="lbr[^"]*"[^>]*>.*?</li>',body,re.S):
            if " data-x" in r.group(0)[:200]: rows.append([i,r.group(0)]); removed.append(re.search(r'href="\.\./tools/([a-z0-9-]+)\.html"',r.group(0)).group(1))
            i+=1
        if rows: J[pid]=rows
        b2=re.sub(r'<li class="lbr[^"]*"[^>]*data-x[^>]*>.*?</li>','',body,flags=re.S)
        return m.group(0).replace(body,b2)
    s=re.sub(r'<section role="tabpanel" id="(lb-[a-z]+)"[^>]*>(.*?)</section>',panel,s,flags=re.S)
    if J:
        json.dump(J,open("leaderboard/extra.json","w"),ensure_ascii=False,separators=(",",":"))
        js=('<script>(function(){var c=document.getElementById("lbctl");if(!c)return;var L=0;function go(){if(L)return;L=1;fetch("extra.json",{cache:"no-cache"}).then(function(r){return r.json()}).then(function(J){'
            'Object.keys(J).forEach(function(k){var o=document.querySelector("#"+k+" ol.lbl");if(!o)return;J[k].forEach(function(p){var t=document.createElement("ol");t.innerHTML=p[1];var li=t.firstChild,ref=o.children[p[0]];o.insertBefore(li,ref||null)})});'
            'var s=document.getElementById("lbcat");if(s)s.dispatchEvent(new Event("change"))})}'
            'c.addEventListener("change",go,true);if(/[?&](cat|free|os)=/.test(location.search))go()})()</script>')
        if "<!--lt:lbx-->" not in s: s=s.replace("</body>","<!--lt:lbx-->"+js+"</body>",1)
    s,nl=_linklist(s,removed,names,"More ranked tools (shown when you filter by category)")
    open(f,"w").write(_common(s)); print(f"lighten: leaderboard: {len(removed)} filter-only rows deferred to leaderboard/extra.json, {nl} text links kept")
def shrink_heavy(f, names):
    """Pages already past the byte budget: drop the logo list, trim JSON-LD, paginate the rest."""
    if not os.path.exists(f) or os.path.getsize(f)<=HEAVY: return
    s=open(f, encoding="utf-8").read()
    block=""
    m=re.search(r'<!--lt:all-->.*?<!--/lt:all-->', s, re.S)
    if m: block=m.group(0)
    else:
        m=re.search(r'<h2[^>]*>All tools on this page</h2>\s*(?:<p[^>]*>.*?</p>|<ul class="linkpile">.*?</ul>)', s, re.S)
        if m: block=m.group(0)
    slugs=[]
    if block:
        seen=set()
        for x in re.findall(r'href="\.\./tools/([a-z0-9-]+)\.html"', block):
            if x not in seen:
                seen.add(x); slugs.append(x)
        s=s.replace(block, "", 1)
    s=_trim_itemlist(s)
    if slugs:
        s, n=_linklist(s, slugs, names, src=f)
    else:
        n=0
    open(f,"w",encoding="utf-8").write(s)
    print(f"lighten shrink: {f} now {os.path.getsize(f)} bytes, {n} tools moved to later pages")
def run(t):
    names={x["slug"]:x["name"] for x in t}
    leaderboard(names)
    targets=["tasks/writing-code.html","categories/mcp-servers.html"]
    for f in glob.glob("categories/*.html"):
        if f.endswith("index.html"): continue
        try:
            if os.path.getsize(f)>HEAVY and f not in targets: targets.append(f)
        except OSError: pass
    for f in targets:
        if os.path.exists(f): grids(f,names)
    for f in list(targets):
        if f.startswith("categories/"): shrink_heavy(f, names)
if __name__=="__main__": run(json.load(open("tools.json")))
