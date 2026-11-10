"""Content-Security-Policy and outbound-link hardening for the static site.

GitHub Pages cannot set response headers, and a meta tag cannot carry
Content-Security-Policy-Report-Only, frame-ancestors, or report-uri. Every
real page therefore gets one enforcing policy via
<meta http-equiv="Content-Security-Policy">.

The policy is the one already proven on tool pages, plus 'wasm-unsafe-eval'
kept only where a page already has it (homepage search compiles Pagefind
WebAssembly). 'unsafe-inline' stays because the morning build rewrites
per-page inline scripts (theme boot, GA4, counts, JSON-LD is not a script,
onclick handlers). Hashing those would break the next rebuild.

Third parties this policy allows, and why:
- challenges.cloudflare.com: Turnstile script, iframe, and the parent-page
  api.js calls (script-src, frame-src, and connect-src). The iframe has its
  own origin, but api.js also connects from this page. Blocking that is what
  leaves real makers on error 600010 ("The anti-bot check did not finish").
  The host is already on the Report-Only header. 'unsafe-eval' stays off.
- www.googletagmanager.com: gtag.js injected by the GA4 snippet.
- *.google-analytics.com and *.analytics.google.com: GA4 collection.
- static.cloudflareinsights.com and cloudflareinsights.com: Cloudflare Web
  Analytics beacon injected in front of GitHub Pages. Not present in our HTML.
- api.agentscouthq.com, votes.agentscouthq.com,
  agentscout-image.agentscouthq.workers.dev: directory, votes, reviews,
  submit fallback, image generator.
- agentscout.beehiiv.com: newsletter links, the signup form (form-action),
  and the embed frame.
Stripe and Whop are normal links, not scripts, so they are not in script-src.
img-src keeps https: so a GA image beacon is not blocked.

Subresource Integrity is applied only to third-party URLs pinned to an exact
semver path or an npm @version. Turnstile's /v0/api.js and gtag.js?id= are
rolling URLs; pinning them would break the next vendor update.
"""
import html as _html
import os
import re

POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com https://www.googletagmanager.com https://static.cloudflareinsights.com; "
    "style-src 'self' 'unsafe-inline'; "
    "font-src 'self'; "
    "img-src 'self' data: blob: https:; "
    "connect-src 'self' https://api.agentscouthq.com https://votes.agentscouthq.com https://agentscout-image.agentscouthq.workers.dev https://agentscout.beehiiv.com https://challenges.cloudflare.com https://*.google-analytics.com https://*.analytics.google.com https://www.googletagmanager.com https://cloudflareinsights.com https://static.cloudflareinsights.com; "
    "frame-src https://challenges.cloudflare.com https://agentscout.beehiiv.com; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self' https://agentscout.beehiiv.com"
)

_CSP = re.compile(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)">')
_TAG = re.compile(r"<(a|form)\b[^>]*>", re.I)
_SKIP_DIR = ("app/", "node_modules/", "preview/", "data/", "pagefind/", ".git/")
_SKIP_NAME = {"og.html", "outreach-tracker.html", "stats.js.html"}
# Exact file pins only. /v0/ and ?id= are rolling vendor URLs, not pins.
_PINNED = re.compile(r"(?:@\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?(?:/|$)|/\d+\.\d+\.\d+/)")
_EXT_ASSET = re.compile(
    r'<(script|link)\b[^>]*?\b(?:src|href)="(https://[^"]+)"[^>]*>',
    re.I,
)


def escape(value):
    """Escape maker-supplied text for HTML text and attributes."""
    return _html.escape(str(value or ""), quote=True)


def safe_http_url(url):
    """Allow only http(s) URLs in hrefs. Anything else becomes a dead link."""
    url = str(url or "").strip()
    if re.match(r"(?i)^https?://", url):
        return url
    return "#"


def policy_for(existing):
    """Canonical policy. Keep wasm-unsafe-eval when the page already has it."""
    if existing and "'wasm-unsafe-eval'" in existing and "'wasm-unsafe-eval'" not in POLICY:
        return POLICY.replace("script-src 'self'", "script-src 'self' 'wasm-unsafe-eval'", 1)
    return POLICY


def _meta(policy):
    return f'<meta http-equiv="Content-Security-Policy" content="{policy}">'


