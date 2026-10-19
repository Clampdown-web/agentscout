#!/usr/bin/env python3
"""Refresh data/sponsor_stats.json, the real numbers shown on the hidden sponsor page (sponsor.html).
- Weekly page views: the Worker /stats endpoint (Analytics Engine counters), web:page_view summed over the last 7 days.
  Our own and automated traffic is already split out by the Worker as internal:* and is NOT counted.
  Needs the STATS_KEY secret in $STATS_KEY or ~/.agentscout-stats-key (never printed).
- Newsletter subscribers: beehiiv active subscribers. There is no beehiiv API key on the box, so pass the number read from
  beehiiv (dashboard or the beehiiv connector's get_publication_stats): --subscribers N. Without it the previous value and
  its date are kept. Nothing is estimated: a missing number shows as "not available" on the page.
- Tool count is not stored here; build_sponsor.py counts tools.json at build time.
Usage: python3 scripts/sponsor_stats.py [--subscribers N]   then rebuild (python3 build_site.py or python3 build_sponsor.py)."""
import json,os,sys,urllib.request,datetime
from zoneinfo import ZoneInfo
F=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","data","sponsor_stats.json")
PT=ZoneInfo("America/Los_Angeles")
def now(): return datetime.datetime.now(PT).strftime("%Y-%m-%dT%H:%M:%S%z")
S=json.load(open(F)) if os.path.exists(F) else {}
key=os.environ.get("STATS_KEY") or (open(os.path.expanduser("~/.agentscout-stats-key")).read().strip() if os.path.exists(os.path.expanduser("~/.agentscout-stats-key")) else "")
if key:
    r=urllib.request.Request("https://agentscout-image.agentscouthq.workers.dev/stats?days=7",headers={"X-Stats-Key":key,"User-Agent":"agentscout-sponsor-stats"})
    d=json.load(urllib.request.urlopen(r,timeout=30))["days"]
    S["weekly_page_views"]=sum(int(x["counters"].get("web:page_view",0)) for x in d)
    S["weekly_window"]=f'{min(x["day"] for x in d)} to {max(x["day"] for x in d)}'
    S["weekly_as_of"]=now()
else: print("No STATS_KEY: weekly page views left as they were",file=sys.stderr)
if "--subscribers" in sys.argv:
    S["newsletter_subscribers"]=int(sys.argv[sys.argv.index("--subscribers")+1]); S["subscribers_as_of"]=now(); S["subscribers_source"]="beehiiv active subscribers"
json.dump(S,open(F,"w"),indent=2); print(json.dumps(S,indent=2))
