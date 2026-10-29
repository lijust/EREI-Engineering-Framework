#!/usr/bin/env python3
"""Read-only public Retal Verse actual project drill-down; distinguish 1064 marketing from numbered villa map inventory."""
import asyncio,json,hashlib,urllib.request,urllib.robotparser
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime,timezone
from playwright.async_api import async_playwright
URL="https://verse.retal.com.sa/?lang=en&state=saudi_arabia&theme=light"
UA="SAE-DB-Retal-Verse-original-project-physical-unit-discovery/1.0"
OUT=Path("sae-retal-verse-nesaj-lazurd-drilldown.json")
DATA={"schema":"SAE_RETAL_VERSE_EXISTING_CANONICAL_NESAJ_LAZURD_INTERACTIVE_UNIT_DISCOVERY",
"project_id":"PRJ-000046","source_url":URL,"utc":datetime.now(timezone.utc).isoformat(),"writes":0,"xhr":[],"errors":[],"interactions":[]}
def allowed(url):
 u=urlsplit(url)
 with urllib.request.urlopen(urllib.request.Request(f"{u.scheme}://{u.netloc}/robots.txt",headers={"User-Agent":UA}),timeout=20) as r:
  if r.status!=200:raise RuntimeError("robots invalid")
  b=r.read(150001)
  if len(b)>150000:raise RuntimeError("robots oversize")
 rp=urllib.robotparser.RobotFileParser();rp.parse(b.decode("utf8","replace").splitlines())
 return rp.can_fetch(UA,url)
async def main():
 try:yes=await asyncio.to_thread(allowed,URL)
 except Exception as e:DATA["stop"]="ROBOTS_UNVERIFIED_"+type(e).__name__;OUT.write_text(json.dumps(DATA));return
 if not yes:DATA["stop"]="ROBOTS_DENY";OUT.write_text(json.dumps(DATA));return
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True)
  page=await b.new_page(user_agent=UA,viewport={"width":1400,"height":940})
  jobs=[];stop=False
  async def cap(r):
   nonlocal stop
   host=urlsplit(r.url).hostname or ""
   if host.endswith("retal.com.sa") and r.status in (403,429):stop=True;return
   if r.status!=200 or len(DATA["xhr"])>=90:return
   if r.request.resource_type not in ("xhr","fetch") and "json" not in r.headers.get("content-type",""):return
   try:
    raw=await r.body()
    if len(raw)>8000000:return
    item={"url":r.url,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"mime":r.headers.get("content-type","")}
    try:
     doc=json.loads(raw)
     def arr(x,depth=0):
      if depth>5:return []
      if isinstance(x,dict):return sum((arr(q,depth+1) for q in x.values()),[])
      if isinstance(x,list):
       if len(x)>=7 and isinstance(x[0],dict):
        return [{"count":len(x),"fields":list(x[0])[:50],"first_item":{k:v for k,v in x[0].items() if isinstance(v,(str,int,float,bool,type(None)))}}]
       return sum((arr(q,depth+1) for q in x[:3]),[])
      return []
     item["arrays"]=arr(doc)[:6]
    except Exception:pass
    DATA["xhr"].append(item)
   except Exception as e:DATA["errors"].append("XHR_"+type(e).__name__)
  page.on("response",lambda r:jobs.append(asyncio.create_task(cap(r))))
  try:
   r=await page.goto(URL,wait_until="domcontentloaded",timeout=45000)
   DATA["http"]=r.status if r else None
   if r and r.status==200 and not stop:
    await page.wait_for_timeout(5000)
    DATA["initial"]=await page.evaluate("""() =>({title:document.title,html_len:document.documentElement.outerHTML.length,text:(document.body.innerText||"").slice(0,2500),iframes:[...document.querySelectorAll('iframe')].map(e=>e.src).slice(0,20),scripts:[...document.querySelectorAll('script[src]')].map(x=>x.src).slice(0,40)})""")
    matches=page.get_by_text("Nesaj Lazurd",exact=True)
    DATA["matches_count"]=await matches.count()
    if await matches.count():
     try:
      target=matches.first
      DATA["match_ancestor"]=await target.evaluate("""e=>e.closest("a,button,[role=button],article,[class*=project],[class*=card]")?.outerHTML.slice(0,2500)||e.parentElement?.outerHTML.slice(0,2500)""")
      await target.click(timeout=4500)
      await page.wait_for_timeout(5500)
      DATA["interactions"].append("clicked_project_own_visible_Nesaj_Lazurd")
      DATA["after"]=await page.evaluate("""() => ({url:location.href,title:document.title,text:document.body.innerText.slice(0,3400),links:[...document.querySelectorAll('a[href]')].filter(a=>/unit|villa|view|plot|phase|المخطط/i.test(a.innerText+" "+a.href)).map(a=>({label:a.innerText.slice(0,70),href:a.href})).slice(0,50),svg:document.querySelectorAll("svg").length,canvas:document.querySelectorAll("canvas").length})""")
     except Exception as e:DATA["errors"].append("CLICK_"+type(e).__name__+":"+str(e)[:150])
  except Exception as e:DATA["errors"].append("PAGE_"+type(e).__name__+":"+str(e)[:150])
  if jobs:await asyncio.gather(*jobs,return_exceptions=True)
  DATA["blocked"]=stop
  OUT.write_text(json.dumps(DATA,ensure_ascii=False,indent=2)+"\n")
  print("SAE_RETAL_VERSE_DRILLDOWN",json.dumps({k:DATA.get(k) for k in ("http","matches_count","match_ancestor","after","blocked","errors")},ensure_ascii=False)[:9000],flush=True)
  print("SAE_RETAL_VERSE_API",json.dumps(DATA["xhr"],ensure_ascii=False)[:15000],flush=True)
  await page.close();await b.close()
if __name__=="__main__":asyncio.run(main())
