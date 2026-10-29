#!/usr/bin/env python3
"""SAE source-only RAFah exact published apartment grid discovery.

Only project 40/50/56/57 that already exist in canonical SAE-DB.
Parses public original developer HTML tables; no external site writes.
"""
import asyncio,json,urllib.request,urllib.robotparser,urllib.parse
from datetime import datetime,timezone
from pathlib import Path
from playwright.async_api import async_playwright

PAGES=[("PRJ-001125","40"),("PRJ-001126","50"),("PRJ-001127","56"),("PRJ-001128","57")]
UA="SAE-DB-original-source-research/1.0"
def allow(url):
 p=urllib.parse.urlsplit(url)
 req=urllib.request.Request(f"{p.scheme}://{p.netloc}/robots.txt",headers={"User-Agent":UA})
 with urllib.request.urlopen(req,timeout=15) as r:
  if r.status!=200:return False,"ROBOTS_UNVERIFIED_NON200"
  rp=urllib.robotparser.RobotFileParser()
  rp.parse(r.read(180000).decode("utf8","replace").splitlines())
  return rp.can_fetch(UA,url),"ROBOTS_READ"
async def visit(browser,id,num):
 url=f"https://rafah.sa/projects/{num}/"
 result={"project_id":id,"project_number":num,"url":url,"tables":[],"resources":[]}
 try:ok,why=await asyncio.to_thread(allow,url)
 except Exception as exc:ok=False;why="ROBOTS_UNKNOWN_"+type(exc).__name__
 result["robots"]={"checked":why,"allowed":ok}
 if not ok:return result
 page=await browser.new_page(user_agent=UA)
 pending=[]
 async def collect(resp):
  if resp.status in (403,429) and "rafah.sa" in resp.url:
   result.setdefault("access_denied",[]).append([resp.status,resp.url[:160]])
  if resp.request.resource_type in ("xhr","fetch") and len(result["resources"])<40:
   try:
    body=await resp.body()
    result["resources"].append({"url":resp.url,"status":resp.status,"size":len(body),
       "contentType":resp.headers.get("content-type",""),
       "sample":body[:200].decode("utf8","replace")})
   except Exception:pass
 page.on("response",lambda r:pending.append(asyncio.create_task(collect(r))))
 try:
  response=await page.goto(url,wait_until="domcontentloaded",timeout=40000)
  result["status_code"]=response.status if response else None
  if result["status_code"] not in (403,429):
   await page.wait_for_timeout(2200)
   result["title"]=await page.title()
   result["tables"]=await page.locator("table").evaluate_all("""els=>els.map((t,k)=>({
      tableIndex:k,classes:t.className,headerText:[...t.querySelectorAll('th')].map(x=>x.innerText.trim()),
      rows:[...t.querySelectorAll('tr')].map((r,j)=>({index:j,html:r.outerHTML.slice(0,1300),
        cells:[...r.querySelectorAll('th,td')].map(c=>({text:c.innerText.trim().slice(0,250),html:c.outerHTML.slice(0,550)}))})).slice(0,120)
    }))""")
   result["body_snippet"]=await page.locator("body").inner_text()
   result["body_snippet"]=result["body_snippet"][:1200]
 except Exception as e:result.setdefault("errors",[]).append(type(e).__name__+":"+str(e)[:250])
 if pending:await asyncio.gather(*pending,return_exceptions=True)
 await page.close()
 return result

async def main():
 out={"schema":"SAE_RAFFAH_FOUR_EXISTING_PROJECT_ORIGINAL_APARTMENT_TABLES_V1",
      "captured_utc":datetime.now(timezone.utc).isoformat(),"production_writes":0,"projects":[]}
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  for id,num in PAGES:
   rec=await visit(browser,id,num)
   out["projects"].append(rec)
   Path("sae-raffah-four-original-unit-tables.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
   print(id,"HTTP",rec.get("status_code"),"tables",len(rec["tables"]),"rows",sum(len(x["rows"]) for x in rec["tables"]),flush=True)
  await browser.close()
if __name__=="__main__":asyncio.run(main())
