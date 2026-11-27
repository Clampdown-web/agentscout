"""Shared page, sitemap, and source rules for the AgentScout guardrails.

A full rebuild is not run in CI. build_site.py calls the network, rewrites
tools.json, and stamps the Pacific date, and later passes rewrite the HTML, so
a fresh run would not match the committed pages. The pull-request check uses a
paired-output heuristic instead: a changed generator or data file must land
with the HTML or sitemap that file is known to write.
"""

from __future__ import annotations

import json
import re
from html import unescape
from urllib.parse import urlparse

SITE = "https://agentscouthq.com"
DAILY_CAP = 3  # free new indexable pages per PT day; raise this single constant (e.g. to 5) later
PAID_DAILY_CAP = 2  # paid indexable pages allowed the same day, outside the free cap
PAID_TIERS = frozenset({"fast_track", "category_pin", "featured_49", "sponsor", "weekly_sponsor"})
HEURISTIC = (
    "This check does not rebuild the site in CI. build_site.py calls the network, "
    "rewrites tools.json, and stamps the Pacific date, and later passes rewrite the HTML, "
    "so a fresh run would not match the committed pages. The check looks for the generated "
    "HTML or sitemap the changed file is supposed to write."
)

# A token of "*" means any published HTML page or sitemap.
BROAD = ("*",)

# Historical logs and email copy. Changing them does not by itself publish a page.
# data/mcp-health is not here. The badge, Responds attributes, Our check block,
# and handshake line are built from that directory, so a change has to land with
# the published HTML.
SKIP_SOURCE_PREFIXES = (
    "data/stars/",
    "data/ratings/",
    "data/lb-ranks/",
    "data/outreach/",
    "data/gen-bg-bank/",
    "data/fonts/",
    "scripts/guardrails/",
)
SKIP_SOURCE_EXACT = {
    "data/relevance_report.json",
    "data/logo_review.json",
    "data/pack-verification.json",
    "data/cwv-candidate-local.json",
    "data/cwv-seo-benchmark.json",
    # These builders do not write HTML or a sitemap. OpenAPI writes JSON and
    # YAML, the neon pass writes share images, and the logo gate only checks.
    "build_openapi.py",
    "build_og_neon.py",
    "build_logocheck.py",
}

# Not documents. stats.js.html is a script fragment. free-tools-rest.html is
# spliced into free-tools.html and is not a URL of its own.
FRAGMENT_EXACT = {"free-tools-rest.html"}

