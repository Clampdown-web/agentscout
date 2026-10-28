#!/usr/bin/env python3
"""macOS-window pack builder HTML shared by /bot-store/ and /bot-templates/."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_pack_catalog import ICONS, STRIPE, public_cards  # noqa: E402

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
.ap-filters{display:flex;flex-wrap:wrap;gap:8px;padding:12px 16px;min-width:0}
.ap-pill{min-height:36px;padding:6px 12px;border-radius:999px;border:1px solid rgba(255,255,255,.12);background:transparent;color:#d4d4d8;font-size:12.5px;font-weight:700;cursor:pointer;max-width:100%;box-sizing:border-box}
.ap-pill[aria-pressed="true"]{background:#f4f4f5;color:#18181b;border-color:#f4f4f5}
.ap-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;padding:0 14px 14px;min-width:0}
.ap-card{background:#1a1d25;border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:12px;min-width:0;box-sizing:border-box;display:flex;flex-direction:column;gap:8px}
.ap-card-top{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;min-width:0}
.ap-ico{width:34px;height:34px;border-radius:10px;display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;background:color-mix(in srgb,var(--ap) 18%,#111)}
.ap-ico svg{display:block}
.ap-add{border:0;background:transparent;color:#a1a1aa;font-size:12px;font-weight:700;cursor:pointer;padding:4px 2px;white-space:nowrap}
.ap-add[aria-pressed="true"]{color:#86efac}
.ap-card h3{margin:0;font-size:14px;color:#fafafa;line-height:1.3;overflow-wrap:anywhere}
.ap-card .ap-tag{margin:0;color:#a1a1aa;font-size:12px;line-height:1.35;overflow-wrap:anywhere}
.ap-preview{align-self:flex-start;background:transparent;border:0;color:#93c5fd;font-size:12px;font-weight:700;cursor:pointer;padding:0;text-align:left}
.ap-foot{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;padding:12px 14px 14px;border-top:1px solid rgba(255,255,255,.08);background:#101218;min-width:0}
.ap-foot p{margin:0;color:#e4e4e7;font-size:13px;line-height:1.45;min-width:0;flex:1 1 220px;overflow-wrap:anywhere}
.ap-actions{display:flex;flex-wrap:wrap;gap:8px;min-width:0}
.ap-btn{display:inline-flex;align-items:center;justify-content:center;min-height:40px;padding:8px 12px;border-radius:10px;font-size:13px;font-weight:800;text-decoration:none;border:1px solid transparent;box-sizing:border-box;max-width:100%;cursor:pointer}
.ap-btn.pay{background:#f4f4f5;color:#18181b}
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


def pack_section_html() -> str:
    cards = public_cards()
    payload = json.dumps({"agents": cards, "stripe": STRIPE}, ensure_ascii=False).replace("<", "\\u003c")
    items = []
    for card in cards:
        icon = ICONS[card["icon"]]
        items.append(
            f'<article class="ap-card" data-pack="{card["slug"]}" data-dept="{card["dept"]}">'
            f'<div class="ap-card-top"><span class="ap-ico" style="--ap:{card["color"]};color:{card["color"]}">'
            f'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="{icon}"/></svg>'
            f'</span><button type="button" class="ap-add" data-add="{card["slug"]}" aria-pressed="false">+ Add</button></div>'
            f'<h3>{card["title"]}</h3><p class="ap-tag">{card["tagline"]}</p>'
            f'<button type="button" class="ap-preview" data-preview="{card["slug"]}">Preview Trained Skills &amp; Scripts</button>'
            f'</article>'
        )
    grid = "".join(items)
    return f"""{CSS}
<section id="ai-agent-packs" class="ap-window" aria-labelledby="ap-title">
  <div class="ap-chrome">
    <span class="ap-dots" aria-hidden="true"><i class="r"></i><i class="y"></i><i class="g"></i></span>
    <div class="ap-chrome-copy">
      <h2 id="ap-title">AI Agent Packs</h2>
      <p>Pick the agents you want in your pack — pre-trained with real skills, routines &amp; Python tools for your business</p>
    </div>
    <div class="ap-chrome-side">
      <span class="ap-count" id="ap-count">25 agents</span>
      <button type="button" class="ap-cart" id="ap-cart" aria-label="Open pack checkout">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M6 6h15l-1.5 9h-12z"/><path d="M6 6L5 3H2"/><circle cx="9" cy="20" r="1.2"/><circle cx="18" cy="20" r="1.2"/></svg>
      </button>
    </div>
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
    <p id="ap-summary">Select agents to build a pack. One agent checks out on its matching flagship Stripe link. Two or more use the $149 pack link. Your order note lists the exact ZIPs to fulfill.</p>
    <div class="ap-actions">
      <button type="button" class="ap-btn copy" id="ap-copy">Copy order note</button>
      <a class="ap-btn copy" id="ap-mail" href="mailto:support@agentscouthq.com?subject=AI%20Agent%20Pack%20order">Email fulfillment</a>
      <a class="ap-btn pay is-off" id="ap-pay" href="https://buy.stripe.com/fZueVe5OX7pt1SB6npe7m08" aria-disabled="true">Checkout</a>
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
  function note(){{
    var rows = list();
    var tier = tierInfo(rows);
    var lines = ["AgentScout AI Agent Pack order", "Selected (" + rows.length + "):"];
    rows.forEach(function(a){{ lines.push("- " + a.title + " — " + a.tagline + " ($" + a.price + ", " + a.script + ")"); }});
    lines.push("Checkout: " + tier.label + " $" + tier.price);
    lines.push("Stripe: " + tier.url);
    lines.push("X Money: @clampdown19");
    lines.push("Fulfill the ZIP for each selected agent. The payment link is the matching flagship checkout.");
    return lines.join("\\n");
  }}
  function tierInfo(rows){{
    if (rows.length === 0) return {{price: 0, url: data.stripe.bundle.url, label: "Select agents", off: true}};
    if (rows.length === 1) return {{price: rows[0].price, url: rows[0].checkoutUrl, label: rows[0].checkoutLabel, off: false}};
    return {{price: 149, url: data.stripe.bundle.url, label: "Pack of " + rows.length, off: false}};
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
      summary.textContent = "Select agents to build a pack. One agent checks out on its matching flagship Stripe link. Two or more use the $149 pack link. Your order note lists the exact ZIPs to fulfill.";
      pay.classList.add("is-off");
      pay.setAttribute("aria-disabled", "true");
      pay.textContent = "Checkout";
    }} else {{
      summary.textContent = rows.length + " selected · " + tier.label + " · $" + tier.price + ". Copy the order note so fulfillment sends those trained ZIPs.";
      pay.classList.remove("is-off");
      pay.removeAttribute("aria-disabled");
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
    document.getElementById("ap-modal-title").textContent = a.title + " — " + a.tagline;
    var routines = a.routines.map(function(r){{ return "<li><code>" + esc(r.cron) + "</code> " + esc(r.title) + "</li>"; }}).join("");
    var skills = a.heuristics.map(function(h){{ return "<li>" + esc(h) + "</li>"; }}).join("");
    var extra = a.storeNote ? "<p>" + esc(a.storeNote) + "</p>" : "";
    document.getElementById("ap-modal-body").innerHTML = extra + "<p>" + esc(a.promise) + "</p><p><b>$" + a.price + "</b> · skill <code>skills/" + esc(a.skill) + "/SKILL.md</code> · script <code>scripts/" + esc(a.script) + "</code></p><h4>Trained judgment</h4><ul>" + skills + "</ul><h4>Routines</h4><ul>" + routines + "</ul>";
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
