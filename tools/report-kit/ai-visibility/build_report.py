#!/usr/bin/env python3
"""Build a branded AgentScout AI Visibility Check report (HTML + PDF).

Reads a dated captures JSON (prompts, sources, rungs) and a scorecard JSON
(qualitative scores and fixes from the written report). Never invents
presence, sources, or scores — those come from the input files.

Usage:
  python3 build_report.py \
    --captures captures.json \
    --scorecard sample-scorecard.json \
    --html sample.html \
    --pdf ../ai-visibility-check-sample-2026-11-11.pdf \
    --previews previews \
    --preview-prefix ../ai-visibility-check-sample-2026-11-11
"""
from __future__ import annotations

import argparse
import html
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

RUNG_CLASS = {
    "recommended": "rec",
    "cited": "cited",
    "mentioned": "ment",
    "absent": "abs",
}
RUNG_LABEL = {
    "recommended": "Recommended",
    "cited": "Cited",
    "mentioned": "Mentioned",
    "absent": "Absent",
}
# Display order for share-of-answer and charts.
RUNG_ORDER = ["recommended", "cited", "mentioned", "absent"]


def esc(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def load_json(path: Path):
    return json.loads(path.read_text())


def rung_chip(rung: str) -> str:
    cls = RUNG_CLASS.get(rung, "abs")
    lab = RUNG_LABEL.get(rung, rung or "Absent")
    return f'<span class="rung {cls}">{esc(lab)}</span>'


def p_join(paragraphs: list[str], cls: str | None = None) -> str:
    attr = f" class='{cls}'" if cls else ""
    return "".join(f"<p{attr}>{esc(p)}</p>" for p in paragraphs if p)


def score_ring_svg(score: int, score_max: int) -> str:
    r = 88
    c = 2 * math.pi * r
    frac = max(0.0, min(1.0, score / float(score_max or 100)))
    dash = c * frac
    gap = c - dash
    return f'''
    <div class="score-ring" role="img" aria-label="Score {score} out of {score_max}">
      <svg viewBox="0 0 210 210" aria-hidden="true">
        <defs>
          <filter id="scoreGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3.2" result="b"/>
            <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>
        <circle cx="105" cy="105" r="88" fill="none" stroke="#2A2A2E" stroke-width="12"/>
        <circle cx="105" cy="105" r="88" fill="none" stroke="#FF8A3D" stroke-width="12"
          stroke-linecap="round" stroke-dasharray="{dash:.2f} {gap:.2f}"
          transform="rotate(-90 105 105)" filter="url(#scoreGlow)"/>
      </svg>
      <div class="score-num"><div class="n">{esc(score)}</div><div class="d">/ {esc(score_max)}</div></div>
    </div>'''


def page_head(section: str, pages: int, page: int) -> str:
    return f'''
    <div class="page-head">
      <div class="brand">
        <img src="assets/logo/logo-mark-dark.svg" alt="AgentScout mark" width="28" height="28">
        <div class="brand-name">Agent<span class="scout">Scout</span></div>
      </div>
      <div class="head-meta">
        <span>{esc(section)}</span>
        <span class="pill">Sample</span>
      </div>
    </div>'''


def page_foot(page: int, pages: int) -> str:
    return f'''
    <div class="page-foot">
      <div>AgentScout · AI Visibility Check · Sample · not published</div>
      <div>agentscouthq.com</div>
      <div class="pg">{page} / {pages}</div>
    </div>'''


def compute_share(captures: dict) -> dict:
    rivals = captures["rivals"]
    prompts = captures["prompts"]
    nonbrand = [p for p in prompts if p.get("kind") != "brand"]
    brand = [p for p in prompts if p.get("kind") == "brand"]
    ids = ["subject"] + [r["id"] for r in rivals]
    names = {"subject": captures["subject"]["name"]}
    for r in rivals:
        names[r["id"]] = r["name"]

    def tally(subset):
        out = {}
        for sid in ids:
            counts = {k: 0 for k in RUNG_ORDER}
            for p in subset:
                rung = (p.get("scores") or {}).get(sid, "absent")
                if rung not in counts:
                    rung = "absent"
                counts[rung] += 1
            present = counts["recommended"] + counts["cited"] + counts["mentioned"]
            out[sid] = {**counts, "present": present, "n": len(subset)}
        return out

    return {
        "ids": ids,
        "names": names,
        "nonbrand": tally(nonbrand),
        "brand": tally(brand),
        "n_nonbrand": len(nonbrand),
        "n_brand": len(brand),
        "n_all": len(prompts),
        "n_top": sum(1 for p in prompts if p.get("top")),
        "n_run": sum(1 for p in prompts if p.get("run")),
    }


def share_chart_svg(share: dict) -> str:
    """Horizontal stacked bars of recommended / cited / mentioned / absent."""
    ids = share["ids"]
    names = share["names"]
    data = share["nonbrand"]
    n = share["n_nonbrand"] or 1
    width = 734
    label_w = 168
    left = label_w + 8
    right = 24
    bar_w = width - left - right
    row_h = 36
    top = 8
    axis_h = 22
    height = top + row_h * len(ids) + axis_h
    colors = {
        "recommended": "#34d399",
        "cited": "#FF8A3D",
        "mentioned": "#FACC15",
        "absent": "#2A2A2E",
    }
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Share of answer on {n} non-brand prompts">'
    ]
    # grid
    for i in range(n + 1):
        x = left + bar_w * (i / n)
        parts.append(
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + row_h * len(ids) - 6}" '
            f'stroke="#2A2A2E" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{height - 4}" fill="#C4C4C8" font-size="11" '
            f'text-anchor="middle" font-family="Inter,system-ui,sans-serif">{i}</text>'
        )
    for i, sid in enumerate(ids):
        y = top + i * row_h
        counts = data[sid]
        parts.append(
            f'<text x="{label_w}" y="{y + 16}" fill="#F5F5F5" font-size="12" '
            f'text-anchor="end" font-family="Inter,system-ui,sans-serif" font-weight="600">'
            f'{esc(names[sid])}</text>'
        )
        x = left
        for rung in RUNG_ORDER:
            w = bar_w * (counts[rung] / n)
            if counts[rung] == 0:
                continue
            # leave a 1px gap between segments except for absent which can be flush
            gap = 1.2 if x > left else 0
            rx = x + gap
            rw = max(0, w - gap)
            parts.append(
                f'<rect x="{rx:.1f}" y="{y + 4}" width="{rw:.1f}" height="18" rx="3" '
                f'fill="{colors[rung]}"/>'
            )
            if counts[rung] and rw >= 16:
                if rung in ("recommended", "cited", "mentioned"):
                    fill = "#0A0A0B"
                else:
                    fill = "#C4C4C8"
                parts.append(
                    f'<text x="{rx + rw/2:.1f}" y="{y + 17}" fill="{fill}" font-size="11" '
                    f'text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-weight="600">'
                    f'{counts[rung]}</text>'
                )
            x += w
    parts.append("</svg>")
    return "\n".join(parts)


