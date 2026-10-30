#!/usr/bin/env python3
"""First-party Ketaf Amlak Al Faisaliyah source 12 ORIGINAL HTML apartment ads.

Only public original project-linked URLs captured by multi-source UI run.
Test whether the publisher explicitly identifies the *physical* apartment,
its project, area, asking amount. Do not treat listing/property ID as physical.
"""
import asyncio,json,re,urllib.request,urllib.robotparser,hashlib
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime,timezone
from playwright.async_api import async_playwright
MANIFEST=Path("tools/sae_ketaf_12_original_source_listing_manifest.json")
OUT=Path("sae-ketaf12-precise-original-page-unit-identity.json")
HOST="www.ketaf.sa";UA="SAE-DB-original-Ketaf-unit-identity-review/1.0"
state={"schema":"SAE_KETAF_EXISTING_PRJ_001144_FIRSTPARTY_12_DETAIL_PAGES", "timestamp":datetime.now(timezone.utc).isoformat(),
 "master_writes":0,"source_only":True,"records":[],"errors":[]}
def save():
 OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def robot():
 with urllib.request.urlopen(urllib.request.Request("https://"+HOST+"/robots.txt",headers={"User-Agent":UA}),timeout=16) as r:
  if r.status!=200:raise RuntimeError("ROBOTS_"+str(r.status))
  b=r.read(150001)
 if len(b)>150000:raise RuntimeError("ROBOTS_SIZE")
 rp=urllib.robotparser.RobotFileParser();rp.parse(b.decode("utf8","replace").splitlines());return rp
async def main():
 data=json.loads(MANIFEST.read_text(encoding="utf8"))
 if data.get("canonical_existing_project")!="PRJ-001144" or data.get("source_id")!="SRC-000047" or len(data.get("records",[]))!=12:raise RuntimeError("SOURCE_INVALID")
 try:rules=await asyncio.to_thread(robot)
 except Exception as ex:state["stop"]="ROBOTS_UNVERIFIED_"+type(ex).__name__;save();return
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  blocked=False
  for target in data["records"]:
   url=target["url"];u=urlsplit(url)
   if u.scheme!="https" or u.hostname!=HOST or u.query!="projectId=301667" or not re.fullmatch(r"/properties/\d+",u.path):raise RuntimeError("INVALID_SOURCE_ORIGINAL_URL")
   item={"firstparty_original_listing":url,"original_site_record_id":target["source_numeric_id"],"source_index_aria":target["aria"],"status":"STARTED"}
   state["records"].append(item)
   if not rules.can_fetch(UA,url):item["status"]="ROBOTS_DENIED";save();continue
   page=await browser.new_page(user_agent=UA)
   def check(r):
    nonlocal blocked
    if urlsplit(r.url).hostname==HOST and r.status in (403,429):blocked=True
   page.on("response",check)
   try:
    await asyncio.sleep(1.1)
    resp=await page.goto(url,wait_until="domcontentloaded",timeout=30000)
    item["http"]=resp.status if resp else None
    if item["http"]==200 and not blocked:
     await page.wait_for_timeout(600)
     d=await page.evaluate("""()=>({title:document.title,
       html_title:[...document.querySelectorAll('h1,h2,h3')].map(x=>x.innerText.trim()).slice(0,12),
       text:(document.body.innerText||'').slice(0,9000),
       officialStructuredData:[...document.querySelectorAll('script[type="application/ld+json"]')].map(x=>x.textContent.slice(0,3000)).slice(0,2)})""")
     item["public_detail"]=d;item["status"]="ORIGINAL_DETAIL_CAPTURED"
    else:item["status"]="STOP_SOURCE_UNAVAILABLE"
   except Exception as ex:item["status"]="BROWSER_FAILURE";item["error"]=type(ex).__name__+":"+str(ex)[:120]
   await page.close()
   save()
   print("SAE_KETAF_SOURCE_DETAIL",json.dumps({"id":item["original_site_record_id"],
    "status":item["status"],"http":item.get("http"),"title":item.get("public_detail",{}).get("title"),
    "body":item.get("public_detail",{}).get("text","")[:5100]},ensure_ascii=False)[:6000],flush=True)
   if blocked:state["stop"]="HTTP_403_429";break
  await browser.close()
 state["summary"]={"source_original_ad_links":len(data["records"]),
  "details_http200":sum(x.get("http")==200 for x in state["records"]),
  "master_writes":0}
 save()
 print("SAE_KETAF_SOURCE_SUMMARY",json.dumps(state["summary"]),flush=True)
if __name__=="__main__":asyncio.run(main())
