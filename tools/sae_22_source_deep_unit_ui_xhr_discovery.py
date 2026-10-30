#!/usr/bin/env python3
"""SAE-DB multi-source deep inventory shape discovery.

22 distinct registered original publisher domains; 37 already-canonical
project URLs. Navigate only public project pages, inspect native inventory UI,
observe same-origin XHR responses. No speculative API URLs or ad aggregate
conversion. No login, contact actions or buying/reservation clicks.
"""
import asyncio,hashlib,json,re,urllib.request,urllib.robotparser
from urllib.parse import urlsplit
from pathlib import Path
from datetime import datetime,timezone
from playwright.async_api import async_playwright

MANIFEST=Path("tools/sae_22_host_high_density_deep_ui_manifest_20261030.json")
OUT=Path("sae-22-host-original-deep-unit-ui-source.json")
UA="SAE-DB-unit-only-official-public-ui/1.0"
CAPTURE={"schema":"SAE_22_DISTINCT_PUBLISHER_DOMAINS_NATIVE_UNIT_UI_XHR_V1",
"observed_utc":datetime.now(timezone.utc).isoformat(),
"master_unit_writes":0,"original_publisher_hosts":[]}
ACTION_REGEX=re.compile(r"(عرض الوحدات|الوحدات المتاحة|تفاصيل الوحدات|اختر وحدتك|استعرض الوحدات|شاهد الوحدات|المخطط التفاعلي|view units|unit availability|available units|show units|units list|view inventory)",re.IGNORECASE)
DOM=r"""() => {
 let as=[...document.querySelectorAll('a[href]')].filter(a=>{
   try {let u=new URL(a.href);return u.hostname===location.hostname && /\/(properties|units|unit|apartment|listing|villa|plots)\/\d+/.test(u.pathname)}
   catch(e){return false}
 }).slice(0,300).map(a=>({href:a.href,text:(a.innerText||'').trim().slice(0,190),aria:a.getAttribute('aria-label')}));
 let data=[...document.querySelectorAll('[data-unit-id],[data-unit-code],[data-unit],[data-plot-number],[data-property-id]')].slice(0,240).map(x=>({unitId:x.dataset.unitId||null,
   code:x.dataset.unitCode||null,unit:x.dataset.unit||null,plot:x.dataset.plotNumber||null,propertyId:x.dataset.propertyId||null,
   html:x.outerHTML.slice(0,330)}));
 let tables=[...document.querySelectorAll('table')].slice(0,9).map(t=>({headers:[...t.querySelectorAll('thead th')].map(x=>x.innerText.trim()).slice(0,25),
   rows:[...t.querySelectorAll('tbody tr')].slice(0,10).map(x=>x.innerText.trim().slice(0,350))}));
 let buttons=[...document.querySelectorAll('button,[role="button"],a')].filter(x=>{
   let t=(x.innerText||'').trim();return t.length>2 && t.length<70 && /عرض الوحدات|الوحدات المتاحة|تفاصيل الوحدات|اختر وحدتك|استعرض الوحدات|شاهد الوحدات|المخطط التفاعلي|view units|unit availability|available units|show units|units list|view inventory/i.test(t);
 }).slice(0,18).map(x=>({text:x.innerText.trim(),tag:x.tagName,href:x.href||null}));
 let scripts=[...document.querySelectorAll('script[src]')].map(x=>x.src).filter(x=>/main|bundle|app|index|livewire/i.test(x)).slice(0,20);
 return {title:document.title,firstparty_unit_links:as,native_unit_nodes:data,
  tables,buttons,firstparty_script_urls:scripts,body_excerpt:(document.body?.innerText||'').slice(0,3800)};
}"""

def checkpoint():
 tmp=OUT.with_suffix(".tmp")
 tmp.write_text(json.dumps(CAPTURE,ensure_ascii=False,indent=2)+"\n",encoding="utf8");tmp.replace(OUT)

def robots(host):
 p="https://"+host+"/robots.txt"
 with urllib.request.urlopen(urllib.request.Request(p,headers={"User-Agent":UA}),timeout=16) as r:
  if r.status in (403,429):raise RuntimeError("ROBOTS_ACCESS_STOP_"+str(r.status))
  if r.status!=200:raise RuntimeError("ROBOTS_HTTP_"+str(r.status))
  b=r.read(140001)
 if len(b)>140000 or not b:raise RuntimeError("ROBOTS_INVALID")
 rp=urllib.robotparser.RobotFileParser()
 rp.parse(b.decode("utf8","replace").splitlines())
 return rp

