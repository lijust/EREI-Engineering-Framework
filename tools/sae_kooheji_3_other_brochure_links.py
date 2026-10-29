#!/usr/bin/env python3
"""Source-only original PDF discovery for THREE existing Kooheji projects."""
import asyncio,json,urllib.request,urllib.robotparser
from datetime import datetime,timezone
from pathlib import Path
from playwright.async_api import async_playwright
BASE="https://koohejidevelopment.sa"
PAGES=[BASE+"/community/belgravia/",BASE+"/community/flamant/",BASE+"/community/vellano/"]
UA="SAE-DB-three-current-community-original-pdfs/1.0"
OUT=Path("sae-kooheji-three-existing-brochure-links.json")
DATA={"canonical_project_by_url":{"belgravia":"PRJ-001212","flamant":"PRJ-001213","vellano":"PRJ-001215"},"source_id":"SRC-000081","utc":datetime.now(timezone.utc).isoformat(),"production_writes":0,"pages":[]}
def robots():
 rp=urllib.robotparser.RobotFileParser()
 with urllib.request.urlopen(urllib.request.Request(BASE+"/robots.txt",headers={"User-Agent":UA}),timeout=15) as res:
  if res.status!=200:raise ValueError("robots HTTP")
  rp.parse(res.read(160000).decode("utf-8","replace").splitlines())
 return rp
DOM=r"""() => ({
 title:document.title,
 original_source_links:[...document.querySelectorAll('a[href]')].map(x=>({href:x.href,text:(x.innerText||'').trim().slice(0,85),
   title:x.getAttribute('title'),download:x.getAttribute('download'),onclick:x.getAttribute('onclick')}))
  .filter(x=>/brochure|floor plan|download|كتيب|تحميل|\.pdf|site.plan|المخطط/i.test(x.href+' '+x.text+' '+x.title)).slice(0,80),
 relevant_buttons:[...document.querySelectorAll('button,[role="button"],a')].filter(x=>/download|brochure|floor plan|كتيب|تحميل/i.test(x.innerText||'')).slice(0,35)
   .map(x=>({html:x.outerHTML.slice(0,1100),text:(x.innerText||'').slice(0,80)})),
 original_pdf_embeds:[...document.querySelectorAll('iframe[src],embed[src],object[data]')].map(x=>x.src||x.data).filter(x=>x&&/\.pdf|uploads/i.test(x)).slice(0,30)
})"""
async def main():
 try:rp=await asyncio.to_thread(robots)
 except Exception as e:
  DATA["state"]="ROBOTS_UNVERIFIED_"+type(e).__name__;OUT.write_text(json.dumps(DATA,ensure_ascii=False,indent=2));return
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  for url in PAGES:
   item={"url":url,"time":datetime.now(timezone.utc).isoformat(),"errors":[]}
   if not rp.can_fetch(UA,url):
    item["state"]="ROBOTS_DISALLOW";DATA["pages"].append(item);continue
   page=await browser.new_page(user_agent=UA)
   blocked=False
   def mark(r):
    nonlocal blocked
    if "koohejidevelopment.sa" in r.url and r.status in (403,429):blocked=True
   page.on("response",mark)
   try:
    res=await page.goto(url,wait_until="domcontentloaded",timeout=40000)
    item["http"]=res.status if res else None
    if not blocked and item["http"]==200:
     await page.wait_for_timeout(1800)
     item["dom"]=await page.evaluate(DOM)
    else:item["state"]="ACCESS_STOP"
   except Exception as e:item["errors"].append(type(e).__name__)
   await page.close();DATA["pages"].append(item)
   OUT.write_text(json.dumps(DATA,ensure_ascii=False,indent=2))
   print("KOOHEJI_THREE_LINKS",json.dumps({"page":url,"status":item.get("http"),"links":item.get("dom",{}).get("original_source_links",[]),"buttons":item.get("dom",{}).get("relevant_buttons",[])[:3]},ensure_ascii=False),flush=True)
   if blocked:break
  await browser.close()
if __name__=="__main__":asyncio.run(main())
