"""Write category <option>s into the homepage and /search/ panels at build time,
so the Category dropdown is full before any JS or data loads (Oct 22 2026)."""
import json, re, html
def run(t=None):
    if t is None:
        d=json.load(open("tools.json",encoding="utf-8")); t=d if isinstance(d,list) else d["tools"]
    cats=sorted({x["category"] for x in t if x.get("category")},key=str.lower)
    opts="".join(f'<option value="{html.escape(c)}">{html.escape(c)}</option>' for c in cats)
    for f,first in (("index.html",'<option value="all">Any category</option>'),("search/index.html",'<option value="">Any category</option>')):
        s=open(f,encoding="utf-8").read()
        if f.startswith("search/") and 'id="fcat"' not in s: continue  # /search/ is a forwarder now (Oct 23 2026)
        n,k=re.subn(r'(<select id="fcat"[^>]*>)(.*?)(</select>)',lambda m:m.group(1)+first+opts+m.group(3),s,count=1,flags=re.S)
        if not k: raise SystemExit(f"build_catopts: no #fcat in {f}")
        open(f,"w",encoding="utf-8").write(n)
    lighten(); agent_json()
    return len(cats)

ONERR=''' onerror="var i=this,n=+(i.dataset.r||0);if(n<2){i.dataset.r=n+1;setTimeout(function(){i.src=i.src.split('?')[0]+'?r='+(n+1)},1500*(n+1))}else i.remove()"'''
# one shared logo-retry handler instead of ~300 bytes inline on every <img> (same behaviour)
RETRY='<script id="fx-retry">document.addEventListener("error",function(e){var i=e.target;if(!i||i.tagName!=="IMG"||!i.closest(".ico"))return;var n=+(i.dataset.r||0);if(n<2){i.dataset.r=n+1;setTimeout(function(){i.src=i.src.split("?")[0]+"?r="+(n+1)},1500*(n+1))}else i.remove()},true)</script>'
# show the first 50 tools, then "Load more" (all items stay in the HTML for search engines and no-JS)
MORE='''<p id="fx-morep" style="text-align:center;margin:18px 0" hidden><button type="button" class="btn" id="fx-more" style="min-height:44px">Load more</button></p><script id="fx-lm">(function(){var S=%s,P=50,m=document.querySelector("main"),it=[].slice.call(m.querySelectorAll(S)),shown=P;var mh=document.getElementById("makers");if(mh){var mg=mh.nextElementSibling;while(mg&&!mg.matches(".grid"))mg=mg.nextElementSibling;if(mg){var mk=[].slice.call(mg.querySelectorAll(S)),K=12;it=mk.slice(0,K).concat(it.filter(function(x){return mk.indexOf(x)<0}),mk.slice(K));shown=P+K}}if(it.length<=P)return;var hs=[].slice.call(m.querySelectorAll("h2"));function seg(h){var a=[],e=h.nextElementSibling;while(e&&e.tagName!=="H2"){a.push(e);e=e.nextElementSibling}return a}
function apply(){it.forEach(function(x,k){x.style.display=k<shown?"":"none"});var nextVis=true;for(var j=hs.length-1;j>=0;j--){var h=hs[j],s=seg(h),n=0,v=0;s.forEach(function(e){[].forEach.call(e.matches(S)?[e]:e.querySelectorAll(S),function(x){n++;if(x.style.display!=="none")v++})});if(!n&&!h.classList.contains("rgroup")){nextVis=true;continue}var vis=n?v>0:nextVis;h.style.display=vis?"":"none";s.forEach(function(e){e.style.display=vis?"":"none"});nextVis=vis}
var b=document.getElementById("fx-morep"),lv=it[Math.min(shown,it.length)-1].closest("ul,.grid");lv.parentNode.insertBefore(b,lv.nextSibling);b.hidden=shown>=it.length;var r=it.length-shown;document.getElementById("fx-more").textContent="Load more ("+r+" more)"}
document.getElementById("fx-more").onclick=function(){shown+=P;apply()};apply()})()</script>'''
LM={"free-tools.html":'"ul>li:has(> a[href^=\\"tools/\\"])"',"new.html":'"a.card.rcard"'}
def lighten():
    import re
    for f,sel in LM.items():
        s=open(f,encoding="utf-8").read()
        s=s.replace(ONERR,"")
        s=re.sub(r'<script id="fx-retry">.*?</script>','',s,flags=re.S)
        s=re.sub(r'<p id="fx-morep".*?</script>','',s,flags=re.S)
        s=re.sub(r'(<main\b[^>]*>)',lambda m:m.group(1)+RETRY,s,count=1)
        s=s.replace('</main>',MORE%sel+'</main>',1)
        open(f,"w",encoding="utf-8").write(s)
def agent_json():
    import shutil; shutil.copyfile(".well-known/agent.json","agent.json")
if __name__=="__main__": print(run())
