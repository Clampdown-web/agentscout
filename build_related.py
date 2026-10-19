"""Related-tools picker for tool pages: same category, ranked by shared description words,
with a load-balancing penalty so every tool in a category gets linked from a few siblings
(not just the first six in tools.json order). Deterministic: no randomness, ties broken by slug."""
import re,collections
STOP=set("a an and the for with your you that this from into onto over across their them they its it's are can via any all not one more most own use uses using built build builds lets let make makes helps help each every other than also like just only open source tool tools platform agent agents ai app apps based plus such which when where what who while within without".split())
# Negated feature mentions ("payments are disabled", "does not support X") describe what a tool does NOT do,
# so they are removed before matching (Oct 19, 2026 PT). Same idea as the task-page rule in build_tasks.TASK_NEG.
NEGATED=re.compile(r"\(?\b(?:real[- ]money )?(?:payments?|billing|checkout|transactions?|purchases?)\s+(?:are |is )?(?:disabled|turned off|not (?:supported|available|enabled))\)?"
    r"|\bno (?:money|funds|real money) (?:moves?|changes? hands)|\b(?:does not|doesn't|do not|don't) (?:claim|support|offer|handle|process) [a-z0-9/+ -]{2,40}?(?=[,.;)]|$)",re.I)
def strip_negated(s): return NEGATED.sub(" ",s)
# Shared concepts that word overlap misses: agent registries, marketplaces and agent-to-agent discovery.
CONCEPTS=[re.compile(r"\bregistr(?:y|ies)\b|\bagents? (?:can )?discover|\bagent(?:-native)? (?:resource )?market(?:place)?s?\b",re.I)]
def concepts(x):
    d=strip_negated(x["name"]+" "+x["description"])
    return {i for i,p in enumerate(CONCEPTS) if p.search(d)}
def _text(x): return x["name"]+" "+x["description"]+" "+" ".join(x.get("tags") or [])
def _tok(s): return {w[:-1] if w.endswith("s") and len(w)>4 else w for w in re.findall(r"[a-z0-9][a-z0-9.+-]{2,}",s.lower())}-STOP
def words(x): return _tok(strip_negated(_text(x)))
def refined(x): return bool(NEGATED.search(_text(x))) or bool(concepts(x))
def pick(t,k=6,penalty=0.06):
    # Pass 1: plain word overlap with load balancing (unchanged ranking for every tool).
    # Pass 2: tools whose text has a negated feature or a shared concept are re-ranked with the refined similarity,
    # using the pass-1 loads, so fixing one tool does not reshuffle the whole category.
    R={id(x):_tok(_text(x)) for x in t}; W={id(x):words(x) for x in t}; C={id(x):concepts(x) for x in t}; by=collections.defaultdict(list)
    for x in t: by[x["category"]].append(x)
    out={}
    def jac(A,Bw): return len(A&Bw)/(len(A|Bw) or 1)
    for cat,xs in by.items():
        load=collections.Counter()
        # pass in order of fewest strong neighbours first so niche tools still get their best matches
        for x in sorted(xs,key=lambda x:x["slug"]):
            cand=sorted((y for y in xs if y is not x),key=lambda y:(-(jac(R[id(x)],R[id(y)])-penalty*load[y["slug"]]),y["slug"]))
            rel=cand[:k]
            for y in rel: load[y["slug"]]+=1
            out[x["slug"]]=rel
        for x in sorted(xs,key=lambda x:x["slug"]):
            if not refined(x): continue
            own=collections.Counter(y["slug"] for y in out[x["slug"]])
            sim=lambda y:jac(W[id(x)],W[id(y)])+0.12*len(C[id(x)]&C[id(y)])
            out[x["slug"]]=sorted((y for y in xs if y is not x),key=lambda y:(-(sim(y)-penalty*(load[y["slug"]]-own[y["slug"]])),y["slug"]))[:k]
    return out
