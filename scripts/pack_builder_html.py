#!/usr/bin/env python3
"""macOS-window pack builder HTML shared by /bot-store/ and /bot-templates/."""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_pack_catalog import ICONS, PACK_TIERS, STRIPE, public_cards  # noqa: E402

CSS = """
<style id="ap-css">
.ap-window{margin:8px 0 28px;border:1px solid rgba(255,255,255,.16);border-radius:22px;background:#12141a;box-shadow:0 24px 60px rgba(0,0,0,.45);overflow:hidden;min-width:0;max-width:100%;box-sizing:border-box}
.ap-chrome{display:flex;align-items:flex-start;gap:12px;padding:16px 16px 12px;border-bottom:1px solid rgba(255,255,255,.08);min-width:0}
.ap-dots{display:flex;gap:6px;padding-top:6px;flex:0 0 auto}
.ap-dots i{width:11px;height:11px;border-radius:50%;display:block}
.ap-dots .r{background:#ff5f57}.ap-dots .y{background:#febc2e}.ap-dots .g{background:#28c840}
.ap-chrome-copy{min-width:0;flex:1}
.ap-chrome h2{margin:0;font-size:clamp(18px,2.4vw,22px);color:#fff;letter-spacing:-.02em}
.ap-chrome p{margin:4px 0 0;color:#a1a1aa;font-size:13px;line-height:1.45}
.ap-chrome-side{display:flex;align-items:center;gap:8px;flex:0 0 auto}
.ap-count{border:1px solid rgba(255,255,255,.12);background:#1c1f27;color:#e4e4e7;border-radius:999px;padding:6px 10px;font-size:12px;font-weight:700;white-space:nowrap}
.ap-cart{width:36px;height:36px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:#1c1f27;color:#fff;display:inline-flex;align-items:center;justify-content:center;cursor:pointer}
.ap-tiers{display:flex;flex-wrap:wrap;gap:8px;padding:12px 16px 4px;min-width:0;align-items:center}
.ap-tier-pill{min-height:34px;padding:5px 11px;border-radius:999px;border:1px solid rgba(52,211,153,.28);background:rgba(16,185,129,.1);color:#d1fae5;font-size:12px;font-weight:700;cursor:pointer;max-width:100%;box-sizing:border-box}
.ap-tier-pill[aria-pressed="true"]{background:#10b981;color:#052e16;border-color:#10b981}
.ap-filters{display:flex;flex-wrap:wrap;gap:8px;padding:8px 16px 12px;min-width:0}
.ap-pill{min-height:36px;padding:6px 12px;border-radius:999px;border:1px solid rgba(255,255,255,.12);background:transparent;color:#d4d4d8;font-size:12.5px;font-weight:700;cursor:pointer;max-width:100%;box-sizing:border-box}
.ap-pill[aria-pressed="true"]{background:#f4f4f5;color:#18181b;border-color:#f4f4f5}
.ap-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;padding:0 14px 14px;min-width:0}
.ap-card{background:#1a1d25;border:1px solid rgba(255,255,255,.1);border-top:2px solid var(--ap,#34d399);border-radius:16px;padding:12px;min-width:0;box-sizing:border-box;display:flex;flex-direction:column;gap:7px}
.ap-card-top{display:flex;align-items:center;justify-content:space-between;gap:6px;min-width:0}
.ap-ico{width:34px;height:34px;border-radius:10px;display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;background:color-mix(in srgb,var(--ap) 18%,#111)}
.ap-ico svg{display:block}
.ap-add{border:1px solid rgba(255,255,255,.14);border-radius:999px;background:#12151c;color:#e4e4e7;font-size:11.5px;font-weight:800;cursor:pointer;padding:4px 9px;white-space:nowrap}
.ap-add[aria-pressed="true"]{background:rgba(16,185,129,.18);border-color:#34d399;color:#86efac}
.ap-dept-row{display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:11px;color:#a1a1aa;font-weight:700}
.ap-price-tag{color:#86efac;font-weight:800}
.ap-card h3{margin:0;font-size:14px;color:#fafafa;line-height:1.3;overflow-wrap:anywhere}
.ap-card h3 a{color:inherit;text-decoration:none}
.ap-by{margin:0;font-size:11.5px;font-weight:700;color:#e4e4e7;line-height:1.3}
.ap-card img.aswm{height:1.15em;width:auto;vertical-align:-.28em;filter:invert(1) hue-rotate(180deg)}
.ap-card .ap-tag{margin:0;color:#d4d4d8;font-size:12px;font-weight:600;line-height:1.35;overflow-wrap:anywhere}
.ap-card .ap-desc{margin:0;color:#a1a1aa;font-size:11.5px;line-height:1.4;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}
.ap-chips{display:flex;flex-wrap:wrap;gap:4px;margin-top:auto;padding-top:2px}
.ap-chip{font-size:10.5px;line-height:1.2;padding:3px 6px;border-radius:6px;background:#111319;border:1px solid rgba(255,255,255,.08);color:#cbd5e1;max-width:100%;overflow-wrap:anywhere}
.ap-preview{align-self:flex-start;background:transparent;border:0;color:#93c5fd;font-size:12px;font-weight:700;cursor:pointer;padding:2px 0 0;text-align:left}
.ap-foot{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;padding:12px 14px 14px;border-top:1px solid rgba(255,255,255,.08);background:#101218;min-width:0}
.ap-foot p{margin:0;color:#e4e4e7;font-size:13px;line-height:1.45;min-width:0;flex:1 1 220px;overflow-wrap:anywhere}
.ap-actions{display:flex;flex-wrap:wrap;gap:8px;min-width:0}
.ap-btn{display:inline-flex;align-items:center;justify-content:center;min-height:40px;padding:8px 12px;border-radius:10px;font-size:13px;font-weight:800;text-decoration:none;border:1px solid transparent;box-sizing:border-box;max-width:100%;cursor:pointer}
.ap-btn.pay{background:#10b981;color:#052e16}
.ap-btn.x{background:transparent;color:#e4e4e7;border-color:rgba(255,255,255,.18)}
.ap-btn.copy{background:#172033;color:#dbeafe;border-color:#1d4ed8}
.ap-btn[disabled],.ap-btn.is-off{opacity:.45;pointer-events:none}
.ap-modal{position:fixed;inset:0;z-index:80;background:rgba(0,0,0,.62);display:flex;align-items:flex-end;justify-content:center;padding:12px;box-sizing:border-box}
.ap-modal[hidden]{display:none}
.ap-sheet{width:min(640px,100%);max-height:min(86vh,760px);overflow:auto;background:#161922;color:#e4e4e7;border-radius:18px;padding:16px;box-sizing:border-box;border:1px solid rgba(255,255,255,.12)}
.ap-sheet h3{margin:0 0 6px;color:#fff}
.ap-sheet p,.ap-sheet li{font-size:13.5px;line-height:1.5}
.ap-sheet code{overflow-wrap:anywhere}
@media(max-width:1100px){.ap-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:760px){.ap-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:560px){
  .ap-grid{grid-template-columns:minmax(0,1fr)}
  .ap-chrome{flex-wrap:wrap}
  .ap-chrome-side{width:100%;justify-content:flex-end}
  .ap-btn{width:100%}
}
</style>
"""


