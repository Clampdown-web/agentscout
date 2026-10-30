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


VC_CSS = ("<style>.vc{background:linear-gradient(180deg,#0d1222,#070a14);border:1px solid rgba(56,189,248,.28);border-radius:16px;padding:18px 20px;margin:14px 0 20px;"
          "box-shadow:0 0 0 1px rgba(56,189,248,.06),0 10px 30px rgba(0,0,0,.35),0 0 24px rgba(56,189,248,.08);color:#cbd5e1;text-align:left;font-size:14px;line-height:1.5;overflow-wrap:anywhere;max-width:100%;box-sizing:border-box}"
          ".vc-hd{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;margin:0 0 12px}.vc-hd h2{margin:0;font-size:17px;letter-spacing:-.01em;color:#f1f5f9}"
          ".vc-dot{width:10px;height:10px;border-radius:50%;background:#22c55e;box-shadow:0 0 8px #22c55e;flex:0 0 auto;animation:vcp 2s ease-in-out infinite}"
          "@keyframes vcp{0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,.6)}50%{box-shadow:0 0 0 6px rgba(34,197,94,0)}}@media (prefers-reduced-motion:reduce){.vc-dot{animation:none}}.vc-dot.vc-dn{background:#f87171;box-shadow:0 0 8px #f87171;animation:none}"
          ".vc-upd{font-size:12px;color:#94a3b8;margin-left:auto}.vc-chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 10px;padding:0;list-style:none}"
          ".vc-chip{display:inline-flex;align-items:baseline;gap:6px;padding:5px 12px;border-radius:999px;font-size:13px;border:1px solid;background:rgba(255,255,255,.03)}.vc-chip b{font-size:15px}"
          ".vc-ok{color:#4ade80;border-color:rgba(74,222,128,.45)}.vc-bad{color:#f87171;border-color:rgba(248,113,113,.45)}.vc-warn{color:#fbbf24;border-color:rgba(251,191,36,.45)}.vc-tot{color:#7dd3fc;border-color:rgba(125,211,252,.45)}"
          ".vc p{margin:0 0 8px;color:#cbd5e1}.vc-lbl{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8;margin:12px 0 6px!important}"
          ".vc-pills{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 8px}.vc-pill{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12.5px;border:1px solid rgba(248,113,113,.4);color:#fca5a5;text-decoration:none;background:rgba(248,113,113,.06)}"
          ".vc-tl{list-style:none;margin:0 0 10px;padding:0 0 0 14px;border-left:2px solid rgba(148,163,184,.25)}.vc-tl li{position:relative;margin:0 0 7px;font-size:13px;color:#cbd5e1}"
          ".vc-tl li:before{content:\"\";position:absolute;left:-20px;top:6px;width:10px;height:10px;border-radius:50%;background:#4ade80;box-shadow:0 0 6px rgba(74,222,128,.7)}.vc-tl li.vc-o:before{background:#22c55e;box-shadow:0 0 8px rgba(34,197,94,.75)}.vc-tl li.vc-e:before{background:#f87171;box-shadow:0 0 6px rgba(248,113,113,.7)}.vc-tl li.vc-n:before{background:#22d3ee;box-shadow:0 0 6px rgba(34,211,238,.6)}"
          ".vc-tl time{color:#94a3b8;font-size:12px;display:block}.vc-btns{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 0}"
          ".vc-btn{display:inline-block;padding:5px 12px;border-radius:999px;font-size:12.5px;border:1px solid rgba(56,189,248,.45);color:#7dd3fc;text-decoration:none;background:rgba(56,189,248,.06)}.vc-btn:hover,.vc-pill:hover{filter:brightness(1.25)}"
          ".panel dl .vc-row{grid-column:1/-1}.vc-row .vc{margin:6px 0 0;padding:14px}</style>")


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
    c.append(f'<li class="vc-chip vc-tot"><b>{len(servers)}</b> checked</li>')
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
            '<span class="vc-upd">Updated twice daily, 7 AM &amp; 7 PM PT</span></div>')


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
        parts.append(f'<p style="color:#94a3b8;font-size:13px">Directory links last checked {_time_html(directory)}.</p>')
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
    parts.append(f'<div class="vc-btns"><a class="vc-btn" href="{prefix}status.json">status.json</a><a class="vc-btn" href="{prefix}mcp/link-status.html">Full MCP link-status table</a></div></section><!--/vs:list-->')
    html_ = "".join(parts)
    if prefix == "../":
        html_ = html_.replace('href="../mcp/link-status.html"', 'href="link-status.html"')
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
    body.append('<div class="vc-btns"><a class="vc-btn" href="../status.json">status.json</a><a class="vc-btn" href="../mcp/link-status.html">Full MCP link-status table</a></div></div>')
    return ("<!--vs:tool--><dt>Status</dt><dd>" + e(status) + extra + "</dd>"
            '<dd class="vc-row">' + "".join(body) + "</dd><!--/vs:tool-->")


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


