#!/usr/bin/env python3
"""Research-only official inventory asset discovery for existing SAE-DB projects."""
import asyncio,json,hashlib,re,urllib.request,urllib.robotparser
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from datetime import datetime,timezone
from playwright.async_api import async_playwright
UA="SAE-DB-firstparty-asset-study/1.0"
SEEDS=[
("PRJ-001038","https://www.nhc.sa/real-estate-development/projects/47838/"),
("PRJ-001041","https://www.nhc.sa/real-estate-development/projects/319/"),
("PRJ-001109","https://www.nhc.sa/real-estate-development/projects/329/"),
("PRJ-001054","https://www.nhc.sa/real-estate-development/projects/333/"),
("PRJ-001106","https://www.nhc.sa/real-estate-development/projects/297/"),
("PRJ-001043","https://www.nhc.sa/real-estate-development/projects/315/")]
OUT=Path("sae-nhc-six-existing-firstparty-plots-source-study.json")
DATA={"schema":"SAE_NHC_SIX_EXISTING_FIRSTPARTY_INVENTORY_ASSET_DISCOVERY_20261029","time_utc":datetime.now(timezone.utc).isoformat(),"source_only":True,"sheets_writes":0,"projects":[]}
def check(url):
 p=urlsplit(url)
 req=urllib.request.Request(p.scheme+"://"+p.netloc+"/robots.txt",headers={"User-Agent":UA})
 with urllib.request.urlopen(req,timeout=15) as r:
  if r.status!=200:raise ValueError("robots failed")
  body=r.read(130000)
 if len(body)>125000:raise ValueError("oversize robots")
 rp=urllib.robotparser.RobotFileParser()
 rp.parse(body.decode("utf-8","replace").splitlines())
 return rp.can_fetch(UA,url)
async def inspect(browser,pid,url):
 rec={"canonical_existing_project":pid,"publisher_project_url":url,"source_only":True,"links":[],"api":[],"errors":[]}
 try:allowed=await asyncio.to_thread(check,url)
 except Exception as e:rec["stop"]="ROBOTS_UNVERIFIED_"+type(e).__name__;return rec
 if not allowed:rec["stop"]="ROBOTS_DISALLOW";return rec
 page=await browser.new_page(user_agent=UA,viewport={"width":1200,"height":900})
 jobs=[];stop=False
 async def take(response):
  nonlocal stop
  u=urlsplit(response.url)
  host=urlsplit(url).hostname or ""
  if response.status in (403,429) and (u.hostname or "").endswith(host.replace("www.","")):stop=True
  if response.status!=200:return
  if len(rec["api"])>=40:return
  ct=response.headers.get("content-type","")
  if response.request.resource_type not in ("xhr","fetch") and "json" not in ct:return
  try:
   body=await response.body()
   if len(body)>4000000:return
   item={"url":response.url,"bytes":len(body),"sha":hashlib.sha256(body).hexdigest(),"mime":ct}
   if "json" in ct or body[:1] in (b"[",b"{"):
    doc=json.loads(body)
    def arrays(x,depth=0):
     if depth>7:return []
     if isinstance(x,dict):return sum((arrays(y,depth+1) for y in x.values()),[])
     if isinstance(x,list):
      if len(x)>=20 and isinstance(x[0],dict):
       return [{"items":len(x),"keys":list(x[0])[:18],"sample":x[:2]}]
      return sum((arrays(y,depth+1) for y in x[:4]),[])
     return []
    item["object_arrays"]=arrays(doc)[:4]
   rec["api"].append(item)
  except Exception as e:rec["errors"].append("XHR_"+type(e).__name__)
 page.on("response",lambda resp:jobs.append(asyncio.create_task(take(resp))))
 try:
  r=await page.goto(url,wait_until="domcontentloaded",timeout=40000)
  rec["status"]=r.status if r else None
  if not stop and rec["status"]==200:
   await page.wait_for_timeout(3500)
   rec["title"]=await page.title()
   rec["links"]=await page.locator("a[href]").evaluate_all("""x=>[...new Map(x.map(a=>[a.href,{href:a.href,text:(a.innerText||"").trim().slice(0,95)}])).values()].filter(a=>/pdf|brochure|masterplan|مخطط|كتيب|خارطة|plan|download|book|interactive|selling/i.test(a.href+" "+a.text)).slice(0,80)""")
   rec["media"]=await page.evaluate("""() => ({iframes:[...document.querySelectorAll('iframe[src]')].map(x=>x.src).slice(0,20),documents:[...document.querySelectorAll('object[data],embed[src]')].map(x=>x.data||x.src).slice(0,20),scripts:[...document.querySelectorAll('script[src]')].map(x=>x.src).filter(x=>/main|app|bundle|assets/i.test(x)).slice(0,20),body:document.body.innerText.slice(0,2500)})""")
 except Exception as e:rec["errors"].append("PAGE_"+type(e).__name__+":"+str(e)[:110])
 if jobs:await asyncio.gather(*jobs,return_exceptions=True)
 await page.close()
 rec["blocked"]=stop
 return rec
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True)
  for pid,url in SEEDS:
   row=await inspect(b,pid,url)
   DATA["projects"].append(row)
   OUT.write_text(json.dumps(DATA,ensure_ascii=False,indent=2)+"\n")
   print("SAE_NHC_PROJECT_ASSET",json.dumps({"pid":pid,"status":row.get("status"),"stop":row.get("stop"),"links":row.get("links",[]),"iframes":row.get("media",{}).get("iframes",[]),"api":len(row.get("api",[])),"errors":row.get("errors",[])},ensure_ascii=False),flush=True)
  await b.close()
if __name__=="__main__":asyncio.run(main())
