"""Extra Bot templates (Oct 21 2026 PT, owner request): data/bot-templates-extra.json -> rows on /bot-templates/ and
one detail page each (bot-templates/<slug>.html). Idempotent; runs from build_site.py before build_tasks (nav/footer pass).
The original templates (32 at launch) are static pages from the Oct 19 launch; this only adds/refreshes the extra ones."""
import json,re,os,html,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from pack_builder_html import pack_section_html
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
def oss_row(e):
    n=esc(e["name"]); o=e["repo"].split("/")[0]; u="https://github.com/"+e["repo"]; st=f'{e["stars"]:,}'
    lic=f' · {esc(e["license"])}' if e.get("license") and e["license"]!="NOASSERTION" else ""
    return (f'<li class="bt-row" id="{e["id"]}" data-plat="grok" data-q="{esc((e["name"]+" "+o).lower())}"><img class="bt-ic logo" src="icons/gh-{o.lower()}.png" alt="{esc(o)} avatar" width="32" height="32" loading="lazy">'
            f'<div class="bt-txt"><div class="bt-nm"><a href="{u}" target="_blank" rel="noopener"><b>{n}</b></a> <span>by @{esc(o)} · ★ {st} on GitHub{lic}</span></div><p class="bt-d" title="{esc(e["desc"])}">{esc(e["desc"])}</p></div>'
            f'<span class="b bt-badge">Open source</span>'
            f'<a class="btn bt-btn" href="{u}" target="_blank" rel="noopener" aria-label="View {n} on GitHub (opens in new tab)">GitHub</a></li>')
CB_LABEL="Community bot (via awesome-grokbot), vetted by AgentScout"
def cb_row(e):
    n=esc(e["name"]); h=esc(e["handle"])
    return (f'<li class="bt-row" id="{e["id"]}" data-plat="grok" data-q="{esc((e["name"]+" "+e["handle"]).lower())}"><img class="bt-ic logo" src="icons/{esc(e.get('logo') or 'community-bot.svg')}" alt="{n} logo" width="32" height="32" loading="lazy">'
            f'<div class="bt-txt"><div class="bt-nm"><a href="{esc(e["url"])}" target="_blank" rel="noopener"><b>{n}</b></a> <span>by <a href="https://x.com/{h}" target="_blank" rel="noopener">@{h}</a> · {CB_LABEL}</span></div><p class="bt-d" title="{esc(e["desc"])}">{esc(e["desc"])}</p></div>'
            f'<span class="b bt-badge">Community</span>'
            f'<a class="btn bt-btn" href="{esc(e["url"])}" target="_blank" rel="noopener" aria-label="Add {n} (opens share page on x.ai)">Add</a></li>')
