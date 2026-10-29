#!/usr/bin/env python3
"""SAE Saudi units-only: a single read-only multi-publisher inventory run.

Target only 36 EXISTING canonical projects from the checked-in live-sheet manifest.
Reuse one browser; four concurrent publishers, one project per publisher.
Honor robots, stop per publisher on 403/429, do not invent units or write Sheets.
"""
import asyncio, json, hashlib, re, urllib.request, urllib.robotparser
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime,timezone
from playwright.async_api import async_playwright

DIR=Path(__file__).resolve().parent
SEEDS=json.loads((DIR/"sae_existing_source_sweep_manifest_20261029.json").read_text())["source_seeds"]
OUTPUT=Path("sae-36-source-tiered-sweep.json")
UA="SAE-DB-publisher-source-study/1.0"
CODE=("unitCode","unit_code","unitNumber","unit_number","villaNumber","plotNumber","plot_number","landNumber","propertyNumber","unitNo")
FIELDS=set(CODE)|{"id","price","area","totalArea","area_sqm","size","floor","building","buildingNo","block","status","availability","bedrooms","bathrooms","type","projectId","project_id","unitArea"}
ROBOT_CACHE={}
BLOCKED=set()
REPORT={"schema":"SAE_36_EXISTING_PROJECT_SOURCE_SWEEP_V1","generated_utc":datetime.now(timezone.utc).isoformat(),"master_writes":0,"results":[]}
LOCKS={}
SEMAPHORE=asyncio.Semaphore(4)

def host(url):
 p=urlsplit(url)
 return p.scheme+"://"+p.netloc.lower()

def robot_check(url):
 h=host(url)
 if h not in ROBOT_CACHE:
  try:
   req=urllib.request.Request(h+"/robots.txt",headers={"User-Agent":UA})
   with urllib.request.urlopen(req,timeout=15) as resp:
    if resp.status!=200:raise ValueError("robots http "+str(resp.status))
    raw=resp.read(250001)
   if len(raw)>250000:raise ValueError("robots too large")
   rp=urllib.robotparser.RobotFileParser()
   rp.parse(raw.decode("utf-8","replace").splitlines())
   ROBOT_CACHE[h]=(rp,"ROBOTS_VERIFIED")
  except Exception as e:ROBOT_CACHE[h]=(None,"ROBOTS_UNVERIFIED_"+type(e).__name__)
 rp,why=ROBOT_CACHE[h]
 return bool(rp and rp.can_fetch(UA,url)),why

def candidates(blob):
 stack=[("$",blob,0)]
 result=[]
 visited=0
 while stack and visited<8000 and len(result)<18:
  path,node,depth=stack.pop();visited+=1
  if depth>7:continue
  if isinstance(node,dict):
   for k,v in list(node.items())[:60]:
    if isinstance(v,(dict,list)):stack.append((path+"."+k,v,depth+1))
  elif isinstance(node,list):
   if len(node)>=5 and all(isinstance(v,dict) for v in node[:min(6,len(node))]):
    for field in CODE:
     if field not in node[0]:continue
     codes=[str(x.get(field,"")).strip() for x in node]
     if all(c not in ("","0","null","None") for c in codes) and len(set(codes))==len(codes):
      result.append({"json_path":path,"unit_code_field":field,"count":len(node),
       "publisher_original_rows":[{k:v for k,v in x.items() if k in FIELDS and isinstance(v,(int,float,str,bool,type(None)))} for x in node[:2500]],
       "source_rows_capped":len(node)>2500})
      break
   for j,v in enumerate(node[:2]):
    if isinstance(v,(dict,list)):stack.append((path+"["+str(j)+"]",v,depth+1))
 return result

DOM=r"""() => {
 const headings=[...document.querySelectorAll('h1,h2,h3,h4,h5,h6,[data-unit]')]
  .filter(x=>/^\s*(الوحدة|وحدة|شقة|الشقة|فيلا|Unit|Villa|Apartment)\s*(رقم|No|#)?\s*[0-9٠-٩]/iu.test(x.innerText||''));
 return {title:document.title,headings:headings.length,
  sample:headings.slice(0,8).map(x=>(x.innerText||'').slice(0,100)),
  buttons:[...new Set([...document.querySelectorAll('button')].map(x=>(x.innerText||x.getAttribute('aria-label')||'').trim()))].slice(0,60),
  links:[...document.querySelectorAll('a[href]')].filter(x=>/unit|villa|plot|map|inventory|المخطط|الوحدة|pdf/i.test(x.href+' '+x.innerText)).slice(0,70).map(x=>({url:x.href,text:(x.innerText||'').slice(0,60)})),
  scripts:[...document.querySelectorAll('script[src]')].slice(0,30).map(x=>x.src),
  embedded:[...document.querySelectorAll('script#__NEXT_DATA__,script[type="application/json"]')].slice(0,3).map(x=>(x.textContent||'').slice(0,150000)),
  iframes:[...document.querySelectorAll('iframe[src]')].slice(0,10).map(x=>x.src),
  canvas:document.querySelectorAll('canvas').length,svg:document.querySelectorAll('svg polygon,svg path').length}
}"""
MORE=re.compile(r"^(?:عرض المزيد|إظهار المزيد|تحميل المزيد|المزيد|Load More|Show More)$",re.I)

