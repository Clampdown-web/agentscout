#!/usr/bin/env python3
"""Fallback order for the daily generator background. Code never draws the art."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
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

    def test_no_configured_api_is_an_empty_provider_list(self):
        self.assertEqual(bg.provider_names({}), [])
        self.assertEqual(bg.provider_names({"XAI_API_KEY": "  ", "OPENAI_API_KEY": ""}), [])

    def test_provider_order(self):
        self.assertEqual(
            bg.provider_names({
                "XAI_API_KEY": "x",
                "OPENAI_API_KEY": "o",
                "FAL_API_KEY": "f",
                "BFL_API_KEY": "b",
                "TOGETHER_API_KEY": "t",
                "STABILITY_API_KEY": "s",
            }),
            ["xai", "openai", "fal", "bfl", "together", "stability"],
        )
        self.assertEqual(
            bg.provider_names({"GEN_BG_API_URL": "https://example.test/v1/images/generations", "GEN_BG_API_KEY": "k"})[0],
            "custom",
        )

    def test_image_flag_installs_that_file_and_bumps_version(self):
        sample = SAMPLE.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            root = site_with(Path(tmp), b"RIFFOLDWEBP", archives=8)
            previous = (root / "assets" / "gen-art.webp").read_bytes()
            code = bg.main(["--site-dir", str(root), "--date", "2026-11-01", "--image", str(SAMPLE), "--skip-api"])
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

            def boom(_env=None):
                raise AssertionError("API helper should not run with --skip-api")

            original = bg.generate_via_api
            bg.generate_via_api = boom
            try:
                code = bg.main(["--site-dir", str(root), "--date", "2026-11-01", "--skip-api"])
            finally:
                bg.generate_via_api = original
            self.assertEqual(code, 0)

    def test_api_result_is_preferred_over_the_bank(self):
        sample = SAMPLE.read_bytes()
        fresh = SAMPLE.read_bytes()[:20] + b"API-IMAGE" + SAMPLE.read_bytes()[20:]
        # fresh must still be a webp; splice after the header so the magic stays valid
        self.assertTrue(fresh.startswith(b"RIFF"))
        with tempfile.TemporaryDirectory() as tmp:
            root = site_with(Path(tmp), sample, bank={"bank-01.webp": sample})

            def fake_api(_env=None):
                return fresh, "$0.04"

            original = bg.generate_via_api
            bg.generate_via_api = fake_api
            try:
                code = bg.main(["--site-dir", str(root), "--date", "2026-11-04"])
            finally:
                bg.generate_via_api = original
            self.assertEqual(code, 0)
            self.assertEqual((root / "assets" / "gen-art.webp").read_bytes(), fresh)
            used = json.loads((root / "data" / "gen-bg-bank" / "used.json").read_text(encoding="utf-8"))
            self.assertEqual(used["entries"], {})

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


if __name__ == "__main__":
    unittest.main()
