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
# Public copy for the MCP/directory link check: once daily around 7 AM Pacific (a run may finish later).
VERIFY_CADENCE = "Updated daily, around 7 AM PT"


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
            item["unverified"] = True
            if x.get("catalog_only"):
                item["catalog_only"] = True
                item["detail"] = "Listed, not yet checked"
            detail = item.get("detail") or ""
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
    checked_count = counts["live"] + counts["down"]
    catalog = {
        "mcp_servers": len(mcp),
        "live": counts["live"],
        "down": counts["down"],
        "checked": checked_count,
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
        note = f'{counts["live"]} of {checked_count} checked servers live, {counts["down"]} down'
        if counts["not yet checked"]:
            note += f', +{counts["not yet checked"]} listed, not yet checked'
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


# Look lives in styles.css (.vc). Do not inline a second neon stylesheet.
VC_CSS = ""


def _hist_cls(note):
    """vc-o green = good, vc-e red = outage, vc-n cyan = neutral."""
    m = re.search(r"(\d+)\s+down", note)
    if m:
        return "vc-e" if int(m.group(1)) > 0 else "vc-o"
    t = re.search(r"(?i)\bto\s+(.+?)\.?$", note) or re.search(r"(?i)(?:->|→)\s*(.+?)\.?$", note)
    if t:
        tgt = t.group(1).strip().lower()
        if tgt in ("ok", "live"):
            return "vc-o"
        if tgt.startswith(("error", "down")):
            return "vc-e"
        return "vc-n"
    return "vc-n"


def _hist_html(items, limit=5):
    if not items:
        return '<p style="margin:0">Check history: not yet checked.</p>'
    lis = []
    for ev in items[:limit]:
        when = ev.get("date") or ""
        if ev.get("time"):
            when = f"{when} {ev['time']}"
        dt, pretty = _pretty_checked(when)
        label = pretty or "not yet checked"
        stamp = f'<time datetime="{e(dt)}">{e(label)}</time>' if dt else f"<time>{e(label)}</time>"
        note = ev.get("note") or ""
        cls = _hist_cls(note)
        lis.append(f'<li class="{cls}">{stamp}{e(note)}</li>')
    return '<ol class="vc-tl" aria-label="Check history">' + "".join(lis) + "</ol>"


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


def _chips(servers):
    live = sum(1 for s in servers if s.get("status") == "live")
    down = sum(1 for s in servers if s.get("status") == "down")
    miss = sum(1 for s in servers if s.get("status") == "not yet checked")
    c = [f'<li class="vc-chip vc-ok"><b>{live}</b> live</li>',
         f'<li class="vc-chip {"vc-bad" if down else "vc-ok"}"><b>{down}</b> down</li>']
    if miss:
        c.append(f'<li class="vc-chip vc-warn"><b>{miss}</b> not yet checked</li>')
    c.append(f'<li class="vc-chip vc-tot"><b>{live + down}</b> checked</li>')
    return '<ul class="vc-chips" aria-label="Link status counts">' + "".join(c) + "</ul>"


def _down_pills(servers, prefix):
    down = [s for s in servers if s.get("status") == "down"]
    if not down:
        return ""
    links = [f'<a class="vc-pill" href="{prefix}tools/{e(s["slug"])}.html">{e(s["name"])}</a>' for s in down[:8]]
    more = f'<span class="vc-pill">+{len(down) - 8} more</span>' if len(down) > 8 else ""
    return '<p class="vc-lbl">Down right now</p><div class="vc-pills">' + "".join(links) + more + "</div>"


def _card_head(heading, down=0):
    dot = "vc-dot vc-dn" if down else "vc-dot"
    return (f'<div class="vc-hd"><span class="{dot}" aria-hidden="true"></span><h2>{e(heading)}</h2>'
            f'<span class="vc-upd">{VERIFY_CADENCE}</span></div>')


def panel(doc, servers, prefix, heading):
    cat = doc["catalog"]
    checked = cat.get("mcp_last_checked") or ""
    directory = cat.get("directory_last_checked") or ""
    parts = [f'<!--vs:list-->{VC_CSS}<section class="verify vc" aria-label="Link check evidence">{_card_head(heading, sum(1 for s in servers if s.get("status") == "down"))}']
    if checked:
        parts.append(_chips(servers))
        parts.append(f'<p>MCP servers last checked {_time_html(checked)}. Status: {_counts_sentence(servers)}.</p>')
        parts.append(_down_pills(servers, prefix))
    else:
        parts.append('<p>MCP link check: not yet checked.</p>')
    if directory:
        parts.append(f'<p class="muted" style="font-size:13px">Directory links last checked {_time_html(directory)}.</p>')
    parts.append('<p class="vc-lbl">Check history</p>')
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
    parts.append(f'<div class="vc-btns"><a class="vc-btn" href="{prefix}status.json">status.json</a><a class="vc-btn" href="{prefix}mcp/status/">MCP status</a></div></section><!--/vs:list-->')
    html_ = "".join(parts)
    if prefix == "../":
        html_ = html_.replace('href="../mcp/status/"', 'href="status/"')
    return html_


def tool_rows(item):
    status = item.get("status") or "not yet checked"
    detail = item.get("detail") or ""
    label = item.get("check_label") or ""
    extra = ""
    if label and label not in ("OK", "not checked"):
        extra = f" ({e(label)})"
    elif detail:
        extra = f" ({e(detail)})"
    cls = "vc-ok" if status == "live" else "vc-bad" if status == "down" else "vc-warn"
    body = [VC_CSS, '<div class="vc">', _card_head("Verification", 1 if status == "down" else 0),
            f'<ul class="vc-chips"><li class="vc-chip {cls}">Status: <b>{e(status)}</b>{extra}</li></ul>']
    if item.get("last_checked"):
        body.append(f'<p>Last checked {_time_html(item["last_checked"])}.</p>')
    body.append('<p class="vc-lbl">Check history</p>')
    if item.get("history"):
        body.append(_hist_html(item["history"], 5))
    else:
        body.append("<p>not yet checked</p>")
    body.append('<div class="vc-btns"><a class="vc-btn" href="../status.json">status.json</a><a class="vc-btn" href="../mcp/status/">MCP status</a></div></div>')
    return ("<!--vs:tool--><dt>Status</dt><dd>" + e(status) + extra + "</dd>"
            '<dd class="vc-row">' + "".join(body) + "</dd><!--/vs:tool-->")


def _swap(s, marker, html_):
    pat = rf"<!--{marker}-->.*?<!--/{marker}-->"
    if re.search(pat, s, flags=re.S):
        return re.sub(pat, lambda _: html_, s, count=1, flags=re.S)
    return None


def home_slim(doc):
    """One line under the homepage search. Counts and the timestamp come from the link-check document."""
    servers = doc["servers"]
    cat = doc["catalog"]
    live = sum(1 for s in servers if s.get("status") == "live")
    down = sum(1 for s in servers if s.get("status") == "down")
    checked_n = live + down
    miss = sum(1 for s in servers if s.get("status") == "not yet checked")
    checked = cat.get("mcp_last_checked") or ""
    when = _time_html(checked) if checked else "not yet checked"
    dot = "vc-dot vc-dn" if down else "vc-dot"
    hist = _hist_html(cat.get("history") or [], 3)
    extra = f' · +{miss} listed, not yet checked' if miss else ""
    return (
        f'<!--vs:home--><section class="verify-slim" aria-label="MCP server link check">'
        f'<span class="{dot}" aria-hidden="true"></span>'
        f'<p><b>{live} of {checked_n}</b> checked servers live{extra} · checked daily · last checked {when}</p>'
        f'<a href="mcp/status/">MCP status →</a>'
        f'<details><summary>Recent checks</summary>{hist}</details>'
        f'</section><!--/vs:home-->'
    )


def apply_home(doc):
    path = "index.html"
    if not os.path.exists(path):
        return
    block = home_slim(doc)
    s = open(path).read()
    swapped = _swap(s, "vs:home", block)
    if swapped is None:
        # Nov 9 2026: homepage Popular lists pills removed; prefer dir:top, then end of header.
        if "<!--dir:top-->" in s:
            swapped = s.replace("<!--dir:top-->", block + "<!--dir:top-->", 1)
        elif "</header>" in s:
            swapped = s.replace("</header>", "</header>" + block, 1)
        else:
            swapped = s
    # The old chip-and-history card is not the homepage treatment.
    swapped = re.sub(r'<!--vs:list-->.*?<!--/vs:list-->', '', swapped, count=1, flags=re.S)
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
    anchor = f"- [MCP server status]({B}mcp/status/): up, down, and not-yet-checked counts from the latest automated link check, with change history"
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


def write_link_status_forward():
    """GitHub Pages ignores _redirects, so the old URL stays a real HTML page that forwards to /mcp/status/.

    The nav and footer are the canonical site chrome, not a mid-build copy of
    index.html. Homepage passes insert extra header links that the nav sync
    then removes; copying the header before that removal is what put those
    links on this redirect page.
    """
    import build_seo_new
    nav, foot = build_seo_new.chrome_for("../")
    canon = B + "mcp/status/"
    nl = ""
    if os.path.exists("mcp/link-status.html"):
        old = open("mcp/link-status.html", encoding="utf-8").read()
        block = re.search(r'<section id="nlblock".*?</section>', old, re.S)
        if block:
            nl = block.group(0)
    page = f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="color-scheme" content="dark light">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MCP server status · AgentScout</title>
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{canon}">
<meta http-equiv="refresh" content="0; url=/mcp/status/">
<link rel="icon" type="image/svg+xml" href="../favicon.svg">
<link rel="stylesheet" href="../styles.css?v={__import__('build_tasks').ASSET_V}">
<script>(function(){{try{{var t=localStorage.getItem("agentscout-theme")}}catch(e){{}}if(t!=="dark"&&t!=="light")t="dark";document.documentElement.dataset.theme=t;window.asToggleTheme=function(){{var n=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.dataset.theme=n;try{{localStorage.setItem("agentscout-theme",n)}}catch(e){{}}}}}})()</script>
</head><body>
{nav}
<main class="wrap"><p>This page moved. <a href="/mcp/status/">MCP server status</a>.</p></main>
{nl}{foot}
<script src="../app.js?v={__import__('build_tasks').ASSET_V}"></script>
</body></html>
'''
    problems = build_seo_new.redirect_page_chrome_problems("mcp/link-status.html", page)
    if problems:
        raise SystemExit("redirect nav check failed: " + "; ".join(problems))
    os.makedirs("mcp", exist_ok=True)
    open("mcp/link-status.html", "w", encoding="utf-8").write(__import__("build_tasks").stamp(page))
    print("link-status forwarder: mcp/link-status.html -> /mcp/status/")


def write_dashboard(tools):
    """Upgrade /mcp/link-status.html in place. Status comes only from the check files."""
    import build_extras as X
    doc = build_document(tools)
    cat = doc["catalog"]
    checked = cat.get("mcp_last_checked") or ""
    dt, pretty = _pretty_checked(checked)
    live, down, miss = cat.get("live", 0), cat.get("down", 0), cat.get("not_yet_checked", 0)
    checked_n = live + down
    total = checked_n + miss
    when = f'<time datetime="{e(dt)}">{e(pretty)}</time>' if dt else "not yet checked"
    rows = []
    for s in doc["servers"]:
        status = s.get("status") or "not yet checked"
        hist = s.get("history") or []
        bits = []
        for ev in hist[:3]:
            note = ev.get("note") or ""
            day = ev.get("date") or ""
            if ev.get("time"):
                day = f"{day} {ev['time']}"
            bits.append(f"{day}: {note}" if day else note)
        hist_txt = " · ".join(bits) if bits else ("No earlier change is in the check log." if status != "not yet checked" else "not yet checked")
        last = _time_html(s["last_checked"]) if s.get("last_checked") else "not yet checked"
        detail = e(s.get("detail") or s.get("check_label") or "")
        shown = {"live": "Up", "down": "Down", "not yet checked": "Not yet checked"}.get(status, status)
        rows.append(
            f'<tr data-status="{e(status)}" data-name="{e(s["name"].lower())}">'
            f'<td><a href="../../tools/{e(s["slug"])}.html">{e(s["name"])}</a></td>'
            f'<td><span class="st-pill st-{e(status.replace(" ", "-"))}">{e(shown)}</span></td>'
            f'<td>{last}</td><td>{detail or "—"}</td><td><div class="st-hist">{e(hist_txt)}</div></td></tr>'
        )
    title = "MCP server status · AgentScout"
    desc = f"{live} of {checked_n} checked MCP servers live. +{miss} listed, not yet checked. {VERIFY_CADENCE}."
    if len(desc) > 156:
        desc = desc[:156].rsplit(" ", 1)[0]
    canon = B + "mcp/status/"
    qa_bits = []
    if checked:
        qa_bits.append(f"{live} of {checked_n} checked servers live. +{miss} listed, not yet checked. {total} MCP servers are in the directory.")
        qa_bits.append(f"Last updated {pretty or checked} Pacific.")
    else:
        qa_bits.append("The MCP link check has no timestamp on file yet.")
    body = f'''<div class="crumb"><a href="../../index.html">AgentScout</a> / <a href="../index.html">MCP servers</a> / Status</div>
<section class="st-dash sheet">
<h1 style="text-align:left">MCP server status</h1>
<p class="lede" style="margin-left:0;text-align:left">Every MCP server in the directory, from the link check stored in <a href="../../status.json">status.json</a>. {VERIFY_CADENCE}. The live count is {live} of {checked_n} checked servers. A server with no row in the check file, including a catalog-only listing, is listed and not yet checked, and is not part of that percentage. The daily check includes catalog-only servers the next time it runs. Nothing on this page is guessed.</p>
<p class="st-updated"><b>Last updated:</b> {when}. {VERIFY_CADENCE}. {e(qa_bits[0] if qa_bits else "")}</p>
<div class="st-counts" role="group" aria-label="Filter by status">
<button type="button" class="st-count on" data-filter="all"><b>{total}</b><span>All</span></button>
<button type="button" class="st-count" data-filter="live"><b>{live}</b><span>Up</span></button>
<button type="button" class="st-count" data-filter="down"><b>{down}</b><span>Down</span></button>
<button type="button" class="st-count" data-filter="not yet checked"><b>{miss}</b><span>Not yet checked</span></button>
</div>
<label class="sr-only" for="st-q">Search MCP servers</label>
<input id="st-q" type="search" placeholder="Search MCP servers" autocomplete="off" enterkeyhint="search">
<p id="st-empty" class="muted" hidden>No servers match that filter.</p>
<div class="cmpscroll" tabindex="0" role="region" aria-label="MCP server status table">
<table class="st-table" id="st-table"><thead><tr><th>MCP server</th><th>Status</th><th>Last checked</th><th>HTTP result</th><th>Recent history</th></tr></thead><tbody>
{"".join(rows)}
</tbody></table></div>
<p class="muted" style="margin-top:14px">Up and down are the checked set. Not yet checked, including catalog-only listings the daily check has not opened, are labeled unverified and stay out of the live percentage. Up includes servers whose latest check was OK, and servers that answered but block scripted requests. Down means the check returned an error or no response. See also <a href="../pricing.html">MCP pricing</a> and <a href="../index.html">MCP servers by task</a>.</p>
</section>
<script>
(function(){{
  var q=document.getElementById("st-q"), rows=[].slice.call(document.querySelectorAll("#st-table tbody tr")), empty=document.getElementById("st-empty"), filter="all";
  function run(){{
    var n=0, s=(q.value||"").trim().toLowerCase();
    rows.forEach(function(r){{
      var ok=(filter==="all"||r.getAttribute("data-status")===filter)&&(!s||r.getAttribute("data-name").indexOf(s)>=0);
      r.hidden=!ok; if(ok)n++;
    }});
    empty.hidden=n>0;
  }}
  document.querySelectorAll(".st-count").forEach(function(b){{b.addEventListener("click",function(){{
    filter=b.getAttribute("data-filter");
    document.querySelectorAll(".st-count").forEach(function(x){{x.classList.toggle("on",x===b)}});
    run();
  }})}});
  q.addEventListener("input",run);
}})();
</script>'''
    items = [{"@type": "ListItem", "position": i + 1, "name": s["name"], "url": s["page"]} for i, s in enumerate(doc["servers"])]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "name": title, "description": desc, "url": canon, "dateModified": (checked[:10] if checked else None)},
        {"@type": "Dataset", "name": "MCP server link status", "description": desc, "url": canon, "dateModified": (checked[:10] if checked else None), "creator": {"@type": "Organization", "name": "AgentScout", "url": B}},
        {"@type": "ItemList", "name": "MCP server status", "numberOfItems": total, "itemListElement": items},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "AgentScout", "item": B},
            {"@type": "ListItem", "position": 2, "name": "MCP servers", "item": B + "mcp/"},
            {"@type": "ListItem", "position": 3, "name": "Status", "item": canon},
        ]},
    ]}
    for node in ld["@graph"]:
        if node.get("dateModified") is None:
            node.pop("dateModified", None)
    os.makedirs("mcp/status", exist_ok=True)
    import build_tasks as _bt
    page = X.shell("../../", title, desc, canon, body, ld)
    page = _bt.ensure_shared_scripts("mcp/status/index.html", page, "../../")
    page = __import__("build_share").apply("mcp/status/index.html", page, "../../", _bt.ASSET_V)
    open("mcp/status/index.html", "w").write(page)
    write_link_status_forward()
    print(f"status dashboard: {live} up, {down} down, {miss} not yet checked")
    return canon


def apply(tools):
    doc = build_document(tools)
    write_status(doc)
    apply_home(doc)
    apply_mcp_pages(doc, tools)
    apply_tool_pages(doc, tools)
    link_llms()
    apply_affiliation()
    import build_aicite as _reach
    _reach.stamp_mcp_pages(tools)
    _reach.stamp_llms_docs()
    print(f"status: wrote status.json ({doc['catalog'].get('live', 0)} live, {doc['catalog'].get('down', 0)} down, {doc['catalog'].get('not_yet_checked', 0)} not yet checked)")


if __name__ == "__main__":
    apply(json.load(open("tools.json")))
