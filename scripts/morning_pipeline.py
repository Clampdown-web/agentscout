#!/usr/bin/env python3
"""Morning pipeline gate around scripts/recheck.py.

The box copy of this step used to keep going when recheck failed: it did not
wait, it did not write a RETRY line, and it still pushed. This module is the
source that copy should run.

On failure it appends one RETRY line to the discovery note, waits 300 seconds,
and runs recheck once more. If that attempt also fails, it returns before push.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WAIT_SECONDS = 300
NOTE_NAME = "discovery-note.txt"


def discovery_note_path(root: Path | None = None) -> Path:
    override = os.environ.get("DISCOVERY_NOTE", "").strip()
    if override:
        return Path(override)
    base = root or ROOT
    return base / "data" / NOTE_NAME


def recheck_command(root: Path | None = None) -> list[str]:
    base = root or ROOT
    return [sys.executable, str(base / "scripts" / "recheck.py")]


def retry_line(when: datetime | None = None) -> str:
    stamp = (when or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"RETRY {stamp} recheck failed; retrying once after {WAIT_SECONDS}s"


def append_retry(note: Path, when: datetime | None = None) -> str:
    line = retry_line(when)
    note.parent.mkdir(parents=True, exist_ok=True)
    existing = note.read_text(encoding="utf-8") if note.exists() else ""
    prefix = "" if (not existing or existing.endswith("\n")) else "\n"
    note.write_text(existing + prefix + line + "\n", encoding="utf-8")
    return line


def run(
    root: Path | None = None,
    *,
    recheck=None,
    push=None,
    sleep=None,
    note: Path | None = None,
    wait: int = WAIT_SECONDS,
) -> int:
    """Run recheck, retry once, and push only when a pass happens.

    recheck() and push() return a process exit code. sleep(seconds) waits.
    The defaults shell out to scripts/recheck.py, do not push (the caller
    passes the push), and sleep for real.
    """
    root = root or ROOT
    note = note or discovery_note_path(root)
    sleeper = sleep or time.sleep

    def default_recheck() -> int:
        result = subprocess.run(recheck_command(root), cwd=root)
        return result.returncode

    check = recheck or default_recheck
    first = check()
    if first == 0:
        if push:
            return push()
        return 0
    append_retry(note)
    print(f"RETRY recheck failed ({first}); waiting {wait}s before one more attempt", flush=True)
    sleeper(wait)
    second = check()
    if second != 0:
        print(f"RETRY recheck failed again ({second}); not pushing", flush=True)
        return second
    if push:
        return push()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        print("morning_pipeline.py does not take arguments; it runs scripts/recheck.py", file=sys.stderr)
        return 2
    return run()


if __name__ == "__main__":
    sys.exit(main())