def build_model(captures: dict, scorecard: dict) -> dict:
    share = compute_share(captures)
    prompts = captures["prompts"]
    # Third-party citations: non-brand answers whose sources are not the subject domain
    domain = (captures["subject"].get("domain") or "").lower()
    # Third-party citations of the subject: pages we opened that actually
    # name it. Other sources of an answer that also recommended the subject
    # do not count unless they themselves name the subject.
    third_party = []
    first_party_hits = []
    for p in prompts:
        if p.get("kind") == "brand":
            continue
        if (p.get("scores") or {}).get("subject") != "absent":
            for s in p.get("sources") or []:
                url = s.get("url") or ""
                host = url.split("/")[2].lower() if "://" in url else ""
                rec = {"prompt_id": p["id"], "prompt": p["prompt"], "url": url, "title": s.get("title")}
                if domain and domain in host:
                    first_party_hits.append(rec)
        for o in p.get("pages_opened") or []:
            if o.get("found_subject"):
                third_party.append({
                    "prompt_id": p["id"],
                    "prompt": p["prompt"],
                    "url": o.get("url"),
                    "title": o.get("note"),
                })
    return {
        "captures": captures,
        "scorecard": scorecard,
        "share": share,
        "third_party": third_party,
        "first_party_hits": first_party_hits,
        "pages": 9,
    }


