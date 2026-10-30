#!/usr/bin/env python3
"""Install the daily generator background. Never draw one with code.

The 7 AM morning routine should call:

    python3 scripts/make_gen_bg.py --site-dir . --date <today> --image <path>

when GenerateImage produced a file, and:

    python3 scripts/make_gen_bg.py --site-dir . --date <today>

otherwise.

Fallback order: --image, then Pollinations.ai (free, no key; unless
--skip-api), then the oldest unused file in data/gen-bg-bank/
(least-recently-used once every file has been used), then keep
assets/gen-art.webp and exit 2. Procedural / PIL art is forbidden.
No paid image APIs.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PROMPT = (
    "16:9 abstract cosmic neural background in AgentScout purple, indigo, and pink tones, "
    "glowing filaments and distant stars, atmospheric, no text, no people, no faces, no letters, no watermark"
)
POLLINATIONS_ATTEMPTS = 2
POLLINATIONS_TIMEOUT = 120
MIN_IMAGE_BYTES = 20 * 1024
TARGET_W, TARGET_H = 1280, 720
# 16:9 is 1.777...; 1024x576 (what Pollinations returns today) matches exactly.
ASPECT_TOLERANCE = 0.08
CSS_RE = re.compile(r"(--gen-art:\s*url\(\s*assets/gen-art\.webp\?v=)[^)]+(\))")
JSON_VER_RE = re.compile(r"gen-art\.webp\?v=[^\"'\s)]+")
ARCHIVE_RE = re.compile(r"^gen-art-(\d{4}-\d{2}-\d{2})\.webp$")
KEEP_ARCHIVE = 7


class UsageError(Exception):
    pass


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except UsageError as exc:
        print(f"make_gen_bg: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Install a real AI generator background. Never draws one.")
    p.add_argument("--site-dir", required=True, help="Site root (the directory that contains assets/ and generate.css)")
    p.add_argument("--date", required=True, help="Day being published, YYYY-MM-DD")
    p.add_argument("--image", help="Image already generated elsewhere (webp, png, or jpeg)")
    p.add_argument("--skip-api", action="store_true", help="Do not call Pollinations; go straight to the bank")
    return p


def run(args) -> int:
    date = _require_date(args.date)
    site = Path(args.site_dir).resolve()
    css_path = site / "generate.css"
    if not css_path.is_file():
        raise UsageError(f"missing {css_path}")
    css_text = css_path.read_text(encoding="utf-8")
    new_css = bump_css(css_text, date)
    live = site / "assets" / "gen-art.webp"

    chosen = None
    if args.image:
        chosen = ("image", load_given_image(Path(args.image)))
    if chosen is None and not args.skip_api:
        generated = generate_via_api(date)
        if generated is not None:
            chosen = ("api", generated)
    bank_name = None
    if chosen is None:
        pick = pick_bank(site / "data" / "gen-bg-bank")
        if pick is not None:
            bank_name, webp = pick
            chosen = ("bank", webp)
    if chosen is None:
        print(
            "warning: no real AI image available (no --image, Pollinations did not "
            "return a usable image, and data/gen-bg-bank/ has nothing to reuse). "
            "Keeping assets/gen-art.webp. Refusing to draw a background with code.",
            file=sys.stderr,
        )
        if not live.is_file():
            print("warning: assets/gen-art.webp is missing; nothing was written.", file=sys.stderr)
        print("source=kept-previous")
        return 2

    source, webp = chosen
    previous = live.read_bytes() if live.is_file() else None
    try:
        archive_previous(site, date, previous)
        live.parent.mkdir(parents=True, exist_ok=True)
        live.write_bytes(webp)
        css_path.write_text(new_css, encoding="utf-8")
        bump_versioned_json(site / "api" / "generator-daily.json", date)
        bump_versioned_json(site / "api" / "sections.json", date)
    except Exception:
        if previous is not None:
            live.write_bytes(previous)
        elif live.is_file() and previous is None:
            live.unlink()
        raise
    if source == "bank" and bank_name:
        record_bank_use(site / "data" / "gen-bg-bank" / "used.json", bank_name, date)
    print(f"source={source}")
    return 0


def _require_date(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise UsageError(f"--date must be YYYY-MM-DD, got {value!r}")
    year, month, day = (int(x) for x in value.split("-"))
    if not (1 <= month <= 12 and 1 <= day <= 31):
        raise UsageError(f"--date is not a calendar day: {value}")
    return value


def bump_css(text: str, date: str) -> str:
    new, n = CSS_RE.subn(rf"\g<1>{date}\2", text, count=1)
    if n != 1:
        raise UsageError("generate.css has no --gen-art:url(assets/gen-art.webp?v=...) to bump")
    return new


def bump_versioned_json(path: Path, date: str) -> None:
    """Keep generate.js and the app manifest on the same cache key as generate.css."""
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    new = JSON_VER_RE.sub(f"gen-art.webp?v={date}", text)
    if new != text:
        path.write_text(new, encoding="utf-8")


def load_given_image(path: Path) -> bytes:
    if not path.is_file():
        raise UsageError(f"--image not found: {path}")
    try:
        return as_webp(path.read_bytes())
    except Exception as exc:
        raise UsageError(f"--image is not a usable image ({exc})") from None


def as_webp(data: bytes) -> bytes:
    if _is_webp(data):
        return data
    if not _is_raster(data):
        raise RuntimeError("not a png, jpeg, or webp image")
    return transcode_to_webp(data)


def _is_webp(data: bytes) -> bool:
    return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"


def _is_raster(data: bytes) -> bool:
    return data.startswith(b"\x89PNG\r\n\x1a\n") or data.startswith(b"\xff\xd8\xff")


def transcode_to_webp(data: bytes) -> bytes:
    """Resize to the site background size and encode WebP. This scales pixels; it does not draw art."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is not available to convert the image to webp")
    if _is_webp(data):
        suffix = ".webp"
    elif data.startswith(b"\x89PNG"):
        suffix = ".png"
    else:
        suffix = ".jpg"
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"in{suffix}"
        dst = Path(tmp) / "out.webp"
        src.write_bytes(data)
        proc = subprocess.run(
            [
                ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(src),
                "-vf", f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=increase,crop={TARGET_W}:{TARGET_H}",
                "-frames:v", "1", "-c:v", "libwebp", "-quality", "82",
                str(dst),
            ],
            capture_output=True,
        )
        if proc.returncode != 0 or not dst.is_file():
            err = proc.stderr.decode("utf-8", "replace").strip().splitlines()
            detail = err[-1][:200] if err else "ffmpeg failed"
            raise RuntimeError(detail)
        out = dst.read_bytes()
    if not _is_webp(out):
        raise RuntimeError("converter did not produce webp")
    return out


