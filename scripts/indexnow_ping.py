"""IndexNow ping (Bing, Yandex, Seznam, Naver via api.indexnow.org). Key file <key>.txt sits at the site root (public by design).
Usage after a push: python3 scripts/indexnow_ping.py URL [URL...]  or  --changed-today (sitemap urls with today's lastmod)."""
import sys,glob,json,os,re,urllib.request,datetime
HOST="agentscouthq.com"
key=[os.path.basename(f)[:-4] for f in glob.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}\.txt",os.path.basename(f))][0]
urls=sys.argv[1:]
if urls==["--changed-today"]:
    d=datetime.date.today().isoformat(); x=open("sitemap.xml").read()
    urls=[u for u,l in re.findall(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>",x) if l.startswith(d)]
for i in range(0,len(urls),10000):
    b=json.dumps({"host":HOST,"key":key,"keyLocation":f"https://{HOST}/{key}.txt","urlList":urls[i:i+10000]}).encode()
    r=urllib.request.urlopen(urllib.request.Request("https://api.indexnow.org/indexnow",data=b,headers={"Content-Type":"application/json; charset=utf-8"}),timeout=30)
    print("indexnow:",len(urls[i:i+10000]),"urls ->",r.status)
