#!/usr/bin/env python3
"""Existing Al Watheer PRJ-001017: capture all original first-party Jazan
individual land-parcel cards behind public Nuzul pagination (read-only).
Never synthesize 43 plot IDs from headline. No new project/developer writes.
"""
import asyncio,hashlib,json,re,urllib.request,urllib.robotparser
from urllib.parse import urlsplit
from datetime import datetime,timezone
from pathlib import Path
from playwright.async_api import async_playwright
PAGE="https://www.albaytalwathir.com/en/projects/301871"
HOST="www.albaytalwathir.com"
UA="SAE-DB-AlWatheer-original-public-parcel-pagination/1.0"
OUT=Path("sae-alwatheer-301871-original-public-pagination.json")
DATA={"schema":"SAE_ALWATHEER_EXISTING_PRJ_001017_REAL_PLOT_SOURCE_PAGINATION_V1",
      "project_id":"PRJ-001017","source_id":"SRC-000114",
      "project_source_url":PAGE,"captured_utc":datetime.now(timezone.utc).isoformat(),
      "production_writes":0,"stages":[],"xhr":[],"errors":[]}
def robots(url):
 u=urlsplit(url)
 if u.scheme!="https" or u.hostname!=HOST:raise RuntimeError("OUT_OF_ORIGINAL_PUBLISHER")
 with urllib.request.urlopen(urllib.request.Request("https://"+HOST+"/robots.txt",headers={"User-Agent":UA}),timeout=17) as r:
  if r.status!=200:raise RuntimeError("ROBOTS_HTTP_"+str(r.status))
  raw=r.read(200000)
 rp=urllib.robotparser.RobotFileParser();rp.parse(raw.decode("utf8","replace").splitlines())
 return rp.can_fetch(UA,url)
EVAL=r"""() => {
 let as=[...document.querySelectorAll('a[href]')].filter(a=>/\/properties\/[0-9]+/.test(a.href) && new URL(a.href).hostname===location.hostname);
 let items=as.map(a=>{
   let c=a.closest('article,.property-card,.property-item,.listing-card,.card,[class*="property"],[class*="listing"]')||a.parentElement?.parentElement?.parentElement;
   return {url:a.href,anchor:(a.innerText||'').trim().slice(0,150),text:(c?.innerText||'').trim().slice(0,1600),html:(c?.outerHTML||'').slice(0,3000)};
 });
 let controls=[...document.querySelectorAll('button,a[href],[role=button]')].filter(e=>{
   let t=(e.innerText||'').trim();
   return /^(?:[1-9][0-9]?|next|التالي|السابق|المزيد|load more|عرض المزيد)$/.test(t.toLowerCase()) || /page=/.test(e.getAttribute('href')||'')
 }).slice(0,70).map(e=>({tag:e.tagName,text:(e.innerText||'').trim().slice(0,70),href:e.href||null,outer:e.outerHTML.slice(0,430)}));
 return {url:location.href,title:document.title,code_links:[...new Map(items.map(x=>[x.url,x])).values()].slice(0,120),controls,body_head:(document.body.innerText||'').slice(0,4500),body_end:(document.body.innerText||'').slice(-3000)};
}"""
async def main():
 try:
  ok=await asyncio.to_thread(robots,PAGE)
  if not ok:DATA["stop"]="ROBOTS_DISALLOW";OUT.write_text(json.dumps(DATA));return
 except Exception as e:
  DATA["stop"]="ROBOTS_UNVERIFIED_"+type(e).__name__;OUT.write_text(json.dumps(DATA));return
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  page=await browser.new_page(user_agent=UA,viewport={"width":1350,"height":950})
  stop=False;tasks=[]
  async def observe(r):
   nonlocal stop
   if urlsplit(r.url).hostname!=HOST:return
   if r.status in (403,429):stop=True;DATA["errors"].append("ORIGIN_HTTP_"+str(r.status));return
   if r.request.resource_type not in ("xhr","fetch") or r.status!=200:return
   try:
    raw=await r.body()
    if len(DATA["xhr"])<30:
     DATA["xhr"].append({"path":urlsplit(r.url).path,"status":r.status,
      "sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),
      "source_json_shape":list(json.loads(raw))[:15] if raw[:1] in (b"[",b"{") else None})
   except Exception as e:DATA["errors"].append("XHR_"+type(e).__name__)
  page.on("response",lambda r:tasks.append(asyncio.create_task(observe(r))))
  try:
   r=await page.goto(PAGE,wait_until="domcontentloaded",timeout=40000)
   DATA["http"]=r.status if r else None
   if r and r.status==200 and not stop:
    await page.wait_for_timeout(2600)
    state=await page.evaluate(EVAL);DATA["stages"].append({"page":1,**state})
    print("SAE_WATHEER_INITIAL",json.dumps({"links":len(state["code_links"]),"items":state["code_links"][:8],"controls":state["controls"][:20]},ensure_ascii=False)[:10000],flush=True)
    for j in range(2,11):
     if stop:break
     # Strictly ordinary public numbered pagination, not speculative URLs.
     target=page.locator('button[aria-label="Go to page '+str(j)+'"]')
     if not await target.count():
      target=page.get_by_role("button",name=str(j),exact=True)
     if not await target.count():
      target=page.get_by_role("link",name=str(j),exact=True)
     if not await target.count():break
     try:
      await target.first.click(timeout=4000)
      oldset={x["url"] for x in DATA["stages"][-1]["code_links"]}
      await page.wait_for_function("""before=>{
       let a=[...document.querySelectorAll('a[href]')].map(e=>e.href).filter(x=>/\/properties\/\d+/.test(x));
       return a.some(x=>!before.includes(x));
      }""",arg=list(oldset),timeout=7000)
      now=await page.evaluate(EVAL)
      DATA["stages"].append({"page":j,**now})
      print("SAE_WATHEER_PAGE",json.dumps({"page":j,"cards":len(now["code_links"]),"first":now["code_links"][:3]},ensure_ascii=False)[:2000],flush=True)
     except Exception as exc:
      DATA["errors"].append("PAGINATION_"+type(exc).__name__)
      break
   else:DATA["stop"]="SOURCE_HTTP_OR_ACCESS_DENIED"
  except Exception as e:DATA["errors"].append("PAGE_"+type(e).__name__+":"+str(e)[:190])
  if tasks:await asyncio.gather(*tasks,return_exceptions=True)
  codes={}
  for stage in DATA["stages"]:
   for item in stage["code_links"]:codes[item["url"]]=item
  DATA["distinct_original_property_links"]=len(codes)
  DATA["source_cards_unique"]=list(codes.values())
  DATA["stopped_due_to_access"]=stop
  for pos in range(0,len(DATA["source_cards_unique"]),9):
   print("SAE_WATHEER_ORIGINAL_LINK_CHUNK",json.dumps({
    "publisher_project_id":"301871","canonical_existing_project_id":"PRJ-001017",
    "source_page":PAGE,"capture_utc":DATA["captured_utc"],
    "chunk_index":pos//9,"links":DATA["source_cards_unique"][pos:pos+9]
   },ensure_ascii=False,separators=(",",":")),flush=True)
  OUT.write_text(json.dumps(DATA,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
  print("SAE_WATHEER_SUMMARY",json.dumps({"http":DATA.get("http"),"stages":len(DATA["stages"]),
    "unique_links":len(codes),"errors":DATA["errors"],"controls":DATA["stages"][-1]["controls"][:15] if DATA["stages"] else []},ensure_ascii=False)[:3500],flush=True)
  await page.close();await browser.close()
if __name__=="__main__":asyncio.run(main())
