/* AgentScout ratings & reviews (tool pages). Static summary is rendered at build time; this refreshes it from the
   Worker and handles the form. Fails silently if the API is down. No cookies; a random visitor ID in localStorage
   ("as-vid") enforces one rating per tool per visitor. */
(function () {
  var W = "https://agentscout-image.agentscouthq.workers.dev";
  // "Rate this tool" (Oct 21 2026): jump to the form and put focus on the first star
  function rateJump(ev) { var fm = document.getElementById("rv-form"); if (!fm) return; try { loadTS() } catch (e) {} if (ev) ev.preventDefault()
    fm.scrollIntoView({ behavior: "smooth", block: "center" }); var r = fm.querySelector('input[name="rv-stars"]'); if (r) setTimeout(function () { try { r.focus({ preventScroll: true }) } catch (e) { r.focus() } }, 350) }
  document.querySelectorAll("a.rv-rate").forEach(function (a) { a.addEventListener("click", rateJump) })
  if (location.hash === "#rate" || location.hash === "#rv-form") setTimeout(rateJump, 300)
  var sec = document.getElementById("reviews"); if (!sec || !window.fetch) return;
  // Turnstile (Oct 21 2026): shown only once a site key is set here; the Worker enforces it when REVIEW_TURNSTILE="true"
  var TS_SITEKEY = "0x4AAAAAAFfaxf14aQF-sky1"
  // Lazy (Oct 21 2026): the widget box is placed now, but api.js from challenges.cloudflare.com loads only when someone interacts with the form or scrolls near it, so pages go quiet on load
  var tsLoaded = false
  function loadTS() { if (tsLoaded || !TS_SITEKEY) return; tsLoaded = true; var sc = document.createElement("script"); window.asTsReady = function () { var el = sec.querySelector(".cf-turnstile"); if (el && window.turnstile && !el.getAttribute("data-rendered")) { el.setAttribute("data-rendered", "1"); try { turnstile.render(el, { sitekey: TS_SITEKEY }) } catch (e) {} } }; sc.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=asTsReady"; sc.async = true; document.head.appendChild(sc) }
  if (TS_SITEKEY) { var fm0 = sec.querySelector(".rv-form button[type=submit]"); if (fm0) { var td = document.createElement("div"); td.className = "cf-turnstile"; td.setAttribute("data-sitekey", TS_SITEKEY); td.style.margin = "12px 0 0"; td.style.minHeight = "65px"; fm0.parentNode.parentNode.insertBefore(td, fm0.parentNode)
    var fz = sec.querySelector(".rv-form"); if (fz) ["pointerdown", "focusin", "input", "change", "touchstart"].forEach(function (e) { fz.addEventListener(e, loadTS, { once: true, passive: true }) })
    if ("IntersectionObserver" in window && fz) { var io = new IntersectionObserver(function (es) { if (es.some(function (x) { return x.isIntersecting })) { io.disconnect(); loadTS() } }, { rootMargin: "300px 0px" }); io.observe(fz) } } }
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
    var T = document.querySelector(".rv-top .rv-topsum");  /* rating line under the tool name */
    if (T) {
      var h = d.count > 0 ? '<a class="rv-topsum" href="#reviews" style="display:inline-flex;align-items:center;gap:6px;color:inherit;text-decoration:none"><span class="rv-stars" style="--r:' + (+d.avg || 0) + ';font-size:15px" aria-hidden="true">★★★★★</span><span><b>' + esc(d.avg.toFixed(1)) + '</b> <span class="muted">(' + d.count + (d.count === 1 ? " rating" : " ratings") + ')</span></span><span class="sr">Rated ' + esc(d.avg.toFixed(1)) + ' out of 5 from ' + d.count + (d.count === 1 ? " rating" : " ratings") + '</span></a>' : '<span class="muted rv-topsum">No ratings yet</span>';
      T.outerHTML = h;
    }
    var L = $(".rv-list"), R = d.reviews || [];
    L.innerHTML = R.map(function (r) {
      return '<li class="rv-item">' + stars(r.stars) + '<span class="sr">' + r.stars + ' out of 5 stars</span> <b class="rv-who">' + esc(r.name || "Anonymous") + '</b> <time class="muted" datetime="' + esc(new Date(r.ts).toISOString()) + '">' + esc(date(r.ts)) + '</time><p>' + esc(r.text) + '</p></li>';
    }).join("");
    L.hidden = !R.length;
  }
  fetch(W + "/reviews?tool=" + encodeURIComponent(tool)).then(function (r) { return r.ok ? r.json() : null; }).then(render).catch(function () {});

  var f = $(".rv-form"); if (!f) return;
  var msg = $(".rv-msg"), btn = f.querySelector("button[type=submit]"), ta = f.querySelector("textarea"), cnt = $(".rv-cnt");
  var MIN = 10, MAX = 600;
  // Oct 21 2026: messages sit right under Submit; errors are red and scrolled into view so they are seen on phones
  function show(t, kind) { msg.textContent = t; msg.className = "rv-msg" + (kind ? " rv-" + kind : ""); msg.style.cssText = kind === "err" ? "color:#c0392b;font-weight:600;margin:8px 0 0" : kind === "ok" ? "color:#1e8449;font-weight:600;margin:8px 0 0;padding:8px 10px;border:1px solid #1e8449;border-radius:8px" : "margin:8px 0 0"; if (kind) { try { msg.scrollIntoView({ behavior: "smooth", block: "center" }) } catch (e) { msg.scrollIntoView() } } }
  var hint = null; if (ta) { hint = document.createElement("p"); hint.className = "rv-hint muted"; hint.style.cssText = "margin:4px 0 0;font-size:13px"; hint.textContent = "Add at least 10 characters, or leave it blank."; (cnt || ta).insertAdjacentElement("afterend", hint) }
  var prev = mine()[tool];
  if (prev) { var p = f.querySelector('input[name="rv-stars"][value="' + prev + '"]'); if (p) p.checked = true; msg.textContent = "You rated " + name + " " + prev + " out of 5. You can change your rating."; }
  if (ta && cnt) ta.addEventListener("input", function () { cnt.textContent = ta.value.trim().length + " / 600"; var n = ta.value.trim().length; if (hint) hint.style.color = n && n < MIN ? "#c0392b" : ""; });
  f.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var s = f.querySelector('input[name="rv-stars"]:checked');
    if (!s) { show("Please pick 1 to 5 stars.", "err"); return; }
    var text = (ta.value || "").trim();
    if (text && (text.length < MIN || text.length > MAX)) { show(text.length < MIN ? "Your review is " + text.length + " characters. Add at least 10 characters, or leave it blank to just rate." : "Reviews can be up to 600 characters.", "err"); return; }
    if (TS_SITEKEY && !((f.querySelector('input[name="cf-turnstile-response"]') || {}).value)) { loadTS(); show("Please complete the quick check above, then press Submit.", "err"); return; }
    btn.disabled = true; show("Sending…");
    var ac = window.AbortController ? new AbortController() : null, tmo = setTimeout(function () { if (ac) ac.abort() }, 15000);
    fetch(W + "/review", { signal: ac ? ac.signal : undefined, method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ tool: tool, stars: +s.value, text: text, name: (f.querySelector('input[name="rv-name"]').value || "").trim(), vid: vid(), website: f.querySelector('input[name="website"]').value, turnstileToken: (f.querySelector('input[name="cf-turnstile-response"]') || {}).value || "" }) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (x) {
        clearTimeout(tmo); btn.disabled = false; try { window.turnstile && turnstile.reset() } catch (e) {}
        if (!x.ok || !x.j.ok) { show((x.j && x.j.error) || "Couldn't send right now. Please try again later.", "err"); return; }
        var m = mine(); m[tool] = +s.value; store("as-rated", JSON.stringify(m));
        show(x.j.pending ? "✓ Thanks! Your rating was saved. Your review will appear after a quick check." : "✓ Thanks! Your rating was saved.", "ok");
        if (x.j.pending) { ta.value = ""; if (cnt) cnt.textContent = "0 / 600"; }
        fetch(W + "/reviews?tool=" + encodeURIComponent(tool) + "&t=" + Date.now()).then(function (r) { return r.ok ? r.json() : null; }).then(render).catch(function () {});
        try { window.asTrack && window.asTrack("button_click", "review_submit"); } catch (e) {}
      })
      .catch(function (e) { clearTimeout(tmo); btn.disabled = false; try { window.turnstile && turnstile.reset() } catch (x) {} show(e && e.name === "AbortError" ? "This is taking too long. Please check your connection and try again." : "Couldn't send right now. Please try again later.", "err"); });
  });
})();
