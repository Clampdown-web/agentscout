/* AgentScout anonymous analytics. No cookies, no personal data, no IP storage (the Worker only keeps daily
   aggregate counters). Runs only with analytics consent (consent.js / window.ASConsent): in strict regions nothing is
   sent until the visitor accepts; elsewhere it's on by default and can be turned off under "Privacy choices".
   sessionStorage is used only (after consent) to count each page once per tab.
   Each batch also carries the linking site's hostname only (document.referrer host, never the full URL) and this page's host.
   Opt-out: ?notrack (or ?notrack=1) on any page (our own devices); automated/headless browsers are skipped.
   Events: page_view, search, tool_click, outbound_link, button_click, quiz_complete, favorite_add, submit_tool, image_generate. */
(function(){
  // Opt-out for our own devices: open any page once with ?notrack (or ?notrack=1; sets a localStorage flag; ?notrack=0 clears it).
  // Automated browsers (navigator.webdriver, headless/automation user agents) never send anything.
  var OFF=false;
  try{var nt=new URLSearchParams(location.search).get("notrack");
    if(nt==="0"){localStorage.removeItem("as_notrack");note("Analytics is back on for this browser.")}
    else if(nt!==null){localStorage.setItem("as_notrack","1");note("Analytics is off for this browser. Open ?notrack=0 to turn it back on.")}
    OFF=localStorage.getItem("as_notrack")==="1"}catch(e){}
  try{if(navigator.webdriver||/HeadlessChrome|Headless|PhantomJS|Playwright|Puppeteer|Selenium|Lighthouse|bot\b|crawler|spider/i.test(navigator.userAgent||""))OFF=true}catch(e){}
  function note(m){function show(){var d=document.createElement("div");d.textContent=m;d.setAttribute("role","status");
    d.style.cssText="position:fixed;left:50%;bottom:16px;transform:translateX(-50%);z-index:99999;background:#111;color:#fff;padding:10px 14px;border-radius:8px;font:14px/1.4 system-ui,sans-serif;box-shadow:0 2px 10px rgba(0,0,0,.3)";
    document.body.appendChild(d);setTimeout(function(){d.remove()},5000)}
    document.body?show():document.addEventListener("DOMContentLoaded",show)}
  if(OFF){window.ASTrack=function(){};window.ASNoTrack=true;return}
  var URL_="https://api.agentscouthq.com/track",q=[],t=null;
  // Referrer: only the hostname of the page that linked here (e.g. "google.com"), never the full URL. "" = direct.
  var REF="";try{REF=document.referrer?new URL(document.referrer).hostname:""}catch(e){}
  // Campaign tags on the landing URL (utm_source/utm_medium/utm_campaign), lower-cased, max 40 chars each; sent with the batch, never stored per visitor.
  var UTM=null;try{var P_=new URLSearchParams(location.search),c_=function(k){return (P_.get(k)||"").toLowerCase().replace(/[^a-z0-9._\- ]/g,"").slice(0,40)};if(P_.get("utm_source")||P_.get("utm_medium")||P_.get("utm_campaign"))UTM={s:c_("utm_source"),m:c_("utm_medium"),c:c_("utm_campaign")}}catch(e){}
  // null = no decision yet (hold events in memory, send nothing); false = drop; true = send
  function ok(){var C=window.ASConsent;if(!C)return false;var s=C.get();if(!s.ready||(s.strict&&!s.decided))return null;return s.analytics}
  function flush(){if(!q.length)return;var a=ok();if(a===null)return;if(!a){q.length=0;return}var body=JSON.stringify(UTM?{source:"web",ref:REF,host:location.hostname,utm:UTM,events:q.splice(0,50)}:{source:"web",ref:REF,host:location.hostname,events:q.splice(0,50)});
    try{if(navigator.sendBeacon&&navigator.sendBeacon(URL_,new Blob([body],{type:"text/plain"})))return}catch(e){}
    try{fetch(URL_,{method:"POST",body:body,keepalive:true,headers:{"Content-Type":"text/plain"}}).catch(function(){})}catch(e){}}
  function track(e,k,qq){var ev={e:e};if(k)ev.k=String(k).slice(0,80);if(qq)ev.q=String(qq).slice(0,60);q.push(ev);clearTimeout(t);t=setTimeout(flush,2000)}
  window.ASTrack=track;
  addEventListener("pagehide",flush);document.addEventListener("visibilitychange",function(){if(document.visibilityState==="hidden")flush()});
  // page_view by path (once per tab per path)
  var pv=false;function pageView(){if(pv)return;pv=true;try{var pk="as_pv:"+location.pathname;if(!sessionStorage.getItem(pk)){sessionStorage.setItem(pk,"1");track("page_view",location.pathname)}}catch(e){track("page_view",location.pathname)}}
  if(window.ASConsent)ASConsent.on(function(s){if(ok()===true){pageView();flush()}else if(ok()===false)q.length=0});
  var here=(location.pathname.match(/\/tools\/([^\/]+)\.html$/)||[])[1]||"";
  // clicks
  document.addEventListener("click",function(ev){
    var sv=ev.target.closest&&ev.target.closest("[data-save]");
    if(sv){setTimeout(function(){if(sv.classList.contains("on"))track("favorite_add",sv.dataset.save)},0);return}
    var a=ev.target.closest&&ev.target.closest("a,button");if(!a)return;
    var h=a.getAttribute("href")||"";
    if(a.hasAttribute("data-pick")){track("editors_pick_click",a.dataset.pick);return track("tool_click",a.dataset.pick)}
    if(a.hasAttribute("data-nl"))return track("button_click","newsletter");
    if(/submit\.html/.test(h))return track("button_click","submit");
    if(/quiz\.html/.test(h))return track("button_click","quiz");
    if(/compare\//.test(h))return track("button_click","compare");
    if(/generate\.html/.test(h)||a.id==="ig-go")return track("button_click","generate");
    var m=h.match(/tools\/([^\/]+)\.html/);if(m)return track("tool_click",m[1]);
    if(/^https?:\/\//.test(h)&&a.host&&a.host!==location.host&&!/beehiiv\.com/.test(a.host)){
      var type=/github\.com/.test(a.host)?"github":(a.textContent||"").match(/website|visit|official/i)?"website":"other";
      track("outbound_link",(here?here+":":"")+type)}
  },true);
  // search: debounced 1.5s after typing stops, and on submit
  var st;document.addEventListener("input",function(ev){var el=ev.target;if(!el||el.type!=="search"&&el.id!=="q"&&el.name!=="h")return;clearTimeout(st);var v=el.value.trim();if(v.length<2)return;st=setTimeout(function(){track("search",null,v.toLowerCase())},1500)},true);
  document.addEventListener("submit",function(ev){var f=ev.target,i=f.querySelector&&f.querySelector('input[type=search],input[name=h],#q');if(i&&i.value.trim().length>1){clearTimeout(st);track("search",null,i.value.trim().toLowerCase())}},true);
  // image_generate: result image appears; submit_tool: success box appears
  function watch(){var img=document.getElementById("ig-img");if(img)img.addEventListener("load",function(){if(/^blob:/.test(img.src))track("image_generate")});
    var done=document.getElementById("sdone");if(done&&window.MutationObserver)new MutationObserver(function(){if(!done.hidden){track("submit_tool");flush()}}).observe(done,{attributes:true,attributeFilter:["hidden"]})}
  document.readyState==="loading"?document.addEventListener("DOMContentLoaded",watch):watch();
})();
