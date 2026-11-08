"""Publish checks split into a local artifact and the site already live.

The morning deep audit mixed those two. A preflight with no Origin, a Turnstile
rejection, a product list with no directory page-count string, and a new local
animation stamp are not catalog defects. This module does not send requests.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

TURNSTILE_REJECTION = "Bot check failed."
PRODUCT_GROUPS = ("packages", "addons", "bot_templates", "agent_packs")
ANIMATION_PAGES = ("index.html", "bot-store/index.html", "videos/index.html")


def preflight_problems(status: int, origin_present: bool) -> list[str]:
    """OPTIONS /submit. No Origin must stay 403. An allowed origin must stay 204."""
    if origin_present:
        if status != 204:
            return [f"OPTIONS with an allowed origin returned {status}, expected 204"]
        return []
    if status != 403:
        return [f"OPTIONS without Origin returned {status}, expected 403"]
    return []


def category_probe_problems(responses: list[tuple[str, str]]) -> list[str]:
    """Live category POSTs. Uniform Turnstile rejections are not category verdicts.

    A different body is reported. Matching the allowlist is a separate local check.
    """
    if not responses:
        return ["category probe was empty"]
    unexpected = [f"{name}: {body}" for name, body in responses if body != TURNSTILE_REJECTION]
    return unexpected


def category_names_problems(option_values: list[str], catalog: list[str]) -> list[str]:
    if list(option_values) != list(catalog) or not catalog:
        return ["submit category options do not match categories.json"]
    if any(not isinstance(value, str) or not value.strip() for value in catalog):
        return ["categories.json has a blank category"]
    return []


def category_accepted(name: str, catalog: list[str]) -> bool:
    """Local allowlist check. It does not contact Turnstile or /submit."""
    return name in catalog


def product_rows(document: dict) -> list[dict]:
    if isinstance(document.get("products"), list):
        return [row for row in document["products"] if isinstance(row, dict)]
    rows: list[dict] = []
    for key in PRODUCT_GROUPS:
        value = document.get(key) or []
        if isinstance(value, list):
            rows.extend(row for row in value if isinstance(row, dict))
    return rows


def product_catalog_problems(document: object) -> list[str]:
    """Structured list_packages / products.json check. A pages string is not required."""
    if not isinstance(document, dict):
        return ["product catalog is not an object"]
    rows = product_rows(document)
    problems: list[str] = []
    if not rows:
        problems.append("product catalog has no products")
        return problems
    declared = document.get("total_products")
    if declared is not None and declared != len(rows):
        problems.append(f"total_products is {declared}, product rows are {len(rows)}")
    seen: set[str] = set()
    for index, row in enumerate(rows):
        ident = row.get("id")
        if not isinstance(ident, str) or not ident:
            problems.append(f"product {index} is missing id")
            continue
        if ident in seen:
            problems.append(f"duplicate product id {ident}")
        seen.add(ident)
        if not isinstance(row.get("name"), str) or not row["name"].strip():
            problems.append(f"{ident} is missing name")
        price = row.get("price_usd")
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            problems.append(f"{ident} is missing price_usd")
    return problems


def list_packages_problems(status: int, document: object, stale: list[str] | None = None) -> list[str]:
    """HTTP 200, structured products, and no stale tokens. pages_str is ignored."""
    problems: list[str] = []
    if status != 200:
        problems.append(f"list_packages HTTP {status}")
    else:
        problems.extend(product_catalog_problems(document))
    if stale:
        problems.append("list_packages stale tokens: " + ", ".join(stale))
    return problems


def animation_token(state: dict) -> str:
    day = str(state.get("date") or "").replace("-", "")
    if not re.fullmatch(r"\d{8}", day):
        raise ValueError("anim_state date is not YYYY-MM-DD")
    return f"{day}-{int(state['tools'])}"


def catalog_counts(tools: object) -> tuple[int, int]:
    rows = tools if isinstance(tools, list) else []
    if isinstance(tools, dict):
        rows = tools.get("tools") or []
    if not isinstance(rows, list):
        return 0, 0
    mcp = sum(1 for row in rows if isinstance(row, dict) and row.get("category") == "MCP servers")
    return len(rows), mcp


def animation_predeploy_problems(state: dict, pages: dict[str, str], tool_count: int, mcp_count: int) -> list[str]:
    """The artifact's own stamp. Today's date and the already-live count are not the stamp."""
    problems: list[str] = []
    if int(state.get("tools") or -1) != int(tool_count):
        problems.append(f"anim_state tools {state.get('tools')} != catalog tools {tool_count}")
    if int(state.get("mcp") or -1) != int(mcp_count):
        problems.append(f"anim_state mcp {state.get('mcp')} != catalog mcp {mcp_count}")
    try:
        token = "?v=" + animation_token(state)
    except (KeyError, TypeError, ValueError) as exc:
        return problems + [f"anim_state cannot make a cache buster ({exc})"]
    for name, text in pages.items():
        if token not in text:
            problems.append(f"{name} is missing the artifact cache buster {token}")
    return problems


def animation_live_token_is_artifact_defect(state: dict, live_tools: int, pages_contain_live_token: bool) -> bool:
    """A newer local count will not contain the previous live token. That absence is not a defect."""
    local = animation_token(state)
    live = f"{str(state['date']).replace('-', '')}-{int(live_tools)}"
    if local == live:
        return not pages_contain_live_token
    return False


def artifact_animation_problems(root: Path) -> list[str]:
    state_path = root / "data" / "anim_state.json"
    tools_path = root / "tools.json"
    if not state_path.is_file():
        return ["data/anim_state.json is missing"]
    if not tools_path.is_file():
        return ["tools.json is missing"]
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        tools = json.loads(tools_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"animation artifact is not valid JSON ({exc})"]
    pages: dict[str, str] = {}
    for rel in ANIMATION_PAGES:
        path = root / rel
        if not path.is_file():
            return [f"{rel} is missing"]
        pages[rel] = path.read_text(encoding="utf-8")
    tool_count, mcp_count = catalog_counts(tools)
    return animation_predeploy_problems(state, pages, tool_count, mcp_count)


def product_snapshot_problems(root: Path) -> list[str]:
    src = root / "api" / "products.json"
    snap = root / "cloudflare-mcp-worker" / "products_snapshot.json"
    if not src.is_file():
        return ["api/products.json is missing"]
    if not snap.is_file():
        return ["cloudflare-mcp-worker/products_snapshot.json is missing"]
    src_text = src.read_text(encoding="utf-8")
    snap_text = snap.read_text(encoding="utf-8")
    problems: list[str] = []
    if src_text != snap_text:
        problems.append("MCP products snapshot differs from api/products.json")
    try:
        document = json.loads(src_text)
    except json.JSONDecodeError as exc:
        return problems + [f"api/products.json is not valid JSON ({exc})"]
    return problems + product_catalog_problems(document)
