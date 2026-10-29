#!/usr/bin/env python3
"""macOS-window pack builder HTML shared by /bot-store/ and /bot-templates/."""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_pack_catalog import ICONS, PACK_TIERS, STRIPE, TIER_PILLS, public_cards  # noqa: E402

CSS = """
<style id="ap-css">
.ap-window{margin:8px 0 28px;border:1px solid rgba(255,255,255,.16);border-radius:22px;background:#101218;box-shadow:0 24px 60px rgba(0,0,0,.45);overflow:visible;min-width:0;max-width:100%;box-sizing:border-box}
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
.ap-tiers{display:flex;flex-wrap:wrap;gap:8px;padding:0 16px 12px;min-width:0}
.ap-tier{display:inline-flex;align-items:center;min-height:36px;padding:6px 10px;border-radius:999px;border:1px solid rgba(147,197,253,.45);background:rgba(147,197,253,.08);color:#e0f2fe;font-size:12px;font-weight:800;cursor:pointer;max-width:100%;box-sizing:border-box;text-align:left;text-decoration:none}
.ap-buy{display:inline-flex;align-items:center;justify-content:center;min-height:36px;padding:6px 12px;border-radius:999px;background:#f4f4f5;color:#18181b;font-size:12.5px;font-weight:800;text-decoration:none;box-sizing:border-box}
.ap-tier[aria-pressed="true"]{background:#f4f4f5;color:#18181b;border-color:#f4f4f5}
.ap-grid{display:grid;grid-template-columns:minmax(0,1fr);gap:14px;padding:4px 14px 16px;min-width:0}
.ap-card{--ap:#93c5fd;position:relative;background:linear-gradient(180deg, color-mix(in srgb, var(--ap) 10%, #181c26) 0%, #141720 100%);border:1px solid color-mix(in srgb, var(--ap) 38%, rgba(255,255,255,.1));border-radius:18px;padding:14px 14px 12px;min-width:0;box-sizing:border-box;display:flex;flex-direction:column;gap:8px;box-shadow:0 10px 28px -10px rgba(0,0,0,.6), 0 0 22px -8px color-mix(in srgb, var(--ap) 35%, transparent);overflow:hidden}
.ap-card::before{content:"";position:absolute;left:0;right:0;top:0;height:3px;background:linear-gradient(90deg, transparent, var(--ap), transparent)}
.ap-card.is-selected,.ap-card:has(.ap-add[aria-pressed="true"]){border-color:var(--ap);box-shadow:0 12px 32px -12px rgba(0,0,0,.7), 0 0 26px -4px color-mix(in srgb, var(--ap) 72%, transparent)}
.ap-card-top{display:flex;flex-wrap:wrap;align-items:center;gap:8px;min-width:0}
.ap-ico{width:40px;height:40px;border-radius:12px;display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;background:color-mix(in srgb, var(--ap) 18%, #111);border:1px solid color-mix(in srgb, var(--ap) 45%, transparent);box-shadow:0 0 16px -6px color-mix(in srgb, var(--ap) 85%, transparent);color:var(--ap)}
.ap-ico svg{display:block}
.ap-badges{display:flex;flex-wrap:wrap;gap:6px;min-width:0;flex:1 1 120px}
.ap-price,.ap-dept{display:inline-flex;align-items:center;max-width:100%;border-radius:999px;padding:4px 8px;font-size:11.5px;font-weight:800;line-height:1.2;box-sizing:border-box}
.ap-price{color:#fff;background:color-mix(in srgb, var(--ap) 24%, #12151c);border:1px solid color-mix(in srgb, var(--ap) 55%, transparent)}
.ap-price small{font-weight:700;opacity:.8;margin-left:4px}
.ap-dept{color:#e4e4e7;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.14)}
.ap-add{margin-left:auto;border:1px solid color-mix(in srgb, var(--ap) 45%, rgba(255,255,255,.16));background:color-mix(in srgb, var(--ap) 18%, #1e2330);color:#f4f4f5;font-size:12px;font-weight:800;cursor:pointer;padding:7px 12px;border-radius:999px;white-space:normal;line-height:1.2;box-sizing:border-box}
.ap-add[aria-pressed="true"]{background:#052e16;color:#10b981;border-color:#10b981;box-shadow:0 0 16px -6px #10b981}
.ap-card h3{margin:2px 0 0;font-size:16.5px;font-weight:800;color:#fff;line-height:1.25;letter-spacing:-.02em;overflow-wrap:anywhere}
.ap-card h3 a{color:inherit;text-decoration:none;display:inline-flex;gap:.28em;flex-wrap:wrap}
.ap-card h3 .ap-role{color:#fff;margin-right:.05em}
.ap-card h3 .ap-kind{color:#d4d4d8;font-weight:700}
.ap-by{margin:0;display:flex;flex-wrap:wrap;align-items:center;gap:6px;font-size:12px;font-weight:700;color:#e4e4e7;line-height:1.3}
.ap-card img.aswm{height:1.15em;width:auto;max-width:100%;vertical-align:-.28em;filter:invert(1) hue-rotate(180deg)}
.ap-verified{display:inline-flex;align-items:center;gap:3px;border-radius:999px;padding:1px 7px;font-size:10.5px;font-weight:800;letter-spacing:.02em;color:#bbf7d0;background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.35)}
.ap-card .ap-tag{margin:0;color:var(--ap);font-size:13px;font-weight:700;line-height:1.4;overflow-wrap:anywhere}
.ap-promise{margin:0;color:#d4d4d8;font-size:13.5px;line-height:1.5;overflow-wrap:anywhere}
.ap-specs{display:flex;flex-wrap:wrap;gap:6px;list-style:none;padding:0;margin:2px 0 0;min-width:0}
.ap-specs li{max-width:100%;overflow-wrap:anywhere;font-size:11.5px;line-height:1.35;color:#e4e4e7;background:#12151c;border:1px solid rgba(255,255,255,.1);border-radius:999px;padding:4px 8px;box-sizing:border-box}
.ap-card-actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:auto;padding-top:4px;min-width:0}
.ap-preview{display:inline-flex;align-items:center;justify-content:center;min-height:36px;padding:6px 12px;border-radius:999px;border:1px solid color-mix(in srgb, var(--ap) 45%, rgba(255,255,255,.18));background:transparent;color:#e0f2fe;font-size:12.5px;font-weight:800;cursor:pointer;box-sizing:border-box;text-align:center}
.ap-details{color:#93c5fd;font-size:12.5px;font-weight:800;text-decoration:none;overflow-wrap:anywhere}
.ap-foot,.ap-dock{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;padding:12px 14px 14px;border-top:1px solid rgba(255,255,255,.08);background:#0e1118;min-width:0}
#ap-dock{border-radius:0 0 22px 22px}
.ap-foot p{margin:0;color:#e4e4e7;font-size:13px;line-height:1.45;min-width:0;flex:1 1 220px;overflow-wrap:anywhere}
.ap-actions{display:flex;flex-wrap:wrap;gap:8px;min-width:0}
.ap-btn{display:inline-flex;align-items:center;justify-content:center;min-height:40px;padding:8px 12px;border-radius:10px;font-size:13px;font-weight:800;text-decoration:none;border:1px solid transparent;box-sizing:border-box;max-width:100%;cursor:pointer;text-align:center}
.ap-btn.pay{background:#f4f4f5;color:#18181b}
.ap-btn.x{background:transparent;color:#e4e4e7;border-color:rgba(255,255,255,.18)}
.ap-btn.copy{background:#172033;color:#dbeafe;border-color:#1d4ed8}
.ap-btn[disabled],.ap-btn.is-off{opacity:.45;pointer-events:none}
.ap-modal{position:fixed;inset:0;z-index:80;background:rgba(0,0,0,.68);display:flex;align-items:flex-end;justify-content:center;padding:12px;box-sizing:border-box}
.ap-modal[hidden]{display:none}
.ap-sheet{width:min(680px,100%);max-height:min(88vh,820px);overflow:auto;background:#12151c;color:#e4e4e7;border-radius:18px;padding:16px;box-sizing:border-box;border:1px solid color-mix(in srgb, var(--ap, #93c5fd) 45%, rgba(255,255,255,.12));box-shadow:0 24px 60px rgba(0,0,0,.5), 0 0 28px -10px color-mix(in srgb, var(--ap, #93c5fd) 55%, transparent);min-width:0}
.ap-sheet-top{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;min-width:0}
.ap-sheet h3{margin:0;color:#fff;font-size:18px;line-height:1.3;overflow-wrap:anywhere}
.ap-sheet h4{margin:14px 0 8px;color:#fff;font-size:14px}
.ap-sheet p,.ap-sheet li{font-size:13.5px;line-height:1.5;overflow-wrap:anywhere}
.ap-sheet code{overflow-wrap:anywhere}
.ap-hosts,.ap-chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0;padding:0;list-style:none}
.ap-hosts li,.ap-chips li{border-radius:999px;padding:4px 8px;font-size:11.5px;font-weight:700;background:#1c2230;border:1px solid rgba(255,255,255,.12);color:#e4e4e7;max-width:100%;overflow-wrap:anywhere}
.ap-kicker{margin:0;color:var(--ap, #93c5fd);font-weight:800;font-size:13px}
.ap-checks,.ap-routines{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px}
.ap-checks li,.ap-routines li{background:#181c27;border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:8px 10px;min-width:0}
.ap-checks li::before{content:"✓ ";color:#34d399;font-weight:800}
.ap-secure{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 0}
.ap-secure span{border-radius:999px;padding:4px 8px;font-size:11.5px;font-weight:800;color:#bbf7d0;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.35)}
.ap-sheet-cta{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.ap-note{color:#a1a1aa;font-size:12.5px}
@media(min-width:640px) and (max-width:1024px){.ap-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(min-width:1025px){.ap-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(min-width:720px){.ap-modal{align-items:center}}
@media(max-width:640px){
  .ap-chrome{flex-wrap:wrap}
  .ap-chrome-side{width:100%;justify-content:flex-end}
  .ap-btn,.ap-sheet-cta .ap-btn{width:100%}
  .ap-card-actions .ap-preview,.ap-card-actions .ap-details{width:100%;justify-content:center;text-align:center}
}
</style>
"""


