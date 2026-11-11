"""Strip session tokens and other secrets before anything is printed or saved.

The harness keeps a session id in memory only long enough to send the next
MCP request. Callers pass that value in, and this module replaces it. It
never logs the raw value.
"""
from __future__ import annotations

import re

_BEARER = re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/=-]{8,}")
_ASSIGNED = re.compile(
    r"(?i)((?:mcp-session-id|authorization|x-api-key|api[-_]?key|access[-_]?token|"
    r"refresh[-_]?token|client[-_]?secret|password)\s*[\"']?\s*[:=]\s*[\"']?)"
    r"([^\s\"',}]+)"
)
_SENSITIVE_KEY = re.compile(
    r"(?i)(session|secret|password|token|authorization|api[-_]?key)"
)


def redact_text(text: str, secrets: tuple[str, ...] = ()) -> str:
    if not text:
        return text
    for secret in secrets:
        if secret and len(secret) >= 6:
            text = text.replace(secret, "[redacted]")
    text = _BEARER.sub(r"\1[redacted]", text)
    text = _ASSIGNED.sub(r"\1[redacted]", text)
    return text


def redact_obj(value, secrets: tuple[str, ...] = ()):
    """Walk JSON-like data. Sensitive keys are replaced, then string values are scrubbed."""
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            name = str(key)
            if _SENSITIVE_KEY.search(name) and not isinstance(item, (dict, list)):
                out[key] = "[redacted]" if item else item
            else:
                out[key] = redact_obj(item, secrets)
        return out
    if isinstance(value, list):
        return [redact_obj(item, secrets) for item in value]
    if isinstance(value, str):
        return redact_text(value, secrets)
    return value
