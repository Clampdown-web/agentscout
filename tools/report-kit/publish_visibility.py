#!/usr/bin/env python3
"""Publish the AI visibility check product page and the sample private report.

Run from the repo root:

    python3 tools/report-kit/publish_visibility.py

Prices and Stripe links for this page are read only from data/ai_visibility_check.json.
The MCP report template is not modified.
"""
from __future__ import annotations

import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_KIT = Path(__file__).resolve().parent
KIT = REPORT_KIT / "ai-visibility"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPORT_KIT))

import catalog  # noqa: E402
import csp as site_csp  # noqa: E402
import ga4  # noqa: E402
import publish_site  # noqa: E402

_spec = importlib.util.spec_from_file_location("visibility_build_report", KIT / "build_report.py")
build_report = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_report)

CSS_V = "202611112100"
ASSET_V = re.search(r'ASSET_V = "(\d+)"', (ROOT / "build_tasks.py").read_text(encoding="utf-8")).group(1)
PAGE_CSS = f"ai-visibility-check.css?v={CSS_V}"
CROSS = 'For how a site shows up in AI answers, see the <a href="ai-visibility-check.html">AI visibility check</a>.'
REFUND_OLD = 'The offer is on the <a href="mcp-test-report.html">MCP server test report</a> page.'
REFUND_NEW = 'The offers are on the <a href="mcp-test-report.html">MCP server test report</a> page and the <a href="ai-visibility-check.html">AI visibility check</a> page.'


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def copy_assets() -> None:
    dest = ROOT / "assets" / "ai-visibility-report"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(KIT / "report.css", dest / "report.css")
    logo = dest / "logo"
    logo.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(KIT / "assets" / "logo" / "logo-mark-dark.svg", logo / "logo-mark-dark.svg")
    fonts = dest / "assets" / "fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    for font in (KIT / "assets" / "fonts").glob("inter-*.ttf"):
        shutil.copyfile(font, fonts / font.name)


def render_pdf_and_sample() -> None:
    subprocess.run(
        [
            sys.executable,
            str(KIT / "build_report.py"),
            "--captures", str(KIT / "captures.json"),
            "--scorecard", str(KIT / "sample-scorecard.json"),
            "--html", str(KIT / "sample.html"),
            "--pdf", str(KIT / "samples" / "ai-visibility-check-sample-2026-11-11.pdf"),
            "--previews", str(ROOT / "assets" / "ai-visibility-report" / "previews"),
            "--robots", "noindex, nofollow",
        ],
        check=True,
        cwd=ROOT,
    )


def render_private(doc: dict) -> str:
    sample_slug = doc["sample_slug"]
    if len(sample_slug) < 24:
        raise SystemExit("sample_slug must be at least 24 characters")
    if "token" in sample_slug.lower():
        raise SystemExit("sample_slug must not use token naming")
    captures = json.loads((KIT / "captures.json").read_text(encoding="utf-8"))
    scorecard = json.loads((KIT / "sample-scorecard.json").read_text(encoding="utf-8"))
    model = build_report.build_model(captures, scorecard)
    report_dir = ROOT / "r" / sample_slug
    report_dir.mkdir(parents=True, exist_ok=True)
    pdf_src = KIT / "samples" / "ai-visibility-check-sample-2026-11-11.pdf"
    shutil.copyfile(pdf_src, report_dir / "report.pdf")
    page = build_report.render_html(model, web={
        "fit": True,
        "logo_src": "/assets/ai-visibility-report/logo/logo-mark-dark.svg",
        "css_href": f"/assets/ai-visibility-report/report.css?v={CSS_V}",
        "robots": "noindex, nofollow",
        "csp": site_csp.POLICY,
        "referrer": "strict-origin-when-cross-origin",
        "pdf_href": "report.pdf",
    })
    page = ga4.apply(page, f"r/{sample_slug}/index.html")
    (report_dir / "index.html").write_text(page, encoding="utf-8")
    return sample_slug


def _offer_card(product: dict, doc: dict) -> str:
    price, url = catalog.selling(product, doc)
    regular = int(product["price"])
    strike = ""
    if price != regular:
        strike = f'<s class="was">${regular}</s>'
    label = "Buy the bundle" if product["id"] == "bundle" else "Buy the AI visibility check"
    return (
        f'<article class="report-offer">'
        f'<h2>{esc(product["name"])}</h2>'
        f'<p>{esc(product["blurb"])}</p>'
        f'<p class="report-price"><span class="now">${price}</span>{strike}</p>'
        f'<a class="btn primary" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'
        f'{publish_site.PAYNOTE}'
        f'</article>'
    )


