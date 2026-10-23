"""Popular lists block (owner-approved Oct 22 2026 PT): internal links from the strongest pages (homepage, hubs, top best/ pages)
to the directory-style list pages that are starting to get Search Console impressions. Idempotent marker block, placed before
<footer. A page never links to itself. Counts come from tools.json. No new colors: existing .chip/.chips styles, 44px tap height."""
import json,os,re,html
e=lambda s:html.escape(str(s),quote=True)
def targets(t):
    n=sum(1 for x in t if x["category"]=="MCP servers"); c=sum(1 for x in t if x["category"]=="coding")
    L=[("categories/mcp-servers.html",f"All {n:,} MCP servers"),("mcp/index.html","Best MCP servers by task"),
       ("mcp/pricing.html","MCP server pricing"),("mcp/link-status.html","MCP link status"),
       ("best/mcp-servers-for-cursor.html","MCP servers for Cursor"),("best/mcp-servers-for-claude-code.html","MCP servers for Claude Code"),
       ("best/ai-coding-agents.html","Best AI coding agents"),("categories/coding.html",f"All {c:,} coding agents"),("s/free-ai-coding-agents.html","Free AI coding agents"),
       ("s/open-source-ai-coding-agents.html","Open-source coding agents"),("best/ai-browser-agents.html","Best AI browser agents"),
       ("best/index.html","All best-of lists")]
    return [(p,l) for p,l in L if os.path.exists(p)]
SOURCES=["index.html","categories/index.html","best/index.html","s/index.html","mcp/index.html","leaderboard/index.html",
 "categories/mcp-servers.html","categories/coding.html","best/ai-coding-agents.html","best/ai-browser-agents.html",
 "best/mcp-servers-for-cursor.html","best/mcp-servers-for-claude-code.html","s/best-mcp-servers.html"]
CH='class="chip" style="display:inline-flex;align-items:center;min-height:44px;box-sizing:border-box;text-decoration:none;color:inherit"'
def run(t):
    T=targets(t); done=0
    for src in SOURCES:
        if not os.path.exists(src): print("build_intlinks: missing source, skipped:",src); continue
        s=open(src).read(); s=re.sub(r"<!--il:pop-->.*?<!--/il:pop-->","",s,flags=re.S)
        up="../"*src.count("/")
        a="".join(f'<a {CH} href="{e(up+p)}">{e(l)}</a>' for p,l in T if p!=src)
        b=f'<!--il:pop--><section class="wrap" aria-label="Popular lists" style="margin:24px auto 8px"><h2 style="font-size:16px;margin:0 0 4px">Popular lists</h2><div class="chips">{a}</div></section><!--/il:pop-->'
        if "<footer" not in s: print("build_intlinks: no footer, skipped:",src); continue
        i=s.find("<!--dir:top-->") if src=="index.html" and "<!--dir:top-->" in s else s.rfind("<footer")  # Oct 23 2026 (owner): homepage directory sits last, right above the footer
        s=s[:i]+b+s[i:]; open(src,"w").write(s); done+=1
    print(f"build_intlinks: Popular lists on {done} pages, {len(T)} targets")
if __name__=="__main__": run(json.load(open("tools.json")))