def _e(val: str) -> str:
    return html.escape(str(val), quote=True)


def pack_section_html() -> str:
    cards = public_cards()
    payload = json.dumps({"agents": cards, "stripe": STRIPE, "tiers": PACK_TIERS}, ensure_ascii=False).replace("<", "\\u003c")
    items = []
    for card in cards:
        icon = ICONS[card["icon"]]
        brand_title = card["brandTitle"]
        chips_html = "".join(
            f'<span class="ap-chip">{_e(c)}</span>'
            for c in [card["skill"], card["script"], f'{len(card["routines"])} Routines']
        )
        items.append(
            f'<article class="ap-card" data-pack="{card["slug"]}" data-dept="{card["dept"]}" style="--ap:{card["color"]}">'
            f'<div class="ap-card-top"><span class="ap-ico" style="--ap:{card["color"]};color:{card["color"]}">'
            f'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="{icon}"/></svg>'
            f'</span><button type="button" class="ap-add" data-add="{card["slug"]}" aria-pressed="false">+ Add</button></div>'
            f'<div class="ap-dept-row"><span>{_e(card["deptLabel"])}</span><span class="ap-price-tag">${card["price"]}</span></div>'
            f'<h3><a href="/bot-store/{card["slug"]}/">{_e(brand_title)}</a></h3>'
            f'<p class="ap-by">built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="120" height="24"></p>'
            f'<p class="ap-tag">{_e(card["taglineRich"])}</p>'
            f'<p class="ap-desc">{_e(card["description"])}</p>'
            f'<div class="ap-chips">{chips_html}</div>'
            f'<button type="button" class="ap-preview" data-preview="{card["slug"]}">Preview Trained Skills &amp; Scripts</button>'
            f'</article>'
        )
    grid = "".join(items)
    tier_btns = "".join(
        f'<button type="button" class="ap-tier-pill" data-ap-tier="{t["bots"]}" aria-pressed="false">'
        f'{_e(t["short_label"])}{" · Save $" + str(t["savings"]) if t["savings"] else ""}</button>'
        for t in PACK_TIERS
    )
    return f"""{CSS}
<section id="ai-agent-packs" class="ap-window" aria-labelledby="ap-title">
  <div class="ap-chrome">
    <span class="ap-dots" aria-hidden="true"><i class="r"></i><i class="y"></i><i class="g"></i></span>
    <div class="ap-chrome-copy">
      <h2 id="ap-title">25 Pre-Trained AI Agent Packs ($35 each · Bundle 5 for $119 · 10 for $199 · 20 for $299 · All 25 for $349)</h2>
      <p>Pick the agents you want in your pack — each ships as a downloadable ZIP with a domain SKILL.md, 3 scheduled cron routines, and a zero-dependency Python CLI tool</p>
    </div>
    <div class="ap-chrome-side">
      <span class="ap-count" id="ap-count">25 agents</span>
      <button type="button" class="ap-cart" id="ap-cart" aria-label="Open pack checkout">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M6 6h15l-1.5 9h-12z"/><path d="M6 6L5 3H2"/><circle cx="9" cy="20" r="1.2"/><circle cx="18" cy="20" r="1.2"/></svg>
      </button>
    </div>
  </div>
  <div class="ap-tiers" role="toolbar" aria-label="Volume discount pack tiers">
    {tier_btns}
  </div>
  <div class="ap-filters" role="toolbar" aria-label="Filter agent packs">
    <button type="button" class="ap-pill" data-ap-filter="all" aria-pressed="true">All 25</button>
    <button type="button" class="ap-pill" data-ap-filter="sales" aria-pressed="false">Sales &amp; Outreach</button>
    <button type="button" class="ap-pill" data-ap-filter="marketing" aria-pressed="false">Marketing &amp; Content</button>
    <button type="button" class="ap-pill" data-ap-filter="ops" aria-pressed="false">Operations &amp; Admin</button>
    <button type="button" class="ap-pill" data-ap-filter="product" aria-pressed="false">Product &amp; Data</button>
  </div>
  <div class="ap-grid">{grid}</div>
  <div class="ap-foot" id="ap-checkout">
    <p id="ap-summary">Pick any agent ($35) or build a volume pack: 5 Bots $119 (Save $56) · 10 Bots $199 (Save $151) · 20 Bots $299 (Save $401) · All 25 Bots $349 (Save $526).</p>
    <div class="ap-actions">
      <button type="button" class="ap-btn copy" id="ap-copy">Copy order note</button>
      <a class="ap-btn copy" id="ap-mail" href="mailto:support@agentscouthq.com?subject=AI%20Agent%20Pack%20order">Email fulfillment</a>
      <a class="ap-btn pay" id="ap-pay" href="https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09">Buy 1 Bot ($35)</a>
      <a class="ap-btn pay" id="ap-pay-all" href="https://buy.stripe.com/28E9AUdhpfVZ0OxbHJe7m0d">Buy All 25 ($349)</a>
      <a class="ap-btn x" id="ap-x" href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer">X Money @clampdown19</a>
    </div>
  </div>
</section>
<div class="ap-modal" id="ap-modal" hidden>
  <div class="ap-sheet" role="dialog" aria-modal="true" aria-labelledby="ap-modal-title">
    <h3 id="ap-modal-title"></h3>
    <div id="ap-modal-body"></div>
    <p><button type="button" class="ap-btn copy" id="ap-modal-close">Close</button></p>
  </div>
</div>
<script id="ap-data" type="application/json">{payload}</script>
<script>
(function(){{
  var data = JSON.parse(document.getElementById("ap-data").textContent);
  var byId = {{}};
  data.agents.forEach(function(a){{ byId[a.slug] = a; }});
  var selected = {{}};
  try {{
    JSON.parse(localStorage.getItem("as_agent_pack") || "[]").forEach(function(slug){{
      if (byId[slug]) selected[slug] = true;
    }});
  }} catch (e) {{}}
  function save(){{
    try {{ localStorage.setItem("as_agent_pack", JSON.stringify(Object.keys(selected))); }} catch (e) {{}}
  }}
  function list(){{ return Object.keys(selected).map(function(slug){{ return byId[slug]; }}); }}
  function tierInfo(rows){{
    var n = rows.length;
    if (n === 0) return {{price: 35, url: data.stripe.pack_1.url, label: "1 AI Agent Pack", savings: 0, off: false}};
    if (n === 1) return {{price: 35, url: data.stripe.pack_1.url, label: "1 AI Agent Pack ($35)", savings: 0, off: false}};
    if (n <= 5) return {{price: 119, url: data.stripe.pack_5.url, label: "5-Bot Pack ($119 · Save $56)", savings: 56, off: false}};
    if (n <= 10) return {{price: 199, url: data.stripe.pack_10.url, label: "10-Bot Pack ($199 · Save $151)", savings: 151, off: false}};
    if (n <= 20) return {{price: 299, url: data.stripe.pack_20.url, label: "20-Bot Pack ($299 · Save $401)", savings: 401, off: false}};
    return {{price: 349, url: data.stripe.pack_25.url, label: "All 25-Bot Mega Pack ($349 · Save $526)", savings: 526, off: false}};
  }}
  function note(){{
    var rows = list();
    var tier = tierInfo(rows);
    var lines = ["AgentScout AI Agent Pack order", "Selected (" + rows.length + "):"];
    rows.forEach(function(a){{ lines.push("- " + a.brandTitle + " — " + a.taglineRich + " ($35, " + a.script + ")"); }});
    lines.push("Checkout tier: " + tier.label);
    lines.push("Stripe: " + tier.url);
    lines.push("X Money: @clampdown19");
    return lines.join("\\n");
  }}
  function paint(){{
    var rows = list();
    document.querySelectorAll("[data-add]").forEach(function(btn){{
      var on = !!selected[btn.getAttribute("data-add")];
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.textContent = on ? "✓ Added" : "+ Add";
    }});
    var count = document.getElementById("ap-count");
    count.textContent = rows.length ? (rows.length + " selected") : "25 agents";
    var tier = tierInfo(rows);
    var summary = document.getElementById("ap-summary");
    var pay = document.getElementById("ap-pay");
    if (!rows.length) {{
      summary.textContent = "Pick any agent ($35) or build a volume pack: 5 Bots $119 (Save $56) · 10 Bots $199 (Save $151) · 20 Bots $299 (Save $401) · All 25 Bots $349 (Save $526).";
      pay.href = data.stripe.pack_1.url;
      pay.textContent = "Buy 1 Bot ($35)";
    }} else {{
      summary.textContent = rows.length + " selected · " + tier.label + ". Copy the order note so fulfillment sends your exact trained ZIPs.";
      pay.href = tier.url;
      pay.textContent = "Checkout $" + tier.price;
    }}
    document.getElementById("ap-mail").href = "mailto:support@agentscouthq.com?subject=" + encodeURIComponent("AI Agent Pack order") + "&body=" + encodeURIComponent(note());
  }}
  document.querySelectorAll("[data-add]").forEach(function(btn){{
    btn.addEventListener("click", function(){{
      var slug = btn.getAttribute("data-add");
      if (selected[slug]) delete selected[slug]; else selected[slug] = true;
      save(); paint();
    }});
  }});
  document.querySelectorAll("[data-ap-tier]").forEach(function(btn){{
    btn.addEventListener("click", function(){{
      var target = parseInt(btn.getAttribute("data-ap-tier"), 10) || 1;
      selected = {{}};
      data.agents.slice(0, target).forEach(function(a){{ selected[a.slug] = true; }});
      document.querySelectorAll("[data-ap-tier]").forEach(function(b){{ b.setAttribute("aria-pressed", b === btn ? "true" : "false"); }});
      save(); paint();
    }});
  }});
  document.querySelectorAll("[data-ap-filter]").forEach(function(btn){{
    btn.addEventListener("click", function(){{
      var dept = btn.getAttribute("data-ap-filter");
      document.querySelectorAll("[data-ap-filter]").forEach(function(b){{ b.setAttribute("aria-pressed", b === btn ? "true" : "false"); }});
      document.querySelectorAll("[data-pack]").forEach(function(card){{
        card.style.display = (dept === "all" || card.getAttribute("data-dept") === dept) ? "" : "none";
      }});
    }});
  }});
  function esc(s){{ return String(s).replace(/[&<>]/g, function(c){{ return {{"&":"&amp;","<":"&lt;",">":"&gt;"}}[c]; }}); }}
  function openModal(slug){{
    var a = byId[slug];
    document.getElementById("ap-modal-title").textContent = a.brandTitle + " — " + a.taglineRich;
    var routines = a.routines.map(function(r){{ return "<li><code>" + esc(r.cron) + "</code> " + esc(r.title) + " (<code>routines/" + esc(r.id) + ".md</code>)</li>"; }}).join("");
    var skills = a.heuristics.map(function(h){{ return "<li>" + esc(h) + "</li>"; }}).join("");
    var extra = a.storeNote ? "<p>" + esc(a.storeNote) + "</p>" : "";
    document.getElementById("ap-modal-body").innerHTML = "<p>" + esc(a.description) + "</p>" + extra + "<p><b>$" + a.price + " one-time</b> (or 5 for $119 · 10 for $199 · 20 for $299 · All 25 for $349) · skill <code>skills/" + esc(a.skill) + "/SKILL.md</code> · script <code>scripts/" + esc(a.script) + "</code></p><h4>Trained judgment (6 heuristics)</h4><ul>" + skills + "</ul><h4>Scheduled Routines (3 cron routines)</h4><ul>" + routines + "</ul><p><a class=\"ap-btn pay\" href=\"" + esc(a.checkoutUrl) + "\">Buy Single Agent ($35)</a> <a class=\"ap-btn copy\" href=\"/bot-store/" + esc(a.slug) + "/\">Full Pack Page</a></p>";
    document.getElementById("ap-modal").hidden = false;
  }}
  document.querySelectorAll("[data-preview]").forEach(function(btn){{
    btn.addEventListener("click", function(){{ openModal(btn.getAttribute("data-preview")); }});
  }});
  document.getElementById("ap-modal-close").addEventListener("click", function(){{ document.getElementById("ap-modal").hidden = true; }});
  document.getElementById("ap-modal").addEventListener("click", function(ev){{ if (ev.target.id === "ap-modal") ev.currentTarget.hidden = true; }});
  document.addEventListener("keydown", function(ev){{ if (ev.key === "Escape") document.getElementById("ap-modal").hidden = true; }});
  document.getElementById("ap-copy").addEventListener("click", function(){{
    var text = note();
    var btn = document.getElementById("ap-copy");
    function done(){{ btn.textContent = "Copied"; setTimeout(function(){{ btn.textContent = "Copy order note"; }}, 1600); }}
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, done);
    else done();
  }});
  document.getElementById("ap-cart").addEventListener("click", function(){{
    document.getElementById("ap-checkout").scrollIntoView({{behavior:"smooth", block:"nearest"}});
  }});
  paint();
}})();
</script>
"""