def product_main(doc: dict, sample_slug: str) -> str:
    shown = [p for p in doc["products"] if p.get("on_page")]
    cards = "".join(_offer_card(p, doc) for p in shown)
    email = doc["questions_email"]
    scorecard = json.loads((KIT / "sample-scorecard.json").read_text(encoding="utf-8"))
    areas = "".join(f"<li>{esc(row)}</li>" for row in scorecard["scoring_method"])
    previews = sorted((ROOT / "assets" / "ai-visibility-report" / "previews").glob("page-*.png"))
    figures = []
    for path in previews:
        width, height = publish_site.png_size(path)
        n = path.stem.split("-")[-1]
        figures.append(
            f'<figure><img src="assets/ai-visibility-report/previews/{esc(path.name)}" alt="Sample report page {esc(n)}" '
            f'width="{width}" height="{height}" loading="lazy" decoding="async"><figcaption>Page {esc(n)}</figcaption></figure>'
        )
    sample_page = f"r/{sample_slug}/"
    sample_pdf = f"r/{sample_slug}/report.pdf"
    return f'''<div class="crumb"><a href="index.html">AgentScout</a> / AI visibility check</div>
<section class="calm">
<h1 style="text-align:left" data-pagefind-weight="10">AI visibility check</h1>
<p class="lede" style="margin-left:0;text-align:left">A written check of how one public site shows up when someone asks a real buyer question in an AI answer. ChatGPT, Perplexity, and Google AI Overviews are the kind of answer this covers. Rivals are scored on the same questions, and the report lists the sources those answers cite.</p>
<p class="report-intro">{esc(doc["intro"]["note"])}</p>
<div class="report-offers">{cards}</div>
<p class="report-ask"><a href="mailto:{esc(email)}">Questions? Email {esc(email)}</a></p>
<p>Testing a public MCP server instead? See the <a href="mcp-test-report.html">MCP server test report</a>, or buy both in the bundle.</p>
<h2 style="font-size:19px;margin:28px 0 8px">What the check covers</h2>
<p>The score is 100 points, split across the questions a buyer or maker would actually type:</p>
<ul>{areas}</ul>
<p>Each prompt is scored on one rung: recommended, cited, mentioned, or absent. The same rung is recorded for the rivals named in the check. Pages the answers cite are opened, and the report says which of those pages already name the site.</p>
<h2 style="font-size:19px;margin:28px 0 8px">What you get</h2>
<ul><li>A private branded web page. It is not in the sitemap.</li><li>The same report as a downloadable PDF.</li><li>One free retest of the same site within 30 days after delivery.</li></ul>
<p>The booking link inside a delivered report stays a placeholder until a calendar exists.</p>
<h2 style="font-size:19px;margin:28px 0 8px">Sample report</h2>
<p>This sample is AgentScout, tested November 11, 2026. It is the baseline run. The private page is not in the sitemap. The PDF is the same nine pages.</p>
<p><a href="{esc(sample_page)}">Open the sample report</a> · <a href="{esc(sample_pdf)}">Download the sample PDF</a></p>
<div class="report-pages">{''.join(figures)}</div>
<h2 style="font-size:19px;margin:28px 0 8px">FAQ</h2>
<h3 style="font-size:16px;margin:16px 0 6px">What does the check cover?</h3>
<p>How the site shows up in AI answers such as ChatGPT, Perplexity, and Google AI Overviews, for real buyer questions. Rivals are compared on those questions. The report lists the cited sources and which of them already name the site.</p>
<h3 style="font-size:16px;margin:16px 0 6px">What do I get?</h3>
<p>A private branded web page and a downloadable PDF of the same report. The page is noindex. After delivery you get one free retest of the same site within 30 days.</p>
<h3 style="font-size:16px;margin:16px 0 6px">What does the intro price cover?</h3>
<p>{esc(doc["intro"]["note"])} The check is $79, marked down from $99. The bundle with the MCP server test is $119, marked down from $149.</p>
<h3 style="font-size:16px;margin:16px 0 6px">Can I get a refund?</h3>
<p>You get a full refund if you ask before testing starts, or if the site cannot be checked at all. Once the report is delivered, there is no refund. The full rules are on the <a href="refunds.html">refund policy</a>.</p>
</section>'''


