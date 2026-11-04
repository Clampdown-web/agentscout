(function(){
  /* Daily art: read the live manifest (also used by the app) so site and app show the same image URL. */
  fetch("api/generator-daily.json?t="+Math.floor(Date.now()/3e5),{cache:"no-store"}).then(function(r){return r.json()}).then(function(d){if(d&&d.path)document.documentElement.style.setProperty("--gen-art","url("+d.path+")")}).catch(function(){});
  var WORKER_URL="https://api.agentscouthq.com/generate",WORKER_FB="https://agentscout-image.agentscouthq.workers.dev/generate";
  var TURNSTILE_SITEKEY="0x4AAAAAAFfaxf14aQF-sky1"; // same site key as reviews.js; the Worker checks it when TURNSTILE_ENABLED==="true"
  var EX=["A friendly robot agent sorting a toolbox of glowing app icons","A team of tiny AI agents building a website, isometric illustration","A coding agent typing at a futuristic terminal, neon blue","A voice AI assistant as a glowing sound wave character","An AI browser agent surfing the web on a paper airplane"];
  var COOL=45000,KEY="as_ig_last",f=document.getElementById("ig-form"),p=document.getElementById("ig-prompt"),
      go=document.getElementById("ig-go"),st=document.getElementById("ig-status"),cnt=document.getElementById("ig-count"),
      out=document.getElementById("ig-out"),img=document.getElementById("ig-img"),op=document.getElementById("ig-open"),nw=document.getElementById("ig-new"),
      ex=document.getElementById("ig-ex"),busy=false,t,last,tsToken="";
  if(TURNSTILE_SITEKEY){var d=document.createElement("div");d.className="cf-turnstile";d.id="ig-turnstile";d.setAttribute("data-sitekey",TURNSTILE_SITEKEY);d.style.margin="12px 0 0";d.style.minHeight="65px";var row=go.parentNode;if(row&&row.parentNode)row.parentNode.insertBefore(d,row.nextSibling);window.asTs=function(k){tsToken=k};d.dataset.callback="asTs";var s=document.createElement("script");s.src="https://challenges.cloudflare.com/turnstile/v0/api.js";s.async=true;document.head.appendChild(s)}
  var SH=["Robot toolbox","Tiny agents","Neon coder","Voice wave","Paper plane"],short=ex.hasAttribute("data-short");
  EX.forEach(function(s,i){var b=document.createElement("button");b.type="button";b.textContent=short?SH[i]:s;b.title=s;b.onclick=function(){p.value=s;upd()};ex.appendChild(b)});
  function upd(){if(cnt)cnt.textContent=p.value.length+"/300"}
  p.addEventListener("input",upd);
  function left(){var l=+localStorage.getItem(KEY)||0;return Math.max(0,COOL-(Date.now()-l))}
  function tick(){clearTimeout(t);if(busy)return;var r=left();if(r>0){go.disabled=true;st.textContent="Next image in "+Math.ceil(r/1000)+"s";t=setTimeout(tick,1000)}else{go.disabled=false;st.textContent=""}}
  function fail(m){busy=false;st.textContent=m;go.disabled=false;setTimeout(tick,6000)}
  f.addEventListener("submit",function(e){
    e.preventDefault();var q=p.value.trim().slice(0,300);if(!q||busy||left()>0)return;
    if(TURNSTILE_SITEKEY&&!tsToken){var hidden=f.querySelector('input[name="cf-turnstile-response"]');tsToken=(hidden&&hidden.value)||""}
    if(TURNSTILE_SITEKEY&&!tsToken){st.textContent="Please complete the quick check above, then press Generate.";return}
    busy=true;go.disabled=true;st.textContent="Generating… this usually takes a few seconds.";
    localStorage.setItem(KEY,Date.now());
    fetch(WORKER_URL,{method:"POST",headers:{"Content-Type":"text/plain;charset=UTF-8"},body:JSON.stringify({prompt:q,turnstileToken:tsToken})}).catch(function(){return fetch(WORKER_FB,{method:"POST",headers:{"Content-Type":"text/plain;charset=UTF-8"},body:JSON.stringify({prompt:q,turnstileToken:tsToken})})})
    .then(function(r){
      if(r.ok&&/^image\//.test(r.headers.get("Content-Type")||""))return r.blob();
      return r.json().catch(function(){return{}}).then(function(j){throw new Error(j.error||(r.status==429?"Today's free images are used up. Please try again tomorrow.":"Image generation failed. Please try again shortly."))});
    })
    .then(function(b){if(last)URL.revokeObjectURL(last);last=URL.createObjectURL(b);img.src=last;op.href=last;nw.href=last;out.hidden=false;busy=false;tick();if(window.turnstile)turnstile.reset()})
    .catch(function(err){try{window.turnstile&&turnstile.reset()}catch(e){}fail(err.message&&err.message!=="Failed to fetch"?err.message:"The generator is unavailable right now. Please try again later.")});
  });
  upd();tick();
})();
