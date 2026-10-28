import os, re, sys
from pathlib import Path
from build_extras import B, e, shell, clip_text, clip_title
sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from pack_builder_html import pack_section_html

CSS = """<style id="bs-css">
.bs-hero{margin:14px 0 22px;padding:24px 20px;text-align:center;border-radius:18px;border:2px solid #84cc16;background:radial-gradient(900px 280px at 0% 0%,rgba(132,204,22,.16),transparent 62%),radial-gradient(900px 280px at 100% 100%,rgba(16,185,129,.14),transparent 62%),#0b0d09;box-shadow:0 12px 34px rgba(0,0,0,.45),0 0 28px rgba(132,204,22,.15)}
.bs-compat-pill{display:inline-flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px;font-weight:800;letter-spacing:.03em;padding:7px 14px;border-radius:999px;background:rgba(132,204,22,.18);border:1.5px solid #a3e635;color:#ecfccb;margin-bottom:12px;box-shadow:0 0 16px rgba(132,204,22,.3)}
.bs-hero img.aswm,.bs-card img.aswm,.bs-bundle img.aswm{filter:invert(1) hue-rotate(180deg)}
.bs-builtby{display:inline-flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:4px;font-size:13px;font-weight:700;color:#e5e7eb;margin:4px auto 6px;text-align:center}
.bs-builtby img.aswm{height:1.38em;vertical-align:-.34em;margin:0 -.35em 0 .08em}
.bs-hero{text-align:center}
.bs-compat-pill{justify-content:center;text-align:center}
.bs-hero h1{margin:0 auto 10px;font-size:clamp(24px,3.6vw,34px);line-height:1.22;color:#fff;text-align:center;display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:6px}
.bs-hero p{margin:0 auto 14px;font-size:15px;line-height:1.6;color:#e7e5e4;max-width:860px;text-align:center;padding:0 10px;box-sizing:border-box}
.bs-hero-badges{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;justify-content:center}
.bs-badge{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:9px;font-size:12.5px;font-weight:700;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.15);color:#f5f5f4;text-decoration:none}
a.bs-badge:hover{border-color:#a3e635;color:#ecfccb;text-decoration:none}
.bs-notice{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;text-align:center;gap:10px;padding:12px 16px;margin:0 0 18px;border-radius:12px;background:rgba(132,204,22,.11);border:1.5px solid rgba(163,230,53,.5);font-size:13px;color:#ecfccb}
.bs-notice a{color:#fde047;font-weight:700;text-decoration:underline}
.bs-vid{margin:0 0 22px;border-radius:14px;overflow:hidden;border:1.5px solid rgba(132,204,22,.5);background:#090806;box-shadow:0 8px 26px rgba(0,0,0,.4)}
.bs-vid video{display:block;width:100%;height:auto;max-width:100%}
.bs-filters{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px;align-items:center}
.bs-fbtn{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:44px;padding:8px 14px;border-radius:10px;font-size:13px;font-weight:700;border:1.5px solid rgba(255,255,255,.16);background:#121318;color:#e5e7eb;cursor:pointer;transition:all .15s}
.bs-fbtn:hover,.bs-fbtn[aria-pressed="true"]{background:rgba(132,204,22,.2);border-color:#a3e635;color:#ecfccb;box-shadow:0 0 14px rgba(132,204,22,.3)}
.bs-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-bottom:18px}
.bs-card{padding:22px 20px;border-radius:15px;background:#14110b;border:1.5px solid rgba(245,158,11,.32);display:flex;flex-direction:column;justify-content:space-between;align-items:center;text-align:center;gap:12px;position:relative;overflow:hidden;box-sizing:border-box;min-width:0}
.bs-card>div{width:100%;display:flex;flex-direction:column;align-items:center;text-align:center}
.bs-card.neon-lime{border:2px solid #84cc16;background:linear-gradient(160deg,rgba(132,204,22,.16),#10140a 68%);box-shadow:0 0 24px rgba(132,204,22,.22),inset 0 0 16px rgba(132,204,22,.08)}
.bs-card.neon-gold{border:2px solid #eab308;background:linear-gradient(160deg,rgba(234,179,8,.16),#141108 68%);box-shadow:0 0 24px rgba(234,179,8,.22),inset 0 0 16px rgba(234,179,8,.08)}
.bs-card.neon-orange{border:2px solid #f97316;background:linear-gradient(160deg,rgba(249,115,22,.16),#150e08 68%);box-shadow:0 0 24px rgba(249,115,22,.22),inset 0 0 16px rgba(249,115,22,.08)}
.bs-card.neon-red{border:2px solid #ef4444;background:linear-gradient(160deg,rgba(239,68,68,.16),#160b0b 68%);box-shadow:0 0 24px rgba(239,68,68,.22),inset 0 0 16px rgba(239,68,68,.08)}
.bs-card.neon-custom{border:2px dashed rgba(168,85,247,.65);background:linear-gradient(160deg,rgba(168,85,247,.12),#110d18 68%)}
.bs-card-top{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;width:100%}
.bs-price{font-size:26px;font-weight:800;color:#fff;letter-spacing:-.02em}
.bs-price small{font-size:12px;font-weight:600;color:#d6d3d1;margin-left:4px}
.bs-tag{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.05em;padding:4px 10px;border-radius:999px;background:rgba(245,158,11,.18);color:#fde68a;border:1px solid rgba(245,158,11,.4)}
.bs-card h2{margin:6px auto 4px;font-size:18px;color:#fff;line-height:1.3;text-align:center}
.bs-card p{margin:0 auto;font-size:13.5px;color:#d6d3d1;line-height:1.55;text-align:center;padding:0 8px;box-sizing:border-box}
.bs-compat-line{display:inline-block;margin-top:8px;padding:4px 9px;border-radius:7px;font-size:11.5px;font-weight:700;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);color:#ecfccb}
.bs-list{list-style:none;padding:0 8px;margin:12px auto 18px;text-align:center;box-sizing:border-box;font-size:13px;color:#e7e5e4;line-height:1.55;width:100%}
.bs-list li{margin:4px 0}
.bs-manifest{padding:12px 14px;border-radius:10px;background:rgba(0,0,0,.38);border:1px solid rgba(255,255,255,.1);font-size:12px;color:#d6d3d1;line-height:1.5;overflow-wrap:anywhere;text-align:center;width:100%;box-sizing:border-box}
.bs-manifest b{color:#fff}
.bs-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px;width:100%;justify-content:center}
.bs-btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:44px;padding:10px 14px;border-radius:10px;font-size:13px;font-weight:800;text-decoration:none;transition:transform .12s,opacity .12s;flex:1 1 auto;text-align:center;box-sizing:border-box}
.bs-btn:hover{transform:translateY(-1px);text-decoration:none}
.bs-bundle{padding:24px 20px;border-radius:16px;background:linear-gradient(135deg,rgba(16,185,129,.22),rgba(132,204,22,.16),#0a1510);border:2.5px solid #10b981;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:16px;box-shadow:0 0 32px rgba(16,185,129,.3),inset 0 0 20px rgba(16,185,129,.1);margin-bottom:24px;box-sizing:border-box}
.bs-bundle-copy{width:100%;min-width:0;display:flex;flex-direction:column;align-items:center;text-align:center}
.bs-bundle-copy h2{margin:6px auto;font-size:21px;color:#fff;line-height:1.28;text-align:center}
.bs-bundle-copy p{margin:0 auto 10px;font-size:14px;color:#ecfdf5;line-height:1.58;text-align:center;max-width:820px}
.bs-bundle-ctas{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:center;width:100%}
.bs-faq{margin:26px 0;padding:22px;border-radius:16px;background:#101218;border:1px solid var(--border)}
.bs-faq h2{margin:0 0 14px;font-size:20px;color:#fff}
.bs-faq-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.bs-faq-item{padding:15px;border-radius:12px;background:#161922;border:1px solid rgba(255,255,255,.1)}
.bs-faq-item h3{margin:0 0 6px;font-size:15px;color:#fff;line-height:1.35}
.bs-faq-item p{margin:0;font-size:13.5px;color:#d1d5db;line-height:1.55}
.bs-faq-item a{color:#a3e635;font-weight:700;text-decoration:underline}
@media(max-width:780px){
  .bs-grid,.bs-faq-grid{grid-template-columns:1fr}
  .bs-hero,.bs-bundle,.bs-faq{padding:16px}
  .bs-btn{width:100%}
}
</style>"""

