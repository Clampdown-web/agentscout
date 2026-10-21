<div class="crumb"><a href="../index.html">AgentScout</a> / Search</div><section style="padding-top:20px;text-align:left">
<h1 style="text-align:left;margin-left:0">Search AgentScout</h1>
<form id="sf" role="search" class="sub" style="max-width:640px;margin:0 0 12px" action="./" method="get"><label for="sq" class="sr-only" style="position:absolute;left:-9999px">Search the whole site</label><input id="sq" name="q" type="search" placeholder="Search tools, guides, news, free tools…" autocomplete="off"><button class="btn primary">Search</button></form>
<div class="filters" role="group" aria-label="Filter results" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 8px">
<label for="ftype">Type</label><select id="ftype" class="ucsel"><option value="">All types</option><option>Tools</option><option>Categories</option><option>Guides &amp; best-of</option><option>News</option><option>Free tools</option><option>Pages</option></select>
<span id="toolf" style="display:contents"><label for="fprice">Pricing</label><select id="fprice" class="ucsel"><option value="">Any pricing</option><option>Free</option><option>Freemium</option><option>Paid</option><option>Not listed</option></select>
<label for="fcat">Category</label><select id="fcat" class="ucsel"><option value="">Any category</option></select>
<label style="display:inline-flex;align-items:center;gap:6px;min-height:44px"><input type="checkbox" id="fos"> Open source only</label></span>
<label for="fsort">Sort</label><select id="fsort" class="ucsel"><option value="">Relevance</option><option value="new">Newest</option></select>
<button type="button" id="fclear" class="chip" style="min-height:44px">Clear filters</button></div>
<p id="sstat" role="status" aria-live="polite" class="muted" style="min-height:24px;margin:6px 0 10px">Type a search to begin.</p>
<div id="sres" style="min-height:60vh"></div>
<p><button type="button" id="smore" class="btn" hidden>Show more results</button></p>
<noscript><p>Search needs JavaScript. Browse <a href="../categories/index.html">categories</a> or the <a href="../index.html#directory">directory</a> instead.</p></noscript>
</section>
<script type="module">
const $=id=>document.getElementById(id);const P=new URLSearchParams(location.search);
const F={type:"ftype",pricing:"fprice",category:"fcat"};let pf,page=0,hits=[],tok=0;const PER=20;
$("sq").value=P.get("q")||"";$("ftype").value=P.get("type")||"";$("fprice").value=P.get("price")||"";$("fos").checked=P.get("os")==="1";$("fsort").value=P.get("sort")==="new"?"new":"";
const esc=s=>String(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function toolMode(){const t=$("ftype").value;$("toolf").style.display=(t===""||t==="Tools")?"contents":"none"}
function sync(){const u=new URLSearchParams();const q=$("sq").value.trim();if(q)u.set("q",q);if($("ftype").value)u.set("type",$("ftype").value);if($("fprice").value)u.set("price",$("fprice").value);if($("fcat").value)u.set("cat",$("fcat").value);if($("fos").checked)u.set("os","1");if($("fsort").value)u.set("sort","new");history.replaceState(null,"","?"+u.toString())}
async function load(){if(pf)return pf;pf=await import("../pagefind/pagefind.js");await pf.options({baseUrl:"/",excerptLength:22});pf.init();
 const f=await pf.filters();const cats=Object.keys(f.category||{}).sort();$("fcat").insertAdjacentHTML("beforeend",cats.map(c=>`<option>${esc(c)}</option>`).join(""));$("fcat").value=P.get("cat")||"";return pf}
async function go(){const my=++tok;toolMode();sync();const q=$("sq").value.trim();const filters={};
 if($("ftype").value)filters.type=$("ftype").value;
 if($("ftype").value===""||$("ftype").value==="Tools"){if($("fprice").value)filters.pricing=$("fprice").value;if($("fcat").value)filters.category=$("fcat").value;if($("fos").checked)filters["open source"]="Yes"}
 if(!q&&!Object.keys(filters).length){$("sres").innerHTML="";$("smore").hidden=true;$("sstat").textContent="Type a search to begin.";return}
 $("sstat").textContent="Searching…";await load();
 const opts={filters};if($("fsort").value==="new")opts.sort={date:"desc"};
 const r=await pf.search(q||null,opts);if(my!==tok)return;hits=r.results;page=0;$("sres").innerHTML="";
 $("sstat").textContent=hits.length?`${hits.length} result${hits.length===1?"":"s"}${q?` for “${q}”`:""}`:`No results${q?` for “${q}”`:""}. Try fewer words or clear filters.`;await more(my)}
async function more(my){const part=await Promise.all(hits.slice(page*PER,(page+1)*PER).map(h=>h.data()));if(my!==tok)return;page++;
 const groups={};for(const d of part){const t=(d.meta&&d.meta.type)||"Pages";(groups[t]=groups[t]||[]).push(d)}
 const order=["Tools","Categories","Guides & best-of","Free tools","News","Pages"];let h="";
 for(const t of order){if(!groups[t])continue;h+=`<h2 style="font-size:16px;margin:22px 0 8px">${esc(t)}</h2><ul style="list-style:none;padding:0;margin:0">`+groups[t].map(d=>`<li style="margin:0 0 14px"><a href="${esc(d.url)}" style="display:inline-flex;align-items:center;gap:8px;min-height:44px;font-weight:600">${d.meta.image&&t==="Tools"?`<img src="${esc(d.meta.image)}" alt="" width="24" height="24" loading="lazy" style="border-radius:6px">`:""}${esc(d.meta.title||d.url)}</a><br><span class="muted" style="font-size:14px">${d.excerpt}</span></li>`).join("")+"</ul>"}
 $("sres").insertAdjacentHTML("beforeend",h);$("smore").hidden=page*PER>=hits.length}
let deb;$("sq").addEventListener("input",()=>{clearTimeout(deb);deb=setTimeout(go,250)});
$("sf").addEventListener("submit",e=>{e.preventDefault();go()});
["ftype","fprice","fcat","fos","fsort"].forEach(id=>$(id).addEventListener("change",go));
$("fclear").onclick=()=>{["ftype","fprice","fcat","fsort"].forEach(id=>$(id).value="");$("fos").checked=false;go();$("sq").focus()};
$("smore").onclick=()=>more(tok);
$("sq").addEventListener("focus",()=>load(),{once:true});
toolMode();if(P.toString())load().then(go);
</script>
