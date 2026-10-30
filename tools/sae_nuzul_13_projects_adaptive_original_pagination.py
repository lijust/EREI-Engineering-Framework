#!/usr/bin/env python3
"""SAE-DB: publisher-family inventory crawler, 13 EXISTING projects / 7 sources.

Designed to replace one-off page scans: per-host robots+rate controls, DOM
pagination to exhaustion, original property URLs and publisher unit labels,
strict same-origin, 403/429 stop, source log at every project and page.
Zero automatic Master writes: next pipeline phase verifies detail card physical
identity, source status, area/price and explicit canonical project join.
"""
from __future__ import annotations

import asyncio, hashlib, json, re, time, urllib.request, urllib.robotparser
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from playwright.async_api import async_playwright

MANIFEST=Path("tools/sae_nuzul_existing_13_project_manifest_20261030.json")
OUTPUT=Path("sae-nuzul-13-original-all-pages-public-source.json")
UA="SAE-DB-publisher-project-physical-units/1.0"
SUMMARY_PREFIX="SAE_NUZUL_FAMILY_SOURCE"
LIMIT_PER_PROJECT=14
MAX_TARGETS=13
SOURCE_DELAY_SECONDS=1.1

state={"schema":"SAE_NUZUL_FAMILY_13_CANONICAL_ORIGINAL_PAGINATION_V2",
       "utc":datetime.now(timezone.utc).isoformat(),"master_writes":0,
       "source_only":True,"results":[],"errors":[]}

DOM=r"""() => {
 const host=location.hostname,all=[...document.querySelectorAll('a[href]')];
 const isDetail=a=>{
   try {const u=new URL(a.getAttribute('href'),location.href);
    return u.hostname===host && /^\/(?:en\/|ar\/)?properties\/\d+\/?$/.test(u.pathname);
   } catch(e){return false}
 };
 const links=all.filter(isDetail).map(a=>{
   const u=new URL(a.getAttribute('href'),location.href);
   const scope=a.closest('.nz-property-row-link,article,.card,[class*="property"],tr')||a;
   return {url:u.href,source_numeric_id:u.pathname.match(/\/(\d+)\/?$/)?.[1],
     label:(a.innerText||'').trim().slice(0,160),
     aria:(a.getAttribute('aria-label')||'').trim().slice(0,220),
     text:(scope.innerText||'').trim().slice(0,650)};
 });
 const unique=[...new Map(links.map(x=>[x.url,x])).values()];
 const paging=[...document.querySelectorAll('button,a[href]')].filter(e=>/^(?:Go to page |page )?\d+$/.test((e.getAttribute('aria-label')||'').trim())||/^(?:\d{1,3}|next|التالي)$/.test((e.innerText||'').trim().toLowerCase()));
 return {url:location.href,title:document.title,
  text_excerpt:(document.body?.innerText||'').slice(0,2100),
  candidates:unique.slice(0,180),
  paging:paging.slice(0,26).map(e=>({aria:e.getAttribute('aria-label'),text:(e.innerText||'').trim(),tag:e.tagName,disabled:e.disabled||false})),
  body_length:(document.body?.innerText||'').length};
}"""

def save():
 temp=OUTPUT.with_suffix(".tmp")
 temp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 temp.replace(OUTPUT)

def get_robots(host):
 url="https://"+host+"/robots.txt"
 with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=16) as r:
  if r.status in (403,429):raise RuntimeError("ROBOTS_SOURCE_HTTP_"+str(r.status))
  if r.status!=200:raise RuntimeError("ROBOTS_HTTP_"+str(r.status))
  content=r.read(180001)
 if not content or len(content)>180000:raise RuntimeError("ROBOTS_INVALID")
 rp=urllib.robotparser.RobotFileParser()
 rp.parse(content.decode("utf8","replace").splitlines())
 return rp

