"""Mobile horizontal-overflow check (Oct 18, 2026 PT).
Loads pages in headless Chrome at 360px and 390px and fails if document.documentElement.scrollWidth > clientWidth.
  python3 scripts/check_overflow.py                 # one page of every type, local build (serves the repo on a free port)
  python3 scripts/check_overflow.py --all           # every sitemap page, local build
  python3 scripts/check_overflow.py --live [--all]  # same against https://agentscouthq.com
  python3 scripts/check_overflow.py --pages tools/x.html,new.html
Type mode also re-checks with every font scaled 1.3x (Android text-size setting); OVERFLOW_TEXT_SCALES=1,1.3,1.5 overrides.
Reports the widest offending elements for each failing page. Exit code 1 on any overflow."""
import sys,os,re,glob,threading,http.server,socketserver,functools
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TYPES=["index.html","bot-templates/index.html","s/best-mcp-servers.html","mcp/crypto-mcp-servers.html","s/ai-crypto-scam-checkers.html","categories/crypto.html","categories/photography-photo-editing.html","categories/coding.html","categories/mcp-servers.html","categories/agent-infra.html","tasks/agent-identity.html",
       "for/photographers.html","s/free-mcp-servers.html","best/ai-coding-agents.html","tools/cursor.html","tools/adobe-lightroom.html",
       "compare/index.html","alternatives/index.html","new.html","news.html","free-tools.html","free-tools/token-counter.html",
       "free-tools/ai-cost-calculator.html","free-tools/ai-agent-readiness-checker.html","quiz.html","submit.html","sponsor.html","categories/index.html","tasks/index.html","saved.html","generate.html","best/best-mcp-servers-2026.html","news/2026/10/index.html"]
def pages_all():
    sm=open(os.path.join(ROOT,"sitemap.xml")).read()
    return [u.replace("https://agentscouthq.com/","") or "index.html" for u in re.findall(r"<loc>([^<]+)</loc>",sm) if not u.endswith((".txt",".xml",".json"))]
def add_compare(P):  # first compare/alternatives detail pages, if any
    for g in ("compare/*-vs-*.html","alternatives/*.html"):
        f=sorted(glob.glob(os.path.join(ROOT,g)))
        f=[x for x in f if not x.endswith("index.html")]
        if f: P.append(os.path.relpath(f[0],ROOT))
    return P
JS="""()=>{const d=document.documentElement,W=d.clientWidth,o=[];if(d.scrollWidth<=W)return{sw:d.scrollWidth,cw:W,o};
for(const e of document.querySelectorAll('body *')){const r=e.getBoundingClientRect();if(r.width===0)continue;if(r.right>W+1||r.left<-1){
 let p=e.parentElement,clip=false;while(p&&p!==document.body){const s=getComputedStyle(p);if(/(auto|scroll|hidden|clip)/.test(s.overflowX)){clip=true;break}p=p.parentElement}
 if(!clip&&getComputedStyle(e).position!=='fixed')o.push(e.tagName+'.'+(typeof e.className==='string'?e.className:'')+' ['+Math.round(r.left)+','+Math.round(r.right)+'] '+(e.textContent||'').trim().slice(0,40))}}
return{sw:d.scrollWidth,cw:W,o:o.slice(0,6)}}"""
SCALEJS="""(k)=>{const els=[...document.querySelectorAll('body, body *')];const fs=els.map(e=>parseFloat(getComputedStyle(e).fontSize));els.forEach((e,i)=>e.style.setProperty('font-size',(fs[i]*k)+'px','important'))}"""
SCALES=[float(x) for x in os.environ.get("OVERFLOW_TEXT_SCALES","1" if "--all" in sys.argv else "1,1.3").split(",")]
WIDTHS=[int(x) for x in os.environ.get("OVERFLOW_WIDTHS","360,390").split(",")]
def main():
    live="--live" in sys.argv; P=pages_all() if "--all" in sys.argv else add_compare(list(TYPES))
    if "--pages" in sys.argv: P=sys.argv[sys.argv.index("--pages")+1].split(",")
    P=[p for p in P if os.path.exists(os.path.join(ROOT,p)) or live]
    if live: base="https://agentscouthq.com"
    else:
        class Q(http.server.SimpleHTTPRequestHandler):
            def log_message(self,*a): pass
        srv=socketserver.ThreadingTCPServer(("127.0.0.1",0),functools.partial(Q,directory=ROOT)); srv.daemon_threads=True
        threading.Thread(target=srv.serve_forever,daemon=True).start(); base=f"http://127.0.0.1:{srv.server_address[1]}"
    bad=[];errs=[]
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path="/usr/bin/google-chrome")
        for w in WIDTHS:
            c=b.new_context(viewport={"width":w,"height":800},is_mobile=True,has_touch=True,device_scale_factor=2)
            c.add_init_script("window.ASNoTrack=true;try{localStorage.setItem('as_consent',JSON.stringify({v:1,analytics:false,embeds:false,strict:false,ts:Date.now()}))}catch(e){}")
            c.route(re.compile(r"^https://[^/]*(workers\.dev|beehiiv\.com|challenges\.cloudflare\.com)/"),lambda r:r.abort())  # third-party hosts only
            pg=c.new_page()
            for p in P:
                try:
                    pg.goto(base+"/"+("" if p=="index.html" else p),wait_until="load",timeout=30000); pg.wait_for_timeout(900 if p=="index.html" else 250)
                    pg.add_style_tag(content="html,body{overflow-x:visible!important}")  # look past the html{overflow-x:clip} safety net
                    r=pg.evaluate(JS); prev=1
                    for k in SCALES:  # Android "text size" setting: scale every font, then re-check
                        if k==1 or r["sw"]>r["cw"]: continue
                        pg.evaluate(SCALEJS,k/prev); prev=k; pg.wait_for_timeout(100); r=pg.evaluate(JS)
                        if r["sw"]>r["cw"]: r["text_scale"]=k
                except Exception as ex:
                    try:  # one retry (live hosting can rate-limit a full crawl)
                        pg.close(); pg=c.new_page(); pg.wait_for_timeout(1500)
                        pg.goto(base+"/"+("" if p=="index.html" else p),wait_until="load",timeout=30000); pg.wait_for_timeout(250)
                        pg.add_style_tag(content="html,body{overflow-x:visible!important}"); r=pg.evaluate(JS)
                    except Exception as ex2: errs.append((w,p)); print(f"ERR {w} {p} {ex2}".splitlines()[0][:200]); continue
                if r["sw"]>r["cw"]: bad.append((w,p,r)); print(f"OVERFLOW {w}px{' text x'+str(r['text_scale']) if r.get('text_scale') else ''} {p}: scrollWidth {r['sw']} > {r['cw']}  {r['o']}")
            c.close()
        b.close()
    print(f"overflow check: {len(P)} pages x {len(WIDTHS)} widths ({', '.join(map(str,WIDTHS))}), {len(bad)} overflowing, {len(errs)} failed to load")
    sys.exit(1 if bad or errs else 0)
if __name__=="__main__": main()
