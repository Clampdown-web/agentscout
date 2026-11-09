"""Popular lists internal links (owner-approved Oct 22 2026 PT; homepage pills removed Nov 9 2026).

Hub pages (not the homepage) still get the chip block before <footer>. The homepage keeps
the MCP status box and tools first; a short Popular lists line lives in the site-wide footer
instead (owner-approved Nov 9 2026 PT). Counts in chip labels come from tools.json. Footer
labels omit counts so they never go stale. Idempotent marker blocks. No new colors: existing
.chip/.chips styles for hubs; footer uses .footpop. 44px tap height.
"""
import json, os, re, html

e = lambda s: html.escape(str(s), quote=True)


def targets(t):
    n = sum(1 for x in t if x["category"] == "MCP servers")
    c = sum(1 for x in t if x["category"] == "coding")
    infra = sum(1 for x in t if x["category"] == "agent infra")
    # agent-infra earned clicks at position 6.5 in the Oct 20-24 Web export, then had no row in the Oct 26-Nov 5 page export.
    L = [
        ("categories/mcp-servers.html", f"All {n:,} MCP servers"),
        ("categories/agent-infra.html", f"All {infra:,} agent infra tools"),
        ("mcp/index.html", "Best MCP servers by task"),
        ("mcp/pricing.html", "MCP server pricing"),
        ("mcp/status/", "MCP status"),
        ("best/mcp-servers-for-cursor.html", "MCP servers for Cursor"),
        ("best/mcp-servers-for-claude-code.html", "MCP servers for Claude Code"),
        ("best/ai-coding-agents.html", "Best AI coding agents"),
        ("categories/coding.html", f"All {c:,} coding agents"),
        ("s/free-ai-coding-agents.html", "Free AI coding agents"),
        ("s/open-source-ai-coding-agents.html", "Open-source coding agents"),
        ("best/ai-browser-agents.html", "Best AI browser agents"),
        ("tasks/browsing-the-web-browser-automation.html", "AI browser automation tools"),
        ("best/ai-voice-agent-platforms.html", "Best AI voice agent platforms"),
        ("tasks/phone-calls.html", "AI phone & call agents"),
        ("best/ai-business-agents.html", "AI agents for business"),
        ("best/conductor-alternatives.html", "Conductor alternatives"),
        ("best/index.html", "All best-of lists"),
    ]
    return [(p, l) for p, l in L if os.path.exists(p)]


# Homepage omitted Nov 9 2026 (owner): pills cluttered the top; footer line carries the links instead.
SOURCES = [
    "categories/index.html",
    "best/index.html",
    "s/index.html",
    "mcp/index.html",
    "leaderboard/index.html",
    "categories/mcp-servers.html",
    "categories/coding.html",
    "best/ai-coding-agents.html",
    "best/ai-browser-agents.html",
    "best/mcp-servers-for-cursor.html",
    "best/mcp-servers-for-claude-code.html",
    "s/best-mcp-servers.html",
    "tasks/index.html",
    "best/ai-voice-agent-platforms.html",
    "best/ai-business-agents.html",
]
CH = 'class="chip" style="display:inline-flex;align-items:center;min-height:44px;box-sizing:border-box;text-decoration:none;color:inherit"'

# Strongest list pages for the site-wide footer line (no hard-coded counts).
FOOT_LINKS = [
    ("s/best-mcp-servers.html", "Best MCP servers"),
    ("best/mcp-servers-for-cursor.html", "MCP servers for Cursor"),
    ("best/ai-coding-agents.html", "Best AI coding agents"),
    ("best/ai-browser-agents.html", "Best AI browser agents"),
    ("best/index.html", "All best-of lists"),
]


def footpop_html(prefix=""):
    """Short Popular lists line for the site-wide footer. prefix is '' or '../'*depth."""
    links = "".join(
        f'<a href="{e(prefix + p)}">{e(l)}</a>' for p, l in FOOT_LINKS if os.path.exists(p)
    )
    return (
        '<!--il:footpop--><nav class="footpop" aria-label="Popular lists">'
        '<span class="footpop-label">Popular lists</span>'
        f"{links}</nav><!--/il:footpop-->"
    )


def apply_footer_line():
    """Idempotent: put the Popular lists footer line on every page with a column footer."""
    block_root = footpop_html("")
    if "Best MCP servers" not in block_root:
        print("build_intlinks: footpop skipped, no targets on disk")
        return 0
    done = 0
    skip_dirs = {".git", "node_modules", "data", "scripts", "assets", "preview", "pagefind", "bot-packages"}
    skip_files = {"googlee55704a7d5d75240.html", "og.html", "stats.js.html", "outreach-tracker.html"}
    for root_dir, dirs, fnames in os.walk("."):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for fn in fnames:
            if not fn.endswith(".html") or fn in skip_files:
                continue
            rel = os.path.relpath(os.path.join(root_dir, fn), ".")
            s = open(rel, encoding="utf-8").read()
            if 'class="footcols"' not in s and "footcols" not in s:
                continue
            if "<footer" not in s:
                continue
            # Strip any previous footpop, then insert before footbase (or before </div></footer wrap close).
            s2 = re.sub(r"<!--il:footpop-->.*?<!--/il:footpop-->", "", s, flags=re.S)
            depth = rel.count("/")
            prefix = "../" * depth
            block = footpop_html(prefix)
            if "footbase" in s2:
                s2 = s2.replace('<div class="footbase">', block + '<div class="footbase">', 1)
            else:
                # Fallback: just before closing footer
                i = s2.rfind("</footer>")
                if i < 0:
                    continue
                s2 = s2[:i] + block + s2[i:]
            if s2 != s:
                open(rel, "w", encoding="utf-8").write(s2)
                done += 1
    print(f"build_intlinks: Popular lists footer line on {done} pages")
    return done


def strip_home_pills():
    """Remove the homepage Popular lists chip block so tools stay right under the MCP status box."""
    path = "index.html"
    if not os.path.exists(path):
        return False
    s = open(path, encoding="utf-8").read()
    s2 = re.sub(r"<!--il:pop-->.*?<!--/il:pop-->", "", s, flags=re.S)
    if s2 != s:
        open(path, "w", encoding="utf-8").write(s2)
        print("build_intlinks: removed Popular lists pills from homepage")
        return True
    print("build_intlinks: homepage already has no Popular lists pills")
    return False


def run(t):
    T = targets(t)
    strip_home_pills()
    done = 0
    for src in SOURCES:
        if not os.path.exists(src):
            print("build_intlinks: missing source, skipped:", src)
            continue
        s = open(src).read()
        s = re.sub(r"<!--il:pop-->.*?<!--/il:pop-->", "", s, flags=re.S)
        up = "../" * src.count("/")
        a = "".join(f'<a {CH} href="{e(up + p)}">{e(l)}</a>' for p, l in T if p != src)
        b = (
            f'<!--il:pop--><section class="wrap" aria-label="Popular lists" style="margin:24px auto 8px">'
            f'<h2 style="font-size:16px;margin:0 0 4px">Popular lists</h2><div class="chips">{a}</div></section><!--/il:pop-->'
        )
        if "<footer" not in s:
            print("build_intlinks: no footer, skipped:", src)
            continue
        i = s.rfind("<footer")
        s = s[:i] + b + s[i:]
        open(src, "w").write(s)
        done += 1
    print(f"build_intlinks: Popular lists chips on {done} hub pages, {len(T)} targets")
    apply_footer_line()


if __name__ == "__main__":
    run(json.load(open("tools.json")))