async def project(browser,src,robots,host_blocked):
 host=src["official_domain"];url=src["url"]
 record={**src,"project_original_url":url,"pages":[],"distinct_cards":[],
         "status":"STARTED","errors":[],"source_capture_utc":datetime.now(timezone.utc).isoformat()}
 if host_blocked.get(host):
  record["status"]="ORIGIN_PRIOR_403_OR_429";return record
 if not robots.can_fetch(UA,url):
  record["status"]="ROBOTS_DISALLOWED";return record
 page=await browser.new_page(user_agent=UA,viewport={"width":1360,"height":900})
 seen=set();blocked=False
 def watch(r):
  nonlocal blocked
  if urlsplit(r.url).hostname==host and r.status in (403,429):
   blocked=True
   host_blocked[host]=True
   record["errors"].append("STOP_ORIGIN_HTTP_"+str(r.status))
 page.on("response",watch)
 try:
  response=await page.goto(url,wait_until="domcontentloaded",timeout=36000)
  record["http"]=response.status if response else None
  if not response or response.status!=200 or blocked:
   record["status"]="ORIGINAL_SOURCE_HTTP_NOT_200";return record
  await page.wait_for_timeout(1000)
  cards={}
  for n in range(1,LIMIT_PER_PROJECT+1):
   if blocked:
    record["status"]="STOP_ORIGIN_ACCESS";break
   observed=await page.evaluate(DOM)
   page_cards=observed["candidates"]
   new_cards=0
   for c in page_cards:
    if c["url"] not in cards:
     cards[c["url"]]=c
     new_cards+=1
   sig=hashlib.sha256(json.dumps([c["source_numeric_id"] for c in page_cards]).encode()).hexdigest()
   record["pages"].append({"page":n,"cards_visible":len(page_cards),
      "new_source_links":new_cards,"sha256_ordered_ids":sig,
      "paging_buttons":observed["paging"][:16]})
   if n==1:record["original_publisher_title"]=observed["title"];record["initial_text"]=observed["text_excerpt"]
   print(SUMMARY_PREFIX,json.dumps({"canonical":src["project"],"host":host,"page":n,
       "new":new_cards,"distinct":len(cards),"available_buttons":len(observed["paging"])},
       ensure_ascii=False),flush=True)
   if n>=LIMIT_PER_PROJECT:record["status"]="STOP_BOUNDED_14_PAGES";break
   next_no=n+1
   nxt=page.locator('button.MuiPaginationItem-page').filter(has_text=re.compile('^'+str(next_no)+'
   if not await nxt.count():
    record["status"]="PUBLIC_PAGINATION_EXHAUSTED";break
   if not await nxt.first.is_enabled():
    record["status"]="PUBLIC_PAGINATION_DISABLED";break
   await asyncio.sleep(SOURCE_DELAY_SECONDS)
   try:
    await nxt.first.click(timeout=5500)
    # Require actual source card link turnover, not arbitrary fixed sleep.
    current_ids=[c["source_numeric_id"] for c in page_cards]
    try:
     await page.wait_for_function(
      """p=>{let now=[...document.querySelectorAll('a[href*="/properties/"]')].map(x=>x.href.match(/\/properties\/(\d+)/)?.[1]).filter(Boolean);
        return now.some(x=>!p.includes(x))}""",
       arg=current_ids,timeout=5000)
    except Exception:
     await page.wait_for_timeout(500)
     check=await page.evaluate(DOM)
     if not check["candidates"] or [x["source_numeric_id"] for x in check["candidates"]]==current_ids:
      record["status"]="PUBLIC_UI_NO_SOURCE_PAGE_CHANGE";break
   except Exception as ex:
    record["errors"].append("NEXT_PAGE_"+type(ex).__name__+":"+str(ex)[:110])
    record["status"]="PUBLIC_UI_PAGING_ERROR";break
  record["distinct_cards"]=list(cards.values())
  for ix in range(0,len(record["distinct_cards"]),12):
   print("SAE_NUZUL_SOURCE_CHUNK",json.dumps({"pid":src["project"],
     "source_id":src["source_id"],"original_project_url":url,
     "source_link_chunk":ix//12,
     "original_listing_cards":record["distinct_cards"][ix:ix+12]},ensure_ascii=False,separators=(",",":"))[:13500],flush=True)
  if record["status"]=="STARTED":record["status"]="SOURCE_COMPLETE_OR_NOT_PAGINATED"
 except Exception as ex:
  record["errors"].append(type(ex).__name__+":"+str(ex)[:175])
  record["status"]="SOURCE_ERROR_FAIL_CLOSED"
 finally:
  await page.close()
 return record

async def main():
 manifest=json.loads(MANIFEST.read_text(encoding="utf8"))
 targets=manifest.get("targets",[])
 if len(targets)!=MAX_TARGETS or any(not re.fullmatch(r"PRJ-\d{6}",t["project"]) for t in targets):
  raise RuntimeError("MANIFEST_NOT_VERIFIED")
 grouped=defaultdict(list)
 for t in targets:
  u=urlsplit(t["url"])
  if u.scheme!="https" or u.hostname!=t["official_domain"] or not re.search(r"/projects/\d+",u.path) or not re.fullmatch(r"SRC-\d{6}",t["source_id"]):
   raise RuntimeError("MANIFEST_EXACT_PUBLISHER_PROJECT_ID_MISSING")
  grouped[t["official_domain"]].append(t)
 rp={}
 for host in grouped:
  try:rp[host]=await asyncio.to_thread(get_robots,host)
  except Exception as ex:rp[host]="ROBOTS_UNVERIFIED_"+type(ex).__name__+":"+str(ex)[:75]
 host_blocked={}
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  for host,domain_targets in grouped.items():
   for source in domain_targets:
    if isinstance(rp[host],str):
     record={**source,"status":rp[host],"pages":[],"distinct_cards":[],"errors":[]}
    else:record=await project(browser,source,rp[host],host_blocked)
    state["results"].append(record)
    save()
    print("SAE_NUZUL_PROJECT",json.dumps({"pid":source["project"],"url":source["url"],
      "source_id":source["source_id"],"status":record["status"],
      "pages":len(record["pages"]),"source_distinct_property_links":len(record["distinct_cards"]),
      "original_samples":record["distinct_cards"][:5],
      "errors":record["errors"][:3]},ensure_ascii=False)[:4400],flush=True)
    await asyncio.sleep(.8)
   if host_blocked.get(host):state["errors"].append("SOURCE_ORIGIN_STOP_"+host)
  await browser.close()
 state["summary"]={"canonical_existing_projects":len(state["results"]),
    "original_publisher_hosts":len(grouped),
    "pages_traversed":sum(len(x["pages"]) for x in state["results"]),
    "distinct_original_property_links":sum(len(x["distinct_cards"]) for x in state["results"]),
    "source_stop_403_429_origins":list(host_blocked),
    "master_writes":0}
 save()
 print("SAE_NUZUL_FAMILY_COMPLETE",json.dumps(state["summary"],ensure_ascii=False),flush=True)

if __name__=="__main__":asyncio.run(main())
))
   if not await nxt.count():
    nxt=page.locator('button[aria-label$=" '+str(next_no)+'"]')
   if not await nxt.count():
    nxt=page.get_by_role("button",name=str(next_no),exact=True)
   if not await nxt.count():
    nxt=page.get_by_role("link",name=str(next_no),exact=True)
   if not await nxt.count():
    record["status"]="PUBLIC_PAGINATION_EXHAUSTED";break
   if not await nxt.first.is_enabled():
    record["status"]="PUBLIC_PAGINATION_DISABLED";break
   await asyncio.sleep(SOURCE_DELAY_SECONDS)
   try:
    await nxt.first.click(timeout=5500)
    # Require actual source card link turnover, not arbitrary fixed sleep.
    current_ids=[c["source_numeric_id"] for c in page_cards]
    try:
     await page.wait_for_function(
      """p=>{let now=[...document.querySelectorAll('a[href*="/properties/"]')].map(x=>x.href.match(/\/properties\/(\d+)/)?.[1]).filter(Boolean);
        return now.some(x=>!p.includes(x))}""",
       arg=current_ids,timeout=5000)
    except Exception:
     await page.wait_for_timeout(500)
     check=await page.evaluate(DOM)
     if not check["candidates"] or [x["source_numeric_id"] for x in check["candidates"]]==current_ids:
      record["status"]="PUBLIC_UI_NO_SOURCE_PAGE_CHANGE";break
   except Exception as ex:
    record["errors"].append("NEXT_PAGE_"+type(ex).__name__+":"+str(ex)[:110])
    record["status"]="PUBLIC_UI_PAGING_ERROR";break
  record["distinct_cards"]=list(cards.values())
  if record["status"]=="STARTED":record["status"]="SOURCE_COMPLETE_OR_NOT_PAGINATED"
 except Exception as ex:
  record["errors"].append(type(ex).__name__+":"+str(ex)[:175])
  record["status"]="SOURCE_ERROR_FAIL_CLOSED"
 finally:
  await page.close()
 return record

