"""Single source for sitewide counts. Run before the other builders, then again after sitemap.xml.

Writes data/site_counts.json. api/metrics.json and data/site_metrics.json are derived from it
(metrics also keeps analytics). Bot templates come from the rows build_bot_templates puts on
/bot-templates/, not from a frozen sum of the source files.
"""
import glob, json, os, re
from datetime import datetime, timezone, timedelta

PATH = "data/site_counts.json"
METRICS = "api/metrics.json"
SITE_METRICS = "data/site_metrics.json"


def _now():
    return datetime.now(timezone(timedelta(hours=-7)))


def load_tools(path="tools.json"):
    if not os.path.exists(path):
        return []
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("tools") or []
    return data


def free_items(tools):
    import build_extras
    return build_extras.free_tool_items(tools)


def sitemap_count(path="sitemap.xml"):
    if not os.path.exists(path):
        return 0
    return open(path, encoding="utf-8").read().count("<loc>")


def bot_template_count():
    import build_bot_templates
    return int(build_bot_templates.live_bot_template_count() or 0)


def _read(path):
    if not os.path.exists(path):
        return {}
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}


def followers():
    """X follower totals. A scoreboard row fetched today wins. Otherwise keep the last
    published totals. Do not lift them with a hardcoded floor."""
    prev = _read(METRICS)
    old = (_read(PATH).get("followers") or {})
    clamp = int(old.get("clampdown19") or prev.get("x_clampdown19_followers") or 0)
    scout = int(old.get("agentscouthq") or prev.get("x_agentscouthq_followers") or 0)
    sb = {}
    for p in (
        "/workspace/data/30-day-sprint-tracker.json",
        "/workspace/data/growth-sprint-30d.json",
        "/workspace/data/30-day-growth-scoreboard.json",
        "data/30-day-growth-scoreboard.json",
        "data/30-day-sprint-tracker.json",
    ):
        if os.path.exists(p):
            sb = _read(p)
            if sb:
                break
    snap = {}
    for p in sorted(glob.glob("/workspace/notes/daily-traffic/*-snapshot.json"), reverse=True):
        snap = _read(p)
        if snap:
            break
    cur = sb.get("current") or {}
    today = _now().strftime("%Y-%m-%d")
    fetched = str(cur.get("x_followers_fetched_at") or cur.get("updated_at") or "")[:10]
    if fetched == today and cur.get("clampdown19_followers") and cur.get("agentscouthq_followers") is not None:
        clamp = int(cur["clampdown19_followers"])
        scout = int(cur["agentscouthq_followers"])
    elif not clamp:
        clamp = int(snap.get("x", {}).get("clampdown19", {}).get("followers") or 0)
        scout = int(snap.get("x", {}).get("agentscouthq", {}).get("followers") or scout or 0)
    return {"clampdown19": clamp, "agentscouthq": scout, "combined": clamp + scout}


def analytics():
    """Pageviews and Search Console impressions from the newest snapshot.
    The last published api/metrics.json is the fallback. No frozen literal."""
    prev = _read(METRICS)
    sb = {}
    for p in (
        "/workspace/data/30-day-sprint-tracker.json",
        "/workspace/data/growth-sprint-30d.json",
        "/workspace/data/30-day-growth-scoreboard.json",
        "data/30-day-growth-scoreboard.json",
        "data/30-day-sprint-tracker.json",
    ):
        if os.path.exists(p):
            sb = _read(p)
            if sb:
                break
    snap = {}
    for p in sorted(glob.glob("/workspace/notes/daily-traffic/*-snapshot.json"), reverse=True):
        snap = _read(p)
        if snap:
            break
    cur = sb.get("current") or {}

    def pick(*vals, fallback_key, alt_key=None):
        for v in vals:
            if v:
                return int(v)
        for key in (fallback_key, alt_key):
            if key and prev.get(key):
                return int(prev[key])
        return 0

    weekly_pv = pick(
        cur.get("weekly_page_views_tracker_7d"),
        (snap.get("ga4") or {}).get("7d", {}).get("screenPageViews"),
        fallback_key="weekly_page_views",
        alt_key="pageviews_7d",
    )
    pv_30d = pick(
        (snap.get("ga4") or {}).get("28d", {}).get("screenPageViews"),
        fallback_key="pageviews_30d",
    )
    ga4_7d = pick(
        cur.get("weekly_visitors_ga4_7d"),
        (snap.get("ga4") or {}).get("7d", {}).get("activeUsers"),
        fallback_key="weekly_visitors_ga4",
    )
    users_30d = pick(
        (snap.get("ga4") or {}).get("28d", {}).get("activeUsers"),
        fallback_key="active_users_30d",
    )
    arrivals = pick(cur.get("weekly_external_arrivals_tracker_7d"), fallback_key="weekly_external_arrivals")
    gsc = pick(
        cur.get("gsc_impressions_7d"),
        cur.get("gsc_7d_impressions"),
        (snap.get("gsc") or {}).get("7d", {}).get("impressions") if isinstance(snap.get("gsc"), dict) else None,
        snap.get("gsc_impressions_7d"),
        snap.get("gsc_7d_impressions"),
        fallback_key="gsc_impressions_7d",
    )
    return {
        "pageviews_7d": weekly_pv,
        "weekly_page_views": weekly_pv,
        "pageviews_30d": pv_30d,
        "weekly_visitors_ga4": ga4_7d,
        "weekly_external_arrivals": arrivals,
        "active_users_30d": users_30d,
        "gsc_impressions_7d": gsc,
    }


