/* Category page filters + sorting (Oct 21 2026). Works on the static cards (data-p pricing class, data-o open source, data-a added, data-g GitHub stars); state lives in URL params price, os, sort. */
(function(){var G=document.getElementById("cgrid"),B=document.getElementById("cfilters");if(!G||!B)return;
var $=function(i){return document.getElementById(i)},C=[].slice.call(G.children),RV={},T=C.length;C.forEach(function(c,i){c._i=i});
var bay=function(r){return r&&r.count?(r.avg*r.count+12)/(r.count+3):0};
function nw(a,b){return (b.dataset.a||"").localeCompare(a.dataset.a||"")||a._i-b._i}
function run(){var pr=$("fprice").value,os=$("fos").checked,s=$("fsort").value,pk=pr==="freeplan"?["free","freemium"]:pr?[pr]:null,n=0;
 var srt=s==="new"?nw:s==="az"?function(a,b){return a.querySelector("h3").textContent.localeCompare(b.querySelector("h3").textContent)}:s==="stars"?function(a,b){return (+b.dataset.g)-(+a.dataset.g)||nw(a,b)}:s==="loved"?function(a,b){return bay(RV[b.dataset.s])-bay(RV[a.dataset.s])||(+b.dataset.g)-(+a.dataset.g)||nw(a,b)}:function(a,b){return a._i-b._i};
 var f=document.createDocumentFragment();C.slice().sort(srt).forEach(function(c){var ok=(!pk||pk.indexOf(c.dataset.p)>=0)&&(!os||c.dataset.o==="1");c.hidden=!ok;if(ok)n++;f.appendChild(c)});G.appendChild(f);
 $("ccount").textContent="Showing "+n+" of "+T+" tools"+(n?"":". No tools match these filters.");
 $("freset").hidden=!(pr||os||s);var nr=0;for(var k in RV)if(RV[k].count)nr++;$("snote").hidden=s!=="loved";$("snote").textContent="Most loved: tools with visitor star ratings first ("+nr+" rated so far, weighted toward 4★ until a tool has more ratings), then by GitHub stars, then newest.";
 try{var p=new URLSearchParams(location.search);[["price",pr],["os",os?"1":""],["sort",s]].forEach(function(x){x[1]?p.set(x[0],x[1]):p.delete(x[0])});var q=p.toString();history.replaceState(null,"",location.pathname+(q?"?"+q:"")+location.hash)}catch(e){}}
var p=new URLSearchParams(location.search),v=function(id,x,ok){if(ok.indexOf(x)>=0)$(id).value=x};
v("fprice",p.get("price")||"",["free","freeplan","freemium","paid","unknown"]);v("fsort",p.get("sort")||"",["new","loved","stars","az"]);$("fos").checked=p.get("os")==="1";
$("fprice").onchange=$("fos").onchange=$("fsort").onchange=run;$("freset").onclick=function(){$("fprice").value="";$("fos").checked=false;$("fsort").value="";run()};
run();
fetch("https://agentscout-image.agentscouthq.workers.dev/reviews/all",{headers:{"X-AgentScout-App":"1"}}).then(function(r){return r.ok?r.json():Promise.reject()}).catch(function(){return fetch("../reviews.json").then(function(r){return r.json()})}).then(function(j){if(j&&j.tools){RV=j.tools;if($("fsort").value==="loved")run()}}).catch(function(){});
})();
