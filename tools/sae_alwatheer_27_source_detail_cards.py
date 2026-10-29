#!/usr/bin/env python3
"""27 independently linked public Jazan land plot details, EXISTING PRJ-001017.

Original publisher index already archived (43 cards: 41 genuine numbered
parcels, 2 mosque/garden). Fetch ONLY 27 source-linked parcel URLs absent from
canonical Master; preserve exact source code, area, asking, status. READ ONLY.
"""
import asyncio,hashlib,json,re,urllib.request,urllib.robotparser
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
from playwright.async_api import async_playwright
MANIFEST=Path("tools/sae_alwatheer_original_plot_manifest_20261030.json")
OUT=Path("sae-alwatheer-27-original-public-details.json")
HOST="www.albaytalwathir.com"
UA="SAE-DB-original-verified-existing-land-parcels/1.0"
DOC={"schema":"SAE_ALWATHEER_27_ORIGINALLY_NUMBERED_PUBLIC_LAND_PLOT_DETAIL_CAPTURE_V1",
     "utc":datetime.now(timezone.utc).isoformat(),"source_only":True,"master_writes":0,
     "source_id":"SRC-000114","canonical_project_id":"PRJ-001017",
     "details":[],"errors":[],"status":"STARTED"}
def robots():
 with urllib.request.urlopen(urllib.request.Request("https://"+HOST+"/robots.txt",headers={"User-Agent":UA}),timeout=15) as f:
  if f.status!=200:raise RuntimeError("ROBOTS_NOT_200")
  b=f.read(180001)
 if len(b)>180000:raise RuntimeError("ROBOTS_TOO_LARGE")
 rp=urllib.robotparser.RobotFileParser();rp.parse(b.decode("utf8","replace").splitlines())
 return rp
def save():
 t=OUT.with_suffix(".tmp")
 t.write_text(json.dumps(DOC,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 t.replace(OUT)
def verify_manifest():
 m=json.loads(MANIFEST.read_text(encoding="utf8"))
 assert m["canonical_existing_project_id"]=="PRJ-001017" and m["publisher_original_project_id"]=="301871"
 selected=[r for r in m["records"] if r["classification"]=="INDIVIDUAL_LAND_PARCEL" and not r["already_in_canonical"]]
 if len(selected)!=27:raise RuntimeError("EXPECTED_EXACT_27")
 seen_codes=set();seen_urls=set()
 for r in selected:
  u=urlsplit(r["original_property_url"])
  if u.scheme!="https" or u.hostname!=HOST or u.query!="projectId=301871" or u.path!="/en/properties/"+r["original_property_id"]:
   raise RuntimeError("UNVERIFIED_SOURCE_DETAIL_URL")
  if not re.fullmatch(r"\d{1,3}",r["original_unit_code"]) or r["original_unit_code"] in seen_codes or u.path in seen_urls:
   raise RuntimeError("DUPLICATE_OR_UNVERIFIED_ORIGINAL_CODE")
  seen_urls.add(u.path);seen_codes.add(r["original_unit_code"])
 return selected

async def main():
 sources=verify_manifest()
 try:rp=await asyncio.to_thread(robots)
 except Exception as e:
  DOC["status"]="ROBOTS_NOT_VERIFIED_"+type(e).__name__;save();return
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  for i,item in enumerate(sources):
   url=item["original_property_url"];pid=item["original_property_id"]
   detail={"original_property_url":url,"original_source_id":pid,
           "original_publisher_parcel_code":item["original_unit_code"],
           "canonical_existing_project_id":"PRJ-001017","status":"STARTED","errors":[]}
   DOC["details"].append(detail)
   if not rp.can_fetch(UA,url):
    detail["status"]="ROBOTS_DENY_DETAIL";save();continue
   page=await browser.new_page(user_agent=UA,viewport={"width":1280,"height":960})
   stop=False
   def mark(resp):
    nonlocal stop
    if urlsplit(resp.url).hostname==HOST and resp.status in (403,429):
     stop=True;detail["errors"].append("SOURCE_HTTP_"+str(resp.status))
   page.on("response",mark)
   try:
    await asyncio.sleep(1.25)
    resp=await page.goto(url,wait_until="domcontentloaded",timeout=32000)
    detail["http"]=resp.status if resp else None
    if resp and resp.status==200 and not stop:
     await page.wait_for_timeout(750)
     state=await page.evaluate("""() => ({
       title:document.title,body:(document.body.innerText||'').slice(0,13000),
       h1:[...document.querySelectorAll('h1,h2,h3')].map(x=>x.innerText.trim()).filter(Boolean).slice(0,17),
       propertyData:[...document.querySelectorAll('tr,[class*=detail],[class*=price],[class*=area]')].slice(0,50).map(x=>x.innerText?.slice(0,260)).filter(Boolean),
       jsonLD:[...document.querySelectorAll('script[type="application/ld+json"]')].map(x=>x.textContent.slice(0,5000)).slice(0,3)
     })""")
     detail["source"]=state
     detail["status"]="EXACT_ORIGINAL_SOURCE_DETAIL_CAPTURED"
    else:detail["status"]="SOURCE_HTTP_STOP"
   except Exception as exc:
    detail["errors"].append(type(exc).__name__+":"+str(exc)[:100])
    detail["status"]="SOURCE_ERROR"
   await page.close()
   print("SAE_WATHEER_PLOT_DETAIL",json.dumps({
    "source_property_id":pid,"original_plot_code":item["original_unit_code"],
    "http":detail.get("http"),"status":detail["status"],
    "title":detail.get("source",{}).get("title"),"headings":detail.get("source",{}).get("h1"),
    "body_excerpt":detail.get("source",{}).get("body","")[:4300],
    "errors":detail["errors"]
   },ensure_ascii=False,separators=(",",":"))[:5500],flush=True)
   save()
   if stop:
    DOC["status"]="SOURCE_403_OR_429_GLOBAL_STOP";break
  await browser.close()
 DOC["status"]=DOC["status"] if DOC["status"]!="STARTED" else "SOURCE_ONLY_CAPTURE_COMPLETED"
 save()
 print("SAE_WATHEER_PLOT_SUMMARY",json.dumps({"scanned":len(DOC["details"]),"http200":sum(x.get("http")==200 for x in DOC["details"]),
   "url_codes":len({x["original_publisher_parcel_code"] for x in DOC["details"]}),"state":DOC["status"]},ensure_ascii=False),flush=True)
if __name__=="__main__":asyncio.run(main())
