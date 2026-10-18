/* Saved (favorites) page: tools hearted on this device (localStorage "as_saves"). */
(function(){var el=document.getElementById("savedlist"),cnt=document.getElementById("savedn"),T=[];
function render(){var s=AS.get("as_saves"),r=T.filter(function(t){return s[t.slug]});cnt.textContent=r.length?r.length+" saved on this device":"";
 el.innerHTML=r.length?'<div class="grid">'+r.map(function(t){return AS.card(t)}).join("")+'</div>':'<div class="empty qbox" style="text-align:center"><p style="font-size:34px;margin:0;color:var(--accent)">♡</p><h2 style="font-size:19px;margin:6px 0">No saved tools yet</h2><p class="muted">Tap the heart on any tool to save it. Saves stay on this device.</p><div class="qnav" style="justify-content:center"><a class="btn primary" href="index.html#directory">Browse tools</a><a class="btn" href="quiz.html">Take the quiz</a></div><p class="muted" style="margin:14px 0 0">Not sure where to start? Browse <a href="for/index.html">AI agents by role</a> or <a href="s/">popular searches</a>.</p></div>';
 AS.fixImgs(el);if(window.ASHearts)ASHearts(el)}
document.addEventListener("click",function(e){if(e.target.closest("[data-save]"))setTimeout(render,0)});
addEventListener("storage",render);
fetch("api/tools.json").then(function(r){return r.json()}).then(function(d){T=Array.isArray(d)?d:d.tools;render()}).catch(function(){el.innerHTML='<p class="empty">Couldn\'t load tools. Please refresh.</p>'});})();
