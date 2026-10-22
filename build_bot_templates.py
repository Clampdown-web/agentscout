"""Extra Bot templates (Oct 21 2026 PT, owner request): data/bot-templates-extra.json -> rows on /bot-templates/ and
one detail page each (bot-templates/<slug>.html). Idempotent; runs from build_site.py before build_tasks (nav/footer pass).
The original 32 templates are static pages from the Oct 19 launch; this only adds/refreshes the extra ones."""
import json,re,os,html
esc=html.escape
SITE="https://agentscouthq.com"; D="bot-templates"; MARK="<!-- btx-generated -->"
SHARE_SVG='<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7"/><path d="M16 6l-4-4-4 4"/><path d="M12 2v13"/></svg>'
PRETTY={"slack":"Slack","notion-workspace":"Notion","linear":"Linear","figma":"Figma","hex":"Hex","pstack":"pstack"}
TERMS=('<li>Terms for every marketplace bot (<a href="https://x.ai/legal/bot-sharing-terms" target="_blank" rel="noopener">x.ai third-party bot terms</a>): adding it lets the bot read, write and send data and use third-party services through the accounts you connect. You connect each account yourself.</li>'
 '<li>License (<a href="https://x.ai/legal/bot-sharing-terms" target="_blank" rel="noopener">x.ai third-party bot terms</a>): a limited, non-exclusive, revocable license to use the bot for your own purposes. You can\'t redistribute or re-share it without the creator\'s permission.</li>'
 '<li>What a template copies (<a href="https://x.ai/bot/guides/templates-for-grok-bot" target="_blank" rel="noopener">x.ai template guide</a>): instructions, memories, skills and first-party plugins, but not the creator\'s secrets, private skills or custom code.</li>')
def share(e,cls,label,txt=""):
    return (f'<button type="button" class="{cls}" data-share data-share-url="{SITE}/{D}/{e["slug"]}.html" data-share-title="{esc(e["name"])}: Grok Bot template by {esc(e["creator"])}" '
            f'data-share-text="{esc(e["desc"])}" aria-label="{label}">{SHARE_SVG}{txt}</button>')
def row(e):
    s=e["slug"]; n=esc(e["name"])
    return (f'<li class="bt-row" id="grok-{s}" data-plat="grok" data-q="{esc((e["name"]+" "+e["creator"]).lower())}"><img class="bt-ic logo" src="icons/creator-{s}.jpg" alt="{n} logo" width="32" height="32" loading="lazy" data-icon="official">'
            f'<div class="bt-txt"><div class="bt-nm"><a href="{s}.html"><b>{n}</b></a> <span>by {esc(e["creator"])}</span></div><p class="bt-d" title="{esc(e["desc"])}">{esc(e["desc"])}</p></div>'
            f'<span class="b bt-badge">Grok Bot</span><span class="sharewrap bt-share">{share(e,"btn sharebtn bt-sbtn","Share "+n)}<span class="sharecount" hidden></span></span>'
            f'<a class="btn bt-btn" href="{esc(e["url"])}" target="_blank" rel="noopener" aria-label="Add {n} (opens original listing)">Add</a></li>')
