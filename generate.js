(function(){
  var EX=["A friendly robot agent sorting a toolbox of glowing app icons","A team of tiny AI agents building a website, isometric illustration","A coding agent typing at a futuristic terminal, neon blue","A voice AI assistant as a glowing sound wave character","An AI browser agent surfing the web on a paper airplane"];
  var COOL=45000,KEY="as_ig_last",f=document.getElementById("ig-form"),p=document.getElementById("ig-prompt"),
      go=document.getElementById("ig-go"),st=document.getElementById("ig-status"),cnt=document.getElementById("ig-count"),
      out=document.getElementById("ig-out"),img=document.getElementById("ig-img"),op=document.getElementById("ig-open"),ex=document.getElementById("ig-ex"),busy=false,t;
  EX.forEach(function(s){var b=document.createElement("button");b.type="button";b.textContent=s;b.onclick=function(){p.value=s;upd()};ex.appendChild(b)});
  function upd(){cnt.textContent=p.value.length+"/300"}
  p.addEventListener("input",upd);
  function left(){var l=+localStorage.getItem(KEY)||0;return Math.max(0,COOL-(Date.now()-l))}
  function tick(){clearTimeout(t);if(busy)return;var r=left();if(r>0){go.disabled=true;st.textContent="Next image in "+Math.ceil(r/1000)+"s";t=setTimeout(tick,1000)}else{go.disabled=false;st.textContent=""}}
  f.addEventListener("submit",function(e){
    e.preventDefault();var q=p.value.trim().slice(0,300);if(!q||busy||left()>0)return;
    busy=true;go.disabled=true;st.textContent="Generating… this can take up to a minute.";
    localStorage.setItem(KEY,Date.now());
    var url="https://image.pollinations.ai/prompt/"+encodeURIComponent(q)+"?width=768&height=768&safe=true&seed="+Math.floor(Math.random()*1e9);
    var n=new Image();
    n.onload=function(){busy=false;img.src=url;op.href=url;out.hidden=false;tick()};
    n.onerror=function(){busy=false;st.textContent="Couldn't generate that one (busy, rate-limited or blocked by the safety filter). Try again shortly.";setTimeout(tick,4000)};
    n.src=url;
  });
  upd();tick();
})();