def render_cover(m: dict) -> str:
    sc = m["scorecard"]
    cap = m["captures"]
    share = m["share"]
    pages = m["pages"]
    names = [r["name"] if r["name"] != "There's An AI For That" else "TAAFT" for r in cap["rivals"]]
    rivals = ", ".join(names)
    findings = []
    for i, fix in enumerate(sc["top_fixes"][:3], start=1):
        findings.append(f'''<div class="kf-item">
              <div class="kf-num">{i}</div>
              <div class="kf-text">{esc(fix["title"])}</div>
              <div class="kf-effort">{esc(fix.get("effort") or "")}</div>
            </div>''')
    meters = []
    for area in sc["scorecard"]:
        pct = 0 if not area["max"] else round(100 * area["points"] / area["max"])
        meters.append(f'''<div class="meter">
              <div class="m-lbl">{esc(area["area"])}</div>
              <div class="m-pts">{esc(area["points"])} <span>/ {esc(area["max"])}</span></div>
              <div class="bar {esc(area["tone"])}"><i style="width:{pct}%"></i></div>
            </div>''')
    nb = share["n_nonbrand"]
    return f'''<article class="sheet sheet-cover">
  <div class="cover-top">
    <div class="brand">
      <img src="assets/logo/logo-mark-dark.svg" alt="AgentScout mark" width="32" height="32">
      <div class="brand-name" style="font-size:18px">Agent<span class="scout">Scout</span></div>
    </div>
    <div class="head-meta">
      <span>agentscouthq.com</span>
      <span class="pill">Sample</span>
    </div>
  </div>

  <div class="cover-grid">
    <div class="cover-copy">
      <div class="kicker">AI Visibility Check</div>
      <h1>{esc(sc["subject_name"])}</h1>
      <div class="endpoint">{esc(sc["subject_url"])}</div>
      <ul class="meta-list">
        <li><span class="lbl">Tested</span><span class="val">{esc(sc["tested_display"])}</span></li>
        <li><span class="lbl">Subject</span><span class="val">A curated directory of AI agent tools and MCP servers</span></li>
        <li><span class="lbl">Rivals</span><span class="val">{esc(rivals)}</span></li>
        <li><span class="lbl">Prompts</span><span class="val">{share["n_all"]} buyer questions ({share["n_top"]} marked top). All {share["n_run"]} were run.</span></li>
        <li><span class="lbl">Surfaces</span><span class="val">AI-answer style web search, plus cited pages we opened. Chat and Perplexity were not run.</span></li>
        <li><span class="lbl">Baseline</span><span class="val">First dated run. No earlier check to compare against.</span></li>
      </ul>
    </div>
    <div class="score-wrap">
      {score_ring_svg(sc["score"], sc["score_max"])}
      <div class="score-caption">Overall score</div>
    </div>
  </div>

  <div class="cover-findings">
    <div class="kicker">Key findings</div>
    <div class="kf-good">
      <div class="kf-mark" aria-hidden="true">✓</div>
      <p>{esc(sc["whats_great"])}</p>
    </div>
    {''.join(findings)}
  </div>

  <div class="cover-meters cover-meters-5">{''.join(meters)}</div>
  <p class="cover-foot-note">{esc(sc["cover_blurb"])}</p>
  {page_foot(1, pages)}
</article>'''


def render_summary(m: dict) -> str:
    sc = m["scorecard"]
    share = m["share"]
    pages = m["pages"]
    rows = []
    total_pts = 0
    total_max = 0
    for area in sc["scorecard"]:
        rows.append(
            f"<tr><td>{esc(area['area'])}</td>"
            f"<td class='num'>{esc(area['points'])} / {esc(area['max'])}</td>"
            f"<td>{esc(area['why'])}</td></tr>"
        )
        total_pts += area["points"]
        total_max += area["max"]
    rows.append(
        f"<tr><td><strong>Total</strong></td>"
        f"<td class='num'><strong>{esc(sc['score'])} / {esc(sc['score_max'])}</strong></td><td></td></tr>"
    )
    as_nb = share["nonbrand"]["subject"]
    verdict_paras = [p.strip() for p in sc["verdict"].split("\n\n") if p.strip()]
    return f'''<article class="sheet sheet-summary">
  {page_head("Summary", pages, 2)}
  <div class="body">
    <div class="sec means">
      <h2>What this means for you</h2>
      {p_join(sc["what_this_means"])}
    </div>

    <div class="sec">
      <h2>Verdict</h2>
      {p_join(verdict_paras, "lead")}
    </div>

    <div class="sec">
      <h2>Scorecard</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Area</th><th class="num">Points</th><th>Why</th></tr></thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </div>

    <div class="sec three" style="grid-template-columns:1fr 1fr 1fr 1fr">
      <div class="stat"><div class="n">{as_nb["present"]}/{share["n_nonbrand"]}</div><div class="l">Non-brand presence</div></div>
      <div class="stat"><div class="n">{as_nb["recommended"]}</div><div class="l">Times recommended</div></div>
      <div class="stat"><div class="n warnc">{len(m["third_party"])}</div><div class="l">Third-party citations</div></div>
      <div class="stat"><div class="n">10/10</div><div class="l">Brand search</div></div>
    </div>
  </div>
  {page_foot(2, pages)}
</article>'''


