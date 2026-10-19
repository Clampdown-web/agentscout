"""Logos next to tool names in every tool listing that used to be text-only (Oct 18, 2026 PT).
Idempotent post-processing over the built HTML, run near the end of build_site.py:
- table cells: a tool link at the start of a <th>/<td> (Quick comparison tables on category, best-of, alternatives, task,
  /s/ and /for/ pages, GitHub-repo tables, compare tables) gets the tool's logo before its name;
- inline tool lists: 'Related: A · B' lines (compare pages) and 'pages on AgentScout: A · B' lines (free tools).
Logo markup is the site's standard small icon (build_extras.ico, 24px): same local asset, letter fallback underneath,
explicit width/height, loading=lazy, and the retry-on-error handler. alt="" because the tool name follows as text.
Prose mentions (sentences in ledes and paragraphs) are left as plain links on purpose."""
import glob,re,json,html
import build_extras
e=lambda s:html.escape(str(s))
def _icon(x,d):
    L=e(x["name"].strip()[:1].upper())
    return (f'<span class="ico sm"><span aria-hidden="true" data-l="{L}"></span><img src="{d}{x["logo"]}" alt="" width="24" height="24" '
            f'loading="lazy" decoding="async" {build_extras.ONERR}></span>')
CELL=re.compile(r'(<t[hd]\b[^>]*>\s*)<a ((?:class="[^"]*" )?)href="((?:\.\./)*)tools/([a-z0-9-]+)\.html"([^>]*)>(?!<span class="ico)')
INL=re.compile(r'<a href="((?:\.\./)*)tools/([a-z0-9-]+)\.html">(?!<span class="ico)')
LISTP=re.compile(r'<p\b[^>]*>(?:Related:|[^<]{0,200}pages on AgentScout:).*?</p>',re.S)
def apply(s,bys):
    n=0
    def cell(m):
        nonlocal n
        x=bys.get(m.group(4))
        if not x or not x.get("logo"): return m.group(0)
        cls=m.group(2)
        cls=('class="icol '+cls[7:]) if cls else 'class="icol" '
        n+=1
        return f'{m.group(1)}<a {cls}href="{m.group(3)}tools/{m.group(4)}.html"{m.group(5)}>{_icon(x,m.group(3))}'
    s=CELL.sub(cell,s)
    def inl(m):
        nonlocal n
        x=bys.get(m.group(2))
        if not x or not x.get("logo"): return m.group(0)
        n+=1; return f'<a class="icol" href="{m.group(1)}tools/{m.group(2)}.html">{_icon(x,m.group(1))}'
    s=LISTP.sub(lambda p:INL.sub(inl,p.group(0)),s)
    return s,n
def run(t):
    bys={x["slug"]:x for x in t}; tot=0; pages=0
    for f in glob.glob("**/*.html",recursive=True):
        if f.startswith(("app/","node_modules/","preview/")) or f in ("outreach-tracker.html","og.html","stats.js.html"): continue
        s=open(f,errors="ignore").read()
        if "tools/" not in s: continue
        s2,n=apply(s,bys)
        if n: open(f,"w").write(s2); tot+=n; pages+=1
    print(f"listlogos: {tot} logos added on {pages} pages")
if __name__=="__main__":
    run(json.load(open("tools.json")))
