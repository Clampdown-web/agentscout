/* Shared helpers: local-only upvotes and saves (localStorage). No server, no tracking. */
const ASe=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const AS={
  get(k){try{return JSON.parse(localStorage.getItem(k)||"{}")}catch{return{}}},
  set(k,v){localStorage.setItem(k,JSON.stringify(v))},
  voted(s){return!!AS.get("as_votes")[s]},saved(s){return!!AS.get("as_saves")[s]},
  toggle(k,s){const o=AS.get(k);o[s]?delete o[s]:o[s]=1;AS.set(k,o);return!!o[s]},
  savedCount(){return Object.keys(AS.get("as_saves")).length},
  up:'<svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 3l5 7H3z"/></svg>',
  bm:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"><path d="M8 13.6S2 10.1 2 5.9A3.1 3.1 0 0 1 8 4.3a3.1 3.1 0 0 1 6 1.6c0 4.2-6 7.7-6 7.7z"/></svg>',
  voteBtn(s){const on=AS.voted(s);return`<button class="vote ${on?"on":""}" data-vote="${ASe(s)}" aria-pressed="${on}" title="Upvote (saved on this device)">${AS.up}<span>${on?1:0}</span></button>`},
  saveBtn(s,label){const on=AS.saved(s);return`<button class="save ${on?"on":""}" data-save="${ASe(s)}" aria-pressed="${on}" title="Save to favorites (this device)" aria-label="Save to favorites">${AS.bm}${label?`<span>${on?"Saved":"Save"}</span>`:""}</button>`},
  bind(root,onchange){if(root===document){if(AS._bound&&!onchange)return;AS._bound=1}root.addEventListener("click",e=>{const v=e.target.closest("[data-vote]"),s=e.target.closest("[data-save]");if(!v&&!s)return;e.preventDefault();e.stopPropagation();
    if(v){const on=AS.toggle("as_votes",v.dataset.vote);document.querySelectorAll(`[data-vote="${CSS.escape(v.dataset.vote)}"]`).forEach(b=>{b.classList.toggle("on",on);b.setAttribute("aria-pressed",on);b.querySelector("span").textContent=on?1:0})}
    if(s){const on=AS.toggle("as_saves",s.dataset.save);document.querySelectorAll(`[data-save="${CSS.escape(s.dataset.save)}"]`).forEach(b=>{b.classList.toggle("on",on);b.setAttribute("aria-pressed",on);const sp=b.querySelector("span");if(sp)sp.textContent=on?"Saved":"Save"})}
    document.querySelectorAll("[data-saved-count]").forEach(n=>n.textContent=AS.savedCount());onchange&&onchange()})}
};
/* Scroll buttons (top + bottom). Injected on every page that loads app.js; no inline script needed. */
(function(){if(window.__asScroll)return;window.__asScroll=1;
function init(){var w=document.createElement("div");w.className="scrollbtns";
w.innerHTML='<button type="button" class="scrollbtn up" aria-label="Back to top" title="Back to top"><span aria-hidden="true">↑</span></button><button type="button" class="scrollbtn down" aria-label="Scroll to bottom" title="Scroll to bottom"><span aria-hidden="true">↓</span></button>';
document.body.appendChild(w);var up=w.querySelector(".up"),dn=w.querySelector(".down"),q=0;
up.onclick=function(){window.scrollTo({top:0,behavior:"smooth"})};
dn.onclick=function(){window.scrollTo({top:document.documentElement.scrollHeight,behavior:"smooth"})};
function upd(){q=0;var y=window.scrollY||0,h=document.documentElement.scrollHeight,v=window.innerHeight,fromBottom=h-(y+v);
up.classList.toggle("show",y>400);dn.classList.toggle("show",h>v+300&&fromBottom>300)}
function sch(){if(!q){q=1;requestAnimationFrame(upd)}}
addEventListener("scroll",sch,{passive:true});addEventListener("resize",sch);addEventListener("load",sch);addEventListener("pageshow",sch);
if(window.ResizeObserver)new ResizeObserver(sch).observe(document.body);upd()}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",init):init()})();
/* Heart (favorite) button on every static tool card; binds document clicks if the page didn't. */
(function(){function hearts(root){(root||document).querySelectorAll('a.card[href*="tools/"]').forEach(function(a){if(a.querySelector(".save"))return;var m=a.getAttribute("href").match(/tools\/([^\/]+)\.html/);if(!m)return;a.classList.add("hashrt");a.insertAdjacentHTML("beforeend",AS.saveBtn(m[1]).replace('class="save','class="save heart'))})}
window.ASHearts=hearts;
function init(){hearts();if(!AS._bound)AS.bind(document);document.querySelectorAll("[data-saved-count]").forEach(function(n){n.textContent=AS.savedCount()})}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",init):init()})();
/* Standard site tool card for JS-rendered lists (quiz, saved). Same markup as the built category/task cards. */
AS.wk=function(){var t;try{t=new Intl.DateTimeFormat("en-CA",{timeZone:"America/Los_Angeles",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date())}catch(e){t=new Date(Date.now()-7*36e5).toISOString().slice(0,10)}var d=new Date(t+"T00:00:00Z");d.setUTCDate(d.getUTCDate()-6);return d.toISOString().slice(0,10)};
AS.card=function(t,extra){var logo=t.logo?t.logo.replace(/^https:\/\/clampdown-web\.github\.io\/agentscout\//,""):"";
return '<a class="card tile" href="tools/'+ASe(t.slug)+'.html">'+(extra||"")+'<div class="ct"><span class="ico "><span aria-hidden="true">'+ASe((t.name||"?")[0])+'</span>'+(logo?'<img src="'+ASe(logo)+'" alt="'+ASe(t.name)+' logo" width="40" height="40" loading="lazy" decoding="async">':"")+'</span><div class="tn"><h3>'+ASe(t.name)+'</h3><div class="badges">'+((t.added||"")>=AS.wk()?'<span class="b new">New</span>':"")+'<span class="b cat">'+ASe(t.category)+'</span><span class="b">'+ASe(t.pricing)+'</span></div></div></div><p class="hook">'+ASe(t.description)+'</p></a>'};
AS.fixImgs=function(root){root.querySelectorAll(".ico img").forEach(function(i){i.addEventListener("error",function(){i.remove()})})};
