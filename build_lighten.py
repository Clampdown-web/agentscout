"""Lighter heavy list pages (owner-approved SEO audit, Oct 22 2026 PT). Idempotent post-pass at the end of build_site.py.
Pages: leaderboard/, tasks/writing-code.html, categories/mcp-servers.html. Nothing is deleted:
1. The inline logo-retry onerror (~150 bytes on every img) becomes one delegated handler with the same behaviour.
2. Repeated inline category icons become one <symbol> each plus <use>.
3. Card grids show the first KEEP cards; the rest load from <page>.more.json on "Show all" (or at once when a filter/sort is used).
   Leaderboard filter-only rows (data-x, hidden until a filter is on) load from leaderboard/extra.json when a filter is used.
4. Crawlability: every tool that loses its static card keeps a plain text link on the page ("All tools on this page"),
   so every tool stays reachable and crawlable without JavaScript."""
import re,json,os,html
KEEP=48
KEEP_BY={"tasks/writing-code.html":12}  # many sub-grids: show 12 per section
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
def _linklist(s,removed,names,head="All tools on this page"):
    have=set(re.findall(r'href="\.\./tools/([a-z0-9-]+)\.html"',s))
    miss=[x for x in removed if x not in have]
    if not miss: return s,0
    lst=" · ".join(f'<a href="../tools/{x}.html">{html.escape(names.get(x,x))}</a>' for x in miss)
    blk=f'<!--lt:all--><section class="alltools" style="margin:28px 0 0"><h2 style="font-size:16px;margin:0 0 8px">{head}</h2><p class="muted" style="font-size:13.5px;line-height:1.9;overflow-wrap:anywhere">{lst}</p></section><!--/lt:all-->'
    return s.replace("</main>",blk+"</main>",1),len(miss)
def grids(f,names):
    K=KEEP_BY.get(f,KEEP)
    s=open(f).read(); base=os.path.basename(f)[:-5]; mj=f[:-5]+".more.json"; J={}; removed=[]; gi=0
    def grid(m):
        nonlocal gi
        open_,body=m.group(1),m.group(2)
        cards=re.findall(r'<a class="card tile".*?</a>',body,re.S)
        if len(cards)<=K+4 or "".join(cards)!=body.strip(): return m.group(0)
        k=f"g{gi}"; gi+=1; J[k]="".join(cards[K:])
        removed.extend(re.search(r'data-s="([^"]+)"',c).group(1) for c in cards[K:])
        o2=open_[:-1]+f' data-mg="{k}" data-total="{len(cards)}">'
        btn=f'<div class="morewrap" style="margin:14px 0 0;text-align:center"><button type="button" class="btn" data-more="{base}.more.json">Show all {len(cards):,} tools ({len(cards)-K:,} more)</button></div>'
        return o2+"".join(cards[:K])+"</div>"+btn
    s=re.sub(r'(<div class="grid"(?: id="cgrid")?>)((?:<a class="card tile".*?</a>)+)</div>',grid,s,flags=re.S)
    def table(m):
        nonlocal gi
        rows=re.findall(r'<tr>.*?</tr>',m.group(2),re.S)
        if len(rows)<=KEEP or "".join(rows)!=m.group(2).strip(): return m.group(0)
        k=f"g{gi}"; gi+=1; J[k]="".join(rows[KEEP:])
        removed.extend(x for r in rows[KEEP:] for x in re.findall(r'href="\.\./tools/([a-z0-9-]+)\.html"',r)[:1])
        return m.group(1)[:-1]+f' data-mg="{k}">'+"".join(rows[:KEEP])+'</tbody></table></div>'+f'<div class="morewrap" style="margin:14px 0 0;text-align:center"><button type="button" class="btn" data-more="{base}.more.json">Show all {len(rows):,} rows ({len(rows)-KEEP:,} more)</button></div>'
    s=re.sub(r'(<tbody>)((?:<tr>.*?</tr>)+)</tbody></table></div>',table,s,flags=re.S)
    if not J: print("lighten: no grid trimmed in",f); open(f,"w").write(_common(s)); return
    json.dump(J,open(mj,"w"),ensure_ascii=False,separators=(",",":"))
    m=re.search(r'<script src="([^"]*catfilter\.js[^"]*)"',s)
    if m and "__cfsrc" not in s: s=s.replace(m.group(0),f'<script>window.__cfsrc="{m.group(1)}"</script>'+m.group(0),1)
    s,nl=_linklist(s,removed,names)
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
def run(t):
    names={x["slug"]:x["name"] for x in t}
    leaderboard(names)
    for f in ("tasks/writing-code.html","categories/mcp-servers.html"):
        if os.path.exists(f): grids(f,names)
if __name__=="__main__": run(json.load(open("tools.json")))
