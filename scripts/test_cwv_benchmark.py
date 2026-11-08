#!/usr/bin/env python3
"""The unthrottled collector waits for load and grades with the original limits."""
from __future__ import annotations

import shutil
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cwv_seo_benchmark as cwv


class CollectorLogicTest(unittest.TestCase):
    def test_measure_url_calls_load_wait_and_grade_page(self):
        seen = {}

        def navigate(url, wait):
            seen["url"] = url
            seen["wait"] = wait
            return {"lcp_ms": 120, "cls": 0.01, "ttfb_ms": 40}

        row = cwv.measure_url("http://127.0.0.1/submit.html", navigate=navigate)
        self.assertEqual(seen["wait"], cwv.WAIT_UNTIL)
        self.assertEqual(seen["wait"], "load")
        self.assertEqual(row["grade"], cwv.grade_page(120, 0.01, 40))
        self.assertEqual(row["grade"], "PASS")
        self.assertEqual(row["throttle"], "none")
        self.assertIs(row["field_cwv"], False)

    def test_over_threshold_is_fail_and_a_blank_reading_is_refused(self):
        row = cwv.measure_url(
            "http://127.0.0.1/",
            navigate=lambda url, wait: {"lcp_ms": 2501, "cls": 0, "ttfb_ms": 10},
        )
        self.assertEqual(row["grade"], "FAIL")
        with self.assertRaises(RuntimeError):
            cwv.measure_url("http://127.0.0.1/", navigate=lambda url, wait: {"lcp_ms": None, "cls": 0, "ttfb_ms": 1})


class ChromeLoadTest(unittest.TestCase):
    def test_open_connection_does_not_block_the_load_reading(self):
        if not shutil.which("google-chrome") or not shutil.which("node"):
            self.skipTest("chrome collector is not installed")
        try:
            cwv._chrome_navigate("about:blank", "load")
        except RuntimeError as exc:
            self.skipTest(f"chrome did not start here: {exc}")

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith("/hang"):
                    import time
                    time.sleep(25)
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"open")
                    return
                body = (
                    b"<!doctype html><html><head><title>bench</title></head><body>"
                    b"<h1 id='hero'>Catalog heading</h1>"
                    b"<script>setInterval(function(){fetch('/hang')},400)</script>"
                    b"</body></html>"
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, fmt, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}/submit.html"
            row = cwv.measure_url(url)
        finally:
            server.shutdown()
        self.assertEqual(row["wait"], "load")
        self.assertIsInstance(row["lcp_ms"], float)
        self.assertGreater(row["lcp_ms"], 0)
        self.assertLessEqual(row["lcp_ms"], 2500)
        self.assertLessEqual(row["ttfb_ms"], 800)
        self.assertEqual(row["grade"], "PASS")
        self.assertIs(row["field_cwv"], False)


if __name__ == "__main__":
    unittest.main()
