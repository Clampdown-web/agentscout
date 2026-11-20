"""Standing recheck (Oct 18, 2026): run after every build and before every commit. Exit 1 if any check fails.
Checks: duplicates (scripts/dedupe_check.py), off-topic share per list page (scripts/check_relevance.py --strict),
logos (scripts/check_logos.py, when present), no sideways scroll on phones (scripts/check_overflow.py), sponsor page stays noindex and out of the sitemap (PR #171). Stripe links stay."""
import subprocess,sys,os,re
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def run(name,cmd):
    r=subprocess.run(cmd,capture_output=True,text=True); out=(r.stdout+r.stderr).strip().splitlines()
    print(f"[{'ok' if r.returncode==0 else 'FAIL'}] {name}: "+(out[-1] if out else ""))
    if r.returncode:
        print("\n".join("   "+l for l in out[-25:]))
        print("RECHECK FAILED: "+name)
        sys.exit(r.returncode or 1)
run("dedupe",[sys.executable,"scripts/dedupe_check.py"])
run("relevance",[sys.executable,"scripts/check_relevance.py","--strict","--write"])
if os.path.exists("scripts/check_logos.py"): run("logos",[sys.executable,"scripts/check_logos.py"])
if os.path.exists("scripts/check_overflow.py"): run("mobile overflow (360/390px, every page type, text 1x and 1.3x)",[sys.executable,"scripts/check_overflow.py"])
_cta="scripts/verify_4tier_ctas.py" if os.path.exists("scripts/verify_4tier_ctas.py") else "/workspace/scripts/verify_4tier_ctas.py"
if os.path.exists(_cta): run("4-tier neon CTA buttons", [sys.executable, _cta])
if os.path.exists("scripts/check_nav_footer.py"): run("unified nav and footer", [sys.executable, "scripts/check_nav_footer.py"])
if os.path.exists("sponsor.html"):
    s=open("sponsor.html").read(); sub=open("submit.html").read() if os.path.exists("submit.html") else ""; sm=open("sitemap.xml").read() if os.path.exists("sitemap.xml") else ""
    stripe_ok=('buy.stripe.com/3cIaEY6T15hlfJr135e7m0e' in s and 'buy.stripe.com/bJefZi4KT6lp9l3dPRe7m00' in s and 'buy.stripe.com/6oU4gA2CL9xB2WFcLNe7m01' in s and 'buy.stripe.com/3cIaEY6T15hlfJr135e7m0e' in sub and 'buy.stripe.com/bJefZi4KT6lp9l3dPRe7m00' in sub and 'buy.stripe.com/6oU4gA2CL9xB2WFcLNe7m01' in sub)
    # PR #171: the sponsor page is noindex on purpose. Do not require it to be indexed.
    in_sitemap=bool(re.search(r"<loc>[^<]*sponsor\.html</loc>", sm))
    noindex='name="robots" content="noindex' in s
    ok=noindex and (not in_sitemap) and stripe_ok
    print(f"[{'ok' if ok else 'FAIL'}] sponsor page hidden: noindex={noindex}, in sitemap={in_sitemap}, stripe_links={stripe_ok}")
    if not ok:
        print("RECHECK FAILED: sponsor")
        sys.exit(1)
print("RECHECK passed")
sys.exit(0)
