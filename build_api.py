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
LIC=__import__("re").compile(r"\b(AGPL[- ]?v?3(?:\.0)?|LGPL[- ]?v?[23](?:\.\d)?|GPL[- ]?v?[23](?:\.0)?|Apache[- ]?2(?:\.0)?|MIT|BSD[- ]?[23]-?Clause|BSD|MPL[- ]?2(?:\.0)?|Elastic License(?: 2\.0)?|SSPL)\b",2)
def lic(x):
    m=LIC.search((x.get("pricing_detail") or "")+" "+x.get("description",""))
    if not m: return ""
    v=m.group(1).replace(" ","-")
    return "Apache-2.0" if v.lower().startswith("apache") else v
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
          "goals":goals(x),"skill":skill(x),"weekly_pick":bool(x.get("featured")),"new":bool(x.get("new")),"new_this_week":(x.get("added") or "")>=(datetime.datetime.now(__import__("zoneinfo").ZoneInfo("America/Los_Angeles")).date()-datetime.timedelta(days=6)).isoformat(),"repo":x.get("repo"),"github_stars":x.get("github_stars"),"open_source":x["pricing"].lower().startswith("open"),"license":lic(x),"tags":x.get("use_cases",[])+x.get("tags",[]),"hybrid":"hybrid" in x.get("tags",[]),"logo":(f"https://agentscouthq.com/{x['logo']}" if x.get("logo") else None),
          "page":f"https://agentscouthq.com/tools/{x['slug']}.html"})
    lc=max((x.get("verified") or "") for x in t)
    json.dump({"version":1,"generated":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"updated":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"last_checked":lc,"count":len(tools),"tools":tools},open("api/tools.json","w"),indent=1,ensure_ascii=False)
if __name__=="__main__": build(json.load(open("tools.json")))
