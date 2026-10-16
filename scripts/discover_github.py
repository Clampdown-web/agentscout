"""Discover agent repos from GitHub topics. Usage: python3 scripts/discover_github.py out.json [min_stars] [since YYYY-MM-DD]"""
import json,sys,time,requests
out=sys.argv[1]; MIN=int(sys.argv[2]) if len(sys.argv)>2 else 500; SINCE=sys.argv[3] if len(sys.argv)>3 else "2026-04-16"
TOPICS=["ai-agents","llm-agent","agent-framework","mcp-server","browser-agent","voice-agent","coding-agent","ai-agent","agents","autonomous-agents","multi-agent","agentic-ai"]
H={"Accept":"application/vnd.github+json","User-Agent":"agentscout"}
seen={}
for t in TOPICS:
  for page in range(1,11):
    q=f"topic:{t} stars:>={MIN} pushed:>={SINCE} archived:false"
    r=requests.get("https://api.github.com/search/repositories",params={"q":q,"sort":"stars","per_page":100,"page":page},headers=H,timeout=30)
    if r.status_code==403 or r.status_code==429: time.sleep(65); r=requests.get(r.url,headers=H,timeout=30)
    if r.status_code!=200: print(t,page,r.status_code); break
    items=r.json().get("items",[])
    for i in items:
      seen.setdefault(i["full_name"].lower(),{k:i.get(k) for k in ["full_name","name","description","homepage","stargazers_count","pushed_at","topics","language","license"]}|{"owner":i["owner"]["login"],"owner_type":i["owner"]["type"],"src":"github:"+t})
    print(t,page,len(items),len(seen),flush=True); time.sleep(7)
    if len(items)<100: break
json.dump(list(seen.values()),open(out,"w"),indent=1)
