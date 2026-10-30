#!/usr/bin/env python3
"""Fallback order for the daily generator background. Code never draws the art."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_gen_bg as bg

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "assets" / "gen-bg-archive" / "gen-art-2026-10-26.webp"
CSS = ":root{--gen-art:url(assets/gen-art.webp?v=20261030)}\n"


def site_with(root: Path, live: bytes, bank: dict[str, bytes] | None = None, archives: int = 0) -> Path:
    (root / "assets").mkdir(parents=True)
    (root / "assets" / "gen-art.webp").write_bytes(live)
    (root / "generate.css").write_text(CSS, encoding="utf-8")
    daily = {
        "image": "https://agentscouthq.com/assets/gen-art.webp?v=20261030",
        "path": "assets/gen-art.webp?v=20261030",
    }
    (root / "api").mkdir()
    (root / "api" / "generator-daily.json").write_text(json.dumps(daily, indent=1) + "\n", encoding="utf-8")
    if bank:
        bdir = root / "data" / "gen-bg-bank"
        bdir.mkdir(parents=True)
        for name, data in bank.items():
            (bdir / name).write_bytes(data)
        (bdir / "used.json").write_text('{"entries": {}}\n', encoding="utf-8")
    if archives:
        adir = root / "assets" / "gen-bg-archive"
        adir.mkdir()
        for i in range(1, archives + 1):
            (adir / f"gen-art-2026-09-{i:02d}.webp").write_bytes(b"RIFFOLD" + bytes([i]))
    return root


class MakeGenBgTest(unittest.TestCase):
    def test_source_never_draws_with_code(self):
        text = (Path(bg.__file__)).read_text(encoding="utf-8")
        for banned in ("import PIL", "from PIL", "ImageDraw", "ImageFont", "Image.new", "import cairo", "import wand", "import cv2", "import skimage"):
            self.assertNotIn(banned, text)

    def test_no_paid_image_apis(self):
        text = Path(bg.__file__).read_text(encoding="utf-8")
        for banned in (
            "XAI_API_KEY", "OPENAI_API_KEY", "FAL_KEY", "FAL_API_KEY", "BFL_API_KEY",
            "TOGETHER_API_KEY", "STABILITY_API_KEY", "GEN_BG_API_URL", "api.x.ai",
            "api.openai.com", "fal.run", "api.bfl.ai", "api.together.xyz", "stability.ai",
            "$0.04", "cost=",
        ):
            self.assertNotIn(banned, text)

    def test_pollinations_url_changes_with_the_date(self):
        first = bg.pollinations_url("2026-11-01")
        second = bg.pollinations_url("2026-11-02")
        self.assertTrue(first.startswith("https://image.pollinations.ai/prompt/"))
        self.assertIn("width=1920&height=1080&nologo=true&model=flux&seed=20261101", first)
        self.assertIn(urllib.parse.quote("no people", safe=""), first)
        self.assertIn("AgentScout", first)
        self.assertIn("seed=20261102", second)
        self.assertNotEqual(first, second)

    def test_image_flag_installs_that_file_and_bumps_version(self):
        sample = SAMPLE.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            root = site_with(Path(tmp), b"RIFFOLDWEBP", archives=8)
            previous = (root / "assets" / "gen-art.webp").read_bytes()
            def boom(*_a, **_k):
                raise AssertionError("Pollinations should not run when --image is set")

            original = bg._http_get
            bg._http_get = boom
            try:
                code = bg.main(["--site-dir", str(root), "--date", "2026-11-01", "--image", str(SAMPLE)])
            finally:
                bg._http_get = original
            self.assertEqual(code, 0)
            self.assertEqual((root / "assets" / "gen-art.webp").read_bytes(), sample)
            self.assertIn("?v=2026-11-01", (root / "generate.css").read_text(encoding="utf-8"))
            daily = json.loads((root / "api" / "generator-daily.json").read_text(encoding="utf-8"))
            self.assertEqual(daily["path"], "assets/gen-art.webp?v=2026-11-01")
            archived = root / "assets" / "gen-bg-archive" / "gen-art-2026-11-01.webp"
            self.assertEqual(archived.read_bytes(), previous)
            names = sorted(p.name for p in (root / "assets" / "gen-bg-archive").glob("gen-art-*.webp"))
            self.assertEqual(len(names), 7)
            self.assertNotIn("gen-art-2026-09-01.webp", names)
            self.assertNotIn("gen-art-2026-09-02.webp", names)
            self.assertIn("gen-art-2026-11-01.webp", names)

    def test_skip_api_uses_oldest_unused_then_least_recently_used(self):
        sample = SAMPLE.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            root = site_with(Path(tmp), sample, bank={"bank-02.webp": sample, "bank-01.webp": sample})
            older = root / "data" / "gen-bg-bank" / "bank-02.webp"
            newer = root / "data" / "gen-bg-bank" / "bank-01.webp"
            os.utime(older, (1_700_000_000, 1_700_000_000))
            os.utime(newer, (1_800_000_000, 1_800_000_000))
            args = ["--site-dir", str(root), "--skip-api"]
            self.assertEqual(bg.main(args + ["--date", "2026-11-01"]), 0)
            used = json.loads((root / "data" / "gen-bg-bank" / "used.json").read_text(encoding="utf-8"))
            self.assertEqual(used["entries"]["bank-02.webp"]["last_used"], "2026-11-01")
            self.assertNotIn("bank-01.webp", used["entries"])
            self.assertEqual(bg.main(args + ["--date", "2026-11-02"]), 0)
            used = json.loads((root / "data" / "gen-bg-bank" / "used.json").read_text(encoding="utf-8"))
            self.assertEqual(used["entries"]["bank-01.webp"]["last_used"], "2026-11-02")
            self.assertEqual(bg.main(args + ["--date", "2026-11-03"]), 0)
            used = json.loads((root / "data" / "gen-bg-bank" / "used.json").read_text(encoding="utf-8"))
            self.assertEqual(used["entries"]["bank-02.webp"]["uses"], 2)
            self.assertEqual(used["entries"]["bank-02.webp"]["last_used"], "2026-11-03")

    def test_added_date_orders_the_bank_and_survives_use(self):
        sample = SAMPLE.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            root = site_with(Path(tmp), sample, bank={"bank-01.webp": sample, "bank-09.webp": sample})
            used_path = root / "data" / "gen-bg-bank" / "used.json"
            used_path.write_text(json.dumps({
                "entries": {
                    "bank-01.webp": {"added": "2026-10-25"},
                    "bank-09.webp": {"added": "2026-10-16"},
                }
            }) + "\n", encoding="utf-8")
            # bank-01 has the older mtime, but bank-09 was added earlier.
            os.utime(root / "data" / "gen-bg-bank" / "bank-01.webp", (1_000, 1_000))
            os.utime(root / "data" / "gen-bg-bank" / "bank-09.webp", (2_000, 2_000))
            self.assertEqual(bg.main(["--site-dir", str(root), "--date", "2026-11-01", "--skip-api"]), 0)
            used = json.loads(used_path.read_text(encoding="utf-8"))
            self.assertEqual(used["entries"]["bank-09.webp"]["last_used"], "2026-11-01")
            self.assertEqual(used["entries"]["bank-09.webp"]["added"], "2026-10-16")
            self.assertNotIn("last_used", used["entries"]["bank-01.webp"])

    def test_skip_api_does_not_call_the_network_helper(self):
        sample = SAMPLE.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            root = site_with(Path(tmp), sample, bank={"bank-01.webp": sample})

            def boom(*_a, **_k):
                raise AssertionError("Pollinations should not run with --skip-api")

            original = bg._http_get
            bg._http_get = boom
            try:
                code = bg.main(["--site-dir", str(root), "--date", "2026-11-01", "--skip-api"])
            finally:
                bg._http_get = original
            self.assertEqual(code, 0)

    def test_pollinations_http_is_resized_and_preferred_over_the_bank(self):
        sample = SAMPLE.read_bytes()
        jpeg = _jpeg(1024, 576)
        self.assertGreaterEqual(len(jpeg), 20 * 1024)
        calls = []

        def fetch(url, timeout):
            calls.append((url, timeout))
            if len(calls) == 1:
                raise TimeoutError("timed out")
            return jpeg, "image/jpeg"

        with tempfile.TemporaryDirectory() as tmp:
            root = site_with(Path(tmp), sample, bank={"bank-01.webp": sample})
            original = bg._http_get
            bg._http_get = fetch
            out = io.StringIO()
            try:
                with redirect_stdout(out):
                    code = bg.main(["--site-dir", str(root), "--date", "2026-11-06"])
            finally:
                bg._http_get = original
            self.assertEqual(code, 0)
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0][0], bg.pollinations_url("2026-11-06"))
            self.assertEqual(calls[0][1], 120)
            installed = (root / "assets" / "gen-art.webp").read_bytes()
            self.assertNotEqual(installed, sample)
            self.assertEqual(bg.decode_size(installed), (1280, 720))
            used = json.loads((root / "data" / "gen-bg-bank" / "used.json").read_text(encoding="utf-8"))
            self.assertEqual(used["entries"], {})
            self.assertEqual(out.getvalue().strip(), "source=api")

    def test_pollinations_rejects_a_bad_response_and_uses_the_bank(self):
        sample = SAMPLE.read_bytes()
        square = _jpeg(640, 640)
        self.assertGreaterEqual(len(square), 20 * 1024)
        calls = {"n": 0}

        def fetch(_url, _timeout):
            calls["n"] += 1
            if calls["n"] == 1:
                return b"not-an-image", "text/html"
            return square, "image/jpeg"

        with tempfile.TemporaryDirectory() as tmp:
            root = site_with(Path(tmp), sample, bank={"bank-01.webp": sample})
            original = bg._http_get
            bg._http_get = fetch
            try:
                code = bg.main(["--site-dir", str(root), "--date", "2026-11-07",])
            finally:
                bg._http_get = original
            self.assertEqual(code, 0)
            self.assertEqual(calls["n"], 2)
            self.assertEqual((root / "assets" / "gen-art.webp").read_bytes(), sample)
            used = json.loads((root / "data" / "gen-bg-bank" / "used.json").read_text(encoding="utf-8"))
            self.assertEqual(used["entries"]["bank-01.webp"]["last_used"], "2026-11-07")

    def test_both_sources_missing_keeps_yesterday_and_exits_2(self):
        sample = SAMPLE.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            root = site_with(Path(tmp), sample)
            css_before = (root / "generate.css").read_text(encoding="utf-8")
            code = bg.main(["--site-dir", str(root), "--date", "2026-11-05", "--skip-api"])
            self.assertEqual(code, 2)
            self.assertEqual((root / "assets" / "gen-art.webp").read_bytes(), sample)
            self.assertEqual((root / "generate.css").read_text(encoding="utf-8"), css_before)
            self.assertFalse((root / "assets" / "gen-bg-archive").exists())

    def test_jpeg_is_converted_to_webp_without_drawing(self):
        with tempfile.TemporaryDirectory() as tmp:
            jpg = Path(tmp) / "in.jpg"
            subprocess.check_call(
                ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=purple:s=64x36", "-frames:v", "1", str(jpg)],
                stdout=subprocess.DEVNULL,
            )
            out = bg.as_webp(jpg.read_bytes())
            self.assertTrue(out.startswith(b"RIFF") and out[8:12] == b"WEBP")


def _jpeg(width: int, height: int) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "fixture.jpg"
        subprocess.check_call(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", f"color=c=0x4b2a86:s={width}x{height},noise=alls=40:allf=t",
                "-frames:v", "1", "-q:v", "2", str(dest),
            ],
            stdout=subprocess.DEVNULL,
        )
        return dest.read_bytes()


if __name__ == "__main__":
    unittest.main()
