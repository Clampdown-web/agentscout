/* Unified site search box (Oct 21 2026, owner-approved): one compact box in the nav on every page.
   Typing shows up to 6 instant tool suggestions with logos (names index first, Pagefind tool results to fill);
   Enter or "See all results" opens /search/?q=. On /search/ itself the box drives the results page (no dropdown). */
(function(){
var f=document.querySelector("form[data-navsearch]");if(!f)return;
var inp=f.querySelector("input"),ul=f.querySelector("ul");
var onSearch=/^\/search\/?(index\.html)?$/.test(location.pathname);
if(onSearch){try{inp.value=new URLSearchParams(location.search).get("q")||""}catch(e){}return}
var names=null,pf=null,items=[],sel=-1,tok=0,deb;
var N=function(s){return (s||"").toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g,"")};
var C=function(s){return N(s).replace(/[^a-z0-9]+/g,"")};
var esc=function(s){return String(s||"").replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})};
function loadNames(){if(names)return Promise.resolve(names);return fetch("/search/names.json").then(function(r){return r.json()}).then(function(d){names=d;return d}).catch(function(){names=[];return names})}
function loadPf(){if(pf)return Promise.resolve(pf);return import("/pagefind/pagefind.js").then(function(m){pf=m;return pf.options({baseUrl:"/"}).then(function(){pf.init();return pf})}).catch(function(){pf=false;return false})}
function nameHits(q){var cq=C(q),nq=N(q),a=[],b=[],c=[];if(!cq)return [];
 for(var i=0;i<names.length;i++){var x=names[i],cn=C(x[0]);if(cn===cq||C(x[1])===cq)a.push(x);else if(cn.indexOf(cq)===0)b.push(x);else if(cq.length>=3&&(N(x[0]).indexOf(nq)>=0||cn.indexOf(cq)>0))c.push(x);if(a.length+b.length>=6)break}
 return a.concat(b,c).slice(0,6).map(function(x){return {t:x[0],u:"/tools/"+x[1]+".html",l:x[2]?"/"+x[2]:"",s:x[3]}})}
function draw(q){var h=items.map(function(it,i){return '<li role="option" id="nso'+i+'" aria-selected="'+(i===sel)+'"><a href="'+esc(it.u)+'">'+(it.l?'<img src="'+esc(it.l)+'" alt="" width="24" height="24" loading="lazy">':'<span class="nsph" aria-hidden="true">'+esc((it.t||"?").charAt(0))+'</span>')+'<span class="nst"><b>'+esc(it.t)+'</b>'+(it.s?'<span>'+esc(it.s)+'</span>':'')+'</span></a></li>'}).join("");
 h+='<li role="option" id="nso'+items.length+'" class="nsall" aria-selected="'+(sel===items.length)+'"><a href="/search/?q='+encodeURIComponent(q)+'">See all results for “'+esc(q)+'” →</a></li>';
 ul.innerHTML=h;ul.hidden=false;inp.setAttribute("aria-expanded","true");inp.setAttribute("aria-activedescendant",sel>=0?"nso"+sel:"")}
function close(){ul.hidden=true;sel=-1;inp.setAttribute("aria-expanded","false");inp.removeAttribute("aria-activedescendant")}
function update(){var q=inp.value.trim(),my=++tok;if(!q){items=[];close();return}
 loadNames().then(function(){if(my!==tok)return;items=nameHits(q);sel=-1;draw(q);
  if(items.length<6&&q.length>=3)return loadPf().then(function(p){if(!p||my!==tok)return;return p.debouncedSearch(q,{filters:{type:"Tools"}},150).then(function(r){if(!r||my!==tok)return;return Promise.all(r.results.slice(0,8).map(function(h){return h.data()})).then(function(ds){if(my!==tok)return;var seen={};items.forEach(function(i){seen[i.u]=1});
   ds.forEach(function(d){var u=d.url.replace(/\.html$/,"")+".html";if(items.length<6&&!seen[u]){seen[u]=1;items.push({t:(d.meta&&d.meta.title)||d.url,u:u,l:(d.meta&&d.meta.logo)||"",s:""})}});draw(q)})})})})}
inp.addEventListener("input",function(){clearTimeout(deb);deb=setTimeout(update,120)});
inp.addEventListener("focus",function(){loadNames();if(inp.value.trim())update()});
inp.addEventListener("keydown",function(e){var n=items.length+1;if(ul.hidden&&e.key!=="Enter")return;
 if(e.key==="ArrowDown"){e.preventDefault();sel=(sel+1)%n;draw(inp.value.trim())}
 else if(e.key==="ArrowUp"){e.preventDefault();sel=(sel-1+n)%n;draw(inp.value.trim())}
 else if(e.key==="Escape"){close()}
 else if(e.key==="Enter"&&sel>=0&&sel<items.length){e.preventDefault();location.href=items[sel].u}});
f.addEventListener("submit",function(e){e.preventDefault();var q=inp.value.trim();location.href="/search/"+(q?"?q="+encodeURIComponent(q):"")});
document.addEventListener("click",function(e){if(!f.contains(e.target))close()});
})();
