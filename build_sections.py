"""api/sections.json: the site's sections (categories, tasks, compare, best, news, image generator, submit) as JSON for the app.
Built from the same data/pages the site generator produces, so the app always matches the website."""
import json,re,glob,os,html,datetime
import build_tasks,build_extras
B=build_extras.B
def txt(s): return html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',s))).strip()
def first(rx,s,d=""):
    m=re.search(rx,s,re.S); return txt(m.group(1)) if m else d
def main_of(p):
    s=open(p).read(); return s[s.index('<main'):s.index('</main>')]
def slugs(m): 
    out=[]
    for x in re.findall(r'href="\.\./tools/([^"/]+)\.html"',m):
        if x not in out: out.append(x)
    return out
def build(t):
    from collections import Counter
    cats=Counter(x["category"] for x in t)
    categories=[{"name":c,"slug":build_extras.catslug(c),"count":n,"url":f"{B}categories/{build_extras.catslug(c)}.html"} for c,n in cats.most_common()]
    tasks=[]
    for s,(T,items) in build_tasks.mapping(t).items():
        tasks.append({"slug":s,"title":"AI agents for "+T[1],"name":T[1],"description":T[5],"tools":[x["slug"] for x in items],"url":f"{B}tasks/{s}.html"})
    compare=[]
    for a,b in build_extras.PAIRS:
        p=f"compare/{build_extras.cslug(a,b)}.html"
        if not os.path.exists(p): continue
        m=main_of(p); rows=[]
        for tr in re.findall(r'<tr><th>((?:(?!</th>).)*?)</th><td>(.*?)</td><td>(.*?)</td></tr>',m.split('<tbody>',1)[-1],re.S):
            lab=txt(tr[0])
            if lab=="Official site": continue
            rows.append([lab,txt(tr[1]),txt(tr[2])])
        compare.append({"slug":build_extras.cslug(a,b),"a":a,"b":b,"title":first(r'<h1[^>]*>(.*?)</h1>',m),
            "verdict":first(r'<p class="lede"[^>]*>(.*?)</p>',m),"note":first(r'<p class="disclose">(.*?)</p>',m),"rows":rows,"url":B+p})
    best=[]
    for p in sorted(glob.glob("best/*.html")):
        if p.endswith("/index.html") or "<main" not in open(p).read(): continue
        m=main_of(p); best.append({"slug":os.path.basename(p)[:-5],"title":first(r'<h1[^>]*>(.*?)</h1>',m),"lede":first(r'<p class="lede"[^>]*>(.*?)</p>',m),"tools":slugs(m),"url":B+p})
    try: news=[{**x,**({"page_url":B+x["page"]} if x.get("page") else {})} for x in json.load(open("news.json"))["items"]]
    except Exception: news=[]
    g=open("generate.html").read(); gm=g[g.index('<main'):g.index('</main>')] if '<main' in g else g
    generate={"title":first(r'<h1[^>]*>(.*?)</h1>',gm,"Free AI Image Generator"),"lede":first(r'<p class="lede"[^>]*>(.*?)</p>',gm),"url":B+"generate.html"}
    submit={"endpoint":"https://agentscout-image.agentscouthq.workers.dev/submit","fields":["name","website","github","category","pricing","desc","email","x","company"],
        "categories":[c for c,_ in cats.most_common()],"pricing":["Open source","Free","Freemium","Paid","Open source + cloud","Source-available","Source-available + cloud","Enterprise / contact sales"],"url":B+"submit.html"}
    free_tools=[{"name":"AI Image Generator","badges":["Free","image"],"description":"Type a prompt and get an image in seconds. Powered by FLUX.1 [schnell].","screen":"Generate","url":B+"generate.html"}]
    badges={"title":"Badges for makers","lede":"If your tool is on AgentScout, you can show it. Badges are free and link to your tool's page, so readers can see how it compares.",
        "kinds":[{"id":"listed","label":"Listed","desc":"for any tool in the directory."},{"id":"featured","label":"Featured","desc":"for tools we've picked as featured."}],
        "variants":["light","dark"],"svg":B+"badges/{id}-{variant}.svg","png":B+"badges/{id}-{variant}.png","link":B}
    out={"free_tools":free_tools,"badges":badges,"updated":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"categories":categories,"tasks":tasks,"compare":compare,"best":best,"news":news,"generate":generate,"submit":submit,
        "newsletter":{"url":"https://agentscout.beehiiv.com/","subscribe":"https://agentscout.beehiiv.com/subscribe","latest":{"title":"AgentScout Weekly #1: 5 agent tools worth trying","date":"2026-10-16","summary":"Labeled for builders and everyday users"}}}
    # Daily generator background: same file + version the site's generate.css uses (daily routine bumps ?v=)
    css=open("generate.css").read(); mv=re.search(r"--gen-art:url\((assets/gen-art\.webp\?v=[^)]+)\)",css)
    rel=mv.group(1) if mv else "assets/gen-art.webp"
    daily={"image":B+rel,"path":rel,"overlay":{"light":"rgba(239,239,254,0.5)","dark":"rgba(37,38,77,0.55)"},"base":{"light":"#EFEFFE","dark":"#25264D"},
        "border":{"light":"#5B5BF7","dark":"#9393FF"},"radius":12,"updated":out["updated"]}
    json.dump(daily,open("api/generator-daily.json","w"),indent=1)
    out["generate"]["daily"]=daily
    json.dump(out,open("api/sections.json","w"),ensure_ascii=False,separators=(",",":"))
    print("sections.json:",len(categories),"categories",len(tasks),"tasks",len(compare),"compare",len(best),"best",len(news),"news")
if __name__=="__main__":
    build(json.load(open("tools.json")))
