/* Shared helpers: local-only upvotes and saves (localStorage). No server, no tracking. */
const ASe=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const AS={
  get(k){try{return JSON.parse(localStorage.getItem(k)||"{}")}catch{return{}}},
  set(k,v){localStorage.setItem(k,JSON.stringify(v))},
  voted(s){return!!AS.get("as_votes")[s]},saved(s){return!!AS.get("as_saves")[s]},
  toggle(k,s){const o=AS.get(k);o[s]?delete o[s]:o[s]=1;AS.set(k,o);return!!o[s]},
  savedCount(){return Object.keys(AS.get("as_saves")).length},
  up:'<svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 3l5 7H3z"/></svg>',
  bm:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 2.5h8v11l-4-3-4 3z"/></svg>',
  voteBtn(s){const on=AS.voted(s);return`<button class="vote ${on?"on":""}" data-vote="${ASe(s)}" aria-pressed="${on}" title="Upvote (saved on this device)">${AS.up}<span>${on?1:0}</span></button>`},
  saveBtn(s,label){const on=AS.saved(s);return`<button class="save ${on?"on":""}" data-save="${ASe(s)}" aria-pressed="${on}" title="Save to your list (this device)">${AS.bm}${label?`<span>${on?"Saved":"Save"}</span>`:""}</button>`},
  bind(root,onchange){root.addEventListener("click",e=>{const v=e.target.closest("[data-vote]"),s=e.target.closest("[data-save]");if(!v&&!s)return;e.preventDefault();e.stopPropagation();
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