# source path -> output prefixes the pull request must also change.
# Directory prefixes end with "/".
SOURCE_OUTPUTS = {
    "build_site.py": BROAD,
    "build.py": BROAD,
    "build_extras.py": BROAD,
    "build_seo.py": BROAD,
    "build_seo_new.py": BROAD,
    "build_seo_trim.py": BROAD,
    "build_fonts.py": BROAD,
    "build_intlinks.py": BROAD,
    "build_listlogos.py": BROAD,
    "build_growth.py": BROAD,
    "csp.py": BROAD,
    "as_boot.py": BROAD,
    "relevance.py": BROAD,
    "quality_picks.py": BROAD,
    "data/detail.tpl": BROAD,
    "tools.json": ("tools/", "index.html", "categories/", "new.html", "sitemap.xml", "sitemap-core.xml"),
    "tool_rich.json": ("tools/", "sitemap.xml"),
    "categories.json": ("categories/", "index.html", "sitemap.xml"),
    "featured.json": ("index.html", "sitemap.xml"),
    "reviews.json": ("tools/", "sitemap.xml"),
    "compare_new.json": ("compare/", "sitemap.xml"),
    "redirects.json": ("r/", "sitemap.xml"),
    "subtasks.json": ("tasks/", "sitemap.xml"),
    "status.json": ("mcp/", "tools/", "sitemap.xml"),
    "news.json": ("news/", "news.html", "sitemap.xml"),
    "news-archive.json": ("news/", "news.html", "sitemap.xml"),
    "news-history.json": ("news/", "news.html", "sitemap.xml"),
    "data/prompts.json": ("prompts/", "sitemap.xml"),
    "data/newsletter-issues.json": ("newsletter.html", "news.html", "sitemap.xml"),
    "data/latest-issue.json": ("index.html", "newsletter.html", "sitemap.xml"),
    "data/best-quick-answers.json": ("best/", "sitemap.xml"),
    "data/quality_guides.json": ("guides/", "sitemap.xml"),
    "data/github.json": ("tools/", "index.html", "sitemap.xml"),
    "data/seo_overrides.json": ("tools/", "best/", "sitemap.xml"),
    "data/index_admit.json": ("tools/", "sitemap.xml"),
    "data/index_hold.json": ("tools/", "sitemap.xml"),
    "data/index_keep_alternatives.json": ("tools/", "sitemap.xml"),
    "data/sponsored_links.json": ("tools/", "sitemap.xml"),
    "data/takedown_blocklist.json": ("tools/", "sitemap.xml"),
    "data/quality_tool_extras.json": ("tools/", "sitemap.xml"),
    "data/search.inc": ("index.html", "search/", "sitemap.xml"),
    "data/site_counts.json": ("index.html", "about.html", "sitemap.xml"),
    "data/sponsor_bar.json": ("sponsor.html", "index.html"),
    "data/sponsor_stats.json": ("sponsor.html",),
    "data/competitor_listing_prices.json": ("sponsor.html",),
    "data/agent-packs-25.json": ("bot-store/", "sitemap.xml"),
    "data/25-agent-upgraded-copy.json": ("bot-store/", "sitemap.xml"),
    "data/bt-links.json": ("bot-templates/", "sitemap.xml"),
    "data/bt-strip.inc": ("bot-templates/", "index.html"),
    "data/absorbed_sets.json": ("s/", "for/", "sitemap.xml"),
    "build_prompts.py": ("prompts/", "sitemap.xml"),
    "build_news.py": ("news/", "news.html", "sitemap.xml"),
    "build_best.py": ("best/", "sitemap.xml"),
    "build_guides.py": ("guides/", "sitemap.xml"),
    "build_videos.py": ("videos/", "sitemap.xml"),
    "build_bot_store.py": ("bot-store/", "sitemap.xml"),
    "build_bot_templates.py": ("bot-templates/", "sitemap.xml"),
    "build_tasks.py": ("tasks/", "submit.html", "sitemap.xml", "index.html"),
    "build_subtasks.py": ("tasks/", "sitemap.xml"),
    "build_mcp_tasks.py": ("mcp/", "sitemap.xml"),
    "build_free_tools.py": ("free-tools/", "free-tools.html", "free-tools-rest.html", "sitemap.xml"),
    "build_leaderboard.py": ("leaderboard/", "sitemap.xml"),
    "build_search.py": ("search/", "sitemap.xml"),
    "build_sponsor.py": ("sponsor.html",),
    "build_redirects.py": ("r/", "sitemap.xml"),
    "build_status.py": ("mcp/", "sitemap.xml"),
    "build_landing.py": ("s/", "for/", "sitemap.xml"),
    "build_recent.py": ("index.html", "new.html", "sitemap.xml"),
    "build_pick.py": ("index.html",),
    "build_links.py": ("tools/", "sitemap.xml"),
    "build_fresh.py": ("tools/", "best/", "sitemap.xml"),
    "build_featured.py": ("index.html",),
    "build_alt.py": ("tools/",),
    "build_ci.py": ("index.html",),
    "build_fix1022.py": ("free-tools.html", "new.html", "categories/", "sitemap.xml"),
    "build_lighten.py": ("leaderboard/", "best/", "categories/", "sitemap.xml"),
    "build_og.py": ("tools/", "sitemap.xml"),
    "build_quality.py": ("tools/", "best/", "sitemap.xml"),
    "build_sections.py": ("index.html", "for/"),
    "build_share.py": ("tools/",),
    "build_trending.py": ("trending.html", "index.html"),
    "build_related.py": ("tools/",),
    "build_rich.py": ("tools/",),
    "build_reviews.py": ("tools/",),
    "build_aeo.py": ("best/", "mcp/", "s/", "sitemap.xml"),
    "build_lastmod.py": ("sitemap.xml",),
    "build_seo_follow.py": ("sitemap.xml", "tools/", "best/"),
    "build_counts.py": ("index.html", "sitemap.xml"),
    "scripts/pack_pages.py": ("bot-store/", "sitemap.xml"),
    "scripts/write_lovable_page.py": ("tools/lovable.html", "sitemap.xml"),
    "scripts/update_news.py": ("news/", "news.html", "sitemap.xml"),
    "scripts/update_latest_issue.py": ("newsletter.html", "index.html", "sitemap.xml"),
}