async def inspect(seed,browser):
 h=host(seed["publisher_page"])
 async with SEMAPHORE:
  async with LOCKS[h]:
   row={"project_id":seed["project_id"],"name_ar":seed["name_ar"],"url":seed["publisher_page"],
    "publisher_total_NOT_inventoried":seed["marketing_total"],"xhr":[],"candidate_arrays":[],
    "errors":[],"more_clicks":0}
   if h in BLOCKED:row["access"]="PUBLISHER_PREVIOUSLY_BLOCKED";return row
   allowed,reason=await asyncio.to_thread(robot_check,row["url"])
   row["robots"]=reason
   if not allowed:row["access"]="FAIL_CLOSED_ROBOTS";return row
   page=await browser.new_page(user_agent=UA)
   tasks=[];blocked=False;seen=set()
   async def observe(response):
    nonlocal blocked
    if host(response.url)!=h:return
    if response.status in (403,429):
     blocked=True;BLOCKED.add(h);row["errors"].append("STOP_HTTP_"+str(response.status));return
    if response.status!=200 or response.request.resource_type not in ("xhr","fetch"):return
    if len(row["xhr"])>=55:return
    try:
     body=await response.body()
     if len(body)>5000000 or not body:return
     digest=hashlib.sha256(body).hexdigest()
     if digest in seen:return
     seen.add(digest)
     path=response.url.split("?")[0]
     row["xhr"].append({"path":path,"sha256":digest,"size":len(body)})
     if body[:1] in (b"{",b"["):
      try:
       for found in candidates(json.loads(body)):
        row["candidate_arrays"].append({"publisher_api":path,**found})
      except (ValueError,UnicodeError):pass
    except Exception as exc:row["errors"].append("XHR_"+type(exc).__name__)
   page.on("response",lambda x:tasks.append(asyncio.create_task(observe(x))))
   try:
    r=await page.goto(row["url"],wait_until="domcontentloaded",timeout=35000)
    row["status"]=r.status if r else None
    if row["status"] in (403,429):blocked=True;BLOCKED.add(h)
    if not blocked and host(page.url)==h:
     await page.wait_for_timeout(1250)
     row["initial"]=await page.evaluate(DOM)
     for payload in row["initial"].get("embedded",[]):
      try:
       for found in candidates(json.loads(payload)):
        row["candidate_arrays"].append({"embedded_original_json":True,**found})
      except ValueError:pass
     for i in range(60):
      if blocked:break
      more=page.get_by_role("button",name=MORE)
      if not await more.count() or not await more.first.is_visible():break
      try:
       before=len(await page.locator("body").inner_text())
       await more.first.click(timeout=2500)
       await page.wait_for_timeout(80)
       after=len(await page.locator("body").inner_text())
       row["more_clicks"]+=1
       if after<=before:break
      except Exception as e:row["errors"].append("MORE_"+type(e).__name__);break
     if not blocked:
      row["final"]=await page.evaluate(DOM)
      text=await page.locator("body").inner_text()
      if row["final"]["headings"]>=5:
       row["original_numbered_cards_text"]=text[:300000]
       row["full_body_sha256"]=hashlib.sha256(text.encode()).hexdigest()
      else:row["public_excerpt"]=text[:1800]
     row["access"]="BLOCKED" if blocked else "INSPECTED"
    else:row["access"]="BLOCKED_OR_REDIRECT"
   except Exception as e:row["errors"].append("PAGE_"+type(e).__name__+":"+str(e)[:100])
   finally:
    if tasks:
     try:await asyncio.wait_for(asyncio.gather(*tasks,return_exceptions=True),timeout=8)
     except Exception:row["errors"].append("XHR_TASK_TIMEOUT")
    await page.close()
   return row

async def main():
 assert len(SEEDS)==36 and len({s["project_id"] for s in SEEDS})==36
 for s in SEEDS:LOCKS.setdefault(host(s["publisher_page"]),asyncio.Lock())
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  async def task(s):
   v=await inspect(s,browser)
   REPORT["results"].append(v)
   OUTPUT.write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+"\n")
   print("SAE_SWEEP",json.dumps({"id":v["project_id"],"access":v.get("access"),
    "status":v.get("status"),"more":v["more_clicks"],
    "dom":v.get("final",{}).get("headings",0),
    "coded":sum(z["count"] for z in v["candidate_arrays"]),
    "errors":v["errors"][:2]},ensure_ascii=False),flush=True)
  await asyncio.gather(*(task(s) for s in SEEDS))
  await browser.close()
 REPORT["results"].sort(key=lambda r:r["project_id"])
 REPORT["summary"]={"project_count":len(REPORT["results"]),
  "sites":len(LOCKS),"inspected":sum(x.get("access")=="INSPECTED" for x in REPORT["results"]),
  "robots_unverified":sum(x.get("access")=="FAIL_CLOSED_ROBOTS" for x in REPORT["results"]),
  "source_blocked":len(BLOCKED),
  "more_clicks":sum(x["more_clicks"] for x in REPORT["results"]),
  "projects_with_itemized_DOM":sum(x.get("final",{}).get("headings",0)>=5 for x in REPORT["results"]),
  "potential_api_arrays":sum(len(x["candidate_arrays"]) for x in REPORT["results"]),
  "new_master_unit_rows":0}
 OUTPUT.write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+"\n")
 print("SAE_SWEEP_SUMMARY",json.dumps(REPORT["summary"],ensure_ascii=False),flush=True)
if __name__=="__main__":
 assert candidates({"inventory":[{"unitNumber":str(i+1)} for i in range(15)]})[0]["count"]==15
 asyncio.run(main())
