"""Optional rich SEO content for tool pages, from tool_rich.json (keyed by slug). Tools without an entry are unchanged."""
import json,html,os,re
e=lambda s:html.escape(str(s or ""))
R=json.load(open("tool_rich.json")) if os.path.exists("tool_rich.json") else {}
H2='<h2 style="font-size:16px;margin-bottom:10px">'
def apply(out,x,t,catslug,prim,B):
    r=R.get(x["slug"])
    if not r: return out,None
    if r.get("kind")=="lite": return lite(out,x,t,catslug,prim,B,r)
    n=x["name"];p=r["pricing"];cat=x["category"];cs=catslug(cat);pg=f"{B}tools/{x['slug']}.html"
    title=f"{n}: Features, Pricing & Alternatives | AgentScout"
    out=re.sub(r"<title>.*?</title>",f"<title>{e(title)}</title>",out,1,flags=re.S)
    out=re.sub(r'<meta name="description" content="[^"]*">',f'<meta name="description" content="{e(r["meta"])}">',out,1)
    out=re.sub(r'<meta property="og:title" content="[^"]*">',f'<meta property="og:title" content="{e(title)}">',out,1)
    out=re.sub(r'<meta property="og:description" content="[^"]*">',f'<meta property="og:description" content="{e(r["meta"])}">',out,1)
    out=out.replace('<meta name="twitter:card"',f'<meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(r["meta"])}"><meta name="twitter:card"',1)
    alts=[y for y in t if y is not x and y["category"]==cat]
    alts=sorted(alts,key=lambda y:(not y.get("featured"),not y.get("logo"),y["name"].lower()))[:5]
    altl=", ".join(f'<a href="{y["slug"]}.html">{e(y["name"])}</a>' for y in alts)
    altp=", ".join(y["name"] for y in alts)
    tiers="".join(f"<li><strong>{e(a)}</strong>: {e(b)}{(' · '+e(c)) if c else ''}</li>" for a,b,c in p["tiers"])
    freeq="Yes. "+e(n)+" has a free plan"+(f" ({e(p['tiers'][0][2])})" if p["tiers"][0][1] in ("$0","Free") else "")+"." if p["free"] else f"No free plan is listed{(', but there is a '+e(p['trial'])) if p['trial'] else ''}. Paid plans start at ${p['start']:g} a month."
    cost=f"{n} pricing starts at ${p['start']:g} a month for paid plans"+(", with a free plan available" if p["free"] else "")+". Plans: "+"; ".join(f"{a} {b}" for a,b,c in p["tiers"])+". "+p.get("note","")+" (as of Oct 2026)"
    faq=[(f"What is {n}?"," ".join(r["long"])),(f"How much does {n} cost?",cost),(f"Does {n} have a free plan?",re.sub("<[^>]+>","",html.unescape(freeq))),(f"What are alternatives to {n}?",f"Other {cat} tools on AgentScout include {altp}.")]
    sec=(f'{H2}What is {e(n)}?</h2>'+"".join(f'<p style="margin:0 0 12px">{e(s)}</p>' for s in r["long"])
      +f'<p class="muted" style="margin:0 0 28px">Listed in our <a href="../categories/{cs}.html">{e(cat)}</a> category. Official site: <a href="{e(prim)}" target="_blank" rel="noopener">{e(re.sub(r"^https?://(www\.)?","",prim).rstrip("/"))}</a>.</p>'
      +f'{H2}Key features</h2><ul style="margin:0 0 28px;padding-left:20px;line-height:1.7">'+"".join(f"<li>{e(f)}</li>" for f in r["features"])+"</ul>"
      +f'{H2}{e(n)} pricing</h2><p style="margin:0 0 8px">{"Free plan available. " if p["free"] else ""}Paid plans from ${p["start"]:g}/month{(". "+e(p["trial"][0].upper()+p["trial"][1:])) if p["trial"] else ""}.</p><ul style="margin:0 0 8px;padding-left:20px;line-height:1.7">{tiers}</ul><p class="muted" style="margin:0 0 28px">{e(p.get("note",""))} Prices as of Oct 2026, from the <a href="{e(p["src"])}" target="_blank" rel="noopener">official pricing page</a>.</p>'
      +f'{H2}{e(n)} alternatives</h2><p style="margin:0 0 28px">Similar {e(cat)} tools: {altl}. <a href="../categories/{cs}.html">Browse all {e(cat)} tools →</a></p>'
      +f'{H2}{e(n)} FAQ</h2>'+"".join(f'<details style="margin:0 0 10px"><summary style="cursor:pointer;font-weight:600">{e(q)}</summary><p style="margin:8px 0 0">{e(a)}</p></details>' for q,a in faq)+'<div style="margin-bottom:28px"></div>')
    offers=[{"@type":"Offer","name":f"{n} {a}","price":re.match(r"\$([\d.]+)",b).group(1) if re.match(r"\$[\d.]+",b) else None,"priceCurrency":"USD","url":p["src"]} for a,b,c in p["tiers"]]
    offers=[o for o in offers if o["price"] is not None]
    app={"@type":"SoftwareApplication","name":n,"url":prim,"description":r["meta"],"applicationCategory":"DeveloperApplication" if x["audience"]=="builders" else "BusinessApplication","operatingSystem":"macOS" if x["slug"]=="coddo" else "Web","offers":offers}
    fq={"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}
    return out,(sec,app,fq,title)

OSI_NOTE="(verified on GitHub)"
def _mdy(d):
    import datetime
    try: return datetime.date.fromisoformat(d).strftime("%b %-d, %Y")
    except Exception: return d or ""
def _facts(n,r):
    """Verified facts block (licence, repo, stars, status) and FAQ items. Only fields present in r["facts"] are shown."""
    F=r.get("facts") or {}; li=[]; fq=[]
    lic=F.get("license")
    if lic:
        li.append(("Open source",(f"Yes ({re.sub(r'^the ','',lic)})" if F.get("osi") else f"Source-available, not OSI open source: {lic}") if F.get("osi") is not False or "Proprietary" not in lic else f"No ({lic})"))
        fq.append((f"Is {n} open source?",(f"Yes. {n} is released under {lic}, according to its GitHub repository." if F.get("osi") else (f"No. {n}'s code is published under {lic}, which is not an OSI-approved open-source licence." if "Proprietary" not in lic else f"No. {n}'s GitHub repository states: {lic}."))))
    if F.get("repo"):
        st=F.get("stars"); li.append(("GitHub",f'<a href="{e(F["repo"])}" target="_blank" rel="noopener">{e(F["repo"].replace("https://github.com/",""))}</a>'+(f" · {st:,} stars" if st else "")+(f" · {F['forks']:,} forks" if F.get("forks") else "")+(f" (as of {_mdy(F.get('checked'))})" if st else ""),True))
    if F.get("archived"): li.append(("Status","Archived: the GitHub repository is read-only and no longer maintained"))
    if F.get("status"): li.append(("Status",F["status"]))
    return li,fq
def _pricing(n,r):
    P=r.get("pricing_v")
    if not P: return "",[],None
    tiers=P["tiers"]; ck=_mdy(P.get("checked"))
    html_=(f'{H2}{e(n)} pricing</h2><ul style="margin:0 0 8px;padding-left:20px;line-height:1.7">'+"".join(f"<li><strong>{e(a)}</strong>: {e(b)}{(' · '+e(c)) if c else ''}</li>" for a,b,c in tiers)+"</ul>"
        +(f'<p style="margin:0 0 8px">{e(P["note"])}</p>' if P.get("note") else "")
        +f'<p class="muted" style="margin:0 0 28px">Source: <a href="{e(P["src"])}" target="_blank" rel="noopener">official pricing page</a>, checked {e(ck)}. Prices change; check the source before buying.</p>')
    plans="; ".join(f"{a}: {b}" for a,b,c in tiers)
    fq=[(f"How much does {n} cost?",f"As of {ck}, {n}'s official pricing page lists: {plans}."+(" "+P["note"] if P.get("note") else ""))]
    free=[a for a,b,c in tiers if re.match(r"(?i)^(\$0(?![\d.])|free\b)",b)]
    isfree=(f"Yes. {n} has a free option ({', '.join(free)}), according to its pricing page (checked {ck})." if P.get("free") and free else f"{n} doesn't list a free plan on its pricing page (checked {ck}). Plans: {plans}.")
    offers=[]
    for a,b,c in tiers:
        m=re.match(r"^(?:from )?\$([\d,]+(?:\.\d+)?)(?:\s*/\s*mo|/mo|/month| per month|\b)",b)
        if (m and ("/mo" in b or "month" in b or re.match(r"^\$0(?![\d.])",b.strip()))) or re.match(r"(?i)^free$",b):
            offers.append({"@type":"Offer","name":f"{n} {a}","price":(m.group(1).replace(",","") if m else "0"),"priceCurrency":"USD","url":P["src"],"description":b+((" · "+c) if c else "")})
    return html_,fq+[("__free__",isfree)],offers

def lite(out,x,t,catslug,prim,B,r):
    """Lighter rich section (Oct 2026 enrichment): grounded description, who it's for, key features, FAQ.
    Keeps the existing About paragraph (additive) and never states pricing beyond the directory's maker-stated label."""
    n=x["name"];cat=x["category"];cs=catslug(cat);pd=x.get("pricing_detail") or x["pricing"]
    alts=sorted([y for y in t if y is not x and y["category"]==cat and "discontinu" not in (y.get("maturity","")+y["description"]).lower()],key=lambda y:(-(y.get("github_stars") or 0),y["name"].lower()))[:5]
    altl=", ".join(f'<a href="{y["slug"]}.html">{e(y["name"])}</a>' for y in alts); altp=", ".join(y["name"] for y in alts)
    pq=f"{n}'s pricing, as the maker states it: {pd}."+(" Open-source tools are free to use, though you may still pay for model API usage or a hosted plan." if re.match(r"(?i)(free, )?open[- ]?source",pd) else "")+" Check the official site for current plans."
    fli,ffq=_facts(n,r); phtml,pfq,offers=_pricing(n,r)
    isfree=[a for q,a in pfq if q=="__free__"]; pfq=[(q,a) for q,a in pfq if q!="__free__"]
    if isfree: pq=isfree[0]
    faq=[(f"What is {n}?",r["long"][0]),(f"Who is {n} for?",r["who"]),(f"Is {n} free?",pq)]+pfq+ffq+[tuple(q) for q in r.get("faq",[])]
    if altp: faq.append((f"What are alternatives to {n}?",f"Other {cat} tools on AgentScout include {altp}."))
    hst=re.sub(r"^https?://(www\.)?","",prim).rstrip("/")
    sec=(f'{H2}What is {e(n)}?</h2>'+"".join(f'<p style="margin:0 0 12px">{e(p)}</p>' for p in r["long"])
      +(f'<p class="muted" style="margin:0 0 28px">Sources: '+", ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(re.sub(r"^https?://(www\.)?","",u).rstrip("/")[:70])}</a>' for u in r["sources"])+f' and our directory listing, checked {e(r.get("updated",""))}.</p>' if r.get("cite") else f'<p class="muted" style="margin:0 0 28px">Sources: the official {"README" if r.get("src_kind")=="README" else "site"} and our directory listing, checked {e(r.get("updated",""))}. Official site: <a href="{e(prim)}" target="_blank" rel="noopener">{e(hst)}</a>.</p>')
      +f'{H2}Who is {e(n)} for?</h2><p style="margin:0 0 28px">{e(r["who"])}</p>'
      +(f'{H2}{e(n)} at a glance</h2><ul style="margin:0 0 28px;padding-left:20px;line-height:1.7">'+"".join(f"<li><strong>{e(k)}</strong>: {v[0] if isinstance(v,tuple) else (v if len(it)>2 else e(v))}</li>" for it in fli for k,v in [(it[0],it[1])])+"</ul>" if fli else "")
      +(f'{H2}Key features</h2><ul style="margin:0 0 28px;padding-left:20px;line-height:1.7">'+"".join(f"<li>{e(f)}</li>" for f in r["features"])+"</ul>" if r.get("features") else "")+phtml
      +f'{H2}{e(n)} FAQ</h2>'+"".join(f'<details style="margin:0 0 10px"><summary style="cursor:pointer;font-weight:600">{e(q)}</summary><p style="margin:8px 0 0">{e(a)}</p></details>' for q,a in faq)+'<div style="margin-bottom:28px"></div>')
    app={"@type":"SoftwareApplication","name":n,"url":prim,"description":" ".join(r["long"])[:500],"applicationCategory":"DeveloperApplication" if x["audience"]=="builders" else "BusinessApplication","applicationSubCategory":cat}
    # Offer only when the price is verified: official pricing page tiers, or a verified OSI open-source licence (free to use)
    F=r.get("facts") or {}
    if offers: app["offers"]=offers
    elif F.get("osi") and F.get("license"): app["offers"]={"@type":"Offer","price":"0","priceCurrency":"USD","description":"Open source ("+re.sub(r"^the ","",F["license"])+")"}
    if F.get("repo"): app["sameAs"]=F["repo"]
    if r.get("features"): app["featureList"]=r["features"]
    fq={"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}
    return out,(sec,app,fq,f"{n}: what it does, pricing and alternatives","lite")