_LINK = re.compile(r"<link\b[^>]*>", re.I)
_META = re.compile(r"<meta\b[^>]*>", re.I)
_REL_CANON = re.compile(r"""\brel\s*=\s*["']canonical["']""", re.I)
_NAME_ROBOTS = re.compile(r"""\bname\s*=\s*["']robots["']""", re.I)
_HREF = re.compile(r"""\bhref\s*=\s*["']([^"']+)["']""", re.I)
_CONTENT = re.compile(r"""\bcontent\s*=\s*["']([^"']*)["']""", re.I)
_LOC = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.I)
_MAIN = re.compile(r"<main\b[^>]*>(.*?)</main>", re.I | re.S)
# The closing tag may carry whitespace, as in </script >. A bare </script>
# misses that and is the CodeQL bad-tag-filter alert.
_SCRIPT = re.compile(r"<script\b[^>]*>.*?</script\b[^>]*>", re.I | re.S)
_STYLE = re.compile(r"<style\b[^>]*>.*?</style\b[^>]*>", re.I | re.S)
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_TAG = re.compile(r"<[^>]+>")
_REASON = re.compile(r"(?im)^[ \t>*-]*Reason this page exists:[ \t]*(.*?)\s*$")
_WORDS = re.compile(r"[A-Za-z0-9']+")

_PLACEHOLDERS = {
    "",
    "todo",
    "tbd",
    "fixme",
    "xxx",
    "n/a",
    "na",
    "none",
    "...",
    "…",
    "___",
    "search query",
    "user need",
    "a search query",
    "a user need",
    "name a real search query or user need",
    "fill this in",
    "fill in",
}

_SKIP_HTML_PREFIXES = (
    "data/",
    "scripts/",
    ".github/",
    "pagefind/",
    "preview/",
    "node_modules/",
    "cloudflare-api-worker/",
    "cloudflare-mcp-worker/",
    "cloudflare-image-worker-patches/",
)


def normalize_url(url: str) -> str:
    """Drop a query and fragment, and turn /index.html into the directory URL.

    /prompts/index.html and /prompts/ are the same public URL. The sitemap still
    lists https://agentscouthq.com/prompts/index.html while the page canonical
    is https://agentscouthq.com/prompts/.
    """
    text = (url or "").strip().split("#", 1)[0].split("?", 1)[0]
    if text.endswith("/index.html"):
        text = text[: -len("index.html")]
    return text


def page_public_url(path: str) -> str:
    """Public URL for a repo path. index.html is the directory URL."""
    rel = path.replace("\\", "/").lstrip("/")
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return SITE + "/" + rel[: -len("index.html")]
    return SITE + "/" + rel


def is_published_html(path: str) -> bool:
    rel = path.replace("\\", "/")
    if not rel.endswith(".html") or rel.endswith(".js.html"):
        return False
    if rel.startswith(_SKIP_HTML_PREFIXES) or rel in FRAGMENT_EXACT:
        return False
    if ".." in rel.split("/"):
        return False
    return True


def looks_like_document(prefix: str) -> bool:
    head = (prefix or "")[:8000].lower()
    return "<!doctype" in head or "<html" in head or 'rel="canonical"' in head or "rel='canonical'" in head


def is_generated_output(path: str) -> bool:
    rel = path.replace("\\", "/")
    if rel in ("sitemap.xml", "sitemap-core.xml", "free-tools-rest.html"):
        return True
    return is_published_html(rel)


