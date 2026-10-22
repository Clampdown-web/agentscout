"""openapi.json (OpenAPI 3.1) for the read-only static JSON feeds under /api/ (Oct 21 2026, owner-approved).
Schemas are inferred from the real files on every build, so fields and counts stay current.
Writes /openapi.json and /.well-known/openapi.json (served because the repo has .nojekyll)."""
import json,os
B="https://agentscouthq.com"
EP=[("tools.json","getTools","Full tool catalog","Every listed AI agent tool with category, pricing, platforms, GitHub data, ratings and its AgentScout page. Rebuilt daily.",["catalog"]),
 ("stats.json","getStats","Lightweight catalog stats","Category, added date and seed flag for every tool, plus the last-checked date. Small file for homepage counters.",["catalog"]),
 ("sections.json","getSections","Site sections","Categories with counts, task pages, comparisons, best-of lists, news, free tools, badges, submit form fields and newsletter info.",["site"]),
 ("editors-pick.json","getEditorsPick","Editor's Pick of the day","Today's Editor's Pick and recent pick history.",["site"]),
 ("quiz.json","getQuiz","Tool-finder quiz","Questions, options and scoring weights used by the tool-finder quiz.",["site"]),
 ("generator-daily.json","getGeneratorDaily","Daily generator image","Today's image-generator background and its overlay colours.",["site"])]
ENUM={("tools","price_tag"):["free","freemium","paid","unknown"],("tools","skill"):["developer","no-code"]}
def T(v):
    return {bool:"boolean",int:"integer",float:"number",str:"string",type(None):"null",list:"array",dict:"object"}[type(v)]
def infer(vals,path=()):
    types={T(v) for v in vals}
    if "integer" in types and "number" in types: types.discard("integer")
    s={}
    objs=[v for v in vals if isinstance(v,dict)]; arrs=[v for v in vals if isinstance(v,list)]
    if objs:
        keys=[];[keys.append(k) for o in objs for k in o if k not in keys]
        s["properties"]={k:infer([o[k] for o in objs if k in o],path+(k,)) for k in keys}
        req=[k for k in keys if all(k in o for o in objs)]
        if req: s["required"]=req
    if arrs:
        items=[i for a in arrs for i in a]
        s["items"]=infer(items,path) if items else {}
    t=sorted(types)
    s={"type":t[0] if len(t)==1 else t,**s}
    if path[-2:] in ENUM: s["enum"]=ENUM[path[-2:]]
    return s
def run():
    paths={}; schemas={}
    for f,op,summ,desc,tags in EP:
        p=f"api/{f}"
        if not os.path.exists(p): continue
        d=json.load(open(p,encoding="utf-8"))
        name="".join(w.capitalize() for w in f[:-5].replace("-"," ").split())
        sc=infer([d]); sc["title"]=name; schemas[name]=sc
        paths["/"+p]={"get":{"operationId":op,"summary":summ,"description":desc,"tags":tags,
          "responses":{"200":{"description":"JSON document","content":{"application/json":{"schema":{"$ref":f"#/components/schemas/{name}"}}}},
                       "404":{"description":"Not found"}}}}
    n=len(json.load(open("api/tools.json",encoding="utf-8"))["tools"])
    spec={"openapi":"3.1.0","info":{"title":"AgentScout public data API","version":"1.0.0",
      "summary":"Read-only static JSON feeds of the AgentScout AI agent tool directory.",
      "description":f"AgentScout lists {n:,} AI agent tools. These endpoints are static JSON files rebuilt daily: no authentication, no query parameters, GET only. Filter client-side.",
      "contact":{"name":"AgentScout","email":"support@agentscouthq.com","url":B+"/"},"termsOfService":B+"/privacy.html"},
      "servers":[{"url":B}],"tags":[{"name":"catalog","description":"Tool catalog data"},{"name":"site","description":"Site sections and features"}],
      "paths":paths,"components":{"schemas":schemas}}
    s=json.dumps(spec,indent=1,ensure_ascii=False)
    os.makedirs(".well-known",exist_ok=True)
    for p in("openapi.json",".well-known/openapi.json"): open(p,"w",encoding="utf-8").write(s+"\n")
if __name__=="__main__": run()
