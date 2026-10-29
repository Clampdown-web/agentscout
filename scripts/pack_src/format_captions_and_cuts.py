#!/usr/bin/env python3
"""Turn a transcript into SRT, VTT, and an ffmpeg cut list for {{YOUR_COMPANY}}.

Flags a weak opening three seconds and lists silence gaps an editor can drop.
It prints an ffmpeg filter graph; it does not render video.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAMPLE = {
    "title": "How we book a visit",
    "cues": [
        {"start": 0.0, "end": 1.2, "text": "um"},
        {"start": 1.4, "end": 3.5, "text": "Wait, your quote sat for six days?"},
        {"start": 3.6, "end": 6.2, "text": "Here is the one-afternoon booking."},
        {"start": 8.4, "end": 11.0, "text": "Tap the link and pick a slot."},
    ],
}

HOOKS = ("wait", "stop", "how", "why", "?", "mistake", "secret", "before", "don't", "dont")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--self-test", action="store_true", help="Run built-in self-test sample and exit 0")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Transcript JSON with cues")
    p.add_argument("--output", help="JSON report path")
    p.add_argument("--gap", type=float, default=0.7, help="Silence gap that becomes a cut")
    return p


def stamp(seconds: float, sep: str) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def analyze(doc: dict, gap: float) -> dict:
    cues = doc["cues"]
    srt, vtt = [], ["WEBVTT", ""]
    cuts = []
    previous_end = 0.0
    for i, cue in enumerate(cues, start=1):
        if cue["start"] - previous_end >= gap:
            cuts.append({
                "from": round(previous_end, 3),
                "to": round(cue["start"], 3),
                "reason": "silence or dead air",
            })
        text = " ".join(cue["text"].split())
        srt.append(f"{i}\n{stamp(cue['start'], ',')} --> {stamp(cue['end'], ',')}\n{text}\n")
        vtt.append(f"{stamp(cue['start'], '.')} --> {stamp(cue['end'], '.')}\n{text}\n")
        previous_end = cue["end"]
    opening = " ".join(c["text"] for c in cues if c["start"] < 3).lower()
    hook = any(token in opening for token in HOOKS) and opening.strip() not in {"um", "uh", ""}
    select = "+".join(
        f"between(t,{c['from']},{c['to']})" for c in cuts
    ) or "0"
    return {
        "company": "{{YOUR_COMPANY}}",
        "title": doc.get("title", "short"),
        "hook_in_first_3_seconds": hook,
        "opening_text": opening,
        "srt": "\n".join(srt),
        "vtt": "\n".join(vtt),
        "cut_list": cuts,
        "ffmpeg_hint": f"ffmpeg -i input.mp4 -vf \"select='not({select})',setpts=N/FRAME_RATE/TB\" -af \"aselect='not({select})',asetpts=N/SR/TB\" output.mp4",
        "storyboard": [
            "0.0-3.0s: pattern interrupt, no logo card",
            "3.0-8.0s: show the result on screen",
            "last 2s: one spoken next step and a burned-in caption",
        ],
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or getattr(args, 'self_test', False) or not args.input
    doc = SAMPLE if dry else json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = analyze(doc, args.gap)
    report["dry_run"] = dry
    payload = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
