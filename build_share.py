"""Share button (share.js) on every content page (tools, categories, tasks, best-of, alternatives, /s/, /for/, compare, news, free tools, hubs, home, new, quiz, generator, about, badges, newsletter). Applied from build_tasks.sitewide() so rebuilds keep it."""
import re
ICON='<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7"/><path d="M16 6l-4-4-4 4"/><path d="M12 2v13"/></svg>'
WRAP=('<span class="sharewrap"><button type="button" class="btn sharebtn" data-share aria-label="Share this page">'+ICON+'Share</button>'
      '<span class="sharecount" hidden></span></span>')
# Pages with no share button on purpose: submit.html (form), 404.html, privacy.html (legal), saved.html (personal list), og.html/outreach-tracker.html (internal)
# mcp/ hub + MCP task pages added Oct 21 2026 upkeep (they had no share button)
EXTRA={"index.html","new.html","news.html","quiz.html","generate.html","about.html","badges.html","newsletter.html"}  # added Oct 18 2026 share audit
CENTER={"index.html","generate.html"}  # centered hero h1 -> centered button
def wanted(f):
    return (f.startswith(("tools/","best/","s/","for/","categories/","tasks/","compare/","news/","free-tools/","mcp/")) or f=="free-tools.html" or f in EXTRA)
def apply(f,s,d,V):
    if not wanted(f) or "<h1" not in s: return s
    if 'data-share' not in s:
        if f.startswith("tools/") and '<span data-actions=' in s:
            s=re.sub(r'(<span data-actions="[^"]*" style="display:contents"></span>)',lambda m:m.group(1)+WRAP,s,count=1)
        else:
            s=re.sub(r'(<h1\b.*?</h1>)',lambda m:m.group(1)+'<div class="shareacts'+(' center' if f in CENTER else '')+'">'+WRAP+'</div>',s,count=1,flags=re.S)
    if 'share.js?v=' not in s:
        s=re.sub(r'(<script src="[^"]*?track\.js\?v=\d+" defer></script>)',lambda m:m.group(1)+f'<script src="{d}share.js?v={V}" defer></script>',s,count=1)
        if 'share.js?v=' not in s: s=s.replace('</body>',f'<script src="{d}share.js?v={V}" defer></script></body>',1)
    return s
