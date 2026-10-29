#!/usr/bin/env python3
"""Email section and X posts for the 25 role packs and the flagship Bot Store."""
from __future__ import annotations

import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_pack_catalog import AGENTS, PACK_TIERS, STRIPE, TIER_PILLS  # noqa: E402

OUT = ROOT / "data" / "outreach"
FLAGSHIP = (
    ("Operations / Monitoring Bot", 39, STRIPE["ops"]["url"], "Ops & Admin"),
    ("SEO & AEO Growth Auditor Bot", 59, STRIPE["seo"]["url"], "Marketing"),
    ("Market & Launch Intel Bot", 59, STRIPE["mkt"]["url"], "Sales"),
    ("CEO Coordinator Bot", 69, STRIPE["ceo"]["url"], "Product"),
    ("4-Bot Company-in-a-Box", 149, STRIPE["bundle"]["url"], "Bundle"),
)


def _e(value: str) -> str:
    return html.escape(value, quote=True)


def email_html() -> str:
    tiers = "".join(
        f'<span style="display:inline-block;margin:4px 6px 0 0;padding:6px 10px;border-radius:999px;background:#172033;color:#e0f2fe;border:1px solid #334155;font:700 12px/1.3 Arial,sans-serif">{_e(TIER_PILLS[row["count"]])}</span>'
        for row in PACK_TIERS.values()
    )
    flagship = []
    for name, price, url, dept in FLAGSHIP:
        flagship.append(
            "<tr>"
            f'<td style="padding:10px;border-bottom:1px solid #243044;color:#fff;font:700 14px Arial">{_e(name)}</td>'
            f'<td style="padding:10px;border-bottom:1px solid #243044;color:#93c5fd">{_e(dept)}</td>'
            f'<td style="padding:10px;border-bottom:1px solid #243044;color:#fff">${price}</td>'
            f'<td style="padding:10px;border-bottom:1px solid #243044"><a href="{_e(url)}" style="color:#052e16;background:#10b981;text-decoration:none;padding:6px 10px;border-radius:999px;font-weight:800">Stripe</a> '
            '<a href="https://x.com/clampdown19" style="color:#e4e4e7">X Money</a></td>'
            "</tr>"
        )
    rows = []
    for agent in AGENTS:
        chips = " · ".join(agent["chips"][:3])
        rows.append(
            "<tr>"
            f'<td style="padding:10px 8px;border-bottom:1px solid #243044;color:#fff;font:700 14px Arial">{_e(agent["card_title"])}<br>'
            f'<span style="color:#a1a1aa;font-weight:600">built by AgentScout</span></td>'
            f'<td style="padding:10px 8px;border-bottom:1px solid #243044;color:#93c5fd">{_e(agent["dept_short"])}</td>'
            f'<td style="padding:10px 8px;border-bottom:1px solid #243044;color:#d4d4d8">{_e(agent["promise"])}<br><span style="color:#e4e4e7">{_e(chips)}</span></td>'
            '<td style="padding:10px 8px;border-bottom:1px solid #243044;color:#fff">$35</td>'
            "</tr>"
        )
    return f"""<section style="background:#0e1118;color:#e4e4e7;padding:20px;border-radius:18px;border:1px solid #334155;font-family:Arial,sans-serif">
  <p style="margin:0 0 6px;font-size:13px">built by AgentScout</p>
  <h2 style="margin:0 0 8px;color:#fff">Bot Store · 4 flagship bots and 25 role packs</h2>
  <p style="margin:0 0 12px;color:#d4d4d8;line-height:1.5">Flagship Pro Bots stay $39 / $59 / $59 / $69, or $149 for the 4-Bot bundle. Role packs are a separate ladder: $35 each, 5 for $119, 10 for $199, 20 for $299, all 25 for $349.</p>
  <div>{tiers}</div>
  <h3 style="color:#fff">Flagship bots</h3>
  <table style="width:100%;border-collapse:collapse">{''.join(flagship)}</table>
  <h3 style="color:#fff">25 AI Agent Packs · $35</h3>
  <table style="width:100%;border-collapse:collapse">{''.join(rows)}</table>
  <p style="margin:14px 0 0"><a href="https://agentscouthq.com/bot-store/#ap-dock" style="color:#93c5fd">Build a pack on the Bot Store</a> · <a href="https://x.com/clampdown19" style="color:#93c5fd">Pay via X Money @clampdown19</a></p>
</section>
"""


def x_posts() -> str:
    posts = []
    master = (
        "25 AI Agent Packs, built by AgentScout. $35 each, or 5 for $119, 10 for $199, "
        "20 for $299, all 25 for $349. Lead Gen Agent, Outreach Agent, and Meta Ads Agent "
        "are in the set. Offline. Zero telemetry. https://agentscouthq.com/bot-store/#ai-agent-packs"
    )
    posts.append(master)
    for key in ("sales", "marketing", "ops", "product"):
        group = [a for a in AGENTS if a["dept"] == key]
        names = ", ".join(a["card_title"] for a in group[:4])
        extra = len(group) - 4
        more = f" +{extra} more" if extra > 0 else ""
        text = (
            f"{group[0]['dept_label']} packs, built by AgentScout. {names}{more}. "
            f"{group[0]['tagline']}. $35 each or the volume ladder to $349. "
            "https://agentscouthq.com/bot-store/#ai-agent-packs"
        )
        posts.append(text)
    lines = []
    for i, post in enumerate(posts, start=1):
        if "Agent Agent" in post:
            raise SystemExit(post)
        lines.append(f"## Post {i} ({len(post)} chars)\n\n{post}\n")
    return "\n".join(lines)


def write_poster() -> Path | None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("poster skipped: Pillow is not installed")
        return None
    font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    font_s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    font_m = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    width = 1080
    row_h = 52
    height = 168 + len(AGENTS) * row_h + 90
    image = Image.new("RGB", (width, height), (14, 17, 24))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((16, 16, width - 16, height - 16), 24, outline=(147, 197, 253), width=2)
    draw.text((36, 32), "25 AI Agent Packs", font=font_b, fill=(255, 255, 255))
    draw.text((36, 64), "built by AgentScout  ·  $35 each  ·  5 $119  ·  10 $199  ·  20 $299  ·  25 $349", font=font_s, fill=(212, 212, 216))
    y = 110
    for agent in AGENTS:
        color = tuple(int(agent["color"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        draw.rounded_rectangle((32, y, width - 32, y + row_h - 8), 12, fill=(22, 26, 36), outline=color, width=2)
        draw.text((46, y + 6), agent["card_title"], font=font_s, fill=(255, 255, 255))
        draw.text((360, y + 8), f"${agent['price']}  {agent['dept_short']}", font=font_m, fill=color)
        blurb = agent["tagline"]
        if len(blurb) > 62:
            blurb = blurb[:59] + "..."
        draw.text((46, y + 26), blurb, font=font_m, fill=(212, 212, 216))
        y += row_h
    draw.text((36, height - 58), "agentscouthq.com/bot-store  ·  X Money @clampdown19", font=font_s, fill=(251, 191, 36))
    dest = OUT / "25-agent-packs-poster.png"
    image.save(dest)
    return dest


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "25-agent-packs-email.html").write_text(email_html(), encoding="utf-8")
    (OUT / "25-agent-packs-x-posts.md").write_text(x_posts(), encoding="utf-8")
    poster = write_poster()
    print("wrote", OUT, poster.stat().st_size if poster else "no poster")


if __name__ == "__main__":
    main()
