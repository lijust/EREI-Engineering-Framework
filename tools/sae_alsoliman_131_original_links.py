#!/usr/bin/env python3
"""Inspect existing SAE project Alsoliman Elite 131 original public documents;
preserve exact source URLs; no synthetic units or Google Sheet writes.
"""
import asyncio,json,re,urllib.parse,urllib.request,urllib.robotparser,hashlib
from pathlib import Path
from datetime import datetime,timezone
from playwright.async_api import async_playwright
PAGES=[
 {"id":"PRJ-001578","page":"https://alsoliman.com.sa/ar/product/%D9%85%D8%AE%D8%B7%D8%B7-%D9%86%D8%AE%D8%A8%D8%A9-%D8%A7%D9%84%D8%B3%D9%84%D9%8A%D9%85%D8%A7%D9%86"},
 {"id":"PRJ-001578","page":"https://alsoliman.com.sa/ar/selling"}
]
UA="SAE-DB-source-study/1.0"
report={"schema":"SAE_ALSOLIMAN_131_FIRSTPARTY_UNITS_AND_PLAN_LINKS_READONLY","captured_utc":datetime.now(timezone.utc).isoformat(),"project_id":"PRJ-001578","writes":0,"pages":[]}
def robots(url):
 p=urllib.parse.urlsplit(url)
 with urllib.request.urlopen(urllib.request.Request(f"{p.scheme}://{p.netloc}/robots.txt",headers={"User-Agent":UA}),timeout=18) as r:
  if r.status!=200:return False
  rule=urllib.robotparser.RobotFileParser();rule.parse(r.read(200000).decode("utf8","replace").splitlines())
  return rule.can_fetch(UA,url)
async def scan(browser,item):
 url=item["page"];obs=dict(item,responses=[])
 try:obs["robots_allowed"]=await asyncio.to_thread(robots,url)
 except Exception as e:obs["robots_error"]=str(e);obs["robots_allowed"]=False
 if not obs["robots_allowed"]:return obs
 page=await browser.new_page(user_agent=UA)
 tasks=[]
 async def capture(resp):
  if resp.status in (403,429) and "alsoliman.com.sa" in resp.url:obs.setdefault("blocked",[]).append([resp.status,resp.url])
  if resp.request.resource_type not in ("document","xhr","fetch"):return
  if len(obs["responses"])>=25:return
  try:
   data=await resp.body()
   text=data.decode("utf8","replace")
   links=re.findall(r'(?:https?://[^"\'\s<>]+\.(?:pdf|PDF)(?:\?[^"\'\s<>]{0,50})?)',text,re.I)
   if links or "131" in text or "نخبة السليمان" in text:
    obs["responses"].append({"url":resp.url,"status":resp.status,
     "size":len(data),"pdf_links":list(dict.fromkeys(links))[:40],
     "unit_numbers_context":re.findall(r".{0,100}(?:project.?131|مخطط نخبة السليمان|elite.?plan|plot.?number).{0,140}",text,re.I)[:12]})
  except Exception as e:obs.setdefault("errors",[]).append("resp_"+type(e).__name__)
 page.on("response",lambda r:tasks.append(asyncio.create_task(capture(r))))
 try:
  r=await page.goto(url,wait_until="domcontentloaded",timeout=30000)
  obs["http"]=r.status if r else None
  if obs["http"] not in (403,429):
   await page.wait_for_timeout(3300)
   obs["links"]=await page.locator("a[href]").evaluate_all("""as=>as.filter(a=>/elite|131|plan|pdf|download|الوحدة|مخطط|نخبة/i.test(a.href+' '+a.innerText)).slice(0,70).map(a=>({text:a.innerText.slice(0,95),url:a.href,html:a.outerHTML.slice(0,350)}))""")
   obs["buttons"]=await page.locator("button").evaluate_all("""bs=>bs.filter(b=>/تحميل|تعريف|مخطط|الوحدة|download/i.test(b.innerText)).slice(0,25).map(b=>b.outerHTML.slice(0,550))""")
   obs["iframes"]=await page.locator("iframe[src],embed[src]").evaluate_all("""es=>es.slice(0,20).map(x=>x.outerHTML.slice(0,450))""")
 except Exception as e:obs.setdefault("errors",[]).append("page_"+str(e)[:200])
 if tasks:await asyncio.gather(*tasks,return_exceptions=True)
 await page.close()
 return obs
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  for target in PAGES:
   o=await scan(browser,target);report["pages"].append(o)
   Path("sae-alsoliman-original-131-links.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
   print(o.get("http"),o.get("robots_allowed"),len(o.get("links",[])),len(o.get("responses",[])),flush=True)
  await browser.close()
if __name__=="__main__":asyncio.run(main())
