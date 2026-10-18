/* AgentScout ratings & reviews (tool pages). Static summary is rendered at build time; this refreshes it from the
   Worker and handles the form. Fails silently if the API is down. No cookies; a random visitor ID in localStorage
   ("as-vid") enforces one rating per tool per visitor. */
(function () {
  var W = "https://agentscout-image.agentscouthq.workers.dev";
  var sec = document.getElementById("reviews"); if (!sec || !window.fetch) return;
  var tool = sec.getAttribute("data-tool"), name = sec.getAttribute("data-name") || "this tool";
  var $ = function (s) { return sec.querySelector(s); };
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }
  function vid() {
    var v = store("as-vid");
    if (!v || !/^[a-f0-9]{32}$/.test(v)) { var a = new Uint8Array(16); crypto.getRandomValues(a); v = Array.prototype.map.call(a, function (b) { return ("0" + b.toString(16)).slice(-2); }).join(""); store("as-vid", v); }
    return v;
  }
  function mine() { try { return JSON.parse(store("as-rated") || "{}"); } catch (e) { return {}; } }
  function stars(n) { return '<span class="rv-stars" style="--r:' + (+n || 0) + '" aria-hidden="true">★★★★★</span>'; }
  function date(ts) { try { return new Date(ts).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }); } catch (e) { return ""; } }
  function render(d) {
    if (!d || typeof d.count !== "number") return;
    var s = $(".rv-sum");
    if (d.count > 0) s.innerHTML = stars(d.avg) + ' <span class="rv-text"><b>' + esc(d.avg.toFixed(1)) + '</b> out of 5 · ' + d.count + (d.count === 1 ? " rating" : " ratings") + '</span>';
    else s.innerHTML = '<span class="rv-text">No ratings yet. Be the first to review ' + esc(name) + '.</span>';
    var L = $(".rv-list"), R = d.reviews || [];
    L.innerHTML = R.map(function (r) {
      return '<li class="rv-item">' + stars(r.stars) + '<span class="sr">' + r.stars + ' out of 5 stars</span> <b class="rv-who">' + esc(r.name || "Anonymous") + '</b> <time class="muted" datetime="' + esc(new Date(r.ts).toISOString()) + '">' + esc(date(r.ts)) + '</time><p>' + esc(r.text) + '</p></li>';
    }).join("");
    L.hidden = !R.length;
  }
  fetch(W + "/reviews?tool=" + encodeURIComponent(tool)).then(function (r) { return r.ok ? r.json() : null; }).then(render).catch(function () {});

  var f = $(".rv-form"); if (!f) return;
  var msg = $(".rv-msg"), btn = f.querySelector("button[type=submit]"), ta = f.querySelector("textarea"), cnt = $(".rv-cnt");
  var prev = mine()[tool];
  if (prev) { var p = f.querySelector('input[name="rv-stars"][value="' + prev + '"]'); if (p) p.checked = true; msg.textContent = "You rated " + name + " " + prev + " out of 5. You can change your rating."; }
  if (ta && cnt) ta.addEventListener("input", function () { cnt.textContent = ta.value.trim().length + " / 600"; });
  f.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var s = f.querySelector('input[name="rv-stars"]:checked');
    if (!s) { msg.textContent = "Please pick 1 to 5 stars."; f.querySelector('input[name="rv-stars"]').focus(); return; }
    var text = (ta.value || "").trim();
    if (text && (text.length < 20 || text.length > 600)) { msg.textContent = "Reviews need 20 to 600 characters, or leave the box empty to just rate."; ta.focus(); return; }
    btn.disabled = true; msg.textContent = "Sending…";
    fetch(W + "/review", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ tool: tool, stars: +s.value, text: text, name: (f.querySelector('input[name="rv-name"]').value || "").trim(), vid: vid(), website: f.querySelector('input[name="website"]').value }) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (x) {
        btn.disabled = false;
        if (!x.ok || !x.j.ok) { msg.textContent = (x.j && x.j.error) || "Couldn't send right now. Please try again later."; return; }
        var m = mine(); m[tool] = +s.value; store("as-rated", JSON.stringify(m));
        msg.textContent = x.j.pending ? "Thanks! Your rating counts now. Your review will appear after a quick check." : "Thanks! Your rating counts now.";
        if (x.j.pending) { ta.value = ""; if (cnt) cnt.textContent = "0 / 600"; }
        fetch(W + "/reviews?tool=" + encodeURIComponent(tool) + "&t=" + Date.now()).then(function (r) { return r.ok ? r.json() : null; }).then(render).catch(function () {});
        try { window.asTrack && window.asTrack("button_click", "review_submit"); } catch (e) {}
      })
      .catch(function () { btn.disabled = false; msg.textContent = "Couldn't send right now. Please try again later."; });
  });
})();