UC_LABEL="Official x.ai use case"
def uc_row(e):
    n=esc(e["name"]); act=' · <span class="bt-act">Acts with your approval</span>' if e.get("acts") else ""
    return (f'<li class="bt-row" id="{e["id"]}" data-plat="grok" data-q="{esc((e["name"]+" "+e["creator"]).lower())}"><img class="bt-ic logo" src="icons/{esc(e.get('logo') or 'official-use-case.svg')}" alt="{n} icon" width="32" height="32" loading="lazy">'
            f'<div class="bt-txt"><div class="bt-nm"><a href="{esc(e["url"])}" target="_blank" rel="noopener"><b>{n}</b></a> <span>by {esc(e["creator"])} · <a href="https://x.ai/bot/use-cases" target="_blank" rel="noopener">{UC_LABEL}</a>{act}</span></div><p class="bt-d" title="{esc(e["desc"])}">{esc(e["desc"])}</p></div>'
            f'<span class="b bt-badge">Official</span>'
            f'<a class="btn bt-btn" href="{esc(e["url"])}" target="_blank" rel="noopener" aria-label="Add {n} (opens share page on x.ai)">Add</a></li>')
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
    OSS=json.load(open("data/bot-templates-oss.json")) if os.path.exists("data/bot-templates-oss.json") else []
    CB=json.load(open("data/bot-templates-community.json")) if os.path.exists("data/bot-templates-community.json") else []
    UC=json.load(open("data/bot-templates-official.json")) if os.path.exists("data/bot-templates-official.json") else []
    s=s.replace(anchor,'<!--btx-->'+"".join(row(e) for e in X)+"".join(uc_row(e) for e in UC)+"".join(oss_row(e) for e in OSS)+"".join(cb_row(e) for e in CB)+'<!--/btx-->'+anchor,1)
    total=len(base)+len(X)+len(UC)+len(OSS)+len(CB)
    s=re.sub(r'\b\d+ ready-made',f'{total} ready-made',s)
    s=re.sub(r'ready-made bots, skills,? (?:and )?workflows','ready-made bots, skills, plugins and workflows',s)  # owner-approved title wording, Oct 21 2026
    # Short index title (owner-approved Oct 21 2026, 7:26 PM PT): under 60 chars so Google does not truncate it
    T=f'AI bot templates, plugins & skills: {total} ready-made'  # owner rename Oct 21 2026 7:49 PM PT (fits all platforms; 'Grok Bot' kept in H1/meta)
    s=re.sub(r'<title>[^<]*</title>',f'<title>{html.escape(T)}</title>',s,count=1)
    for k in ('property="og:title"','name="twitter:title"'): s=re.sub(rf'(<meta {k} content=")[^"]*',lambda m:m.group(1)+html.escape(T),s,count=1)
    # ItemList from every row on the page, in page order (Ops follow-up Oct 21 2026): numberOfItems == rows shown
    def il_all(m):
        o=json.loads(m.group(1)); old={i["url"]:i["name"] for i in o["itemListElement"]}
        L=[]
        for r in re.findall(r'<li class="bt-row".*?</li>',s,flags=re.S):
            h=re.search(r'<a href="([^"]+)"[^>]*><b>(.*?)</b>',r)
            if not h: continue
            u=h.group(1) if h.group(1).startswith("http") else f"{SITE}/{D}/{h.group(1)}"
            L.append({"@type":"ListItem","position":len(L)+1,"name":old.get(u) or html.unescape(re.sub(r'<[^>]+>','',h.group(2))),"url":u})
        o["itemListElement"]=L; o["numberOfItems"]=len(L)
        return '<script type="application/ld+json">'+json.dumps(o)+'</script>'
    s=re.sub(r'<script type="application/ld\+json">(\{"@context": "https://schema.org", "@type": "ItemList".*?)</script>',il_all,s,count=1,flags=re.S)
    open(ip,"w").write(s)
    shell=open(f"{D}/haggle-bot.html").read()
    pool=[(e["slug"],e["name"],e["creator"]) for e in X]
    for k,e in enumerate(X):
        rel=[p for p in pool[k+1:]+pool[:k]][:4]
        open(f"{D}/{e['slug']}.html","w").write(detail(e,shell,rel))
    print(f"bot templates: {len(X)} extra, {total} total")
    # Keep every hardcoded template count in sync with the data (Oct 21 2026): homepage strip source + preview copy
    SUB="Ready-made bots, skills, plugins and workflows for Grok Bot, Claude, Codex, OpenClaw, Cursor and n8n."
    for fp in ("data/bt-strip.inc","preview/site-test/index.html"):
        if os.path.exists(fp):
            t=open(fp).read(); t2=re.sub(r'See all \d+ →',f'See all {total} →',t)
            t2=re.sub(r'(<p class="btsub">)[^<]*(</p>)',lambda m:m.group(1)+SUB+m.group(2),t2)
            t2=re.sub(r'(?i)AI\s+Agents\s+Directory','AgentScout, the AI agent tools directory',t2)  # no rival names (owner, Oct 22 2026)
            if t2!=t: open(fp,"w").write(t2)

