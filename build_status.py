"""Link-check evidence on the homepage, /mcp/, and each MCP server listing.

Every time, status, and history line is read from data/mcp_link_status.json,
data/mcp_history.json, or api/tools.json. A server with no link-status row is
"not yet checked". Nothing here is inferred from the clock.
"""
import glob, html, json, os, re

import build_aeo

e = html.escape
B = "https://agentscouthq.com/"
AFF = "AgentScout (agentscouthq.com) is not affiliated with other projects named AgentScout."
MONTHS = ("", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
SKIP_MCP = {"mcp/connect.html", "mcp/pricing.html", "mcp/link-status.html"}


def _pretty_day(day):
    y, m, d = day.split("-")
    return f"{MONTHS[int(m)]} {int(d)}, {y}"


def _pretty_checked(checked):
    """'2026-10-29 07:03' -> visible Pacific time. Date-only strings stay date-only."""
    checked = (checked or "").strip()
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})(?: (\d{2}):(\d{2}))?", checked)
    if not m:
        return "", ""
    day, hh, mm = m.group(1), m.group(2), m.group(3)
    if hh is None:
        return day, _pretty_day(day)
    hour = int(hh)
    am = "AM" if hour < 12 else "PM"
    h12 = hour % 12 or 12
    return f"{day}T{hh}:{mm}", f"{_pretty_day(day)}, {h12}:{mm} {am} PT"


def _bucket(label):
    if label == "OK" or label == "Reachable, blocks automated checks":
        return "live"
    if label in ("Error", "Not responding"):
        return "down"
    return "not yet checked"


def _history_events():
    try:
        rows = json.load(open("data/mcp_history.json"))
    except Exception:
        return []
    out = []
    for row in rows:
        day = str(row.get("date") or "")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            continue
        for note in row.get("changes") or []:
            if "link status" in note:
                out.append({"date": day, "note": note})
    return out


def build_document(tools):
    import build_aicite as bac
    try:
        raw = json.load(open("data/mcp_link_status.json"))
    except Exception:
        raw = {}
    results = raw.get("results") or {}
    checked = str(raw.get("checked") or "").strip()
    events = _history_events()
    mcp = [x for x in tools if x.get("category") == "MCP servers"]
    by_name = {x["name"]: x["slug"] for x in mcp}
    servers = []
    counts = {"live": 0, "down": 0, "not yet checked": 0}
    for x in sorted(mcp, key=lambda z: z["slug"]):
        codes = results.get(x["slug"])
        item = {
            "slug": x["slug"],
            "name": x["name"],
            "page": f"{B}tools/{x['slug']}.html",
        }
        if codes:
            label, detail = bac.lstat(codes)
            status = _bucket(label)
            item["status"] = status
            if checked:
                item["last_checked"] = checked
            if detail:
                item["detail"] = detail
            if label not in ("OK", "not checked"):
                item["check_label"] = label
        else:
            status = "not yet checked"
            item["status"] = status
            detail = ""
            label = "not checked"
        own = [ev for ev in events if ev["note"].startswith(x["name"] + " link status")]
        history = []
        if codes and checked:
            note = status
            if detail:
                note += f" ({detail})"
            history.append({"date": checked[:10], "note": note, **({"time": checked[11:16]} if len(checked) >= 16 else {})})
        history.extend(reversed(own))
        if history:
            item["history"] = history[:8]
        counts[status] = counts.get(status, 0) + 1
        servers.append(item)
    catalog = {
        "mcp_servers": len(mcp),
        "live": counts["live"],
        "down": counts["down"],
        "not_yet_checked": counts["not yet checked"],
    }
    day = build_aeo.catalog_check_date()
    if day:
        catalog["directory_last_checked"] = day
    if checked:
        catalog["mcp_last_checked"] = checked
        catalog["timezone"] = raw.get("tz") or "America/Los_Angeles"
    hist = []
    if checked:
        note = f'{counts["live"]} live, {counts["down"]} down'
        if counts["not yet checked"]:
            note += f', {counts["not yet checked"]} not yet checked'
        hist.append({"date": checked[:10], "note": note, **({"time": checked[11:16]} if len(checked) >= 16 else {})})
    hist.extend(reversed(events))
    if hist:
        catalog["history"] = hist[:12]
    return {
        "catalog": catalog,
        "servers": servers,
        "by_slug": {s["slug"]: s for s in servers},
        "by_name": by_name,
    }


def write_status(doc):
    out = {"catalog": doc["catalog"], "servers": doc["servers"]}
    open("status.json", "w").write(json.dumps(out, indent=1, ensure_ascii=False) + "\n")


def _time_html(checked):
    dt, pretty = _pretty_checked(checked)
    if not pretty:
        return "not yet checked"
    if dt:
        return f'<time datetime="{e(dt)}">{e(pretty)}</time>'
    return e(pretty)