def write_product_page(doc: dict, sample_slug: str) -> None:
    src = (ROOT / "mcp-test-report.html").read_text(encoding="utf-8")
    title = "AI visibility check · AgentScout"
    desc = "How a public site shows up in AI answers for real buyer questions, with rivals and cited sources. Private page and PDF. Intro $79 ($99 regular). Bundle $119 ($149)."
    src = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", src, count=1, flags=re.S)
    src = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + esc(desc) + m.group(2), src, count=1)
    src = re.sub(r'(<link rel="canonical" href=")[^"]*(")', lambda m: m.group(1) + "https://agentscouthq.com/ai-visibility-check.html" + m.group(2), src, count=1)
    for prop in ("og:title", "og:description", "og:url", "twitter:title", "twitter:description"):
        value = {
            "og:title": title,
            "og:description": desc,
            "og:url": "https://agentscouthq.com/ai-visibility-check.html",
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
        "url": "https://agentscouthq.com/ai-visibility-check.html",
    }
    blob = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")

    def _swap_ld(match):
        raw = match.group(1)
        if '"@type": "WebPage"' in raw or '"@type":"WebPage"' in raw:
            return '<script type="application/ld+json">' + blob + "</script>"
        return match.group(0)

    src = re.sub(r'<script type="application/ld\+json">(.*?)</script>', _swap_ld, src, count=2, flags=re.S)
    src = src.replace("mcp-test-report.css?v=202611111902", PAGE_CSS)
    if "ai-visibility-check.css" not in src:
        src = src.replace(f'href="styles.css?v={ASSET_V}">', f'href="styles.css?v={ASSET_V}"><link rel="stylesheet" href="{PAGE_CSS}">', 1)
    main = product_main(doc, sample_slug)
    src = re.sub(r"(<main class=\"wrap\" data-pagefind-body>).*(</main>)", lambda m: m.group(1) + main + m.group(2), src, count=1, flags=re.S)
    (ROOT / "ai-visibility-check.html").write_text(src, encoding="utf-8")


def stamp_visibility_links() -> int:
    changed = 0
    pattern = re.compile(
        r'(<a href="([^"]*)mcp-test-report\.html">MCP server test</a>)'
        r'(?!<a href="\2ai-visibility-check\.html">AI visibility check</a>)'
    )
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in publish_site.SKIP_WALK and not d.startswith(".")]
        for name in files:
            if not name.endswith(".html"):
                continue
            path = Path(dirpath) / name
            text = path.read_text(encoding="utf-8", errors="replace")
            new, n = pattern.subn(r'\1<a href="\2ai-visibility-check.html">AI visibility check</a>', text)
            if n and new != text:
                path.write_text(new, encoding="utf-8")
                changed += 1
    return changed


def patch_mcp_page() -> None:
    path = ROOT / "mcp-test-report.html"
    text = path.read_text(encoding="utf-8")
    if "ai-visibility-check.html" in text.split("<footer", 1)[0] and CROSS in text:
        return
    needle = '<p class="report-intro">'
    insert = f"<p>{CROSS}</p>\n"
    if CROSS not in text:
        text = text.replace(needle, insert + needle, 1)
        path.write_text(text, encoding="utf-8")


def patch_sitemap() -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    loc = "https://agentscouthq.com/ai-visibility-check.html"
    if loc not in text:
        row = f"  <url><loc>{loc}</loc><lastmod>2026-11-11</lastmod></url>\n"
        anchor = "  <url><loc>https://agentscouthq.com/mcp-test-report.html</loc><lastmod>2026-11-11</lastmod></url>\n"
        if anchor not in text:
            raise SystemExit("sitemap.xml is missing the MCP test report URL")
        text = text.replace(anchor, anchor + row, 1)
    if "/r/" in text:
        raise SystemExit("sitemap.xml contains a private report URL")
    path.write_text(text, encoding="utf-8")
    llms = ROOT / "llms.txt"
    llm = llms.read_text(encoding="utf-8")
    line = "- [AI visibility check](https://agentscouthq.com/ai-visibility-check.html): how a public site shows up in AI answers for real buyer questions, with a private page and PDF\n"
    if "ai-visibility-check.html" not in llm:
        needle = "- [MCP server test report](https://agentscouthq.com/mcp-test-report.html): protocol test of a public MCP server, with a private page, PDF, and dated badge\n"
        if needle not in llm:
            raise SystemExit("llms.txt is missing the MCP test report line")
        llm = llm.replace(needle, needle + line, 1)
        llms.write_text(llm, encoding="utf-8")


def patch_refunds() -> None:
    path = ROOT / "refunds.html"
    text = path.read_text(encoding="utf-8")
    if REFUND_OLD in text:
        text = text.replace(REFUND_OLD, REFUND_NEW, 1)
        path.write_text(text, encoding="utf-8")


def main() -> int:
    os.chdir(ROOT)
    doc = catalog.load_visibility()
    copy_assets()
    render_pdf_and_sample()
    sample_slug = render_private(doc)
    write_product_page(doc, sample_slug)
    patch_mcp_page()
    changed = stamp_visibility_links()
    patch_sitemap()
    patch_refunds()
    publish_site.patch_products(catalog.load_prices())
    print(f"published sample /r/{sample_slug}/ and /ai-visibility-check.html ({changed} pages linked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