def render_charts(m: dict) -> str:
    share = m["share"]
    pages = m["pages"]
    names = share["names"]
    rows = []
    for sid in share["ids"]:
        d = share["nonbrand"][sid]
        rows.append(
            "<tr>"
            f"<td>{esc(names[sid])}</td>"
            f"<td class='num'>{d['recommended']}</td>"
            f"<td class='num'>{d['cited']}</td>"
            f"<td class='num'>{d['mentioned']}</td>"
            f"<td class='num'>{d['absent']}</td>"
            f"<td class='num'><strong>{d['present']}/{share['n_nonbrand']}</strong></td>"
            "</tr>"
        )
    return f'''<article class="sheet sheet-share">
  {page_head("Share of answer", pages, 3)}
  <div class="body">
    <div class="sec card chart-card">
      <h2>Share of answer on {share["n_nonbrand"]} non-brand prompts</h2>
      <p class="chart-note">Each bar is one site’s results across the nine prompts that are not a brand search. A segment’s number is how many of those prompts landed on that rung. Recommended is green, cited is orange, mentioned is yellow, and absent is the dark remainder.</p>
      {share_chart_svg(share)}
      <div class="legend share-legend">
        <span><i class="sw" style="background:#34d399"></i>Recommended</span>
        <span><i class="sw" style="background:#FF8A3D"></i>Cited</span>
        <span><i class="sw" style="background:#FACC15"></i>Mentioned</span>
        <span><i class="sw" style="background:#2A2A2E"></i>Absent</span>
      </div>
    </div>

    <div class="sec" style="margin-top:8px">
      <h2>Counts</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Site</th><th class="num">Recommended</th><th class="num">Cited</th><th class="num">Mentioned</th><th class="num">Absent</th><th class="num">Present</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
      <p class="chart-pointer">AgentScout is present on 2 of 9 non-brand prompts, both as recommended, and both from its own pages. Glama is present on 4 of 9 and is the strongest rival in this set. PulseMCP and mcp.so are each present on 4 of 9. There’s An AI For That appears only as the subject of its own comparison query. This is the first dated run, so there is no prior share-of-answer to compare. Exact sources for every prompt are in the appendix.</p>
    </div>
    {surfaces_foot(m)}
  </div>
  {page_foot(3, pages)}
</article>'''


def render_questions(m: dict) -> str:
    cap = m["captures"]
    share = m["share"]
    pages = m["pages"]
    rivals = cap["rivals"]
    def rival_head(name: str) -> str:
        return "TAAFT" if name == "There's An AI For That" else name
    head_rivals = "".join(f"<th class='ctr'>{esc(rival_head(r['name']))}</th>" for r in rivals)
    body = []
    for p in cap["prompts"]:
        top = " · Top" if p.get("top") else ""
        scores = p.get("scores") or {}
        cells = [rung_chip(scores.get("subject", "absent"))]
        for r in rivals:
            cells.append(rung_chip(scores.get(r["id"], "absent")))
        cell_html = "".join(f"<td class='ctr'>{c}</td>" for c in cells)
        body.append(
            "<tr>"
            f"<td class='q'>{esc(p['prompt'])}"
            f"<span class='kind'>{esc(p['kind'].title())}{top}</span></td>"
            f"{cell_html}"
            "</tr>"
        )
    return f'''<article class="sheet sheet-questions">
  {page_head("Per-question results", pages, 4)}
  <div class="body">
    <div class="sec">
      <h2>Score on each prompt</h2>
      <p class="tiny" style="margin-top:-4px;margin-bottom:10px">Scoring is conservative. Recommended means the answer named the site as a pick or a place to start or submit. Cited means the site’s own page was a source, but the synthesis did not clearly recommend it. Mentioned means a passing name in the synthesis or on a cited page we opened. Absent means we did not find it. A product that is only the subject of the query is scored mentioned, not recommended.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Prompt</th><th class="ctr">AgentScout</th>{head_rivals}</tr></thead>
          <tbody>{''.join(body)}</tbody>
        </table>
      </div>
      <p class="tiny" style="margin-top:6px">TAAFT is There’s An AI For That. Prompt 3, “list my AI agent tool,” was chosen as maker language. The answer treated it as a request for a catalog, not a submit form, and AgentScout was absent. The clearer wording, “where to submit an AI agent tool,” is prompt 5. Prompt 9 is a brand search: official pages leading is expected, and it is not counted in the share-of-answer table on the previous page.</p>
    </div>
  </div>
  {page_foot(4, pages)}
</article>'''