def write_dashboard(tools):
    """Upgrade /mcp/link-status.html in place. Status comes only from the check files."""
    import build_extras as X
    doc = build_document(tools)
    cat = doc["catalog"]
    checked = cat.get("mcp_last_checked") or ""
    dt, pretty = _pretty_checked(checked)
    live, down, miss = cat.get("live", 0), cat.get("down", 0), cat.get("not_yet_checked", 0)
    total = live + down + miss
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
            f'<td>{last}</td><td>{detail or "—"}</td><td>{e(hist_txt)}</td></tr>'
        )
    title = "MCP server status · AgentScout"
    desc = f"Up, down, and not-yet-checked counts for {total} MCP servers on AgentScout, from the latest twice-daily link check."
    if len(desc) > 156:
        desc = desc[:156].rsplit(" ", 1)[0]
    canon = B + "mcp/status/"
    qa_bits = []
    if checked:
        qa_bits.append(f"{live} up, {down} down, {miss} not yet checked, out of {total} MCP servers.")
        qa_bits.append(f"Last updated {pretty or checked} Pacific.")
    else:
        qa_bits.append("The MCP link check has no timestamp on file yet.")
    body = f'''<div class="crumb"><a href="../../index.html">AgentScout</a> / <a href="../index.html">MCP servers</a> / Status</div>
<section class="st-dash" style="padding-top:20px;text-align:left">
<h1 style="text-align:left">MCP server status</h1>
<p class="lede" style="margin-left:0;text-align:left">Every MCP server in the directory, from the link check stored in <a href="../../status.json">status.json</a>. Updated twice daily, 7 AM &amp; 7 PM PT. A server with no row in the check file is not yet checked. Nothing on this page is guessed.</p>
<p class="st-updated"><b>Last updated:</b> {when}. Updated twice daily, 7 AM &amp; 7 PM PT. {e(qa_bits[0] if qa_bits else "")}</p>
<div class="st-counts" role="group" aria-label="Filter by status">
<button type="button" class="st-count on" data-filter="all"><b>{total}</b><span>All</span></button>
<button type="button" class="st-count" data-filter="live"><b>{live}</b><span>Up</span></button>
<button type="button" class="st-count" data-filter="down"><b>{down}</b><span>Down</span></button>
<button type="button" class="st-count" data-filter="not yet checked"><b>{miss}</b><span>Not yet checked</span></button>
</div>
<label class="sr-only" for="st-q">Search MCP servers</label>
<input id="st-q" type="search" placeholder="Search MCP servers" autocomplete="off" enterkeyhint="search">
<p id="st-empty" class="muted" hidden>No servers match that filter.</p>
<div style="overflow-x:auto;max-width:100%" tabindex="0" role="region" aria-label="MCP server status table">
<table class="st-table" id="st-table"><thead><tr><th>MCP server</th><th>Status</th><th>Last checked</th><th>HTTP result</th><th>Recent history</th></tr></thead><tbody>
{"".join(rows)}
</tbody></table></div>
<p class="muted" style="margin-top:14px">Up includes servers whose latest check was OK, and servers that answered but block scripted requests. Down means the check returned an error or no response. See also <a href="../pricing.html">MCP pricing</a> and <a href="../index.html">MCP servers by task</a>.</p>
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
    open("mcp/status/index.html", "w").write(X.shell("../../", title, desc, canon, body, ld))
    open("mcp/link-status.html", "w").write(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>MCP server status · AgentScout</title>'
        f'<link rel="canonical" href="{canon}"><meta name="robots" content="noindex,follow">'
        '<meta http-equiv="refresh" content="0; url=status/"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'</head><body><a href="status/">MCP server status</a></body></html>\n'
    )
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
    print(f"status: wrote status.json ({doc['catalog'].get('live', 0)} live, {doc['catalog'].get('down', 0)} down, {doc['catalog'].get('not_yet_checked', 0)} not yet checked)")


if __name__ == "__main__":
    apply(json.load(open("tools.json")))
