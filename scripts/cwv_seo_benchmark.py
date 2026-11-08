"""Unthrottled lab timings for the publish gate.

The collector waits for the load event, then reads LCP, CLS, and TTFB.
It does not wait for networkidle. Turnstile may keep a connection open
after load; that does not omit the page. Thresholds stay LCP 2500, CLS 0.1,
and TTFB 800. This is not Lighthouse and it is not field data.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from urllib.parse import urlparse

THRESHOLDS = {"lcp_ms": 2500, "cls": 0.1, "ttfb_ms": 800}
WAIT_UNTIL = "load"
METHOD = "cwv_seo_benchmark.measure_url"
# The six URLs the fixture already named, plus submit.html, which the old
# not_measured list was dropping.
REQUIRED_PATHS = (
    "/",
    "/bot-store/",
    "/videos/",
    "/bot-templates/",
    "/mcp/",
    "/tools/noteboxd.html",
    "/submit.html",
)

_NODE = r"""
const url = process.env.MEASURE_URL;
const {spawn} = require('child_process');
const port = 9366 + Math.floor(Math.random()*200);
const chrome = spawn(process.env.CHROME_BIN || '/usr/bin/google-chrome', [
  '--headless=new','--disable-gpu','--no-sandbox','--disable-dev-shm-usage',
  '--remote-debugging-port='+port,'about:blank'
], {stdio:'ignore'});
const sleep = (ms) => new Promise((r)=>setTimeout(r, ms));
function die(err){ try{chrome.kill('SIGKILL')}catch(e){} console.error(err); process.exit(1); }
(async () => {
  let version;
  for (let i=0;i<40;i++){
    try { version = await (await fetch('http://127.0.0.1:'+port+'/json/version')).json(); break; }
    catch(e){ await sleep(100); }
  }
  if (!version) die('chrome debug port did not open');
  const page = (await (await fetch('http://127.0.0.1:'+port+'/json')).json()).find((t)=>t.type==='page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id=0; const pending=new Map();
  function send(method, params={}){
    const msgId=++id;
    ws.send(JSON.stringify({id:msgId, method, params}));
    return new Promise((res,rej)=>{ pending.set(msgId,{res,rej}); setTimeout(()=>rej(new Error(method)), 20000); });
  }
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const p = pending.get(msg.id); pending.delete(msg.id);
      msg.error ? p.rej(new Error(JSON.stringify(msg.error))) : p.res(msg.result);
    }
  };
  await new Promise((res,rej)=>{ ws.onopen=res; ws.onerror=rej; });
  await send('Page.enable');
  await send('Network.enable');
  await send('Network.setCacheDisabled', {cacheDisabled:true});
  await send('Page.addScriptToEvaluateOnNewDocument', {source:
    'window.__lcp=null;window.__cls=0;'+
    'try{new PerformanceObserver(function(list){var es=list.getEntries();var last=es[es.length-1];'+
    'window.__lcp=last.startTime;}).observe({type:"largest-contentful-paint",buffered:true});}catch(e){}'+
    'try{new PerformanceObserver(function(list){list.getEntries().forEach(function(e){if(!e.hadRecentInput)window.__cls+=e.value});'+
    '}).observe({type:"layout-shift",buffered:true});}catch(e){}'
  });
  let loaded=false;
  const waitLoad = new Promise((res)=>{
    const prev=ws.onmessage;
    ws.onmessage=(ev)=>{ prev(ev); const msg=JSON.parse(ev.data); if(msg.method==='Page.loadEventFired'){loaded=true; res();} };
    setTimeout(res, 15000);
  });
  await send('Page.navigate', {url});
  await waitLoad;
  if (!loaded) die('load event did not fire');
  await sleep(400);
  const state = await send('Runtime.evaluate', {expression:
    '({lcp_ms: window.__lcp, cls: window.__cls||0, ttfb_ms: (performance.getEntriesByType("navigation")[0]||{}).responseStart||0})',
    returnByValue:true});
  const v = state.result.value;
  process.stdout.write(JSON.stringify({lcp_ms:v.lcp_ms, cls:v.cls, ttfb_ms:v.ttfb_ms}));
  chrome.kill('SIGKILL');
  process.exit(0);
})().catch(die);
"""


def completion_wait(has_turnstile: bool = False) -> str:
    """Load, whether or not the page keeps a challenge connection open."""
    return WAIT_UNTIL


def grade_page(lcp_ms: float, cls: float, ttfb_ms: float) -> str:
    if lcp_ms > THRESHOLDS["lcp_ms"] or cls > THRESHOLDS["cls"] or ttfb_ms > THRESHOLDS["ttfb_ms"]:
        return "FAIL"
    return "PASS"


def page_path(url: str) -> str:
    path = urlparse(url).path or "/"
    return path or "/"


def measure_url(url: str, navigate=None) -> dict:
    """One unthrottled reading. navigate(url, wait) -> {lcp_ms, cls, ttfb_ms}."""
    wait = completion_wait(url.rstrip("/").endswith("submit.html"))
    if wait != WAIT_UNTIL:
        raise RuntimeError(f"collector wait must be {WAIT_UNTIL}")
    reader = navigate or _chrome_navigate
    raw = reader(url, wait)
    if not isinstance(raw, dict):
        raise RuntimeError("collector returned no reading")
    missing = [key for key in ("lcp_ms", "cls", "ttfb_ms") if raw.get(key) is None]
    if missing:
        raise RuntimeError("collector missing " + ", ".join(missing))
    lcp, cls, ttfb = float(raw["lcp_ms"]), float(raw["cls"]), float(raw["ttfb_ms"])
    return {
        "url": url,
        "lcp_ms": lcp,
        "cls": cls,
        "ttfb_ms": ttfb,
        "grade": grade_page(lcp, cls, ttfb),
        "wait": wait,
        "throttle": "none",
        "field_cwv": False,
    }


def _chrome_navigate(url: str, wait: str) -> dict:
    if wait != "load":
        raise RuntimeError("chrome collector only waits for load")
    if not shutil.which("node") or not (shutil.which("google-chrome") or shutil.which("google-chrome-stable")):
        raise RuntimeError("chrome collector is not available")
    env = os.environ.copy()
    env["MEASURE_URL"] = url
    proc = subprocess.run(
        ["node", "-e", _NODE],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "chrome collector failed")
    return json.loads(proc.stdout)
