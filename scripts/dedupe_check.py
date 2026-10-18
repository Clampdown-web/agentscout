"""Duplicate check for tools.json by normalized name, domain and GitHub repo. Exit 1 on duplicates."""
import json,re,sys,collections
from urllib.parse import urlparse
SHARED={"huggingface.co","developer.nvidia.com","github.com","devin.ai","langchain.com","modelcontextprotocol.io","izotope.com","borisfx.com","waves.com"}  # hosts shared by legitimately distinct pre-existing tools
def norm(s): return re.sub(r'[^a-z0-9]','',re.sub(r'\(.*?\)','',s or '').lower())
def dom(u):
  if not u: return ''
  d=urlparse(u if '//' in u else 'https://'+u).netloc.lower().removeprefix('www.')
  return '' if d in SHARED or d.endswith('github.io') else d
def repo_of(x):
  out=set()
  for u in (x.get('github'),x.get('repo'),x.get('url')):
    if u and ('github.com' in u or u.count('/')==1 and '.' not in u.split('/')[0]):
      out.add('/'.join(u.lower().replace('https://github.com/','').strip('/').split('/')[:2]))
  return out
def keys(t):
  K={"name":set(),"domain":set(),"repo":set()}
  for x in t:
    K["name"].add(norm(x['name']))
    for u in (x.get('url'),x.get('website')):
      d=dom(u); d and K["domain"].add(d+urlparse(u).path.rstrip('/') if d in () else d)
    K["repo"]|=repo_of(x)
  return K
if __name__=="__main__":
  t=json.load(open(sys.argv[1] if len(sys.argv)>1 else 'tools.json')); bad=False
  for k,f in [("name",lambda x:{norm(x['name'])}),("domain",lambda x:{dom(u) for u in (x.get('url'),x.get('website'))}-{''}),("repo",repo_of),("slug",lambda x:{x['slug']}),("id",lambda x:{x['id']})]:
    c=collections.Counter(v for x in t for v in f(x)); d=[v for v,n in c.items() if n>1]
    print(k,"duplicates:",d); bad|=bool(d)
  sys.exit(1 if bad else 0)