def archive_previous(site: Path, date: str, previous: bytes | None) -> None:
    dest_dir = site / "assets" / "gen-bg-archive"
    dest_dir.mkdir(parents=True, exist_ok=True)
    written = None
    if previous:
        written = dest_dir / f"gen-art-{date}.webp"
        written.write_bytes(previous)
    dated = []
    for path in dest_dir.glob("gen-art-*.webp"):
        match = ARCHIVE_RE.match(path.name)
        if match:
            dated.append((match.group(1), path))
    dated.sort()
    extra = len(dated) - KEEP_ARCHIVE
    for _, path in dated:
        if extra <= 0:
            break
        if written is not None and path.resolve() == written.resolve():
            continue
        path.unlink()
        extra -= 1


def pick_bank(bank_dir: Path) -> tuple[str, bytes] | None:
    if not bank_dir.is_dir():
        return None
    files = [p for p in bank_dir.glob("bank-*.webp") if p.is_file() and p.stat().st_size > 0 and _is_webp(p.read_bytes())]
    if not files:
        return None
    used = load_used(bank_dir / "used.json")
    unused = [p for p in files if not (used.get(p.name) or {}).get("last_used")]
    if unused:
        # `added` is tracked in used.json so a git checkout (which rewrites mtimes)
        # still serves the bank in the order the images were created.
        def unused_key(p: Path):
            added = str((used.get(p.name) or {}).get("added") or "")
            if added:
                return (0, added, p.name)
            return (1, f"{p.stat().st_mtime:020.3f}", p.name)
        unused.sort(key=unused_key)
        choice = unused[0]
    else:
        def key(p: Path):
            entry = used.get(p.name) or {}
            return (str(entry.get("last_used") or ""), int(entry.get("uses") or 0), p.name)
        choice = min(files, key=key)
    return choice.name, choice.read_bytes()


