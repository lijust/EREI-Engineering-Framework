#!/usr/bin/env python3
"""First-party Alsoliman project 131 actual sale portal: discover clickable public inventory."""
import asyncio,json,hashlib,urllib.request,urllib.robotparser,re
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime,timezone
from playwright.async_api import async_playwright
BASE="https://alsoliman.com.sa"
URL=BASE+"/ar/selling"
UA="SAE-DB-project131-inventory-source-research/1.0"
OUT=Path("sae-alsoliman-131-public-portal-source.json")
result={"schema":"SAE_EXISTING_PROJECT_001578_ALSOLIMAN_SOURCE_INTELLIGENCE_20261029","canonical_id":"PRJ-001578","source_url":URL,"created_utc":datetime.now(timezone.utc).isoformat(),"production_writes":0,"net":[],"clicks":[],"errors":[]}
def robots(url):
 u=urlparse(url)
 with urllib.request.urlopen(urllib.request.Request(u.scheme+"://"+u.netloc+"/robots.txt",headers={"User-Agent":UA}),timeout=16) as f:
  if f.status!=200:raise RuntimeError("ROBOTS_UNVERIFIED")
  buf=f.read(140001)
  if len(buf)>140000:raise RuntimeError("ROBOTS_OVERSIZE")
 rp=urllib.robotparser.RobotFileParser()
 rp.parse(buf.decode("utf8","replace").splitlines())
 return rp.can_fetch(UA,url)
async def main():
 try:ok=await asyncio.to_thread(robots,URL)
 except Exception as e:result["stop"]="ROBOTS_UNVERIFIED_"+type(e).__name__;OUT.write_text(json.dumps(result));return
 if not ok:result["stop"]="ROBOTS_DISALLOW";OUT.write_text(json.dumps(result));return
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True)
  page=await b.new_page(user_agent=UA,viewport={"width":1365,"height":1000})
  tasks=[];blocked=False
  async def resp(r):
   nonlocal blocked
   domain=urlparse(r.url).hostname or ""
   if r.status in (403,429) and (domain=="alsoliman.com.sa" or domain.endswith(".alsoliman.com.sa")):blocked=True;return
   if r.status!=200 or len(result["net"])>=100:return
   if r.request.resource_type not in ("xhr","fetch") and "json" not in r.headers.get("content-type",""):return
   try:
    raw=await r.body()
    if not raw or len(raw)>7500000:return
    item={"url":r.url,"sha":hashlib.sha256(raw).hexdigest(),"size":len(raw)}
    try:
     obj=json.loads(raw)
     def arrays(x,depth=0):
      if depth>6:return []
      if isinstance(x,dict):return sum((arrays(z,depth+1) for z in x.values()),[])
      if isinstance(x,list):
       if len(x)>=5 and isinstance(x[0],dict):return [{"n":len(x),"first_fields":list(x[0])[:35],"sample":x[:3]}]
       return sum((arrays(z,depth+1) for z in x[:4]),[])
      return []
     item["arrays"]=arrays(obj)[:6]
     if re.search(r'131|نخبة السليمان|elite',raw[:30000].decode("utf8","ignore"),re.I):item["preview"]=raw[:2600].decode("utf8","replace")
    except Exception:pass
    result["net"].append(item)
   except Exception as e:result["errors"].append("XHR_"+type(e).__name__)
  page.on("response",lambda r:tasks.append(asyncio.create_task(resp(r))))
  try:
   r=await page.goto(URL,wait_until="domcontentloaded",timeout=45000)
   result["http"]=r.status if r else None
   if result["http"]==200 and not blocked:
    await page.wait_for_timeout(2500)
    result["original_title"]=await page.title()
    result["131_html"]=await page.locator("text=مخطط نخبة السليمان").first.evaluate("""e=>e.closest('article,.project,.card,.item,.col-lg-4,.col-md-4,.col-md-6')?.outerHTML.slice(0,6000)||e.parentElement?.parentElement?.outerHTML.slice(0,6000)""")
    result["131_anchors"]=await page.locator("a[href]").evaluate_all("""x=>x.filter(y=>/131|نخبة|elite/i.test((y.innerText||"")+' '+y.href)).map(y=>({text:y.innerText.slice(0,80),url:y.href,html:y.outerHTML.slice(0,800)})).slice(0,25)""")
    target=page.get_by_text("مخطط نخبة السليمان",exact=True).first
    if await target.count():
     try:
      await target.click(timeout=6000)
      await page.wait_for_timeout(4500)
      result["after_click_url"]=page.url
      result["after_click"]=await page.evaluate("""()=>({title:document.title,text:document.body.innerText.slice(0,4000),links:[...document.querySelectorAll('a[href]')].filter(a=>/بيع|وحدة|قطعة|مخطط|unit|sale/i.test(a.innerText+" "+a.href)).map(a=>({text:a.innerText.slice(0,90),href:a.href})).slice(0,40)})""")
      result["clicks"].append("project_131_name")
     except Exception as e:result["errors"].append("CLICK_"+type(e).__name__+":"+str(e)[:90])
  except Exception as e:result["errors"].append("PAGE_"+type(e).__name__+":"+str(e)[:90])
  if tasks:await asyncio.gather(*tasks,return_exceptions=True)
  result["blocked"]=blocked
  OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
  print("SAE_ALSOLIMAN_131",json.dumps({k:result.get(k) for k in ("http","131_html","131_anchors","after_click_url","after_click","blocked","errors")},ensure_ascii=False).slice(0,9000),flush=True)
  print("SAE_ALSOLIMAN_131_API",json.dumps(result["net"],ensure_ascii=False).slice(0,14000),flush=True)
  await page.close();await b.close()
if __name__=="__main__":asyncio.run(main())