def _e(value) -> str:
    return html.escape(str(value or ""), quote=True)


def pack_section_html() -> str:
    cards = public_cards()
    tiers = list(PACK_TIERS.values())
    payload = json.dumps(
        {"agents": cards, "stripe": STRIPE, "packTiers": tiers},
        ensure_ascii=False,
    ).replace("<", "\\u003c")
    tier_pills = "".join(
        f'<a class="ap-tier" data-ap-tier="{row["count"]}" href="{_e(row["url"])}" target="_blank" rel="noopener noreferrer">{_e(TIER_PILLS[row["count"]])}</a>'
        for row in tiers
    )
    items = []
    for card in cards:
        icon = ICONS[card["icon"]]
        chips = "".join(
            f"<li>{_e(chip)}</li>"
            for chip in card["chips"]
            if chip not in {
                card["script"],
                f"🐍 {card['script']}",
                f"🧠 {card['skill']}/SKILL.md",
                f"⏰ {len(card['routines'])} routines",
            }
            and not str(chip).endswith(".py")
        )
        items.append(
            f'<article class="ap-card" style="--ap:{_e(card["color"])}" data-pack="{_e(card["slug"])}" data-dept="{_e(card["dept"])}">'
            f'<div class="ap-card-top">'
            f'<span class="ap-ico" style="color:{_e(card["color"])}">'
            f'<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="{icon}"/></svg>'
            f'</span>'
            f'<span class="ap-badges"><span class="ap-price">${card["price"]}<small>once</small></span>'
            f'<span class="ap-dept">{_e(card["deptShort"])}</span></span>'
            f'<a class="ap-buy" href="{_e(PACK_TIERS["tier_1"]["url"])}" target="_blank" rel="noopener noreferrer">Buy $35</a>'
            f'<button type="button" class="ap-add" data-add="{_e(card["slug"])}" aria-pressed="false">+ Add ($35)</button>'
            f'</div>'
            f'<h3><a href="/bot-store/{_e(card["slug"])}/"><span class="ap-role">{_e(card["role"])}</span> <span class="ap-kind">Agent</span></a></h3>'
            f'<p class="ap-by">built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="120" height="24">'
            f'<span class="ap-verified">✓ Verified</span></p>'
            f'<p class="ap-tag">{_e(card["tagline"])}</p>'
            f'<p class="ap-promise">{_e(card["promise"])}</p>'
            f'<ul class="ap-specs">'
            f'<li>🧠 {_e(card["skill"])}/SKILL.md</li>'
            f'<li>🐍 {_e(card["script"])}</li>'
            f'<li>⏰ {len(card["routines"])} routines</li>'
            f'<li>🔒 Offline · Zero Telemetry</li>'
            f'{chips}'
            f'</ul>'
            f'<div class="ap-card-actions">'
            f'<button type="button" class="ap-preview" data-preview="{_e(card["slug"])}">Preview Skills &amp; Routines</button>'
            f'<a class="ap-details" href="/bot-store/{_e(card["slug"])}/">Full Pack Details →</a>'
            f'</div></article>'
        )
    grid = "".join(items)
    html_doc = """@@CSS@@
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
  <div class="ap-filters" role="toolbar" aria-label="Filter agent packs">
    <button type="button" class="ap-pill" data-ap-filter="all" aria-pressed="true">All 25</button>
    <button type="button" class="ap-pill" data-ap-filter="sales" aria-pressed="false">Sales &amp; Outreach</button>
    <button type="button" class="ap-pill" data-ap-filter="marketing" aria-pressed="false">Marketing &amp; Content</button>
    <button type="button" class="ap-pill" data-ap-filter="ops" aria-pressed="false">Operations &amp; Admin</button>
    <button type="button" class="ap-pill" data-ap-filter="product" aria-pressed="false">Product &amp; Data</button>
  </div>
  <div class="ap-tiers" role="group" aria-label="Volume discount tiers">@@TIERS@@</div>
  <div class="ap-grid">@@GRID@@</div>
  <div class="ap-foot ap-dock" id="ap-dock">
    <p id="ap-summary">Each role pack is $35. Volume pricing: 5 for $119, 10 for $199, 20 for $299, all 25 for $349. Flagship Pro Bots stay $39 / $59 / $59 / $69, and the 4-Bot bundle stays $149.</p>
    <div class="ap-actions">
      <button type="button" class="ap-btn copy" id="ap-copy">Copy order note</button>
      <a class="ap-btn copy" id="ap-mail" href="mailto:support@agentscouthq.com?subject=AI%20Agent%20Pack%20order">Email fulfillment</a>
      <a class="ap-btn pay is-off" id="ap-pay" href="#ap-dock" aria-disabled="true">Checkout</a>
      <a class="ap-btn x" id="ap-x" href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer">X Money @clampdown19</a>
    </div>
  </div>
</section>
<div class="ap-modal" id="ap-modal" hidden>
  <div class="ap-sheet" role="dialog" aria-modal="true" aria-labelledby="ap-modal-title">
    <div class="ap-sheet-top">
      <h3 id="ap-modal-title"></h3>
      <button type="button" class="ap-btn copy" id="ap-modal-close">Close</button>
    </div>
    <div id="ap-modal-body"></div>
  </div>
</div>
<script id="ap-data" type="application/json">@@PAYLOAD@@</script>
<script>
(function(){
  var data = JSON.parse(document.getElementById("ap-data").textContent);
  var byId = {};
  data.agents.forEach(function(a){ byId[a.slug] = a; });
  var selected = {};
  try {
    JSON.parse(localStorage.getItem("as_agent_pack") || "[]").forEach(function(slug){
      if (byId[slug]) selected[slug] = true;
    });
  } catch (e) {}
  function save(){
    try { localStorage.setItem("as_agent_pack", JSON.stringify(Object.keys(selected))); } catch (e) {}
  }
  function list(){ return Object.keys(selected).map(function(slug){ return byId[slug]; }); }
  function money(n){
    var s = (Math.round(Number(n) * 100) / 100).toFixed(2);
    return s.replace(/\\.00$/, "");
  }
  function tier(ids){
    var n = ids.length;
    var ladder = (data.packTiers || []).slice().sort(function(a, b){ return a.count - b.count; });
    if (!n) return {n: 0, price: 0, regular: 0, save: 0, perBot: 0, label: "Select agents", url: "", nudge: "", off: true};
    var inf = 1e9;
    var best = [];
    for (var i = 0; i <= n; i++) best.push(inf);
    best[0] = 0;
    for (var have = 0; have <= n; have++){
      if (best[have] >= inf) continue;
      ladder.forEach(function(row){
        var nxt = have + row.count;
        if (nxt <= n && best[have] + row.price < best[nxt]) best[nxt] = best[have] + row.price;
      });
    }
    var price = best[n];
    var regular = n * 35;
    var exact = null;
    ladder.forEach(function(row){ if (row.count === n) exact = row; });
    var nudge = "";
    ladder.forEach(function(row){
      if (!nudge && row.count > n && row.price < price){
        var add = row.count - n;
        var extra = price - row.price;
        var short = String(row.label).split(" (")[0];
        nudge = "Add " + add + " more " + (add === 1 ? "bot" : "bots") + " to unlock the " + short + " for $" + row.price + " (save $" + extra + " more)!";
      }
    });
    return {
      n: n,
      price: price,
      regular: regular,
      save: regular - price,
      perBot: Math.round((price / n) * 100) / 100,
      label: exact ? exact.label : (n + " AI Agent Packs ($" + price + ")"),
      url: exact && exact.url ? exact.url : "",
      nudge: nudge,
      off: !(exact && exact.url)
    };
  }
  function note(){
    var rows = list();
    var quote = tier(Object.keys(selected));
    var lines = ["AgentScout AI Agent Pack order", "Selected (" + rows.length + "):"];
    rows.forEach(function(a){ lines.push("- " + a.productName + " — " + a.tagline + " ($" + a.price + ", " + a.script + ")"); });
    lines.push("Price: $" + quote.price + " (" + quote.label + ")");
    if (quote.save) lines.push("Regular $" + quote.regular + " · Save $" + quote.save + " · $" + money(quote.perBot) + "/bot");
    if (quote.nudge) lines.push(quote.nudge);
    lines.push("Stripe: " + (quote.url || "pending — do not use a flagship bot link"));
    lines.push("X Money: @clampdown19");
    lines.push("Fulfill the ZIP for each selected role pack. This price is separate from the $39/$59/$69 bots and the $149 bundle.");
    return lines.join("\\n");
  }
  function paint(){
    var rows = list();
    var ids = Object.keys(selected);
    document.querySelectorAll("[data-pack]").forEach(function(card){
      card.classList.toggle("is-selected", !!selected[card.getAttribute("data-pack")]);
    });
    document.querySelectorAll("[data-add]").forEach(function(btn){
      var on = !!selected[btn.getAttribute("data-add")];
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.textContent = on ? "✓ Added" : "+ Add ($35)";
    });
    var quote = tier(ids);
    document.getElementById("ap-count").textContent = rows.length ? (rows.length + " selected") : "25 agents";
    var summary = document.getElementById("ap-summary");
    var pay = document.getElementById("ap-pay");
    document.querySelectorAll("[data-ap-tier]").forEach(function(btn){
      btn.setAttribute("aria-pressed", String(quote.n) === btn.getAttribute("data-ap-tier") ? "true" : "false");
    });
    var copyBtn = document.getElementById("ap-copy");
    var mailBtn = document.getElementById("ap-mail");
    if (!rows.length) {
      summary.textContent = "Each role pack is $35. Volume pricing: 5 for $119, 10 for $199, 20 for $299, all 25 for $349. Flagship Pro Bots stay $39 / $59 / $59 / $69, and the 4-Bot bundle stays $149.";
      if (copyBtn) copyBtn.style.display = "none";
      if (mailBtn) mailBtn.style.display = "none";
      pay.classList.add("is-off");
      pay.setAttribute("aria-disabled", "true");
      pay.href = "#ap-dock";
      pay.textContent = "Select agents above to checkout";
    } else {
      if (copyBtn) copyBtn.style.display = "";
      if (mailBtn) mailBtn.style.display = "";
      var bits = [rows.length + " selected", quote.label, "$" + money(quote.price)];
      if (quote.regular !== quote.price) bits.push("regular $" + money(quote.regular));
      if (quote.save) bits.push("Save $" + money(quote.save));
      bits.push("$" + money(quote.perBot) + "/bot");
      if (quote.nudge) bits.push(quote.nudge);
      if (!quote.url) bits.push("Stripe link for this tier is not connected yet. Copy the order note or pay via X Money @clampdown19.");
      summary.textContent = bits.join(" · ").replace(" · " + quote.nudge, ". " + quote.nudge);
      if (quote.url) {
        pay.classList.remove("is-off");
        pay.removeAttribute("aria-disabled");
        pay.href = quote.url;
        pay.textContent = "Checkout $" + money(quote.price);
      } else {
        pay.classList.add("is-off");
        pay.setAttribute("aria-disabled", "true");
        pay.href = "#ap-dock";
        pay.textContent = "Checkout $" + money(quote.price);
      }
    }
    document.getElementById("ap-mail").href = "mailto:support@agentscouthq.com?subject=" + encodeURIComponent("AI Agent Pack order") + "&body=" + encodeURIComponent(note());
  }
  function toggle(slug){
    if (selected[slug]) delete selected[slug]; else selected[slug] = true;
    save(); paint();
  }
  document.querySelectorAll("[data-add]").forEach(function(btn){
    btn.addEventListener("click", function(){ toggle(btn.getAttribute("data-add")); });
  });
  document.querySelectorAll("[data-ap-filter]").forEach(function(btn){
    btn.addEventListener("click", function(){
      var dept = btn.getAttribute("data-ap-filter");
      document.querySelectorAll("[data-ap-filter]").forEach(function(b){ b.setAttribute("aria-pressed", b === btn ? "true" : "false"); });
      document.querySelectorAll("[data-pack]").forEach(function(card){
        card.style.display = (dept === "all" || card.getAttribute("data-dept") === dept) ? "" : "none";
      });
    });
  });
  document.querySelectorAll("[data-ap-tier]").forEach(function(btn){
    btn.addEventListener("click", function(){
      document.getElementById("ap-dock").scrollIntoView({behavior:"smooth", block:"nearest"});
    });
  });
  function esc(s){ return String(s).replace(/[&<>]/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;"}[c]; }); }
  function openModal(slug){
    var a = byId[slug];
    var sheet = document.querySelector(".ap-sheet");
    sheet.style.setProperty("--ap", a.color);
    document.getElementById("ap-modal-title").textContent = a.productName;
    var on = !!selected[slug];
    var hosts = ["Grok Bot", "Claude Code", "Cursor", "Codex", "Lovable"].map(function(h){ return "<li>" + esc(h) + "</li>"; }).join("");
    var skills = a.heuristics.map(function(h){ return "<li>" + esc(h) + "</li>"; }).join("");
    var routines = a.routines.map(function(r){
      return "<li><b>" + esc(r.title) + "</b><br><code>" + esc(r.cron) + "</code><br>" + esc(r.prompt || "") + "</li>";
    }).join("");
    var chips = (a.chips || []).map(function(c){ return "<li>" + esc(c) + "</li>"; }).join("");
    var extra = a.storeNote ? "<p class=\\"ap-note\\">" + esc(a.storeNote) + "</p>" : "";
    document.getElementById("ap-modal-body").innerHTML =
      extra +
      "<p class=\\"ap-kicker\\">" + esc(a.tagline) + "</p>" +
      "<p>" + esc(a.promise) + "</p>" +
      "<ul class=\\"ap-hosts\\">" + hosts + "</ul>" +
      "<ul class=\\"ap-chips\\">" + chips + "</ul>" +
      "<h4>Trained judgment</h4><ul class=\\"ap-checks\\">" + skills + "</ul>" +
      "<h4>Routines</h4><ul class=\\"ap-routines\\">" + routines + "</ul>" +
      "<h4>Security</h4><div class=\\"ap-secure\\"><span>100% Python stdlib</span><span>0 network calls</span><span>Approval-gated</span></div>" +
      "<div class=\\"ap-sheet-cta\\">" +
      "<button type=\\"button\\" class=\\"ap-btn pay\\" data-modal-add=\\"" + esc(a.slug) + "\\">" + (on ? "✓ Added" : "+ Add ($35)") + "</button>" +
      "<a class=\\"ap-btn copy\\" href=\\"/bot-store/" + esc(a.slug) + "/\\">View Full Pack Page</a>" +
      "<a class=\\"ap-btn x\\" href=\\"" + esc(a.checkoutUrl || "#ap-dock") + "\\"" + (a.checkoutUrl ? " target=\\"_blank\\" rel=\\"noopener noreferrer\\"" : "") + ">Instant Checkout ($" + a.price + ")</a>" +
      "</div>";
    document.getElementById("ap-modal").hidden = false;
  }
  document.querySelectorAll("[data-preview]").forEach(function(btn){
    btn.addEventListener("click", function(){ openModal(btn.getAttribute("data-preview")); });
  });
  document.getElementById("ap-modal-body").addEventListener("click", function(ev){
    var btn = ev.target.closest("[data-modal-add]");
    if (!btn) return;
    toggle(btn.getAttribute("data-modal-add"));
    openModal(btn.getAttribute("data-modal-add"));
  });
  document.getElementById("ap-modal-close").addEventListener("click", function(){ document.getElementById("ap-modal").hidden = true; });
  document.getElementById("ap-modal").addEventListener("click", function(ev){ if (ev.target.id === "ap-modal") ev.currentTarget.hidden = true; });
  document.addEventListener("keydown", function(ev){ if (ev.key === "Escape") document.getElementById("ap-modal").hidden = true; });
  document.getElementById("ap-copy").addEventListener("click", function(){
    var text = note();
    var btn = document.getElementById("ap-copy");
    function done(){ btn.textContent = "Copied"; setTimeout(function(){ btn.textContent = "Copy order note"; }, 1600); }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, done);
    else done();
  });
  document.getElementById("ap-cart").addEventListener("click", function(){
    document.getElementById("ap-dock").scrollIntoView({behavior:"smooth", block:"nearest"});
  });
  paint();
})();
</script>
"""
    return (
        html_doc.replace("@@CSS@@", CSS)
        .replace("@@TIERS@@", tier_pills)
        .replace("@@GRID@@", grid)
        .replace("@@PAYLOAD@@", payload)
    )
