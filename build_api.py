"""Generates api/tools.json (machine-readable daily feed for the AgentScout app) from tools.json."""
import json,os,datetime
def tag(p):
    p=p.lower()
    if p.startswith("open") : return "free"
    if "freemium" in p or "cloud" in p: return "freemium"
    if p in("see site",): return "unknown"
    return "paid"
# Hand-checked platform overrides (Oct 20 2026 data cleanup): desktop editors were showing as "Web".
PLAT={"cursor":["Desktop (macOS, Windows, Linux)"],"windsurf":["Desktop (macOS, Windows, Linux)","IDE extension"],"zed":["Desktop (macOS, Windows, Linux)"],"trae":["Desktop (macOS, Windows, Linux)"],
 "github-copilot":["IDE extension","Web"],"lm-studio":["Desktop (macOS, Windows, Linux)"],"jan":["Desktop (macOS, Windows, Linux)"]}
def platforms(x):
    if x.get("slug") in PLAT: return PLAT[x["slug"]]
    a=x.get("audience","");c=x["category"]
    if a!="ready to use" or c in("frameworks","MCP & infra","evals & observability","memory & RAG","security & governance","sandboxes & code execution","models & local runtimes"): return ["Developer (API/SDK)"]+(["Self-host"] if "open" in x["pricing"].lower() else [])
    return ["Web"]
GOALS={"coding":["coding","app builders","sandboxes & code execution"],"research":["research","browser/computer use"],"crypto":["crypto"],"writing":["productivity","models & local runtimes"],"media":["voice","vision","film & TV production","video generation","film & TV audio","music production","image generation","graphic design & branding","3D & concept art","photography & photo editing"],"automation":["no-code builders","browser/computer use","personal agents","frameworks","MCP & infra","memory & RAG"],"support":["customer support","sales & marketing","business agents"]}
KW={"crypto":["crypto","wallet","trading","defi","onchain","token"],"support":["support","customer","helpdesk"],"writing":["writ","content","copy"],"media":["video","voice","image","speech"]}
def goals(x):
    txt=(x["name"]+" "+x["description"]).lower()
    return sorted({g for g,c in GOALS.items() if x["category"] in c}|{g for g,k in KW.items() if any(w in txt for w in k)})
# DIY hardware/firmware projects: real voice projects, but not ready-made voice agents, so free-tool picks rank them after software.
HW={"xiaozhi-esp32","elatoai"}
DEV_CATS=("coding","frameworks","MCP & infra")  # always developer tools, even when "ready to use" (Cursor is not "no code needed")
def skill(x):
    if x["category"] in DEV_CATS: return "developer"
    return "no-code" if x.get("audience")=="ready to use" or x["category"] in("no-code builders","app builders","personal agents","business agents","customer support","sales & marketing") else "developer"
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
          "goals":goals(x),"skill":skill(x),"weekly_pick":bool(x.get("featured")),"new":bool(x.get("new")),"seed":bool(x.get("seed")),"new_this_week":(not x.get("seed")) and (x.get("added") or "")>=(datetime.datetime.now(__import__("zoneinfo").ZoneInfo("America/Los_Angeles")).date()-datetime.timedelta(days=6)).isoformat(),"repo":x.get("repo"),"github_stars":x.get("github_stars"),"open_source":x["pricing"].lower().startswith("open"),"license":lic(x),"tags":x.get("use_cases",[])+x.get("tags",[])+(["hardware"] if x.get("slug") in HW else []),"hybrid":"hybrid" in x.get("tags",[]),"logo":(f"https://agentscouthq.com/{x['logo']}" if x.get("logo") else None),
          "page":f"https://agentscouthq.com/tools/{x['slug']}.html"})
    lc=max((x.get("verified") or "") for x in t)
    json.dump({"version":1,"generated":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"updated":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"last_checked":lc,"count":len(tools),"tools":tools},open("api/tools.json","w"),indent=1,ensure_ascii=False)
    # small file for the homepage "Recently added" stats (stats.js.html), so the homepage doesn't download the full 1.5 MB API
    json.dump({"last_checked":lc,"tools":[{"category":x.get("category"),"added":x.get("added"),"seed":bool(x.get("seed"))} for x in t]},open("api/stats.json","w"),separators=(",",":"),ensure_ascii=False)
if __name__=="__main__": build(json.load(open("tools.json")))