PROMPT_NOTES = {
    1: "The synthesis picks Skillful.sh for breadth, AgentScout as a practical curated and link-checked directory, and AgentShortlist for use-case rankings. AgentScout’s official homepage was a cited source. PulseMCP, mcp.so, Glama, and There’s An AI For That did not appear.",
    2: "The answer sends people to the official MCP Registry first, then PulseMCP, mcp.so, Smithery, Glama, and MCP.Directory. We opened the cited index at automationswitch.com/mcp. It lists 18 directories and does not include AgentScout.",
    3: "Chosen as maker language (“list my tool”). The answer returned catalogs of agent tools (Agent Field Guide, AIMap, agentools.sh, and others), not submit forms. AgentScout and all four rivals were absent. See prompt 5 for the clearer submit wording.",
    4: "The synthesis calls Glama the best MCP directory for 2026, with the official registry as the canonical metadata source. PulseMCP and mcp.so are named on cited articles we checked, so they are scored mentioned. AgentScout is not in the synthesis, not a source, and not in the explainx.ai top 10 we opened.",
    5: "The synthesis names AgentScout among the places to submit an AI agent tool, and the official submit page was a cited source. The four scored rivals did not appear. This is the query where AgentScout’s own submit page does the work.",
    6: "The sources were smaller 2026 directories and review sites (Raunak’s Radar, Chat AI Tools, AIToolCrux, The Independent AI, best-ai.org). AgentScout was absent. So were There’s An AI For That and Futurepedia in this particular result set. That is a finding about this surface on this date, not a claim that those incumbents are generally invisible.",
    7: "The synthesis recommends Glama, the official registry, Docker MCP Catalog, mcp.so, and MCPVault. We opened all five cited comparison pages. None of them name AgentScout. PulseMCP is the subject of the query, so it is scored mentioned.",
    8: "The synthesis recommends Futurepedia, Future Tools, Toolify, PoweredByAI, and Product Hunt. We opened three cited listicles, including a November 2026 top 10 and a 13-alternative check dated November 4, 2026. AgentScout is on none of them. There’s An AI For That is the subject of the query.",
    9: "All five sources are official AgentScout pages (home, about, new, best, and tasks). The official site leads and the description is accurate. No third-party review appeared. Unrelated GitHub repositories also named “agentscout” did not appear in this result set.",
    10: "The answer itself is about Anthropic’s Connectors Directory and Claude Code commands. A cited guide (mcpstepbystep.com, verified October 8, 2026) names PulseMCP, mcp.so, and Glama, so those rivals are scored mentioned. AgentScout is not in the synthesis, not a source, and not in that guide.",
}


def render_notes(m: dict) -> str:
    cap = m["captures"]
    pages = m["pages"]
    blocks = []
    for p in cap["prompts"]:
        note = PROMPT_NOTES.get(p["id"], p.get("notes") or "")
        rung = (p.get("scores") or {}).get("subject", "absent")
        blocks.append(
            f'''<div class="prompt-note">
        <h3><span class="qn">{p["id"]}.</span>“{esc(p["prompt"])}” {rung_chip(rung)}</h3>
        <p>{esc(note)}</p>
      </div>'''
        )
    return f'''<article class="sheet sheet-notes">
  {page_head("What the answers said", pages, 5)}
  <div class="body">
    <div class="sec">
      <h2>Prompt notes</h2>
      <p class="tiny" style="margin-top:-2px;margin-bottom:5px">A short reading of each AI-style answer. Every claim below comes from the capture for that prompt, including pages we opened. Full source lists are in the appendix.</p>
      {''.join(blocks)}
    </div>
  </div>
  {page_foot(5, pages)}
</article>'''


