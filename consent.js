/* AgentScout privacy choices. Categories: necessary (always on: saved tools, votes, theme), analytics (anonymous
   counts sent by track.js) and embeds (the Beehiiv newsletter sign-up, which may set Beehiiv's own cookies).
   Strict regions (from the Worker's /geo; any failure counts as strict): banner with Accept all / Reject all /
   Customize, and nothing optional runs until the visitor chooses. Elsewhere: a small dismissible notice, analytics
   and embeds on by default, opt-out one tap away. The choice is kept in localStorage "as_consent". */
(function(){
  var KEY="as_consent",V=1,GEO="https://agentscout-image.agentscouthq.workers.dev/geo",subs=[];
  var S={ready:false,decided:false,strict:true,analytics:false,embeds:false};
  function load(){try{var j=JSON.parse(localStorage.getItem(KEY)||"null");if(j&&j.v===V)return j}catch(e){}return null}
  function save(){try{localStorage.setItem(KEY,JSON.stringify({v:V,analytics:S.analytics,embeds:S.embeds,strict:S.strict,ts:new Date().toISOString()}))}catch(e){}}
  function emit(){document.documentElement.classList.toggle("as-noembed",!S.embeds);subs.forEach(function(f){try{f(get())}catch(e){}})}
  function get(){return{ready:S.ready,decided:S.decided,strict:S.strict,analytics:S.analytics,embeds:S.embeds}}
  function set(a,em){S.analytics=!!a;S.embeds=!!em;S.decided=true;save();closeBar();emit()}
  window.ASConsent={get:get,set:set,open:openPicker,on:function(f){subs.push(f);if(S.ready)f(get())}};
  document.documentElement.classList.add("as-noembed");

  // ---- styles (theme variables from styles.css) ----
  var css='.as-ph{border:1px dashed var(--line);border-radius:10px;padding:14px;text-align:left;font-size:14px;color:var(--muted);max-width:460px;margin:0 auto}.as-ph p{margin:0 0 10px}html:not(.as-noembed) .as-ph{display:none}html.as-noembed form[action*="beehiiv.com"]{display:none!important}'+
  '.as-bar{position:fixed;z-index:999;left:50%;transform:translateX(-50%);bottom:calc(12px + env(safe-area-inset-bottom));width:calc(100% - 24px);max-width:760px;box-sizing:border-box;background:var(--card);color:var(--text);border:1px solid var(--line);border-radius:12px;box-shadow:0 4px 18px rgba(0,0,0,.14);padding:10px 14px;font-size:13px;line-height:1.45;display:flex;align-items:center;gap:12px}'+
  '.as-bar p{margin:0;color:var(--muted);flex:1;min-width:0}.as-bar p b{color:var(--text)}.as-bar .as-row{display:flex;flex-wrap:nowrap;gap:6px;flex:none}.as-bar .btn{height:32px;padding:0 12px;font-size:13px}.as-bar a{color:var(--accent)}'+
  '.as-note{left:16px;transform:none;width:auto;max-width:340px;padding:7px 34px 7px 12px;font-size:12.5px;border-radius:999px;box-shadow:0 2px 10px rgba(0,0,0,.12)}.as-note .as-x{position:absolute;top:50%;right:4px;transform:translateY(-50%);width:28px;height:28px;border:0;background:none;color:var(--muted);font-size:18px;line-height:1;cursor:pointer;border-radius:50%}'+
  'html.as-pad body{padding-bottom:var(--as-pad,0px)}html.as-pad .scrollbtns{bottom:calc(var(--as-pad,0px) + 12px + env(safe-area-inset-bottom))}'+
  '.as-link{background:none;border:0;padding:0;color:var(--accent);font:inherit;cursor:pointer;text-decoration:underline}'+
  '.as-ov{position:fixed;inset:0;z-index:1001;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;padding:16px}'+
  '.as-dlg{background:var(--card);color:var(--text);border:1px solid var(--line);border-radius:14px;max-width:520px;width:100%;max-height:90vh;overflow:auto;padding:20px;font-size:14px;line-height:1.5;box-shadow:0 12px 40px rgba(0,0,0,.3)}'+
  '.as-dlg h2{font-size:18px;margin:0 0 6px}.as-dlg>p{color:var(--muted);margin:0 0 14px}.as-dlg a{color:var(--accent)}.as-cat{display:flex;gap:12px;align-items:flex-start;border-top:1px solid var(--line);padding:12px 0}.as-cat div{flex:1}.as-cat b{display:block}.as-cat span{color:var(--muted);font-size:13px}'+
  '.as-sw{appearance:none;-webkit-appearance:none;flex:none;width:42px;height:24px;border-radius:999px;background:var(--line);position:relative;cursor:pointer;margin:2px 0 0;transition:background .15s}.as-sw::after{content:"";position:absolute;top:3px;left:3px;width:18px;height:18px;border-radius:50%;background:#fff;transition:left .15s}.as-sw:checked{background:var(--accent)}.as-sw:checked::after{left:21px}.as-sw:disabled{opacity:.6;cursor:not-allowed}.as-sw:focus-visible,.as-bar .btn:focus-visible,.as-dlg .btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}'+
  '.as-dlg .as-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}@media(max-width:640px){.as-bar{flex-wrap:wrap;gap:8px;bottom:calc(8px + env(safe-area-inset-bottom));width:calc(100% - 16px);padding:9px 12px}.as-bar .as-row{width:100%}.as-bar .as-row .btn,.as-dlg .as-row .btn{flex:1}.as-note{left:8px;width:auto;max-width:calc(100% - 88px);border-radius:12px}}';
  var st=document.createElement("style");st.textContent=css;document.head.appendChild(st);

  function el(h){var d=document.createElement("div");d.innerHTML=h.trim();return d.firstChild}
  var bar=null,lastFocus=null;
  var ro=null;
  function pad(){var r=document.documentElement;if(!bar){r.classList.remove("as-pad");r.style.removeProperty("--as-pad");return}r.style.setProperty("--as-pad",(bar.offsetHeight+24)+"px");r.classList.add("as-pad")}
  function mount(){document.body.appendChild(bar);pad();if(window.ResizeObserver){ro=new ResizeObserver(pad);ro.observe(bar)}else window.addEventListener("resize",pad)}
  function closeBar(){if(ro){ro.disconnect();ro=null}window.removeEventListener("resize",pad);if(bar){bar.remove();bar=null}pad()}
  var PRIV=relRoot()+"privacy.html";
  function relRoot(){var s=document.querySelector('script[src*="consent.js"]');return s?s.getAttribute("src").replace(/consent\.js.*$/,""):""}
  function showBanner(){closeBar();
    bar=el('<div class="as-bar" role="region" aria-labelledby="as-bt"><p><b id="as-bt">Privacy choices:</b> we\'d like to count anonymous visits (no cookies, nothing that identifies you) and load Beehiiv\'s newsletter sign-up, which may set its own cookies. Nothing optional runs until you choose. <a href="'+PRIV+'">Privacy policy</a></p><div class="as-row"><button type="button" class="btn" data-a="all">Accept all</button><button type="button" class="btn" data-a="none">Reject all</button><button type="button" class="btn" data-a="custom">Customize</button></div></div>');
    bar.addEventListener("click",function(e){var a=e.target.getAttribute("data-a");if(a==="all")set(1,1);else if(a==="none")set(0,0);else if(a==="custom")openPicker()});
    mount()}
  function showNotice(){closeBar();
    bar=el('<div class="as-bar as-note" role="region" aria-label="Privacy notice"><p>Anonymous visit counts, no cookies. <button type="button" class="as-link" data-a="opt">Opt out</button> · <button type="button" class="as-link" data-a="custom">Privacy choices</button></p><button type="button" class="as-x" data-a="ok" aria-label="Dismiss privacy notice">×</button></div>');
    bar.addEventListener("click",function(e){var a=e.target.getAttribute("data-a");if(a==="ok")set(S.analytics,S.embeds);else if(a==="opt")set(0,S.embeds);else if(a==="custom")openPicker()});
    mount()}
  function openPicker(){
    if(document.querySelector(".as-ov"))return;lastFocus=document.activeElement;
    var ov=el('<div class="as-ov"><div class="as-dlg" role="dialog" aria-modal="true" aria-labelledby="as-pt" aria-describedby="as-pd"><h2 id="as-pt">Privacy choices</h2><p id="as-pd">Choose what AgentScout may use. You can change this anytime from "Privacy choices" in the footer. <a href="'+PRIV+'">Privacy policy</a></p>'+
      '<label class="as-cat"><div><b>Necessary</b><span>Always on. Saved tools, votes, theme and the image generator cooldown, kept only in your browser.</span></div><input type="checkbox" class="as-sw" checked disabled aria-label="Necessary, always on"></label>'+
      '<label class="as-cat"><div><b>Analytics</b><span>Anonymous counts of page views, searches and clicks. No cookies, no personal data; stored only as daily totals.</span></div><input type="checkbox" class="as-sw" id="as-an"'+(S.analytics?" checked":"")+'></label>'+
      '<label class="as-cat"><div><b>Embedded content</b><span>The newsletter sign-up form, run by Beehiiv. Beehiiv may set its own cookies when you use it.</span></div><input type="checkbox" class="as-sw" id="as-em"'+(S.embeds?" checked":"")+'></label>'+
      '<div class="as-row"><button type="button" class="btn primary" data-a="save">Save choices</button><button type="button" class="btn" data-a="all">Accept all</button><button type="button" class="btn" data-a="none">Reject all</button></div></div></div>');
    function close(){ov.remove();document.removeEventListener("keydown",key,true);if(lastFocus&&lastFocus.focus)lastFocus.focus()}
    function key(e){if(e.key==="Escape"){e.preventDefault();close()}else if(e.key==="Tab"){var f=ov.querySelectorAll("a,button,input:not([disabled])"),a=f[0],z=f[f.length-1];if(e.shiftKey&&document.activeElement===a){e.preventDefault();z.focus()}else if(!e.shiftKey&&document.activeElement===z){e.preventDefault();a.focus()}}}
    ov.addEventListener("click",function(e){if(e.target===ov)return close();var a=e.target.getAttribute("data-a");if(!a)return;
      if(a==="save")set(ov.querySelector("#as-an").checked,ov.querySelector("#as-em").checked);else if(a==="all")set(1,1);else set(0,0);close()});
    document.addEventListener("keydown",key,true);document.body.appendChild(ov);ov.querySelector("#as-an").focus()}

  // "Load newsletter form" placeholders in front of every Beehiiv form (including ones app.js adds later)
  function ph(root){(root.querySelectorAll?root:document).querySelectorAll('form[action*="beehiiv.com"]').forEach(function(f){
    if(f.previousElementSibling&&f.previousElementSibling.classList.contains("as-ph"))return;
    var p=el('<div class="as-ph"><p>The newsletter sign-up is run by Beehiiv, which may set its own cookies. It loads only if you allow embedded content.</p><button type="button" class="btn">Load newsletter form</button></div>');
    p.querySelector("button").addEventListener("click",function(){set(S.analytics,1);var i=f.querySelector("input[type=email]");if(i)i.focus()});
    f.parentNode.insertBefore(p,f)})}
  document.addEventListener("click",function(e){var a=e.target.closest&&e.target.closest("[data-consent-open],a[href$='#privacy-choices']");if(a){e.preventDefault();openPicker()}});
  function boot(){ph(document);if(window.MutationObserver)new MutationObserver(function(ms){ms.forEach(function(m){m.addedNodes.forEach(function(n){if(n.nodeType===1)ph(n)})})}).observe(document.body,{childList:true,subtree:true});
    if(location.hash==="#privacy-choices")openPicker()}

  function start(strict){S.strict=strict;S.ready=true;
    if(strict){S.analytics=false;S.embeds=false;emit();showBanner()}else{S.analytics=true;S.embeds=true;emit();showNotice()}}
  var saved=load();
  function init(){boot();
    if(saved){S.decided=true;S.strict=!!saved.strict;S.analytics=!!saved.analytics;S.embeds=!!saved.embeds;S.ready=true;emit();return}
    var g=null;try{g=JSON.parse(sessionStorage.getItem("as_geo")||"null")}catch(e){}
    if(g&&typeof g.strict==="boolean")return start(g.strict);
    var done=false,timer=setTimeout(function(){if(!done){done=true;start(true)}},3000);
    fetch(GEO,{cache:"no-store"}).then(function(r){return r.ok?r.json():null}).then(function(j){if(done)return;done=true;clearTimeout(timer);
      var s=!(j&&j.strict===false);try{if(j)sessionStorage.setItem("as_geo",JSON.stringify({strict:s}))}catch(e){}start(s)})
      .catch(function(){if(!done){done=true;clearTimeout(timer);start(true)}})}
  document.readyState==="loading"?document.addEventListener("DOMContentLoaded",init):init();
})();
