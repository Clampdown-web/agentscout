/* Compare any two tools: type-ahead pickers over api/tools.json, side-by-side table, shareable ?a=slug&b=slug. */
function asSlug(s){s=String(s==null?"":s);return /^[a-z0-9][a-z0-9-]{0,80}$/.test(s)?s:""}
function asListingHttp(u){
  var s=String(u==null?"":u).trim();
  if(!s)return "";
  try{
    var x=new URL(s);
    if((x.protocol!=="http:"&&x.protocol!=="https:")||x.username||x.password)return "";
    return s;
  }catch(e){return ""}
}
function asListingLogo(u){
  var raw=String(u==null?"":u).trim().replace(/^https:\/\/clampdown-web\.github\.io\/agentscout\//,"assets/");
  if(!raw||raw.indexOf("..")>=0)return "";
  if(/^https?:\/\//i.test(raw)){
    try{
      var x=new URL(raw);
      if(x.protocol!=="https:"||x.username||x.password)return "";
      if(x.hostname!=="agentscouthq.com"&&x.hostname!=="www.agentscouthq.com")return "";
      if(!/^\/assets\/[A-Za-z0-9._/-]+$/.test(x.pathname))return "";
      return raw;
    }catch(e){return ""}
  }
  if(!/^\/?assets\/[A-Za-z0-9._/-]+$/.test(raw))return "";
  return raw;
}
(function(){
if(!window.ASimgErr)window.ASimgErr=function(i){var n=+(i.dataset.r||0);if(n<2){i.dataset.r=n+1;setTimeout(function(){i.src=i.src.split('?')[0]+'?r='+(n+1)},1500*(n+1))}else i.remove()};
var root=document.getElementById("cpick");if(!root)return;
var T=[],BS={},sel={a:"",b:""},PAIRS=(root.dataset.pairs||"").split(",");
var E=function(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})};
var res=document.getElementById("cp-res");
function ico(t){var src=asListingLogo(t.logo);return '<span class="ico sm"><span aria-hidden="true" data-l="'+E((t.name||"?")[0].toUpperCase())+'"></span>'+(src?'<img src="'+E(src)+'" alt="'+E(t.name)+' logo" width="40" height="40" loading="lazy" onerror="ASimgErr(this)">':"")+'</span>'}
function box(k){
  var inp=document.getElementById("cp-"+k),list=document.getElementById("cp-"+k+"-l"),hi=-1,cur=[];
  function show(){var q=inp.value.trim().toLowerCase();
    cur=(q?T.filter(function(t){return t.name.toLowerCase().indexOf(q)>=0||t.slug.indexOf(q)>=0}).sort(function(x,y){return x.name.toLowerCase().indexOf(q)-y.name.toLowerCase().indexOf(q)}):T).slice(0,8);
    hi=cur.length?0:-1;
    list.innerHTML=cur.map(function(t,i){return '<li role="option" data-i="'+i+'" class="'+(i===hi?"on":"")+'">'+ico(t)+'<span><b>'+E(t.name)+'</b><small>'+E(t.category)+'</small></span></li>'}).join("")||'<li class="none">No match</li>';
    list.hidden=false;inp.setAttribute("aria-expanded","true")}
  function pick(t){sel[k]=t.slug;inp.value=t.name;list.hidden=true;inp.setAttribute("aria-expanded","false")}
  inp.addEventListener("input",function(){sel[k]="";show()});
  inp.addEventListener("focus",show);
  inp.addEventListener("blur",function(){setTimeout(function(){list.hidden=true;inp.setAttribute("aria-expanded","false")},150)});
  inp.addEventListener("keydown",function(e){if(list.hidden)return;
    if(e.key==="ArrowDown"||e.key==="ArrowUp"){e.preventDefault();hi=(hi+(e.key==="ArrowDown"?1:-1)+cur.length)%cur.length;[].forEach.call(list.children,function(li,i){li.classList.toggle("on",i===hi)})}
    else if(e.key==="Enter"&&cur[hi]){e.preventDefault();pick(cur[hi])}else if(e.key==="Escape")list.hidden=true});
  list.addEventListener("mousedown",function(e){var li=e.target.closest("li[data-i]");if(li){e.preventDefault();pick(cur[+li.dataset.i])}});
  return {set:function(s){var t=BS[s];sel[k]=t?s:"";inp.value=t?t.name:""}};
}
var A,Bx;
function stars(n){return n?Number(n).toLocaleString("en-US"):"–"}
function fmt(d){if(!d)return"–";var p=d.split("-");return["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][+p[1]-1]+" "+(+p[2])+", "+p[0]}
function render(push){
  var a=BS[sel.a],b=BS[sel.b];
  if(!a||!b){res.innerHTML='<p class="muted" style="margin:14px 0 0">'+(sel.a||sel.b?"Pick a second tool.":"")+'</p>';return}
  if(a.slug===b.slug){res.innerHTML='<p class="muted" style="margin:14px 0 0">Pick two different tools.</p>';return}
  var sa=asSlug(a.slug),sb=asSlug(b.slug);
  var m=sa&&sb&&PAIRS.indexOf(sa+"-vs-"+sb)>=0?sa+"-vs-"+sb:sa&&sb&&PAIRS.indexOf(sb+"-vs-"+sa)>=0?sb+"-vs-"+sa:"";
  var row=function(l,f){return "<tr><th>"+l+"</th><td>"+f(a)+"</td><td>"+f(b)+"</td></tr>"};
  var btns=function(t){var w=asListingHttp(t.website||t.url),g=asListingHttp(t.github);return (w?'<a class="btn" href="'+E(w)+'" target="_blank" rel="noopener noreferrer">Website ↗</a> ':"")+(g?'<a class="btn" href="'+E(g)+'" target="_blank" rel="noopener noreferrer">GitHub ↗</a>':"")};
  res.innerHTML=(m?'<p class="cp-match">We have a written comparison for this pair: <a href="'+m+'.html">'+E(BS[m.split("-vs-")[0]]?BS[m.split("-vs-")[0]].name:a.name)+' vs '+E(BS[m.split("-vs-")[1]]?BS[m.split("-vs-")[1]].name:b.name)+' →</a></p>':"")+
   '<div class="tablewrap"><table class="cmp cp-t"><thead><tr><th><span class="sr">Feature</span></th>'+[a,b].map(function(t){var slug=asSlug(t.slug);return '<th><div class="cp-h"><a class="icol" href="'+(slug?"../tools/"+slug+".html":"#")+'">'+ico(t)+E(t.name)+'</a>'+(typeof AS!=="undefined"&&AS.saveBtn?AS.saveBtn(slug||t.slug).replace('class="save','class="save heart cp-heart'):"")+'</div></th>'}).join("")+'</tr></thead><tbody>'+
   row("Category",function(t){return '<span class="b cat">'+E(t.category)+'</span>'})+
   row("Pricing",function(t){return E(t.pricing)})+
   row("Open source",function(t){return t.open_source?"Yes"+(t.license?" ("+E(t.license)+")":""):"No"})+
   row("License",function(t){return E(t.license||(t.open_source?"See repo":"–"))})+
   row("GitHub stars",function(t){return stars(t.github_stars)})+
   row("Description",function(t){return E(t.description)})+
   row("Best for",function(t){var g=(t.tags&&t.tags.length?t.tags:t.goals)||[];return g.length?g.map(function(x){return '<span class="b">'+E(x)+'</span>'}).join(" "):"–"})+
   row("Added",function(t){return fmt(t.added)})+
   row("Links",btns)+'</tbody></table></div>';
  if(push){var u=location.pathname+"?a="+encodeURIComponent(a.slug)+"&b="+encodeURIComponent(b.slug);history.replaceState(null,"",u);if(window.ASTrack)ASTrack("compare_pick",a.slug+":"+b.slug)}
}
document.getElementById("cp-go").addEventListener("click",function(){render(true)});
document.getElementById("cp-swap").addEventListener("click",function(){var x=sel.a;A.set(sel.b);Bx.set(x);render(!!(BS[sel.a]&&BS[sel.b]))});
document.getElementById("cp-copy").addEventListener("click",function(){var b=this;if(!(BS[sel.a]&&BS[sel.b]))return;try{navigator.clipboard.writeText(location.origin+location.pathname+"?a="+sel.a+"&b="+sel.b);b.textContent="Link copied"}catch(e){}setTimeout(function(){b.textContent="Copy link"},1600)});
fetch("../api/tools.json").then(function(r){return r.json()}).then(function(d){T=(Array.isArray(d)?d:d.tools).slice().sort(function(x,y){return x.name.localeCompare(y.name)});T.forEach(function(t){BS[t.slug]=t});
  A=box("a");Bx=box("b");var p=new URLSearchParams(location.search);if(p.get("a"))A.set(p.get("a"));if(p.get("b"))Bx.set(p.get("b"));if(sel.a&&sel.b)render(false)})
 .catch(function(){res.innerHTML='<p class="empty">Couldn\'t load tools. Please refresh.</p>'});
})();
