"""Dated noindex hold for enriched tool pages.

A batch in data/index_hold.json stays out of the sitemap until its date,
in America/Los_Angeles. The build lets out at most one batch per calendar
day, oldest first, and each batch is capped at `cap` slugs (the same five
a day as new unenriched URLs). Progress is stored on the index state dict
the caller saves, so a second build the same day does not release another batch.
"""


def held_slugs(today, hold, state, cap=5):
    """Slugs that stay noindex. Updates `state` when a batch is released."""
    if not isinstance(hold, dict):
        return set()
    cap = max(int(cap or 0), 0)
    batches = []
    for item in hold.get("releases") or []:
        if not isinstance(item, dict):
            continue
        date = str(item.get("date") or "")
        slugs = [s for s in (item.get("slugs") or []) if isinstance(s, str) and s]
        if not date or not slugs or cap == 0:
            continue
        for i in range(0, len(slugs), cap):
            batches.append((date, slugs[i:i + cap]))
    released = set(state.get("hold_released_slugs") or [])
    release_day = state.get("hold_release_day") or ""
    pending = []
    for date, slugs in batches:
        still = [s for s in slugs if s not in released]
        if still and date <= today:
            pending.append((date, still))
    pending.sort()
    if release_day != today and pending:
        date, slugs = pending[0]
        released.update(slugs)
        state["hold_released_slugs"] = sorted(released)
        state["hold_release_day"] = today
        dates = list(state.get("hold_released") or [])
        if date not in dates:
            dates.append(date)
        state["hold_released"] = dates
    held = set()
    for date, slugs in batches:
        for slug in slugs:
            if slug not in released:
                held.add(slug)
    for slug in hold.get("slugs") or []:
        if isinstance(slug, str) and slug and slug not in released:
            held.add(slug)
    return held
