"""Repo entrypoint for the 7AM deep audit.

The box copy at /workspace/scripts/daily_deep_audit.py is not in git. This module
is the source that copy should be replaced by. It does not POST /submit, does not
bypass Turnstile, and does not write the tree it reads.

  AGENTSCOUT_ROOT=<tree> python3 daily_deep_audit.py --predeploy
  AGENTSCOUT_ROOT=<tree> python3 daily_deep_audit.py --live

--predeploy is the publish gate (local artifact, nav, footer, zips, categories).
--live checks the deployed origin rule and list_packages shape. A live page that
still shows yesterday's animation stamp is reported and does not fail --predeploy.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import publish_gate

STALE_ROOT = Path("/workspace/agent-tool-finder")
SUBMIT_URL = "https://api.agentscouthq.com/submit"
MCP_URL = "https://mcp.agentscouthq.com/mcp"
ALLOWED_ORIGIN = "https://agentscouthq.com"
FULL_SITE_TOOLS = 2000
NAV_SKIP = {"404.html", "google823b89b55b70e740.html"}


class AuditResult:
    def __init__(self) -> None:
        self.problems: list[str] = []
        self.passes: list[str] = []
        self.synthetic_accepted = 0
        self.category_acceptance_claimed = False
        self.live_posts = 0

    def ok(self, message: str) -> None:
        self.passes.append(message)

    def err(self, message: str) -> None:
        self.problems.append(message)


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


def _full_site(tool_count: int) -> bool:
    return tool_count >= FULL_SITE_TOOLS


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
    if _full_site(tool_count) and checked <= 2000:
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


def coverage_problems(root: Path, tool_count: int) -> list[str]:
    """Nav, footer, submit links, scroll arrows, and the read-only zip and CTA checks."""
    import verify_4tier_ctas
    import verify_bot_zip_packages

    problems = []
    problems.extend(nav_footer_problems(root, tool_count))
    problems.extend(submit_link_problems(root))
    problems.extend(scroll_problems(root))
    if not _full_site(tool_count):
        return problems
    packs = root / "bot-packages" / "25-agent-packs"
    if not packs.is_dir():
        problems.append("bot packages are missing from a full catalog")
    else:
        bad, _passed = verify_bot_zip_packages._audit(root)
        problems.extend(bad)
    try:
        problems.extend(verify_4tier_ctas.problems(root))
    except OSError as exc:
        problems.append(f"4-tier CTA check could not read the tree ({exc})")
    pack_pages = list((root / "bot-store").glob("*/index.html")) if (root / "bot-store").is_dir() else []
    if len(pack_pages) != 25:
        problems.append(f"bot-store pack pages are {len(pack_pages)}, expected 25")
    for page in pack_pages:
        if "Agent Agent" in page.read_text(encoding="utf-8", errors="ignore"):
            problems.append(f"{page.relative_to(root).as_posix()} contains Agent Agent")
    return problems


def local_contract_problems(root: Path) -> tuple[list[str], int]:
    problems = []
    problems.extend(publish_gate.artifact_animation_problems(root))
    problems.extend(publish_gate.product_snapshot_problems(root))
    category_problems, accepted = synthetic_category_problems(root)
    problems.extend(category_problems)
    return problems, accepted


def predeploy(root: Path) -> AuditResult:
    result = AuditResult()
    tool_count, _mcp = _catalog_counts(root)
    problems, accepted = local_contract_problems(root)
    result.synthetic_accepted = accepted
    result.category_acceptance_claimed = False
    for item in problems:
        result.err(item)
    for item in coverage_problems(root, tool_count):
        result.err(item)
    if not result.problems:
        result.ok(
            f"predeploy artifact checks passed for {root} "
            f"({result.synthetic_accepted} categories accepted by the synthetic inner check, no live POST)"
        )
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
    if not any(item.startswith("OPTIONS") or item.startswith("list_packages") or "allow-origin" in item for item in result.problems):
        result.ok("live origin rule and list_packages shape passed; category acceptance was not claimed from the network")
    result.live_posts = 0
    return result


def render(result: AuditResult, label: str) -> int:
    print(f"=== {label} ===")
    for line in result.passes:
        print(f"  [PASS] {line}")
    for line in result.problems:
        print(f"  [FAIL] {line}")
    print(f"\nSUMMARY: {len(result.passes)} PASSED, {len(result.problems)} FAILED")
    return 1 if result.problems else 0


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