# Files the site build rewrites. refresh-pr-builds keeps main's copy when one of
# these conflicts, then runs the build so the pull request's source and data are
# applied again. Published HTML (tools/, best/, compare/, and the other public
# pages) stays is_generated_output, above. Do not add source catalogs here:
# tools.json, tool_rich.json, and data/*.json that authors edit are not generated.
REFRESH_GENERATED_EXACT = (
    "llms.txt",
    "llms-full.txt",
    "openapi.json",
    "openapi.yaml",
    "og.png",
    "server.json",
    "status.json",
    "data/lastmod.json",
    "data/og_cache.json",
    "data/mcp_snapshot.json",
    "search/names.json",
    "search/words.json",
    "mcp-server/src/products_snapshot.json",
    ".well-known/openapi.yaml",
)
REFRESH_GENERATED_PREFIXES = (
    "pagefind/",
    "og/",
)


def is_refresh_generated(path: str) -> bool:
    """True when a merge conflict in this path can be rebuilt from source.

    The guardrail's is_generated_output covers published HTML, sitemap.xml,
    sitemap-core.xml, and free-tools-rest.html. The extra names are the other
    build outputs page-update pull requests usually touch: api/*.json, root
    sitemap-*.xml, the Pagefind index, lastmod state, share images, catalog
    snapshots, and .well-known JSON.
    """
    rel = path.replace("\\", "/").strip()
    if rel.startswith("./"):
        rel = rel[2:]
    if is_generated_output(rel):
        return True
    if rel in REFRESH_GENERATED_EXACT or rel.startswith(REFRESH_GENERATED_PREFIXES):
        return True
    parent, _, name = rel.rpartition("/")
    if parent == "" and name.startswith("sitemap") and name.endswith(".xml"):
        return True
    if parent == "api" and name.endswith(".json"):
        return True
    if parent == ".well-known" and name.endswith(".json"):
        return True
    if parent == "cloudflare-mcp-worker" and name.endswith("_snapshot.json"):
        return True
    return False


def source_outputs(path: str) -> tuple[str, ...] | None:
    """Output prefixes a changed source must refresh, or None when it is not a page source."""
    rel = path.replace("\\", "/")
    if rel in SKIP_SOURCE_EXACT or rel.startswith(SKIP_SOURCE_PREFIXES):
        return None
    if rel.startswith("data/mcp-health/"):
        return BROAD
    if rel.startswith("scripts/test_") or "/test_" in rel:
        return None
    if rel in SOURCE_OUTPUTS:
        return SOURCE_OUTPUTS[rel]
    if rel.startswith("data/bot-templates-") and rel.endswith(".json"):
        return ("bot-templates/", "sitemap.xml")
    if rel.startswith("scripts/pack_src/") and rel.endswith(".py"):
        return ("bot-store/", "sitemap.xml")
    name = rel.rsplit("/", 1)[-1]
    if "/" not in rel and name.endswith(".py") and (name == "build.py" or name.startswith("build_")):
        return BROAD
    if rel.startswith("data/") and rel.endswith((".json", ".tpl", ".inc")):
        return BROAD
    return None


def output_satisfies(path: str, outputs: tuple[str, ...]) -> bool:
    rel = path.replace("\\", "/")
    if not is_generated_output(rel):
        return False
    if "*" in outputs:
        return True
    for token in outputs:
        if token.endswith("/") and rel.startswith(token):
            return True
        if rel == token:
            return True
    return False


def describe_outputs(outputs: tuple[str, ...]) -> str:
    if "*" in outputs:
        return "a published *.html page, sitemap.xml, or sitemap-core.xml"
    nice = []
    for token in outputs:
        if token.endswith("/"):
            nice.append(token + "*.html")
        else:
            nice.append(token)
    return ", ".join(nice)


def canonical_href(document: str) -> str | None:
    for tag in _LINK.findall(document or ""):
        if _REL_CANON.search(tag):
            match = _HREF.search(tag)
            return match.group(1).strip() if match else ""
    return None


def robots_content(document: str) -> str | None:
    for tag in _META.findall(document or ""):
        if _NAME_ROBOTS.search(tag):
            match = _CONTENT.search(tag)
            return match.group(1) if match else ""
    return None


