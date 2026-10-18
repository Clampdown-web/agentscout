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
/* Newsletter: links with data-nl (and the signup forms with data-nlform) never open a tab or leave the page.
   Nothing from Beehiiv loads with the page. A tap on "Subscribe free" loads Beehiiv's hosted signup form
   (agentscout.beehiiv.com/subscribe) in an iframe right there, so the visitor types their email once, in Beehiiv's form.
   (Beehiiv's page ignores ?email=, so we don't ask for the address twice.) consent.js keeps these forms hidden until
   embedded content is allowed. */
(function(){
var LATEST={title:"AgentScout Weekly #1: 5 agent tools worth trying",date:"Oct 16, 2026",sub:"Labeled for builders and everyday users"};
var SRC="https://agentscout.beehiiv.com/subscribe";
function open1(form,host,msg){var f=host.querySelector("iframe.nlframe");if(!f){f=document.createElement("iframe");f.className="nlframe";f.title="Newsletter signup form (Beehiiv)";f.src=SRC;host.appendChild(f)}
 f.classList.add("show");form.hidden=true;if(msg)msg.textContent="Enter your email in the box below and tap Subscribe. You stay on this page.";try{f.scrollIntoView({block:"nearest",behavior:"smooth"})}catch(e){}}
function wire(form,host,msg){form.addEventListener("submit",function(e){e.preventDefault();open1(form,host,msg)})}
function panel(){var p=document.createElement("div");p.className="nlpanel";p.setAttribute("role","region");p.setAttribute("aria-label","Newsletter signup");
p.innerHTML='<div class="nlin"><button type="button" class="nlx" aria-label="Close newsletter panel">×</button><h3>Get the best new AI agents, weekly</h3><p class="muted">One short email with new tools, launches and what\'s worth trying. Free, unsubscribe anytime.</p><p class="nllatest"><span class="b">Latest issue</span> <strong>'+ASe(LATEST.title)+'</strong> <span class="muted">· '+ASe(LATEST.date)+' · '+ASe(LATEST.sub)+'</span></p><form class="nlgo" action="'+SRC+'" method="get"><button class="btn primary" type="submit">Subscribe free</button></form><p class="nlmsg muted" aria-live="polite"></p></div>';
wire(p.querySelector("form"),p.querySelector(".nlin"),p.querySelector(".nlmsg"));p.querySelector(".nlx").onclick=function(){p.remove();document.querySelectorAll("[data-nl][aria-expanded=true]").forEach(function(a){a.setAttribute("aria-expanded","false")})};return p}
function anchorFor(a){var nav=a.closest("nav");if(nav)return nav;return a.closest("p,li,.card,.cta,.about,div")||a}
document.addEventListener("click",function(e){var a=e.target.closest("a[data-nl]");if(!a)return;e.preventDefault();
 var at=anchorFor(a),next=at.nextElementSibling,open=next&&next.classList.contains("nlpanel");
 document.querySelectorAll(".nlpanel").forEach(function(x){x.remove()});document.querySelectorAll("[data-nl]").forEach(function(x){x.setAttribute("aria-expanded","false")});
 if(open)return;var p=panel();at.insertAdjacentElement("afterend",p);a.setAttribute("aria-expanded","true");var i=p.querySelector("form button");i&&i.focus({preventScroll:true});p.scrollIntoView({block:"nearest",behavior:"smooth"})});
function init(){document.querySelectorAll("form[data-nlform]").forEach(function(f){var m=document.createElement("p");m.className="nlmsg muted";m.setAttribute("aria-live","polite");f.insertAdjacentElement("afterend",m);wire(f,f.closest(".nlbox")||f.parentNode,m)});
 document.querySelectorAll("a[data-nl]").forEach(function(a){a.setAttribute("aria-expanded","false");a.setAttribute("role","button")})}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",init):init()})();
/* Category icons (Lucide-style inline SVG, stroke currentColor). Mirrors app v10 catIcons.js; unknown categories fall back to "tag". */
(function(){var P={games:'<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 12h4M8 10v4M15 13h.01M18 11h.01"/>',coding:'<path d="m16 18 6-6-6-6M8 6l-6 6 6 6"/>',voice:'<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4"/>',vision:'<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',research:'<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',frameworks:'<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z"/>',"mcp & infra":'<circle cx="12" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><path d="M12 7v4M12 11l-6 6M12 11l6 6"/>',"evals & observability":'<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/>',"browser/computer use":'<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/>',"no-code builders":'<path d="m15 4 5 5L9 20H4v-5z"/><path d="M12 7l5 5"/>',"business agents":'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2M2 13h20"/>',"personal agents":'<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',"app builders":'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',productivity:'<path d="M18 6 7 17l-5-5M22 10l-7.5 7.5L13 16"/>',models:'<rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v4M15 1v4M9 19v4M15 19v4M1 9h4M1 15h4M19 9h4M19 15h4"/>',"memory & rag":'<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',"customer support":'<path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3"/>',"sales & marketing":'<path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/>',"security & governance":'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',"models & local runtimes":'<rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v4M15 1v4M9 19v4M15 19v4M1 9h4M1 15h4M19 9h4M19 15h4"/>',crypto:'<circle cx="12" cy="12" r="10"/><path d="M9 8h4.5a2 2 0 0 1 0 4H9h5a2 2 0 0 1 0 4H9zM9 8v8M11 6v2M11 16v2"/>',image:'<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-5-5L5 21"/>'},FB='<path d="M12 2H2v10l9.3 9.3a1 1 0 0 0 1.4 0l8.6-8.6a1 1 0 0 0 0-1.4z"/><circle cx="7" cy="7" r="1.5"/>';
var S={};Object.keys(P).forEach(function(k){S[k.replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"")]=k});
function svg(c){c=(c||"").trim().toLowerCase();return '<svg class="cico" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'+(P[c]||FB)+'</svg>'}
window.AS=window.AS||{};AS.catIcon=svg;
function slugCat(h,abs){var m=/categories\/([a-z0-9-]+)\.html/.exec(abs||h||"");return m&&m[1]!=="index"?(S[m[1]]||m[1].replace(/-/g," ")):null}
function add(el,c){if(!el)return;for(var i=0;i<el.children.length;i++)if((el.children[i].getAttribute("class")||"").indexOf("cico")>-1)return;el.insertAdjacentHTML("afterbegin",svg(c));el.classList.add("has-cico")}
function run(root){root=root||document;
 root.querySelectorAll(".b.cat").forEach(function(b){add(b,b.textContent)});
 root.querySelectorAll(".chip[data-c]").forEach(function(b){if(b.dataset.c!=="all")add(b,b.dataset.c)});
 root.querySelectorAll(".cattile[data-cat]").forEach(function(a){add(a,a.dataset.cat)});
 root.querySelectorAll('a[href$=".html"]').forEach(function(a){var c=slugCat(null,a.href);if(!c)return;if(a.classList.contains("b")||a.classList.contains("chip"))add(a,c);else if(a.classList.contains("card"))add(a.querySelector(".ct h3"),c)})}
function hdr(){var c=slugCat(location.pathname);if(c){var h=document.querySelector("main h1, section h1, h1");add(h,c)}}
function init(){run();hdr();new MutationObserver(function(ms){ms.forEach(function(m){m.addedNodes.forEach(function(n){if(n.nodeType===1)run(n.parentNode||n)})})}).observe(document.body,{childList:true,subtree:true})}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",init):init()})();

/* Relative "Added X days ago" for <time class="ago" datetime="YYYY-MM-DD"> (static date stays as fallback/tooltip) */
(function(){function ago(r){(r||document).querySelectorAll("time.ago:not([data-ago])").forEach(function(t){var d=t.getAttribute("datetime");if(!/^\d{4}-\d{2}-\d{2}$/.test(d))return;var p=d.split("-"),then=new Date(+p[0],p[1]-1,+p[2]),now=new Date(),n=Math.round((new Date(now.getFullYear(),now.getMonth(),now.getDate())-then)/864e5);if(n<0)return;t.title=t.textContent;t.textContent=n===0?"today":n===1?"yesterday":n<60?n+" days ago":n<730?Math.round(n/30.4)+" months ago":Math.round(n/365)+" years ago";t.setAttribute("data-ago","1")})}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",function(){ago()}):ago();window.asAgo=ago})();