def tabs(e):
    T=[]
    if e["memories"]:
        m=[esc(x) for x in e["memories"][:8]]; rest=e["memories_total"]-len(m)
        if rest>0: m.append(f"{rest} more memories: see the original listing.")
        T.append(("Memories",f'Facts the bot starts with ({e["memories_total"]} on the listing)',m))
    if e["skills"]: T.append(("Skills",f'Playbooks it can run ({len(e["skills"])})',[f'<b>{esc(a)}</b>: {esc(b)}' if b else f'<b>{esc(a)}</b>' for a,b in e["skills"]]))
    if e["routines"]: T.append(("Routines",f'Jobs that run on their own ({len(e["routines"])})',[f'<b>{esc(a)}</b>: {esc(b)}' if b else f'<b>{esc(a)}</b>' for a,b in e["routines"]]))
    it=[f'<b>{esc(PRETTY.get(a,a))}</b>: {esc(b)}' if b else f'<b>{esc(PRETTY.get(a,a))}</b>' for a,b in e["integrations"]]
    T.append(("Integrations",f'Apps it can use ({len(e["integrations"])})' if it else "Apps it can use (none listed)",it+[TERMS]))
    nm=esc(e["name"])
    h=f'<div class="bd-tabs" role="tablist" aria-label="{nm} details">'+"".join(f'<button type="button" role="tab" id="t-{i}" aria-controls="p-{i}" aria-selected="{"true" if i==0 else "false"}" tabindex="{0 if i==0 else -1}">{t[0]}</button>' for i,t in enumerate(T))+'</div>\n'
    h+="".join(f'<div class="bd-panel" role="tabpanel" id="p-{i}" aria-labelledby="t-{i}"{"" if i==0 else " hidden"}><h2>{t[1]}</h2><ul>'+"".join(f"<li>{x}</li>" for x in t[2])+'</ul></div>' for i,t in enumerate(T))
    return h
