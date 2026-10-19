"""Related-tools picker for tool pages: same category. Slots 1-3 are the best-known close matches; slots 4-6 are ranked
by shared description words with a load-balancing penalty so every tool in a category gets linked from a few siblings
(not just the first six in tools.json order). Deterministic: no randomness, ties broken by slug."""
import re,collections
STOP=set("a an and the for with your you that this from into onto over across their them they its it's are can via any all not one more most own use uses using built build builds lets let make makes helps help each every other than also like just only open source tool tools platform agent agents ai app apps based plus such which when where what who while within without".split())
# Negated feature mentions ("payments are disabled", "does not support X") describe what a tool does NOT do,
# so they are removed before matching (Oct 19, 2026 PT). Same idea as the task-page rule in build_tasks.TASK_NEG.
NEGATED=re.compile(r"\(?\b(?:real[- ]money )?(?:payments?|billing|checkout|transactions?|purchases?)\s+(?:are |is )?(?:disabled|turned off|not (?:supported|available|enabled))\)?"
    r"|\bno (?:money|funds|real money) (?:moves?|changes? hands)|\b(?:does not|doesn't|do not|don't) (?:claim|support|offer|handle|process) [a-z0-9/+ -]{2,40}?(?=[,.;)]|$)",re.I)
def strip_negated(s): return NEGATED.sub(" ",s)
# Shared concepts that word overlap misses: agent registries, marketplaces and agent-to-agent discovery.
CONCEPTS=[re.compile(r"\bregistr(?:y|ies)\b|\bagents? (?:can )?discover|\bagent(?:-native)? (?:resource )?market(?:place)?s?\b",re.I),
    # Email delivery and verification tools (sending, verifying or looking up emails; SMTP; deliverability), added Oct 19, 2026 PT so
    # email MCP servers (MailVeri, RocketReach, SendPulse, Bird, Atomic Mail) are matched with each other rather than with generic MCP servers.
    re.compile(r"\b(?:send(?:ing)?|verif\w*|look(?:ing)? up|find(?:ing|s)?) (?:and receiv\w+ )?(?:(?:verified|single|work|bulk) )?(?:emails?|e-mail)\b|\bemail (?:verification|deliverability|marketing|outreach|api|lists?)\b|\b(?:smtp|deliverability)\b",re.I)]
def concepts(x):
    d=strip_negated(x["name"]+" "+x["description"])
    return {i for i,p in enumerate(CONCEPTS) if p.search(d)}
def _text(x): return x["name"]+" "+x["description"]+" "+" ".join(x.get("tags") or [])
def _tok(s): return {w[:-1] if w.endswith("s") and len(w)>4 else w for w in re.findall(r"[a-z0-9][a-z0-9.+-]{2,}",s.lower())}-STOP
def words(x): return _tok(strip_negated(_text(x)))
def refined(x): return bool(NEGATED.search(_text(x))) or bool(concepts(x))
def _prominence(t):
    """How well known a tool is: an editor-written /compare/ page, the curated launch catalog (seed), featured, GitHub stars."""
    import os,math
    cmp=collections.Counter()
    if os.path.isdir("compare"):
        for f in os.listdir("compare"):
            if "-vs-" in f: a,b=f[:-5].split("-vs-",1); cmp[a]+=1; cmp[b]+=1
    pairs={tuple(sorted(f[:-5].split("-vs-",1))) for f in (os.listdir("compare") if os.path.isdir("compare") else []) if "-vs-" in f}
    P={x["slug"]:2*cmp[x["slug"]]+(1 if x.get("seed") else 0)+(1 if x.get("featured") else 0)+math.log10((x.get("github_stars") or 0)+1)/2 for x in t}
    return P,pairs
def pick(t,k=6,top=3,pool=10,frac=0.6,penalty=0.06):
    """Related tools for each tool page, within its category (Oct 19, 2026 PT).
    Slots 1-3: the best-known close matches. Candidates are the `pool` most similar tools (at least `frac` of the best match's similarity) plus any tool we wrote a
    /compare/ page against; among them, compare partners first, then prominence, then similarity.
    Slots 4-6: similarity with a load-balancing penalty, so smaller tools still get linked.
    Similarity ignores negated features and adds shared concepts (see NEGATED and CONCEPTS)."""
    W={id(x):words(x) for x in t}; C={id(x):concepts(x) for x in t}; P,pairs=_prominence(t); by=collections.defaultdict(list)
    for x in t: by[x["category"]].append(x)
    out={}
    def sim(a,b):
        A,Bw=W[id(a)],W[id(b)]
        return len(A&Bw)/(len(A|Bw) or 1)+0.12*len(C[id(a)]&C[id(b)])
    for cat,xs in by.items():
        load=collections.Counter(); head={}
        for x in sorted(xs,key=lambda x:x["slug"]):
            others=sorted((y for y in xs if y is not x),key=lambda y:(-sim(x,y),y["slug"]))
            best=sim(x,others[0]) if others else 0
            cand=[y for y in others[:pool] if sim(x,y)>0 and sim(x,y)>=frac*best]+[y for y in others[pool:] if tuple(sorted((x["slug"],y["slug"]))) in pairs]
            cand=sorted(cand,key=lambda y:(tuple(sorted((x["slug"],y["slug"]))) not in pairs,-P[y["slug"]],-sim(x,y),y["slug"]))
            head[x["slug"]]=cand[:top]
            for y in cand[:top]: load[y["slug"]]+=1
        # pass in slug order; tools nobody links yet get picked first among similar ones via the load penalty
        for x in sorted(xs,key=lambda x:x["slug"]):
            h=head[x["slug"]]; hs={y["slug"] for y in h}
            rest=sorted((y for y in xs if y is not x and y["slug"] not in hs),key=lambda y:(-(sim(x,y)-penalty*load[y["slug"]]),y["slug"]))[:k-len(h)]
            for y in rest: load[y["slug"]]+=1
            out[x["slug"]]=h+rest
    return out
