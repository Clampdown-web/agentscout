"""Save/vote boot used by data/detail.tpl and copied into built pages.

app.js defines AS. Google's live test of tools/magentic-ui.html on 2026-11-07
loaded the HTML and then failed app.js with no HTTP status ("Other error").
The inline boot then threw ReferenceError: AS is not defined. The buttons are
already in the HTML, so the boot is optional: skip it when AS did not load.
"""
OLD = (
    '<script>document.querySelectorAll("[data-actions]").forEach(n=>{const s=n.dataset.actions;'
    'if(!n.parentNode.querySelector("[data-save]"))n.outerHTML=AS.saveBtn(s,1)+AS.voteBtn(s)});'
    '/* buttons are in the HTML (no layout shift); set their state from this device */'
    'document.querySelectorAll(".acts [data-save]").forEach(b=>{const on=AS.saved(b.dataset.save);'
    'b.classList.toggle("on",on);b.setAttribute("aria-pressed",on);b.querySelector("span").textContent=on?"Saved":"Save"});'
    'document.querySelectorAll(".acts [data-vote]").forEach(b=>{const on=AS.voted(b.dataset.vote);'
    'b.classList.toggle("on",on);b.setAttribute("aria-pressed",on);b.querySelector("span").textContent=on?1:0});'
    'AS.bind(document);document.querySelectorAll("[data-saved-count]").forEach(n=>n.textContent=AS.savedCount());</script>'
)
_BODY = OLD[len("<script>"):-len("</script>")]
NEW = '<script>if(typeof AS!=="undefined"&&AS.saveBtn){' + _BODY + "}</script>"

def guard(html):
    if OLD not in html:
        return html
    return html.replace(OLD, NEW)