async def main():
 manifest=json.loads(MANIFEST.read_text(encoding="utf8"))
 targets=manifest.get("targets",[])
 if len(targets)!=MAX_TARGETS or any(not re.fullmatch(r"PRJ-\d{6}",t["project"]) for t in targets):
  raise RuntimeError("MANIFEST_NOT_VERIFIED")
 grouped=defaultdict(list)
 for t in targets:
  u=urlsplit(t["url"])
  if u.scheme!="https" or u.hostname!=t["official_domain"] or not re.search(r"/projects/\d+",u.path) or not re.fullmatch(r"SRC-\d{6}",t["source_id"]):
   raise RuntimeError("MANIFEST_EXACT_PUBLISHER_PROJECT_ID_MISSING")
  grouped[t["official_domain"]].append(t)
 rp={}
 for host in grouped:
  try:rp[host]=await asyncio.to_thread(get_robots,host)
  except Exception as ex:rp[host]="ROBOTS_UNVERIFIED_"+type(ex).__name__+":"+str(ex)[:75]
 host_blocked={}
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  for host,domain_targets in grouped.items():
   for source in domain_targets:
    if isinstance(rp[host],str):
     record={**source,"status":rp[host],"pages":[],"distinct_cards":[],"errors":[]}
    else:record=await project(browser,source,rp[host],host_blocked)
    state["results"].append(record)
    save()
    print("SAE_NUZUL_PROJECT",json.dumps({"pid":source["project"],"url":source["url"],
      "source_id":source["source_id"],"status":record["status"],
      "pages":len(record["pages"]),"source_distinct_property_links":len(record["distinct_cards"]),
      "original_samples":record["distinct_cards"][:5],
      "errors":record["errors"][:3]},ensure_ascii=False)[:4400],flush=True)
    await asyncio.sleep(.8)
   if host_blocked.get(host):state["errors"].append("SOURCE_ORIGIN_STOP_"+host)
  await browser.close()
 state["summary"]={"canonical_existing_projects":len(state["results"]),
    "original_publisher_hosts":len(grouped),
    "pages_traversed":sum(len(x["pages"]) for x in state["results"]),
    "distinct_original_property_links":sum(len(x["distinct_cards"]) for x in state["results"]),
    "source_stop_403_429_origins":list(host_blocked),
    "master_writes":0}
 save()
 print("SAE_NUZUL_FAMILY_COMPLETE",json.dumps(state["summary"],ensure_ascii=False),flush=True)

if __name__=="__main__":asyncio.run(main())