def is_noindex(document: str, header: str | None = None) -> bool:
    if header and re.search(r"\bnoindex\b", header, re.I):
        return True
    content = robots_content(document)
    return bool(content and re.search(r"\bnoindex\b", content, re.I))


def sitemap_locs(document: str) -> dict[str, str]:
    """Map a normalized URL to the first raw <loc> that produced it."""
    found: dict[str, str] = {}
    for loc in _LOC.findall(document or ""):
        raw = loc.strip()
        found.setdefault(normalize_url(raw), raw)
    return found


def main_text(document: str) -> str:
    match = _MAIN.search(document or "")
    if not match:
        return ""
    chunk = _COMMENT.sub(" ", match.group(1))
    chunk = _STYLE.sub(" ", chunk)
    chunk = _SCRIPT.sub(" ", chunk)
    chunk = _TAG.sub(" ", chunk)
    return " ".join(unescape(chunk).split())


def canonical_problem(document: str, path: str) -> str | None:
    expected = page_public_url(path)
    href = canonical_href(document)
    if href is None or href == "":
        return f"{path} has no canonical link. Expected {expected}."
    if normalize_url(href) != normalize_url(expected):
        return f"{path} canonical is {href}, expected {expected}."
    return None


def reason_lines(body: str) -> list[str]:
    lines = []
    for match in _REASON.finditer(body or ""):
        text = _COMMENT.sub("", match.group(1))
        lines.append(" ".join(text.strip().strip("\"'").split()))
    return lines


def reason_is_real(text: str) -> bool:
    collapsed = " ".join((text or "").split())
    if collapsed.lower() in _PLACEHOLDERS:
        return False
    if len(collapsed) < 8:
        return False
    words = _WORDS.findall(collapsed)
    return len(words) >= 2


def reason_problem(body: str, pages: list[str]) -> str | None:
    if not pages:
        return None
    lines = reason_lines(body)
    if any(reason_is_real(line) for line in lines):
        return None
    listed = ", ".join(pages)
    if not lines:
        return (
            f"This PR adds an indexable page ({listed}) but the PR description has no "
            '"Reason this page exists:" line. Add one that names a real search query or user need.'
        )
    return (
        f"This PR adds an indexable page ({listed}) but the "
        '"Reason this page exists:" line is empty or still a placeholder. '
        "Name a real search query or user need."
    )

def tool_slug_from_url(url: str) -> str | None:
    """Slug for a tool page URL such as /tools/kurodyne or /tools/kurodyne.html; else None."""
    parsed = urlparse(normalize_url(url))
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    # Only the AgentScout host (or a bare path with no host) can yield a slug.
    if host not in ("", "agentscouthq.com"):
        return None
    path = parsed.path or ""
    m = re.match(r"^/tools/([^/]+?)/?$", path)
    if not m:
        return None
    slug = m.group(1)
    if slug.lower().endswith(".html"):
        slug = slug[:-5]
    slug = slug.strip().lower()
    if not slug or slug == "index":
        return None
    return slug


def is_paid_listing(entry: dict) -> bool:
    """Match build_extras._paid_listing / build_growth: fast_track or listing_tier (also tier)."""
    if not isinstance(entry, dict):
        return False
    tier = str(entry.get("listing_tier") or entry.get("tier") or "").lower().replace("-", "_")
    return bool(entry.get("fast_track") or tier in PAID_TIERS)


def paid_slugs_from_tools_json(raw: str) -> set[str]:
    if not (raw or "").strip():
        return set()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return set()
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("tools") or data.get("items") or []
    else:
        return set()
    slugs: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or not is_paid_listing(item):
            continue
        slug = str(item.get("slug") or "").strip().lower()
        if slug:
            slugs.add(slug)
    return slugs


def classify_indexable(urls: list[str], paid_slugs: set[str]) -> tuple[list[str], list[str]]:
    """Split sitemap URLs into (free, paid). Non-tool URLs are free."""
    free, paid = [], []
    paid_slugs = {s.lower() for s in paid_slugs}
    for url in urls:
        slug = tool_slug_from_url(url)
        if slug and slug in paid_slugs:
            paid.append(url)
        else:
            free.append(url)
    return free, paid
