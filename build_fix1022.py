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
# First 50 directory rows stay in the layout. The rest keep their HTML (search engines,
# no-JS) but are display:none from the first style pass, so the phone does not lay out
# ~1,800 rows before the intro can paint. Load more reveals the next 50.
FX_HEAD='<script id="fx-boot">document.documentElement.classList.add("fx-js")</script><style id="fx-css">html.fx-js .fx-tail{display:none}</style>'
FX_MORE='''<script id="fx-lm">(function(){var box=document.getElementById("fx-morep"),btn=document.getElementById("fx-more"),tpl=document.getElementById("fx-rest");if(!box||!btn||!tpl)return;var P=50,left=+(box.getAttribute("data-left")||0);if(left<=0)return;box.hidden=false;var hold=tpl.content.getElementById("fx-hold"),dest=document.getElementById("fx-first");function place(){var lis=document.querySelectorAll("main li"),last=null;for(var i=0;i<lis.length;i++){var a=lis[i].firstElementChild;if(a&&a.tagName==="A"&&(a.getAttribute("href")||"").indexOf("tools/")===0&&!lis[i].classList.contains("fx-tail"))last=lis[i]}if(!last)return;var ul=last.parentNode;if(box.previousElementSibling!==ul)ul.parentNode.insertBefore(box,ul.nextSibling)}function take(n){var moved=0;while(moved<n&&hold&&hold.firstElementChild){var li=hold.firstElementChild;li.classList.remove("fx-tail");dest.appendChild(li);moved++}while(moved<n){var h=tpl.content.querySelector("h2");if(!h)break;var e=h,ul=null;while(e){var next=e.nextElementSibling;if(e!==h&&e.tagName==="H2")break;e.classList.remove("fx-tail");tpl.parentNode.insertBefore(e,tpl);if(e.tagName==="UL")ul=e;e=next}if(!ul)break;var lis=ul.querySelectorAll("li.fx-tail");for(var i=0;i<lis.length&&moved<n;i++){lis[i].classList.remove("fx-tail");moved++}}return moved}btn.onclick=function(){var n=take(P);left=Math.max(0,left-n);box.setAttribute("data-left",left);box.hidden=left<=0;btn.textContent=left>0?"Load more ("+left+" more)":"Load more";place()}})()</script>'''
_VOID={"area","base","br","col","embed","hr","img","input","link","meta","source","track","wbr"}
def _strip_fx_marks(s):
    s=re.sub(r'<script id="fx-boot">.*?</script>','',s,flags=re.S)
    s=re.sub(r'<style id="fx-css">.*?</style>','',s,flags=re.S)
    s=re.sub(r'\sclass="fx-tail"','',s)
    s=re.sub(r'class="fx-tail ','class="',s)
    s=re.sub(r' fx-tail"','"',s)
    return s
def _add_class(tag, name):
    m=re.search(r'\sclass="([^"]*)"', tag)
    if not m:
        return tag[:-1]+f' class="{name}">'
    classes=m.group(1).split()
    if name in classes: return tag
    return tag[:m.start(1)]+name+" "+m.group(1)+tag[m.end(1):]
def _tag_end(raw, start):
    i, quote=start, None
    while i<len(raw):
        c=raw[i]
        if quote:
            if c==quote: quote=None
        elif c in "\"'": quote=c
        elif c==">": return i
        i+=1
    raise ValueError("unclosed tag")
def unwrap_fx_rest(s):
    """Put a previously stashed tail back, so a second build starts from the full list."""
    s=re.sub(r'<script id="ft-paint">.*?</script>','',s,flags=re.S)
    m=re.search(r'<template id="fx-rest"><div id="fx-hold">(.*?)</div>(.*?)</template>', s, re.S)
    if not m:
        return s
    hold, rest=m.group(1), m.group(2)
    s=s[:m.start()]+rest+s[m.end():]
    idx=s.find('<ul id="fx-first"')
    if idx>=0:
        ul_end=s.find("</ul>", idx)
        s=s[:ul_end]+hold+s[ul_end:]
        s=s.replace(' id="fx-first"','',1)
    else:
        s=s.replace("</ul><p id=\"fx-morep\"", hold+"</ul><p id=\"fx-morep\"", 1)
    return s
def move_big_ld(s):
    """The directory ItemList is ~230KB in <head>, ahead of the intro paragraph that is the LCP."""
    m=re.search(r'<script type="application/ld\+json">.{20000,}?</script>', s, re.S)
    if not m:
        return s
    block=m.group(0)
    if s.find("</body>")-m.end()<5000:
        return s
    s=s[:m.start()]+s[m.end():]
    return s.replace("</body>", block+"</body>", 1)
def flush_free(s):
    if 'id="ft-paint"' in s:
        return s
    if "<!--/quality-guide-->" in s:
        return s.replace("<!--/quality-guide-->", '<!--/quality-guide--><script id="ft-paint">void 0</script>', 1)
    return s
