#!/usr/bin/env python3
"""SAE-DB: inspect 4 original Modn project unit-price tables, read only."""
import asyncio,json,urllib.request,urllib.robotparser
from pathlib import Path
from datetime import datetime,timezone
from playwright.async_api import async_playwright
ROOT="https://modn-alshmal.sa"
SEEDS=[("PRJ-001129",ROOT+"/property/modn-12/"),
       ("PRJ-001130",ROOT+"/property/modn-13/"),
       ("PRJ-001132",ROOT+"/property/modn-15/"),
       ("PRJ-001133",ROOT+"/property/modn18/")]
UA="SAE-DB-original-modn-unit-table-study/1.0"
OUT=Path("sae-modn-four-native-tables-source.json")
DATA={"schema":"SAE_MODN_FOUR_EXISTING_ORIGINAL_TABULAR_UNITS_SOURCE_V1","records":[],"writes":0,"utc":datetime.now(timezone.utc).isoformat()}
def check():
 rp=urllib.robotparser.RobotFileParser()
 with urllib.request.urlopen(urllib.request.Request(ROOT+"/robots.txt",headers={"User-Agent":UA}),timeout=15) as f:
  if f.status!=200:raise RuntimeError("robots not 200")
  rp.parse(f.read(150000).decode("utf-8","replace").splitlines())
 return rp
DOM=r"""() => {
 const tables=[...document.querySelectorAll('table')];
 const rows=tables.map((t,i)=>({index:i,headers:[...t.querySelectorAll('thead th')].map(x=>x.innerText.trim()),
  data:[...t.querySelectorAll('tbody tr')].slice(0,350).map(x=>({text:x.innerText.trim().slice(0,650),cells:[...x.querySelectorAll('td')].map(y=>y.innerText.trim())}))}));
 const dyn=[...document.querySelectorAll('[data-unit],[data-unit-id],[data-unit-code],[data-building]')].slice(0,150).map(x=>({tag:x.tagName,html:x.outerHTML.slice(0,350)}));
 const inputs=[...document.querySelectorAll('select,input')].filter(x=>/الوحدة|السعر|unit|price|building/i.test(x.outerHTML)).slice(0,60).map(x=>x.outerHTML.slice(0,300));
 return {title:document.title,table_count:tables.length,tables:rows,unit_nodes:dyn,inputs,html_units:[...document.querySelectorAll('h3,h4,h5')].filter(x=>/رقم الوحدة|رقم الشقة/.test(x.innerText)).slice(0,40).map(x=>x.parentElement?.outerHTML.slice(0,800)),page_text:(document.body?.innerText||'').slice(0,9000)};
}"""
async def main():
 try:rp=await asyncio.to_thread(check)
 except Exception as e:
  DATA["stop"]="ROBOTS_UNVERIFIED_"+type(e).__name__;OUT.write_text(json.dumps(DATA,ensure_ascii=False,indent=2));return
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  for pid,url in SEEDS:
   row={"project_id":pid,"official_url":url,"capture_utc":datetime.now(timezone.utc).isoformat(),"errors":[]}
   if not rp.can_fetch(UA,url):
    row["state"]="ROBOTS_DISALLOW";DATA["records"].append(row);continue
   page=await browser.new_page(user_agent=UA)
   blocked=False
   def stop(resp):
    nonlocal blocked
    if "modn-alshmal.sa" in resp.url and resp.status in (403,429):blocked=True
   page.on("response",stop)
   try:
    res=await page.goto(url,wait_until="domcontentloaded",timeout=35000)
    row["http"]=res.status if res else None
    if not blocked and row["http"]==200:
     await page.wait_for_timeout(2500)
     row["source_dom"]=await page.evaluate(DOM)
     row["state"]="SOURCE_CAPTURED"
    else:row["state"]="ACCESS_BLOCKED"
   except Exception as e:row["state"]="PAGE_ERROR";row["errors"].append(type(e).__name__)
   await page.close()
   DATA["records"].append(row)
   OUT.write_text(json.dumps(DATA,ensure_ascii=False,indent=2))
   print("MODN_TABLE",json.dumps({"pid":pid,"state":row["state"],"http":row.get("http"),"tables":len(row.get("source_dom",{}).get("tables",[])),"table_rows":sum(len(x["data"]) for x in row.get("source_dom",{}).get("tables",[])),"headers":[x["headers"] for x in row.get("source_dom",{}).get("tables",[])]},ensure_ascii=False),flush=True)
   if blocked:break
  await browser.close()
if __name__=="__main__":asyncio.run(main())
