#!/usr/bin/env python3
"""SAE source-only per-unit discovery for existing canonical Saudi projects.

Direct publisher pages via public UI; does not bypass 403/429 or login.
Do not synthesize numbered records from project aggregate totals.
"""
import asyncio, json, urllib.parse, urllib.request, urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright
PROJECTS=[
 ("PRJ-000333","https://www.alomarinvest.sa/ar/projects/301526"),
 ("PRJ-001075","https://www.alolayanholding.sa/projects/301568"),
 ("PRJ-001822","https://www.senanrealestate.sa/projects/301371"),
 ("PRJ-001823","https://www.senanrealestate.sa/projects/301368")
]
UA="SAE-DB-research-public-unit-source/1.0"
def robots(url):
 u=urllib.parse.urlsplit(url)
 with urllib.request.urlopen(urllib.request.Request(f"{u.scheme}://{u.netloc}/robots.txt",headers={"User-Agent":UA}),timeout=14) as r:
  if r.status!=200:return False,"ROBOTS_HTTP_"+str(r.status)
  rp=urllib.robotparser.RobotFileParser()
  rp.parse(r.read(200000).decode("utf8","replace").splitlines())
  return rp.can_fetch(UA,url),"CHECKED"
async def inspect(page):
 return await page.evaluate("""() => {
 const mark=[...document.querySelectorAll('h2,h3,h4,div')].find(x=>/^وحدات المشروع\\s*\\d+/.test(x.innerText.trim())&&x.innerText.trim().length<45);
 const t=[...document.querySelectorAll('table')].map(x=>({html:x.outerHTML.slice(0,1500),rows:[...x.querySelectorAll('tr')].map(r=>r.innerText.trim().slice(0,200))})).slice(0,3);
 const buttons=[...document.querySelectorAll('button')].map(x=>({text:x.innerText.trim().slice(0,80),aria:x.getAttribute('aria-label'),disabled:x.disabled,html:x.outerHTML.slice(0,350)})).filter(x=>x.text||x.aria).slice(-75);
 const links=[...document.querySelectorAll('a[href]')].filter(x=>/وحدة|تاون هاوس|مباعة|الشقة|تفاصيل|الوحدات/i.test(x.innerText)).slice(0,20).map(x=>({text:x.innerText.trim().slice(0,60),url:x.href}));
 return {url:location.href,title:document.title,marker:mark?.innerText.trim().slice(0,80),tables:t,buttons,links,
 body_tail:(document.body.innerText||'').slice(-8500)};
}""")
async def main():
 out={"schema":"SAE_EXISTING_PROJECTS_NUZUL_PAGINATION_READONLY_V1","utc":datetime.now(timezone.utc).isoformat(),"writes":0,"projects":[]}
 async with async_playwright() as pw:
  browser=await pw.chromium.launch()
  for pid,url in PROJECTS:
   rec={"id":pid,"url":url,"snapshots":[],"responses":[]}
   try:
    permit,rob=await asyncio.to_thread(robots,url)
    rec["robots"]={"allowed":permit,"result":rob}
    if not permit:
     out["projects"].append(rec);continue
    page=await browser.new_page(user_agent=UA,viewport={"width":1280,"height":900})
    tasks=[]
    async def capture(r):
     if r.status in (403,429) and urllib.parse.urlsplit(r.url).hostname==urllib.parse.urlsplit(url).hostname:
      rec["blocked"]=r.status
     if r.request.resource_type not in ("fetch","xhr"):return
     try:
      body=await r.body()
      if len(rec["responses"])<75:
       rec["responses"].append({"status":r.status,"url":r.url,"bytes":len(body),"sample":body[:250].decode("utf8","replace")})
     except Exception:pass
    page.on("response",lambda r:tasks.append(asyncio.create_task(capture(r))))
    try:
     first=await page.goto(url,wait_until="domcontentloaded",timeout=35000)
     rec["http"]=first.status if first else None
     if first and first.status not in (403,429):
      await page.wait_for_timeout(2700)
      rec["snapshots"].append({"stage":"initial",**(await inspect(page))})
      # Pagination: click public page 2 only when original source UI has it.
      paging=page.get_by_role("button",name="2",exact=True)
      if await paging.count()>0:
       await paging.first.click(timeout=6000)
       await page.wait_for_timeout(2200)
       rec["snapshots"].append({"stage":"page2",**(await inspect(page))})
    except Exception as ex:rec.setdefault("errors",[]).append(str(ex)[:200])
    if tasks:await asyncio.gather(*tasks,return_exceptions=True)
    await page.close()
   except Exception as ex:rec.setdefault("errors",[]).append("robots_or_browser_"+str(ex)[:190])
   out["projects"].append(rec)
   Path("sae-nuzul-pagination-public-source.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
   print(pid,"status",rec.get("http"),"snapshots",len(rec["snapshots"]),"xhr",len(rec["responses"]),"blocked",rec.get("blocked"),flush=True)
  await browser.close()
if __name__=="__main__":asyncio.run(main())
