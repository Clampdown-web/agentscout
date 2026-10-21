/* Unified site search box (Oct 21 2026, owner-approved): one compact box in the nav on every page.
   Typing shows up to 6 instant tool suggestions with logos (names index first, Pagefind tool results to fill);
   Enter or "See all results" opens /search/?q=. On /search/ itself the box drives the results page (no dropdown). */
(function(){
var f=document.querySelector("form[data-navsearch]");if(!f)return;
var inp=f.querySelector("input"),ul=f.querySelector("ul");
var onSearch=/^\/search\/?(index\.html)?$/.test(location.pathname);
if(onSearch){try{inp.value=new URLSearchParams(location.search).get("q")||""}catch(e){}return}
var names=null,words=null,pf=null,items=[],sel=-1,tok=0,deb;
var N=function(s){return (s||"").toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g,"")};
var C=function(s){return N(s).replace(/[^a-z0-9]+/g,"")};
var esc=function(s){return String(s||"").replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})};
function loadNames(){if(names)return Promise.resolve(names);return fetch("/search/names.json").then(function(r){return r.json()}).then(function(d){names=d;return d}).catch(function(){names=[];return names})}
function loadPf(){if(pf)return Promise.resolve(pf);return import("/pagefind/pagefind.js").then(function(m){pf=m;return pf.options({baseUrl:"/"}).then(function(){pf.init();return pf})}).catch(function(){pf=false;return false})}
function nameHits(q){var cq=C(q),nq=N(q),a=[],b=[],c=[];if(!cq)return [];
 for(var i=0;i<names.length;i++){var x=names[i],cn=C(x[0]);if(cn===cq||C(x[1])===cq)a.push(x);else if(cn.indexOf(cq)===0)b.push(x);else if(cq.length>=3&&(N(x[0]).indexOf(nq)>=0||cn.indexOf(cq)>0))c.push(x);if(a.length+b.length>=6)break}
 return a.concat(b,c).slice(0,6).map(function(x){return {t:x[0],u:"/tools/"+x[1]+".html",l:x[2]?"/"+x[2]:"",s:x[3]}})}
function loadWords(){if(words)return Promise.resolve(words);return fetch("/search/words.json").then(function(r){return r.json()}).then(function(d){words=d;return d}).catch(function(){words=[];return words})}
function lev(a,b){if(Math.abs(a.length-b.length)>2)return 9;var D=[],i,j;for(i=0;i<=a.length;i++){D[i]=[i];for(j=1;j<=b.length;j++)D[i][j]=i?Math.min(D[i-1][j]+1,D[i][j-1]+1,D[i-1][j-1]+(a[i-1]===b[j-1]?0:1),(i>1&&j>1&&a[i-1]===b[j-2]&&a[i-2]===b[j-1])?D[i-2][j-2]+1:9):j}return D[a.length][b.length]}
function fuzzyNames(q){var cq=C(q);if(cq.length<3)return [];var lim=cq.length<=5?1:2,r=[];
 for(var i=0;i<names.length;i++){var x=names[i],d=Math.min(lev(cq,C(x[0])),lev(cq,C(x[1])));if(d<=lim)r.push([d,x])}
 r.sort(function(a,b){return a[0]-b[0]});return r.slice(0,6).map(function(p){var x=p[1];return {t:x[0],u:"/tools/"+x[1]+".html",l:x[2]?"/"+x[2]:"",s:x[3]}})}
function fixQuery(q){var ws=N(q).split(/[^a-z0-9]+/).filter(Boolean);return ws.map(function(w){if(w.length<3)return w;var best=w,bd=9,bc=0,lim=w.length<=5?1:2;
 for(var i=0;i<words.length;i++){var v=words[i][0];if(v===w)return w;var d=lev(w,v);if(d<bd||(d===bd&&words[i][1]>bc)){bd=d;bc=words[i][1];best=v}}return bd<=lim?best:w}).join(" ")}
function draw(q){var h=items.map(function(it,i){return '<li role="option" id="nso'+i+'" aria-selected="'+(i===sel)+'"><a href="'+esc(it.u)+'">'+(it.l?'<img src="'+esc(it.l)+'" alt="" width="24" height="24" loading="lazy">':'<span class="nsph" aria-hidden="true">'+esc((it.t||"?").charAt(0))+'</span>')+'<span class="nst"><b>'+esc(it.t)+'</b>'+(it.s?'<span>'+esc(it.s)+'</span>':'')+'</span></a></li>'}).join("");
 h+='<li role="option" id="nso'+items.length+'" class="nsall" aria-selected="'+(sel===items.length)+'"><a href="/search/?q='+encodeURIComponent(q)+'">See all results for “'+esc(q)+'” →</a></li>';
 ul.innerHTML=h;ul.hidden=false;inp.setAttribute("aria-expanded","true");inp.setAttribute("aria-activedescendant",sel>=0?"nso"+sel:"")}
function close(){ul.hidden=true;sel=-1;inp.setAttribute("aria-expanded","false");inp.removeAttribute("aria-activedescendant")}
function update(){var q=inp.value.trim(),my=++tok;if(!q){items=[];close();return}
 loadNames().then(function(){if(my!==tok)return;items=nameHits(q);var pq=q;
  if(!items.length&&q.length>=3){items=fuzzyNames(q);return loadWords().then(function(){if(my!==tok)return;pq=fixQuery(q);if(C(pq)!==C(q)&&!items.length)items=nameHits(pq);return pq})}
  return pq}).then(function(pq){if(my!==tok||pq===undefined)return;sel=-1;draw(q);
  if(items.length<6&&q.length>=3)return loadPf().then(function(p){if(!p||my!==tok)return;return p.debouncedSearch(pq,{filters:{type:"Tools"}},150).then(function(r){if(!r||my!==tok)return;return Promise.all(r.results.slice(0,8).map(function(h){return h.data()})).then(function(ds){if(my!==tok)return;var seen={};items.forEach(function(i){seen[i.u]=1});
   ds.forEach(function(d){var u=d.url.replace(/\.html$/,"")+".html";if(items.length<6&&!seen[u]){seen[u]=1;items.push({t:(d.meta&&d.meta.title)||d.url,u:u,l:(d.meta&&d.meta.logo)||"",s:""})}});draw(q)})})})}).catch(function(){/* stale Pagefind chunk after a deploy (e.g. "invalid gzip data"): keep name suggestions, no page error */})}
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