def _hist_html(items, limit=6):
    if not items:
        return "<p style=\"margin:0\">Check history: not yet checked.</p>"
    lis = []
    for ev in items[:limit]:
        when = ev.get("date") or ""
        if ev.get("time"):
            when = f"{when} {ev['time']}"
        dt, pretty = _pretty_checked(when)
        label = pretty or "not yet checked"
        stamp = f'<time datetime="{e(dt)}">{e(label)}</time>' if dt else e(label)
        lis.append(f"<li>{stamp}: {e(ev.get('note') or '')}</li>")
    return '<ul style="margin:0 0 8px;padding-left:1.2em">' + "".join(lis) + "</ul>"


def _counts_sentence(servers):
    live = sum(1 for s in servers if s.get("status") == "live")
    down = sum(1 for s in servers if s.get("status") == "down")
    miss = sum(1 for s in servers if s.get("status") == "not yet checked")
    bits = [f"<b>{live} live</b>", f"<b>{down} down</b>"]
    if miss:
        bits.append(f"<b>{miss} not yet checked</b>")
    return ", ".join(bits)


def _down_links(servers, prefix):
    down = [s for s in servers if s.get("status") == "down"]
    if not down:
        return ""
    links = [f'<a href="{prefix}tools/{e(s["slug"])}.html">{e(s["name"])}</a>' for s in down[:5]]
    more = f" and {len(down) - 5} more" if len(down) > 5 else ""
    return " Down: " + ", ".join(links) + more + "."


def panel(doc, servers, prefix, heading):
    cat = doc["catalog"]
    checked = cat.get("mcp_last_checked") or ""
    directory = cat.get("directory_last_checked") or ""
    parts = [f'<!--vs:list--><section class="verify" aria-label="Link check evidence" style="margin:12px 0 18px;overflow-wrap:anywhere;max-width:100%"><h2 style="font-size:16px;margin:0 0 6px">{e(heading)}</h2>']
    if directory:
        parts.append(f'<p style="margin:0 0 6px">Directory links last checked {_time_html(directory)}.</p>')
    if checked:
        parts.append(f'<p style="margin:0 0 6px">MCP servers last checked {_time_html(checked)}. Status: {_counts_sentence(servers)}.{_down_links(servers, prefix)}</p>')
    else:
        parts.append('<p style="margin:0 0 6px">MCP link check: not yet checked.</p>')
    parts.append('<p style="margin:0 0 4px">Check history:</p>')
    if servers is doc["servers"]:
        hist = cat.get("history") or []
    else:
        names = {s["name"] for s in servers}
        hist = []
        if checked:
            note = _counts_sentence(servers).replace("<b>", "").replace("</b>", "")
            hist.append({"date": checked[:10], "note": note, **({"time": checked[11:16]} if len(checked) >= 16 else {})})
        for ev in reversed(_history_events()):
            if any(ev["note"].startswith(name + " link status") for name in names):
                hist.append(ev)
    parts.append(_hist_html(hist))
    parts.append(f'<p style="margin:0"><a href="{prefix}status.json">status.json</a> · <a href="{prefix}mcp/link-status.html">Full MCP link-status table</a></p></section><!--/vs:list-->')
    # mcp pages already live under mcp/, so the link-status href above is wrong for them.
    html_ = "".join(parts)
    if prefix == "../":
        html_ = html_.replace('href="../mcp/link-status.html"', 'href="link-status.html"')
    return html_


def tool_rows(item):
    rows = []
    if item.get("last_checked"):
        rows.append(f'<dt>Last checked</dt><dd>{_time_html(item["last_checked"])}</dd>')
    status = item.get("status") or "not yet checked"
    detail = item.get("detail") or ""
    label = item.get("check_label") or ""
    extra = ""
    if label and label not in ("OK", "not checked"):
        extra = f' <span class="muted">({e(label)})</span>'
    elif detail:
        extra = f' <span class="muted">({e(detail)})</span>'
    rows.append(f"<dt>Status</dt><dd>{e(status)}{extra}</dd>")
    if item.get("history"):
        rows.append("<dt>Check history</dt><dd>" + _hist_html(item["history"], 5) + "</dd>")
    elif status == "not yet checked":
        rows.append("<dt>Check history</dt><dd>not yet checked</dd>")
    return "<!--vs:tool-->" + "".join(rows) + "<!--/vs:tool-->"


def _swap(s, marker, html_):
    pat = rf"<!--{marker}-->.*?<!--/{marker}-->"
    if re.search(pat, s, flags=re.S):
        return re.sub(pat, lambda _: html_, s, count=1, flags=re.S)
    return None


