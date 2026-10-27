"""Ratings & reviews on tool pages (Oct 18 2026).
- Fetches real data from the Worker (GET /reviews/all: rating count + average per tool, approved reviews only) and keeps
  the last good copy in reviews.json, so a build without network keeps the current data. Nothing is ever seeded.
- Inserts the "Ratings and reviews" section (static summary + approved reviews + form; reviews.js refreshes it and
  handles the form) into every tool page, before the alternatives block.
- AggregateRating + Review JSON-LD go on the SoftwareApplication node ONLY when a tool has at least one approved review.
- Adds a "rating" object to api/tools.json for tools with ratings.
Called from build_site.py after build_api, on every build."""
import json,os,re,html,glob,urllib.request,datetime
W="https://api.agentscouthq.com"
e=lambda s:html.escape(str(s if s is not None else ""))
def data():
    try:
        r=urllib.request.urlopen(urllib.request.Request(W+"/reviews/all",headers={"X-AgentScout-App":"1","User-Agent":"agentscout-build"}),timeout=10)
        d=json.load(r)
        if isinstance(d.get("tools"),dict):
            json.dump(d,open("reviews.json","w"),indent=1,ensure_ascii=False); return d["tools"]
    except Exception as ex: print("reviews: using cached reviews.json (",str(ex)[:80],")")
    try: return json.load(open("reviews.json")).get("tools",{})
    except Exception: return {}
def stars(n): return f'<span class="rv-stars" style="--r:{n}" aria-hidden="true">★★★★★</span>'
def day(ts): return datetime.datetime.fromtimestamp(ts/1000,datetime.timezone.utc)
def section(x,d,V):
    n=x["name"]; s=x["slug"]; c=(d or {}).get("count",0); R=(d or {}).get("reviews",[]) if c else []
    summ=(f'{stars(d["avg"])} <span class="rv-text"><b>{d["avg"]:.1f}</b> out of 5 · {c} rating{"s" if c!=1 else ""}</span>' if c else f'<span class="rv-text">No ratings yet. Be the first to review {e(n)}.</span>')
    lis="".join(f'<li class="rv-item">{stars(r["stars"])}<span class="sr">{r["stars"]} out of 5 stars</span> <b class="rv-who">{e(r.get("name") or "Anonymous")}</b> <time class="muted" datetime="{day(r["ts"]).isoformat()[:19]}Z">{day(r["ts"]).strftime("%b %-d, %Y")}</time><p>{e(r["text"])}</p></li>' for r in R)
    radios="".join(f'<input type="radio" class="sr" name="rv-stars" id="rv-s{i}" value="{i}"><label for="rv-s{i}" title="{i} star{"s" if i>1 else ""}"><span class="sr">{i} star{"s" if i>1 else ""}</span></label>' for i in range(1,6))
    return (f'<section id="reviews" class="rv" data-tool="{e(s)}" data-name="{e(n)}" aria-labelledby="rv-h"><h2 id="rv-h" style="font-size:16px;margin-bottom:10px">{e(n)} ratings and reviews</h2>'
        f'<div class="rv-sum">{summ}</div><ol class="rv-list"{"" if R else " hidden"}>{lis}</ol>'
        f'<p class="rv-cta">{"Be the first to rate" if not c else "Used"} {e(n)}{"" if not c else "? Rate it too"}: tap 1 to 5 stars below. A written review is optional.</p>'
        f'<form class="rv-form" id="rv-form" novalidate><fieldset class="rv-pick"><legend>Your rating of {e(n)}</legend><div class="rv-row">{radios}</div></fieldset>'
        f'<label for="rv-text">Short review (optional)</label><textarea id="rv-text" name="rv-text" rows="3" maxlength="600" placeholder="What worked, what didn\'t? 10 to 600 characters, no links."></textarea><span class="rv-cnt muted" aria-hidden="true">0 / 600</span>'
        f'<label for="rv-name">Name (optional)</label><input type="text" id="rv-name" name="rv-name" maxlength="40" autocomplete="nickname">'
        f'<div class="rv-hp" aria-hidden="true"><label for="rv-website">Leave this empty</label><input type="text" id="rv-website" name="website" tabindex="-1" autocomplete="off"></div>'
        f'<p style="margin:14px 0 0"><button type="submit" class="btn primary">Submit rating</button></p><p class="rv-msg" role="status" aria-live="polite"></p>'
        f'<p class="rv-note muted">Star ratings count right away; written reviews appear after a quick check. One rating per tool per visitor. Reviews are from site visitors, not verified users. <a href="../privacy.html#reviews">How reviews work</a></p></form>'
        f'<script src="../reviews.js?v={V}" defer></script></section>')