# ---- Filters (Oct 21 2026 PT, owner request): count pill, search, use-case chips, URL params, empty state. ----
FCSS=('<style id="btf-css">.bt-h1{flex-wrap:wrap;white-space:normal;overflow-wrap:anywhere;row-gap:4px}.bt-count{display:inline-flex;align-items:center;justify-content:center;min-width:2.2em;height:1.5em;padding:0 .45em;margin-left:.4em;border-radius:999px;background:var(--soft);border:1px solid var(--line);color:var(--muted);font-size:.5em;font-weight:600;vertical-align:middle}'
 '.btf{margin:14px 0 6px;display:flex;flex-direction:column;gap:10px;min-width:0}.btf-s{position:relative;max-width:520px}.btf-s input{width:100%;box-sizing:border-box;min-height:44px;padding:0 12px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--text);font:inherit;font-size:16px}'
 '.bt-pills,.btf-cats{display:flex;flex-wrap:wrap;gap:8px;overflow:hidden;padding-bottom:4px;min-width:0;max-width:100%}.bt-pills .chip,.btf-cats .chip{flex:0 1 auto;white-space:normal;max-width:100%;height:auto;overflow-wrap:anywhere}'
 '.bt-row,.bt-txt,.bt-grid{min-width:0;max-width:100%}.bt-act,.bt-d,.bt-nm{white-space:normal;overflow-wrap:anywhere;text-overflow:clip;max-width:100%}'
 '@media(max-width:1100px){.bt-pills,.btf-cats{flex-wrap:wrap!important;overflow-x:hidden!important}.bt-pills .chip,.btf-cats .chip{white-space:normal;max-width:100%}}'
 '.btf-lbl{font-size:13px;color:var(--muted);margin:0}.btf-st{font-size:14px;color:var(--muted);margin:4px 0 0}.bt-empty{display:none;padding:28px 12px;text-align:center;border:1px dashed var(--line);border-radius:12px;margin:16px 0}.bt-empty p{margin:0 0 12px}'
 '.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}'
 '@media(min-width:900px){.bt-pills,.btf-cats{overflow:visible}}'
 '@media(max-width:480px){div.bt-nm{flex-wrap:wrap;row-gap:0;min-height:0}div.bt-nm>a{min-height:32px;max-width:100%}div.bt-nm>span{flex:1 1 100%;font-size:13px;flex-wrap:wrap;white-space:normal;column-gap:.25em;row-gap:0}div.bt-nm span a{flex:0 0 auto;max-width:100%;min-height:32px;line-height:32px}}</style>')  # Oct 25 2026 PT post-update pass: byline links were squeezed to 0-27px at 360px; wrap byline under name on phones
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
    if os.path.exists("data/bot-templates-community.json"):
        for e in json.load(open("data/bot-templates-community.json")): M.setdefault(e["id"],e["cats"])
    if os.path.exists("data/bot-templates-official.json"):
        for e in json.load(open("data/bot-templates-official.json")): M.setdefault(e["id"],e["cats"])
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
    s=re.sub(r'((?:Bot templates|AI bot templates|Grok Bot templates, plugins &amp; skills))</h1>',rf'\1<span id="bt-count" class="bt-count" aria-label="{total} templates">{total}</span></h1>',s,count=1)
    s=re.sub(r'<!--bt-anim-->.*?<!--/bt-anim-->','',s,flags=re.S)
    s=re.sub(r'<!--btf-->.*?<!--/btf-->','',s,flags=re.S)
    s=s.replace('<input id="bt-q" type="hidden" value="">','')
    ui=('<!--bt-anim--><figure style="margin:16px 0 20px;border-radius:14px;overflow:hidden;border:1px solid var(--line);background:#080810"><video autoplay loop muted playsinline preload="metadata" poster="../assets/animations/agentscout-bot-constellation-poster.png" style="display:block;width:100%;height:auto;max-width:100%"><source src="../assets/animations/agentscout-bot-constellation.mp4" type="video/mp4"></video></figure><!--/bt-anim--><!--btf--><div class="btf"><div class="btf-s" hidden><label for="bt-q" class="sr-only">Search bot templates</label><input id="bt-q" type="search" placeholder="Search by name, creator, task or platform" autocomplete="off" enterkeyhint="search" hidden></div>'
        '<p class="btf-lbl" id="btf-cl">Use case</p><div class="btf-cats" role="group" aria-labelledby="btf-cl"><button type="button" class="chip on" data-c="all" aria-pressed="true">All uses</button>'
        +"".join(f'<button type="button" class="chip" data-c="{k}" aria-pressed="false">{esc(v)} <span aria-hidden="true">· {cnt[k]}</span></button>' for k,v in CATS.items() if cnt[k])+
        f'</div><p id="bt-status" class="btf-st" role="status" aria-live="polite">Showing {total} of {total} templates</p></div><!--/btf-->')
    i=s.find('</div>',s.find('<div class="bt-pills"'))+6; s=s[:i]+ui+s[i:]
    s=re.sub(r'<div id="bt-empty" class="bt-empty">.*?</div>','<div id="bt-empty" class="bt-empty"><p>No templates match those filters.</p><button type="button" class="btn" data-bt-reset>Reset filters</button></div>',s,count=1,flags=re.S)
    s=re.sub(r'<style id="btf-css">.*?</style>','',s,flags=re.S); s=re.sub(r'<style id="bt-mba-css">.*?</style>','',s,flags=re.S); s=s.replace('</head>',FCSS+MBA_CSS+'</head>',1)
    s=re.sub(r'<script id="btf-js">.*?</script>','',s,flags=re.S)
    s=re.sub(r'<script>\(function\(\)\{var pills=.*?</script>','',s,count=1,flags=re.S)
    s=s.replace('</body>',FJS+'</body>',1)  # menu search box removed Oct 23 2026
    s=re.sub(r"<!--bt-mba-->.*?<!--/bt-mba-->","",s,flags=re.S)
    s=s.replace('<section id="bt-featured">',made_by_agentscout_html(total)+'<section id="bt-featured">',1)
    open(f"{D}/index.html","w").write(s)
    print("bot templates filters:",total,"rows;",", ".join(f"{CATS[k]} {v}" for k,v in cnt.items()))
# Tap targets (Oct 22 2026 PT, owner "fix what's broken"): back link + related links were 19-22px tall at 390px; >=44px via min-height/padding only, no color change.
TAPCSS='<style id="bt-tap-css">.bd-back{display:inline-flex;align-items:center;min-height:44px;padding-right:8px}.bd-rel li a{display:inline-flex;align-items:center;min-height:44px}</style>'
def tap():
    n=0
    for f in sorted(os.listdir(D)):
        if not f.endswith(".html") or f=="index.html": continue
        fp=f"{D}/{f}"; s=open(fp).read()
        if 'class="bd-back"' not in s and 'class="bd-rel"' not in s: continue
        t=re.sub(r'<style id="bt-tap-css">.*?</style>','',s,flags=re.S).replace('</head>',TAPCSS+'</head>',1)
        if t!=s: open(fp,"w").write(t); n+=1
    print("bot templates tap css:",n,"pages")

def verify_logos():
    s=open(f"{D}/index.html").read()
    srcs=re.findall(r'<img[^>]+class="bt-ic[^"]*"[^>]+src="icons/([^"]+)"',s)
    bad=[x for x in srcs if x in ("community-bot.svg","official-use-case.svg","default.svg") or not os.path.exists(f"{D}/icons/{x}") or os.path.getsize(f"{D}/icons/{x}")<100 or os.path.getsize(f"{D}/icons/{x}")>20000]
    over=[fn for fn in os.listdir(f"{D}/icons") if os.path.isfile(f"{D}/icons/{fn}") and os.path.getsize(f"{D}/icons/{fn}")>20000]
    assert not bad and not over, f"bot templates logo check failed (generic, missing, or >20KB icons): bad={bad} over20KB={over}"
    print(f"bot templates logos verified: {len(srcs)}/{len(srcs)} real icons <=20KB on /{D}/index.html (0 generic)")