def compute(tools=None, pages=None, bot_templates=None):
    tools = load_tools() if tools is None else tools
    items = free_items(tools)
    free_cats = {x.get("category") for x in items if x.get("category") and x.get("category") != "other"}
    used = {x.get("category") for x in tools if x.get("category") and x.get("category") != "other"}
    mcp = sum(1 for x in tools if x.get("category") == "MCP servers")
    pages = sitemap_count() if pages is None else pages
    if bot_templates is None:
        bot_templates = bot_template_count()
        if not bot_templates:
            bot_templates = int((_read(PATH).get("bot_templates") or 0))
    return {
        "tools": len(tools),
        "free_tools": len(items),
        "free_categories": len(free_cats),
        "mcp_servers": mcp,
        "categories": len(used),
        "pages_sitemap": int(pages or 0),
        "bot_templates": int(bot_templates or 0),
        "followers": followers(),
        "computed_at": _now().isoformat(timespec="seconds"),
    }


def save(counts):
    os.makedirs("data", exist_ok=True)
    open(PATH, "w", encoding="utf-8").write(json.dumps(counts, indent=2) + "\n")
    return counts


def load():
    data = _read(PATH)
    return data or None


def require(tools=None):
    """Return site_counts, recomputing when the tool list length has moved."""
    tools = load_tools() if tools is None else tools
    cur = load()
    if not cur or cur.get("tools") != len(tools) or "free_tools" not in cur:
        return write(tools)
    return cur


def metrics_catalog():
    """Directory totals the homepage reads from api/metrics.json.

    tools_count and mcp_servers_count are the source of truth for a catalog claim.
    A missing file falls back to the same recount that writes those fields.
    """
    m = _read(METRICS)
    tools = int(m.get("tools_count") or 0)
    mcp = int(m.get("mcp_servers_count") or m.get("mcp_count") or 0)
    if not tools or not mcp:
        counted = require()
        tools = tools or int(counted.get("tools") or 0)
        mcp = mcp or int(counted.get("mcp_servers") or 0)
    updated = str(m.get("updated") or "")
    display = str(m.get("updated_display") or updated)
    return {"tools": tools, "mcp": mcp, "updated": updated, "updated_display": display}


def write(tools=None):
    counts = compute(tools)
    save(counts)
    mirror_site_metrics(counts)
    patch_origin_sentence(counts)
    return counts


def set_bot_templates(n):
    """Called by build_bot_templates after it counts the rows it rendered."""
    counts = load() or compute()
    counts["bot_templates"] = int(n)
    counts["computed_at"] = _now().isoformat(timespec="seconds")
    save(counts)
    mirror_site_metrics(counts)
    return counts


def refresh_pages():
    """Second pass: sitemap.xml is final, so the page count can be rewritten."""
    counts = load() or write()
    pages = sitemap_count()
    if pages:
        counts["pages_sitemap"] = pages
    bt = bot_template_count()
    if bt:
        counts["bot_templates"] = bt
    counts["computed_at"] = _now().isoformat(timespec="seconds")
    save(counts)
    mirror_site_metrics(counts)
    sync_metrics_counts(counts)
    patch_origin_sentence(counts)
    return counts


