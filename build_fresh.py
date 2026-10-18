"""Freshness + scanability pass (Oct 18 2026). Idempotent post-processing, run at the end of build_site.py (before build_og).
- Visible 'Updated <Month D, YYYY>' line under the intro on tool, category, best-of, task and /s/ pages. The date is real data:
  for a tool page the latest of its link-check date ("verified") and the date it was added; for a list page the latest such
  date across the tools listed on it (category pages: every tool in the category). Dates in tools.json are Pacific dates.
- The same date as dateModified in the page's WebPage/CollectionPage JSON-LD.
- A short 'Quick comparison' table (tool, pricing, best for, open source) near the top of best-of and category pages, built only
  from existing listing data: pricing as the maker states it (short label), "best for" = the listing's first use-case tag
  (the same tag shown on the tool page), open source = Yes / Source-available / Open weights when the stated pricing says so,
  otherwise left blank (never guessed)."""
import glob,re,json,html,datetime
e=lambda s:html.escape(str(s or ""))
def _date(x): return max(x.get("verified") or "",x.get("added") or "")
def _fmt(d): return datetime.date.fromisoformat(d).strftime("%B %-d, %Y")
def _main(s):
    a=s.find("<main"); b=s.find('<section id="nlblock"',a)
    return a,(b if b>0 else s.find("</main>",a))
def _slugs(s,bys):
    a,b=_main(s); out=[]
    for sl in re.findall(r'href="\.\./tools/([a-z0-9-]+)\.html"',s[a:b]):
        if sl in bys and sl not in out: out.append(sl)
    return out
def _os(p):
    p=p.lower()
    if p.startswith(("open source","open standard")): return "Yes"
    if p.startswith("open weights"): return "Open weights"
    if p.startswith("source-available"): return "Source-available"
    return ""
def _bestfor(x):
    u=(x.get("use_cases") or [""])[0]
    return u[:1].upper()+u[1:] if u and u!=x.get("category") else ""
def table(rows,total,bys):
    trs="".join(f'<tr><th scope="row"><a href="../tools/{x["slug"]}.html">{e(x["name"])}</a></th><td>{e(x["pricing"])}</td><td>{e(_bestfor(x))}</td><td>{e(_os(x["pricing"]))}</td></tr>' for x in rows)
    cap=f"Top {len(rows)} of {total:,} listed below" if total>len(rows) else f"All {len(rows)} listed below"
    return (f'<!--xl:cmp--><div class="cmpwrap"><h2 class="cmph">Quick comparison <span>{cap}. Pricing as the maker states it; blank means we don\'t have it.</span></h2>'
            f'<div class="cmpscroll"><table class="cmptbl"><thead><tr><th scope="col">Tool</th><th scope="col">Pricing</th><th scope="col">Best for</th><th scope="col">Open source</th></tr></thead><tbody>{trs}</tbody></table></div></div><!--/xl:cmp-->')
def _ld(s,date,types):
    def fix(m):
        raw=m.group(1)
        try: d=json.loads(raw)
        except Exception: return m.group(0)
        nodes=d.get("@graph",[d]) if isinstance(d,dict) else (d if isinstance(d,list) else [])
        hit=False
        for n in nodes:
            if isinstance(n,dict) and n.get("@type") in types: n["dateModified"]=date; hit=True
        if not hit: return m.group(0)
        out=json.dumps(d,ensure_ascii=False) if '": ' in raw else json.dumps(d,ensure_ascii=False,separators=(",",":"))
        return '<script type="application/ld+json">'+out.replace("</","<\\/")+"</script>"
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>',fix,s,flags=re.S)
def _upd(s,date):
    s=re.sub(r'<p class="updated">.*?</p>','',s,flags=re.S)
    tag=f'<p class="updated">Updated <time datetime="{date}">{_fmt(date)}</time></p>'
    a,b=_main(s); m=re.compile(r'<p class="lede"[^>]*>.*?</p>',re.S).search(s,a,b)
    if not m: return s,False
    return s[:m.end()]+tag+s[m.end():],True
def run(t):
    import build_extras,collections
    bys={x["slug"]:x for x in t}; bycat=collections.defaultdict(list)
    for x in t: bycat[build_extras.catslug(x["category"])].append(x)
    c=collections.Counter()
    files=[("tool",f) for f in sorted(glob.glob("tools/*.html"))]+[("cat",f) for f in sorted(glob.glob("categories/*.html"))]+[("best",f) for f in sorted(glob.glob("best/*.html"))]+[("task",f) for f in sorted(glob.glob("tasks/*.html"))]+[("s",f) for f in sorted(glob.glob("s/*.html"))]
    for kind,f in files:
        if f.endswith("/index.html"): continue
        s0=s=open(f).read()
        if 'name="robots" content="noindex' in s: continue
        s=re.sub(r"<!--xl:cmp-->.*?<!--/xl:cmp-->","",s,flags=re.S)
        if kind=="tool":
            x=bys.get(f[6:-5]); listed=[x] if x else []
        elif kind=="cat":
            listed=bycat.get(f[11:-5],[])
        else:
            listed=[bys[k] for k in _slugs(s,bys)]
        if not listed: c["no_data"]+=1; continue
        date=max(_date(x) for x in listed)
        s,ok=_upd(s,date); c["updated" if ok else "no_lede"]+=1
        s=_ld(s,date,("WebPage","CollectionPage"))
        if kind in ("cat","best"):
            order=_slugs(s,bys)
            if kind=="cat": order=[k for k in order if bys[k] in listed] or [x["slug"] for x in listed]
            rows=[bys[k] for k in order[:10]]
            if len(rows)>=3:
                tb=table(rows,len(order) if kind=="best" else len(listed),bys)
                a,b=_main(s); anchor=None
                for pat in (r'<p class="muted" style="margin:0 0 18px"><strong>How we ranked:</strong>.*?</p>',r'<p class="tcount"[^>]*>.*?</p>',r'<p class="updated">.*?</p>'):
                    m=re.compile(pat,re.S).search(s,a,b)
                    if m: anchor=m; break
                if anchor: s=s[:anchor.end()]+tb+s[anchor.end():]; c["tables"]+=1
        if s!=s0: open(f,"w").write(s)
    print("freshness:",dict(c))
if __name__=="__main__": run(json.load(open("tools.json")))
