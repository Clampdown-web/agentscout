#!/usr/bin/env python3
"""JSON-LD embedded in a script tag must not be able to close that tag."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_bot_templates import ld_script


def main():
    payload = "</script><script>alert(1)</script>"
    html = ld_script({"name": payload, "ok": "Cursor"})
    body = html.split(">", 1)[1].rsplit("</script>", 1)[0]
    if "</" in body:
        raise SystemExit("json-ld body still contains a script closer")
    parsed = json.loads(body)
    if parsed["name"] != payload or parsed["ok"] != "Cursor":
        raise SystemExit("json-ld round trip changed the text")
    plain = ld_script({"name": "Cursor", "url": "https://agentscouthq.com/tools/cursor.html"})
    if "<\\/" in plain:
        raise SystemExit("a normal listing was escaped")
    print("json-ld script escape ok")


if __name__ == "__main__":
    main()