MBA_CSS = """<style id="bt-mba-css">
.bt-hub-bar{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0 18px;padding:12px 14px;border-radius:12px;background:var(--card);border:1.5px solid rgba(16,185,129,.45);align-items:center;justify-content:space-between;box-shadow:0 0 16px rgba(16,185,129,.12)}
.bt-hub-tabs{display:flex;flex-wrap:wrap;gap:8px}
.bt-hub-tab{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:999px;font-size:13px;font-weight:800;text-decoration:none;min-height:40px}
.bt-hub-tab.pro{background:linear-gradient(135deg,#84cc16,#10b981);color:#05140b;box-shadow:0 0 14px rgba(132,204,22,.45)}
.bt-hub-tab.comm{background:var(--soft);color:var(--text);border:1px solid var(--line)}
.bt-hub-tab.vid{background:rgba(249,115,22,.14);color:#ea580c;border:1.5px solid rgba(249,115,22,.5)}
@media(prefers-color-scheme:dark){.bt-hub-tab.vid{color:#fb923c}}
html[data-theme="dark"] .bt-hub-tab.vid{color:#fb923c}
.mba-sec img.aswm{filter:invert(1) hue-rotate(180deg)}
.mba-builtby{display:inline-flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:4px;font-size:12.5px;font-weight:700;color:#e5e7eb;margin:4px auto 6px;text-align:center}
.mba-builtby img.aswm{height:1.38em;vertical-align:-.34em;margin:0 -.35em 0 .08em}
section.mba-sec,.bt section.mba-sec{margin:14px 0 26px;padding:22px;border-radius:16px;border:2px solid rgba(16,185,129,.65);background:linear-gradient(155deg,#090d0a 0%,#11150d 55%,#16110b 100%);color:#fafaf9;box-shadow:0 14px 36px rgba(0,0,0,.45),0 0 24px rgba(16,185,129,.18);min-width:0}
.mba-notice{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:10px;padding:14px 18px;margin-bottom:16px;border-radius:12px;background:rgba(132,204,22,.12);border:1.5px solid rgba(163,230,53,.5);font-size:13px;line-height:1.5;color:#ecfccb;box-sizing:border-box}
.mba-notice a{color:#fde047;font-weight:700;text-decoration:underline}
.mba-head{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:12px;margin-bottom:16px;padding:18px 20px;border-radius:12px;background:rgba(16,18,14,.92);border:1.5px solid rgba(52,211,153,.4);box-sizing:border-box}
.mba-eyebrow{display:inline-flex;align-items:center;justify-content:center;text-align:center;gap:6px;padding:6px 14px;border-radius:999px;background:rgba(16,185,129,.18);border:1.5px solid #34d399;color:#6ee7b7;font-size:11.5px;font-weight:800;letter-spacing:.03em;text-transform:uppercase;margin:0 auto 8px;box-shadow:0 0 12px rgba(16,185,129,.35)}
.mba-head h2{margin:0 auto 8px;font-size:clamp(19px,2.5vw,25px);line-height:1.3;color:#fff;text-align:center;display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:6px}
.mba-head p{margin:0 auto;padding:0 10px;font-size:14px;line-height:1.55;color:#d6d3d1;max-width:800px;text-align:center;box-sizing:border-box}
.mba-vid{margin:0 0 16px;border-radius:12px;overflow:hidden;border:1.5px solid rgba(163,230,53,.45);background:#0a0906;line-height:0;box-shadow:0 0 20px rgba(132,204,22,.18)}
.mba-vid video{display:block;width:100%;height:auto;max-width:100%;object-fit:contain}
.mba-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-bottom:14px}
.mba-card{display:flex;flex-direction:column;justify-content:space-between;align-items:center;text-align:center;padding:20px 18px;border-radius:12px;background:rgba(16,18,14,.95);border:2px solid rgba(132,204,22,.5);min-width:0;gap:12px;transition:transform .15s,box-shadow .15s;box-sizing:border-box}
.mba-card:hover{transform:translateY(-2px)}
.mba-card>div{width:100%;display:flex;flex-direction:column;align-items:center;text-align:center}
.mba-card.neon-lime{border-color:#84cc16;background:linear-gradient(180deg,rgba(132,204,22,.14) 0%,rgba(14,18,12,.96) 55%);box-shadow:0 8px 26px rgba(132,204,22,.22),0 0 18px rgba(163,230,53,.24)}
.mba-card.neon-gold{border-color:#eab308;background:linear-gradient(180deg,rgba(234,179,8,.14) 0%,rgba(18,16,10,.96) 55%);box-shadow:0 8px 26px rgba(234,179,8,.22),0 0 18px rgba(250,204,21,.24)}
.mba-card.neon-orange{border-color:#f97316;background:linear-gradient(180deg,rgba(249,115,22,.15) 0%,rgba(20,13,10,.96) 55%);box-shadow:0 8px 26px rgba(249,115,22,.24),0 0 18px rgba(251,146,60,.25)}
.mba-card.neon-red{border-color:#ef4444;background:linear-gradient(180deg,rgba(239,68,68,.15) 0%,rgba(20,11,12,.96) 55%);box-shadow:0 8px 26px rgba(239,68,68,.24),0 0 18px rgba(248,113,113,.25)}
.mba-card-top{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;width:100%}
.mba-price{font-size:24px;font-weight:900;color:#fff;line-height:1}
.mba-price small{font-size:12px;font-weight:600;color:#d6d3d1}
.mba-tag{display:inline-flex;align-items:center;justify-content:center;padding:4px 10px;border-radius:999px;font-size:11px;font-weight:800;letter-spacing:.03em;text-transform:uppercase}
.mba-card h3{margin:0 auto;font-size:16.5px;line-height:1.35;color:#fff;text-align:center}
.mba-card p{margin:0 auto;padding:0 8px;font-size:13px;line-height:1.55;color:#d6d3d1;text-align:center;box-sizing:border-box}
.mba-list{list-style:none;padding:0 8px;margin:10px auto 14px;text-align:center;box-sizing:border-box;font-size:12.5px;line-height:1.5;color:#e7e5e4;width:100%}
.mba-list li{margin-bottom:5px}
.mba-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:auto;padding-top:6px;width:100%;justify-content:center}
.mba-btn{display:inline-flex;align-items:center;justify-content:center;padding:9px 13px;border-radius:9px;font-size:13px;font-weight:800;text-decoration:none;min-height:42px;flex:1 1 auto;text-align:center}
.mba-bundle{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:14px;padding:22px 20px;border-radius:12px;background:linear-gradient(135deg,rgba(16,185,129,.22),rgba(132,204,22,.14));border:2px solid #10b981;box-shadow:0 10px 30px rgba(16,185,129,.28),0 0 22px rgba(52,211,153,.28);box-sizing:border-box}
.mba-bundle-copy{width:100%;min-width:0;display:flex;flex-direction:column;align-items:center;text-align:center}
.mba-bundle-copy h3{margin:0 auto 6px;font-size:17.5px;color:#fff;text-align:center}
.mba-bundle-copy p{margin:0 auto;font-size:13.5px;line-height:1.55;color:#f5f5f4;text-align:center;max-width:780px}
.mba-bundle-ctas{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:center;width:100%}
@media(max-width:860px){.mba-grid{grid-template-columns:1fr}}
@media(max-width:520px){.mba-sec img.aswm{filter:invert(1) hue-rotate(180deg)}
.mba-builtby{display:inline-flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:4px;font-size:12.5px;font-weight:700;color:#e5e7eb;margin:4px auto 6px;text-align:center}
.mba-builtby img.aswm{height:1.38em;vertical-align:-.34em;margin:0 -.35em 0 .08em}
section.mba-sec,.bt section.mba-sec{padding:16px}.mba-head{padding:18px 16px;text-align:center}.mba-notice{padding:14px 16px;text-align:center;justify-content:center}.mba-notice div{justify-content:center;width:100%}.mba-card{padding:18px 16px}.mba-bundle{padding:18px 16px}.mba-btn{width:100%;box-sizing:border-box}.bt-hub-tab{width:100%;justify-content:center;box-sizing:border-box}}
</style>"""