def detail(e,shell,rel):
    s=e["slug"]; nm=esc(e["name"]); cr=esc(e["creator"]); title=f'{e["name"]}: Grok Bot template by {e["creator"]}'
    md=f'{e["name"]} by {e["creator"]}: {e["desc"]}'; url=f"{SITE}/{D}/{s}.html"
    h=shell
    h=re.sub(r'<title>.*?</title>',f'<title>{esc(title)} · AgentScout</title>',h,count=1)
    h=re.sub(r'(<meta name="description" content=")[^"]*',lambda m:m.group(1)+esc(md),h,count=1)
    h=re.sub(r'(<link rel="canonical" href=")[^"]*',lambda m:m.group(1)+url,h,count=1)
    for k,v in (("og:title",title),("og:description",md),("og:url",url)): h=re.sub(rf'(<meta property="{k}" content=")[^"]*',lambda m:m.group(1)+esc(v),h,count=1)
    for k,v in (("twitter:title",title),("twitter:description",md)): h=re.sub(rf'(<meta name="{k}" content=")[^"]*',lambda m:m.group(1)+esc(v),h,count=1)
    cw=json.dumps({"@context":"https://schema.org","@type":"CreativeWork","name":e["name"],"description":e["desc"],"url":url,"sameAs":e["url"],"author":{"@type":"Person","name":e["creator"]}},ensure_ascii=False)
    h=re.sub(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "CreativeWork".*?</script>',lambda m:f'<script type="application/ld+json">{cw}</script>',h,count=1,flags=re.S)
    bc=json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":SITE+"/"},{"@type":"ListItem","position":2,"name":"Bot templates","item":f"{SITE}/{D}/"},{"@type":"ListItem","position":3,"name":e["name"],"item":url}]},ensure_ascii=False)
    h=re.sub(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "BreadcrumbList".*?</script>',lambda m:f'<script type="application/ld+json">{bc}</script>',h,count=1,flags=re.S)
    main=(f'<main class="wrap bt" data-pagefind-body>{MARK}\n<a class="bd-back" href="index.html">← Bot templates</a>\n'
      f'<div class="bd-top"><img class="bt-ic big logo" src="icons/creator-{s}.jpg" alt="{nm} logo" width="84" height="84" loading="lazy" data-icon="official"><div><h1 data-pagefind-weight="10">{nm}</h1><div class="bd-meta"><span>by {cr}</span><span class="b">Grok Bot</span></div></div></div>\n'
      f'<p class="bd-long">{esc(e["long"])}</p>\n'
      f'<div class="bd-cta"><a class="btn primary" href="{esc(e["url"])}" target="_blank" rel="noopener">Add on x.ai ↗</a><span class="sharewrap">{share(e,"btn sharebtn","Share this page","Share")}<span class="sharecount" hidden></span></span></div>\n'
      +tabs(e)+
      f'\n<p class="bd-src">Taken from the {nm} listing on x.ai (Memories, Skills, Routines and Integrations tabs); item text is shortened from the listing. Anything stated nowhere is marked "Not stated".</p>\n'
      '<section class="bd-rel"><h2 class="bt-h">More Grok Bot templates</h2><ul>'+"".join(f'<li><a href="{a}.html">{esc(b)}</a> <span class="bt-by">by {esc(c)}</span></li>' for a,b,c in rel)+'</ul></section>\n'
      f'<p class="bt-disc">AgentScout links to the original public listings and doesn\'t host copies. We aren\'t affiliated with xAI, Anthropic, OpenAI, OpenClaw, Cursor, n8n or the creators listed. Names and logos belong to their owners. Grok Bot cards show the creator\'s photo from the x.ai marketplace. Listing checked {e["checked_h"]}.</p>\n'
      f'<span id="pfm" hidden><span data-pagefind-filter="type:Guides & best-of"></span><span data-pagefind-meta="logo:/{D}/icons/creator-{s}.jpg"></span><span data-pagefind-sort="date:{e["checked"]}"></span><span data-pagefind-meta="type:Guides & best-of"></span></span></main>')
    return h[:h.find('<main')]+main+h[h.find('</main>')+7:]
def run():
    if not os.path.exists("data/bot-templates-extra.json"): return
    X=json.load(open("data/bot-templates-extra.json"))
    import datetime
    for e in X: e["checked_h"]=datetime.date.fromisoformat(e["checked"]).strftime("%b %-d, %Y")
    ip=f"{D}/index.html"; s=open(ip).read()
    s=re.sub(r'<!--btx-->.*?<!--/btx-->','',s,flags=re.S)
    base=[m for m in re.findall(r'<li class="bt-row" id="([^"]+)"',s)]
    X=[e for e in X if f'grok-{e["slug"]}' not in base and not os.path.exists(f"{D}/{e['slug']}.html") or (os.path.exists(f"{D}/{e['slug']}.html") and MARK in open(f"{D}/{e['slug']}.html").read())]
    anchor='</ul></section><section class="bt-sec" data-sec="claude">'
    assert anchor in s
    s=s.replace(anchor,'<!--btx-->'+"".join(row(e) for e in X)+'<!--/btx-->'+anchor,1)
    total=len(base)+len(X)
    s=re.sub(r'\b\d+ ready-made',f'{total} ready-made',s)
    def il(m):
        o=json.loads(m.group(1)); ex={f"{SITE}/{D}/{e['slug']}.html" for e in X}
        L=[i for i in o["itemListElement"] if i["url"] not in ex]
        # put extras right after the last Grok Bot item (same order as the page)
        g=[k for k,i in enumerate(L) if i["url"].rsplit('/',1)[-1].replace('.html','') in ("overheard","dr-eggbot","haggle-bot","seo-aeo-desk","competitor-watch","nightly-audit-engineer")]
        at=(max(g)+1) if g else len(L)
        L=L[:at]+[{"@type":"ListItem","position":0,"name":e["name"],"url":f"{SITE}/{D}/{e['slug']}.html"} for e in X]+L[at:]
        for k,i in enumerate(L): i["position"]=k+1
        o["itemListElement"]=L; o["numberOfItems"]=len(L)
        return '<script type="application/ld+json">'+json.dumps(o)+'</script>'
    s=re.sub(r'<script type="application/ld\+json">(\{"@context": "https://schema.org", "@type": "ItemList".*?)</script>',il,s,count=1,flags=re.S)
    open(ip,"w").write(s)
    shell=open(f"{D}/haggle-bot.html").read()
    pool=[(e["slug"],e["name"],e["creator"]) for e in X]
    for k,e in enumerate(X):
        rel=[p for p in pool[k+1:]+pool[:k]][:4]
        open(f"{D}/{e['slug']}.html","w").write(detail(e,shell,rel))
    print(f"bot templates: {len(X)} extra, {total} total")

# ---- Filters (Oct 21 2026 PT, owner request): count pill, search, use-case chips, URL params, empty state. ----
FCSS=('<style id="btf-css">.bt-h1{flex-wrap:wrap;row-gap:4px}.bt-count{display:inline-flex;align-items:center;justify-content:center;min-width:2.2em;height:1.5em;padding:0 .45em;margin-left:.4em;border-radius:999px;background:var(--soft);border:1px solid var(--line);color:var(--muted);font-size:.5em;font-weight:600;vertical-align:middle}'
 '.btf{margin:14px 0 6px;display:flex;flex-direction:column;gap:10px;min-width:0}.btf-s{position:relative;max-width:520px}.btf-s input{width:100%;box-sizing:border-box;min-height:44px;padding:0 12px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--text);font:inherit;font-size:16px}'
 '.bt-pills,.btf-cats{display:flex;gap:8px;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:thin;padding-bottom:4px;min-width:0;max-width:100%}.bt-pills .chip,.btf-cats .chip{flex:0 0 auto;white-space:nowrap}'
 '.btf-lbl{font-size:13px;color:var(--muted);margin:0}.btf-st{font-size:14px;color:var(--muted);margin:4px 0 0}.bt-empty{display:none;padding:28px 12px;text-align:center;border:1px dashed var(--line);border-radius:12px;margin:16px 0}.bt-empty p{margin:0 0 12px}'
 '.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}'
 '@media(min-width:900px){.bt-pills,.btf-cats{flex-wrap:wrap;overflow:visible}}</style>')
FJS=r'''<script id="btf-js">(function(){var $=function(s){return document.querySelector(s)},A=function(s){return [].slice.call(document.querySelectorAll(s))};
var q=$('#bt-q'),rows=A('.bt-row'),P=A('.bt-pills .chip'),C=A('.btf-cats .chip'),st=$('#bt-status'),em=$('#bt-empty'),cnt=$('#bt-count'),f='all',c='all',T=rows.length;
if(cnt)cnt.textContent=T;
function sync(){var u=new URLSearchParams(location.search),s=q.value.trim();s?u.set('q',s):u.delete('q');c!=='all'?u.set('cat',c):u.delete('cat');f!=='all'?u.set('platform',f):u.delete('platform');var x=u.toString();history.replaceState(null,'',location.pathname+(x?'?'+x:'')+location.hash)}
function apply(nosync){var s=q.value.trim().toLowerCase(),n=0;
 A('.bt-sec').forEach(function(sec){var k=0;sec.querySelectorAll('.bt-row').forEach(function(r){var ok=(f==='all'||r.dataset.plat===f)&&(c==='all'||(' '+r.dataset.cat+' ').indexOf(' '+c+' ')>-1)&&(!s||r.dataset.q.indexOf(s)>-1);r.hidden=!ok;if(ok)k++});sec.hidden=!k;n+=k});
 var fl=f!=='all'||c!=='all'||!!s;$('#bt-featured').hidden=fl;em.style.display=n?'none':'block';
 st.textContent='Showing '+n+' of '+T+' templates';if(!nosync)sync()}
function pick(L,b){L.forEach(function(x){var on=x===b;x.classList.toggle('on',on);x.setAttribute('aria-pressed',on)})}
P.forEach(function(b){b.addEventListener('click',function(){f=b.dataset.f;pick(P,b);apply()})});
C.forEach(function(b){b.addEventListener('click',function(){c=b.dataset.c;pick(C,b);apply()})});
q.addEventListener('input',function(){apply()});
A('[data-bt-reset]').forEach(function(b){b.addEventListener('click',function(){q.value='';f='all';c='all';pick(P,P[0]);pick(C,C[0]);apply()})});
var u=new URLSearchParams(location.search),h=(location.hash||'').slice(1),pf=u.get('platform')||h,ct=u.get('cat');
var m=P.filter(function(b){return b.dataset.f===pf})[0];if(m){f=pf;pick(P,m)}
m=C.filter(function(b){return b.dataset.c===ct})[0];if(m){c=ct;pick(C,m)}
if(u.get('q'))q.value=u.get('q');apply(true)})();</script>'''
def filters():
    s=open(f"{D}/index.html").read(); M=json.load(open("data/bot-templates-cats.json")); CATS=M["_cats"]
    X={e["slug"]:e for e in json.load(open("data/bot-templates-extra.json"))}
    cnt={k:0 for k in CATS}; total=0
    def fix(m):
        nonlocal total; tag=m.group(0); rid=re.search(r'id="([^"]+)"',tag).group(1); total+=1
        cats=M.get(rid) or (print(f"bot templates: WARN no category for {rid}") or ["productivity"])
        for k in cats: cnt[k]+=1
        tag=re.sub(r' data-cat="[^"]*"','',tag)
        return tag[:-1]+f' data-cat="{" ".join(cats)}">'
    s=re.sub(r'<li class="bt-row" id="[^"]+"[^>]*>',fix,s)
    # enrich search text with description + platform (and creator for static rows)
    def dq(m):
        li=m.group(0); nm=re.search(r'<b>(.*?)</b>',li); by=re.search(r'<span>by (.*?)</span>',li) or re.search(r'class="bt-by">(.*?)<',li)
        d=re.search(r'class="bt-d"[^>]*>(.*?)</p>',li); pl=re.search(r'class="b bt-badge">(.*?)<',li)
        txt=" ".join(html.unescape(re.sub('<[^>]+>','',x.group(1))) for x in (nm,by,d,pl) if x).lower()
        return re.sub(r'data-q="[^"]*"',lambda _:f'data-q="{esc(txt)}"',li,count=1)
    s=re.sub(r'<li class="bt-row".*?</li>',dq,s,flags=re.S)
    s=re.sub(r'<span id="bt-count"[^>]*>.*?</span>','',s)
    s=s.replace('Bot templates</h1>',f'Bot templates<span id="bt-count" class="bt-count" aria-label="{total} templates">{total}</span></h1>',1)
    s=re.sub(r'<!--btf-->.*?<!--/btf-->','',s,flags=re.S)
    s=s.replace('<input id="bt-q" type="hidden" value="">','')
    ui=('<!--btf--><div class="btf"><div class="btf-s"><label for="bt-q" class="sr-only">Search bot templates</label><input id="bt-q" type="search" placeholder="Search by name, creator, task or platform" autocomplete="off" enterkeyhint="search"></div>'
        '<p class="btf-lbl" id="btf-cl">Use case</p><div class="btf-cats" role="group" aria-labelledby="btf-cl"><button type="button" class="chip on" data-c="all" aria-pressed="true">All uses</button>'
        +"".join(f'<button type="button" class="chip" data-c="{k}" aria-pressed="false">{esc(v)} <span aria-hidden="true">· {cnt[k]}</span></button>' for k,v in CATS.items() if cnt[k])+
        f'</div><p id="bt-status" class="btf-st" role="status" aria-live="polite">Showing {total} of {total} templates</p></div><!--/btf-->')
    i=s.find('</div>',s.find('<div class="bt-pills"'))+6; s=s[:i]+ui+s[i:]
    s=re.sub(r'<div id="bt-empty" class="bt-empty">.*?</div>','<div id="bt-empty" class="bt-empty"><p>No templates match those filters.</p><button type="button" class="btn" data-bt-reset>Reset filters</button></div>',s,count=1,flags=re.S)
    s=re.sub(r'<style id="btf-css">.*?</style>','',s,flags=re.S); s=s.replace('</head>',FCSS+'</head>',1)
    s=re.sub(r'<script id="btf-js">.*?</script>','',s,flags=re.S)
    s=re.sub(r'<script>\(function\(\)\{var pills=.*?</script>','',s,count=1,flags=re.S)
    s=s.replace('<script src="/navsearch.js',FJS+'<script src="/navsearch.js',1)
    open(f"{D}/index.html","w").write(s)
    print("bot templates filters:",total,"rows;",", ".join(f"{CATS[k]} {v}" for k,v in cnt.items()))
_run0=run
def run():
    _run0(); filters()

if __name__=="__main__": run()
