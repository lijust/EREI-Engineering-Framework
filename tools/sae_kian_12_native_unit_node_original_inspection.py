#!/usr/bin/env python3
"""Kian Residence PRJ-001827 exact publisher DOM data-unit node inspection.

A 22-host survey found 12 elements with native unit attributes; determine
whether they are physical units, only models, or interface elements. No writes.
"""
import asyncio,hashlib,json,re,urllib.request,urllib.robotparser
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from playwright.async_api import async_playwright
HOST="kian-d.com";URL="https://kian-d.com/projects/kian-residence/"
UA="SAE-DB-Kian-original-public-unit-nodes/1.0"
OUT=Path("sae-kian-original-unit-node-deep-evidence.json")
result={"schema":"SAE_EXISTING_PRJ_001827_KIAN_SOURCE_12_NATIVE_DOM_UNIT_NODES",
"source_url":URL,"project_id":"PRJ-001827","utc":datetime.now(timezone.utc).isoformat(),
"source_only":True,"canonical_writes":0}
def robots():
 with urllib.request.urlopen(urllib.request.Request("https://"+HOST+"/robots.txt",headers={"User-Agent":UA}),timeout=18) as r:
  if r.status!=200:raise RuntimeError("ROBOTS_STATUS_"+str(r.status))
  b=r.read(180001)
 if len(b)>180000:raise RuntimeError("ROBOTS_TOO_LARGE")
 rp=urllib.robotparser.RobotFileParser();rp.parse(b.decode("utf8","replace").splitlines())
 return rp.can_fetch(UA,URL)
async def main():
 try:allowed=await asyncio.to_thread(robots)
 except Exception as e:result["stop"]="ROBOTS_UNVERIFIED_"+type(e).__name__;OUT.write_text(json.dumps(result));return
 if not allowed:result["stop"]="ROBOTS_DISALLOW";OUT.write_text(json.dumps(result));return
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  page=await browser.new_page(user_agent=UA)
  access=False;xhrs=[]
  async def response(r):
   nonlocal access
   if (urlsplit(r.url).hostname or "").removeprefix("www.")!=HOST:return
   if r.status in (403,429):access=True;return
   if r.status!=200 or r.request.resource_type not in ("xhr","fetch"):return
   try:
    b=await r.body()
    if len(b)>2000000:return
    item={"url":r.url,"sha":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
    if b[:1] in (b"[",b"{"):
     d=json.loads(b)
     item["first_data_keys"]=list(d)[:20] if isinstance(d,dict) else "ARRAY"
     item["source_samples"]=d[:2] if isinstance(d,list) else {k:v for k,v in d.items() if isinstance(v,(int,str,float,bool))}
    xhrs.append(item)
   except Exception:pass
  tasks=[]
  page.on("response",lambda r:tasks.append(asyncio.create_task(response(r))))
  try:
   r=await page.goto(URL,wait_until="domcontentloaded",timeout=35000)
   result["http"]=r.status if r else None
   if r and r.status==200 and not access:
    await page.wait_for_timeout(1800)
    result["capture"]=await page.evaluate("""() => {
     let nodes=[...document.querySelectorAll('[data-unit-id],[data-unit-code],[data-unit],[data-plot-number],[data-property-id]')];
     return {title:document.title,body:(document.body.innerText||'').slice(0,16000),
      nodes:nodes.map((x,i)=>({i,tag:x.tagName,dataset:x.dataset,
        class:x.className,html:x.outerHTML.slice(0,950),
        surroundingText:(x.closest('article,.unit,.unit-card,.card,[class*="unit"],[class*="property"]')?.innerText||x.parentElement?.parentElement?.innerText||'').slice(0,1400)})).slice(0,120),
      buttons:[...document.querySelectorAll('button')].map(x=>({text:x.innerText.trim().slice(0,60),html:x.outerHTML.slice(0,300)})).slice(0,60)};
    }""")
    result["status"]="SOURCE_CAPTURED"
   else:result["status"]="ACCESS_STOP"
  except Exception as e:result["status"]="PAGE_ERROR";result["error"]=type(e).__name__+":"+str(e)[:140]
  if tasks:await asyncio.gather(*tasks,return_exceptions=True)
  result["blocked"]=access;result["same_origin_xhr"]=xhrs[:25]
  await page.close();await browser.close()
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("SAE_KIAN_SOURCE_SUMMARY",json.dumps({"http":result.get("http"),"status":result.get("status"),
 "original_dom_nodes":len(result.get("capture",{}).get("nodes",[])),"source_xhr":len(xhrs)},ensure_ascii=False),flush=True)
 for n in result.get("capture",{}).get("nodes",[]):
  print("SAE_KIAN_NATIVE_NODE|"+json.dumps(n,ensure_ascii=False,separators=(",",":"))[:4500],flush=True)
if __name__=="__main__":asyncio.run(main())