def arrays(x,path="$",depth=0):
 if depth>6:return []
 out=[]
 if isinstance(x,dict):
  for k,y in list(x.items())[:70]:
   if isinstance(y,(list,dict)):out.extend(arrays(y,path+"."+str(k),depth+1))
 elif isinstance(x,list):
  if len(x)>=3 and isinstance(x[0],dict):
   fields=set()
   for row in x[:7]:fields.update(row)
   indicators=bool(fields&{"unit_number","unitNumber","unit_code","unitCode","plot_number","plotNumber","property_id","unitId","UnitId","building_no"})
   if indicators:out.append({"json_path":path,"object_count":len(x),"source_field_keys":sorted(fields)[:45],
    "source_preview":[{k:v for k,v in row.items() if k in ("unit_number","unitNumber","unit_code","unitCode","plot_number","plotNumber","area","price","building_no","project_id","id") and (v is None or isinstance(v,(str,float,int,bool)))} for row in x[:3]]})
  for i,y in enumerate(x[:2]):
   if isinstance(y,(dict,list)):out.extend(arrays(y,path+"["+str(i)+"]",depth+1))
 return out[:15]

async def browse(browser,source,project,rule,origin_blocked):
 url=project["original_project_url"];host=source["domain"]
 item={"canonical_existing_project_id":project["canonical_project_id"],"publisher_source_id":source["source_id"],
  "project_url":url,"marketing_total_not_source_proof":project["marketing_total_NOT_UNIT_PROOF"],
  "original_publisher_name":project["project_name"],"status":"STARTED","snapshots":[],"xhr":[],"errors":[]}
 if origin_blocked.get(host):item["status"]="ORIGIN_PREVIOUS_ACCESS_STOP";return item
 if not rule.can_fetch(UA,url):item["status"]="ROBOTS_DISALLOW";return item
 page=await browser.new_page(user_agent=UA,viewport={"width":1440,"height":950})
 pending=[];observed_shas=set();blocked=False
 async def watch(r):
  nonlocal blocked
  if urlsplit(r.url).hostname!=host:return
  if r.status in (403,429):
   blocked=True;origin_blocked[host]=True
   item["errors"].append("ORIGIN_HTTP_"+str(r.status))
   return
  if r.status!=200 or r.request.resource_type not in ("xhr","fetch") or len(item["xhr"])>55:return
  try:
   raw=await r.body()
   if not raw or len(raw)>3500000:return
   digest=hashlib.sha256(raw).hexdigest()
   if digest in observed_shas:return
   observed_shas.add(digest)
   snapshot={"url":r.url,"sha256":digest,"bytes":len(raw)}
   try:
    obj=json.loads(raw)
    snapshot["original_unit_shaped_arrays"]=arrays(obj)
   except Exception:pass
   if snapshot.get("original_unit_shaped_arrays") or re.search(r"unit|inventory|property|plot|livewire",urlsplit(r.url).path,re.I):
    item["xhr"].append(snapshot)
  except Exception as ex:item["errors"].append("XHR_"+type(ex).__name__)
 page.on("response",lambda r:pending.append(asyncio.create_task(watch(r))))
 try:
  await asyncio.sleep(.9)
  res=await page.goto(url,wait_until="domcontentloaded",timeout=28000)
  item["http"]=res.status if res else None
  if not res or res.status!=200 or blocked:
   item["status"]="PROJECT_NOT_PUBLIC_200";return item
  await page.wait_for_timeout(950)
  item["snapshots"].append({"stage":"INITIAL",**(await page.evaluate(DOM))})
  eligible=page.locator("button,[role=button],a").filter(has_text=ACTION_REGEX)
  attempts=0
  if await eligible.count():
   n=await eligible.count()
   for i in range(min(n,5)):
    if attempts>=3 or blocked:break
    action=eligible.nth(i)
    try:
     if not await action.is_visible():continue
     href=await action.get_attribute("href")
     if href and (urlsplit(href).hostname not in ("",None,host) and href.startswith("http")):continue
     title=(await action.inner_text()).strip()[:90]
     if re.search(r"(?i)(book|buy|reserve|احجز|اتصل|سجل|اشترك)",title):continue
     await action.click(timeout=3800)
     await page.wait_for_timeout(950)
     attempts+=1
     item["snapshots"].append({"stage":"CLICK_UNIT_UI","control":title,**(await page.evaluate(DOM))})
    except Exception as exc:item["errors"].append("PUBLIC_UNIT_UI_"+type(exc).__name__)
  item["status"]="SOURCE_UI_DISCOVERY_COMPLETED" if not blocked else "STOP_ORIGIN_403_429"
 except Exception as exc:item["errors"].append("BROWSER_"+type(exc).__name__+":"+str(exc)[:110]);item["status"]="SOURCE_ERROR"
 finally:
  if pending:await asyncio.gather(*pending,return_exceptions=True)
  await page.close()
 return item

