#!/usr/bin/env python3
"""Publish the MCP test-report product page, the sample private report, and the price feed rows.

Run from the repo root:

    python3 tools/report-kit/publish_site.py

Prices and Stripe links are read only from data/mcp_test_report.json.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))
sys.path.insert(0, str(ROOT))

import build_report  # noqa: E402
import catalog  # noqa: E402
import csp as site_csp  # noqa: E402

CSS_V = "202611111902"
ASSET_V = re.search(r'ASSET_V = "(\d+)"', (ROOT / "build_tasks.py").read_text(encoding="utf-8")).group(1)
PAYNOTE = (
    '<p class="paynote" style="flex:1 1 100%;min-width:0;max-width:100%;width:100%;box-sizing:border-box;margin:8px auto 0;white-space:normal;overflow-wrap:anywhere;'
    'font-size:13px;line-height:1.45;text-align:center;color:var(--muted)">'
    "EU and UK buyers: paying starts delivery right away, which ends the 14-day cancellation right. "
    '<a href="refunds.html">Refund policy</a>.</p>'
)
SKIP_WALK = {".git", "node_modules", "preview", "data", "pagefind", "assets", "scripts", "bot-packages", "r", "__pycache__"}


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def png_size(path: Path) -> tuple[int, int]:
    raw = path.read_bytes()
    return struct.unpack(">II", raw[16:24])


def copy_assets() -> None:
    dest = ROOT / "assets" / "mcp-report"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(KIT / "report.css", dest / "report.css")
    logo = dest / "logo"
    logo.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(KIT / "assets" / "logo" / "logo-mark-dark.svg", logo / "logo-mark-dark.svg")
    fonts = dest / "assets" / "fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    for font in (KIT / "assets" / "fonts").glob("inter-*.ttf"):
        shutil.copyfile(font, fonts / font.name)


def render_sample(doc: dict) -> str:
    token = doc["sample_slug"]
    if len(token) < 24:
        raise SystemExit("sample token must be at least 24 characters")
    transcript = json.loads((KIT / "samples" / "mcp-test-report-sample-2026-11-11.transcript.json").read_text(encoding="utf-8"))
    scorecard = json.loads((KIT / "sample-scorecard.json").read_text(encoding="utf-8"))
    model = build_report.build_model(transcript, scorecard)
    badge = build_report.build_badge_svg(scorecard["score"], scorecard["score_max"], scorecard["badge_date"])
    public_badge = ROOT / "assets" / "mcp-report" / "badge.svg"
    public_badge.write_text(badge, encoding="utf-8")
    (KIT / "badge-sample.svg").write_text(badge, encoding="utf-8")

    report_dir = ROOT / "r" / token
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "badge.svg").write_text(badge, encoding="utf-8")
    shutil.copyfile(KIT / "samples" / "mcp-test-report-sample-2026-11-11.pdf", report_dir / "report.pdf")

    page = build_report.render_html(model, web={
        "fit": True,
        "logo_src": "/assets/mcp-report/logo/logo-mark-dark.svg",
        "badge_src": "badge.svg",
        "css_href": f"/assets/mcp-report/report.css?v={CSS_V}",
        "robots": "noindex, nofollow",
        "csp": site_csp.POLICY,
        "referrer": "strict-origin-when-cross-origin",
        "pdf_href": "report.pdf",
    })
    (report_dir / "index.html").write_text(page, encoding="utf-8")

    previews = ROOT / "assets" / "mcp-report" / "previews"
    previews.mkdir(parents=True, exist_ok=True)
    for old in previews.glob("page-*.png"):
        old.unlink()
    subprocess.run(
        ["pdftoppm", "-png", "-scale-to", "900", str(report_dir / "report.pdf"), str(previews / "page")],
        check=True,
    )
    return token


def _offer_card(product: dict, doc: dict) -> str:
    price, url = catalog.selling(product, doc)
    regular = int(product["price"])
    strike = ""
    if price != regular:
        strike = f'<s class="was">${regular}</s>'
    label = "Buy the bundle" if product["id"] == "bundle" else "Buy the MCP server test report"
    return (
        f'<article class="report-offer">'
        f'<h2>{esc(product["name"])}</h2>'
        f'<p>{esc(product["blurb"])}</p>'
        f'<p class="report-price"><span class="now">${price}</span>{strike}</p>'
        f'<a class="btn primary" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'
        f'{PAYNOTE}'
        f'</article>'
    )


def product_main(doc: dict, token: str) -> str:
    shown = [p for p in doc["products"] if p.get("on_page")]
    cards = "".join(_offer_card(p, doc) for p in shown)
    email = doc["questions_email"]
    scorecard = json.loads((KIT / "sample-scorecard.json").read_text(encoding="utf-8"))
    steps = "".join(f"<li>{esc(step)}</li>" for step in scorecard["methodology"])
    areas = "".join(f"<li>{esc(row['area'])}</li>" for row in scorecard["scorecard"])
    previews = sorted((ROOT / "assets" / "mcp-report" / "previews").glob("page-*.png"))
    figures = []
    for path in previews:
        width, height = png_size(path)
        n = path.stem.split("-")[-1]
        figures.append(
            f'<figure><img src="assets/mcp-report/previews/{esc(path.name)}" alt="Sample report page {esc(n)}" '
            f'width="{width}" height="{height}" loading="lazy" decoding="async"><figcaption>Page {esc(n)}</figcaption></figure>'
        )
    badge_date = scorecard["badge_date"]
    score = f'{scorecard["score"]}/{scorecard["score_max"]}'
    alt = f"Tested by AgentScout · {score} · {badge_date}"
    badge_url = "https://agentscouthq.com/assets/mcp-report/badge.svg"
    listing = "https://agentscouthq.com/tools/microsoft-learn-mcp.html"
    html_snip = (
        f'<a href="{listing}" target="_blank" rel="noopener noreferrer">'
        f'<img src="{badge_url}" alt="{alt}. Dated test result, not an endorsement." width="440"></a>'
    )
    md_snip = f"[![{alt}]({badge_url})]({listing})"
    sample_page = f"r/{token}/"
    sample_pdf = f"r/{token}/report.pdf"
    return f'''<div class="crumb"><a href="index.html">AgentScout</a> / MCP server test report</div>
<section class="calm">
<h1 style="text-align:left" data-pagefind-weight="10">MCP server test report</h1>
<p class="lede" style="margin-left:0;text-align:left">A written test of one public MCP server: we connect over the protocol, call the safe read-only tools, time the round trips, and score the schema. You get a private page, a PDF, and a dated badge.</p>
<p>For how a site shows up in AI answers, see the <a href="ai-visibility-check.html">AI visibility check</a>.</p>
<p class="report-intro">{esc(doc["intro"]["note"])}</p>
<div class="report-offers">{cards}</div>
<p class="report-ask"><a href="mailto:{esc(email)}">Questions? Email {esc(email)}</a></p>
<h2 style="font-size:19px;margin:28px 0 8px">What is tested</h2>
<p>The score covers these areas:</p>
<ul>{areas}</ul>
<p>The run itself is:</p>
<ol>{steps}</ol>
<p>Authenticated servers, stdio installs, and write or payment tools are out of scope. The booking link inside a delivered report stays a placeholder until a calendar exists.</p>
<h2 style="font-size:19px;margin:28px 0 8px">Sample report</h2>
<p>This sample is Microsoft Learn MCP, tested November 11, 2026. The private page is not in the sitemap. The PDF is the same nine pages.</p>
<p><a href="{esc(sample_page)}">Open the sample report</a> · <a href="{esc(sample_pdf)}">Download the sample PDF</a></p>
<div class="report-pages">{''.join(figures)}</div>
<h2 style="font-size:19px;margin:28px 0 8px">Tested by AgentScout badge</h2>
<p>The badge is generated from the score and the test date. It is a dated result, not an endorsement.</p>
<div class="report-badge"><img src="assets/mcp-report/badge.svg" alt="{esc(alt)}" width="440" height="64"></div>
<div class="report-snippets">
<div><h3 style="font-size:15px;margin:0 0 6px">HTML</h3><textarea readonly rows="4" aria-label="HTML badge snippet" onclick="this.select()">{esc(html_snip)}</textarea></div>
<div><h3 style="font-size:15px;margin:0 0 6px">Markdown</h3><textarea readonly rows="4" aria-label="Markdown badge snippet" onclick="this.select()">{esc(md_snip)}</textarea></div>
</div>
</section>'''


def write_product_page(doc: dict, token: str) -> None:
    src = (ROOT / "badges.html").read_text(encoding="utf-8")
    title = "MCP server test report · AgentScout"
    desc = "Protocol test of a public MCP server, with a private report, PDF, and dated badge. Intro $79 ($99 regular). Bundle with an AI visibility check $119 ($149 regular)."
    src = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", src, count=1, flags=re.S)
    src = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + esc(desc) + m.group(2), src, count=1)
    src = re.sub(r'(<link rel="canonical" href=")[^"]*(")', lambda m: m.group(1) + "https://agentscouthq.com/mcp-test-report.html" + m.group(2), src, count=1)
    for prop in ("og:title", "og:description", "og:url", "twitter:title", "twitter:description"):
        value = {
            "og:title": title,
            "og:description": desc,
            "og:url": "https://agentscouthq.com/mcp-test-report.html",
            "twitter:title": title,
            "twitter:description": desc,
        }[prop]
        name = "property" if prop.startswith("og:") else "name"
        src = re.sub(
            rf'(<meta {name}="{prop}" content=")[^"]*(")',
            lambda m, v=value: m.group(1) + esc(v) + m.group(2),
            src,
            count=1,
        )
    ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": desc,
        "url": "https://agentscouthq.com/mcp-test-report.html",
    }
    blob = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")

    def _swap_ld(match):
        raw = match.group(1)
        if '"@type": "WebPage"' in raw or '"@type":"WebPage"' in raw:
            return '<script type="application/ld+json">' + blob + "</script>"
        return match.group(0)

    src = re.sub(r'<script type="application/ld\+json">(.*?)</script>', _swap_ld, src, count=2, flags=re.S)
    css = f'<link rel="stylesheet" href="mcp-test-report.css?v={CSS_V}">'
    if "mcp-test-report.css" not in src:
        src = src.replace(f'href="styles.css?v={ASSET_V}">', f'href="styles.css?v={ASSET_V}">' + css, 1)
    main = product_main(doc, token)
    src = re.sub(r"(<main class=\"wrap\" data-pagefind-body>).*(</main>)", lambda m: m.group(1) + main + m.group(2), src, count=1, flags=re.S)
    (ROOT / "mcp-test-report.html").write_text(src, encoding="utf-8")


def stamp_links() -> int:
    changed = 0
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_WALK and not d.startswith(".")]
        for name in files:
            if not name.endswith(".html"):
                continue
            path = Path(dirpath) / name
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8", errors="replace")
            if "<nav" not in text and "<footer" not in text:
                continue
            new = _insert_link(text)
            if new != text:
                path.write_text(new, encoding="utf-8")
                changed += 1
                rel = rel  # kept for debugging
    return changed


def _prefix_from(chunk: str) -> str:
    match = re.search(r'href="([^"]*)mcp/status/"', chunk)
    return match.group(1) if match else ""


def _insert_link(text: str) -> str:
    def nav(match):
        body = match.group(2)
        if "mcp-test-report.html" in body:
            return match.group(0)
        prefix = _prefix_from(body)
        link = f'<a href="{prefix}mcp-test-report.html">MCP server test</a>'
        return match.group(1) + body + link + match.group(3)

    text = re.sub(
        r'(<summary>MCP</summary><div class="navpanel">)(.*?)(</div></details>)',
        nav,
        text,
        count=1,
        flags=re.S,
    )

    def foot(match):
        body = match.group(2)
        if "mcp-test-report.html" in body:
            return match.group(0)
        prefix = _prefix_from(body) or _prefix_from(match.group(0))
        if not prefix and 'href="categories/mcp-servers.html"' not in body and 'href="../categories/mcp-servers.html"' not in body and 'href="/categories/mcp-servers.html"' not in body:
            href = re.search(r'href="([^"]*)categories/mcp-servers.html"', body)
            prefix = href.group(1) if href else ""
        link = f'<a href="{prefix}mcp-test-report.html">MCP server test</a>'
        return match.group(1) + body + link + match.group(3)

    text = re.sub(
        r'(<div class="footcol"><h2>MCP</h2>)(.*?)(</div>)',
        foot,
        text,
        count=1,
        flags=re.S,
    )
    return text


def patch_mcp_index() -> None:
    path = ROOT / "mcp" / "index.html"
    text = path.read_text(encoding="utf-8")
    needle = 'Use AgentScout from your AI client: <a href="connect.html">connect to the free AgentScout MCP server</a>.'
    extra = needle + '</p><p style="font-size:14px"><a href="../mcp-test-report.html">MCP server test report</a>: a protocol test of a public MCP server, with a private page and PDF.'
    if needle in text and "protocol test of a public MCP server" not in text:
        text = text.replace(needle, extra, 1)
        path.write_text(text, encoding="utf-8")


def patch_sitemap(doc_has_page: bool = True) -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    loc = "https://agentscouthq.com/mcp-test-report.html"
    if loc not in text:
        row = f"  <url><loc>{loc}</loc><lastmod>2026-11-11</lastmod></url>\n"
        text = text.replace(
            "  <url><loc>https://agentscouthq.com/how-it-started.html</loc><lastmod>2026-11-10</lastmod></url>\n",
            "  <url><loc>https://agentscouthq.com/how-it-started.html</loc><lastmod>2026-11-10</lastmod></url>\n" + row,
            1,
        )
    if "/r/" in text:
        raise SystemExit("sitemap.xml contains a private report URL")
    path.write_text(text, encoding="utf-8")
    llms = ROOT / "llms.txt"
    llm = llms.read_text(encoding="utf-8")
    line = "- [MCP server test report](https://agentscouthq.com/mcp-test-report.html): protocol test of a public MCP server, with a private page, PDF, and dated badge\n"
    if "mcp-test-report.html" not in llm:
        llm = llm.replace("- [Badges](https://agentscouthq.com/badges.html)\n", "- [Badges](https://agentscouthq.com/badges.html)\n" + line, 1)
        llms.write_text(llm, encoding="utf-8")


def patch_refunds(doc: dict) -> None:
    path = ROOT / "refunds.html"
    text = path.read_text(encoding="utf-8")
    desc = "Refunds for the $15 fast-track listing, sponsorships, Bot Store downloads, and paid reports. Email support@agentscouthq.com to ask."
    text = text.replace(
        "Refunds for the $15 fast-track listing, sponsorships, and Bot Store downloads. Email support@agentscouthq.com to ask.",
        desc,
    )
    text = text.replace(
        "When a paid listing, sponsorship, or Bot Store download can be refunded, and how to ask.",
        "When a paid listing, sponsorship, Bot Store download, or paid report can be refunded, and how to ask.",
    )
    short = "<li>An MCP server test report, an AI visibility check, or the bundle of both is fully refunded if you ask before testing starts, or if we cannot run the test at all. Once the report is delivered, there is no refund, and you get one free retest or fix check of the same server or site within 30 days.</li>"
    if short not in text:
        text = text.replace(
            "<li>Directory submissions included with the $99 weekly sponsorship follow the sponsorship refund. If you paid for those submissions on their own before this change, you get a full refund if you ask before we start. After we start, the refund is prorated, or there is no refund once the work is delivered.</li></ul>",
            "<li>Directory submissions included with the $99 weekly sponsorship follow the sponsorship refund. If you paid for those submissions on their own before this change, you get a full refund if you ask before we start. After we start, the refund is prorated, or there is no refund once the work is delivered.</li>" + short + "</ul>",
            1,
        )
    parts = [f'{p["name"]} is ${p["price"]}, or ${p["intro"]} intro' for p in doc["products"]]
    section = (
        '<h2 style="font-size:19px;margin:32px 0 8px">MCP server test reports and AI visibility checks</h2>'
        f'<p>{".".join([])}</p>'
    )
    offered = ". ".join(parts) + ". " + doc["intro"]["note"]
    section = (
        '<h2 style="font-size:19px;margin:32px 0 8px">MCP server test reports and AI visibility checks</h2>'
        f'<p>{esc(offered)}</p>'
        '<ul>'
        '<li>You get a full refund if you ask before testing starts.</li>'
        '<li>You get a full refund if we cannot run the test at all, for example when the MCP server or site cannot be reached and you cannot fix access.</li>'
        '<li>Once a report is delivered, there is no refund. You get one free retest or fix check of the same server or site within 30 days.</li>'
        '</ul>'
        '<p>Email <a href="mailto:support@agentscouthq.com?subject=Report%20refund">support@agentscouthq.com</a>. The offers are on the <a href="mcp-test-report.html">MCP server test report</a> page and the <a href="ai-visibility-check.html">AI visibility check</a> page.</p>'
    )
    marker = '<h2 style="font-size:19px;margin:32px 0 8px">EU and UK buyers</h2>'
    if "MCP server test reports and AI visibility checks" not in text:
        text = text.replace(marker, section + marker, 1)
    named = "; ".join(f'{p["name"]} ${p["price"]} (${p["intro"]} intro)' for p in doc["products"])
    answer = (
        "You get a full refund if you ask before testing starts, or if we cannot run the test at all "
        "(for example the MCP server or site cannot be reached and you cannot fix access). "
        "Once a report is delivered, there is no refund, and you get one free retest or fix check of the same server or site within 30 days. "
        f"The priced products are: {named}. Email support@agentscouthq.com."
    )
    question = {
        "@type": "Question",
        "name": "What is the refund for an MCP server test report, an AI visibility check, or the bundle?",
        "acceptedAnswer": {"@type": "Answer", "text": answer},
    }

    def _faq(match):
        raw = match.group(1).replace("<\\/", "</")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return match.group(0)
        graph = data.get("@graph") if isinstance(data, dict) else None
        if not graph:
            return match.group(0)
        for item in graph:
            if item.get("@type") == "WebPage":
                item["description"] = "Refunds for the $15 fast-track listing, sponsorships, Bot Store downloads, and paid reports. Email support@agentscouthq.com to ask."
            if item.get("@type") == "FAQPage":
                names = [q.get("name") for q in item.get("mainEntity") or []]
                if question["name"] not in names:
                    item.setdefault("mainEntity", []).insert(-1, question)
        blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
        return '<script type="application/ld+json">' + blob + "</script>"

    text = re.sub(r'<script type="application/ld\+json">(.*?)</script>', _faq, text, flags=re.S)
    path.write_text(text, encoding="utf-8")


def patch_products(doc: dict) -> None:
    rows = catalog.catalog_entries(doc)
    path = ROOT / "api" / "products.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["reports"] = rows
    graph = (data.get("schema_org") or {}).get("@graph") or []
    skus = {item.get("sku") for item in graph}
    for row in rows:
        if row["sku"] in skus:
            continue
        graph.append({
            "@type": "Product",
            "sku": row["sku"],
            "name": row["name"],
            "description": row["description"],
            "category": row["category"],
            "brand": {"@type": "Brand", "name": "AgentScout"},
            "offers": {
                "@type": "Offer",
                "price": str(row["price_usd"]),
                "priceCurrency": "USD",
                "url": row["checkout_url"],
                "availability": "https://schema.org/InStock",
            },
        })
    if "schema_org" in data:
        data["schema_org"]["@graph"] = graph
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")
    (ROOT / ".well-known" / "acp.json").write_text(text, encoding="utf-8")
    for dest in (
        ROOT / "cloudflare-mcp-worker" / "products_snapshot.json",
        ROOT / "mcp-server" / "src" / "products_snapshot.json",
    ):
        dest.write_text(text, encoding="utf-8")


def patch_headers() -> None:
    path = ROOT / "_headers"
    text = path.read_text(encoding="utf-8")
    block = "/r/*\n  X-Robots-Tag: noindex, nofollow\n"
    if "/r/*" not in text:
        text = text.replace("/*\n", block + "\n/*\n", 1)
        path.write_text(text, encoding="utf-8")


def main() -> int:
    os.chdir(ROOT)
    doc = catalog.load_prices()
    copy_assets()
    token = render_sample(doc)
    write_product_page(doc, token)
    stamp_links()
    patch_mcp_index()
    patch_sitemap()
    patch_refunds(doc)
    patch_products(doc)
    patch_headers()
    print(f"published sample /r/{token}/ and /mcp-test-report.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