def sync_metrics_counts(counts):
    """Keep api/metrics.json catalog fields aligned. Analytics stay as published."""
    m = _read(METRICS)
    if not m:
        return
    fol = counts.get("followers") or {}
    m["tools_count"] = counts["tools"]
    m["mcp_servers_count"] = counts["mcp_servers"]
    m["categories_count"] = counts["categories"]
    m["indexed_pages_count"] = counts["pages_sitemap"]
    m["pages_count"] = counts["pages_sitemap"]
    m["mcp_count"] = counts["mcp_servers"]
    if fol.get("clampdown19"):
        m["x_clampdown19_followers"] = fol["clampdown19"]
        m["x_agentscouthq_followers"] = fol["agentscouthq"]
        m["x_combined_followers"] = fol["combined"]
    os.makedirs("api", exist_ok=True)
    open(METRICS, "w", encoding="utf-8").write(json.dumps(m, indent=2) + "\n")


def mirror_site_metrics(counts, metrics=None):
    """data/site_metrics.json is a mirror, not a source. Catalog numbers come from site_counts."""
    metrics = metrics or _read(METRICS)
    a = analytics()
    fol = counts.get("followers") or {}
    pt = _now()
    doc = {
        "tools_count": counts["tools"],
        "mcp_servers_count": counts["mcp_servers"],
        "categories_count": counts["categories"],
        "bot_templates_count": counts["bot_templates"],
        "indexed_pages_count": counts["pages_sitemap"],
        "pages_count": counts["pages_sitemap"],
        "mcp_count": counts["mcp_servers"],
        "free_tools_count": counts["free_tools"],
        "free_categories_count": counts["free_categories"],
        "pageviews_7d": int(metrics.get("pageviews_7d") or a["pageviews_7d"] or 0),
        "x_clampdown19_followers": int(fol.get("clampdown19") or 0),
        "x_agentscouthq_followers": int(fol.get("agentscouthq") or 0),
        "x_combined_followers": int(fol.get("combined") or 0),
        "pageviews_30d": int(metrics.get("pageviews_30d") or a["pageviews_30d"] or 0),
        "weekly_page_views": int(metrics.get("weekly_page_views") or a["weekly_page_views"] or 0),
        "gsc_7d_impressions": int(metrics.get("gsc_impressions_7d") or a["gsc_impressions_7d"] or 0),
        "gsc_impressions_7d": int(metrics.get("gsc_impressions_7d") or a["gsc_impressions_7d"] or 0),
        "updated_at": pt.isoformat(timespec="seconds"),
        "updated_display": pt.strftime("%b %-d, %Y"),
        "source": PATH,
    }
    os.makedirs("data", exist_ok=True)
    open(SITE_METRICS, "w", encoding="utf-8").write(json.dumps(doc, indent=2) + "\n")


def patch_origin_sentence(counts):
    """how-it-started.html states the current catalog. Dated October news pages are left alone."""
    path = "how-it-started.html"
    if not os.path.exists(path):
        return
    fol = counts.get("followers") or {}
    display = _now().strftime("%b %-d, %Y")
    m = _read(METRICS)
    if m.get("updated_display"):
        display = m["updated_display"]
    sentence = (
        f"As of {display}, this site lists {counts['tools']:,} tools, including {counts['mcp_servers']:,} MCP servers, "
        f"and {counts['bot_templates']:,} templates. Combined followers of @clampdown19 and @AgentScoutHQ: {fol.get('combined', 0):,}."
    )
    text = open(path, encoding="utf-8").read()
    new, n = re.subn(
        r"As of [^.<]{0,40}, this site lists [\d,]+ tools, including [\d,]+ MCP servers, and [\d,]+ templates\. Combined followers of @clampdown19 and @AgentScoutHQ: [\d,]+\.",
        sentence,
        text,
        count=1,
    )
    if n and new != text:
        open(path, "w", encoding="utf-8").write(new)


def signature():
    c = load() or {}
    return [c.get(k) for k in ("tools", "free_tools", "mcp_servers", "categories", "pages_sitemap", "bot_templates")]


def main():
    counts = write()
    print(
        "site_counts:",
        f"tools={counts['tools']}",
        f"free={counts['free_tools']}",
        f"free_cats={counts['free_categories']}",
        f"mcp={counts['mcp_servers']}",
        f"categories={counts['categories']}",
        f"pages={counts['pages_sitemap']}",
        f"templates={counts['bot_templates']}",
        f"followers={counts['followers']['combined']}",
    )
    return counts


if __name__ == "__main__":
    main()