JS = """<script>
(function(){
  var btns = document.querySelectorAll('.bs-fbtn[data-filter]');
  var items = document.querySelectorAll('[data-bs-cat]');
  btns.forEach(function(btn){
    btn.addEventListener('click', function(){
      var cat = btn.getAttribute('data-filter');
      btns.forEach(function(b){ b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'); });
      items.forEach(function(el){
        var c = el.getAttribute('data-bs-cat') || '';
        el.style.display = (cat === 'all' || c.indexOf(cat) !== -1) ? '' : 'none';
      });
    });
  });
})();
</script>"""

def pages(t):
    os.makedirs("bot-store", exist_ok=True)
    import re
    n_bt = len(re.findall(r'<li class="bt-row"', open("bot-templates/index.html", encoding="utf-8").read())) if os.path.exists("bot-templates/index.html") else 189
    canon = f"{B}bot-store/"
    title = clip_title("AgentScout Bot Store — Pre-Trained Grok Bots ($39–$69, $149)")
    desc = clip_text("AI agent skills packs for your business: 5 flagship bots ($39–$149) and 25 role agents with skills, routines, and scripts.", 160)

    body = (
        f'{CSS}'
        f'<div class="crumb"><a href="../index.html">AgentScout</a> / Bot Store</div>'
        f'<section class="bs-hero">'
        f'<span class="bs-compat-pill">⚡ Built Natively for Grok Bot · Also Compatible with Claude Code, Cursor &amp; OpenAI Codex</span>'
        f'<h1>AgentScout Bot Store: Pre-Trained Grok Bots built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"></h1>'
        f'<p>General-purpose bots for running your own SaaS or online business. Set <code>{{{{YOUR_COMPANY}}}}</code> and <code>{{{{YOUR_DOMAIN}}}}</code>, then use them for uptime and inbox monitoring, technical SEO and Core Web Vitals auditing, competitor and launch tracking, and executive team coordination. <b>Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex)</b>: scheduled routines, a shared <code>/workspace/handoff/</code> folder, and a 4-bot <code>Work Chat</code> room. Every ZIP ships <code>SYSTEM.md</code> role prompts, <code>SKILL.md</code> playbooks, standalone Python 3 scripts, <code>mcp.json</code>, and <code>README-QUICKSTART.md</code>.</p>'
        f'<div class="bs-hero-badges">'
        f'<a class="bs-badge" href="#bot-packages" style="border-color:#a3e635;color:#ecfccb">🟢 $39 / 🟡 $59 / 🟠 $59 / 🔴 $69 Individual Bots</a>'
        f'<a class="bs-badge" href="#bundle-package" style="border-color:#34d399;color:#d1fae5">💚 $149 Full 4-Bot Bundle (Save $77)</a>'
        f'<a class="bs-badge" href="#ai-agent-packs" style="border-color:#93c5fd;color:#dbeafe">AI Agent Packs · 25 trained roles</a>'
        f'<a class="bs-badge" href="../bot-templates/#bt-featured">📚 {n_bt} Free Community Bot Templates →</a>'
        f'<a class="bs-badge" href="../videos/#guide-trained-bots">🎬 Watch 60fps Video Walkthrough →</a>'
        f'</div>'
        f'</section>'
        f'<div class="bs-notice">'
        f'<span>📦 <b>WHAT YOU ARE BUYING HERE:</b> Downloadable Pre-Trained AI Bot ZIP Packages (<code>SYSTEM.md</code> + Scheduled Cron Routines + <code>SKILL.md</code> Playbooks + Python 3 Scripts + <code>mcp.json</code> + Single-Organization <code>LICENSE.txt</code>). <b>What\'s inside every .zip:</b> <code>README-QUICKSTART.md</code> (5-minute step-by-step setup guide for Grok Bot, Claude Code, Cursor &amp; OpenAI Codex). The 4-Bot Bundle also includes <code>README-TEAM-BUNDLE.md</code>. <b>Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex).</b> <b>This is NOT a directory listing boost.</b></span>'
        f'<a href="../sponsor.html#packages">Want to list or boost your AI tool in the AgentScout directory instead? ($0 / $29 / $49 / $99) →</a>'
        f'</div>'
        f'<figure class="bs-vid"><video autoplay loop muted playsinline controls preload="metadata" poster="../assets/animations/agentscout-trained-bots-ad-poster.png" width="1200" height="640" style="aspect-ratio:1200/640"><source src="../assets/animations/agentscout-trained-bots-ad.mp4?v=202610280208" type="video/mp4"></video></figure>'
        f'<div class="bs-filters" role="toolbar" aria-label="Filter Bot Store by category">'
        f'<button type="button" class="bs-fbtn" data-filter="all" aria-pressed="true">All Bots (5)</button>'
        f'<button type="button" class="bs-fbtn" data-filter="ops" aria-pressed="false">🟢 Operations &amp; QA</button>'
        f'<button type="button" class="bs-fbtn" data-filter="seo" aria-pressed="false">🟡 SEO &amp; AEO Growth</button>'
        f'<button type="button" class="bs-fbtn" data-filter="intel" aria-pressed="false">🟠 Market &amp; Launch Intel</button>'
        f'<button type="button" class="bs-fbtn" data-filter="exec" aria-pressed="false">🔴 Executive &amp; Full-Stack</button>'
        f'<button type="button" class="bs-fbtn" data-filter="bundle" aria-pressed="false">💚 Multi-Bot Team Bundles</button>'
        f'</div>'
        # Bundle featured highlight
        f'<div id="bundle-package" class="bs-bundle" data-bs-cat="bundle ops seo intel exec">'
        f'<div class="bs-bundle-copy">'
        f'<span class="bs-tag" style="background:rgba(16,185,129,.25);border:1.5px solid #34d399;color:#d1fae5;box-shadow:0 0 12px rgba(16,185,129,.4)">💚 Package #5 · Neon Mint-Emerald · Best Value · Save $77 vs. $226 Separately</span>'
        f'<h2>AgentScout Full 4-Bot "Company-in-a-Box" Team Bundle ($149 One-Time)</h2><div class="bs-builtby">Pre-Trained Pro Bot built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"></div>'
        f'<p>All 4 general-purpose bots for <code>{{{{YOUR_COMPANY}}}}</code> (<code>{{{{YOUR_DOMAIN}}}}</code>) — <b>1. Operations / Monitoring Bot ($39)</b> + <b>2. SEO &amp; AEO Growth Auditor Bot ($59)</b> + <b>3. Market &amp; Launch Intel Bot ($59)</b> + <b>4. CEO Coordinator Bot ($69)</b> — uptime and inbox monitoring, technical SEO and Core Web Vitals, competitor and launch tracking, and executive coordination, sharing one <code>/workspace/handoff/</code> folder, for <b>$149 one-time</b> (saves <b>$77</b> off the $226 individual total).</p>'
        f'<ul class="bs-list"><li><b>What\'s inside every .zip:</b> <code>README-QUICKSTART.md</code> (5-minute step-by-step setup guide for Grok Bot, Claude Code, Cursor &amp; OpenAI Codex)</li><li><b>4-Bot Bundle:</b> <code>README-TEAM-BUNDLE.md</code> shared team handoff and setup guide</li></ul>'
        f'<div class="bs-manifest"><b>📦 Bundle ZIP Manifest:</b> All 4 bot folders + <code>README-QUICKSTART.md</code> (5-minute step-by-step setup guide for Grok Bot, Claude Code, Cursor &amp; OpenAI Codex) + <code>README-TEAM-BUNDLE.md</code> + uptime, inbox, Core Web Vitals, and competitor-watch scripts for <code>{{{{YOUR_COMPANY}}}}</code> + <code>mcp.json</code> + Single-Organization <code>LICENSE.txt</code> (watermarked per order). <b>Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex).</b></div>'
        f'</div>'
        f'<div class="bs-bundle-ctas">'
        f'<a class="bs-btn" href="https://buy.stripe.com/fZueVe5OX7pt1SB6npe7m08" target="_blank" rel="noopener noreferrer" style="background:linear-gradient(135deg,#10b981,#34d399);color:#031811;padding:12px 20px;box-shadow:0 6px 20px rgba(16,185,129,.45)">Buy All 4 Bots Together — $149 (Save $77) →</a>'
        f'<a class="bs-btn" href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer" style="background:rgba(12,10,6,.9);color:#d1fae5;border:1px solid #10b981">Pay $149 via X Money (@clampdown19)</a>'
        f'</div>'
        f'</div>'
        # 4 Individual Bots + Custom Bot Drop Card
        f'<div id="bot-packages" class="bs-grid">'
        # Card 1
        f'<article id="ops-monitoring-bot" class="bs-card neon-lime" data-bs-cat="ops">'
        f'<div><div class="bs-card-top"><span class="bs-price" style="color:#a3e635;text-shadow:0 0 14px rgba(163,230,53,.45)">$39 <small>one-time · sold separately</small></span><span class="bs-tag" style="background:rgba(132,204,22,.22);border:1.5px solid #a3e635;color:#ecfccb;box-shadow:0 0 12px rgba(132,204,22,.4)">🟢 Bot #1 · Neon Lime</span></div>'
        f'<h2>1. AgentScout Operations / Monitoring Bot</h2><div class="bs-builtby">Pre-Trained Pro Bot built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"></div>'
        f'<p>Uptime and inbox monitor for <code>{{{{YOUR_COMPANY}}}}</code>. It checks <code>{{{{YOUR_DOMAIN}}}}</code> on a schedule, triages the support inbox, and recovers failed routines.</p>'
        f'<span class="bs-compat-line">⚡ Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex)</span></div>'
        f'<ul class="bs-list">'
        f'<li><b>Uptime checks:</b> Scheduled HTTP status and response-time checks for <code>{{{{YOUR_DOMAIN}}}}</code></li>'
        f'<li><b>Inbox monitoring:</b> Triages support mail for <code>{{{{YOUR_COMPANY}}}}</code> and drafts replies for you to send</li>'
        f'<li><b>Routine recovery:</b> Notices failed scheduled jobs and writes the next step</li>'
        f'<li><b>What\'s inside every .zip:</b> <code>README-QUICKSTART.md</code> (5-minute step-by-step setup guide for Grok Bot, Claude Code, Cursor &amp; OpenAI Codex)</li>'
        f'</ul>'
        f'<div class="bs-manifest"><b>ZIP Includes:</b> <code>SYSTEM.md</code> · <code>README-QUICKSTART.md</code> · <code>OPS-BOT-HANDOFF.md</code> · <code>SKILL.md</code> · <code>uptime_check.py</code> · <code>inbox_triage.py</code> · <code>mcp.json</code> · <code>LICENSE.txt</code></div>'
        f'<div class="bs-actions">'
        f'<a class="bs-btn" href="https://buy.stripe.com/cNidRa0uDdNRgNvaDFe7m03" target="_blank" rel="noopener noreferrer" style="background:linear-gradient(135deg,#84cc16,#a3e635);color:#081202;box-shadow:0 4px 16px rgba(132,204,22,.45)">Buy AgentScout Operations / Monitoring Bot ($39) →</a>'
        f'<a class="bs-btn" href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer" style="background:rgba(255,255,255,.07);color:#ecfccb;border:1px solid #84cc16">Pay $39 on X Money (@clampdown19)</a>'
        f'</div></article>'
        # Card 2
        f'<article id="seo-aeo-auditor-bot" class="bs-card neon-gold" data-bs-cat="seo">'
        f'<div><div class="bs-card-top"><span class="bs-price" style="color:#facc15;text-shadow:0 0 14px rgba(250,204,21,.45)">$59 <small>one-time · sold separately</small></span><span class="bs-tag" style="background:rgba(234,179,8,.22);border:1.5px solid #facc15;color:#fef9c3;box-shadow:0 0 12px rgba(234,179,8,.4)">🟡 Bot #2 · Neon Gold</span></div>'
        f'<h2>2. AgentScout SEO &amp; AEO Growth Auditor Bot</h2><div class="bs-builtby">Pre-Trained Pro Bot built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"></div>'
        f'<p>Technical SEO and Core Web Vitals auditor for <code>{{{{YOUR_DOMAIN}}}}</code>. It reviews Search Console, page speed, canonicals, and structured data, and notes how answer engines cite <code>{{{{YOUR_COMPANY}}}}</code>.</p>'
        f'<span class="bs-compat-line">⚡ Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex)</span></div>'
        f'<ul class="bs-list">'
        f'<li><b>Core Web Vitals:</b> Checks LCP, INP, and CLS on the key templates of <code>{{{{YOUR_DOMAIN}}}}</code></li>'
        f'<li><b>Technical SEO:</b> Reviews titles, canonicals, indexability, and structured data</li>'
        f'<li><b>Search Console deltas:</b> Flags query and page changes for <code>{{{{YOUR_COMPANY}}}}</code></li>'
        f'<li><b>What\'s inside every .zip:</b> <code>README-QUICKSTART.md</code> (5-minute step-by-step setup guide for Grok Bot, Claude Code, Cursor &amp; OpenAI Codex)</li>'
        f'</ul>'
        f'<div class="bs-manifest"><b>ZIP Includes:</b> <code>SYSTEM.md</code> · <code>README-QUICKSTART.md</code> · <code>SKILL.md</code> · <code>seo_audit.py</code> · <code>cwv_check.py</code> · <code>mcp.json</code> · <code>LICENSE.txt</code></div>'
        f'<div class="bs-actions">'
        f'<a class="bs-btn" href="https://buy.stripe.com/14A7sMfpx6lp9l3aDFe7m05" target="_blank" rel="noopener noreferrer" style="background:linear-gradient(135deg,#eab308,#facc15);color:#141002;box-shadow:0 4px 16px rgba(234,179,8,.45)">Buy AgentScout SEO &amp; AEO Growth Auditor Bot ($59) →</a>'
        f'<a class="bs-btn" href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer" style="background:rgba(255,255,255,.07);color:#fef9c3;border:1px solid #eab308">Pay $59 on X Money (@clampdown19)</a>'
        f'</div></article>'
        # Card 3
        f'<article id="market-launch-intel-bot" class="bs-card neon-orange" data-bs-cat="intel">'
        f'<div><div class="bs-card-top"><span class="bs-price" style="color:#fb923c;text-shadow:0 0 14px rgba(251,146,60,.45)">$59 <small>one-time · sold separately</small></span><span class="bs-tag" style="background:rgba(249,115,22,.22);border:1.5px solid #fb923c;color:#ffedd5;box-shadow:0 0 12px rgba(249,115,22,.4)">🟠 Bot #3 · Neon Sunset Orange</span></div>'
        f'<h2>3. AgentScout Market &amp; Launch Intel Bot</h2><div class="bs-builtby">Pre-Trained Pro Bot built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"></div>'
        f'<p>Competitor and launch tracker for <code>{{{{YOUR_COMPANY}}}}</code>. It watches rival products, pricing pages, and public launches, then files a morning brief.</p>'
        f'<span class="bs-compat-line">⚡ Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex)</span></div>'
        f'<ul class="bs-list">'
        f'<li><b>Competitor watch:</b> Tracks rival launches, pricing-page changes, and positioning for <code>{{{{YOUR_COMPANY}}}}</code></li>'
        f'<li><b>Launch radar:</b> Notes public launches (Product Hunt, Hacker News, and the open web) with source URLs</li>'
        f'<li><b>Morning brief:</b> Writes what changed overnight and which claims on <code>{{{{YOUR_DOMAIN}}}}</code> look stale</li>'
        f'<li><b>What\'s inside every .zip:</b> <code>README-QUICKSTART.md</code> (5-minute step-by-step setup guide for Grok Bot, Claude Code, Cursor &amp; OpenAI Codex)</li>'
        f'</ul>'
        f'<div class="bs-manifest"><b>ZIP Includes:</b> <code>SYSTEM.md</code> · <code>README-QUICKSTART.md</code> · <code>SKILL.md</code> · <code>competitor_watch.py</code> · <code>launch_radar.py</code> · <code>mcp.json</code> · <code>LICENSE.txt</code></div>'
        f'<div class="bs-actions">'
        f'<a class="bs-btn" href="https://buy.stripe.com/4gM8wQelt11568RaDFe7m06" target="_blank" rel="noopener noreferrer" style="background:linear-gradient(135deg,#f97316,#fb923c);color:#140702;box-shadow:0 4px 16px rgba(249,115,22,.45)">Buy AgentScout Market &amp; Launch Intel Bot ($59) →</a>'
        f'<a class="bs-btn" href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer" style="background:rgba(255,255,255,.07);color:#ffedd5;border:1px solid #f97316">Pay $59 on X Money (@clampdown19)</a>'
        f'</div></article>'
        # Card 4
        f'<article id="ceo-coordinator-bot" class="bs-card neon-red" data-bs-cat="exec">'
        f'<div><div class="bs-card-top"><span class="bs-price" style="color:#f87171;text-shadow:0 0 14px rgba(248,113,113,.45)">$69 <small>one-time · sold separately</small></span><span class="bs-tag" style="background:rgba(239,68,68,.22);border:1.5px solid #f87171;color:#fee2e2;box-shadow:0 0 12px rgba(239,68,68,.4)">🔴 Bot #4 · Neon Crimson Red</span></div>'
        f'<h2>4. AgentScout CEO Coordinator Bot</h2><div class="bs-builtby">Pre-Trained Pro Bot built by <span class="sr-only">AgentScout</span><img class="aswm" src="../logo-wordmark.svg" alt="" aria-hidden="true" width="168" height="32"></div>'
        f'<p>Executive coordinator for <code>{{{{YOUR_COMPANY}}}}</code>. It reads the uptime, SEO, and competitor briefs and writes the daily plan for the team.</p>'
        f'<span class="bs-compat-line">⚡ Built for Grok Bot (also compatible with Claude Code, Cursor &amp; Codex)</span></div>'
        f'<ul class="bs-list">'
        f'<li><b>Team coordination:</b> Assigns follow-ups to the ops, SEO, and market bots through <code>/workspace/handoff/</code> and <code>Work Chat</code></li>'
        f'<li><b>Daily executive brief:</b> One plan for <code>{{{{YOUR_COMPANY}}}}</code> from the overnight checks</li>'
        f'<li><b>Owner queue:</b> Lists decisions that still need a person, with the source note attached</li>'
        f'<li><b>What\'s inside every .zip:</b> <code>README-QUICKSTART.md</code> (5-minute step-by-step setup guide for Grok Bot, Claude Code, Cursor &amp; OpenAI Codex)</li>'
        f'</ul>'
        f'<div class="bs-manifest"><b>ZIP Includes:</b> <code>SYSTEM.md</code> · <code>README-QUICKSTART.md</code> · <code>daily_brief.md</code> · team handoff notes · <code>mcp.json</code> · <code>LICENSE.txt</code></div>'
        f'<div class="bs-actions">'
        f'<a class="bs-btn" href="https://buy.stripe.com/9B69AU2CLh031SB8vxe7m07" target="_blank" rel="noopener noreferrer" style="background:linear-gradient(135deg,#ef4444,#f87171);color:#fff;box-shadow:0 4px 16px rgba(239,68,68,.45)">Buy AgentScout CEO Coordinator Bot ($69) →</a>'
        f'<a class="bs-btn" href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer" style="background:rgba(255,255,255,.07);color:#fee2e2;border:1px solid #ef4444">Pay $69 on X Money (@clampdown19)</a>'
        f'</div></article>'
        # Expansion card: Request a Custom Bot / Next Bot Drop
        f'<article id="custom-bot-drop" class="bs-card neon-custom" data-bs-cat="all ops seo intel exec bundle" style="grid-column:1 / -1">'
        f'<div class="bs-card-top"><span class="bs-price" style="color:#d8b4fe;font-size:20px">🚀 Next Bot Drop / Custom Bot Build</span><span class="bs-tag" style="background:rgba(168,85,247,.22);border:1.5px solid #c084fc;color:#f3e8ff">New Bots Added Regularly</span></div>'
        f'<h2>Need a Custom Pre-Trained Grok Bot or Specialized Multi-Agent Team?</h2>'
        f'<p>We are expanding the AgentScout Bot Store with new domain-specific Grok Bots (GitHub PR Reviewer Bot, Founder Outbound CRM Bot, Beehiiv Newsletter Editor Bot, and Security Watchtower Bot). Want early access to the next drop or a custom-trained bot wired for your stack?</p>'
        f'<div class="bs-actions">'
        f'<a class="bs-btn" href="mailto:support@agentscouthq.com?subject=Custom%20Bot%20Request%20%2F%20Next%20Bot%20Drop" style="background:rgba(168,85,247,.22);border:1.5px solid #c084fc;color:#f3e8ff;flex:0 1 auto">Request a Custom Bot (support@agentscouthq.com) →</a>'
        f'<a class="bs-btn" href="../bot-templates/#bt-featured" style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);color:#e5e7eb;flex:0 1 auto">Browse {n_bt} Free Community Bot Templates →</a>'
        f'</div></article>'
        f'</div>'
        f'{pack_section_html()}'
        # FAQ & Platform Compatibility Box
        f'<section class="bs-faq" aria-labelledby="bs-faq-h">'
        f'<h2 id="bs-faq-h">What Platform Do These Run On? (Compatibility, Delivery &amp; License FAQ)</h2>'
        f'<div class="bs-faq-grid">'
        f'<div class="bs-faq-item"><h3>What platform are AgentScout Bot Store packages built for?</h3><p>They are built natively for Grok Bot first (where 24/7 scheduled cron routines, the shared /workspace/handoff/ computer, Gmail/X connectors, and 4-bot Work Chat team coordination run turnkey out of the box), and because each ZIP ships standard SYSTEM.md role prompts, SKILL.md playbooks, standalone Python 3 scripts, and mcp.json, they are also compatible with Claude Code, Cursor, and OpenAI Codex.</p></div>'
        f'<div class="bs-faq-item"><h3>How is the Bot Store different from AgentScout Directory Listing packages?</h3><p>The Bot Store ($39, $59, $59, $69 individual bots and $149 4-Bot Bundle) sells downloadable pre-trained AI bot configurations and scripts you run in your own workspace. Directory Listing packages ($0 Free, $29 Fast-Track, $49 Category Pin, $99/wk Sitewide Sponsor) list and promote your AI software tool on agentscouthq.com.</p></div>'
        f'<div class="bs-faq-item"><h3>3. Instant Delivery + Single-Organization Commercial License</h3><p>After Stripe Checkout (or X Money payment to <a href="https://x.com/clampdown19" target="_blank" rel="noopener noreferrer">@clampdown19</a>), you receive the complete ZIP package with a Single-Organization Commercial License (<code>LICENSE.txt</code>) and a cryptographic per-buyer order watermark so your whole internal team can run and customize the bots.</p></div>'
        f'<div class="bs-faq-item"><h3>4. Free Community Templates vs. Directory Listing Boosts</h3><p>Looking for free starter prompts? Explore <a href="../bot-templates/#bt-featured">{n_bt} free community bot templates</a>. Looking to list or feature your AI software product in the AgentScout directory instead? See our <a href="../sponsor.html#packages">4 Directory Listing Packages ($0 / $29 / $49 / $99)</a>.</p></div>'
        f'</div>'
        f'</section>{JS}'
    )

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": canon + "#webpage",
                "name": title,
                "description": desc,
                "url": canon,
                "isPartOf": {"@type": "WebSite", "name": "AgentScout", "url": B}
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "AgentScout", "item": B},
                    {"@type": "ListItem", "position": 2, "name": "Bot Store", "item": canon}
                ]
            },
            {
                "@type": "VideoObject",
                "name": "AgentScout Bot Store: 4 Pre-Trained Grok Bots ($39/$59/$59/$69) & $149 4-Bot Team Bundle",
                "description": "60fps showcase of the 4 downloadable pre-trained AgentScout bots and the $149 Full 4-Bot Company-in-a-Box Team Bundle. Built for Grok Bot and compatible with Claude Code, Cursor, and OpenAI Codex.",
                "thumbnailUrl": B + "assets/animations/agentscout-trained-bots-ad-poster.png",
                "contentUrl": B + "assets/animations/agentscout-trained-bots-ad.mp4",
                "uploadDate": "2026-10-28T02:00:00-07:00",
                "duration": "PT20S"
            },
            {
                "@type": "ItemList",
                "name": "AgentScout Pre-Trained Pro Bots & 4-Bot Team Bundle",
                "numberOfItems": 5,
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "item": {
                            "@type": "Product",
                            "name": "1. AgentScout Operations / Monitoring Bot",
                            "sku": "as-bot-ops-39",
                            "brand": {"@type": "Organization", "name": "AgentScout", "url": "https://agentscouthq.com"},
                            "description": "General-purpose uptime and inbox monitor for {{YOUR_COMPANY}} ({{YOUR_DOMAIN}}). Built for Grok Bot (also compatible with Claude Code, Cursor & Codex).",
                            "offers": {"@type": "Offer", "price": "39.00", "priceCurrency": "USD", "availability": "https://schema.org/InStock", "url": "https://buy.stripe.com/cNidRa0uDdNRgNvaDFe7m03"}
                        }
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "item": {
                            "@type": "Product",
                            "name": "2. AgentScout SEO & AEO Growth Auditor Bot",
                            "sku": "as-bot-seo-aeo-59",
                            "brand": {"@type": "Organization", "name": "AgentScout", "url": "https://agentscouthq.com"},
                            "description": "General-purpose technical SEO and Core Web Vitals auditor for {{YOUR_DOMAIN}}. Built for Grok Bot (also compatible with Claude Code, Cursor & Codex).",
                            "offers": {"@type": "Offer", "price": "59.00", "priceCurrency": "USD", "availability": "https://schema.org/InStock", "url": "https://buy.stripe.com/14A7sMfpx6lp9l3aDFe7m05"}
                        }
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "item": {
                            "@type": "Product",
                            "name": "3. AgentScout Market & Launch Intel Bot",
                            "sku": "as-bot-market-intel-59",
                            "brand": {"@type": "Organization", "name": "AgentScout", "url": "https://agentscouthq.com"},
                            "description": "General-purpose competitor and launch tracker for {{YOUR_COMPANY}}. Built for Grok Bot (also compatible with Claude Code, Cursor & Codex).",
                            "offers": {"@type": "Offer", "price": "59.00", "priceCurrency": "USD", "availability": "https://schema.org/InStock", "url": "https://buy.stripe.com/4gM8wQelt11568RaDFe7m06"}
                        }
                    },
                    {
                        "@type": "ListItem",
                        "position": 4,
                        "item": {
                            "@type": "Product",
                            "name": "4. AgentScout CEO Coordinator Bot",
                            "sku": "as-bot-ceo-69",
                            "brand": {"@type": "Organization", "name": "AgentScout", "url": "https://agentscouthq.com"},
                            "description": "General-purpose executive coordinator for {{YOUR_COMPANY}}. Built for Grok Bot (also compatible with Claude Code, Cursor & Codex).",
                            "offers": {"@type": "Offer", "price": "69.00", "priceCurrency": "USD", "availability": "https://schema.org/InStock", "url": "https://buy.stripe.com/9B69AU2CLh031SB8vxe7m07"}
                        }
                    },
                    {
                        "@type": "ListItem",
                        "position": 5,
                        "item": {
                            "@type": "Product",
                            "name": "AgentScout Full 4-Bot Company-in-a-Box Team Bundle",
                            "sku": "as-bot-bundle-149",
                            "brand": {"@type": "Organization", "name": "AgentScout", "url": "https://agentscouthq.com"},
                            "description": "All 4 general-purpose bots for {{YOUR_COMPANY}} ({{YOUR_DOMAIN}}): uptime, technical SEO and Core Web Vitals, competitor tracking, and executive coordination. $149 (Save $77). Built for Grok Bot (also compatible with Claude Code, Cursor & Codex).",
                            "offers": {"@type": "Offer", "price": "149.00", "priceCurrency": "USD", "availability": "https://schema.org/InStock", "url": "https://buy.stripe.com/fZueVe5OX7pt1SB6npe7m08"}
                        }
                    }
                ]
            },
            {
                "@type": "SoftwareApplication",
                "name": "AgentScout Bot Store",
                "applicationCategory": "BusinessApplication",
                "operatingSystem": "Grok Bot, Claude Code, Cursor, Codex",
                "url": canon,
                "author": {"@type": "Organization", "name": "AgentScout", "url": "https://agentscouthq.com"},
                "brand": {"@type": "Organization", "name": "AgentScout", "url": "https://agentscouthq.com"},
                "offers": {"@type": "AggregateOffer", "lowPrice": "39.00", "highPrice": "149.00", "priceCurrency": "USD", "offerCount": 30}
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": "What platform are AgentScout Bot Store packages built for?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "They are built natively for Grok Bot first (where 24/7 scheduled cron routines, the shared /workspace/handoff/ computer, Gmail/X connectors, and 4-bot Work Chat team coordination run turnkey out of the box), and because each ZIP ships standard SYSTEM.md role prompts, SKILL.md playbooks, standalone Python 3 scripts, and mcp.json, they are also compatible with Claude Code, Cursor, and OpenAI Codex."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": "How is the Bot Store different from AgentScout Directory Listing packages?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "The Bot Store ($39, $59, $59, $69 individual bots and $149 4-Bot Bundle) sells downloadable pre-trained AI bot configurations and scripts you run in your own workspace. Directory Listing packages ($0 Free, $29 Fast-Track, $49 Category Pin, $99/wk Sitewide Sponsor) list and promote your AI software tool on agentscouthq.com."
                        }
                    }
                ]
            }
        ]
    }
    open("bot-store/index.html", "w", encoding="utf-8").write(shell("../", title, desc, canon, body, ld))
    from pack_pages import write_pack_pages
    pack_urls = write_pack_pages()
    import build_openapi
    build_openapi.sync_products_snapshot()
    return [canon] + pack_urls
