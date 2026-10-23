/* Agent Finder Quiz page. Questions + weights from api/quiz.json, scoring in quiz-score.js. State lives in the URL hash (#goal=coding&skill=developer&budget=free&oss=yes) so results are shareable. */
(function(){
var ROLE={coding:["developers","developers"],research:["researchers","researchers"],automation:["founders","founders and small businesses"],support:["customer-support-teams","customer support teams"],writing:["content-creators","content creators"],build:["ai-engineers","AI engineers"]};
var Q,T,box=document.getElementById("quiz"),res=document.getElementById("qresults");
function parse(){var a={};location.hash.replace(/^#/,"").split("&").forEach(function(p){var kv=p.split("=");if(kv[0]&&kv[1])a[decodeURIComponent(kv[0])]=decodeURIComponent(kv[1])});return a}
function hashOf(a){return Q.questions.filter(function(q){return a[q.key]}).map(function(q){return q.key+"="+encodeURIComponent(a[q.key])}).join("&")}
function step(a){for(var i=0;i<Q.questions.length;i++)if(!a[Q.questions[i].key])return i;return Q.questions.length}
function go(a){var h=hashOf(a);if(("#"+h)!==location.hash){history.pushState(null,"",h?"#"+h:location.pathname+location.search)}render()}
function render(){var a=parse(),i=step(a),n=Q.questions.length;
 if(i<n){var q=Q.questions[i];res.innerHTML="";
  box.innerHTML='<div class="qbox"><p class="qprog">Question '+(i+1)+' of '+n+(q.optional?" · optional":"")+'</p><div class="qbar"><i style="width:'+Math.round(i/n*100)+'%"></i></div><h2 class="qq">'+ASe(q.q)+'</h2><div class="qopts">'+q.options.map(function(o){return '<button type="button" class="qopt" data-k="'+ASe(q.key)+'" data-v="'+ASe(o.id)+'">'+ASe(o.label)+(o.hint?'<small>'+ASe(o.hint)+'</small>':"")+'</button>'}).join("")+'</div><div class="qnav">'+(i>0?'<button type="button" class="btn" data-back>← Back</button>':"")+(q.optional?'<button type="button" class="btn" data-k="'+ASe(q.key)+'" data-v="any">Skip</button>':"")+'</div></div>';
  var f=box.querySelector(".qopt");if(f&&document.activeElement&&document.activeElement.closest&&document.activeElement.closest("#quiz"))f.focus();return}
 var r=ASQuiz.rank(T,a,Q),lab=function(k){var q=Q.questions.filter(function(x){return x.key===k})[0],o=q&&q.options.filter(function(x){return x.id===a[k]})[0];return o?o.label:""};
 box.innerHTML='<div class="qbox"><p class="qprog">Your answers</p><div class="badges">'+Q.questions.map(function(q){return a[q.key]?'<span class="b">'+ASe(lab(q.key))+'</span>':""}).join("")+'</div><div class="qnav"><button type="button" class="btn" data-retake>↺ Retake</button><a class="btn" href="index.html#directory">View all tools</a><button type="button" class="btn primary" data-share>Copy share link</button><span class="muted" id="qshared" aria-live="polite"></span></div></div>';
 res.innerHTML='<h2>'+(r.length?"Your top "+r.length+" matches":"No close matches")+'</h2><p class="muted">'+(r.length?"Ranked from "+T.length+" link-checked tools by what you need, your technical level, budget and open-source preference.":"Try a different budget or technical level.")+'</p><div class="grid">'+r.map(function(t,k){return AS.card(t.seed?Object.assign({},t,{added:""}):t,'<span class="qrank">#'+(k+1)+'</span>')}).join("")+'</div>'+(ROLE[a.goal]?'<p style="margin-top:18px">More for you: <a href="for/'+ROLE[a.goal][0]+'.html">AI agents for '+ROLE[a.goal][1]+' →</a> · <a href="s/">Popular lists</a></p>':'<p style="margin-top:18px">More for you: <a href="for/index.html">Browse AI agents by role →</a> · <a href="s/">Popular lists</a></p>');
 AS.fixImgs(res);if(window.ASHearts)ASHearts(res)}
box.addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;var a=parse();
 if(b.hasAttribute("data-k")){a[b.dataset.k]=b.dataset.v;go(a);if(step(a)>=Q.questions.length&&window.ASTrack)ASTrack("quiz_complete",a.goal)}
 else if(b.hasAttribute("data-back")){var i=step(a);if(i>0)delete a[Q.questions[i-1].key];go(a)}
 else if(b.hasAttribute("data-retake")){go({})}
 else if(b.hasAttribute("data-share")){var u=location.href,m=document.getElementById("qshared");(navigator.clipboard?navigator.clipboard.writeText(u):Promise.reject()).then(function(){m.textContent="Link copied"},function(){m.textContent=u})}});
addEventListener("popstate",function(){Q&&render()});addEventListener("hashchange",function(){Q&&render()});
Promise.all([fetch("api/quiz.json").then(function(r){return r.json()}),fetch("api/tools.json").then(function(r){return r.json()})]).then(function(d){Q=d[0];T=Array.isArray(d[1])?d[1]:d[1].tools;render()}).catch(function(){box.innerHTML='<p class="empty">Couldn\'t load the quiz. Please refresh.</p>'});
})();
