"""Standing recheck (Oct 18, 2026): run after every build and before every commit. Exit 1 if any check fails.
Checks: duplicates (scripts/dedupe_check.py), off-topic share per list page (scripts/check_relevance.py --strict),
logos (scripts/check_logos.py, when present), sponsor page stays hidden (noindex, not in sitemap, not linked)."""
import subprocess,sys,os,glob,re
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
bad=[]
def run(name,cmd):
    r=subprocess.run(cmd,capture_output=True,text=True); out=(r.stdout+r.stderr).strip().splitlines()
    print(f"[{'ok' if r.returncode==0 else 'FAIL'}] {name}: "+(out[-1] if out else ""))
    if r.returncode: bad.append(name); print("\n".join("   "+l for l in out[-25:]))
run("dedupe",[sys.executable,"scripts/dedupe_check.py"])
run("relevance",[sys.executable,"scripts/check_relevance.py","--strict","--write"])
if os.path.exists("scripts/check_logos.py"): run("logos",[sys.executable,"scripts/check_logos.py"])
if os.path.exists("sponsor.html"):
    s=open("sponsor.html").read(); sm=open("sitemap.xml").read() if os.path.exists("sitemap.xml") else ""
    linked=[f for f in glob.glob("**/*.html",recursive=True) if f!="sponsor.html" and re.search(r'href="[^"]*sponsor\.html',open(f,errors="ignore").read())]
    ok=('noindex' in s) and ('sponsor.html' not in sm) and not linked
    print(f"[{'ok' if ok else 'FAIL'}] sponsor page hidden: noindex={'noindex' in s}, in sitemap={'sponsor.html' in sm}, linked from {len(linked)} pages {linked[:3]}")
    if not ok: bad.append("sponsor")
print("RECHECK", "FAILED: "+", ".join(bad) if bad else "passed")
sys.exit(1 if bad else 0)