def made_by_agentscout_html(total=189):
    return (
        '<!--bt-mba-->'
        '<script type="application/ld+json">{"@context":"https://schema.org","@type":"SoftwareApplication","name":"AgentScout Bot Templates","applicationCategory":"BusinessApplication","operatingSystem":"Grok Bot, Claude Code, Cursor, Codex","url":"https://agentscouthq.com/bot-templates/","author":{"@type":"Organization","name":"AgentScout","url":"https://agentscouthq.com"},"brand":{"@type":"Organization","name":"AgentScout","url":"https://agentscouthq.com"},"offers":{"@type":"Offer","price":"0","priceCurrency":"USD","availability":"https://schema.org/InStock"}}</script>'
        '<div class="bt-hub-bar" aria-label="Jump to Bot Store or Free Community Templates">'
        '<div class="bt-hub-tabs">'
        '<a class="bt-hub-tab pro" href="../bot-store/">🛒 Dedicated Bot Store ($39 / $59 / $59 / $69 · $149 Bundle) →</a>'
        '<a class="bt-hub-tab comm" href="#made-by-agentscout">🤖 Quick-Buy Pro Bots Below ↓</a>'
        f'<a class="bt-hub-tab comm" href="#bt-featured">📚 Browse {total} Free Community Templates ↓</a>'
        '<a class="bt-hub-tab vid" href="../videos/">🎬 Watch Quick-Start Guides (8) →</a>'
        '</div>'
        '<span class="muted" style="font-size:12.5px">Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex)</span>'
        '</div>'
        '<section id="made-by-agentscout" class="mba-sec" aria-labelledby="mba-h">'
        '<div class="mba-notice">'
        '<span>📦 <b>WHAT YOU ARE BUYING IN THIS SECTION:</b> Downloadable Pre-Trained AI Bot Packages (<code>SYSTEM.md</code> + Cron Routines + <code>SKILL.md</code> Playbooks + Python 3 Scripts + <code>mcp.json</code>) in <b>5 distinct neon colors</b> (<b>Neon Lime</b>, <b>Neon Gold</b>, <b>Neon Sunset Orange</b>, <b>Neon Crimson Red</b>, and <b>Neon Mint-Emerald</b>). <b>What\'s inside every .zip:</b> <code>README-QUICKSTART.md</code> (5-minute step-by-step setup guide for Grok Bot, Claude Code, Cursor &amp; OpenAI Codex). The 4-Bot Bundle also includes <code>README-TEAM-BUNDLE.md</code>. <b>Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex).</b> <b>This is NOT a directory listing boost.</b></span>'
        '<div style="display:flex;flex-wrap:wrap;gap:12px;justify-content:center;text-align:center">'
        '<a href="../bot-store/">Open Full Bot Store (/bot-store/) →</a>'
        '<a href="../sponsor.html#packages">Want to list or boost a tool in the directory instead? ($0 / $29 / $49 / $99) →</a>'
        '</div>'
        '</div>'
        '<div class="mba-head"><div>'
        '<span class="mba-eyebrow">⚡ Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex) · 5 Neon Bot Packages</span>'
        '<h2 id="mba-h">Pre-Trained Pro Bots &amp; "Company-in-a-Box" Team Bundle built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"></h2>'
        f'<p>General-purpose bots for your own SaaS or online business. Set <code>{{{{YOUR_COMPANY}}}}</code> and <code>{{{{YOUR_DOMAIN}}}}</code> for uptime and inbox monitoring, technical SEO and Core Web Vitals auditing, competitor and launch tracking, and executive team coordination. Built natively for <b>Grok Bot</b> first — scheduled routines, a shared <code>/workspace/handoff/</code> folder, and 4-bot <code>Work Chat</code> run out of the box — and each ZIP also drops into <b>Claude Code, Cursor, and OpenAI Codex</b>. Buy any bot individually (<code>$39</code>, <code>$59</code>, <code>$59</code>, <code>$69</code> — <code>$226</code> separately) or all 4 in the <b>$149 Company-in-a-Box Team Bundle (Save $77)</b>. File lists are on the <a href="../bot-store/" style="color:#fde047;font-weight:700;text-decoration:underline">dedicated AgentScout Bot Store</a>, and <a href="#bt-featured" style="color:#a3e635;text-decoration:underline">{total} free community bot templates</a> are below.</p>'
        '</div>'
        '<div style="display:flex;flex-wrap:wrap;justify-content:center;gap:8px;width:100%;max-width:100%;min-width:0;box-sizing:border-box">'
        '<a class="mba-btn" href="../bot-store/" style="flex:1 1 auto;max-width:100%;box-sizing:border-box;background:linear-gradient(135deg,#10b981,#34d399);color:#031811;box-shadow:0 4px 14px rgba(16,185,129,.4)">🛒 Open Full Bot Store →</a>'
        '<a class="mba-btn" href="../videos/#guide-trained-bots" style="flex:1 1 auto;max-width:100%;box-sizing:border-box;background:rgba(132,204,22,.18);border:1.5px solid #a3e635;color:#ecfccb">🎬 Watch 60fps Bot Demo →</a>'
        '</div>'
        '</div>'
        '<figure class="mba-vid"><video autoplay loop muted playsinline preload="metadata" poster="../assets/animations/agentscout-trained-bots-ad-poster.png" width="1200" height="560" style="aspect-ratio:1200/560"><source src="../assets/animations/agentscout-trained-bots-ad.mp4?v=202610280208" type="video/mp4"></video></figure>'
        '<div class="mba-grid">'
        # Card 1: $39 Operations / Monitoring Bot — Neon Lime Green (#84cc16 / #a3e635)
        '<div class="mba-card neon-lime">'
        '<div><div class="mba-card-top"><span class="mba-price" style="color:#a3e635;text-shadow:0 0 14px rgba(163,230,53,.45)">$39 <small>one-time · sold separately</small></span><span class="mba-tag" style="background:rgba(132,204,22,.22);border:1.5px solid #a3e635;color:#ecfccb;box-shadow:0 0 12px rgba(132,204,22,.4)">🟢 Bot #1 · Neon Lime</span></div>'
        '<h3 style="margin-top:8px">1. AgentScout Operations / Monitoring Bot (Uptime &amp; Inbox Monitoring)</h3><div class="mba-builtby">Pre-Trained Pro Bot built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"></div>'
        '<p style="margin-top:4px">General-purpose uptime and inbox monitor for <code>{{YOUR_COMPANY}}</code>. It checks <code>{{YOUR_DOMAIN}}</code> on a schedule, triages the support inbox, and recovers failed routines. Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex).</p></div>'
        '<ul class="mba-list"><li>Scheduled HTTP uptime checks for <code>{{YOUR_DOMAIN}}</code></li><li>Support-inbox triage for <code>{{YOUR_COMPANY}}</code></li><li>Routine failure recovery</li><li>Includes <code>README-QUICKSTART.md</code> (5-minute step-by-step setup guide for Grok Bot, Claude Code, Cursor &amp; OpenAI Codex)</li></ul>'
        '<div class="mba-actions">'
        '<a class="mba-btn" href="https://buy.stripe.com/cNidRa0uDdNRgNvaDFe7m03" target="_blank" rel="noopener noreferrer" style="background:linear-gradient(135deg,#84cc16,#a3e635);color:#081202;box-shadow:0 4px 16px rgba(132,204,22,.45)">Buy AgentScout Operations / Monitoring Bot ($39) →</a>'
        '<a class="mba-btn" href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer" style="background:rgba(255,255,255,.07);color:#ecfccb;border:1px solid #84cc16">Pay $39 on X Money (@clampdown19)</a>'
        '</div></div>'
        # Card 2: $59 2. AgentScout SEO & AEO Growth Auditor Bot — Neon Electric Gold / Yellow (#eab308 / #facc15)
        '<div class="mba-card neon-gold">'
        '<div><div class="mba-card-top"><span class="mba-price" style="color:#facc15;text-shadow:0 0 14px rgba(250,204,21,.45)">$59 <small>one-time · sold separately</small></span><span class="mba-tag" style="background:rgba(234,179,8,.22);border:1.5px solid #facc15;color:#fef9c3;box-shadow:0 0 12px rgba(234,179,8,.4)">🟡 Bot #2 · Neon Gold</span></div>'
        '<h3 style="margin-top:8px">2. AgentScout SEO &amp; AEO Growth Auditor Bot (Technical SEO &amp; Core Web Vitals)</h3><div class="mba-builtby">Pre-Trained Pro Bot built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"></div>'
        '<p style="margin-top:4px">General-purpose technical SEO and Core Web Vitals auditor for <code>{{YOUR_DOMAIN}}</code>. It reviews page speed, titles, canonicals, and structured data for <code>{{YOUR_COMPANY}}</code>. Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex).</p></div>'
        '<ul class="mba-list"><li>Core Web Vitals (LCP, INP, CLS) on <code>{{YOUR_DOMAIN}}</code></li><li>Titles, canonicals, indexability, and structured data</li><li>Search Console query and page deltas</li><li>Includes <code>README-QUICKSTART.md</code> (5-minute step-by-step setup guide for Grok Bot, Claude Code, Cursor &amp; OpenAI Codex)</li></ul>'
        '<div class="mba-actions">'
        '<a class="mba-btn" href="https://buy.stripe.com/14A7sMfpx6lp9l3aDFe7m05" target="_blank" rel="noopener noreferrer" style="background:linear-gradient(135deg,#eab308,#facc15);color:#141002;box-shadow:0 4px 16px rgba(234,179,8,.45)">Buy AgentScout SEO &amp; AEO Growth Auditor Bot ($59) →</a>'
        '<a class="mba-btn" href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer" style="background:rgba(255,255,255,.07);color:#fef9c3;border:1px solid #eab308">Pay $59 on X Money (@clampdown19)</a>'
        '</div></div>'
        # Card 3: $59 Market & Launch Intel Bot — Neon Sunset Orange (#f97316 / #fb923c)
        '<div class="mba-card neon-orange">'
        '<div><div class="mba-card-top"><span class="mba-price" style="color:#fb923c;text-shadow:0 0 14px rgba(251,146,60,.45)">$59 <small>one-time · sold separately</small></span><span class="mba-tag" style="background:rgba(249,115,22,.22);border:1.5px solid #fb923c;color:#ffedd5;box-shadow:0 0 12px rgba(249,115,22,.4)">🟠 Bot #3 · Neon Sunset Orange</span></div>'
        '<h3 style="margin-top:8px">3. AgentScout Market &amp; Launch Intel Bot (Competitor &amp; Launch Tracking)</h3><div class="mba-builtby">Pre-Trained Pro Bot built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"></div>'
        '<p style="margin-top:4px">General-purpose competitor and launch tracker for <code>{{YOUR_COMPANY}}</code>. It watches rival products, pricing pages, and public launches, then files a morning brief. Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex).</p></div>'
        '<ul class="mba-list"><li>Rival launches, pricing pages, and positioning for <code>{{YOUR_COMPANY}}</code></li><li>Public launch notes with source URLs</li><li>Morning brief, including stale claims on <code>{{YOUR_DOMAIN}}</code></li><li>Includes <code>README-QUICKSTART.md</code> (5-minute step-by-step setup guide for Grok Bot, Claude Code, Cursor &amp; OpenAI Codex)</li></ul>'
        '<div class="mba-actions">'
        '<a class="mba-btn" href="https://buy.stripe.com/4gM8wQelt11568RaDFe7m06" target="_blank" rel="noopener noreferrer" style="background:linear-gradient(135deg,#f97316,#fb923c);color:#140702;box-shadow:0 4px 16px rgba(249,115,22,.45)">Buy AgentScout Market &amp; Launch Intel Bot ($59) →</a>'
        '<a class="mba-btn" href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer" style="background:rgba(255,255,255,.07);color:#ffedd5;border:1px solid #f97316">Pay $59 on X Money (@clampdown19)</a>'
        '</div></div>'
        # Card 4: $69 CEO Coordinator Bot — Neon Crimson Red / Coral (#ef4444 / #f87171)
        '<div class="mba-card neon-red">'
        '<div><div class="mba-card-top"><span class="mba-price" style="color:#f87171;text-shadow:0 0 14px rgba(248,113,113,.45)">$69 <small>one-time · sold separately</small></span><span class="mba-tag" style="background:rgba(239,68,68,.22);border:1.5px solid #f87171;color:#fee2e2;box-shadow:0 0 12px rgba(239,68,68,.4)">🔴 Bot #4 · Neon Crimson Red</span></div>'
        '<h3 style="margin-top:8px">4. AgentScout CEO Coordinator Bot (Executive Team Coordination)</h3><div class="mba-builtby">Pre-Trained Pro Bot built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"></div>'
        '<p style="margin-top:4px">General-purpose executive coordinator for <code>{{YOUR_COMPANY}}</code>. It reads the uptime, SEO, and competitor briefs and writes the daily plan for the team. Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex).</p></div>'
        '<ul class="mba-list"><li>Assigns follow-ups across the ops, SEO, and market bots</li><li>Daily executive brief for <code>{{YOUR_COMPANY}}</code></li><li>Owner queue for decisions that still need a person</li><li>Includes <code>README-QUICKSTART.md</code> (5-minute step-by-step setup guide for Grok Bot, Claude Code, Cursor &amp; OpenAI Codex)</li></ul>'
        '<div class="mba-actions">'
        '<a class="mba-btn" href="https://buy.stripe.com/9B69AU2CLh031SB8vxe7m07" target="_blank" rel="noopener noreferrer" style="background:linear-gradient(135deg,#ef4444,#f87171);color:#fff;box-shadow:0 4px 16px rgba(239,68,68,.45)">Buy AgentScout CEO Coordinator Bot ($69) →</a>'
        '<a class="mba-btn" href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer" style="background:rgba(255,255,255,.07);color:#fee2e2;border:1px solid #ef4444">Pay $69 on X Money (@clampdown19)</a>'
        '</div></div>'
        '</div>'
        # Card 5: $149 Full 4-Bot Bundle — Neon Mint-Emerald (#10b981 / #34d399)
        '<div class="mba-bundle">'
        '<div class="mba-bundle-copy">'
        '<span class="mba-tag" style="background:rgba(16,185,129,.25);border:1.5px solid #34d399;color:#d1fae5;margin-bottom:6px;box-shadow:0 0 12px rgba(16,185,129,.4)">💚 Package #5 · Neon Mint-Emerald · All 4 Bots Sold Together · Save $77 vs. $226</span>'
        '<h3>$149 Full 4-Bot "Company-in-a-Box" Team Bundle (All 4 Bots Above + Shared Handoff Protocol)</h3><div class="mba-builtby">Pre-Trained Pro Bot built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"></div>'
        '<p>All 4 general-purpose bots for <code>{{YOUR_COMPANY}}</code> (<code>{{YOUR_DOMAIN}}</code>) — <b>1. AgentScout Operations / Monitoring Bot ($39)</b> + <b>2. AgentScout SEO &amp; AEO Growth Auditor Bot ($59)</b> + <b>3. AgentScout Market &amp; Launch Intel Bot ($59)</b> + <b>4. AgentScout CEO Coordinator Bot ($69)</b> — uptime and inbox monitoring, technical SEO and Core Web Vitals, competitor and launch tracking, and executive coordination, sharing one <code>/workspace/handoff/</code> folder, for <b>$149 one-time</b> (saves <b>$77</b> off the $226 individual total). <b>Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex).</b></p>'
        '<ul class="mba-list"><li>What\'s inside every .zip: <code>README-QUICKSTART.md</code> (5-minute step-by-step setup guide for Grok Bot, Claude Code, Cursor &amp; OpenAI Codex)</li><li>4-Bot Bundle also includes <code>README-TEAM-BUNDLE.md</code></li></ul>'
        '</div>'
        '<div class="mba-bundle-ctas">'
        '<a class="mba-btn" href="https://buy.stripe.com/fZueVe5OX7pt1SB6npe7m08" target="_blank" rel="noopener noreferrer" style="background:linear-gradient(135deg,#10b981,#34d399);color:#031811;padding:10px 18px;box-shadow:0 6px 20px rgba(16,185,129,.45)">Buy All 4 Bots Together — $149 (Save $77) →</a>'
        '<a class="mba-btn" href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer" style="background:rgba(12,10,6,.9);color:#d1fae5;border:1px solid #10b981">Pay $149 via X Money (@clampdown19)</a>'
        '<a class="mba-btn" href="../bot-store/" style="background:rgba(255,255,255,.08);color:#ecfccb;border:1px solid rgba(163,230,53,.5)">Full Bot Store Details →</a>'
        '</div></div>'
        '</section>'
        + pack_section_html()
        + '<!--/bt-mba-->'
    )

_run0=run
def run():
    _run0(); filters(); tap(); verify_logos()

def pages(t=None):
    """Rebuild /bot-templates/ index (filters, counts, and the Made by AgentScout section)."""
    filters()
    return [f"{SITE}/{D}/"]

if __name__=="__main__": run()
