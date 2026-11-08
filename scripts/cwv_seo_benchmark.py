"""Unthrottled lab timings for the publish gate.

Turnstile keeps a challenge connection open, so waiting for networkidle never
finishes on submit.html. The completion signal is the load event. LCP, CLS,
and TTFB are read from the performance timeline after that. Thresholds stay
LCP 2500, CLS 0.1, and TTFB 800. This module does not claim field data and
does not accept a throttled Lighthouse run as its result.
"""
from __future__ import annotations

THRESHOLDS = {"lcp_ms": 2500, "cls": 0.1, "ttfb_ms": 800}
WAIT_UNTIL = "load"
METHOD = "cwv_seo_benchmark.measure_url"


def completion_wait(has_turnstile: bool) -> str:
    """Turnstile or not, do not wait for networkidle."""
    return WAIT_UNTIL


def grade_page(lcp_ms: float, cls: float, ttfb_ms: float) -> str:
    if lcp_ms > THRESHOLDS["lcp_ms"] or cls > THRESHOLDS["cls"] or ttfb_ms > THRESHOLDS["ttfb_ms"]:
        return "FAIL"
    return "PASS"