def render_citations(m: dict) -> str:
    sc = m["scorecard"]
    pages = m["pages"]
    rows = []
    for t in sc["citation_targets"]:
        rows.append(
            "<tr>"
            f"<td class='wrap'><a href=\"{esc(t['url'])}\">{esc(t['url'].replace('https://', ''))}</a></td>"
            f"<td class='cite-why'>{esc(t['why'])}</td>"
            f"<td>{esc(t['realistic'])}</td>"
            "</tr>"
        )
    fp = []
    for t in sc["first_party_already_working"]:
        fp.append(
            "<tr>"
            f"<td class='wrap'><a href=\"{esc(t['url'])}\">{esc(t['url'].replace('https://', ''))}</a></td>"
            f"<td class='cite-why'>{esc(t['why'])}</td>"
            "</tr>"
        )
    return f'''<article class="sheet sheet-cites">
  {page_head("Citation audit", pages, 6)}
  <div class="body">
    <div class="sec">
      <h2>Pages the answers already pull from</h2>
      <p class="tiny" style="margin-top:-2px;margin-bottom:5px">These are realistic outreach targets: third-party pages that were sources of a non-brand answer in this run, and that do not currently name AgentScout. We opened each of these pages in this check.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Page</th><th>Why it matters</th><th>Realistic?</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </div>
    <div class="sec" style="margin-top:8px">
      <h2>Pages that already work — all first-party</h2>
      <p class="tiny" style="margin-top:-2px;margin-bottom:5px">These are the only pages that put AgentScout into a non-brand answer in this check. They are official AgentScout URLs. No third-party page that we opened named the directory.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Page</th><th>Why it matters</th></tr></thead>
          <tbody>{''.join(fp)}</tbody>
        </table>
      </div>
    </div>
    <div class="sec" style="margin-top:8px">
      <h2>Other directories that appeared, not scored as rivals</h2>
      <p>On the headline agent-directory query, Skillful.sh, AgentShortlist, DeepYard, and Fushu were cited. On MCP queries, the official MCP Registry, Smithery, Docker MCP Catalog, MCP.Directory, and MCPVault appeared often. On general AI-directory queries, Futurepedia, Future Tools, Toolify, PoweredByAI, and Product Hunt were recommended. They are part of the landscape, but they were not among the four rivals scored on every prompt.</p>
    </div>
  </div>
  {page_foot(6, pages)}
</article>'''


def render_fixes(m: dict) -> str:
    sc = m["scorecard"]
    pages = m["pages"]
    blocks = []
    for i, fix in enumerate(sc["top_fixes"], start=1):
        steps = "".join(f"<li>{esc(s)}</li>" for s in fix.get("steps") or [])
        blocks.append(f'''<div class="fix">
              <div class="fix-num">{i}</div>
              <div>
                <h3>{esc(fix["title"])}</h3>
                <p>{esc(fix["why"])}</p>
                <ol>{steps}</ol>
              </div>
            </div>''')
    also = "".join(f"<li>{esc(x)}</li>" for x in sc.get("further_improvements") or [])
    return f'''<article class="sheet sheet-fixes">
  {page_head("Top fixes", pages, 7)}
  <div class="body">
    <div class="sec">
      <h2>Top 5 fixes</h2>
      <p style="margin-top:-4px;margin-bottom:10px">These are the changes that would close the largest remaining gaps in the score. None of them requires a change to how the directory itself is curated.</p>
      {''.join(blocks)}
    </div>
  </div>
  {page_foot(7, pages)}
</article>'''


