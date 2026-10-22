"""One-off: backfill added (first git commit containing the tool name) and source. Source was then set by id range of batch commits (<=97 original, 98-167 directory, 168-446 GitHub, 447-502 MCP registry, 503+ Product Hunt/Hugging Face)."""
import json,subprocess,re
def src(msg):
  m=msg.lower()
  if "product hunt" in m or "hugging face" in m: return None  # mixed batch, decide per tool below
  if "mcp registry" in m or "mcp servers from" in m: return "MCP registry"
  if "github topics" in m or "open-source agent tools from github" in m: return "GitHub"
  if "70 verified" in m or "futurepedia" in m: return "directory"
  return "original"
HF={"IBM CUGA","AgentFlow","TEN Framework","Galileo Agent Leaderboard","CAMEL"}
revs=subprocess.check_output(["git","log","--reverse","--format=%H|%cs|%s","--","tools.json"]).decode().splitlines()
first={}
for line in revs:
  h,d,msg=line.split("|",2)
  try: t=json.loads(subprocess.check_output(["git","show",f"{h}:tools.json"]))
  except Exception: continue
  if isinstance(t,dict): t=t.get("tools",[])
  for x in t:
    k=re.sub(r'[^a-z0-9]','',x.get("name","").lower())
    if k not in first: first[k]=(d,msg)
t=json.load(open("tools.json"))
for x in t:
  k=re.sub(r'[^a-z0-9]','',x["name"].lower())
  d,msg=first.get(k,(x.get("verified"),"original"))
  s=src(msg)
  if s is None: s="Hugging Face" if x["name"] in HF else "Product Hunt"
  x.setdefault("added",d); x.setdefault("source",s)
json.dump(t,open("tools.json","w"),indent=2,ensure_ascii=False)
import collections; print(collections.Counter(x["source"] for x in t)); print(collections.Counter(x["added"] for x in t).most_common(12))