def load_used(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"make_gen_bg: warning: ignoring unreadable {path} ({exc})", file=sys.stderr)
        return {}
    entries = raw.get("entries") if isinstance(raw, dict) else None
    if not isinstance(entries, dict):
        print(f"make_gen_bg: warning: ignoring {path} (expected an entries object)", file=sys.stderr)
        return {}
    return entries


def record_bank_use(path: Path, name: str, date: str) -> None:
    raw = {"entries": {}}
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("entries"), dict):
                raw = loaded
            else:
                raw = {"entries": {}}
        except (OSError, json.JSONDecodeError):
            raw = {"entries": {}}
    entries = raw.setdefault("entries", {})
    prev = entries.get(name) if isinstance(entries.get(name), dict) else {}
    updated = {"last_used": date, "uses": int(prev.get("uses") or 0) + 1}
    if prev.get("added"):
        updated["added"] = prev["added"]
    entries[name] = updated
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def pollinations_url(date: str) -> str:
    """Free Pollinations FLUX URL. The seed is the date, so a re-run of the same day matches and the next day does not."""
    prompt = urllib.parse.quote(PROMPT, safe="")
    seed = int(date.replace("-", ""))
    return (
        f"https://image.pollinations.ai/prompt/{prompt}"
        f"?width=1920&height=1080&nologo=true&model=flux&seed={seed}"
    )


def generate_via_api(date: str):
    """Return WebP bytes from Pollinations, or None after one retry. Never calls a paid API."""
    url = pollinations_url(date)
    for attempt in range(1, POLLINATIONS_ATTEMPTS + 1):
        try:
            body, ctype = _http_get(url, POLLINATIONS_TIMEOUT)
            _validate_generated(body, ctype)
            return transcode_to_webp(body)
        except Exception as exc:
            detail = str(exc).splitlines()[0][:200]
            again = "retrying" if attempt < POLLINATIONS_ATTEMPTS else "skipping"
            print(f"make_gen_bg: warning: Pollinations attempt {attempt} failed ({detail}); {again}", file=sys.stderr)
    return None


def _validate_generated(body: bytes, content_type: str) -> None:
    ctype = (content_type or "").split(";", 1)[0].strip().lower()
    if not ctype.startswith("image/"):
        raise RuntimeError(f"content-type is {content_type or 'missing'}")
    if len(body) < MIN_IMAGE_BYTES:
        raise RuntimeError(f"image is {len(body)} bytes, under 20 KB")
    width, height = decode_size(body)
    if height <= 0 or abs((width / height) - (16 / 9)) > ASPECT_TOLERANCE:
        raise RuntimeError(f"aspect {width}x{height} is not about 16:9")


def decode_size(data: bytes) -> tuple[int, int]:
    """Decode the image far enough to read its pixel size. Raises if it is not a real image."""
    ffprobe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")
    if not ffprobe or not ffmpeg:
        raise RuntimeError("ffmpeg is not available to decode the image")
    if _is_webp(data):
        suffix = ".webp"
    elif data.startswith(b"\x89PNG"):
        suffix = ".png"
    elif data.startswith(b"\xff\xd8\xff"):
        suffix = ".jpg"
    else:
        suffix = ".img"
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"in{suffix}"
        src.write_bytes(data)
        probe = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(src)],
            capture_output=True, text=True,
        )
        decoded = subprocess.run([ffmpeg, "-v", "error", "-i", str(src), "-f", "null", "-"], capture_output=True)
    if probe.returncode != 0 or decoded.returncode != 0:
        raise RuntimeError("image did not decode")
    parts = (probe.stdout or "").strip().split(",")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise RuntimeError("image did not decode")
    return int(parts[0]), int(parts[1])


def _http_get(url: str, timeout: int) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"Accept": "image/*", "User-Agent": "AgentScout-gen-bg"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(20_000_001)
            if len(body) > 20_000_000:
                raise RuntimeError("image response too large")
            return body, resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        detail = exc.read(240).decode("utf-8", "replace").replace("\n", " ")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:180]}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise RuntimeError(f"request failed: {reason}") from None


if __name__ == "__main__":
    sys.exit(main())
