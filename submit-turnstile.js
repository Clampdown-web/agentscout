/* Submit-form Turnstile. api.js is in the page head (explicit render, onload=asTsLoad).
   This file installs asTsLoad as soon as it runs, and honors a head stub that set
   asTsLoaded if api.js finished first. Siteverify stays on the worker.
   This file never calls challenges.cloudflare.com/siteverify. */
(function (root) {
  var SITEKEY = "0x4AAAAAAFfaxf14aQF-sky1";
  var ACTION = "submit";
  var AUTO_RESETS = 2;
  var AUTO_MS = 8000;
  var SCRIPT = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=asTsLoad";
  /* These codes are not visitor-retryable (bad sitekey, wrong domain, clock). 600* and 300* are. */
  var NON_RETRY = {
    "110100": 1, "110110": 1, "110200": 1, "200100": 1,
    "400020": 1, "400021": 1, "400070": 1
  };
  var started = false;
  var widgetId = null;
  var attempts = 0;
  var freshUsed = 0;
  var apiReady = false;
  var lastCode = "";
  var timer = 0;

  function codeOf(code) {
    return code == null ? "" : String(code);
  }

  function retryable(code) {
    var n = codeOf(code);
    if (!n || NON_RETRY[n]) return false;
    if (n.slice(0, 3) === "600" || n.slice(0, 3) === "300") return true;
    return n === "110600" || n === "110620" || n === "200500";
  }

  function shouldAutoReset(code, attemptCount) {
    return retryable(code) && attemptCount < AUTO_RESETS;
  }

  function widgetErrorText(code, auto) {
    var n = codeOf(code);
    var tail = auto
      ? " Trying again automatically. Nothing was sent."
      : " Press Try the check again. Nothing was sent. You can also use the email link below the form.";
    return "The anti-bot check did not finish" + (n ? " (code " + n + ")" : "") + ". It is still required before this form can send." + tail;
  }

  function expiredText() {
    return "The check expired after 5 minutes. A new one is starting. Wait until it finishes, then submit.";
  }

  function timeoutText() {
    return "The check timed out. A new one is starting. If it asks you to tick the box, keep this section on screen.";
  }

  function missingTokenText() {
    return "Please complete the quick check above, then press Submit.";
  }

  function submitFailureText(message) {
    var msg = message && message !== "Failed to fetch" ? String(message) : "We could not send it right now.";
    if (!/complete the check again/i.test(msg)) msg += " Complete the check again, then press Submit.";
    return msg;
  }

  function tokenUsable(token, expired) {
    return typeof token === "string" && token.length > 0 && token.length <= 2048 && expired !== true;
  }

  /* null status means fetch rejected (no HTTP response). Any status means the body arrived,
     so the single-use token must not be sent to another host. */
  function nextEndpoint(httpStatus, index, count) {
    if (httpStatus == null && index + 1 < count) return index + 1;
    return -1;
  }

  function is600(code) {
    return codeOf(code).slice(0, 3) === "600";
  }

  /* freshCount is how many remove()+render() recoveries already ran.
     Two reset() attempts come first. One fresh render follows only for 600* codes. */
  function planWidgetError(code, attemptCount, freshCount) {
    var used = freshCount == null ? 0 : freshCount;
    var auto = shouldAutoReset(code, attemptCount);
    var fresh = !auto && is600(code) && used < 1;
    return { auto: auto, fresh: fresh, text: widgetErrorText(code, auto || fresh), suppressBuiltinRetry: true };
  }

  function $(id) {
    return document.getElementById(id);
  }

  function setStatus(text) {
    var er = $("sfts");
    if (!er) return;
    er.textContent = text || "";
    if (text) er.dataset.tserr = "1";
    else delete er.dataset.tserr;
  }

  function showRetry(on) {
    var wrap = $("sfts-retry-wrap");
    if (wrap) wrap.hidden = !on;
  }

  function clearTimer() {
    if (timer) {
      clearTimeout(timer);
      timer = 0;
    }
  }

  function barBlocks(node) {
    if (!node || !root.getComputedStyle) return false;
    var cs = root.getComputedStyle(node);
    if (cs.visibility === "hidden" || cs.display === "none" || cs.opacity === "0") return false;
    var rect = node.getBoundingClientRect();
    if (rect.width < 2 || rect.height < 2) return false;
    if (node.classList && node.classList.contains("scrollbtns")) {
      var shown = node.querySelector(".scrollbtn.show");
      if (!shown) return false;
      var sc = root.getComputedStyle(shown);
      if (sc.visibility === "hidden" || sc.display === "none" || sc.opacity === "0") return false;
    }
    return true;
  }

  /* Scroll the widget above a fixed consent bar or visible scroll buttons only when they overlap it.
     Off-screen widgets are left alone so the page does not jump while someone is still reading. */
  function clearOfFixedBars() {
    var el = $("sf-turnstile");
    if (!el) return;
    var rect = el.getBoundingClientRect();
    var cut = null;
    var bars = document.querySelectorAll(".as-bar,.scrollbtns");
    for (var i = 0; i < bars.length; i++) {
      if (!barBlocks(bars[i])) continue;
      var br = bars[i].getBoundingClientRect();
      var ox = Math.min(rect.right, br.right) - Math.max(rect.left, br.left);
      var oy = Math.min(rect.bottom, br.bottom) - Math.max(rect.top, br.top);
      if (ox > 8 && oy > 8) cut = cut == null ? br.top : Math.min(cut, br.top);
    }
    if (cut != null && rect.bottom > cut - 12) root.scrollBy(0, rect.bottom - cut + 24);
  }

  function reveal() {
    try { clearOfFixedBars(); } catch (e) {}
    var el = $("sfts") || $("sf-turnstile");
    if (!el || !el.scrollIntoView) return;
    try { el.scrollIntoView({ block: "center", behavior: "smooth" }); }
    catch (e) { try { el.scrollIntoView(); } catch (e2) {} }
  }

  function resetWidget(message) {
    clearTimer();
    showRetry(false);
    var api = root.turnstile;
    if (api && widgetId != null && typeof api.reset === "function") {
      try { api.reset(widgetId); } catch (e) {}
    }
    setStatus(message || "Starting the check again.");
  }

  /* A stuck 600* widget often ignores reset(). Drop it and render a new one.
     Still no token, so the form cannot send. */
  function freshRender(message) {
    clearTimer();
    showRetry(false);
    var api = root.turnstile;
    var old = widgetId;
    widgetId = null;
    if (api && old != null && typeof api.remove === "function") {
      try { api.remove(old); } catch (e) {}
    }
    renderWidget();
    if (widgetId == null) {
      setStatus(widgetErrorText(lastCode, false));
      showRetry(true);
      try { reveal(); } catch (e) {}
      return;
    }
    setStatus(message || "Starting the check again.");
  }

  /* api.js retries on its own unless this returns true AND the widget retry mode is not auto.
     render() sets retry to never, so this return stops that scheduler, including the immediate
     retry it otherwise uses for challenge-crash codes. */
  function onError(code) {
    clearTimer();
    lastCode = codeOf(code);
    var plan = planWidgetError(code, attempts, freshUsed);
    setStatus(plan.text);
    if (plan.auto) {
      attempts += 1;
      showRetry(false);
      timer = setTimeout(function () {
        resetWidget("Starting the check again.");
      }, AUTO_MS);
    } else if (plan.fresh) {
      freshUsed += 1;
      showRetry(false);
      timer = setTimeout(function () {
        freshRender("Starting the check again.");
      }, 0);
    } else {
      showRetry(true);
      try { reveal(); } catch (e) {}
    }
    return true;
  }

  function onSuccess() {
    attempts = 0;
    freshUsed = 0;
    clearTimer();
    showRetry(false);
    setStatus("");
  }

  function onExpired() {
    /* refresh-expired auto already requests a new token. Resetting here would start a second one. */
    setStatus(expiredText());
    showRetry(false);
  }

  function onTimeout() {
    setStatus(timeoutText());
    try { clearOfFixedBars(); } catch (e) {}
  }

  function onBeforeInteractive() {
    try { clearOfFixedBars(); } catch (e) {}
  }

  function onManual() {
    attempts = 0;
    freshUsed = 0;
    resetWidget("Starting the check again. Wait until it finishes, then press Submit.");
  }

  /* Normal and flexible widgets are 300px wide. A narrower box (or a box that
     has not been laid out yet) makes Turnstile return 400020, which is not a
     visitor-retryable code, so the same render would fail again. Compact is 150px. */
  function widgetSize(width) {
    var n = Number(width);
    if (!isFinite(n) || n < 300) return "compact";
    return "flexible";
  }

  function themeNow() {
    var theme = document.documentElement && document.documentElement.getAttribute("data-theme");
    return theme === "dark" || theme === "light" ? theme : "auto";
  }

  function renderWidget() {
    if (widgetId != null) return;
    var el = $("sf-turnstile");
    var api = root.turnstile;
    if (!el || !api || typeof api.render !== "function") return;
    var width = 0;
    try { width = el.getBoundingClientRect().width; } catch (e) {}
    widgetId = api.render(el, {
      sitekey: el.getAttribute("data-sitekey") || SITEKEY,
      action: ACTION,
      size: widgetSize(width),
      theme: themeNow(),
      retry: "never",
      "refresh-expired": "auto",
      "refresh-timeout": "auto",
      callback: onSuccess,
      "error-callback": onError,
      "expired-callback": onExpired,
      "timeout-callback": onTimeout,
      "before-interactive-callback": onBeforeInteractive
    });
    root.setTimeout(function () { try { clearOfFixedBars(); } catch (e) {} }, 0);
  }

  function onLoad() {
    apiReady = true;
    if (started) renderWidget();
  }

  /* Run at parse time, not from start(). api.js may call asTsLoad before or after
     this file, and before DOMContentLoaded calls start(). */
  function bindApiLoad() {
    root.asTsLoad = onLoad;
    if (root.asTsLoaded || (root.turnstile && typeof root.turnstile.render === "function")) apiReady = true;
  }

  function start() {
    if (started || !root.document) return;
    started = true;
    root.asTsLoad = onLoad;
    root.asTsErr = onError;
    root.asTsOk = onSuccess;
    root.asTsExpired = onExpired;
    root.asTsTimeout = onTimeout;
    root.asTsBeforeInteractive = onBeforeInteractive;
    var btn = $("sfts-retry");
    if (btn && !btn.dataset.bound) {
      btn.dataset.bound = "1";
      btn.addEventListener("click", onManual);
    }
    if (root.addEventListener && !root.asTsScroll) {
      root.asTsScroll = 1;
      root.addEventListener("scroll", function () {
        try { clearOfFixedBars(); } catch (e) {}
      }, { passive: true });
    }
    if (!apiReady && (root.asTsLoaded || (root.turnstile && typeof root.turnstile.render === "function"))) apiReady = true;
    if (apiReady) renderWidget();
  }

  function readToken() {
    var api = root.turnstile;
    if (api && widgetId != null) {
      try {
        if (typeof api.isExpired === "function" && api.isExpired(widgetId)) return "";
        if (typeof api.getResponse === "function") {
          var live = api.getResponse(widgetId);
          return tokenUsable(live, false) ? live : "";
        }
      } catch (e) {}
      /* A live widget owns the token. Do not fall through to a hidden input reset() may not have cleared. */
      return "";
    }
    var hidden = document.querySelector('#sf input[name="cf-turnstile-response"]');
    return tokenUsable(hidden && hidden.value, false) ? hidden.value : "";
  }

  function postJson(urls, bodyStr) {
    function go(i) {
      return fetch(urls[i], {
        method: "POST",
        headers: { "Content-Type": "text/plain;charset=UTF-8" },
        body: bodyStr
      }).then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (!r.ok || !j.ok) throw new Error((j && j.error) || "Something went wrong.");
          return j;
        });
      }, function () {
        var next = nextEndpoint(null, i, urls.length);
        if (next >= 0) return go(next);
        throw new Error("We could not send it right now.");
      });
    }
    return go(0);
  }

  function invalidate() {
    attempts = 0;
    freshUsed = 0;
    resetWidget("Complete the check again, then press Submit.");
  }

  bindApiLoad();

  root.AgentScoutTurnstile = {
    SITEKEY: SITEKEY,
    ACTION: ACTION,
    SCRIPT: SCRIPT,
    AUTO_MS: AUTO_MS,
    AUTO_RESETS: AUTO_RESETS,
    retryable: retryable,
    shouldAutoReset: shouldAutoReset,
    widgetErrorText: widgetErrorText,
    expiredText: expiredText,
    timeoutText: timeoutText,
    missingTokenText: missingTokenText,
    submitFailureText: submitFailureText,
    tokenUsable: tokenUsable,
    nextEndpoint: nextEndpoint,
    planWidgetError: planWidgetError,
    widgetSize: widgetSize,
    start: start,
    readToken: readToken,
    postJson: postJson,
    invalidate: invalidate,
    reveal: reveal,
    clearOfFixedBars: clearOfFixedBars
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
