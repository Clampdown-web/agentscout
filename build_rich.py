"""Optional rich SEO content for tool pages, from tool_rich.json (keyed by slug). Tools without an entry are unchanged."""
import json,html,os,re
e=lambda s:html.escape(str(s or ""))
R=json.load(open("tool_rich.json")) if os.path.exists("tool_rich.json") else {}
H2='<h2 style="font-size:16px;margin-bottom:10px">'
def apply(out,x,t,catslug,prim,B):
    r=R.get(x["slug"])
    if not r: return out,None
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