async def main():
 data=json.loads(MANIFEST.read_text(encoding="utf8"));sources=data["sources"]
 if len(sources)!=22:raise RuntimeError("MANIFEST_PROJECTS_CHANGED")
 for s in sources:
  host=s["domain"]
  if not re.fullmatch(r"SRC-\d{6}",s["source_id"]):raise RuntimeError("BAD_SOURCE")
  if any(urlsplit(p["original_project_url"]).hostname.replace("www.","")!=host for p in s["targets"]):
   raise RuntimeError("OFF_ORIGIN_MANIFEST")
 # One worker per origin, up to 4 DIFFERENT origins concurrently.
 # Strictly sequential project requests within an origin.
 gate=asyncio.Semaphore(4)
 async def get_one_rules(source):
  async with gate:
   try:return source["domain"],await asyncio.to_thread(robots,source["domain"])
   except Exception as exc:
    return source["domain"],"ROBOTS_UNVERIFIED_"+type(exc).__name__+":"+str(exc)[:90]
 discovered=await asyncio.gather(*(get_one_rules(s) for s in sources))
 per_origin=dict(discovered)
 blocked={};lock=asyncio.Lock()
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  async def worker(source):
   async with gate:
    host=source["domain"];r=per_origin[host]
    result={"source_id":source["source_id"],"domain":host,"targets":[]}
    if isinstance(r,str):result["status"]=r
    else:
     for p in source["targets"]:
      obs=await browse(browser,source,p,r,blocked)
      result["targets"].append(obs)
      print("SAE_DEEP_SOURCE_PROJECT",json.dumps({"domain":host,"pid":p["canonical_project_id"],
       "http":obs.get("http"),"status":obs["status"],
       "unit_original_links":sum(len(x["firstparty_unit_links"]) for x in obs.get("snapshots",[])),
       "native_unit_nodes":sum(len(x["native_unit_nodes"]) for x in obs.get("snapshots",[])),
       "native_unit_xhr":sum(len(x.get("original_unit_shaped_arrays",[])) for x in obs["xhr"]),
       "unit_ui_clicked":[x.get("control") for x in obs.get("snapshots",[]) if x["stage"]=="CLICK_UNIT_UI"],
       "errors":obs["errors"][:4]},ensure_ascii=False)[:1900],flush=True)
      if blocked.get(host):break
    async with lock:
     CAPTURE["original_publisher_hosts"].append(result)
     checkpoint()
    return result
  results=await asyncio.gather(*(worker(s) for s in sources))
  await browser.close()
 CAPTURE["summary"]={"registered_publishers_tested":len(results),
  "public_original_project_pages_scanned":sum(len(x["targets"]) for x in results),
  "source_native_unit_nodes":sum(len(y["native_unit_nodes"]) for x in results for p in x["targets"] for y in p.get("snapshots",[])),
  "source_linked_individual_pages":sum(len(y["firstparty_unit_links"]) for x in results for p in x["targets"] for y in p.get("snapshots",[])),
  "publisher_ajax_itemized_arrays":sum(len(y.get("original_unit_shaped_arrays",[])) for x in results for p in x["targets"] for y in p.get("xhr",[])),
  "blocked_origins":list(blocked),"canonical_writes":0}
 checkpoint()
 print("SAE_DEEP_22_SOURCE_SUMMARY",json.dumps(CAPTURE["summary"],ensure_ascii=False),flush=True)

if __name__=="__main__":asyncio.run(main())
