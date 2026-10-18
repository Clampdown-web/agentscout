"""Related-tools picker for tool pages: same category, ranked by shared description words,
with a load-balancing penalty so every tool in a category gets linked from a few siblings
(not just the first six in tools.json order). Deterministic: no randomness, ties broken by slug."""
import re,collections
STOP=set("a an and the for with your you that this from into onto over across their them they its it's are can via any all not one more most own use uses using built build builds lets let make makes helps help each every other than also like just only open source tool tools platform agent agents ai app apps based plus such which when where what who while within without".split())
def words(x):
    s=(x["name"]+" "+x["description"]+" "+" ".join(x.get("tags") or [])).lower()
    return {w[:-1] if w.endswith("s") and len(w)>4 else w for w in re.findall(r"[a-z0-9][a-z0-9.+-]{2,}",s)}-STOP
def pick(t,k=6,penalty=0.06):
    W={id(x):words(x) for x in t}; by=collections.defaultdict(list)
    for x in t: by[x["category"]].append(x)
    out={}
    for cat,xs in by.items():
        load=collections.Counter()
        def sim(a,b):
            A,Bw=W[id(a)],W[id(b)]
            return len(A&Bw)/(len(A|Bw) or 1)
        # pass in order of fewest strong neighbours first so niche tools still get their best matches
        for x in sorted(xs,key=lambda x:x["slug"]):
            cand=sorted((y for y in xs if y is not x),key=lambda y:(-(sim(x,y)-penalty*load[y["slug"]]),y["slug"]))
            rel=cand[:k]
            for y in rel: load[y["slug"]]+=1
            out[x["slug"]]=rel
    return out
