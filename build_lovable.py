"""Re-apply the Lovable 25 AI Agent Packs section after a tool-page rewrite.

build_site.py and the enrichment passes that patch tools/*.html call run()
so a later rewrite cannot drop the section. The writer is idempotent.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run() -> int:
    script = ROOT / "scripts" / "write_lovable_page.py"
    proc = subprocess.run([sys.executable, str(script)], cwd=str(ROOT))
    if proc.returncode:
        print("BUILD FAILED: tools/lovable.html is missing the 25 AI Agent Packs section")
        sys.exit(proc.returncode)
    return 0
