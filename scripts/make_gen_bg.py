#!/usr/bin/env python3
"""Install the daily generator background. Never draw one with code.

The 7 AM morning routine should call:

    python3 scripts/make_gen_bg.py --site-dir . --date <today> --image <path>

when GenerateImage produced a file, and:

    python3 scripts/make_gen_bg.py --site-dir . --date <today>

otherwise.

Fallback order: --image, then a live image API (unless --skip-api; skipped
cleanly when no key is configured), then the oldest unused file in
data/gen-bg-bank/ (least-recently-used once every file has been used), then
keep assets/gen-art.webp and exit 2. Procedural / PIL art is forbidden.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

# Published Imagine list price for grok-imagine-image-2.0 (flat per image).
XAI_IMAGE_COST = "$0.04"
PROMPT = (
    "Abstract 16:9 cosmic neural landscape, deep indigo and violet with magenta "
    "and soft pink light, glowing filaments and distant stars, atmospheric, "
    "no text, no letters, no watermark, no logo, no people, no faces, no figures"
)
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
    p.add_argument("--skip-api", action="store_true", help="Do not call a live image API; go straight to the bank")
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
        chosen = ("image", load_given_image(Path(args.image)), "0")
    if chosen is None and not args.skip_api:
        generated = generate_via_api()
        if generated is not None:
            webp, cost = generated
            chosen = ("api", webp, cost)
    bank_name = None
    if chosen is None:
        pick = pick_bank(site / "data" / "gen-bg-bank")
        if pick is not None:
            bank_name, webp = pick
            chosen = ("bank", webp, "0")
    if chosen is None:
        print(
            "warning: no real AI image available (no --image, no image API, and "
            "data/gen-bg-bank/ has nothing to reuse). Keeping assets/gen-art.webp. "
            "Refusing to draw a background with code.",
            file=sys.stderr,
        )
        if not live.is_file():
            print("warning: assets/gen-art.webp is missing; nothing was written.", file=sys.stderr)
        print("source=kept-previous cost=0")
        return 2

    source, webp, cost = chosen
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
    print(f"source={source} cost={cost}")
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
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is not available to convert the image to webp")
    suffix = ".png" if data.startswith(b"\x89PNG") else ".jpg"
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"in{suffix}"
        dst = Path(tmp) / "out.webp"
        src.write_bytes(data)
        proc = subprocess.run(
            [
                ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(src),
                "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
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


def generate_via_api(env=None):
    """Return (webp_bytes, cost) or None when no API is configured or every call fails."""
    env = os.environ if env is None else env
    providers = list_providers(env)
    if not providers:
        return None
    for name, fn in providers:
        try:
            data, cost = fn()
            return as_webp(data), cost
        except Exception as exc:
            detail = str(exc).splitlines()[0][:200]
            print(f"make_gen_bg: warning: {name} image API failed ({detail}); skipping", file=sys.stderr)
    return None


def list_providers(env: dict):
    found = []
    custom = _env(env, "GEN_BG_API_URL")
    custom_key = _env(env, "GEN_BG_API_KEY", "XAI_API_KEY", "OPENAI_API_KEY")
    if custom and custom_key:
        found.append(("custom", lambda: _openai_images(custom, custom_key, env, custom=True)))
    xai = _env(env, "XAI_API_KEY")
    if xai:
        found.append(("xai", lambda: _openai_images("https://api.x.ai/v1/images/generations", xai, env, xai=True)))
    openai = _env(env, "OPENAI_API_KEY")
    if openai:
        found.append(("openai", lambda: _openai_images("https://api.openai.com/v1/images/generations", openai, env)))
    fal = _env(env, "FAL_KEY", "FAL_API_KEY")
    if fal:
        found.append(("fal", lambda: _fal(fal)))
    bfl = _env(env, "BFL_API_KEY")
    if bfl:
        found.append(("bfl", lambda: _bfl(bfl)))
    together = _env(env, "TOGETHER_API_KEY")
    if together:
        found.append(("together", lambda: _together(together)))
    stability = _env(env, "STABILITY_API_KEY")
    if stability:
        found.append(("stability", lambda: _stability(stability)))
    return found


def provider_names(env: dict) -> list[str]:
    return [name for name, _ in list_providers(env)]


def _env(env: dict, *names: str) -> str:
    for name in names:
        value = str(env.get(name) or "").strip()
        if value:
            return value
    return ""


def _openai_images(url: str, key: str, env: dict, xai: bool = False, custom: bool = False):
    if xai or (custom and "x.ai" in url):
        body = {
            "model": env.get("XAI_IMAGE_MODEL") or env.get("GEN_BG_API_MODEL") or "grok-imagine-image-2.0",
            "prompt": PROMPT,
            "n": 1,
            "aspect_ratio": "16:9",
            "resolution": "1k",
            "quality": "low",
            "response_format": "b64_json",
        }
        cost = XAI_IMAGE_COST
    else:
        body = {
            "model": env.get("OPENAI_IMAGE_MODEL") or env.get("GEN_BG_API_MODEL") or "gpt-image-1",
            "prompt": PROMPT,
            "n": 1,
            "size": env.get("OPENAI_IMAGE_SIZE") or "1536x1024",
            "response_format": "b64_json",
        }
        cost = "unknown"
    _raw, parsed = _post_json(url, body, {"Authorization": f"Bearer {key}"})
    return _image_bytes(parsed), _reported_cost(parsed, cost)


def _fal(key: str):
    _raw, parsed = _post_json(
        "https://fal.run/fal-ai/flux/schnell",
        {
            "prompt": PROMPT,
            "image_size": "landscape_16_9",
            "num_images": 1,
            "output_format": "jpeg",
            "enable_safety_checker": True,
        },
        {"Authorization": f"Key {key}"},
    )
    return _image_bytes(parsed), _reported_cost(parsed, "unknown")


def _together(key: str):
    _raw, parsed = _post_json(
        "https://api.together.xyz/v1/images/generations",
        {
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": PROMPT,
            "width": 1280,
            "height": 720,
            "n": 1,
            "response_format": "b64_json",
            "steps": 4,
        },
        {"Authorization": f"Bearer {key}"},
    )
    return _image_bytes(parsed), _reported_cost(parsed, "unknown")


def _bfl(key: str):
    _, created = _post_json(
        "https://api.bfl.ai/v1/flux-pro-1.1",
        {"prompt": PROMPT, "width": 1024, "height": 576},
        {"x-key": key},
    )
    request_id = created.get("id")
    if not request_id:
        raise RuntimeError("BFL response had no id")
    sample = None
    for _ in range(20):
        time.sleep(1)
        _, polled = _get_json(f"https://api.bfl.ai/v1/get_result?id={request_id}", {"x-key": key})
        status = str(polled.get("status") or "")
        if status == "Ready":
            sample = (polled.get("result") or {}).get("sample")
            break
        if status in {"Error", "Request Moderated", "Content Moderated", "Task not found"}:
            raise RuntimeError(f"BFL status {status}")
    if not sample:
        raise RuntimeError("BFL result was not ready")
    return _download(sample), "unknown"


def _stability(key: str):
    boundary = "----AgentScoutGenBg" + uuid.uuid4().hex
    chunks = []
    for name, value in (("prompt", PROMPT), ("aspect_ratio", "16:9"), ("output_format", "webp")):
        chunks.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
        )
    chunks.append(f"--{boundary}--\r\n".encode())
    status, body, ctype = _request(
        "https://api.stability.ai/v2beta/stable-image/generate/core",
        data=b"".join(chunks),
        headers={
            "Authorization": f"Bearer {key}",
            "Accept": "image/*",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    if not ctype.startswith("image/"):
        raise RuntimeError(f"Stability returned {ctype or 'no content type'} ({status})")
    return body, "unknown"


def _post_json(url: str, body: dict, headers: dict):
    data = json.dumps(body).encode()
    hdrs = {"Content-Type": "application/json", "Accept": "application/json", **headers}
    status, raw, _ctype = _request(url, data=data, headers=hdrs)
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"HTTP {status} was not JSON") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("image API returned a non-object")
    return raw, parsed


def _get_json(url: str, headers: dict):
    status, raw, _ctype = _request(url, headers={"Accept": "application/json", **headers})
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"HTTP {status} was not JSON") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("image API returned a non-object")
    return raw, parsed


def _request(url: str, data=None, headers=None, timeout=120):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(20_000_001)
            if len(body) > 20_000_000:
                raise RuntimeError("image response too large")
            return resp.status, body, resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        detail = exc.read(240).decode("utf-8", "replace").replace("\n", " ")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:180]}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"request failed: {exc.reason}") from None


def _image_bytes(payload: dict) -> bytes:
    items = payload.get("data") or payload.get("images") or []
    if not isinstance(items, list) or not items:
        if payload.get("b64_json") or payload.get("url"):
            items = [payload]
        else:
            raise RuntimeError("image API returned no image")
    item = items[0] if isinstance(items[0], dict) else {}
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    url = item.get("url") or ""
    if isinstance(url, str) and url.startswith("data:"):
        return base64.b64decode(url.split(",", 1)[1])
    if url:
        return _download(url)
    raise RuntimeError("image API item had no url or b64_json")


def _download(url: str) -> bytes:
    if not isinstance(url, str) or not url.startswith("https://"):
        raise RuntimeError("refusing a non-https image url")
    _status, body, _ctype = _request(url, timeout=60)
    if not (_is_webp(body) or _is_raster(body)):
        raise RuntimeError("downloaded file is not an image")
    return body


def _reported_cost(payload: dict, fallback: str) -> str:
    for key in ("cost", "price"):
        if payload.get(key) not in (None, ""):
            return str(payload[key])
    usage = payload.get("usage")
    if isinstance(usage, dict) and usage.get("cost") not in (None, ""):
        return str(usage["cost"])
    return fallback


if __name__ == "__main__":
    sys.exit(main())