def apply_home(doc):
    path = "index.html"
    if not os.path.exists(path):
        return
    block = panel(doc, doc["servers"], "", "Verification")
    s = open(path).read()
    swapped = _swap(s, "vs:list", block)
    if swapped is None:
        anchor = "<!--/ci:mcp--></p>"
        if anchor in s:
            swapped = s.replace(anchor, anchor + block, 1)
        else:
            swapped = s
    if swapped != s:
        open(path, "w").write(swapped)


def apply_mcp_pages(doc, tools):
    mcp_slugs = {x["slug"] for x in tools if x.get("category") == "MCP servers"}
    pages = ["mcp/index.html"] + sorted(p for p in glob.glob("mcp/*.html") if p not in SKIP_MCP and p != "mcp/index.html")
    for path in pages:
        if not os.path.exists(path) or path in SKIP_MCP:
            continue
        s = open(path).read()
        if 'http-equiv="refresh"' in s[:800]:
            continue
        if path == "mcp/index.html":
            shown = doc["servers"]
            title = "Verification"
        else:
            slugs = []
            for slug in re.findall(r'href="(?:\.\./)?tools/([a-z0-9-]+)\.html"', s):
                if slug in mcp_slugs and slug not in slugs:
                    slugs.append(slug)
            shown = [doc["by_slug"][slug] for slug in slugs if slug in doc["by_slug"]]
            title = "Verification for this list"
        block = panel(doc, shown, "../", title)
        swapped = _swap(s, "vs:list", block)
        if swapped is None:
            m = re.search(r'(<p class="lede"[^>]*>.*?</p>)', s, flags=re.S)
            swapped = s[:m.end()] + block + s[m.end():] if m else s
        if swapped != s:
            open(path, "w").write(swapped)


def apply_tool_pages(doc, tools):
    n = 0
    for x in tools:
        if x.get("category") != "MCP servers":
            continue
        path = f"tools/{x['slug']}.html"
        if not os.path.exists(path):
            continue
        item = doc["by_slug"].get(x["slug"]) or {"status": "not yet checked", "name": x["name"], "slug": x["slug"]}
        block = tool_rows(item)
        s = open(path).read()
        swapped = _swap(s, "vs:tool", block)
        if swapped is None:
            m = re.search(r"<dt>Link checked</dt><dd>.*?</dd>", s, flags=re.S)
            if m:
                swapped = s[:m.end()] + block + s[m.end():]
            elif "</dl>" in s:
                swapped = s.replace("</dl>", block + "</dl>", 1)
            else:
                swapped = s
        if swapped != s:
            open(path, "w").write(swapped)
            n += 1
    print(f"status: MCP listing pages updated {n}")


def link_llms():
    line = f"- [Link-check status]({B}status.json): last-checked time, live or down status, and check history for every MCP server"
    path = "llms.txt"
    if not os.path.exists(path):
        return
    s = open(path).read()
    if "status.json" in s:
        return
    anchor = f"- [MCP server link status]({B}mcp/link-status.html): latest automated link check for every MCP server, with change history"
    if anchor in s:
        s = s.replace(anchor, anchor + "\n" + line, 1)
        open(path, "w").write(s)


def _expand_org(s):
    alt = build_aeo.ALT_NAMES
    same = build_aeo.SAME_AS

    def fix(m):
        raw = m.group(1)
        try:
            data = json.loads(raw)
        except Exception:
            return m.group(0)
        changed = False

        def walk(node):
            nonlocal changed
            if isinstance(node, dict):
                kind = node.get("@type")
                kinds = kind if isinstance(kind, list) else [kind]
                if "Organization" in kinds:
                    if node.get("alternateName") != alt or node.get("sameAs") != same:
                        node["alternateName"] = alt
                        node["sameAs"] = same
                        node["identifier"] = "com.agentscouthq/directory"
                        changed = True
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(data)
        if not changed:
            return m.group(0)
        return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>"

    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', fix, s, flags=re.S)


def apply_affiliation():
    for path in ("about.html", "mcp/connect.html"):
        if not os.path.exists(path):
            continue
        s = open(path).read()
        if AFF not in s:
            s2, n = re.subn(r'(<p class="lede"[^>]*>.*?</p>)', lambda m: m.group(1) + f"<p>{AFF}</p>", s, count=1, flags=re.S)
            s = s2 if n else s
        s2 = _expand_org(s)
        if s2 != s or AFF not in open(path).read():
            open(path, "w").write(s2)


def apply(tools):
    doc = build_document(tools)
    write_status(doc)
    apply_home(doc)
    apply_mcp_pages(doc, tools)
    apply_tool_pages(doc, tools)
    link_llms()
    apply_affiliation()
    print(f"status: wrote status.json ({doc['catalog'].get('live', 0)} live, {doc['catalog'].get('down', 0)} down, {doc['catalog'].get('not_yet_checked', 0)} not yet checked)")


if __name__ == "__main__":
    apply(json.load(open("tools.json")))
