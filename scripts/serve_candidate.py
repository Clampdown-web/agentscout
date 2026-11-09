#!/usr/bin/env python3
"""Serve this checkout on 127.0.0.1 only.

No public deploy and no secrets. Open the printed submit URL in a desktop
browser. Turnstile's sitekey is limited to agentscouthq.com, so this server
can show layout, contrast, and the #sfts error text. It cannot collect a
real challenge token.
"""
from __future__ import annotations

import argparse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    handler = lambda *a, **k: SimpleHTTPRequestHandler(*a, directory=str(root), **k)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"http://127.0.0.1:{args.port}/submit.html?notrack=1")
    print("Bind is 127.0.0.1 only. Stop with Ctrl-C. Do not submit the form.")
    server.serve_forever()


if __name__ == "__main__":
    main()
