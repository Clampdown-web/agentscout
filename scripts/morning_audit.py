"""Repo entrypoint for the 7AM deep audit.

The box copy at /workspace/scripts/daily_deep_audit.py is not in git. This module
is the source that copy should be replaced by. It does not POST /submit, does not
bypass Turnstile, and does not write the tree it reads.

  AGENTSCOUT_ROOT=<tree> python3 daily_deep_audit.py --predeploy
  AGENTSCOUT_ROOT=<tree> python3 daily_deep_audit.py --live

--predeploy is the publish gate. It reads the tree and does not write it.
--live reads the deployed site. It does not POST /submit and it does not call
api.indexnow.org. A live page that still shows the previous stamp is DEFERRED,
not an artifact failure. A measurement file that is absent is UNVERIFIED, not a pass.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import cwv_seo_benchmark
import publish_gate

STALE_ROOT = Path("/workspace/agent-tool-finder")
SUBMIT_URL = "https://api.agentscouthq.com/submit"
MCP_URL = "https://mcp.agentscouthq.com/mcp"
ALLOWED_ORIGIN = "https://agentscouthq.com"
NAV_SKIP = {"404.html", "google823b89b55b70e740.html"}
LAB_SOURCES = {"lab-lighthouse", "lab-pagespeed", "lab-unthrottled-benchmark"}
FIELD_SOURCES = {"field-crux", "field-search-console"}
BENCHMARK_SOURCE = "lab-unthrottled-benchmark"
BENCHMARK_METHOD = "cwv_seo_benchmark.measure_url"
UNTHROTTLED_THRESHOLDS = {"lcp_ms": 2500, "cls": 0.1, "ttfb_ms": 800}
STALE_TOKENS = ("2,467+", "2,095+", "2,104+", "2,350+")
DIRECTORY_STRIPE = {
    "$15 Fast-Track": "https://buy.stripe.com/3cIaEY6T15hlfJr135e7m0e",
    "$49 30-Day Category Pin": "https://buy.stripe.com/bJefZi4KT6lp9l3dPRe7m00",
    "$99/wk Weekly Sitewide Sponsor": "https://buy.stripe.com/6oU4gA2CL9xB2WFcLNe7m01",
}
BOT_STRIPE = {
    "$39 Operations Bot": "https://buy.stripe.com/cNidRa0uDdNRgNvaDFe7m03",
    "$59 SEO Bot": "https://buy.stripe.com/14A7sMfpx6lp9l3aDFe7m05",
    "$59 Market Bot": "https://buy.stripe.com/4gM8wQelt11568RaDFe7m06",
    "$69 CEO Bot": "https://buy.stripe.com/9B69AU2CLh031SB8vxe7m07",
    "$149 Bundle": "https://buy.stripe.com/fZueVe5OX7pt1SB6npe7m08",
}
FORM_IDS = (
    "sf", "spkg-field", "name", "website", "category", "pricing", "desc", "email",
    "found", "sbtn", "sdone", "sdone-msg", "sdone-pay", "sdone-pay-btn",
)
LIVE_PAGES = (
    "https://agentscouthq.com/",
    "https://agentscouthq.com/submit.html",
    "https://agentscouthq.com/sponsor.html",
    "https://agentscouthq.com/new.html",
    "https://agentscouthq.com/mcp/",
    "https://agentscouthq.com/mcp/connect.html",
    "https://agentscouthq.com/bot-store/",
    "https://agentscouthq.com/bot-templates/",
    "https://agentscouthq.com/videos/",
    "https://agentscouthq.com/newsletter.html",
    "https://agentscouthq.com/api/products.json",
    "https://agentscouthq.com/.well-known/acp.json",
    "https://agentscouthq.com/.well-known/ai-plugin.json",
    "https://agentscouthq.com/.well-known/mcp.json",
    "https://agentscouthq.com/openapi.yaml",
    "https://agentscouthq.com/llms.txt",
    "https://agentscouthq.com/llms-full.txt",
)
CRAWLER_UA = "Mozilla/5.0 (compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot)"
CLONER_UA = "Mozilla/4.5 (compatible; HTTrack 3.0x)"


class AuditResult:
    def __init__(self) -> None:
        self.problems: list[str] = []
        self.passes: list[str] = []
        self.deferred: list[str] = []
        self.unverified: list[str] = []
        self.synthetic_accepted = 0
        self.category_acceptance_claimed = False
        self.live_posts = 0

    def ok(self, message: str) -> None:
        self.passes.append(message)

    def err(self, message: str) -> None:
        self.problems.append(message)

    def later(self, message: str) -> None:
        self.deferred.append(message)

    def unknown(self, message: str) -> None:
        self.unverified.append(message)

    def settle(self, name: str, problems: list[str], ok_detail: str) -> None:
        if problems:
            for item in problems:
                self.err(f"{name}: {item}")
            return
        self.ok(f"{name}: {ok_detail}")


def resolve_root(explicit: str | None = None) -> Path:
    raw = explicit if explicit is not None else os.environ.get("AGENTSCOUT_ROOT")
    if not raw:
        raise SystemExit(
            "AGENTSCOUT_ROOT is required. This audit does not default to /workspace/agent-tool-finder."
        )
    given = Path(raw)
    if given.as_posix().rstrip("/") == STALE_ROOT.as_posix() and os.environ.get("AGENTSCOUT_ALLOW_STALE_ROOT") != "1":
        raise SystemExit(
            "AGENTSCOUT_ROOT is the stale checkout /workspace/agent-tool-finder. "
            "Point it at the tree under review."
        )
    root = given.resolve()
    if not root.is_dir():
        raise SystemExit(f"AGENTSCOUT_ROOT is not a directory: {root}")
    return root


def _option_values(html: str, select_id: str) -> list[str]:
    import html as html_lib
    match = re.search(rf'<select[^>]*id=["\']?{select_id}\b.*?</select>', html, re.S | re.I)
    block = match.group(0) if match else ""
    values = []
    for attrs, text in re.findall(r"<option([^>]*)>([^<]*)</option>", block, re.I):
        found = re.search(r'value=["\']([^"\']*)["\']', attrs)
        raw = found.group(1) if found else text
        value = html_lib.unescape(raw).strip()
        if value:
            values.append(value)
    return values


def _catalog_counts(root: Path) -> tuple[int, int]:
    path = root / "tools.json"
    if not path.is_file():
        return 0, 0
    try:
        return publish_gate.catalog_counts(json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return 0, 0


def _large_catalog(tool_count: int) -> bool:
    """Only the nav page-count minimum uses this. Other checks are not skipped by size."""
    return tool_count >= 2000


def nav_footer_problems(root: Path, tool_count: int) -> list[str]:
    """Sitewide nav and footer parity. Same comparison the box script ran."""
    problems = []
    ref_nav = None
    ref_ft = None
    nav_mismatches = []
    ft_mismatches = []
    dup_pages = []
    checked = 0
    for path in sorted(root.glob("**/*.html")):
        rel = path.relative_to(root).as_posix()
        if rel in NAV_SKIP or rel.startswith(("reports/", "widgets/", "preview/", "pagefind/")):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        nav = re.search(r"<nav[^>]*>(.*?)</nav>", text, re.S)
        foot = re.search(r"<footer[^>]*>(.*?)</footer>", text, re.S)
        if not nav or not foot:
            continue
        checked += 1
        nav_links = [_link_text(a) for a in re.findall(r"<a[^>]*>(.*?)</a>", nav.group(1), re.S)]
        ft_links = [_link_text(a) for a in re.findall(r"<a[^>]*>(.*?)</a>", foot.group(1), re.S)]
        norm = [re.sub(r"[^a-z0-9 ]", "", link.lower()).strip() for link in nav_links]
        dups = sorted({link for link in norm if link and norm.count(link) > 1})
        if dups:
            dup_pages.append(f"{rel}:{dups}")
        if ref_nav is None:
            ref_nav = nav_links
            ref_ft = ft_links
        else:
            if nav_links != ref_nav:
                nav_mismatches.append(rel)
            if ft_links != ref_ft:
                ft_mismatches.append(rel)
    if _large_catalog(tool_count) and checked <= 2000:
        problems.append(f"nav/footer checked {checked} pages, a full catalog needs more than 2000")
    if checked == 0:
        problems.append("nav/footer found no pages with both nav and footer")
    if nav_mismatches or ft_mismatches:
        problems.append(
            f"nav/footer mismatch across {checked} pages: "
            f"nav={len(nav_mismatches)} footer={len(ft_mismatches)}"
        )
    if dup_pages:
        problems.append(f"duplicate header menu buttons on {len(dup_pages)} pages")
    return problems


def _link_text(raw: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", raw)).strip()


def submit_link_problems(root: Path) -> list[str]:
    problems = []
    checked = 0
    for path in sorted(root.glob("**/*.html")):
        rel = path.relative_to(root).as_posix()
        if rel.startswith(("preview/", "data/", "pagefind/", "reports/")):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "http-equiv=\"refresh\"" in text.lower() and "<nav" not in text:
            continue
        nav = re.search(r"<nav[^>]*>.*?</nav>", text, re.S)
        foot = re.search(r"<footer[^>]*>.*?</footer>", text, re.S)
        if not nav or not foot:
            continue
        checked += 1
        if "Submit a tool" not in nav.group(0):
            problems.append(f"{rel} nav missing Submit a tool")
        if "Submit a tool" not in foot.group(0):
            problems.append(f"{rel} footer missing Submit a tool")
        depth = rel.count("/")
        expected = ("../" * depth) + "submit.html"
        for href in re.findall(r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>[^<]*Submit a tool", text, re.I):
            if href not in (expected, "/submit.html", "https://agentscouthq.com/submit.html") and not href.startswith(expected + "#"):
                problems.append(f"{rel} bad Submit a tool href={href}")
        if "issues/new?labels=submission" in text and rel != "submit.html":
            problems.append(f"{rel} contains a legacy GitHub submission link")
    if checked == 0:
        problems.append("no pages checked for Submit a tool")
    submit = root / "submit.html"
    form = submit.read_text(encoding="utf-8", errors="ignore") if submit.is_file() else ""
    if 'id="sf"' not in form or 'id="sbtn"' not in form or "https://api.agentscouthq.com/submit" not in form:
        problems.append("submit.html is missing #sf, #sbtn, or the submit endpoint")
    return problems[:8]


def scroll_problems(root: Path) -> list[str]:
    css_path = root / "styles.css"
    js_path = root / "app.js"
    if not css_path.is_file() or not js_path.is_file():
        return ["styles.css or app.js is missing, so scroll arrows cannot be checked"]
    css = re.sub(r"/\*.*?\*/", "", css_path.read_text(encoding="utf-8"), flags=re.S)
    problems = []
    if ".scrollbtns" not in css or ".scrollbtn.show" not in css:
        problems.append("styles.css is missing .scrollbtns or .scrollbtn.show")
    js = js_path.read_text(encoding="utf-8")
    block = re.search(r"/\* Scroll buttons.*?\}\)\(\);", js, re.S)
    chunk = block.group(0) if block else ""
    if "scrollbtn up" not in chunk or "scrollbtn down" not in chunk:
        problems.append("app.js does not create the up and down scroll buttons")
    return problems


def synthetic_category_problems(root: Path) -> tuple[list[str], int]:
    """Run the inner category decision locally. This does not POST and does not claim a live accept."""
    catalog_path = root / "categories.json"
    submit_path = root / "submit.html"
    problems = []
    if not catalog_path.is_file() or not submit_path.is_file():
        return ["categories.json or submit.html is missing"], 0
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"categories.json is not valid JSON ({exc})"], 0
    if not isinstance(catalog, list):
        return ["categories.json is not a list"], 0
    html = submit_path.read_text(encoding="utf-8")
    options = _option_values(html, "category")
    pricing = _option_values(html, "pricing")
    problems.extend(publish_gate.category_names_problems(options, catalog))
    if not pricing:
        problems.append("submit.html is missing pricing options")
        return problems, 0
    accepted = 0
    for name in catalog:
        decision = publish_gate.inner_submit_decision(name, "__audit_invalid__", catalog, pricing)
        if decision == publish_gate.PRICING_REJECTION:
            accepted += 1
        elif decision is None:
            problems.append(f"{name}: invalid pricing was treated as a storable submission")
        else:
            problems.append(f"{name}: {decision}")
    unknown = publish_gate.inner_submit_decision("not-a-category", "__audit_invalid__", catalog, pricing)
    if unknown != publish_gate.CATEGORY_REJECTION:
        problems.append("an unknown category was not rejected by the inner check")
    return problems, accepted


def record_coverage(result: AuditResult, root: Path, tool_count: int) -> None:
    """Every local surface gets its own named line. Size does not skip a surface."""
    import verify_4tier_ctas
    import verify_bot_zip_packages

    result.settle("nav-footer", nav_footer_problems(root, tool_count), "nav and footer match on the pages that have both")
    result.settle("submit-links", submit_link_problems(root), "Submit a tool links resolve and the form endpoint is present")
    result.settle("scroll-arrows", scroll_problems(root), "app.js creates the buttons and styles.css keeps them")
    packs = root / "bot-packages" / "25-agent-packs"
    if not packs.is_dir():
        zip_problems = ["bot-packages/25-agent-packs is missing"]
    else:
        zip_problems, _passed = verify_bot_zip_packages._audit(root)
    result.settle("zip-packages", zip_problems, "package tree and START-HERE copies match; no verification file was written")
    try:
        cta_problems = verify_4tier_ctas.problems(root)
    except OSError as exc:
        cta_problems = [f"could not read the tree ({exc})"]
    result.settle("four-tier-ctas", cta_problems, "flagship links, prices, and 25 cards are present")
    pack_pages = list((root / "bot-store").glob("*/index.html")) if (root / "bot-store").is_dir() else []
    pack_problems = []
    if len(pack_pages) != 25:
        pack_problems.append(f"bot-store pack pages are {len(pack_pages)}, expected 25")
    for page in pack_pages:
        if "Agent Agent" in page.read_text(encoding="utf-8", errors="ignore"):
            pack_problems.append(f"{page.relative_to(root).as_posix()} contains Agent Agent")
    result.settle("pack-pages", pack_problems, "25 pack pages and no Agent Agent title")
    result.settle("pack-ux", pack_ux_problems(root), "hosts, cache buster, dock, and outreach email are present")


def template_count_problems(root: Path) -> list[str]:
    state_path = root / "data" / "anim_state.json"
    page = _read(root, "bot-templates/index.html")
    if not state_path.is_file() or not page:
        return ["bot template count cannot be checked: anim_state or bot-templates/index.html is missing"]
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"anim_state.json is not valid JSON ({exc})"]
    rows = len(re.findall(r'<li class="bt-row"', page))
    expected = state.get("bot_templates")
    if expected != rows:
        return [f"bot-templates rows {rows} != anim_state bot_templates {expected}"]
    return []


def pack_ux_problems(root: Path) -> list[str]:
    """Local pack-builder checks from the box audit. They do not fetch the live site."""
    store = _read(root, "bot-store/index.html")
    templates = _read(root, "bot-templates/index.html")
    videos = _read(root, "videos/index.html")
    lovable = _read(root, "tools/lovable.html")
    outreach = _read(root, "data/outreach/25-agent-packs-email.html")
    problems = []
    if not store or not templates:
        return ["pack UX cannot be checked: bot-store or bot-templates index is missing"]
    if "{tier_btns}" in store or "{tier_btns}" in templates:
        problems.append("literal {tier_btns} in bot-store or bot-templates")
    if "#ap-dock{position:sticky" in store or 'id="ap-dock" hidden' not in store or "#ap-dock[hidden]{display:none" not in store:
        problems.append("#ap-dock is not hidden on load or still uses sticky positioning")
    if '</span><span class="ap-kind">Agent</span>' in store and ' </span><span class="ap-kind">Agent</span>' not in store:
        problems.append("bot-store card title is missing the space before Agent")
    for rel, text in (("bot-store/index.html", store), ("bot-templates/index.html", templates)):
        section = re.search(r'<section[^>]*id="ai-agent-packs"[^>]*>.*?</section>', text, re.S)
        block = section.group(0) if section else ""
        for host in ("Claude Code", "Cursor", "Codex", "Grok Bot", "Lovable"):
            if host not in block:
                problems.append(f"{rel} #ai-agent-packs is missing {host}")
        if text.count('class="ap-compat"') != 25:
            problems.append(f"{rel} ap-compat count is {text.count('class=\"ap-compat\"')}, expected 25")
        if "<li>Zero Telemetry</li>" in text:
            problems.append(f"{rel} contains a duplicate Zero Telemetry chip")
    pack_pages = list((root / "bot-store").glob("*/index.html"))
    compat = sum('class="pack-compat"' in page.read_text(encoding="utf-8", errors="ignore") for page in pack_pages)
    if compat != 25:
        problems.append(f"pack-compat is on {compat}/25 pack pages")
    if not videos or "$35" not in videos or "25 AI Agent Packs" not in videos or "Lovable" not in videos:
        problems.append("videos/index.html is missing the 25 AI Agent Packs guide")
    if "agentscout-bot-constellation.mp4?v=" not in templates:
        problems.append("bot-templates/index.html constellation video is missing its cache buster")
    if not lovable or "#ai-agent-packs" not in lovable or "$35" not in lovable:
        problems.append("tools/lovable.html is missing the pack link")
    if "https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09" not in outreach or "Claude" not in outreach:
        problems.append("data/outreach/25-agent-packs-email.html is missing the Stripe link or host list")
    return problems


def local_contract_problems(root: Path) -> tuple[list[str], int]:
    problems = []
    problems.extend(publish_gate.artifact_animation_problems(root))
    problems.extend(publish_gate.product_snapshot_problems(root))
    category_problems, accepted = synthetic_category_problems(root)
    problems.extend(category_problems)
    return problems, accepted


def _read(root: Path, rel: str) -> str:
    path = root / rel
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def form_field_problems(root: Path) -> list[str]:
    html = _read(root, "submit.html")
    if not html:
        return ["submit.html is missing"]
    missing = [item for item in FORM_IDS if not re.search(rf'\bid=["\']?{re.escape(item)}["\'\s>]', html)]
    if missing:
        return [f"submit.html is missing form ids: {', '.join(missing)}"]
    return []


def stripe_file_problems(root: Path) -> list[str]:
    submit = _read(root, "submit.html")
    sponsor = _read(root, "sponsor.html")
    acp = _read(root, ".well-known/acp.json")
    store = _read(root, "bot-store/index.html")
    templates = _read(root, "bot-templates/index.html")
    problems = []
    if not sponsor:
        problems.append("sponsor.html is missing")
    if not acp:
        problems.append(".well-known/acp.json is missing")
    for label, url in DIRECTORY_STRIPE.items():
        if url not in submit or url not in sponsor or url not in acp:
            problems.append(f"{label} is not wired in submit.html, sponsor.html, and acp.json")
    for label, url in BOT_STRIPE.items():
        if url not in store or url not in templates or url not in acp:
            problems.append(f"{label} is not wired in bot-store, bot-templates, and acp.json")
    if "logo-wordmark.svg" not in store:
        problems.append("bot-store/index.html is missing logo-wordmark.svg")
    return problems


def listed_email_problems(text: str, html: str, pages_label: str, followers_label: str) -> list[str]:
    """Assertions from the box email check. The strings are not written to disk."""
    problems = []
    if pages_label not in text:
        problems.append(f"listed email text is missing {pages_label}")
    if followers_label not in text:
        problems.append(f"listed email text is missing {followers_label}")
    for url in list(DIRECTORY_STRIPE.values()) + list(BOT_STRIPE.values()):
        if url not in text:
            problems.append(f"listed email text is missing {url}")
    if "logo-wordmark-dark.png" not in html:
        problems.append("listed email html is missing logo-wordmark-dark.png")
    if "logo-wordmark.svg" in html:
        problems.append("listed email html includes logo-wordmark.svg")
    return problems


def preview_listed_email(pages_label: str, followers_label: str) -> tuple[str, str]:
    """In-memory preview. It does not write a file and it does not send mail."""
    links = "\n".join(list(DIRECTORY_STRIPE.values()) + list(BOT_STRIPE.values()))
    text = f"{pages_label}\n{followers_label}\n{links}\n"
    html = '<img src="https://agentscouthq.com/logo-wordmark-dark.png" alt="built by AgentScout">'
    return text, html


def _artifact_labels(root: Path) -> tuple[dict, list[str]]:
    problems = []
    metrics_path = root / "api" / "metrics.json"
    if not metrics_path.is_file():
        return {}, ["api/metrics.json is missing, so the listed email has no artifact counts"]
    try:
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"api/metrics.json is not valid JSON ({exc})"]
    try:
        tools = f"{int(metrics['tools_count']):,}"
        pages = f"{int(metrics.get('pages_count') or metrics.get('indexed_pages_count')):,}+"
        followers = f"{int(metrics['x_combined_followers']):,}+"
    except (KeyError, TypeError, ValueError) as exc:
        return {}, [f"api/metrics.json is missing a count ({exc})"]
    return {"tools": tools, "pages": pages, "followers": followers}, problems


def indexnow_key_problems(root: Path) -> tuple[str, list[str]]:
    keys = [path for path in root.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}", path.stem)]
    if len(keys) != 1:
        return "", [f"expected one IndexNow key file at the tree root, found {len(keys)}"]
    body = keys[0].read_text(encoding="utf-8").strip()
    if body != keys[0].stem:
        return "", ["IndexNow key file body does not match its name"]
    return keys[0].stem, []


def measurement_evidence(document: object, kind: str, artifact_date: str, artifact_tools: int | None = None) -> tuple[list[str], str]:
    """The unthrottled numeric gate stays. A throttled Lighthouse file cannot pass it."""
    label = "cwv-seo-benchmark.json" if kind == "cwv" else "seo-vitals-latest.json"
    if not isinstance(document, dict):
        return [f"{label} is not an object"], ""
    problems = []
    generated = str(document.get("generated_at") or "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", generated):
        problems.append(f"{label} generated_at must be YYYY-MM-DD")
    elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", artifact_date or ""):
        problems.append(f"{label} cannot be dated because anim_state date is missing")
    elif generated < artifact_date:
        problems.append(f"{label} generated_at {generated} is older than the artifact date {artifact_date}")
    scope = document.get("scope") if isinstance(document.get("scope"), dict) else {}
    if scope.get("artifact_date") != artifact_date:
        problems.append(f"{label} scope.artifact_date does not match anim_state")
    if artifact_tools is not None and scope.get("artifact_tools") != artifact_tools:
        problems.append(f"{label} scope.artifact_tools does not match anim_state")
    source = document.get("source")
    if source not in LAB_SOURCES | FIELD_SOURCES:
        problems.append(f"{label} source is not a known lab or field source")
    if document.get("field_cwv") is True and source not in FIELD_SOURCES:
        problems.append(f"{label} field_cwv true is not valid for a lab source")
    targets = document.get("targets")
    if not isinstance(targets, list) or not targets or not all(isinstance(item, str) and item.startswith("http") for item in targets):
        problems.append(f"{label} targets must list the measured URLs")
        targets = []
    if kind == "cwv":
        if source != BENCHMARK_SOURCE or document.get("method") != BENCHMARK_METHOD or document.get("throttle") != "none":
            problems.append(
                f"{label} must be method {BENCHMARK_METHOD} with throttle none. "
                "Throttled Lighthouse is a separate lab signal and does not pass this gate."
            )
        thresholds = document.get("thresholds")
        if thresholds != UNTHROTTLED_THRESHOLDS:
            problems.append(f"{label} thresholds must stay LCP 2500, CLS 0.1, and TTFB 800")
        pages = document.get("pages")
        measured: list[str] = []
        if not isinstance(pages, list) or not pages:
            problems.append(f"{label} needs the measured pages")
        else:
            for page in pages:
                if not isinstance(page, dict):
                    problems.append(f"{label} has a page that is not an object")
                    continue
                url = page.get("url")
                if not isinstance(url, str) or url not in targets:
                    problems.append(f"{label} page {url} is not in targets")
                    continue
                measured.append(cwv_seo_benchmark.page_path(url))
                lcp, cls, ttfb = page.get("lcp_ms"), page.get("cls"), page.get("ttfb_ms")
                if isinstance(lcp, bool) or not isinstance(lcp, (int, float)) or lcp > 2500:
                    problems.append(f"{label} {url} lcp_ms {lcp} is over 2500 or missing")
                if isinstance(cls, bool) or not isinstance(cls, (int, float)) or cls > 0.1:
                    problems.append(f"{label} {url} cls {cls} is over 0.1 or missing")
                if isinstance(ttfb, bool) or not isinstance(ttfb, (int, float)) or ttfb > 800:
                    problems.append(f"{label} {url} ttfb_ms {ttfb} is over 800 or missing")
                if page.get("grade") == "PASS" and (
                    not isinstance(lcp, (int, float)) or lcp > 2500
                    or not isinstance(cls, (int, float)) or cls > 0.1
                    or not isinstance(ttfb, (int, float)) or ttfb > 800
                ):
                    problems.append(f"{label} {url} grade PASS contradicts the numeric gate")
            missing = [path for path in cwv_seo_benchmark.REQUIRED_PATHS if path not in measured]
            if missing:
                problems.append(f"{label} did not measure {', '.join(missing)}")
        omitted = document.get("not_measured")
        if not isinstance(omitted, list):
            problems.append(f"{label} not_measured must be a list")
        elif omitted:
            problems.append(f"{label} not_measured must be empty; an omitted page is not a reading")
            for item in omitted:
                reason = str(item.get("reason") or "") if isinstance(item, dict) else str(item)
                url = str(item.get("url") or "a page") if isinstance(item, dict) else "a page"
                if "networkidle" in reason.lower():
                    problems.append(
                        f"{label} {url} was skipped on networkidle. "
                        "Wait for load and read LCP, CLS, and TTFB. Leave Turnstile on the page."
                    )
    else:
        if document.get("throttle") not in (None, "none"):
            problems.append(f"{label} throttled Lighthouse does not meet the SEO 100 and Best Practices 100 gate")
        vitals = document.get("pagespeed_and_vitals")
        if not isinstance(vitals, dict) or len(vitals) < 5:
            problems.append(f"{label} needs 5 templates")
        else:
            for url, modes in vitals.items():
                if url not in targets:
                    problems.append(f"{label} template {url} is not in targets")
                if not isinstance(modes, dict):
                    problems.append(f"{label} {url} is not an object")
                    continue
                for mode in ("mobile", "desktop"):
                    scores = (modes.get(mode) or {}).get("scores") or {}
                    if scores.get("seo") != 100 or scores.get("best_practices") != 100:
                        problems.append(f"{label} {url} {mode} is not SEO 100 and Best Practices 100")
    if source == BENCHMARK_SOURCE:
        note = f"unthrottled lab benchmark dated {generated or 'unknown'}; not field CWV"
    elif source in LAB_SOURCES:
        note = f"source {source} is lab data and does not prove field CWV"
    elif source in FIELD_SOURCES:
        note = f"source {source} is field data, not a lab run"
    else:
        note = "source missing"
    return problems, note


def inline_script_problems(label: str, html: str) -> list[str]:
    import subprocess
    import tempfile
    scripts = re.findall(
        r"<script(?![^>]*type=['\"]application/(?:ld\+json|json)['\"])(?![^>]*src=)[^>]*>(.*?)</script>",
        html, re.S | re.I,
    )
    problems = []
    for index, code in enumerate(scripts, start=1):
        if not code.strip():
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
            handle.write(code)
            path = handle.name
        result = subprocess.run(["node", "--check", path], capture_output=True, text=True)
        if result.returncode != 0:
            problems.append(f"{label} inline script {index} failed node --check")
    return problems


def header_problems(headers: dict) -> list[str]:
    lowered = {str(key).lower(): str(value) for key, value in headers.items()}
    problems = []
    if "cloudflare" not in lowered.get("server", "").lower():
        problems.append("live homepage server is not Cloudflare")
    if "max-age=31536000" not in lowered.get("strict-transport-security", ""):
        problems.append("live homepage is missing HSTS max-age=31536000")
    if lowered.get("x-frame-options", "").upper() not in ("DENY", "SAMEORIGIN"):
        problems.append("live homepage X-Frame-Options is not DENY or SAMEORIGIN")
    if lowered.get("x-content-type-options", "").lower() != "nosniff":
        problems.append("live homepage is missing nosniff")
    if "strict-origin" not in lowered.get("referrer-policy", "").lower():
        problems.append("live homepage Referrer-Policy is not strict-origin")
    return problems


def predeploy(root: Path) -> AuditResult:
    result = AuditResult()
    tool_count, _mcp = _catalog_counts(root)
    result.category_acceptance_claimed = False
    result.settle("animation", publish_gate.artifact_animation_problems(root), "stamp matches anim_state and tools.json")
    result.settle("products", publish_gate.product_snapshot_problems(root), "snapshot matches api/products.json")
    category_problems, accepted = synthetic_category_problems(root)
    result.synthetic_accepted = accepted
    result.settle("categories", category_problems, f"synthetic inner check accepted {accepted}; no live POST")
    record_coverage(result, root, tool_count)
    result.settle("form-fields", form_field_problems(root), "14 submit form ids are present")
    result.settle("template-count", template_count_problems(root), "bot-templates rows match anim_state")
    result.settle("stripe-files", stripe_file_problems(root), "directory and bot Stripe URLs are wired in the tree")
    labels, label_problems = _artifact_labels(root)
    if label_problems:
        result.unknown("listed-email: " + "; ".join(label_problems))
    else:
        text, html = preview_listed_email(labels["pages"], labels["followers"])
        result.settle(
            "listed-email",
            listed_email_problems(text, html, labels["pages"], labels["followers"]),
            "in-memory preview has the artifact counts, Stripe links, and dark wordmark",
        )
    script_problems = []
    for rel in ("index.html", "submit.html", "sponsor.html"):
        script_problems.extend(inline_script_problems(rel, _read(root, rel)))
    result.settle("inline-scripts", script_problems, "node --check passed on index, submit, and sponsor")
    key, key_problems = indexnow_key_problems(root)
    detail = f"{key}.txt matches its body; api.indexnow.org was not called" if key else "key file checked"
    result.settle("indexnow-file", key_problems, detail)
    artifact_date, artifact_tools = _artifact_binding(root)
    for rel in ("data/cwv-seo-benchmark.json", "data/cwv-candidate-local.json"):
        result.settle(
            rel,
            benchmark_document_problems(root / rel, artifact_date, artifact_tools),
            "unthrottled load readings for the six fixture targets and submit.html",
        )
    result.later("postdeploy-http: Stripe Checkout, live page counts, Cloudflare headers, and the cloner block run in --live")
    result.later(
        "postdeploy-vitals: predeploy requires data/cwv-seo-benchmark.json (current live) and "
        "data/cwv-candidate-local.json (this tree on 127.0.0.1). A missing file is a failure. "
        "seo-vitals-latest.json is still optional and is not Lighthouse-simulated LCP. "
        "scripts/pack_src/seo_site_audit.py does not measure CWV."
    )
    result.later("postdeploy-animation: live stamp lag is reported by --live and does not fail this artifact")
    return result


def _http(url: str, method: str = "GET", data: bytes | None = None, headers: dict | None = None):
    merged = {"User-Agent": "AgentScout-DailyDeepAudit/1.0"}
    if headers:
        merged.update(headers)
    request = urllib.request.Request(url, data=data, headers=merged, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "ignore")
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, body


def mcp_body_problems(status: int, body: str) -> list[str]:
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return ["list_packages response is not JSON"]
    if not isinstance(parsed, dict):
        return ["list_packages response is not an object"]
    structured = (parsed.get("result") or {}).get("structuredContent")
    if not isinstance(structured, dict):
        content = ((parsed.get("result") or {}).get("content") or [{}])
        text = content[0].get("text") if content and isinstance(content[0], dict) else ""
        try:
            structured = json.loads(text) if text else None
        except json.JSONDecodeError:
            structured = None
    if not isinstance(structured, dict):
        return ["list_packages has no structuredContent"]
    stale = [token for token in ("2,467+", "2,095+", "2,104+", "2,350+") if token in body]
    return publish_gate.list_packages_problems(status, structured, stale)


def live(root: Path, fetch=None) -> AuditResult:
    """Origin both ways and semantic list_packages. No category POST. No acceptance claim."""
    fetch = fetch or _http
    result = AuditResult()
    result.category_acceptance_claimed = False
    no_status, _no_headers, _no_body = fetch(SUBMIT_URL, "OPTIONS", None, None)
    yes_headers_in = {
        "Origin": ALLOWED_ORIGIN,
        "Access-Control-Request-Method": "POST",
    }
    yes_status, yes_headers, _yes_body = fetch(SUBMIT_URL, "OPTIONS", None, yes_headers_in)
    for item in publish_gate.preflight_problems(no_status, origin_present=False):
        result.err(item)
    for item in publish_gate.preflight_problems(yes_status, origin_present=True):
        result.err(item)
    allow = ""
    if isinstance(yes_headers, dict):
        allow = yes_headers.get("Access-Control-Allow-Origin") or yes_headers.get("access-control-allow-origin") or ""
    if yes_status == 204 and allow != ALLOWED_ORIGIN:
        result.err(f"allowed-origin preflight allow-origin is {allow!r}")
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "list_packages", "arguments": {}},
    }).encode()
    mcp_status, _mcp_headers, mcp_body = fetch(
        MCP_URL,
        "POST",
        payload,
        {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
    )
    for item in mcp_body_problems(mcp_status, mcp_body):
        result.err(item)
    live_pages(result, fetch)
    stripe_live(result, fetch)
    edge_live(result, fetch)
    indexnow_live(result, root, fetch)
    measurements_live(result, root)
    lead_gen_live(result, fetch)
    result.ok("category acceptance was not claimed from the network and /submit was not posted")
    result.live_posts = 0
    return result


def live_pages(result: AuditResult, fetch) -> None:
    try:
        status, _headers, body = fetch("https://agentscouthq.com/api/metrics.json", "GET", None, None)
        metrics = json.loads(body) if status == 200 else {}
        tools = int(metrics["tools_count"])
        pages = f"{int(metrics.get('pages_count') or metrics['indexed_pages_count']):,}+"
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        result.err("live /api/metrics.json did not return the tool and page counts")
        return
    if status != 200:
        result.err(f"live /api/metrics.json HTTP {status}")
        return
    result.ok(f"live metrics HTTP 200 tools={tools:,} pages={pages}")
    for url in LIVE_PAGES:
        page_status, _page_headers, page = fetch(url, "GET", None, None)
        stale = [token for token in STALE_TOKENS if token in page]
        if page_status != 200 or stale:
            result.err(f"{url} HTTP {page_status} stale={stale}")
    home_status, _home_headers, home = fetch("https://agentscouthq.com/", "GET", None, None)
    if pages not in home:
        result.later(f"live homepage does not yet show {pages}; that is postdeploy lag, not an artifact failure")
    else:
        result.ok(f"live homepage shows {pages}")


def stripe_live(result: AuditResult, fetch) -> None:
    for label, url in DIRECTORY_STRIPE.items():
        status, _headers, body = fetch(url, "GET", None, {"User-Agent": "Mozilla/5.0"})
        stale = [token for token in STALE_TOKENS if token in body]
        if status != 200 or stale or "no longer active" in body.lower():
            result.err(f"Stripe Checkout {label} HTTP {status} stale={stale}")
        else:
            result.ok(f"Stripe Checkout {label} HTTP 200")


def edge_live(result: AuditResult, fetch) -> None:
    status, headers, _body = fetch("https://agentscouthq.com/", "GET", None, {"User-Agent": CRAWLER_UA})
    if status != 200:
        result.err(f"crawler homepage HTTP {status}")
    else:
        for item in header_problems(headers or {}):
            result.err(item)
    blocked, _blocked_headers, _blocked_body = fetch("https://agentscouthq.com/", "GET", None, {"User-Agent": CLONER_UA})
    if blocked != 403:
        result.err(f"HTTrack homepage HTTP {blocked}, expected 403")
    else:
        result.ok("HTTrack is blocked with HTTP 403")


def indexnow_live(result: AuditResult, root: Path, fetch) -> None:
    key, problems = indexnow_key_problems(root)
    for item in problems:
        result.err(item)
    if not key:
        return
    status, _headers, body = fetch(f"https://agentscouthq.com/{key}.txt", "GET", None, None)
    if status != 200 or body.strip() != key:
        result.err(f"IndexNow key URL HTTP {status}; body matches the file: {body.strip() == key}")
    else:
        result.ok(f"IndexNow key URL returned the file body; api.indexnow.org was not called")


def _artifact_binding(root: Path) -> tuple[str, int | None]:
    path = root / "data" / "anim_state.json"
    if not path.is_file():
        return "", None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "", None
    tools = state.get("tools")
    return str(state.get("date") or ""), tools if isinstance(tools, int) else None


def benchmark_document_problems(path: Path, artifact_date: str, artifact_tools: int | None) -> list[str]:
    """A missing or incomplete seven-URL reading is a failure, not an unknown."""
    if not path.is_file():
        return [f"{path.name} is missing; an unmeasured benchmark is not a pass"]
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path.name} is not valid JSON ({exc})"]
    problems, _note = measurement_evidence(document, "cwv", artifact_date, artifact_tools)
    return problems


def measurements_live(result: AuditResult, root: Path) -> None:
    cwv_path = Path(os.environ["AGENTSCOUT_CWV_JSON"]) if os.environ.get("AGENTSCOUT_CWV_JSON") else root / "data" / "cwv-seo-benchmark.json"
    vitals_path = Path(os.environ["AGENTSCOUT_VITALS_JSON"]) if os.environ.get("AGENTSCOUT_VITALS_JSON") else root / "data" / "seo-vitals-latest.json"
    artifact_date, artifact_tools = _artifact_binding(root)
    how = (
        "data/cwv-seo-benchmark.json is required in the tree. A missing file fails. "
        "cwv-seo-benchmark.json must use method cwv_seo_benchmark.measure_url, throttle none, "
        "thresholds lcp_ms 2500, cls 0.1, ttfb_ms 800, generated_at on or after anim_state date, "
        "and scope.artifact_date plus scope.artifact_tools. "
        "Do not copy throttled Lighthouse LCP into that file or set field_cwv true. "
        "A networkidle timeout is not a measured page: wait for load, then read the performance entries. "
        "seo-vitals-latest.json still requires SEO 100 and Best Practices 100 with throttle none. "
        "scripts/pack_src/seo_site_audit.py does not measure CWV. This audit does not write either file."
    )
    if not cwv_path.is_file():
        result.err(f"cwv-lab-or-field: {cwv_path} is missing; an unmeasured benchmark is not a pass. {how}")
    else:
        result.settle("cwv-lab-or-field", benchmark_document_problems(cwv_path, artifact_date, artifact_tools), "committed unthrottled readings match the gate")
    for path, kind, name in ((vitals_path, "vitals", "seo-vitals"),):
        if not path.is_file():
            result.unknown(f"{name}: {path} is not in the tree. {how}")
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            result.err(f"{name}: {path.name} is not valid JSON ({exc})")
            continue
        problems, note = measurement_evidence(document, kind, artifact_date, artifact_tools)
        result.settle(name, problems, note)


def lead_gen_live(result: AuditResult, fetch) -> None:
    status, _headers, body = fetch("https://agentscouthq.com/bot-store/lead-gen/", "GET", None, None)
    if status != 200 or "Agent Agent" in body:
        result.err(f"live lead-gen HTTP {status}, Agent Agent present: {'Agent Agent' in body}")
    else:
        result.ok("live lead-gen HTTP 200 with no Agent Agent title")


def render(result: AuditResult, label: str) -> int:
    print(f"=== {label} ===")
    for line in result.passes:
        print(f"  [PASS] {line}")
    for line in result.problems:
        print(f"  [FAIL] {line}")
    for line in result.deferred:
        print(f"  [DEFERRED] {line}")
    for line in result.unverified:
        print(f"  [UNVERIFIED] {line}")
    print(
        f"\nSUMMARY: {len(result.passes)} PASSED, {len(result.problems)} FAILED, "
        f"{len(result.deferred)} DEFERRED, {len(result.unverified)} UNVERIFIED"
    )
    return 1 if result.problems or result.unverified else 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    mode = "predeploy"
    if "--live" in args:
        mode = "live"
    if "--predeploy" in args and "--live" in args:
        root = resolve_root()
        pre = render(predeploy(root), "PREDEPLOY")
        post = render(live(root), "LIVE")
        return 1 if pre or post else 0
    root = resolve_root()
    if mode == "live":
        return render(live(root), "LIVE")
    return render(predeploy(root), "PREDEPLOY")