def apply_csp(html, path="x.html"):
    """Insert or replace the CSP meta tag. Idempotent."""
    if not _site_page(path, html):
        return html
    found = _CSP.search(html)
    tag = _meta(policy_for(found.group(1) if found else ""))
    if found:
        current = found.group(0)
        if current == tag:
            return html
        return html[:found.start()] + tag + html[found.end():]
    charset = re.search(r'<meta charset="utf-8">', html)
    if charset:
        return html[:charset.end()] + tag + html[charset.end():]
    return re.sub(r"<head[^>]*>", lambda m: m.group(0) + tag, html, count=1, flags=re.I)


def _rel_value(rel):
    parts = rel.split()
    if "noopener" not in parts:
        parts.append("noopener")
    if "noreferrer" not in parts:
        i = parts.index("noopener")
        parts.insert(i + 1, "noreferrer")
    return " ".join(parts)


def _fix_tag(match):
    tag = match.group(0)
    if not re.search(r'target\s*=\s*"_blank"', tag, re.I):
        return tag
    rel = re.search(r'\srel="([^"]*)"', tag)
    if not rel:
        return tag[:-1] + ' rel="noopener noreferrer">'
    updated = _rel_value(rel.group(1))
    if updated == rel.group(1):
        return tag
    return tag[:rel.start(1)] + updated + tag[rel.end(1):]


def harden_links(html):
    """target=_blank anchors and forms get rel=noopener noreferrer."""
    return _TAG.sub(_fix_tag, html)


def harden(html, path="x.html"):
    """CSP plus outbound-link rel. Safe to run on every generator pass."""
    if not _site_page(path, html):
        return html
    return harden_links(apply_csp(html, path))


def _site_page(path, html):
    p = str(path or "").replace("\\", "/").lstrip("./")
    if p == "data/detail.tpl":
        return True
    if p.startswith(_SKIP_DIR):
        return False
    if os.path.basename(p) in _SKIP_NAME:
        return False
    low = html[:800].lower()
    return "<html" in low or "<!doctype" in low or "<head" in low


def missing_sri(html):
    """Third-party script/style URLs pinned to a semver, without integrity."""
    missing = []
    for match in _EXT_ASSET.finditer(html):
        url = match.group(2)
        tag = match.group(0)
        if not _PINNED.search(url.split("?", 1)[0]):
            continue
        if "integrity=" not in tag.lower():
            missing.append(url)
    return missing


def render_tool_sample(tool):
    """Fill data/detail.tpl the way a tool page does, with maker text escaped.

    build_site uses csp.escape for the same fields. This sample is what the
    check renders without rebuilding the whole catalog.
    """
    root = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(root, "data/detail.tpl"), encoding="utf-8") as handle:
        tpl = handle.read()
    name = escape(tool.get("name"))
    desc = escape(tool.get("description"))
    price = escape(tool.get("pricing_detail") or tool.get("pricing"))
    url = escape(safe_http_url(tool.get("visit_url") or tool.get("website") or tool.get("url")))
    repl = {
        "{{META}}": escape(tool.get("description")),
        "{{NAME}}": name,
        "{{DESC}}": desc,
        "{{URL}}": url,
        "{{HOST}}": escape("example.com"),
        "{{SLUG}}": "sample-tool",
        "{{CAT}}": escape(tool.get("category") or "MCP servers"),
        "{{CATSLUG}}": "mcp-servers",
        "{{PRICE}}": escape(tool.get("pricing")),
        "{{FACTS}}": f"<dt>Pricing</dt><dd>{price}</dd><dt>Note</dt><dd>{escape(tool.get('status_note'))}</dd>",
        "{{UC}}": "",
        "{{REL}}": "",
        "{{GHBTN}}": "",
        "{{NEW}}": "",
        "{{ICO}}": "",
        "{{MAKER_CTA}}": f"<p>Good for: {escape(tool.get('good_for'))}</p>",
        "{{ABOUT}}": f"<p>{desc}</p>",
        "{{BOTSTORE}}": "",
        "{{BADGE}}": "",
        "{{CMP}}": "",
    }
    for key, value in repl.items():
        tpl = tpl.replace(key, value)
    return harden(tpl, "tools/sample-tool.html")


def apply_all(root="."):
    n = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "app", "preview", "pagefind")]
        for name in filenames:
            if not name.endswith((".html", ".tpl")):
                continue
            path = os.path.relpath(os.path.join(dirpath, name), root)
            try:
                original = open(path, encoding="utf-8").read()
            except (OSError, UnicodeError):
                continue
            updated = harden(original, path)
            if updated != original:
                open(path, "w", encoding="utf-8").write(updated)
                n += 1
    return n


if __name__ == "__main__":
    print("csp: updated", apply_all(), "files")
