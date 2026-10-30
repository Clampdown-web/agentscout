(function(){
  var KEY="as_launch_checklist_v1";
  function load(){try{return JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){return{}}}
  function save(o){localStorage.setItem(KEY,JSON.stringify(o))}
  var boxes=[].slice.call(document.querySelectorAll("#lchks input[type=checkbox]"));
  var state=load();
  boxes.forEach(function(b){b.checked=!!state[b.value]});
  function paint(){var n=boxes.filter(function(b){return b.checked}).length;var el=document.getElementById("lprog");if(el)el.textContent=n+" of "+boxes.length+" done"}
  boxes.forEach(function(b){b.addEventListener("change",function(){var o=load();o[b.value]=b.checked;save(o);paint()})});
  paint();
})();
