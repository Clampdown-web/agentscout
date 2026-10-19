"""Self-hosted Inter (Oct 18, 2026 PT). Same font files Google Fonts serves (Inter v20, OFL), now in assets/fonts/.
Replaces the Google Fonts <link>s with a preload of the latin subset and drops the Google hosts from the CSP.
Idempotent; runs at the end of build_site.py over every HTML page and the detail template."""
import os,re
OLD=re.compile(r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\s*<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>\s*<link href="https://fonts\.googleapis\.com/css2\?family=Inter[^"]*" rel="stylesheet">|<link href="https://fonts\.googleapis\.com/css2\?family=Inter[^"]*" rel="stylesheet">')
CSS=re.compile(r'<link rel="stylesheet" href="([^"]*?)styles\.css')
def fix(s):
    m=CSS.search(s)
    if not m: return s
    pre=m.group(1)
    s=OLD.sub(lambda _:f'<link rel="preload" href="{pre}assets/fonts/inter-latin.woff2" as="font" type="font/woff2" crossorigin>',s)
    return s.replace("style-src 'self' 'unsafe-inline' https://fonts.googleapis.com","style-src 'self' 'unsafe-inline'").replace("font-src 'self' https://fonts.gstatic.com","font-src 'self'")
def run():
    n=0;left=[]
    files=["data/detail.tpl"]
    for root,ds,fs in os.walk("."):
        ds[:]=[d for d in ds if d not in (".git","node_modules","app")]
        files+= [os.path.join(root,f)[2:] for f in fs if f.endswith(".html")]
    for f in files:
        if f=="outreach-tracker.html": continue
        s=open(f).read(); t=fix(s)
        if t!=s: open(f,"w").write(t); n+=1
        if "fonts.googleapis.com" in t: left.append(f)
    print(f"fonts: self-hosted Inter on {n} files" + (f"; still on Google Fonts: {left[:5]}" if left else ""))
if __name__=="__main__": run()
