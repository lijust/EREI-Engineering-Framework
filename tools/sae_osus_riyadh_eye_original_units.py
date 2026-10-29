#!/usr/bin/env python3
"""Exact original developer OSUS Eye public unit cards; read-only, no synthetic inventory."""
import asyncio,json,re,hashlib,urllib.request,urllib.robotparser
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from playwright.async_api import async_playwright
URL="https://osus.com.sa/en/properties-listing/"
UA="SAE-DB-OSUS-Riyadh-original-unit-inventory/1.0"
OUT=Path("sae-osus-riyadh-original-unit-inventory.json")
D={"schema":"SAE_OSUS_RIYADH_EYE_ORIGINAL_PUBLIC_UNIT_INVENTORY_V1","source_page":URL,"canonical_project_candidate":"PRJ-000336","utc":datetime.now(timezone.utc).isoformat(),"sheet_writes":0,"responses":[]}
def check():
 rp=urllib.robotparser.RobotFileParser()
 with urllib.request.urlopen(urllib.request.Request("https://osus.com.sa/robots.txt",headers={"User-Agent":UA}),timeout=18) as r:
  if r.status!=200:raise RuntimeError("robots status "+str(r.status))
  rp.parse(r.read(170000).decode("utf-8","replace").splitlines())
 return rp.can_fetch(UA,URL)
async def main():
 try:allowed=await asyncio.to_thread(check)
 except Exception as e:D["stop"]="ROBOTS_UNVERIFIED_"+type(e).__name__;OUT.write_text(json.dumps(D));return
 if not allowed:D["stop"]="ROBOTS_DISALLOW";OUT.write_text(json.dumps(D));return
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True)
  page=await b.new_page(user_agent=UA,viewport={"width":1400,"height":950})
  jobs=[];blocked=False
  async def cap(r):
   nonlocal blocked
   host=urlsplit(r.url).hostname or ""
   if host.endswith("osus.com.sa") and r.status in (403,429):blocked=True;return
   if r.status!=200 or len(D["responses"])>=70:return
   if r.request.resource_type not in ("xhr","fetch") and "json" not in r.headers.get("content-type",""):return
   try:
    content=await r.body()
    if len(content)>6000000:return
    item={"url":r.url,"sha256":hashlib.sha256(content).hexdigest(),"bytes":len(content),"content_type":r.headers.get("content-type","")}
    if b"OE/" in content or b"OSUS EYE" in content or b"osus eye" in content.lower():
     item["original_response_excerpt"]=content[:1500000].decode("utf-8","replace")
    D["responses"].append(item)
   except Exception as e:D.setdefault("errors",[]).append(type(e).__name__)
  page.on("response",lambda r:jobs.append(asyncio.create_task(cap(r))))
  try:
   r=await page.goto(URL,wait_until="domcontentloaded",timeout=45000)
   D["http"]=r.status if r else None
   if r and r.status==200 and not blocked:
    await page.wait_for_timeout(6500)
    D["page_title"]=await page.title()
    D["initial"]=await page.evaluate("""() => ({text:(document.body?.innerText||"").slice(0,6000),links:[...document.querySelectorAll('a[href]')].filter(x=>/OE\\/|property|details/i.test(x.innerText+' '+x.href)).map(x=>({text:x.innerText.trim().slice(0,160),href:x.href})).slice(0,80)})""")
    for i in range(20):
     if blocked:break
     before=await page.locator("body").inner_text()
     await page.evaluate("window.scrollTo(0,document.body.scrollHeight)")
     await page.wait_for_timeout(550)
     after=await page.locator("body").inner_text()
     D["scroll_steps"]=i+1
     if i>3 and len(after)==len(before):break
    D["final_body"]=await page.locator("body").inner_text()
    D["final_links"]=await page.locator("a[href]").evaluate_all("""x=>x.filter(a=>/OE\\/|property|details/i.test(a.innerText+' '+a.href)).map(a=>({text:a.innerText.trim().slice(0,200),href:a.href})).slice(0,1500)""")
    D["visible_oe_codes"]=sorted(set(re.findall(r"OE/[A-Z0-9/\\-]+",D["final_body"])))
    D["counts"]={"codes":len(D["visible_oe_codes"]),"links":len(D["final_links"]),"chars":len(D["final_body"]),"xhr":len(D["responses"])}
  except Exception as e:D["error"]=type(e).__name__+":"+str(e)[:250]
  if jobs:await asyncio.gather(*jobs,return_exceptions=True)
  D["blocked"]=blocked
  OUT.write_text(json.dumps(D,ensure_ascii=False,indent=2)+"\n")
  print("OSUS_RIYADH_SOURCE",json.dumps({k:D.get(k) for k in ("http","counts","visible_oe_codes","error","blocked","stop")},ensure_ascii=False),flush=True)
  await page.close();await b.close()
if __name__=="__main__":asyncio.run(main())
