"""Generates api/tools.json (machine-readable daily feed for the AgentScout app) from tools.json."""
import json,os,datetime
def tag(p):
    p=p.lower()
    if p.startswith("open") : return "free"
    if "freemium" in p or "cloud" in p: return "freemium"
    if p in("see site",): return "unknown"
    return "paid"
def platforms(x):
    a=x.get("audience","");c=x["category"]
    if a!="ready to use" or c in("frameworks","MCP & infra","evals & observability"): return ["Developer (API/SDK)"]+(["Self-host"] if "open" in x["pricing"].lower() else [])
    return ["Web"]
def build(t):
    os.makedirs("api",exist_ok=True)
    tools=[]
    for x in t:
        f=[x["pricing_detail"] or x["pricing"]]
        if x.get("maturity"): f.append(x["maturity"])
        if x.get("github_stars"): f.append(f"{x['github_stars']} GitHub stars")
        f+= [u.capitalize() for u in x.get("use_cases",[]) if u!=x["category"]]
        tools.append({"name":x["name"],"slug":x["slug"],"url":x["url"],"category":x["category"],
          "description":x["description"],"key_features":f,"pricing":x.get("pricing_detail") or x["pricing"],
          "price_tag":tag(x["pricing"]),"platforms":platforms(x),"date_added":x.get("verified"),
          "weekly_pick":bool(x.get("featured")),"new":bool(x.get("new")),"repo":x.get("repo"),
          "page":f"https://clampdown-web.github.io/agentscout/tools/{x['slug']}.html"})
    json.dump({"version":1,"generated":datetime.datetime.utcnow().isoformat()+"Z","count":len(tools),"tools":tools},open("api/tools.json","w"),indent=1,ensure_ascii=False)
if __name__=="__main__": build(json.load(open("tools.json")))
