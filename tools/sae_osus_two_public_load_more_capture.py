#!/usr/bin/env python3
"""SAE-DB source-only Osus original public load-more grid probe.
Two VERIFIED existing canonical projects; no database writes or invented units.
"""
import asyncio,json,re,urllib.request,urllib.robotparser
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from playwright.async_api import async_playwright
SEEDS=[
 ("PRJ-001140","https://osuse.sa/project/4f129c5b-c9f8-44f0-a175-1a97479b100c"),
 ("PRJ-001139","https://osuse.sa/project/b6f90000-c504-42be-8801-78322eb4667a")
]
UA="SAE-DB-public-collection/1.0"
OUT=Path("sae-osus-existing-two-unit-grid-capture.json")
result={"schema":"SAE_DB_OSUS_EXISTING_TWO_SOURCE_UNIT_GRIDS_V1","utc":datetime.now(timezone.utc).isoformat(),"source_only":True,"master_writes":0,"rows":[]}
def save():
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def robots(url):
 u=urlsplit(url); rp=urllib.robotparser.RobotFileParser()
 with urllib.request.urlopen(urllib.request.Request(f"{u.scheme}://{u.netloc}/robots.txt",headers={"User-Agent":UA}),timeout=18) as r:
  if r.status!=200:return False,"robots_status_"+str(r.status)
  content=r.read(200001)
 if len(content)>200000:return False,"robots_oversize"
 rp.parse(content.decode("utf-8","replace").splitlines())
 return rp.can_fetch(UA,url),"robots_verified"
async def run_one(browser,pid,url):
 row={"project_id":pid,"original_url":url,"errors":[],"clicks":0,"capture_utc":datetime.now(timezone.utc).isoformat()}
 try:
  allowed,reason=await asyncio.to_thread(robots,url)
 except Exception as e:allowed=False;reason="robots_unverified_"+type(e).__name__
 row["robots"]=reason;row["allowed"]=allowed
 if not allowed:return row
 page=await browser.new_page(user_agent=UA,viewport={"width":1366,"height":900})
 blocked=False
 def stop_check(response):
  nonlocal blocked
  host=urlsplit(response.url).hostname or ""
  if host=="osuse.sa" or host.endswith(".osuse.sa"):
   if response.status in (403,429):blocked=True;row["errors"].append("SOURCE_ACCESS_"+str(response.status))
 page.on("response",stop_check)
 try:
  r=await page.goto(url,wait_until="domcontentloaded",timeout=45000)
  row["http"]=r.status if r else None
  if not r or r.status in (403,429):blocked=True
  if blocked:return row
  await page.wait_for_timeout(2500)
  row["initial_structure"]=await page.evaluate("""() => {
    const a=[...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(e=>(e.innerText||'').includes('الوحدة')).slice(0,8);
    return {headings:a.map(e=>({tag:e.tagName,text:e.innerText,html:e.parentElement?.parentElement?.outerHTML.slice(0,3000)})),
      buttons:[...document.querySelectorAll('button')].filter(x=>/المزيد|الكل|المتاحة/.test(x.innerText)).slice(0,12).map(x=>({text:x.innerText,html:x.outerHTML.slice(0,500)})),
      text_len:(document.body.innerText||'').length}
  }""")
  more=page.get_by_role("button",name=re.compile("المزيد"))
  for k in range(80):
   if blocked:break
   if await more.count()==0:break
   item=more.first
   if not await item.is_visible():break
   before=await page.locator("body").inner_text()
   try:await item.click(timeout=3500)
   except Exception as e:row["errors"].append("click_"+type(e).__name__);break
   await page.wait_for_timeout(160)
   after=await page.locator("body").inner_text()
   row["clicks"]+=1
   if len(after)<=len(before):
    row["errors"].append("no_new_public_text_click_"+str(k))
    break
  row["blocked"]=blocked
  row["final_text"]=await page.locator("body").inner_text()
  row["final_structure"]=await page.evaluate("""() => ({
    headings:[...document.querySelectorAll('h2,h3,h4,h5,h6')].filter(e=>/^\\s*الوحدة[\\s\\u00a0]+/u.test(e.innerText||'')).length,
    button_labels:[...document.querySelectorAll('button')].filter(x=>/المزيد/.test(x.innerText||'')).map(x=>x.innerText),
    body_length:(document.body?.innerText||'').length
  })""")
  row["units_text_span"]=row["final_text"].split("## الوحدات المتاحة")[-1].split("إجمالي الوحدات")[0][:1000]
  print("OSUS_PROJECT",json.dumps({k:row.get(k) for k in ("project_id","http","clicks","blocked","final_structure","errors")},ensure_ascii=False),flush=True)
 except Exception as e:row["errors"].append("page_"+type(e).__name__+":"+str(e)[:160])
 finally:await page.close()
 return row
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True)
  for pid,url in SEEDS:
   row=await run_one(browser,pid,url)
   result["rows"].append(row);save()
   print("SOURCE_RESULT",pid,row.get("http"),row.get("robots"),"clicks",row.get("clicks"),"chars",len(row.get("final_text","")),"errors",row.get("errors",[])[:4],flush=True)
   if row.get("blocked"):break
  await browser.close()
if __name__=="__main__":asyncio.run(main())
