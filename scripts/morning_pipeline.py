#!/usr/bin/env python3
"""Morning pipeline. The first failing check stops the run.

Steps, in order: recheck, predeploy, the local audit, tests, then the live
audit. A failing step writes reports/pipeline-failure-<Pacific date>.md, prints
one PIPELINE FAILED line, and returns that step's exit code. Later steps do
not run, and push is not called.

The live audit is the network fetch. It is retried once after 300 seconds.
Recheck, predeploy, the local audit, and the tests are not retried.

  PIPELINE_SKIP=live python3 scripts/morning_pipeline.py

skips named steps. The refresh workflow skips live because that audit reads
the public site, not the pull request.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")
ROOT = Path(__file__).resolve().parents[1]
WAIT_SECONDS = 300
NOTE_NAME = "discovery-note.txt"
TEST_SCRIPTS = (
    "scripts/test_morning_pipeline.py",
    "scripts/test_refresh_pr_build.py",
    "scripts/test_publish_gate.py",
    "scripts/test_morning_audit.py",
)


@dataclass(frozen=True)
class Step:
    name: str
    transient: bool = False


@dataclass(frozen=True)
class Outcome:
    code: int
    reason: str


def pipeline_steps() -> list[Step]:
    return [
        Step("recheck"),
        Step("predeploy"),
        Step("audit"),
        Step("tests"),
        Step("live", transient=True),
    ]


def discovery_note_path(root: Path | None = None) -> Path:
    override = os.environ.get("DISCOVERY_NOTE", "").strip()
    if override:
        return Path(override)
    base = root or ROOT
    return base / "data" / NOTE_NAME


def failure_report_path(root: Path, when: datetime) -> Path:
    day = when.astimezone(PT).date().isoformat()
    return root / "reports" / f"pipeline-failure-{day}.md"


def command_for(name: str, root: Path | None = None) -> list[list[str]]:
    base = root or ROOT
    py = sys.executable
    if name == "recheck":
        return [[py, str(base / "scripts" / "recheck.py")]]
    if name == "predeploy":
        return [[py, str(base / "daily_deep_audit.py"), "--predeploy"]]
    if name == "audit":
        return [[py, str(base / "daily_deep_audit.py")]]
    if name == "tests":
        return [[py, str(base / rel)] for rel in TEST_SCRIPTS]
    if name == "live":
        return [[py, str(base / "daily_deep_audit.py"), "--live"]]
    raise KeyError(name)


def retry_line(when: datetime | None = None, step: str = "live") -> str:
    moment = (when or datetime.now(PT)).astimezone(PT).replace(microsecond=0)
    stamp = moment.isoformat()
    return f"RETRY {stamp} {step} failed; retrying once after {WAIT_SECONDS}s"


def append_retry(note: Path, step: str = "live", when: datetime | None = None) -> str:
    line = retry_line(when, step)
    note.parent.mkdir(parents=True, exist_ok=True)
    existing = note.read_text(encoding="utf-8") if note.exists() else ""
    prefix = "" if (not existing or existing.endswith("\n")) else "\n"
    note.write_text(existing + prefix + line + "\n", encoding="utf-8")
    return line


def failed_line(step: str, reason: str) -> str:
    text = " ".join((reason or "").split()) or "failed"
    if len(text) > 240:
        text = text[:237] + "..."
    return f"PIPELINE FAILED: {step}: {text}"


def write_failure(path: Path, step: str, reason: str, when: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = when.astimezone(PT).strftime("%Y-%m-%d %H:%M %Z")
    path.write_text(
        f"# Pipeline failed\n\nStep: {step}\nReason: {reason}\nWhen: {stamp}\n",
        encoding="utf-8",
    )


def _last_line(text: str) -> str:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return lines[-1] if lines else ""


def _normalize(value) -> Outcome:
    if isinstance(value, Outcome):
        return value
    if isinstance(value, tuple):
        return Outcome(int(value[0]), str(value[1]))
    code = int(value)
    return Outcome(code, f"exit {code}" if code else "")


def _run_commands(step: Step, root: Path) -> Outcome:
    last_reason = ""
    for argv in command_for(step.name, root):
        result = subprocess.run(argv, cwd=root, capture_output=True, text=True)
        combined = (result.stdout or "") + (result.stderr or "")
        if combined:
            print(combined, end="" if combined.endswith("\n") else "\n", flush=True)
        label = Path(argv[-1]).as_posix()
        last_reason = _last_line(combined) or f"{label} exit {result.returncode}"
        if result.returncode != 0:
            return Outcome(result.returncode or 1, f"{label}: {last_reason}")
    return Outcome(0, last_reason)


def _invoke(step: Step, root: Path, runners: dict | None) -> Outcome:
    try:
        if runners is not None:
            if step.name not in runners:
                raise KeyError(step.name)
            return _normalize(runners[step.name]())
        return _run_commands(step, root)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        return Outcome(code or 1, f"SystemExit: {code}")
    except Exception as exc:
        return Outcome(1, f"{type(exc).__name__}: {exc}")


def run(
    root: Path | None = None,
    *,
    steps: list[Step] | None = None,
    runners: dict | None = None,
    push=None,
    sleep=None,
    note: Path | None = None,
    wait: int = WAIT_SECONDS,
    now=None,
    skip: set[str] | None = None,
) -> int:
    """Run each step. Stop at the first failure. Retry only a transient step, once."""
    root = root or ROOT
    note = note or discovery_note_path(root)
    sleeper = sleep or time.sleep
    clock = now or (lambda: datetime.now(PT))
    skipped = skip or set()
    report = failure_report_path(root, clock())

    for step in steps or pipeline_steps():
        if step.name in skipped:
            print(f"skip {step.name}", flush=True)
            continue
        when = clock()
        outcome = _invoke(step, root, runners)
        if outcome.code != 0 and step.transient:
            print(append_retry(note, step.name, when), flush=True)
            print(
                f"RETRY {step.name} failed ({outcome.code}): {outcome.reason}; waiting {wait}s before one more attempt",
                flush=True,
            )
            sleeper(wait)
            outcome = _invoke(step, root, runners)
        if outcome.code != 0:
            reason = outcome.reason or f"exit {outcome.code}"
            write_failure(report, step.name, reason, clock())
            print(f"wrote {report}", flush=True)
            print(failed_line(step.name, reason), flush=True)
            return outcome.code or 1

    if report.exists():
        report.unlink()
    if push:
        pushed = _normalize(push())
        if pushed.code != 0:
            reason = pushed.reason or f"exit {pushed.code}"
            write_failure(report, "push", reason, clock())
            print(failed_line("push", reason), flush=True)
            return pushed.code or 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        print("morning_pipeline.py does not take arguments", file=sys.stderr)
        return 2
    skip = {part.strip() for part in os.environ.get("PIPELINE_SKIP", "").split(",") if part.strip()}
    return run(skip=skip)


if __name__ == "__main__":
    sys.exit(main())