def top(x,d):
    """Compact rating line under the tool name (Oct 18 2026): average + count, or 'No ratings yet', and a jump link to #reviews.
    Fixed min-height so reviews.js refreshing it never shifts the layout."""
    c=(d or {}).get("count",0)
    summ=(f'<a class="rv-topsum" href="#reviews" style="display:inline-flex;align-items:center;gap:6px;color:inherit;text-decoration:none"><span class="rv-stars" style="--r:{d["avg"]};font-size:15px" aria-hidden="true">★★★★★</span><span><b>{d["avg"]:.1f}</b> <span class="muted">({c} rating{"s" if c!=1 else ""})</span></span><span class="sr">Rated {d["avg"]:.1f} out of 5 from {c} rating{"s" if c!=1 else ""}</span></a>'
          if c else '<span class="muted rv-topsum">No ratings yet</span>')
    return (f'<div class="rv-top" style="display:flex;align-items:center;flex-wrap:wrap;gap:4px 10px;min-height:24px;line-height:24px;margin:-6px 0 12px;font-size:14px">'
            f'{summ}<span class="muted" aria-hidden="true">·</span><a class="rv-write rv-rate" href="#rv-form">★ Rate this tool</a></div>')
def run(t):
    import build_tasks; V="202610211400"  # reviews.js cache version (Oct 21 2026: own constant; bump when reviews.js changes)
    D=data(); bs={x["slug"]:x for x in t}; ld_n=0; ins=0
    for f in glob.glob("tools/*.html"):
        s0=os.path.basename(f)[:-5]; x=bs.get(s0)
        if not x: continue
        h=open(f).read(); o=h
        h=re.sub(r'<section id="reviews".*?</section>','',h,flags=re.S)
        sec=section(x,D.get(s0),V)
        h=re.sub(r'<div class="rv-top".*?</a></div>','',h,count=1,flags=re.S)
        h=h.replace('</h1>','</h1>'+top(x,D.get(s0)),1)
        h,k=re.subn(r'(<h2 style="font-size:16px;margin-bottom:12px">[^<]*alternatives</h2>)',lambda m:sec+m.group(1),h,count=1)
        if not k: h,k=re.subn(r'(<h2 style="font-size:16px;margin:36px 0 6px">Badge for makers</h2>)',lambda m:sec+m.group(1),h,count=1)
        ins+=k
        d=D.get(s0) or {}; R=d.get("reviews") or []
        def fix(m):
            try: L=json.loads(m.group(1))
            except Exception: return m.group(0)
            for nd in L.get("@graph",[]):
                if nd.get("@type")=="WebPage" and isinstance(nd.get("about"),dict):
                    a=nd["about"]; a.pop("aggregateRating",None); a.pop("review",None)
                    if R and d.get("count"):
                        a["aggregateRating"]={"@type":"AggregateRating","ratingValue":d["avg"],"ratingCount":d["count"],"reviewCount":len(R),"bestRating":5,"worstRating":1}
                        a["review"]=[{"@type":"Review","author":{"@type":"Person","name":r.get("name") or "Anonymous visitor"},"datePublished":day(r["ts"]).date().isoformat(),"reviewBody":r["text"],"reviewRating":{"@type":"Rating","ratingValue":r["stars"],"bestRating":5,"worstRating":1}} for r in R[:10]]
            return '<script type="application/ld+json">'+json.dumps(L,ensure_ascii=False).replace("</","<\\/")+'</script>'
        h=re.sub(r'<script type="application/ld\+json">(.*?)</script>',lambda m:fix(m) if '"WebPage"' in m.group(1) else m.group(0),h,flags=re.S)
        if R and d.get("count"): ld_n+=1
        if h!=o: open(f,"w").write(h)
    # API: rating object on tools that have ratings
    try:
        A=json.load(open("api/tools.json")); ch=False
        for y in A.get("tools",[]):
            d=D.get(y.get("slug"))
            new={"average":d["avg"],"count":d["count"],"approved_reviews":len(d.get("reviews") or []),"reviews_api":f'{W}/reviews?tool={y["slug"]}'} if d and d.get("count") else None
            if new and y.get("rating")!=new: y["rating"]=new; ch=True
            elif not new and "rating" in y: y.pop("rating"); ch=True
        if ch: json.dump(A,open("api/tools.json","w"),indent=1,ensure_ascii=False)
    except Exception as ex: print("reviews api:",ex)
    print("reviews:",ins,"sections,",sum(1 for v in D.values() if v.get("count")),"tools with ratings,",ld_n,"with review JSON-LD")
