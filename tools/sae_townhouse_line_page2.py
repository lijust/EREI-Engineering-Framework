#!/usr/bin/env python3
"""Capture exact original numbered townhouses on public project page 2."""
import asyncio,json,urllib.request,urllib.robotparser
from datetime import datetime,timezone
from pathlib import Path
from playwright.async_api import async_playwright
URL="https://www.alolayanholding.sa/projects/301568"
UA="SAE-DB-public-unit-evidence/1.0"
async def main():
 out={"schema":"SAE_TOWNHOUSE_LINE_PUBLIC_PAGE_2_EXACT_UNITS","project_id":"PRJ-001075","captured_utc":datetime.now(timezone.utc).isoformat(),"source":URL,"writes":0,"snapshots":[]}
 with urllib.request.urlopen(urllib.request.Request("https://www.alolayanholding.sa/robots.txt",headers={"User-Agent":UA}),timeout=18) as f:
  rp=urllib.robotparser.RobotFileParser();rp.parse(f.read(250000).decode("utf8","replace").splitlines())
 if not rp.can_fetch(UA,URL):
  out["status"]="ROBOTS_DENIED"
 else:
  async with async_playwright() as p:
   browser=await p.chromium.launch()
   page=await browser.new_page(user_agent=UA)
   res=await page.goto(URL,wait_until="domcontentloaded",timeout=45000)
   out["http_status"]=res.status
   if res.status not in (403,429):
    await page.wait_for_timeout(1600)
    out["paging_buttons"]=await page.locator("button").evaluate_all("""els=>els.filter(e=>/صفحة 2|الصفحة التالية/.test(e.getAttribute('aria-label')||'')).map(e=>e.outerHTML.slice(0,550))""")
    async def table():
     return await page.locator("table").evaluate_all("""tables=>tables.map(t=>({headers:[...t.querySelectorAll('th')].map(q=>q.innerText.trim()),rows:[...t.querySelectorAll('tbody tr')].map(q=>({cells:[...q.querySelectorAll('td')].map(c=>c.innerText.trim()),links:[...q.querySelectorAll('a[href]')].map(a=>({url:a.href,text:a.innerText.trim()}))}))}))""")
    out["snapshots"].append({"stage":"page1","table":await table()})
    btn=page.locator('button[aria-label*="صفحة 2"]')
    out["page2_button_count"]=await btn.count()
    if await btn.count()>0:
     await btn.first.click(timeout=8500)
     await page.wait_for_timeout(1700)
     out["snapshots"].append({"stage":"page2","table":await table(),"url":page.url})
    else:out["status"]="PAGINATION_BUTTON_NOT_FOUND"
   await browser.close()
 Path("sae-townhouse-line-exact-page2.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
 print("SAE_TOWNHOUSE_LINE_PUBLIC_EXACT_SOURCE="+json.dumps(out,ensure_ascii=False,separators=(",",":")),flush=True)
if __name__=="__main__":asyncio.run(main())