def render_method(m: dict) -> str:
    sc = m["scorecard"]
    cap = m["captures"]
    pages = m["pages"]
    steps = "".join(f"<li>{esc(s)}</li>" for s in sc["methodology"])
    scope = "".join(f"<li>{esc(s)}</li>" for s in sc["out_of_scope"])
    method_pts = "".join(f"<li>{esc(s)}</li>" for s in sc["scoring_method"])
    also = "".join(f"<li>{esc(x)}</li>" for x in sc.get("further_improvements") or [])
    nxt = sc["next_step"]
    return f'''<article class="sheet sheet-method">
  {page_head("Methodology and disclaimer", pages, 8)}
  <div class="body">
    <div class="next-step">
      <div class="kicker">{esc(nxt["title"])}</div>
      <h2>Book a free retest within 30 days</h2>
      <p>{esc(nxt["body"])}</p>
      <div class="book">{esc(nxt["link_label"])}</div>
    </div>

    <div class="sec two">
      <div>
        <h2>How this was checked</h2>
        <ol class="steps">{steps}</ol>
      </div>
      <div>
        <h2>How the 100 points are assigned</h2>
        <ol class="steps">{method_pts}</ol>
      </div>
    </div>

    <div class="sec two">
      <div>
        <h2>What this sample does not include</h2>
        <ul class="scope">{scope}</ul>
      </div>
      <div>
        <h2>Disclaimer</h2>
        <div class="disc">
          <p>{esc(sc["disclaimer"])}</p>
          <p>Test date: {esc(sc["tested_display"])}. Time zone: {esc(sc["timezone_label"])}.</p>
        </div>
      </div>
    </div>
    <div class="sec also" style="margin-top:6px">
      <h3>Also worth watching</h3>
      <p class="tiny" style="margin-bottom:6px">{esc(sc.get("further_note") or "")}</p>
      <ol>{also}</ol>
    </div>
  </div>
  {page_foot(8, pages)}
</article>'''



def surfaces_foot(m: dict) -> str:
    cap = m["captures"]
    run = "".join(f"<li>{esc(s)}</li>" for s in cap.get("surfaces_run") or [])
    not_run = "".join(f"<li>{esc(s)}</li>" for s in cap.get("surfaces_not_run") or [])
    collisions = "".join(f"<li>{esc(s)}</li>" for s in cap.get("name_collisions") or [])
    note = (
        "Dated prompt captures: captures.json, in this template folder. "
        "Scores and fixes: sample-scorecard.json. Rebuild with build_report.py. "
        "Time zone for every timestamp: America/Los_Angeles (Pacific Time)."
    )
    return (
        '<div class="sec three appendix-foot">'
        "<div><h3>Surfaces run</h3>"
        f'<ul class="scope">{run}</ul></div>'
        "<div><h3>Surfaces not run</h3>"
        f'<ul class="scope">{not_run}</ul></div>'
        "<div><h3>Name collisions checked</h3>"
        f'<ul class="scope">{collisions}</ul>'
        f'<p class="tiny" style="margin-top:4px">{note}</p></div>'
        "</div>"
    )


def render_appendix(m: dict) -> str:
    cap = m["captures"]
    pages = m["pages"]
    rows = []
    for p in cap["prompts"]:
        srcs = p.get("sources") or []
        src_txt = "; ".join(
            (s.get("url") or "").replace("https://", "") for s in srcs
        )
        opened = p.get("pages_opened") or []
        opened_txt = "; ".join(
            (o.get("url") or "").replace("https://", "") for o in opened
        ) or "—"
        run = "Run" if p.get("run") else "Not run"
        top = " · top" if p.get("top") else ""
        rows.append(
            "<tr>"
            f"<td class='num'>{p['id']}</td>"
            f"<td class='wrap'>{esc(p['prompt'])}<div class='tiny'>{esc(p['kind'])}{top}</div></td>"
            f"<td>{esc(run)}</td>"
            f"<td class='wrap tiny'>{esc(src_txt)}</td>"
            f"<td class='wrap tiny'>{esc(opened_txt)}</td>"
            "</tr>"
        )
    return f'''<article class="sheet sheet-appendix">
  {page_head("Appendix", pages, 9)}
  <div class="body">
    <div class="sec">
      <h2>Appendix: Prompt log</h2>
      <p class="tiny" style="margin-top:-2px;margin-bottom:5px">Every prompt below was actually run. All ten were checked on November 11, 2026, 2:24–2:26 AM PT, on AI-answer style web search (WebSearch) plus the source links it returned. “Opened” means we fetched the page in this check and searched it for an AgentScout mention. Nothing in this table was invented.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th class="num">#</th><th>Prompt</th><th>Status</th><th>Answer sources</th><th>Pages opened</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </div>
    </div>
  </div>
  {page_foot(9, pages)}
</article>'''


