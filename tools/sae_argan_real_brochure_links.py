#!/usr/bin/env python3
"""SAE source-only: discover actual embedded PDF flipbook URLs on four original
Alargan existing project pages. No login, no inventory guesses, no writes.
"""
import asyncio,json,re,urllib.request,urllib.robotparser,urllib.parse
from datetime import datetime,timezone
from pathlib import Path
from playwright.async_api import async_playwright
TARGETS=[
("PRJ-001483","https://alargan.com.sa/fursan/"),
("PRJ-001487","https://alargan.com.sa/suhool/"),
("PRJ-001484","https://alargan.com.sa/green-oasis/"),
("PRJ-001491","https://alargan.com.sa/murjana/")
]
UA="SAE-DB-public-source-study/1.0"
def robots(url):
 p=urllib.parse.urlsplit(url)
 with urllib.request.urlopen(urllib.request.Request(f"{p.scheme}://{p.netloc}/robots.txt",headers={"User-Agent":UA}),timeout=15) as r:
  if r.status!=200:return False
  rp=urllib.robotparser.RobotFileParser()
  rp.parse(r.read(250000).decode("utf-8","replace").splitlines())
 return rp.can_fetch(UA,url)
async def scan(browser,id,url):
 result={"project":id,"url":url,"captures":[]}
 try:result["robots"]=await asyncio.to_thread(robots,url)
 except Exception as e:result["robots_error"]=str(e);result["robots"]=False
 if not result["robots"]:return result
 page=await browser.new_page(user_agent=UA)
 tasks=[]
 async def resp(r):
  if r.status in (403,429) and "alargan.com.sa" in r.url:
   result.setdefault("access_blocked",[]).append([r.status,r.url[:170]])
  if r.request.resource_type not in ("document","xhr","fetch"):return
  if len(result["captures"])>=35:return
  try:
   body=await r.body()
   text=body.decode("utf-8","replace")
   links=re.findall(r'https?[^\s"\']{6,400}\.(?:pdf|PDF)(?:\?[^\s"\']{0,100})?',text,re.I)
   attrs=re.findall(r'(?:data-pdf|data-source|data-url|data-book-id|data-bookid|src)=[\'"]([^\'"]{2,400})',text,re.I)
   flip=re.findall(r'.{0,120}(?:dflip|flipbook|\.pdf|\.PDF|[23]d-flip-book).{0,180}',text,re.I)[:50]
   if links or flip:
    result["captures"].append({"kind":r.request.resource_type,"url":r.url,"status":r.status,"links":links[:40],"attributes":attrs[:30],"html_contexts":flip[:20]})
  except Exception as e:result.setdefault("errors",[]).append("response:"+type(e).__name__)
 page.on("response",lambda r:tasks.append(asyncio.create_task(resp(r))))
 try:
  rs=await page.goto(url,wait_until="domcontentloaded",timeout=30000)
  result["main_status"]=rs.status if rs else None
  if result["main_status"] not in (403,429):
   await page.wait_for_timeout(2800)
   result["links"]=await page.locator("a[href]").evaluate_all("""es=>es.filter(x=>/brochure|flipbook|\.pdf|كتيب/i.test(x.href+' '+x.innerText)).map(x=>({text:x.innerText.slice(0,90),href:x.href})).slice(0,40)""")
   result["flip_elements"]=await page.locator('[class*="flip"],[data-pdf],[data-book-id],[data-source]').evaluate_all("""es=>es.slice(0,50).map(x=>({tag:x.tagName,id:x.id,classes:x.className,html:x.outerHTML.slice(0,650)}))""")
   result["pdf_embeds"]=await page.locator('iframe[src],embed[src],object[data]').evaluate_all("""es=>es.slice(0,30).map(x=>x.outerHTML.slice(0,450))""")
 except Exception as e:result.setdefault("errors",[]).append("page:"+str(e)[:170])
 if tasks:await asyncio.gather(*tasks,return_exceptions=True)
 await page.close()
 return result

async def main():
 out={"schema":"SAE_FIRSTPARTY_ALARGAN_ACTUAL_PUBLIC_FLIPBOOK_LINKS","captured_utc":datetime.now(timezone.utc).isoformat(),"production_writes":0,"projects":[]}
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  for pid,url in TARGETS:
   j=await scan(browser,pid,url)
   out["projects"].append(j)
   Path("sae-argan-official-embedded-pdf-links.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
   print(pid,j.get("main_status"),"links",len(j.get("links",[])),"contexts",len(j.get("captures",[])),flush=True)
  await browser.close()
if __name__=="__main__":asyncio.run(main())