def stash_free_tail(s):
    """Keep the first page of rows in the live tree. The rest stays in the HTML, inside a template, so it is not styled before paint."""
    if 'id="fx-rest"' in s or 'id="fx-morep"' not in s:
        return s
    tail=s.find(' class="fx-tail"')
    li=s.find("<li", max(0, tail-80))
    if tail<0 or li<0 or li>tail:
        return s
    ul_end=s.find("</ul>", tail)
    if ul_end<0:
        return s
    hold=s[li:ul_end]
    s=s[:li]+s[ul_end:]
    ul_open=s.rfind("<ul ", 0, li)
    if ul_open<0:
        return s
    ul_tag_end=s.find(">", ul_open)
    if 'id="fx-first"' not in s[ul_open:ul_tag_end+1]:
        s=s[:ul_open]+s[ul_open:ul_tag_end].replace("<ul ", '<ul id="fx-first" ', 1)+s[ul_tag_end:]
    h=re.search(r'<h2 [^>]*class="[^"]*fx-tail', s)
    end=s.find('<script id="fx-lm">')
    if h and h.start()<end:
        d=s.find('class="fx-tail disclose"')
        if d>h.start():
            p_end=s.find("</p>", d)
            if p_end>0:
                end=p_end+4
        rest=s[h.start():end]
        s=s[:h.start()]+s[end:]
    else:
        rest=""
    tpl='<template id="fx-rest"><div id="fx-hold">'+hold+'</div>'+rest+'</template>'
    return s.replace('<script id="fx-lm">', tpl+'<script id="fx-lm">', 1)
def mark_free_directory(s, page_size=50):
    """Hide directory rows after the first page without a startup style pass over all of them."""
    from html.parser import HTMLParser
    s=unwrap_fx_rest(s)
    s=_strip_fx_marks(s)
    class Scan(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.stack=[]; self.nodes=[]
        def _pos(self):
            line, off=self.getpos()
            if line<=1: return off
            idx=0
            for _ in range(line-1):
                idx=s.find("\n", idx)+1
            return idx+off
        def handle_starttag(self, tag, attrs):
            node={"tag":tag,"start":self._pos(),"attrs":dict(attrs),"parent":self.stack[-1] if self.stack else None,"children":[]}
            if node["parent"] is not None: node["parent"]["children"].append(node)
            self.nodes.append(node)
            if tag not in _VOID: self.stack.append(node)
        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)
        def handle_endtag(self, tag):
            while self.stack:
                node=self.stack.pop()
                node["end"]=self._pos()
                if node["tag"]==tag: break
    scan=Scan(); scan.feed(s)
    tools=[n for n in scan.nodes if n["tag"]=="li" and n["children"] and n["children"][0]["tag"]=="a" and n["children"][0]["attrs"].get("href","").startswith("tools/")]
    if len(tools)<=page_size: return s
    visible=set(id(n) for n in tools[:page_size])
    heads=[n for n in scan.nodes if n["tag"]=="h2"]
    mark=set()
    for i,h in enumerate(heads):
        end=heads[i+1]["start"] if i+1<len(heads) else len(s)
        group=[li for li in tools if h["start"]<li["start"]<end]
        if not group: continue
        if any(id(li) in visible for li in group):
            mark.update(id(li) for li in group if id(li) not in visible)
        else:
            mark.add(id(h))
            parent=h["parent"]
            if parent:
                for sib in parent["children"]:
                    if h["start"]<sib["start"]<end: mark.add(id(sib))
            mark.update(id(li) for li in group)
    edits=[]
    for n in scan.nodes:
        if id(n) not in mark: continue
        stop=_tag_end(s, n["start"])
        edits.append((n["start"], stop+1, _add_class(s[n["start"]:stop+1], "fx-tail")))
    ul=tools[page_size-1]["parent"]
    ul_end=s.find("</ul>", ul["end"])
    left=len(tools)-page_size
    button=f'<p id="fx-morep" style="text-align:center;margin:18px 0" hidden data-left="{left}"><button type="button" class="btn" id="fx-more" style="min-height:44px">Load more ({left} more)</button></p>'
    edits.append((ul_end+len("</ul>"), ul_end+len("</ul>"), button))
    head=s.find("</head>")
    edits.append((head, head, FX_HEAD))
    main=s.rfind("</main>")
    edits.append((main, main, FX_MORE))
    for start, stop, repl in sorted(edits, key=lambda x: x[0], reverse=True):
        s=s[:start]+repl+s[stop:]
    s=stash_free_tail(s)
    s=move_big_ld(s)
    s=flush_free(s)
    return s
def lighten():
    import re
    for f,sel in LM.items():
        s=open(f,encoding="utf-8").read()
        # The directory tail lives in free-tools-rest.html so the first screen is not a 1.5MB download.
        if f=="free-tools.html" and s.count('href="tools/')<80 and __import__("os").path.exists("free-tools-rest.html"):
            continue
        if f=="free-tools.html":
            s=unwrap_fx_rest(s)
        s=s.replace(ONERR,"")
        s=re.sub(r'<script id="fx-retry">.*?</script>','',s,flags=re.S)
        s=re.sub(r'<p id="fx-morep".*?</p>','',s,flags=re.S)
        s=re.sub(r'<script id="fx-lm">.*?</script>','',s,flags=re.S)
        s=re.sub(r'(<main\b[^>]*>)',lambda m:m.group(1)+RETRY,s,count=1)
        if f=="free-tools.html":
            s=mark_free_directory(s)
        else:
            s=s.replace("</main>", MORE%sel+"</main>", 1)
        open(f,"w",encoding="utf-8").write(s)
def agent_json():
    import shutil; shutil.copyfile(".well-known/agent.json","agent.json")
if __name__=="__main__": print(run())
