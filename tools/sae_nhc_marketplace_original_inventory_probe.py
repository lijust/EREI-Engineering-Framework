#!/usr/bin/env python3
"""Read-only public NHC marketplace unit listing discovery; respect origin robots and access controls."""
import asyncio,hashlib,json,urllib.request,urllib.robotparser
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime,timezone
from playwright.async_api import async_playwright
URLS=["https://nhc.sakani.sa/marketplace","https://ahl.nhc.sa/ar"]
UA="SAE-DB-public-original-listing-research/1.0"
OUT=Path("sae-nhc-public-marketplace-source-study.json")
data={"schema":"SAE_NHC_PUBLIC_ORIGINAL_MARKETPLACE_LISTING_SOURCE_ONLY","capture_utc":datetime.now(timezone.utc).isoformat(),"sheet_writes":0,"results":[]}
def allow(url):
 u=urlsplit(url);robots=u.scheme+"://"+u.netloc+"/robots.txt"
 req=urllib.request.Request(robots,headers={"User-Agent":UA})
 with urllib.request.urlopen(req,timeout=20) as r:
  if r.status!=200:return False,"ROBOTS_NOT_200"
  content=r.read(150001)
 if len(content)>150000:return False,"ROBOTS_TOO_LARGE"
 parser=urllib.robotparser.RobotFileParser()
 parser.parse(content.decode("utf8","replace").splitlines())
 return parser.can_fetch(UA,url),"ROBOTS_PARSED"
async def check(url,browser):
 row={"source":url,"responses":[],"errors":[]}
 try:allowed,info=await asyncio.to_thread(allow,url)
 except Exception as e:allowed=False;info="ROBOTS_UNVERIFIED_"+type(e).__name__
 row["robots"]=info
 if not allowed:row["stop"]="ROBOTS_BLOCKED_OR_UNVERIFIED";return row
 page=await browser.new_page(user_agent=UA)
 requests=[];blocked=False
 async def resp(r):
  nonlocal blocked
  orig=urlsplit(url).hostname or ""
  host=urlsplit(r.url).hostname or ""
  if r.status in (403,429) and (host==orig or host.endswith("."+orig)):blocked=True
  if r.status!=200 or len(row["responses"])>=90:return
  if r.request.resource_type not in ("xhr","fetch") and "json" not in r.headers.get("content-type",""):return
  try:
   content=await r.body()
   if len(content)>8500000:return
   meta={"url":r.url,"size":len(content),"sha256":hashlib.sha256(content).hexdigest(),"mime":r.headers.get("content-type","")}
   try:
    blob=json.loads(content)
    def arr(o,dep=0):
     if dep>6:return []
     if isinstance(o,dict):return sum([arr(v,dep+1) for v in o.values()],[])
     if isinstance(o,list):
      if len(o)>=5 and isinstance(o[0],dict):
       fields=list(o[0].keys())
       rec={"count":len(o),"fields":fields[:40],"samples":[{k:v for k,v in x.items() if isinstance(v,(str,int,float,bool,type(None)))} for x in o[:3]]}
       return [rec]
      return sum([arr(v,dep+1) for v in o[:3]],[])
     return []
    meta["arrays"]=arr(blob)[:8]
   except Exception:pass
   row["responses"].append(meta)
  except Exception as e:row["errors"].append("XHR_"+type(e).__name__)
 page.on("response",lambda r:requests.append(asyncio.create_task(resp(r))))
 try:
  r=await page.goto(url,wait_until="domcontentloaded",timeout=45000)
  row["http"]=r.status if r else None
  if row["http"]==200 and not blocked:
   await page.wait_for_timeout(7500)
   row["title"]=await page.title()
   row["page"]=await page.evaluate("""() => ({ text:(document.body?.innerText||"").slice(0,1800), buttons:[...document.querySelectorAll('button')].map(e=>e.innerText.trim()).filter(Boolean).slice(0,65), links:[...document.querySelectorAll('a[href]')].filter(x=>/الوحدات|استكشف|عرض|unit|project/i.test(x.innerText+" "+x.href)).map(x=>({title:x.innerText.trim().slice(0,50),href:x.href})).slice(0,40)})""")
 except Exception as e:row["errors"].append("PAGE_"+type(e).__name__+":"+str(e)[:120])
 if requests:await asyncio.gather(*requests,return_exceptions=True)
 row["blocked"]=blocked
 await page.close()
 return row
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True)
  for url in URLS:
   x=await check(url,b);data["results"].append(x)
   OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
   print("SAE_NHC_SOURCE",json.dumps({"url":url,"robots":x.get("robots"),"http":x.get("http"),"blocked":x.get("blocked"),"api":len(x["responses"]),"arrays":sum(len(q.get("arrays",[])) for q in x["responses"]),"page":x.get("page",{}),"errors":x.get("errors",[])[:3]},ensure_ascii=False),flush=True)
  await b.close()
if __name__=="__main__":asyncio.run(main())
