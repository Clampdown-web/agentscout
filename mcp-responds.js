/* Responds sort for ranked MCP lists. Same rule as responds_sort() in scripts/mcp_response_rate.py.
   Only items with data-resp="1" (display rate, at least 3 responded-or-failed checks) move.
   They order by data-rr (rate_30d) then data-rn (n_30d). Everyone else keeps today's order.
   A thin sample is data-resp="0" and does not jump the list. */
(function(){
  var lists=[].slice.call(document.querySelectorAll("[data-responds-list]"));
  var sel=document.querySelector("[data-responds-sort]");
  if(!lists.length||!sel)return;
  lists.forEach(function(list){
    [].slice.call(list.children).forEach(function(el,i){el._i=i});
  });
  function byResponds(a,b){
    var ar=a.dataset.resp==="1", br=b.dataset.resp==="1";
    if(ar!==br)return ar?-1:1;
    if(ar){
      var d=(+b.dataset.rr)-(+a.dataset.rr);
      if(d)return d;
      d=(+b.dataset.rn)-(+a.dataset.rn);
      if(d)return d;
    }
    return a._i-b._i;
  }
  function run(){
    var mode=sel.value==="responds";
    lists.forEach(function(list){
      var kids=[].slice.call(list.children);
      kids.sort(mode?byResponds:function(a,b){return a._i-b._i});
      kids.forEach(function(el){list.appendChild(el)});
    });
    try{
      var p=new URLSearchParams(location.search);
      if(sel.value)p.set("sort",sel.value);else p.delete("sort");
      var q=p.toString();
      history.replaceState(null,"",location.pathname+(q?"?"+q:"")+location.hash);
    }catch(e){}
  }
  try{if(new URLSearchParams(location.search).get("sort")==="responds")sel.value="responds"}catch(e){}
  sel.addEventListener("change",run);
  if(sel.value)run();
})();
