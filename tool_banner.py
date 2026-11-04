"""Bot Store strip on every /tools/*.html page.

The markup lives in data/detail.tpl. build_site.py copies that template for each
new listing, then ensure() puts the same strip on the page if a later edit
dropped it. Redirect stubs under tools/ have no <main> and are left alone.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TPL = ROOT / "data" / "detail.tpl"
_BANNER = re.compile(r'<a class="bsbanner"[^>]*>.*?</a>', re.S)


def banner_html() -> str:
    m = _BANNER.search(TPL.read_text(encoding="utf-8"))
    if not m:
        raise SystemExit("data/detail.tpl is missing the tool-page Bot Store banner")
    return m.group(0)


def ensure(html: str) -> str:
    """Insert the template banner once, or refresh an existing one to match it."""
    banner = banner_html()
    if 'class="bsbanner"' in html:
        return _BANNER.sub(banner, html, count=1)
    if "<main" not in html:
        return html
    return re.sub(r"(<main\b[^>]*>)", lambda m: m.group(1) + "\n  " + banner, html, count=1)
