"""Google Analytics 4 tag for every page (added 2026-10-19, owner-approved). Property 559504931, stream 16160444227.
apply(html) inserts/refreshes one marked <script> block before </head> and adds GA hosts to the page CSP; idempotent.
Called from build_tasks.sitewide() and from build_extras' atexit hook, so every generator run keeps the tag.
Behaviour (all in the inline snippet below):
- Skipped entirely (gtag.js never requested) when the owner opt-out flag is set (?notrack=1 -> localStorage as_notrack=1,
  the same flag track.js uses; ?notrack=0 clears it) or the browser is automated/headless (same test as track.js).
- Consent Mode v2 defaults: EEA + UK + CH -> analytics/ad storage, ad_user_data, ad_personalization all denied;
  elsewhere analytics_storage granted, ad signals denied. allow_google_signals and allow_ad_personalization_signals false.
- Follows the site's own consent manager (consent.js / window.ASConsent): gtag.js loads only once analytics is allowed
  (strict regions: after "Accept"; elsewhere: by default, unless the visitor opted out). Turning analytics off later
  sets consent denied + ga-disable. Pages without consent.js load it with the defaults above.
- gtag.js is injected async after the window load event, so it never blocks rendering or delays onload.
Skipped files: meta-refresh redirect stubs, preview/ drafts, og.html, outreach-tracker.html, app/ and node_modules/."""
import re, glob, os
ID = "G-TGDXK5F13D"
START, END = "<!-- ga4 -->", "<!-- /ga4 -->"
_EEA = ["AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","GR","HU","IE","IT","LV","LT","LU","MT","NL","PL","PT","RO",
        "SK","SI","ES","SE","IS","LI","NO","GB","CH"]
SNIPPET = (START + '<script>(function(){var ID="' + ID + '",off=false;'
  'try{var nt=new URLSearchParams(location.search).get("notrack");if(nt==="1")localStorage.setItem("as_notrack","1");else if(nt==="0")localStorage.removeItem("as_notrack");off=localStorage.getItem("as_notrack")==="1"}catch(e){}'
  'try{if(navigator.webdriver||/HeadlessChrome|Headless|PhantomJS|Playwright|Puppeteer|Selenium|Lighthouse|bot\\b|crawler|spider/i.test(navigator.userAgent||""))off=true}catch(e){}'
  'if(off){window["ga-disable-"+ID]=true;return}'
  'window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}window.gtag=gtag;'
  'var D={ad_storage:"denied",ad_user_data:"denied",ad_personalization:"denied"};'
  'gtag("consent","default",Object.assign({analytics_storage:"denied",region:' + str(_EEA).replace("'", '"').replace(" ", "") + '},D));'
  'gtag("consent","default",Object.assign({analytics_storage:"granted"},D));'
  'gtag("set","ads_data_redaction",true);'
  'var go=false;function start(){if(go)return;go=true;gtag("js",new Date());gtag("config",ID,{allow_google_signals:false,allow_ad_personalization_signals:false});'
  'function inj(){var s=document.createElement("script");s.async=true;s.src="https://www.googletagmanager.com/gtag/js?id="+ID;document.head.appendChild(s)}'
  'document.readyState==="complete"?inj():addEventListener("load",inj)}'
  'function c(x){if(!x.ready||(x.strict&&!x.decided))return;var a=!!x.analytics;window["ga-disable-"+ID]=!a;'
  'gtag("consent","update",{analytics_storage:a?"granted":"denied"});if(a)start()}'
  'function hook(){if(window.ASConsent)ASConsent.on(c);else start()}'
  'document.readyState==="loading"?document.addEventListener("DOMContentLoaded",hook):hook()})();</script>' + END)
_BLOCK = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
_CSP = re.compile(r'(<meta http-equiv="Content-Security-Policy" content=")([^"]*)(")')
GTM = "https://www.googletagmanager.com"
GA_CONNECT = "https://*.google-analytics.com https://*.analytics.google.com https://www.googletagmanager.com"
def _csp(m):
    c = m.group(2)
    if GTM not in c.split("connect-src")[0]:
        c = re.sub(r"script-src ([^;]*)", lambda k: "script-src " + k.group(1) + " " + GTM, c, count=1)
    if "google-analytics.com" not in c:
        c = re.sub(r"connect-src ([^;]*)", lambda k: "connect-src " + k.group(1) + " " + GA_CONNECT, c, count=1)
    return m.group(1) + c + m.group(3)
def skip(path, s):
    p = path.replace("\\", "/").lstrip("./")
    if os.path.basename(p) in {"og.html", "outreach-tracker.html", "stats.js.html"}: return True
    if p.startswith(("app/", "node_modules/", "preview/", ".git/")): return True
    if re.search(r'<meta http-equiv="refresh"', s, re.I): return True   # redirect stubs: no analytics (same as track.js)
    return "</head>" not in s
def apply(s, path="x.html"):
    if skip(path, s): return s
    s = _CSP.sub(_csp, s, count=1)
    if _BLOCK.search(s): return _BLOCK.sub(lambda m: SNIPPET, s, count=1)
    return s.replace("</head>", SNIPPET + "</head>", 1)
def apply_all(root="."):
    n = 0
    for f in glob.glob(os.path.join(root, "**/*.html"), recursive=True):
        rel = os.path.relpath(f, root)
        if rel.startswith(("app/", "node_modules/", "preview/", ".git/")): continue
        try: s = open(f, encoding="utf-8").read()
        except Exception: continue
        o = s; s = apply(s, rel)
        if s != o: open(f, "w", encoding="utf-8").write(s); n += 1
    return n
if __name__ == "__main__":
    print("ga4: updated", apply_all(), "pages")
