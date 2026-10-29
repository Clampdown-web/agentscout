#!/usr/bin/env python3
"""START HERE guides and the trust lines the pack pages read.

The guide is generated from each pack's real files. Dates are never written
here: verify_bot_zip_packages.py records them in data/pack-verification.json
and the page build only displays a line when that record exists.
"""
from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_PATH = ROOT / "data" / "pack-verification.json"
ROLE_ZIPS = ROOT / "bot-packages" / "25-agent-packs" / "zips"
FLAGSHIP_ZIPS = ROOT / "bot-packages" / "zips"
SETUP_LINE = "Set up for your business in 10 minutes."
GUIDE_LINE = "Includes a START HERE setup guide"
HELP_EMAIL = "support@agentscouthq.com"
ALLOWED_PLACEHOLDERS = {"YOUR_COMPANY", "YOUR_DOMAIN"}
_MONTHS = (
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
_PROMISE_BANS = (
    "free setup",
    "set it up for you",
    "we'll set it up",
    "we will set it up",
    "24/7 support",
    "support window",
    "within 24 hours",
    "response within",
    "priority support",
    "dedicated support",
)
_prepared = False


def format_tested_on(iso_day: str) -> str:
    year, month, day = (int(part) for part in iso_day.split("-"))
    return f"Tested on {_MONTHS[month]} {day}, {year}"


def load_verification() -> dict:
    if not VERIFICATION_PATH.is_file():
        return {}
    try:
        data = json.loads(VERIFICATION_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def tested_line(slug: str) -> str:
    record = (load_verification().get("packs") or {}).get(slug) or {}
    if not record.get("ok"):
        return ""
    day = str(record.get("verified_on") or "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        return ""
    return format_tested_on(day)


def verified_on(slug: str) -> str:
    record = (load_verification().get("packs") or {}).get(slug) or {}
    if not record.get("ok"):
        return ""
    day = str(record.get("verified_on") or "")
    return day if re.fullmatch(r"\d{4}-\d{2}-\d{2}", day) else ""


def zip_names(path: Path) -> list[str]:
    if not path.is_file():
        return []
    with zipfile.ZipFile(path) as archive:
        return [info.filename for info in archive.infolist() if not info.is_dir()]


def detect_platforms(names: list[str]) -> list[str]:
    """Platforms evidenced by files in the ZIP. Order is the public line order."""
    bases = {name.replace("\\", "/").split("/")[-1] for name in names}
    paths = [name.replace("\\", "/") for name in names]
    found: list[str] = []
    if "SYSTEM.md" in bases:
        found.append("Grok Bot")
    if "LOVABLE.md" in bases and any(path.endswith("SKILL.md") for path in paths):
        found.append("Lovable")
    if "CLAUDE.md" in bases:
        found.append("Claude Code")
    if ".cursorrules" in bases:
        found.append("Cursor")
    if "AGENTS.md" in bases:
        found.append("Codex")
    return found


def works_with_line(platforms: list[str]) -> str:
    """Buyer-facing line. Grok + Lovable SKILL.md use the approved sentence."""
    has_grok = "Grok Bot" in platforms
    has_lovable = "Lovable" in platforms
    if has_grok and has_lovable:
        return "Works with: Grok Bot (also imports as Lovable SKILL.md)"
    if has_grok:
        return "Works with: Grok Bot"
    if has_lovable:
        return "Works with: Lovable (imports as SKILL.md)"
    others = [name for name in platforms if name not in {"Grok Bot", "Lovable"}]
    if others:
        return "Works with: " + " · ".join(others)
    return ""


def works_with_for_zip(path: Path) -> str:
    return works_with_line(detect_platforms(zip_names(path)))


def placeholder_problems(text: str) -> list[str]:
    problems = []
    doubles = set(re.findall(r"\{\{([^{}]+)\}\}", text))
    extra = sorted(doubles - ALLOWED_PLACEHOLDERS)
    if extra:
        problems.append("unexpected placeholders " + ", ".join(extra))
    singles = sorted(set(re.findall(r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)\}(?!\})", text)))
    if singles:
        problems.append("single-brace placeholders " + ", ".join(singles))
    lowered = text.lower()
    for phrase in _PROMISE_BANS:
        if phrase in lowered:
            problems.append("unsupported promise: " + phrase)
    return problems


def _require_clean(text: str, label: str) -> str:
    problems = placeholder_problems(text)
    if problems:
        raise SystemExit(f"{label}: " + "; ".join(problems))
    return text


def _import_text(names: list[str], skill_file: str) -> str:
    bases = {name.replace("\\", "/").split("/")[-1] for name in names}
    sentences = ["Import the template."]
    if "SYSTEM.md" in bases:
        sentences.append("In Grok Bot, create a teammate and paste SYSTEM.md into its instructions.")
    if "LOVABLE.md" in bases and skill_file:
        sentences.append(
            "In Lovable, import this ZIP under Workspace settings, then Skills, then Add, then Upload ZIP. "
            f"Lovable reads {skill_file}."
        )
    hosts = []
    if "CLAUDE.md" in bases:
        hosts.append("Claude Code (CLAUDE.md)")
    if ".cursorrules" in bases:
        hosts.append("Cursor (.cursorrules)")
    if "AGENTS.md" in bases:
        hosts.append("Codex (AGENTS.md)")
    if hosts:
        sentences.append("This folder also includes " + ", ".join(hosts) + ".")
    if len(sentences) == 1:
        sentences.append("Unzip the folder and open the instruction file for your agent host.")
    return " ".join(sentences)


def _replace_text(kind: str) -> str:
    if kind == "role":
        command = 'python3 setup_workspace.py --apply --company "Your Company" --domain "yourdomain.com"'
    else:
        command = 'python3 setup_workspace.py --company "Your Company" --domain "yourdomain.com"'
    return (
        "Replace {{YOUR_COMPANY}} and {{YOUR_DOMAIN}}. From the unzipped folder run "
        f"`{command}`. That writes those two values through the package."
    )


def _connect_text(names: list[str]) -> str:
    bases = {name.replace("\\", "/").split("/")[-1] for name in names}
    if "mcp.json" not in bases and ".mcp.json" not in bases:
        return (
            "Connect tools. This package does not ship a tool connection file. "
            "Use the accounts you already have, and do not add a service this folder does not mention."
        )
    return (
        "Connect tools. Open mcp.json and, if your company already runs an MCP server, put that server's URL in the entry. "
        "If you do not have one, leave the file unchanged. The file does not connect a tool by itself."
    )


def _role_names(agent: dict) -> list[str]:
    skill = f"skills/{agent['skill_slug']}/SKILL.md"
    script = f"scripts/{agent['script']}"
    return [
        "SYSTEM.md",
        "LOVABLE.md",
        "CLAUDE.md",
        ".cursorrules",
        "AGENTS.md",
        "mcp.json",
        "setup_workspace.py",
        skill,
        script,
        "context/business-profile.md",
        "routines/routines.json",
    ]


def role_steps(agent: dict) -> list[dict]:
    names = _role_names(agent)
    skill = f"skills/{agent['skill_slug']}/SKILL.md"
    script = f"scripts/{agent['script']}"
    return [
        {"name": "Import the template", "text": _import_text(names, skill)},
        {"name": "Replace {{YOUR_COMPANY}} and {{YOUR_DOMAIN}}", "text": _replace_text("role")},
        {"name": "Connect tools", "text": _connect_text(names)},
        {
            "name": "Run the first task",
            "text": f"Run the first task. From this folder run `python3 {script} --dry-run`.",
        },
    ]


def role_expect(agent: dict) -> str:
    first = agent["routines"][0][2] if agent.get("routines") else "the first routine"
    return (
        f"The dry run prints a JSON report from sample rows and exits. "
        f"It does not email, post, spend, delete, or file anything. "
        f"The routine \"{first}\" is a draft for you to read. "
        f"You decide what leaves the machine."
    )


def role_inside(agent: dict) -> list[str]:
    count = len(agent["routines"])
    first = agent["routines"][0][2] if agent.get("routines") else "the first routine"
    noun = "routine" if count == 1 else "routines"
    return [
        f"`SYSTEM.md`, the role instructions for the {agent['card_title']}",
        f"`skills/{agent['skill_slug']}/SKILL.md`, the playbook",
        f"`scripts/{agent['script']}`, a local Python 3 script (standard library only)",
        f"`routines/`, {count} scheduled {noun}, starting with {first}",
        "`setup_workspace.py`, which writes your company name and domain",
        "`mcp.json`, an optional MCP server entry",
        "`context/business-profile.md`, the offer, voice, and constraints",
    ]


def render_markdown(title: str, intro: str, inside: list[str], steps: list[dict], expect: str) -> str:
    bullets = "\n".join(f"- {line}" for line in inside)
    numbered = "\n".join(f"{index}. {step['text']}" for index, step in enumerate(steps, start=1))
    text = (
        f"# START HERE: {title}\n\n"
        f"{intro}\n\n"
        f"## What's inside\n\n"
        f"{bullets}\n\n"
        f"## 10-minute setup\n\n"
        f"{numbered}\n\n"
        f"## What to expect on the first run\n\n"
        f"{expect}\n\n"
        f"## Help\n\n"
        f"Questions about this download: {HELP_EMAIL}\n"
    )
    return _require_clean(text, title)


def render_role_start_here(agent: dict) -> str:
    intro = (
        f"{agent['product_name']} for {{{{YOUR_COMPANY}}}} ({agent['tagline']}). "
        f"Domain placeholder: {{{{YOUR_DOMAIN}}}}."
    )
    return render_markdown(
        agent["product_name"],
        intro,
        role_inside(agent),
        role_steps(agent),
        role_expect(agent),
    )


def _python_commands(text: str, names: set[str]) -> list[str]:
    found = []
    for match in re.finditer(r"python3\s+([A-Za-z0-9_./-]+\.py)", text):
        rel = match.group(1)
        if rel in names and rel not in found:
            found.append(rel)
    return found


def _expect_for_script(rel: str) -> str:
    base = rel.split("/")[-1]
    if base == "daily_deep_audit.py":
        return (
            "If {{YOUR_DOMAIN}} is still unfilled, python3 "
            + rel
            + " prints a dry-run line and does not open a connection. "
            "After you replace {{YOUR_DOMAIN}}, it requests that site's homepage and prints a pass or a failure. "
            "It does not send email, post, or spend."
        )
    if base in {"audit_jsonld_and_llms.py", "check_seo_aeo.py", "llms_validator.py"}:
        return (
            f"`python3 {rel}` scans HTML files in that folder and prints how many JSON-LD blocks it found. "
            "An empty folder reports zero files. It does not send email, post, or spend."
        )
    if base in {"scan_x_outliers.py", "outlier_scanner.py"}:
        return (
            f"`python3 {rel}` prints JSON from built-in sample posts. "
            "It does not post, send email, or spend."
        )
    if base == "handoff_coordinator.py":
        return (
            f"`python3 {rel}` prints a JSON list of the four bot roles and exits. "
            "It does not send email, post, or spend."
        )
    return (
        f"`python3 {rel}` prints a local report and exits. "
        "It does not send email, post, or spend."
    )


def _flagship_inside(names: list[str]) -> list[str]:
    skills = [name for name in names if name.endswith("SKILL.md")]
    scripts = [
        name for name in names
        if name.endswith(".py") and (name.startswith("scripts/") or "/scripts/" in name)
    ]
    systems = [name for name in names if name.endswith("SYSTEM.md")]
    lines = []
    folders = []
    for name in names:
        top = name.split("/")[0]
        if "/" in name and top not in folders and not top.startswith("."):
            folders.append(top)
    bot_folders = [folder for folder in folders if folder[0].isdigit() or folder.endswith("-bot")]
    if bot_folders:
        lines.append("Bot folders: " + ", ".join(f"`{folder}`" for folder in bot_folders))
    if len(systems) == 1:
        lines.append(f"`{systems[0]}`, the role instructions")
    elif systems:
        lines.append(f"`SYSTEM.md` in {len(systems)} folders, including `{systems[0]}`")
    if len(skills) <= 3:
        lines.extend(f"`{skill}`" for skill in skills)
    elif skills:
        lines.append(f"{len(skills)} skill files, including `{skills[0]}`")
    show = scripts[:4]
    lines.extend(f"`{script}`" for script in show)
    if len(scripts) > len(show):
        lines.append(f"{len(scripts) - len(show)} more Python scripts under the bot folders")
    if "README-TEAM-BUNDLE.md" in names:
        lines.append("`README-TEAM-BUNDLE.md`, the four-bot handoff notes")
    elif "README-QUICKSTART.md" in names:
        lines.append("`README-QUICKSTART.md`")
    if any(name.endswith("mcp.json") for name in names):
        lines.append("`mcp.json`, an optional MCP server entry")
    if any(name.endswith("setup_workspace.py") for name in names):
        lines.append("`setup_workspace.py`, which writes your company name and domain")
    routine_files = [name for name in names if "/routines/" in name or name.startswith("routines/")]
    if routine_files:
        lines.append(f"`routines/` ({len(routine_files)} files)")
    return lines


def render_flagship_start_here(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        names = [info.filename for info in archive.infolist() if not info.is_dir()]
        title = path.stem
        if archive.comment:
            try:
                comment = json.loads(archive.comment.decode("utf-8"))
                title = str(comment.get("product") or title)
            except (json.JSONDecodeError, UnicodeDecodeError):
                title = path.stem
        readme_name = "README-TEAM-BUNDLE.md" if "README-TEAM-BUNDLE.md" in names else "README-QUICKSTART.md"
        readme = archive.read(readme_name).decode("utf-8", "replace") if readme_name in names else ""
    name_set = set(names)
    commands = _python_commands(readme, name_set)
    if not commands:
        commands = [name for name in names if "/scripts/" in name and name.endswith(".py")][:1]
    skill = next((name for name in names if name.endswith("SKILL.md")), "")
    skill_label = "SKILL.md" if skill else ""
    task = "Run the first task."
    if len(commands) == 1:
        task += f" From the unzipped folder run `python3 {commands[0]}`."
    elif commands:
        joined = ", ".join(f"`python3 {command}`" for command in commands)
        task += f" From the unzipped folder run {joined}."
    else:
        task += " Open README-QUICKSTART.md and run the first Python command it lists."
    steps = [
        {"name": "Import the template", "text": _import_text(names, skill_label)},
        {"name": "Replace {{YOUR_COMPANY}} and {{YOUR_DOMAIN}}", "text": _replace_text("flagship")},
        {"name": "Connect tools", "text": _connect_text(names)},
        {"name": "Run the first task", "text": task},
    ]
    if len(commands) == 1:
        expect = _expect_for_script(commands[0])
    else:
        expect = " ".join(_expect_for_script(command) for command in commands)
    intro = f"{title}. Use this folder for {{{{YOUR_COMPANY}}}} on {{{{YOUR_DOMAIN}}}}."
    return render_markdown(title, intro, _flagship_inside(names), steps, expect)


def write_root_into_zip(path: Path, filename: str, content: str) -> None:
    """Replace one archive-root file and keep every other member and the zip comment."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(path, "r") as source:
        comment = source.comment
        members = []
        for info in source.infolist():
            if info.filename == filename:
                continue
            members.append((info, source.read(info.filename)))
    with zipfile.ZipFile(tmp, "w") as target:
        for info, payload in members:
            copied = zipfile.ZipInfo(filename=info.filename, date_time=info.date_time)
            copied.compress_type = info.compress_type or zipfile.ZIP_DEFLATED
            copied.external_attr = info.external_attr
            copied.flag_bits = info.flag_bits & ~0x1  # drop encryption flag if any
            target.writestr(copied, payload)
        guide = zipfile.ZipInfo(filename=filename)
        guide.compress_type = zipfile.ZIP_DEFLATED
        target.writestr(guide, content.encode("utf-8"))
        target.comment = comment
    tmp.replace(path)


def refresh_flagship_zips() -> None:
    for path in sorted(FLAGSHIP_ZIPS.glob("*.zip")):
        guide = render_flagship_start_here(path)
        write_root_into_zip(path, "START-HERE.md", guide)


def prepare_packs() -> None:
    """Rebuild role ZIPs and refresh flagship START HERE files once per process."""
    global _prepared
    if _prepared:
        return
    import build_25_agent_packs

    build_25_agent_packs.build()
    refresh_flagship_zips()
    _prepared = True


def stamp_verification(passed: dict[str, dict]) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    payload = {
        "source": "scripts/verify_bot_zip_packages.py",
        "verified_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "packs": passed,
    }
    VERIFICATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    VERIFICATION_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def success_record(zip_rel: str) -> dict:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return {
        "ok": True,
        "verified_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verified_on": now.date().isoformat(),
        "zip": zip_rel,
    }
