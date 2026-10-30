function $(i){return document.getElementById(i)}
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
var W="https://votes.agentscouthq.com/roast";
var FAST="https://buy.stripe.com/3cIaEY6T15hlfJr135e7m0e";
function show(d){
  if(!d||d.error){$("rout").innerHTML='<p class="empty" role="alert">'+esc((d&&d.error)||"The check failed. Try again in a minute.")+'</p>';return}
  var rows=(d.checks||[]).map(function(c){
    return '<li style="margin:0 0 10px;list-style:none"><b>'+(c.ok?"✅":"❌")+" "+esc(c.label)+'</b> <span class="muted">'+c.points+' pts</span>'+(c.ok?"":'<br><span class="muted" style="font-size:13.5px">'+esc(c.fix)+'</span>')+'</li>'
  }).join("");
  var listed=d.listed?'<p>Already listed on AgentScout: <a href="../tools/'+esc(d.listed.slug)+'.html">'+esc(d.listed.name)+'</a>.</p>':'<p>Not in the AgentScout directory yet.</p>';
  $("rout").innerHTML='<div style="border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:18px 0;background:var(--card)"><h2 style="font-size:22px;margin:0 0 6px">'+d.score+'/100</h2><p class="muted" style="margin:0 0 12px;overflow-wrap:anywhere">'+esc(d.final_url||"")+'</p>'+listed+'<ul style="padding:0;margin:0">'+rows+'</ul>'
    +'<p style="margin:14px 0 0;display:flex;flex-wrap:wrap;gap:8px"><a class="btn primary" href="../submit.html">Submit free</a><a class="btn primary" href="'+FAST+'" target="_blank" rel="noopener noreferrer">Fast-Track ($15) →</a></p></div>'
}
function go(u){
  $("rb").disabled=true;$("rout").innerHTML='<p class="muted">Checking '+esc(u)+'…</p>';
  fetch(W+"?url="+encodeURIComponent(u)).then(function(r){return r.json()}).then(show).catch(function(){show({error:"The check failed. Try again in a minute."})}).finally(function(){$("rb").disabled=false})
}
$("rf").addEventListener("submit",function(ev){ev.preventDefault();var u=$("ru").value.trim();if(u)go(u)});
var hs=decodeURIComponent(location.hash.slice(1));if(hs){$("ru").value=hs;$("rf").requestSubmit()}
