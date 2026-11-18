"""Descriptive alt text on images (Search Console / @Niche_Lion playbook, Nov 17 2026).

Post-processing pass, run at the end of build_site.py after build_seo_trim:
- tool logos (assets/logos/<slug>.png) rendered with alt="" next to the tool name get
  alt="<Tool name> logo" from tools.json (slug -> name). The logo sits beside the
  tool name as text, so the alt names the logo rather than repeating the page.
- a missing alt attribute on the AgentScout wordmark (logo-wordmark.svg) gets
  alt="AgentScout" (og.html shipped with no alt at all).
- logos whose slug is not in tools.json (removed tools) are left alone and reported.
Idempotent: only touches alt="" (or a missing alt) on those two patterns; never
overwrites a non-empty alt. Other empty-alt images (bot-template icons, favicon,
wordmark beside sr-only "AgentScout" text) are decorative and stay empty.
"""
import html
import json
import os
import re

e = lambda s: html.escape(str(s), quote=True)

SKIP_DIRS = {".git", "node_modules", "data", "scripts", "assets", "preview", "pagefind", "bot-packages"}
SKIP_FILES = {"googlee55704a7d5d75240.html"}

IMG_RE = re.compile(r"<img\b[^>]*>", re.S)
SRC_RE = re.compile(r"""src\s*=\s*["']([^"']+)["']""")
ALT_RE = re.compile(r"""alt\s*=\s*(["'])(.*?)\1""")


def _names(t=None):
    names = {}
    tools = t if t is not None else json.load(open("tools.json", encoding="utf-8"))
    for x in tools:
        if isinstance(x, dict) and x.get("slug") and x.get("name"):
            names[x["slug"]] = x["name"]
    return names


def _fix_tag(tag, names, unresolved):
    m = SRC_RE.search(tag)
    if not m:
        return tag, None
    src = m.group(1)
    base = os.path.basename(src)
    stem, _ext = os.path.splitext(base)
    am = ALT_RE.search(tag)
    if am and am.group(2).strip():
        return tag, None  # already descriptive; never overwrite
    if "assets/logos/" in src:
        name = names.get(stem)
        if not name:
            unresolved.add(stem)
            return tag, None
        alt = f"{name} logo"
    elif stem == "logo-wordmark" and am is None:
        alt = "AgentScout"
    else:
        return tag, None
    if am:
        return tag[: am.start()] + f'alt="{e(alt)}"' + tag[am.end():], alt
    return tag[:4] + f' alt="{e(alt)}"' + tag[4:], alt


def run(t=None):
    names = _names(t)
    filled = 0
    unresolved = set()
    files_changed = 0
    for root_dir, dirs, fnames in os.walk("."):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS]
        for fn in fnames:
            if not fn.endswith(".html") or fn in SKIP_FILES:
                continue
            rel = os.path.relpath(os.path.join(root_dir, fn), ".")
            s = open(rel, encoding="utf-8").read()

            def _sub(m):
                nonlocal filled
                new, alt = _fix_tag(m.group(0), names, unresolved)
                if alt is not None:
                    filled += 1
                return new

            s2 = IMG_RE.sub(_sub, s)
            if s2 != s:
                open(rel, "w", encoding="utf-8").write(s2)
                files_changed += 1
    print(f"build_alt: descriptive alt on {filled} images across {files_changed} pages")
    if unresolved:
        print(f"build_alt: {len(unresolved)} logo slugs not in tools.json, left alone: {sorted(unresolved)}")
    return filled


if __name__ == "__main__":
    run(json.load(open("tools.json", encoding="utf-8")))
