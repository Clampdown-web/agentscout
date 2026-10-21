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
if __name__=="__main__": run()