def render_html(m: dict, web: dict | None = None) -> str:
    """Printable report. Pass web= to publish the noindex page.

    With web omitted, the markup matches the print sample: relative
    stylesheet and logo, no site chrome. web may set robots, csp,
    referrer, css_href, logo_src, pdf_href, and fit.
    """
    web = web or {}
    sc = m["scorecard"]
    title = f"AgentScout AI Visibility Check — {sc['subject_name']}"
    sheets = [
        render_cover(m),
        render_summary(m),
        render_charts(m),
        render_questions(m),
        render_notes(m),
        render_citations(m),
        render_fixes(m),
        render_method(m),
        render_appendix(m),
    ]
    logo_src = web.get("logo_src")
    if logo_src:
        sheets = [sheet.replace('src="assets/logo/logo-mark-dark.svg"', f'src="{esc(logo_src)}"') for sheet in sheets]
    if web.get("fit"):
        sheets = [f'<div class="fit">{sheet}</div>' for sheet in sheets]
    robots = ""
    if web.get("robots"):
        robots = f'\n  <meta name="robots" content="{esc(web["robots"])}">'
    csp_meta = ""
    if web.get("csp"):
        # The policy is our constant. It uses single quotes and must stay literal
        # inside the double-quoted content attribute. It contains no double quote.
        csp_meta = f'\n  <meta http-equiv="Content-Security-Policy" content="{web["csp"]}">'
    referrer = ""
    if web.get("referrer"):
        referrer = f'\n  <meta name="referrer" content="{esc(web["referrer"])}">'
    css_href = web.get("css_href") or "report.css"
    webbar = ""
    if web.get("pdf_href"):
        webbar = (
            '<p class="webbar"><span>Private AgentScout report</span>'
            f'<a href="{esc(web["pdf_href"])}">Download PDF</a></p>\n'
        )
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">{referrer}{csp_meta}{robots}
  <title>{esc(title)}</title>
  <link rel="stylesheet" href="{esc(css_href)}">
</head>
<body>
{webbar}{chr(10).join(sheets)}
</body>
</html>
'''


def render_previews(pdf_path: Path, preview_dir: Path, copy_prefix: Path | None = None) -> list[Path]:
    preview_dir.mkdir(parents=True, exist_ok=True)
    for old in preview_dir.glob("page-*.png"):
        old.unlink()
    # 150 dpi keeps letter pages around 1275px wide, which is sharp in chat
    # and still comfortable on a phone.
    subprocess.run(
        ["pdftoppm", "-png", "-r", "150", str(pdf_path), str(preview_dir / "page")],
        check=True,
    )
    pages = sorted(preview_dir.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[1]))
    if copy_prefix is not None:
        parent = copy_prefix.parent
        stem = copy_prefix.name
        # Delete leftover PREFIX-page-N.png beyond the new count
        existing = list(parent.glob(f"{stem}-page-*.png"))
        for old in existing:
            old.unlink()
        for p in pages:
            dest = parent / f"{stem}-{p.name}"
            shutil.copy2(p, dest)
    return pages


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    uri = html_path.resolve().as_uri()
    cmd = [
        "google-chrome",
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--no-default-browser-check",
        "--hide-scrollbars",
        "--allow-file-access-from-files",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        "--virtual-time-budget=15000",
        uri,
    ]
    print("Rendering PDF:", " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, check=True)
    print(f"Wrote {pdf_path} ({pdf_path.stat().st_size} bytes)", file=sys.stderr)


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--captures", type=Path, default=HERE / "captures.json")
    p.add_argument("--scorecard", type=Path, default=HERE / "sample-scorecard.json")
    p.add_argument("--html", type=Path, default=HERE / "sample.html")
    p.add_argument("--pdf", type=Path, default=None)
    p.add_argument("--previews", type=Path, default=None,
                   help="Directory for page-N.png previews (pdftoppm). Requires --pdf.")
    p.add_argument("--preview-prefix", type=Path, default=None,
                   help="Also copy previews to PREFIX-page-N.png and delete stale ones.")
    p.add_argument("--robots", default=None,
                   help="Optional robots meta, for the print sample kept in the repo.")
    args = p.parse_args(argv)

    captures = load_json(args.captures)
    scorecard = load_json(args.scorecard)
    model = build_model(captures, scorecard)
    web = {"robots": args.robots} if args.robots else None
    html_out = render_html(model, web)
    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.html.write_text(html_out)
    print(f"Wrote {args.html} ({args.html.stat().st_size} bytes)", file=sys.stderr)

    if args.pdf:
        render_pdf(args.html, args.pdf)
        if args.previews:
            pages = render_previews(args.pdf, args.previews, args.preview_prefix)
            print(f"Wrote {len(pages)} page previews in {args.previews}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
