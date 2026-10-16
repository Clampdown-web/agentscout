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
GOALS={"coding":["coding","app builders"],"research":["research","browser/computer use"],"crypto":[],"writing":["productivity","models"],"media":["voice","vision"],"automation":["no-code builders","browser/computer use","personal agents","frameworks","MCP & infra"],"support":["business agents"]}
KW={"crypto":["crypto","wallet","trading","defi","onchain","token"],"support":["support","customer","helpdesk"],"writing":["writ","content","copy"],"media":["video","voice","image","speech"]}
def goals(x):
    txt=(x["name"]+" "+x["description"]).lower()
    return sorted({g for g,c in GOALS.items() if x["category"] in c}|{g for g,k in KW.items() if any(w in txt for w in k)})
def skill(x):
    return "no-code" if x.get("audience")=="ready to use" or x["category"] in("no-code builders","app builders","personal agents","business agents") else "developer"
def build(t):
    os.makedirs("api",exist_ok=True)
    tools=[]
    for x in t:
        f=[x["pricing_detail"] or x["pricing"]]
        if x.get("maturity"): f.append(x["maturity"])
        if x.get("github_stars"): f.append(f"{x['github_stars']} GitHub stars")
        f+= [u.capitalize() for u in x.get("use_cases",[]) if u!=x["category"]]
        tools.append({"name":x["name"],"slug":x["slug"],"url":x["url"],"website":x.get("website",""),"github":x.get("github",""),"category":x["category"],
          "description":x["description"],"key_features":f,"pricing":x.get("pricing_detail") or x["pricing"],
          "price_tag":tag(x["pricing"]),"platforms":platforms(x),"date_added":x.get("added") or x.get("verified"),"added":x.get("added"),"source":x.get("source"),
          "goals":goals(x),"skill":skill(x),"weekly_pick":bool(x.get("featured")),"new":bool(x.get("new")),"new_this_week":(x.get("added") or "")>=(datetime.date.today()-datetime.timedelta(days=7)).isoformat(),"repo":x.get("repo"),"logo":(f"https://clampdown-web.github.io/agentscout/{x['logo']}" if x.get("logo") else None),
          "page":f"https://clampdown-web.github.io/agentscout/tools/{x['slug']}.html"})
    json.dump({"version":1,"generated":datetime.datetime.utcnow().isoformat()+"Z","count":len(tools),"tools":tools},open("api/tools.json","w"),indent=1,ensure_ascii=False)
if __name__=="__main__": build(json.load(open("tools.json")))
