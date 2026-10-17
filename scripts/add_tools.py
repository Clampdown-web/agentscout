"""Verify and append tools to tools.json.
Input TSV columns: repo_or_blank  category  pricing  audience  description  [name]  [website]
  - repo: owner/name on GitHub (or blank for closed products; then name+website required)
Checks: GitHub repo exists & not archived, website returns 200 (bot-blocked 403 => website dropped, github kept),
logo = site apple-touch-icon / icon >=64px, else GitHub owner avatar; dedupe by name/domain/repo against tools.json.
Usage: python3 scripts/add_tools.py batch.tsv [--source="GitHub"|"MCP registry"|"Product Hunt"|"Hugging Face"|"Futurepedia"|...] [--dry]
Each new tool is stamped added=today and source; build_site.py then refreshes the homepage Recently added section, new.html and llms.txt.
 [--cache=discovered.json from discover_github.py]"""
import sys,json,re,io,requests,concurrent.futures as cf
from urllib.parse import urljoin,urlparse
from PIL import Image
sys.path.insert(0,'scripts'); from dedupe_check import norm,dom,keys
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
GH={"Accept":"application/vnd.github+json","User-Agent":"agentscout"}
BADHOST=re.compile(r'(linkedin|discord|deepwiki|arxiv|twitter|x\.com|youtube|aka\.ms|bilibili|notion\.site|go\.novu)',re.I)
CATS={"frameworks","coding","MCP & infra","evals & observability","voice","browser/computer use","research","no-code builders","business agents","personal agents","app builders","vision","games","crypto","productivity","models"}
PRICES={"Open source","Freemium","Open source + cloud","Paid","Usage-based","Enterprise","See site","Open weights","Open standard"}
def getimg(u):
  try:
    r=requests.get(u,headers=UA,timeout=12)
    if r.status_code!=200: return None
    data=r.content
    if u.split('?')[0].endswith('.svg') or data.lstrip()[:5] in (b'<svg ',b'<?xml'):
      import cairosvg; data=cairosvg.svg2png(bytestring=data,output_width=128,output_height=128)
    im=Image.open(io.BytesIO(data))
    if im.format=='ICO': im.size=max(im.ico.sizes())
    im.load()
    if min(im.size)<64: return None
    ex=im.convert('RGB').getextrema()
    return None if all(a==b for a,b in ex) else im  # reject blank single-color images
  except Exception: return None
def verify(row):
  row+=['']*(7-len(row)); repo,cat,pr,aud,desc,name,site=row[:7]; o={"err":None}
  assert cat in CATS and pr in PRICES, (cat,pr)
  stars=None;owner_avatar=None
  if repo:
    j=CACHE.get(repo.lower())
    if not j:
      r=requests.get(f"https://api.github.com/repos/{repo}",headers=GH,timeout=15)
      if r.status_code!=200: return {"err":f"github {r.status_code}","repo":repo}
      j=r.json(); j["owner_login"]=j["owner"]["login"]
    elif requests.head(f"https://github.com/{j['full_name']}",headers=UA,timeout=15,allow_redirects=True).status_code!=200: return {"err":"github dead","repo":repo}
    if j.get("archived"): return {"err":"archived","repo":repo}
    repo=j["full_name"]; stars=j["stargazers_count"]; owner_avatar=f"https://github.com/{j.get('owner_login') or j.get('owner')}.png?size=200"
    name=name or j["name"]; site=site or (j.get("homepage") or "")
  if site and not site.startswith('http'): site='https://'+site
  if site and (BADHOST.search(site) or 'github.com' in site or 'github.io' in site and not repo): site=""
  html=""
  if site:
    try:
      r=requests.get(site,headers=UA,timeout=15); 
      if r.status_code==200: site=r.url; html=r.text
      else: site=""
    except Exception: site=""
  if not repo and not site: return {"err":"no live link","name":name}
  cands=[]
  for m in re.finditer(r'<link[^>]+>',html,re.I):
    t=m.group(0)
    if re.search(r'rel=["\'][^"\']*(apple-touch-icon|icon)',t,re.I):
      h=re.search(r'href=["\']([^"\']+)',t)
      if h: cands.append(urljoin(site,h.group(1)))
  cands.sort(key=lambda u:0 if 'apple' in u else 1)
  if site: cands+= [urljoin(site,'/apple-touch-icon.png'),urljoin(site,'/favicon.ico')]
  if owner_avatar: cands.append(owner_avatar)
  logo=None
  if re.search(r'hf\.space|huggingface\.co/spaces',site): cands=[c for c in cands if 'huggingface' not in c and 'hf.space' not in c]
  cands=[c for c in cands if not re.search(r'github\.com/fluidicon|githubassets|figma\.com|google\.com/favicon',c)]
  for c in cands:
    im=getimg(c)
    if im: logo=(im,c);break
  if not logo: return {"err":"no logo","name":name}
  pretty=name if (not repo or row[5] or any(ch.isupper() for ch in name)) else name.replace('-',' ').replace('_',' ').title()
  e={"name":pretty,"url":site or f"https://github.com/{repo}","description":desc,"category":cat,"pricing":pr,
     "maturity":"Mature" if (stars or 0)>=5000 else "Active","audience":aud,"featured":False,"new":True,
     "verified":__import__('datetime').date.today().isoformat(),"added":__import__('datetime').date.today().isoformat(),"source":SOURCE,"pricing_detail":"","use_cases":[],
     "website":site,"github":f"https://github.com/{repo}" if repo else ""}
  if repo: e["repo"]=repo; e["github_stars"]=stars
  return {"err":None,"e":e,"logo":logo}
CACHE={};SOURCE="manual"
if __name__=="__main__":
  for a in sys.argv:
    if a.startswith("--source="): SOURCE=a[9:]
    elif a.startswith("--cache=") and SOURCE=="manual": SOURCE="GitHub"
  for a in sys.argv:
    if a.startswith("--cache="): CACHE={i["full_name"].lower():i for i in json.load(open(a[8:]))}
  rows=[l.rstrip('\n').split('\t') for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
  t=json.load(open('tools.json')); K=keys(t)
  with cf.ThreadPoolExecutor(8) as ex: res=list(ex.map(verify,rows))
  nid=max(x['id'] for x in t); added=[]; skipped={}
  for r in res:
    if r["err"]: skipped.setdefault(r["err"].split()[0],[]).append(r.get("repo") or r.get("name")); continue
    e=r["e"]; ks=keys([e])
    if ks["name"]&K["name"] or ks["domain"]&K["domain"] or ks["repo"]&K["repo"]: skipped.setdefault("duplicate",[]).append(e["name"]); continue
    for k in K: K[k]|=ks[k]
    nid+=1; e["id"]=nid; e["slug"]=re.sub(r"[^a-z0-9]+","-",e["name"].lower()).strip("-"); e["logo"]=f"assets/logos/{e['slug']}.png"
    if "--dry" not in sys.argv:
      im=r["logo"][0].convert("RGBA"); im.thumbnail((128,128)); im.save(e["logo"])
    added.append(e)
  if "--dry" not in sys.argv:
    t+=added; json.dump(t,open('tools.json','w'),indent=2,ensure_ascii=False)
  print(json.dumps({"added":len(added),"total":len(t),"skipped":{k:len(v) for k,v in skipped.items()},"skipped_detail":skipped},indent=1))
