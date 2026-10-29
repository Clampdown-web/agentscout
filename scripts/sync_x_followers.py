#!/usr/bin/env python3
"""Record today's X follower counts on the 30-day sprint tracker.

Each new daily_log row is built only from counts fetched in this run.
The previous row is never used as a template. If either account cannot be
fetched, the script exits with an error and leaves the tracker unchanged.

A new row whose counts happen to equal the previous day prints a warning.
That warning is not a copy: the numbers still came from this run's fetch.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "data" / "30-day-sprint-tracker.json"
PT = ZoneInfo("America/Los_Angeles")
ACCOUNTS = (
    ("clampdown19", "clampdown19_followers"),
    ("AgentScoutHQ", "agentscouthq_followers"),
)
COUNT_FIELDS = ("clampdown19_followers", "agentscouthq_followers", "combined_followers")
_FOLLOWERS = re.compile(r"\[([0-9][0-9,]*) Followers\]")
_JSON_COUNT = re.compile(r'"followers_count"\s*:\s*(\d+)')


class FetchError(Exception):
    """A live follower count was not available for this run."""


def fetch_account(username: str, opener=urllib.request.urlopen) -> int:
    """Read one public follower count. Raises FetchError instead of guessing."""
    url = f"https://r.jina.ai/https://x.com/{username}"
    req = urllib.request.Request(url, headers={"User-Agent": "AgentScout-follower-sync/1.0"})
    try:
        with opener(req, timeout=25) as resp:
            body = resp.read().decode("utf-8", "replace")
    except Exception as exc:
        raise FetchError(f"{username}: {exc}") from exc
    match = _FOLLOWERS.search(body) or _JSON_COUNT.search(body)
    if not match:
        raise FetchError(f"{username}: live follower count was not in the response")
    return int(match.group(1).replace(",", ""))


def fetch_followers(opener=urllib.request.urlopen) -> dict:
    """Fetch both accounts. A partial result is a failure, not a fallback."""
    fetched = {}
    errors = []
    for username, field in ACCOUNTS:
        try:
            fetched[field] = fetch_account(username, opener)
        except FetchError as exc:
            errors.append(str(exc))
    if errors:
        raise FetchError("; ".join(errors))
    return fetched


def build_row(day: str, fetched: dict, fetched_at: str) -> dict:
    """Build one tracker row from this run's fetch. Does not take a previous row."""
    missing = [field for _, field in ACCOUNTS if fetched.get(field) is None]
    if missing:
        raise FetchError("missing live counts for " + ", ".join(missing))
    try:
        clamp = int(fetched["clampdown19_followers"])
        hq = int(fetched["agentscouthq_followers"])
    except (TypeError, ValueError) as exc:
        raise FetchError(f"follower counts are not integers ({exc})") from exc
    if clamp < 0 or hq < 0:
        raise FetchError("follower counts cannot be negative")
    return {
        "date": day,
        "clampdown19_followers": clamp,
        "agentscouthq_followers": hq,
        "combined_followers": clamp + hq,
        "source": "live_fetch",
        "fetched_at": fetched_at,
    }


def follower_signature(row: dict) -> tuple:
    return tuple(row.get(field) for field in COUNT_FIELDS)


def previous_row(log: list, day: str) -> dict | None:
    """The latest row for a different date. Used only to compare, never to copy."""
    for row in reversed(log):
        if row.get("date") != day:
            return row
    return None


def warn_if_unchanged(new_row: dict, previous: dict | None, err=sys.stderr) -> bool:
    if previous and follower_signature(new_row) == follower_signature(previous):
        print(
            "WARNING: "
            f"{new_row.get('date')} follower counts match {previous.get('date')} "
            f"({new_row.get('clampdown19_followers')} + {new_row.get('agentscouthq_followers')} "
            f"= {new_row.get('combined_followers')}). "
            "These numbers were fetched in this run and were not copied from the previous row.",
            file=err,
        )
        return True
    return False


def apply_fetch(tracker: dict, day: str, fetched: dict, fetched_at: str, err=sys.stderr) -> dict:
    """Return a new tracker. Follower fields come only from `fetched`."""
    row = build_row(day, fetched, fetched_at)
    log = [dict(item) for item in (tracker.get("daily_log") or [])]
    warn_if_unchanged(row, previous_row(log, day), err)
    log = [item for item in log if item.get("date") != day]
    log.append(row)
    log.sort(key=lambda item: item.get("date") or "")
    current = dict(tracker.get("current") or {})
    for field in (*COUNT_FIELDS, "as_of", "source"):
        current.pop(field, None)
    current.update(
        {
            "clampdown19_followers": row["clampdown19_followers"],
            "agentscouthq_followers": row["agentscouthq_followers"],
            "combined_followers": row["combined_followers"],
            "as_of": day,
            "source": "live_fetch",
        }
    )
    updated = dict(tracker)
    updated["daily_log"] = log
    updated["current"] = current
    return updated


def audit_tracker(tracker: dict) -> list[str]:
    """Fail rows that were not fetched on their own date, including copied templates.

    Equal counts on two days are allowed when the later row's fetched_at is that
    day's timestamp. A copied row keeps the previous day's fetched_at, or has none.
    """
    bad = []
    log = tracker.get("daily_log") or []
    if not log:
        bad.append("30-day sprint tracker daily_log is empty")
        return bad
    for row in log:
        day = str(row.get("date") or "")
        if row.get("source") != "live_fetch":
            bad.append(f"{day or 'row'} was not marked live_fetch")
        if row.get("clampdown19_followers") is None or row.get("agentscouthq_followers") is None:
            bad.append(f"{day or 'row'} is missing a live follower count")
            continue
        expected = int(row["clampdown19_followers"]) + int(row["agentscouthq_followers"])
        if row.get("combined_followers") != expected:
            bad.append(f"{day} combined_followers is not the sum of the two accounts")
        fetched_at = str(row.get("fetched_at") or "")
        if not day or not fetched_at.startswith(day):
            bad.append(f"{day or 'row'} fetched_at {fetched_at or 'missing'} is not from that day")
    return bad


def load_tracker(path: Path = TRACKER) -> dict:
    if not path.is_file():
        return {"daily_log": [], "current": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None, fetch=fetch_followers) -> int:
    del argv
    try:
        fetched = fetch()
        if not isinstance(fetched, dict):
            raise FetchError("fetch did not return counts")
    except FetchError as exc:
        print(
            f"ERROR: follower fetch failed ({exc}). Refusing to copy the previous day's row.",
            file=sys.stderr,
        )
        return 1
    now = datetime.now(PT)
    day = now.date().isoformat()
    fetched_at = now.strftime("%Y-%m-%dT%H:%M:%S%z")
    try:
        updated = apply_fetch(load_tracker(), day, fetched, fetched_at)
    except FetchError as exc:
        print(
            f"ERROR: {exc}. Refusing to copy the previous day's row.",
            file=sys.stderr,
        )
        return 1
    problems = audit_tracker(updated)
    if problems:
        for line in problems:
            print("ERROR:", line, file=sys.stderr)
        print("ERROR: not writing the sprint tracker.", file=sys.stderr)
        return 1
    TRACKER.parent.mkdir(parents=True, exist_ok=True)
    TRACKER.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
    row = updated["daily_log"][-1]
    print(
        f"wrote {TRACKER.relative_to(ROOT)} {row['date']}: "
        f"{row['clampdown19_followers']} + {row['agentscouthq_followers']} "
        f"= {row['combined_followers']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
