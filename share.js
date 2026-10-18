/* AgentScout Share button + share counter. No libraries, no cookies.
   Markup: <span class="sharewrap"><button type="button" class="btn sharebtn" data-share ...>Share</button><span class="sharecount" hidden></span></span>
   - navigator.share (mobile, tablets, many desktops) opens the native share sheet; otherwise a small menu:
     Copy link, X, Facebook, LinkedIn, Reddit, WhatsApp, Email (new tab, rel=noopener).
   - Counter: GET /shares (cached ~10 min at the edge), shown from 3 shares up. A real share or copy from this button
     sends one POST /share, at most once per page per visitor per Pacific day (localStorage flag only). */
(function(){
  var API="https://agentscout-image.agentscouthq.workers.dev",MIN=3;
  function canon(){var l=document.querySelector('link[rel="canonical"]');return (l&&l.href)||location.href.split("#")[0].split("?")[0]}
  function path(){try{return new URL(canon()).pathname.toLowerCase()}catch(e){return location.pathname}}
  function withUtm(u,m){try{var x=new URL(u);x.searchParams.set("utm_source","share");if(m)x.searchParams.set("utm_medium",m);return x.href}catch(e){return u}}
  function title(){var h=document.querySelector("h1"),t="";if(h){h=h.cloneNode(true);[].forEach.call(h.querySelectorAll('[aria-hidden="true"]'),function(x){x.remove()});t=h.textContent}t=(t||document.title).replace(/\s+/g," ").trim();return t||document.title}
  function text(){var m=document.querySelector('meta[name="description"]');var d=(m&&m.content||"").trim();return d.length>140?d.slice(0,137).replace(/\s+\S*$/,"")+"…":d}
  function day(){try{return new Intl.DateTimeFormat("en-CA",{timeZone:"America/Los_Angeles"}).format(new Date())}catch(e){return new Date().toISOString().slice(0,10)}}
  function track(k){try{window.ASTrack&&window.ASTrack("button_click",k)}catch(e){}}
  var counts={},els=[];
  function label(n){return "Shared "+n.toLocaleString("en-US")+" times"}
  function render(){els.forEach(function(c){var n=counts[path()]||0;if(n>=MIN){c.textContent=label(n);c.hidden=false}else c.hidden=true})}
  function counted(){var k="as_shared:"+path();try{if(localStorage.getItem(k)===day())return true;localStorage.setItem(k,day())}catch(e){}return false}
  function record(how){
    track("share:"+how);
    if(counted())return;
    counts[path()]=(counts[path()]||0)+1;render();
    if(!window.ASNoTrack)try{fetch(API+"/share",{method:"POST",mode:"cors",keepalive:true,headers:{"Content-Type":"text/plain"},body:JSON.stringify({path:path()})}).catch(function(){})}catch(e){}
  }
  function load(){
    try{fetch(API+"/shares?paths="+encodeURIComponent(path()),{mode:"cors"}).then(function(r){return r.ok?r.json():null}).then(function(j){if(j&&j.counts){var p=path(),n=+j.counts[p]||0;if(n>(counts[p]||0))counts[p]=n;render()}}).catch(function(){})}catch(e){}
  }
  function nets(u,t){var e=encodeURIComponent,tt=t+" | AgentScout";return [
    ["X","https://x.com/intent/post?text="+e(tt)+"&url="+e(withUtm(u,"x"))],
    ["Facebook","https://www.facebook.com/sharer/sharer.php?u="+e(withUtm(u,"facebook"))],
    ["LinkedIn","https://www.linkedin.com/sharing/share-offsite/?url="+e(withUtm(u,"linkedin"))],
    ["Reddit","https://www.reddit.com/submit?url="+e(withUtm(u,"reddit"))+"&title="+e(t)],
    ["WhatsApp","https://wa.me/?text="+e(tt+" "+withUtm(u,"whatsapp"))],
    ["Email","mailto:?subject="+e(tt)+"&body="+e(text()+"\n\n"+withUtm(u,"email"))]]}
  var menu=null,owner=null;
  function close(focus){if(!menu)return;menu.remove();menu=null;if(owner){owner.setAttribute("aria-expanded","false");if(focus)owner.focus()}owner=null;document.removeEventListener("click",outside,true);document.removeEventListener("keydown",keys,true)}
  function outside(ev){if(menu&&!menu.contains(ev.target)&&ev.target!==owner)close(false)}
  function items(){return menu?[].slice.call(menu.querySelectorAll('[role="menuitem"]')):[]}
  function keys(ev){if(!menu)return;var it=items(),i=it.indexOf(document.activeElement);
    if(ev.key==="Escape"){ev.preventDefault();close(true)}
    else if(ev.key==="ArrowDown"){ev.preventDefault();it[(i+1)%it.length].focus()}
    else if(ev.key==="ArrowUp"){ev.preventDefault();it[(i-1+it.length)%it.length].focus()}
    else if(ev.key==="Home"){ev.preventDefault();it[0].focus()}
    else if(ev.key==="End"){ev.preventDefault();it[it.length-1].focus()}
    else if(ev.key==="Tab")close(false)}
  function copy(u,btn){
    function done(){btn.textContent="Copied ✓";btn.setAttribute("aria-label","Link copied");record("copy");setTimeout(function(){close(true)},900)}
    function legacy(){var ta=document.createElement("textarea");ta.value=u;ta.setAttribute("readonly","");ta.style.position="fixed";ta.style.opacity="0";document.body.appendChild(ta);ta.select();var ok=false;try{ok=document.execCommand("copy")}catch(e){}ta.remove();ok?done():(btn.textContent="Press Ctrl+C",window.prompt("Copy this link:",u))}
    if(navigator.clipboard&&window.isSecureContext)navigator.clipboard.writeText(u).then(done,legacy);else legacy()}
  function open(b){
    close(false);owner=b;b.setAttribute("aria-expanded","true");
    var u=canon(),t=title();
    menu=document.createElement("div");menu.className="sharemenu";menu.setAttribute("role","menu");menu.setAttribute("aria-label","Share this page");
    var c=document.createElement("button");c.type="button";c.setAttribute("role","menuitem");c.textContent="Copy link";
    c.addEventListener("click",function(ev){ev.preventDefault();copy(withUtm(u,"copy"),c)});menu.appendChild(c);
    nets(u,t).forEach(function(n){var a=document.createElement("a");a.setAttribute("role","menuitem");a.href=n[1];a.textContent=n[0];
      if(n[0]!=="Email"){a.target="_blank";a.rel="noopener noreferrer"}
      a.addEventListener("click",function(){record(n[0].toLowerCase());setTimeout(function(){close(false)},0)});menu.appendChild(a)});
    b.parentNode.appendChild(menu);
    document.addEventListener("click",outside,true);document.addEventListener("keydown",keys,true);
    c.focus()}
  function click(ev){var b=ev.currentTarget;
    if(menu&&owner===b){close(true);return}
    var u=withUtm(canon(),"native");
    if(navigator.share){navigator.share({title:title(),text:text(),url:u}).then(function(){record("native")},function(err){if(!err||err.name!=="AbortError")open(b)});return}
    open(b)}
  function init(){
    var bs=document.querySelectorAll("[data-share]");if(!bs.length)return;
    [].forEach.call(bs,function(b){b.setAttribute("aria-haspopup","menu");b.setAttribute("aria-expanded","false");b.addEventListener("click",click);
      var c=b.parentNode.querySelector(".sharecount");if(c){c.setAttribute("aria-live","polite");els.push(c)}});
    load()}
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();
