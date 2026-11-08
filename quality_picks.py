"""Named starting points for the agent-infra guide.

The sentence after each link is that tool's directory description, not a new claim.
A row is omitted when the slug is missing or no longer filed under agent infra.
"""
import html

e = html.escape


def choice_html(picks, by_slug, bridge=False):
    rows = []
    for row in picks or []:
        bits = []
        for slug in row.get("slugs") or []:
            tool = by_slug.get(slug)
            if not tool or tool.get("category") != "agent infra":
                continue
            desc = " ".join((tool.get("description") or "").split()).rstrip(".")
            if not desc:
                continue
            bits.append(f'<a href="../tools/{e(slug)}.html">{e(tool["name"])}</a>: {e(desc)}')
        if not bits:
            continue
        rows.append(f'<li><strong>{e(row["label"])}.</strong> {"; ".join(bits)}.</li>')
    if not rows:
        return ""
    note = ""
    if bridge:
        note = (
            '<p style="margin:0 0 12px">Browser agents such as <a href="../tools/magentic-ui.html">MagenticLite</a> '
            'are filed under <a href="browser-computer-use.html">browser and computer use</a>, not here. '
            'The project README still asks you to connect a model endpoint. The gateway and inference rows above '
            'are directory listings for that job, not a recommendation from the maker.</p>'
        )
    return (
        '<h2 id="choose" style="font-size:18px;margin:18px 0 8px">Start with the job</h2>'
        '<p style="margin:0 0 8px">Each line is that listing\'s own description. Open one before you scroll the full grid.</p>'
        f'<ul style="margin:0 0 8px;padding-left:20px;line-height:1.7">{"".join(rows)}</ul>'
        + note
    )


def model_note():
    """Shown on a tool page whose README says you bring your own model."""
    return (
        '<p class="modelnote" style="margin:0 0 28px">The README quick start has you connect a model endpoint during onboarding, '
        'and the app does not include one. <a href="../categories/agent-infra.html#choose">Gateways and inference hosts</a> '
        'in the directory are a place to look, not a list the maker published.</p>'
    )
